/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * Serial USART interface
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include "serial.h"

#include <stddef.h>
#include <stdio.h>

#include "stm32f0xx.h"
#include "stm32f0xx_usart.h"
#include "systick.h"

// Baud rate for UART1 which connects to either a control board, or the previous preamp board.
#define UART_BAUD 9600

// Peripheral clock frequency in Hz. This clock is divided by BRR to get the baud rate.
#define PCLK_FREQ_HZ 8000000

// Timeout address reception, 40 ms should allow down to 1k baud
#define ADDR_TIMEOUT_MS 40

// Slave I2C address to be used on I2C1 (controller board bus).
// Address is stored in the top 7 bits of the byte, with the LSB 0.
uint8_t i2c_addr_ = 0;

// Passthrough messages between UART1<->UART2
bool uart_passthrough_ = false;

// Enables or disables passthrough of data received on the controller USART, USART1, to the
// expander USART, USART2.
void setUartPassthrough(bool passthrough) {
  uart_passthrough_ = passthrough;

  // If switching to passthrough mode, clear any debug messages pending.
  // If switching from passthrough mode, clear any programming messages pending.
  USART2->RQR |= USART_RQR_RXFRQ;  // RX data flush request, ensure no data is pending.

  // TODO: Verify these can be removed.
  // if (passthrough) {
  //    USART2->CR1 |= USART_CR1_RXNEIE;   // Enable RX interrupts for USART2.
  //    NVIC->ISER[0] = 1 << USART2_IRQn;  // Enable USART2 peripheral interrupts
  //} else {
  //   USART2->CR1 &= ~USART_CR1_RXNEIE;  // Disable RX interrupts for USART2.
  //   NVIC->ICER[0] = 1 << USART2_IRQn;  // Disable USART2 peripheral interrupts
  //}
}

bool getUartPassthrough() {
  return uart_passthrough_;
}

uint8_t getI2C1Address() {
  return i2c_addr_;
}

// Send an I2C address to the connected expansion unit, if one exists.
void sendAddressToSlave(uint8_t i2c_addr) {
  while (!(USART2->ISR & USART_ISR_TXE)) {}
  USART2->TDR = 'A';
  while (!(USART2->ISR & USART_ISR_TXE)) {}
  USART2->TDR = i2c_addr;
  while (!(USART2->ISR & USART_ISR_TXE)) {}
  USART2->TDR = '\n';
}

// UART1 allows the Pi to set preamp I2C addresses and flash preamp software
// UART2 is used for communicating with an expansion preamp.
void serial_init(serial_port_t port) {
  // TODO: Add baud rate parameter or create separate baud rate changing function
  // (for changing USART2's baud rate after receiving the auto-baud on USART1.)
  USART_TypeDef* usart_regs = port == serial_ctrl ? USART1 : USART2;

  // Clocks for both USARTs should always be enabled.
  RCC->APB2ENR |= RCC_APB2ENR_USART1EN;  // Enable peripheral clocks for USART1.
  RCC->APB1ENR |= RCC_APB1ENR_USART2EN;  // Enable peripheral clock for USART2.

  usart_regs->CR1 = 0;  // Disable USART so it can be configured.
  usart_regs->CR2 = 0;  // Ensure CR2 is cleared.
  usart_regs->CR3 = 0;  // Ensure CR3 is cleared.

  // Setup auto-baudrate detection, all other bits of CR2 should be 0.
  // Mode 0b01, aka "Falling Edge" mode, must start with 0b10...
  // Since UART sends LSB first, the first character must be 0bXXXXXX01
  // 'A' = 0b0100_0001 so works perfectly!
  // if (port == serial_ctrl) {
  // usart_regs->CR2 = USART_CR2_ABRMODE_0 | USART_CR2_ABREN;
  //}

  // Determine the value to divide the UART's input clock by to get the output baud desired.
  // Auto-baud will override this.
#if ((PCLK_FREQ_HZ % UART_BAUD) >= (UART_BAUD / 2))
  usart_regs->BRR = PCLK_FREQ_HZ / UART_BAUD + 1;
#else
  usart_regs->BRR = PCLK_FREQ_HZ / UART_BAUD;
#endif

  // Enable receiver, transmitter, RX empty interrupt, and enable USART1.
  usart_regs->CR1 = USART_CR1_RXNEIE | USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;

  // Enable USART1 peripheral's interrupts.
  NVIC->ISER[0] = port == serial_ctrl ? (1 << USART1_IRQn) : (1 << USART2_IRQn);
}

// Add a character to the serial buffer (UART)
static inline void check_for_address(uint8_t data_in) {
  static enum {
    WAITING_FOR_A,
    WAITING_FOR_ADDR,
    WAITING_FOR_NEWLINE
  } addr_state             = WAITING_FOR_A;
  static uint8_t next_addr = 0;
  static uint8_t timeout   = 0;

  // If too much time has elapsed since the last character received, start over.
  uint32_t current_time = millis();
  if (addr_state != WAITING_FOR_A && current_time > timeout) {
    printf("Address timeout\n");
    addr_state = WAITING_FOR_A;
  }

  // Expect 'A', ADDR, '\n' (or the old 'A', ADDR, '\r', '\n')
  switch (addr_state) {
    default:
      if (data_in == 'A') {
        timeout    = millis() + ADDR_TIMEOUT_MS;
        addr_state = WAITING_FOR_ADDR;
      }
      break;
    case WAITING_FOR_ADDR:
      next_addr  = data_in;
      addr_state = WAITING_FOR_NEWLINE;
      break;
    case WAITING_FOR_NEWLINE:
      if (data_in == '\n') {
        i2c_addr_  = next_addr;
        addr_state = WAITING_FOR_A;
      } else if (data_in == '\r') {
        // Got '\r', next should be '\n' so stay in this state.
        // TODO: remove this option.
      } else {
        // Got invalid character, go back to start.
        printf("Bad character received on serial\n");
        addr_state = WAITING_FOR_A;
      }
      break;
  }
}

// Handles the interrupt data reception from the control board or upstream preamp board.
void usart1_irq_handler() {
  uint32_t isr = USART1->ISR;
  if (isr & USART_ISR_ABRE) {
    // Auto-baud failed, clear read data and reset auto-baud
    USART1->RQR |= USART_RQR_ABRRQ | USART_RQR_RXFRQ;
  } else if (isr & USART_ISR_RXNE) {
    // RX data is ready, read it!
    uint8_t m = (uint8_t)USART1->RDR;
    if (uart_passthrough_) {
      // In passthrough (programming) mode, nothing else uses the UART so it's safe
      // to send data without checking flags.
      USART2->TDR = m;
    } else {
      // In normal mode, the only data received on USART1 is the "set I2C address" command.
      check_for_address(m);
    }
  }
}

// Handles the interrupt on the downstream UART data reception
void usart2_irq_handler() {
  // TODO: Add to transmit queue
  // Forward anything received on UART2 (expansion box)
  // to UART1 (back up the chain to the controller board)
  if (USART_GetITStatus(USART2, USART_IT_RXNE) != RESET) {
    uint16_t m = USART_ReceiveData(USART2);
    USART_SendData(USART1, m);
  }
}

// Write a character to UART
int _write(int file __attribute__((__unused__)), char* ptr, int len) {
  // Only stdout is actually supported, but accept any file writes as if they were to STDOUT_FILENO.
  // EXCEPT in uart_passthrough_ mode, where printf() writes to USART1 are forbidden.
  if (uart_passthrough_) {
    return -1;
  }

  uint32_t written = 0;
  for (; len != 0; --len) {
    // TODO: Add to transmit queue instead
    while (!(USART1->ISR & USART_ISR_TXE)) {}
    USART1->TDR = (uint16_t)*ptr++;
    written++;
  }
  return written;
}

// Below are unused system calls, implemented as stubs.

// Closing files not supported (no files can be opened).
int _close(int fd __attribute__((__unused__))) {
  return -1;
}

// Identifies all files as character special devices, forcing one-byte-read at a time.
#include <sys/stat.h>
int _fstat(int file __attribute__((__unused__)), struct stat* st) {
  st->st_mode = S_IFCHR;
  return 0;
}

// Test whether file is associated with a terminal device.
// The only 'file' implemented is stdout, so always return 1.
int _isatty(int file __attribute__((__unused__))) {
  return 1;
}

// Seeking is not supported.
int _lseek(int file __attribute__((__unused__)), int offset __attribute__((__unused__)),
           int whence __attribute__((__unused__))) {
  // Return 0, implying the file is empty.
  return 0;
}

// Read not yet implemented, will return -1.
int _read(int file __attribute__((__unused__)), char* ptr __attribute__((__unused__)),
          int len __attribute__((__unused__))) {
  return -1;
}
