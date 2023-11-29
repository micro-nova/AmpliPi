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

#include <string.h>  // memset

#include "stm32f0xx.h"
#include "stm32f0xx_gpio.h"
#include "stm32f0xx_usart.h"

// Peripheral clock frequency in Hz. This clock is divided by BRR to get the baud rate.
#define PCLK_FREQ_HZ 8000000

// Need at least 3 bytes for data: A + ADDR + \n.
// Memory is 4-byte word aligned, so the following works well with the
// 2 bytes for flags.
#define SB_MAX_SIZE 6

// Timeout address reception, 40 ms should allow down to 1k buad
#define SB_TIMEOUT 40

// Slave I2C address to be used on I2C1 (controller board bus).
// Address is stored in the top 7 bits of the byte, with the LSB 0.
uint8_t i2c_addr_ = 0;

// Passthrough messages between UART1<->UART2
bool uart_passthrough_ = false;

void setUartPassthrough(bool passthrough) {
  uart_passthrough_ = passthrough;
  if (passthrough) {
    USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
    NVIC_EnableIRQ(USART2_IRQn);
  } else {
    USART_ITConfig(USART2, USART_IT_RXNE, DISABLE);
    NVIC_DisableIRQ(USART2_IRQn);
  }
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

// Serial buffer for UART handling of I2C addresses
typedef struct {
  uint8_t data[SB_MAX_SIZE];  // Byte buffer
  uint8_t ind;                // Index (current location)
  uint8_t done;               // Buffer is complete (terminator reached)
  // uint32_t start;              // Time of first character reception (ms)
} SerialBuffer;
volatile SerialBuffer uart1_rx_buf_;
SerialBuffer          uart_tx_buf_;

void serialBufferReset(volatile SerialBuffer* sb) {
  memset((void*)sb, 0, sizeof(SerialBuffer));
}

// Add a character to the serial buffer (UART)
void serialBufferAdd(volatile SerialBuffer* sb, uint8_t data_in) {
  // Add new byte to buffer (as long as it isn't complete or overflowed).
  // Post-increment index.
  if (!sb->done) {
    sb->data[sb->ind++] = data_in;

    // On first character, start timer. Reset buffer if timed out.
    /*if (!sb->start) {
      sb->start = millis();
    } else if (sb->start > SB_TIMEOUT) {
      serialBufferReset(sb);
    }*/
  }

  // Check for completion (i.e. when last byte is \n)
  if (sb->ind >= 3 && sb->data[sb->ind - 1] == '\n') {
    sb->done = 1;

    // "A" - address identifier. Defends against potential noise on the wire
    if (uart1_rx_buf_.data[0] == 'A') {
      uart_tx_buf_      = uart1_rx_buf_;
      uart_tx_buf_.ind  = 0;
      uart_tx_buf_.done = 0;
      // initUart2(USART1->BRR);  // Use the same baud rate for both UARTs
      i2c_addr_ = uart1_rx_buf_.data[1];
    }
    serialBufferReset(sb);
  }

  // Check for overflow (i.e. when index exceeds buffer)
  if (sb->ind >= SB_MAX_SIZE && !sb->done) {
    serialBufferReset(sb);
  }
}

void initUart1() {
  // UART1 allows the Pi to set preamp I2C addresses and flash preamp software

  // Enable peripheral clock for UART1
  RCC->APB2ENR |= RCC_APB2ENR_USART1EN;

  // Setup USART1
  USART_Cmd(USART1, ENABLE);
  USART_InitTypeDef USART_InitStructure;
  USART_InitStructure.USART_BaudRate            = 9600;  // Auto-baud will override this
  USART_InitStructure.USART_WordLength          = USART_WordLength_8b;
  USART_InitStructure.USART_StopBits            = USART_StopBits_1;
  USART_InitStructure.USART_Parity              = USART_Parity_No;
  USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
  USART_InitStructure.USART_Mode                = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART1, &USART_InitStructure);

  // Setup auto-baudrate detection
  // Mode 0b01, aka "Falling Edge" mode, must start with 0b10...
  // Since UART sents LSB first, the first character must be 0bXXXXXX01
  // USART1->CR2 |= USART_AutoBaudRate_FallingEdge | USART_CR2_ABREN;

  USART_Cmd(USART1, ENABLE);

  // USART1 interrupt handler setup
  USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
  NVIC_EnableIRQ(USART1_IRQn);
}

// UART2 is used for communicating with an expansion preamp.
// @param baud: Baud rate to set in Hz.
void initUart2(uint16_t baud) {
  // Enable peripheral clock for UART2
  RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

  // Setup USART2
  USART_Cmd(USART2, ENABLE);
  USART_InitTypeDef USART_InitStructure2;
  USART_InitStructure2.USART_BaudRate            = 9600;
  USART_InitStructure2.USART_WordLength          = USART_WordLength_8b;
  USART_InitStructure2.USART_StopBits            = USART_StopBits_1;
  USART_InitStructure2.USART_Parity              = USART_Parity_No;
  USART_InitStructure2.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
  USART_InitStructure2.USART_Mode                = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART2, &USART_InitStructure2);
  // USART2->BRR = PCLK_FREQ_HZ / baud_div;
  (void)baud;  // TODO: Use auto-bauding.
  USART_Cmd(USART2, ENABLE);
}

/* Handles the interrupt on the upstream UART data reception.
 * Defined in startup_stm32.s.
 */
void usart1_irq_handler() {
  uint32_t isr = USART1->ISR;
  if (isr & USART_ISR_ABRE) {
    // Auto-baud failed, clear read data and reset auto-baud
    USART1->RQR |= USART_RQR_ABRRQ | USART_RQR_RXFRQ;
    serialBufferReset(&uart1_rx_buf_);
  } else if (isr & USART_ISR_RXNE) {
    uint16_t m = USART_ReceiveData(USART1);
    if (uart_passthrough_) {
      USART_SendData(USART2, m);
    } else {
      serialBufferAdd(&uart1_rx_buf_, (uint8_t)m);
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
