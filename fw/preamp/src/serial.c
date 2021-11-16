/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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
#include "stm32f0xx_rcc.h"
#include "stm32f0xx_usart.h"

// Need at least 3 bytes for data: A + ADDR + \n.
// Memory is 4-byte word aligned, so the following works well with the
// 2 bytes for flags.
#define SB_MAX_SIZE 6

// Timeout address reception, 40 ms should allow down to 1k buad
#define SB_TIMEOUT 40

// Slave I2C address on I2C1 (controller bus)
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
  }

  // Check for overflow (i.e. when index exceeds buffer)
  if (sb->ind >= SB_MAX_SIZE && !sb->done) {
    serialBufferReset(sb);
  }
}

void initUart1() {
  // UART1 allows the Pi to set preamp I2C addresses and flash preamp software

  // Enable peripheral clocks for UART1
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);

  // Setup USART1
  USART_Cmd(USART1, ENABLE);
  USART_InitTypeDef USART_InitStructure;
  USART_InitStructure.USART_BaudRate   = 9600;  // Auto-baud will override this
  USART_InitStructure.USART_WordLength = USART_WordLength_8b;
  USART_InitStructure.USART_StopBits   = USART_StopBits_1;
  USART_InitStructure.USART_Parity     = USART_Parity_No;
  USART_InitStructure.USART_HardwareFlowControl =
      USART_HardwareFlowControl_None;
  USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
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

void initUart2(uint16_t brr) {
#ifndef DEBUG_OVER_UART2
  // UART2 is used for debugging with an external debugger
  // or for communicating with an expansion preamp.

  // Enable peripheral clock
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

  // Setup USART2
  USART_Cmd(USART2, ENABLE);
  USART_InitTypeDef USART_InitStructure2;
  USART_InitStructure2.USART_BaudRate   = 9600;
  USART_InitStructure2.USART_WordLength = USART_WordLength_8b;
  USART_InitStructure2.USART_StopBits   = USART_StopBits_1;
  USART_InitStructure2.USART_Parity     = USART_Parity_No;
  USART_InitStructure2.USART_HardwareFlowControl =
      USART_HardwareFlowControl_None;
  USART_InitStructure2.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART2, &USART_InitStructure2);
  // USART2->BRR = brr;
  (void)brr;
  USART_Cmd(USART2, ENABLE);
#endif
}

bool checkForNewAddress() {
  static size_t tx_len = 0;

  // TODO: Assume default slave address, wait a bit to see if new address is
  //       received, then either accept new address or use default.
  // TODO: Better state machine with timeout
  if (uart1_rx_buf_.done) {
    // "A" - address identifier. Defends against potential noise on the wire
    if (uart1_rx_buf_.data[0] == 'A') {
      // Set expansion preamp's address, if it exists. Increment the address
      // received by 0x10 to get the address for the next preamp.
      uart_tx_buf_      = uart1_rx_buf_;
      tx_len            = uart_tx_buf_.ind;
      uart_tx_buf_.ind  = 0;
      uart_tx_buf_.done = 0;
      // initUart2(USART1->BRR);  // Use the same baud rate for both UARTs
      i2c_addr_ = uart1_rx_buf_.data[1];
    }
    serialBufferReset(&uart1_rx_buf_);
  }
  // Forward address to next preamp
  /*if (tx_len && USART1->ISR & USART_ISR_TXE && USART2->ISR & USART_ISR_TXE) {
    uint16_t data = uart_tx_buf_.data[uart_tx_buf_.ind];
    USART_SendData(USART1, data);
    if (uart_tx_buf_.ind == 1) {
      data += 0x10;  // New address for next preamp
    }
    USART_SendData(USART2, data);
    uart_tx_buf_.ind++;
    tx_len--;
  }*/
  if (i2c_addr_) {
    (void)tx_len;
    while (!(USART2->ISR & USART_ISR_TXE)) {}
    USART2->TDR = 'A';
    while (!(USART2->ISR & USART_ISR_TXE)) {}
    USART2->TDR = i2c_addr_ + 0x10;  // Add 0x10 to get next address
    while (!(USART2->ISR & USART_ISR_TXE)) {}
    USART2->TDR = 0x0A;  // '\n'
  }
  return i2c_addr_ != 0;
}

uint8_t getI2C1Address() {
  return i2c_addr_;
}

// Handles the interrupt on UART data reception
void USART1_IRQHandler(void) {
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

void USART2_IRQHandler(void) {
  // Forward anything received on UART2 (expansion box)
  // to UART1 (back up the chain to the controller board)
  if (USART_GetITStatus(USART2, USART_IT_RXNE) != RESET) {
    uint16_t m = USART_ReceiveData(USART2);
    USART_SendData(USART1, m);
  }
}
