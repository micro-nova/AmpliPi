/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "audio_mux.h"
#include "ctrl_i2c.h"
#include "int_i2c.h"
#include "port_defs.h"
#include "stm32f0xx.h"
#include "systick.h"
#include "version.h"

// State of the AmpliPi hardware
AmpliPiState state_;

void USART_PutString(USART_TypeDef* USARTx, const char* str);

// Uncomment the line below to use the debugger
//#define DEBUG_OVER_UART2

void initGpio() {
  // Enable peripheral clocks for GPIO ports
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOC, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOD, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);

  // Setup IO pin directions PORT A
  GPIO_InitTypeDef GPIO_InitStructureA;
  GPIO_InitStructureA.GPIO_Pin =
      pZONE1_SRC1_EN | pZONE1_SRC3_EN | pZONE2_SRC1_EN | pZONE2_SRC2_EN |
      pZONE2_SRC4_EN | pZONE6_SRC2_EN | pZONE6_SRC3_EN | pZONE6_SRC4_EN |
      pZONE4_MUTE | pZONE5_MUTE | pZONE6_STBY;
  GPIO_InitStructureA.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureA.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureA.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureA.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOA, &GPIO_InitStructureA);

  // Setup IO pin directions PORT B
  GPIO_InitTypeDef GPIO_InitStructureB;
  GPIO_InitStructureB.GPIO_Pin =
      pZONE3_SRC2_EN | pZONE3_SRC3_EN | pZONE3_SRC4_EN | pZONE3_SRC2_EN |
      pZONE4_SRC2_EN | pZONE5_SRC2_EN | pZONE5_SRC4_EN | pZONE1_MUTE |
      pZONE1_STBY | pZONE2_STBY | pZONE3_STBY | pSRC1_AEN | pSRC2_AEN;
  GPIO_InitStructureB.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureB.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureB.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureB.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOB, &GPIO_InitStructureB);

  // Setup IO pin directions PORT C
  GPIO_InitTypeDef GPIO_InitStructureC;
  GPIO_InitStructureC.GPIO_Pin =
      pZONE2_SRC3_EN | pZONE3_SRC1_EN | pZONE4_SRC1_EN | pZONE4_SRC3_EN |
      pZONE4_SRC4_EN | pZONE5_SRC3_EN | pZONE6_SRC1_EN | pZONE2_MUTE |
      pZONE3_MUTE | pZONE4_STBY | pZONE5_STBY | pSRC3_AEN | pSRC4_AEN |
      pSRC2_DEN | pSRC3_DEN | pSRC4_DEN;
  GPIO_InitStructureC.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureC.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureC.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureC.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructureC);

  // Setup IO pin directions PORT D
  GPIO_InitTypeDef GPIO_InitStructureD;
  GPIO_InitStructureD.GPIO_Pin   = pSRC1_DEN;
  GPIO_InitStructureD.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureD.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureD.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureD.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOD, &GPIO_InitStructureD);

  // Setup IO pin directions PORT F
  GPIO_InitTypeDef GPIO_InitStructureF;
  GPIO_InitStructureF.GPIO_Pin = pZONE1_SRC2_EN | pZONE1_SRC4_EN |
                                 pZONE5_SRC1_EN | pZONE6_MUTE | pNRST_OUT |
                                 pBOOT0_OUT;
  GPIO_InitStructureF.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureF.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureF.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureF.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOF, &GPIO_InitStructureF);
}

void initUart1() {
  // UART1 allows the Pi to set preamp I2C addresses and flash preamp software

  // Enable peripheral clocks for UART1
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);

  // Connect pins to alternate function for UART1
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource9, GPIO_AF_1);
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource10, GPIO_AF_1);

  // Config UART1 GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureUART;
  GPIO_InitStructureUART.GPIO_Pin   = GPIO_Pin_9 | GPIO_Pin_10;
  GPIO_InitStructureUART.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureUART.GPIO_PuPd  = GPIO_PuPd_UP;
  GPIO_InitStructureUART.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureUART.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_Init(GPIOA, &GPIO_InitStructureUART);

  // Setup USART1
  USART_Cmd(USART1, ENABLE);
  USART_InitTypeDef USART_InitStructure;
  USART_InitStructure.USART_BaudRate = 115200;  // Auto-baud will override this
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
  USART1->CR2 |= USART_AutoBaudRate_FallingEdge | USART_CR2_ABREN;

  USART_Cmd(USART1, ENABLE);

  // USART1 interrupt handler setup
  USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
  NVIC_EnableIRQ(USART1_IRQn);
}

void initUart2(uint16_t brr) {
  // UART2 is used for debugging with an external debugger
  // or for communicating with an expansion preamp.

  // Enable peripheral clock
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

  // Connect pins to alternate function for UART2
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource14, GPIO_AF_1);
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource15, GPIO_AF_1);

  // Configure UART2 GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureUART2;
  GPIO_InitStructureUART2.GPIO_Pin   = GPIO_Pin_14 | GPIO_Pin_15;
  GPIO_InitStructureUART2.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureUART2.GPIO_PuPd  = GPIO_PuPd_UP;
  GPIO_InitStructureUART2.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureUART2.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_Init(GPIOA, &GPIO_InitStructureUART2);

  // Setup USART2
  USART_Cmd(USART2, ENABLE);
  USART_InitTypeDef USART_InitStructure2;
  USART_InitStructure2.USART_BaudRate   = 115200;
  USART_InitStructure2.USART_WordLength = USART_WordLength_8b;
  USART_InitStructure2.USART_StopBits   = USART_StopBits_1;
  USART_InitStructure2.USART_Parity     = USART_Parity_No;
  USART_InitStructure2.USART_HardwareFlowControl =
      USART_HardwareFlowControl_None;
  USART_InitStructure2.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART2, &USART_InitStructure2);
  USART2->BRR = brr;
  USART_Cmd(USART2, ENABLE);
}

// Need at least 5 bytes for data: A + ADDR + \r + \n + \0.
// Memory is 4-byte word aligned, so the following works well with the
// 2 bytes for flags.
#define SB_MAX_SIZE 6

// Timeout address reception, 40 ms should allow down to 1k buad
#define SB_TIMEOUT 40

// Serial buffer for UART handling of I2C addresses
typedef struct {
  char    data[SB_MAX_SIZE];  // Byte buffer
  uint8_t ind;                // Index (current location)
  uint8_t done;               // Buffer is complete (terminator reached)
  // uint32_t start;              // Time of first character reception (ms)
} SerialBuffer;
volatile SerialBuffer uart1RxBuffer_;

void rxBufReset(volatile SerialBuffer* sb) {
  memset((void*)sb, 0, sizeof(SerialBuffer));
}

// Add a character to the serial buffer (UART)
void rxBufAdd(volatile SerialBuffer* sb, uint8_t data_in) {
  // Add new byte to buffer (as long as it isn't complete or overflowed).
  // Post-increment index.
  if (!sb->done) {
    sb->data[sb->ind++] = data_in;

    // On first character, start timer. Reset buffer if timed out.
    /*if (!sb->start) {
      sb->start = millis();
    } else if (sb->start > SB_TIMEOUT) {
      rxBufReset(sb);
    }*/
  }

  // Check for completion (i.e. when last two bytes are <CR><LF>)
  if (sb->ind >= 2 && sb->data[sb->ind - 2] == '\r' &&
      sb->data[sb->ind - 1] == '\n') {
    sb->done = 1;
  }

  // Check for overflow (i.e. when index exceeds buffer)
  if (sb->ind >= SB_MAX_SIZE && !sb->done) {
    rxBufReset(sb);
  }
}

void initState(AmpliPiState* state) {
  memset(state, 0, sizeof(AmpliPiState));
  state->pwr_gpio.en_12v = 1;  // Always enable 12V
}

int main(void) {
  // TODO: Setup watchdog

  // RESET AND PIN SETUP
  writePin(exp_nrst_, false);   // Low-pulse on NRST_OUT so expansion boards are
                                // reset by the controller board
  writePin(exp_boot0_, false);  // Needs to be low so the subsequent preamp
                                // board doesn't start in 'Boot Mode'

  // INIT
  initState(&state_);
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality
  initGpio();     // UART and I2C require GPIO pins
  // Initialize each channel's volume state
  // (does not write to volume control ICs)
  initZones();
  // Initialize each source's analog/digital state
  initSources();
  initUart1();  // The preamp will receive its I2C network address via UART
  initInternalI2C(&state_);  // Setup the internal I2C bus

  // RELEASE EXPANSION RESET
  // Needs to be high so the subsequent preamp board is not held in 'Reset Mode'
  writePin(exp_nrst_, true);
  state_.expansion.nrst = true;

  USART_PutString(USART1, "Entering main loop\r\n");

  // Main loop, awaiting I2C commands
  while (1) {
    // TODO: Clear watchdog

    // Check for incomming control messages if a slave address has been set
    if (state_.i2c_addr && ctrlI2CAddrMatch()) {
      ctrlI2CTransact(&state_);
    }

    // TODO: Assume default slave address, wait a bit to see if new address is
    //       received, then either accept new address or use default.
    // TODO: Better state machine with timeout
    if (uart1RxBuffer_.done) {
      // "A" - address identifier. Defends against potential noise on the wire
      if (uart1RxBuffer_.data[0] == 'A') {
#ifndef DEBUG_OVER_UART2
        // Set expansion preamp's address, if it exists. Increment the address
        // received by 0x10 to get the address for the next preamp.
        SerialBuffer tx_buf = uart1RxBuffer_;
        tx_buf.data[1]      = tx_buf.data[1] + 0x10;
        initUart2(USART1->BRR);  // Use the same baud rate for both UARTs
        USART_PutString(USART2, tx_buf.data);
#endif
        // Initialize I2C1 with the new address
        state_.i2c_addr = uart1RxBuffer_.data[1];
        ctrlI2CInit(state_.i2c_addr);
      }
      rxBufReset(&uart1RxBuffer_);
      USART_PutString(USART1, "Address\r\n");
    }

    // Read internal I2C bus every 32 ms (31.25 Hz)
    bool read_internal_i2c = !(millis() & ((1 << 5) - 1));
    if (read_internal_i2c) {
      // TODO: move logic outside I2C function
      updateInternalI2C(&state_);
    }
  }
}

/*
 * Function to send a string over USART
 * Inputs: USARTx (1 or 2), string
 * Process: Sends out string character-by-character and then sends
 * carriage return and line feed when done if needed
 */
void USART_PutString(USART_TypeDef* USARTx, const char* str) {
  while (*str != 0) {
    while (!(USARTx->ISR & USART_ISR_TXE)) {}
    USART_SendData(USARTx, *str);
    str++;
  }
}

// Handles the interrupt on UART data reception
void USART1_IRQHandler(void) {
  uint32_t isr = USART1->ISR;
  if (isr & USART_ISR_ABRE) {
    // Auto-baud failed, clear read data and reset auto-baud
    USART1->RQR |= USART_RQR_ABRRQ | USART_RQR_RXFRQ;
  } else if (isr & USART_ISR_RXNE) {
    uint16_t m = USART_ReceiveData(USART1);
    if (state_.uart_passthrough) {
      USART_SendData(USART2, m);
    } else {
      rxBufAdd(&uart1RxBuffer_, (uint8_t)m);
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
