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

#include "channel.h"
#include "ctrl_i2c.h"
#include "front_panel.h"
#include "port_defs.h"
#include "power_board.h"
#include "stm32f0xx.h"
#include "systick.h"
#include "version.h"

void USART_PutString(USART_TypeDef* USARTx, volatile uint8_t* str);

// Uncomment the line below to use the debugger
//#define DEBUG_OVER_UART2

void init_gpio() {
  // Enable peripheral clocks for GPIO ports
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOC, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOD, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);

  // Setup IO pin directions PORT A
  GPIO_InitTypeDef GPIO_InitStructureA;
  GPIO_InitStructureA.GPIO_Pin = pCH1_SRC1_EN | pCH1_SRC3_EN | pCH2_SRC1_EN |
                                 pCH2_SRC2_EN | pCH2_SRC4_EN | pCH6_SRC2_EN |
                                 pCH6_SRC3_EN | pCH6_SRC4_EN | pCH4_MUTE |
                                 pCH5_MUTE | pCH6_STBY;
  GPIO_InitStructureA.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureA.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureA.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureA.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOA, &GPIO_InitStructureA);

  // Setup IO pin directions PORT B
  GPIO_InitTypeDef GPIO_InitStructureB;
  GPIO_InitStructureB.GPIO_Pin = pCH3_SRC2_EN | pCH3_SRC3_EN | pCH3_SRC4_EN |
                                 pCH3_SRC2_EN | pCH4_SRC2_EN | pCH5_SRC2_EN |
                                 pCH5_SRC4_EN | pCH1_MUTE | pCH1_STBY |
                                 pCH2_STBY | pCH3_STBY | pSRC1_AEN | pSRC2_AEN;
  GPIO_InitStructureB.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureB.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureB.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureB.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOB, &GPIO_InitStructureB);

  // Setup IO pin directions PORT C
  GPIO_InitTypeDef GPIO_InitStructureC;
  GPIO_InitStructureC.GPIO_Pin =
      pCH2_SRC3_EN | pCH3_SRC1_EN | pCH4_SRC1_EN | pCH4_SRC3_EN | pCH4_SRC4_EN |
      pCH5_SRC3_EN | pCH6_SRC1_EN | pCH2_MUTE | pCH3_MUTE | pCH4_STBY |
      pCH5_STBY | pSRC3_AEN | pSRC4_AEN | pSRC2_DEN | pSRC3_DEN | pSRC4_DEN;
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
  GPIO_InitStructureF.GPIO_Pin = pCH1_SRC2_EN | pCH1_SRC4_EN | pCH5_SRC1_EN |
                                 pCH6_MUTE | pNRST_OUT | pBOOT0_OUT;
  GPIO_InitStructureF.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureF.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureF.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureF.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOF, &GPIO_InitStructureF);
}

void init_i2c2() {
  /* I2C-2 is internal to a single AmpliPi unit.
   * The STM32 is the master and controls the volume chips, power, fans,
   * and front panel LEDs.
   *
   * Bus Capacitance
   * | Device           | Capacitance (pF)
   * | STM32            | 5
   * | MAX11601 (ADC)   | 15 (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.15? t_SU.DAT>0.1 t_r<.3 t_f<.3)
   * | MCP23008 (Power) | ?? (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.9   t_SU.DAT>0.1 t_r<.3 t_f<.3)
   * | MCP23008 (LEDs)  | ??
   * | MCP4017 (DPot)   | 10 (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.9   t_SU.DAT>0.1 t_r<.3 t_f<.04)
   * | TDA7448 (Vol1)   | ??????????????
   * | TDA7448 (Vol2)   | Doesn't even specify max frequency...
   * ~70 pF for all devices, plus say ~20 pF for all traces and wires = ~90 pF
   * So rise time t_r ~= 0.8473 * 1 kOhm * 90 pF = 76 ns
   * Measured rise time: 72 ns
   * Measured fall time:  4 ns
   *
   * Pullup Resistor Values
   *   Max output current for I2C Standard/Fast mode is 3 mA, so min pullup is:
   *    Rp > [V_DD - V_OL(max)] / I_OL = (3.3 V - 0.4 V) / 3 mA = 967 Ohm
   *   Max bus capacitance (with only resistor for pullup) is 200 pF.
   *   Standard mode rise-time t_r(max) = 1000 ns
   *    Rp_std < t_r(max) / (0.8473 * C_b) = 1000 / (0.8473 * 0.2) = 5901 Ohm
   *   Fast mode rise-time t_r(max) = 300 ns
   *    Rp_fast < t_r(max) / (0.8473 * C_b) = 1000 / (0.8473 * 0.2) = 1770 Ohm
   *   For Standard mode: 1k <= Rp <= 5.6k
   *   For Fast mode: 1k <= Rp <= 1.6k
   */

  // Enable peripheral clock for I2C2
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);

  // Enable SDA1, SDA2, SCL1, SCL2 clocks
  // Enabled here since this is called before I2C1
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);

  // Connect pins to alternate function for I2C2
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource10, GPIO_AF_1);  // I2C2_SCL
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource11, GPIO_AF_1);  // I2C2_SDA

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C;
  GPIO_InitStructureI2C.GPIO_Pin   = pSCL_VOL | pSDA_VOL;
  GPIO_InitStructureI2C.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
  GPIO_InitStructureI2C.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

  // Setup I2C2
  I2C_InitTypeDef I2C_InitStructure2;
  I2C_InitStructure2.I2C_Mode                = I2C_Mode_I2C;
  I2C_InitStructure2.I2C_AnalogFilter        = I2C_AnalogFilter_Enable;
  I2C_InitStructure2.I2C_DigitalFilter       = 0x00;
  I2C_InitStructure2.I2C_OwnAddress1         = 0x00;
  I2C_InitStructure2.I2C_Ack                 = I2C_Ack_Enable;
  I2C_InitStructure2.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;

  // Datasheet example: 100 kHz: 0x10420F13, 400 kHz: 0x10310309
  // Excel tool, rise/fall 76/15 ns: 100 kHz: 0x00201D2B (0.5935% error)
  //                                 400 kHz: 0x0010020A (2.4170% error)

  // Common parameters
  // t_I2CCLK = 1 / 8 MHz = 125 ns
  // t_AF(min) = 50 ns
  // t_AF(max) = 260 ns
  // t_r = 72 ns
  // t_f = 4 ns
  // Fall time must be < 300 ns
  // For Standard mode (100 kHz), rise time < 1000 ns
  // For Fast mode (400 kHz), rise time < 300 ns
  // tR = 0.8473*Rp*Cb = 847.3*Cb

  // Standard mode, max 100 kHz
  // t_LOW > 4.7 us
  // t_HIGH > 4 us
  // t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (4700 - 50) / 4 = 1.1625 ns
  // t_I2CCLK < t_HIGH = 4000 ns
  // Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
  // t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
  // SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
  // SDADEL >= [t_f - 50 - 375] / 125 --- This will be < 0, so SDASEL >= 0
  // SDADEL <= [t_HD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
  // SDADEL <= (3450 - 76 - 260 - 500) / 125 = 20.912
  // SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
  // SCLDEL >= (76 + 250) / 125 - 1 = 1.608
  // So 0 <= SDADEL <= 20, SCLDEL >= 2
  // I2C_TIMINGR[31:16] = 0x0020
  //
  // t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
  // 4000 <= 50 + 2*125 + 125*(SCLH + 1)
  // 3575 <= 125*SCLH
  // SCLH >= 28.6 = 0x1D
  //
  // t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
  // 4700 <= 50 + 2*125 + 125*(SCLL + 1)
  // 4275 <= 125*SCLL
  // SCLL >= 34.2 = 0x23
  //
  // Need to stay under 100 kHz in "worst" case. Keep SCLH at min,
  // but here we determine final SCLL.
  // t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns (100 kHz max)
  // t_SYNC1(min) = t_f + t_AF(min) + t_DNF + 2*t_I2CCLK
  // t_SYNC1(min) = 6 + 50 + 2*125 = 306 ns
  // t_SYNC2(min) = t_r + t_AF(min) + t_DNF + 2*t_I2CCLK
  // t_SYNC2(min) = 76 + 50 + 2*125 = 376 ns
  // t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns
  // t_LOW + t_HIGH >= 9318 ns
  // t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 9318 ns
  // 125*(SCLL + 1) + 125*30 >= 9318 ns
  // 125*(SCLL + 1) + 125*30 >= 9318 ns
  // SCLL >= 43.544 = 0x2C

  // Fast mode, max 400 kHz
  // TODO?

  I2C_InitStructure2.I2C_Timing = 0x00201D2C;
  I2C_Init(I2C2, &I2C_InitStructure2);
  I2C_Cmd(I2C2, ENABLE);
}

void init_uart1() {
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
  USART1->CR2 |= USART_AutoBaudRate_FallingEdge | USART_CR2_ABREN;

  USART_Cmd(USART1, ENABLE);

  // USART1 interrupt handler setup
  USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
  NVIC_EnableIRQ(USART1_IRQn);
}

void init_uart2(uint16_t brr) {
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

// Serial buffer for UART handling of I2C addresses
#define SB_MAX_SIZE (64)
typedef struct {
  uint8_t data[SB_MAX_SIZE];  // Byte buffer
  uint8_t ind;                // Index (current location)
  uint8_t done;               // Buffer is complete (terminator reached)
  uint8_t ovf;                // Buffer has overflowed!
} SerialBuffer;
volatile SerialBuffer UART_Preamp_RxBuffer;

// Add a character to the serial buffer (UART)
void RxBuf_Add(volatile SerialBuffer* sb, uint8_t data_in) {
  // Add new byte to buffer (as long as it isn't complete or overflowed).
  // Post-increment index.
  if (!(sb->done) && !(sb->ovf)) {
    sb->data[sb->ind++] = data_in;
  }
  // Check for completion (i.e. when last two bytes are <CR><LF>)
  if (sb->ind >= 2 && sb->data[(sb->ind) - 2] == 0x0D &&
      sb->data[(sb->ind) - 1] == 0x0A) {
    sb->done = 1;
  }
  // Check for overflow (i.e. when index exceeds buffer)
  if (sb->ind >= SB_MAX_SIZE) {
    sb->ovf = 1;
  }
}

int main(void) {
  // VARIABLES
  uint8_t i2c_addr;       // I2C address received via UART
  bool    red_on = true;  // Used for switching the Standby/On LED

  // RESET AND PIN SETUP
  Pin f0 = {'F', 0};  // Expansion connector NRST_OUT
  Pin f1 = {'F', 1};  // Expansion connector BOOT0_OUT
  clearPin(f0);  // Low-pulse on NRST_OUT so expansion boards are reset by the
                 // controller board
  clearPin(f1);  // Needs to be low so the subsequent preamp board doesn't
                 // start in 'Boot Mode'

  // INIT
  init_gpio();   // UART and I2C require GPIO pins
  init_uart1();  // The preamp will receive its I2C network address via UART
  init_i2c2();   // Need I2C2 initialized for the front panel functionality
                 // during the address loop
  enableFrontPanel();  // Setup the I2C->GPIO chip
  enablePowerBoard();  // Setup the power supply chip
  enablePSU();         // Turn on 9V/12V power
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality

  // RELEASE EXPANSION RESET
  // delay_ms(1);          // Hold low for 1 ms
  setPin(f0);  // Needs to be high so the subsequent preamp board is not held in
               // 'Reset Mode'

  while (1) {
    if (UART_Preamp_RxBuffer.done == 1) {
      // "A" - address identifier. Defends against potential noise on the wire
      if (UART_Preamp_RxBuffer.data[0] == 0x41) {
        // This will be the device address on I2C1.
        i2c_addr = UART_Preamp_RxBuffer.data[1];
#ifndef DEBUG_OVER_UART2
        // Set expansion preamp's address, if it exists. Increment the address
        // received by 0x10 to get the address for the next preamp.
        SerialBuffer tx_buf         = UART_Preamp_RxBuffer;
        tx_buf.data[tx_buf.ind - 3] = tx_buf.data[tx_buf.ind - 3] + 0x10;
        init_uart2(USART1->BRR);  // Use the same baud rate for both UARTs
        USART_PutString(USART2, tx_buf.data);
#endif
        break;
      }
      // Allow time for any extra garbage data to shift in
      delay_ms(2);
      // Only necessary for multiple runs without cycling power
      memset((void*)&UART_Preamp_RxBuffer, 0, sizeof(SerialBuffer));
    } else if (UART_Preamp_RxBuffer.ovf == 1) {
      // Clear the buffer if it overflows
      memset((void*)&UART_Preamp_RxBuffer, 0, sizeof(SerialBuffer));
    }

    // Alternate red light status at ~1 Hz
    bool blink = (millis() >> 10) & 1;
    if (red_on != blink) {
      red_on = blink;
      updateFrontPanel(red_on);
    }
  }

  // Stabilize the blinking red LED once an address is given
  updateFrontPanel(true);
  // Initialize I2C with the new address
  CtrlI2CInit(i2c_addr);
  // Initialize each channel's volume state
  // (does not write to volume control ICs)
  initChannels();
  // Initialize each source's analog/digital state
  initSources();

  // Main loop, awaiting I2C commands
  while (1) {
    // Check for incomming control messages
    if (CtrlI2CAddrMatch()) {
      CtrlI2CTransact(f0, f1);
    }
  }
}

/*
 * Function to send a string over USART
 * Inputs: USARTx (1 or 2), string
 * Process: Sends out string character-by-character and then sends
 * carriage return and line feed when done if needed
 */
void USART_PutString(USART_TypeDef* USARTx, volatile uint8_t* str) {
  // Delay time in ms. Increase to send out message more slowly. At 9600 baud,
  // UART sends roughly 1 char each millisecond
  int dt = 2;
  while (*str != 0) {
    // TODO: Delay until ready
    USART_SendData(USARTx, *str);
    str++;
    delay_ms(dt);
  }
  delay_ms(dt);
}

// Handles the interrupt on UART data reception
void USART1_IRQHandler(void) {
  uint32_t isr = USART1->ISR;
  if (isr & USART_ISR_ABRE) {
    // Auto-baud failed, clear read data and reset auto-baud
    USART1->RQR |= USART_RQR_ABRRQ | USART_RQR_RXFRQ;
  } else if (isr & USART_ISR_RXNE) {
    uint16_t m = USART_ReceiveData(USART1);
    if (UartPassthroughEnabled()) {
      USART_SendData(USART2, m);
    } else {
      RxBuf_Add(&UART_Preamp_RxBuffer, (uint8_t)m);
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
