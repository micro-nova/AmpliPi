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

#include "channel.h"
#include "front_panel.h"
#include "port_defs.h"
#include "power_board.h"
#include "stm32f0xx.h"
#include "systick.h"
#include "version.h"

static bool uart_passthrough_ = false;

void init_i2c1(uint8_t preamp_addr);
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

void init_i2c1(uint8_t preamp_addr) {
  // I2C1 is from control board
  //
  // Single AmpliPi unit:
  //  t_r = ~370 ns
  //  t_f = ~5.3 ns
  // Single expansion unit:
  //  t_r = ~450 ns
  //  t_f = ~7.2 ns
  // Two expansion units:
  //  t_r = ~600 ns
  //  t_f = ~9.4 ns

  // Enable peripheral clock for I2C1
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

  // Connect pins to alternate function for I2C1
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource6, GPIO_AF_1);  // I2C1_SCL
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource7, GPIO_AF_1);  // I2C1_SDA

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C;
  GPIO_InitStructureI2C.GPIO_Pin   = pSCL | pSDA;
  GPIO_InitStructureI2C.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
  GPIO_InitStructureI2C.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

  // Setup I2C1
  I2C_InitTypeDef I2C_InitStructure1;
  I2C_InitStructure1.I2C_Mode                = I2C_Mode_I2C;
  I2C_InitStructure1.I2C_AnalogFilter        = I2C_AnalogFilter_Enable;
  I2C_InitStructure1.I2C_DigitalFilter       = 0x00;
  I2C_InitStructure1.I2C_OwnAddress1         = preamp_addr;
  I2C_InitStructure1.I2C_Ack                 = I2C_Ack_Enable;
  I2C_InitStructure1.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
  I2C_InitStructure1.I2C_Timing = 0;  // Clocks not generated in slave mode
  I2C_Init(I2C1, &I2C_InitStructure1);
  I2C_Cmd(I2C1, ENABLE);
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

void init_uart() {
  // UART allows the control board to set preamp I2C addresses and flash preamp
  // software UART2 is used for debugging with an external debugger

  // Enable peripheral clocks for UART
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1, ENABLE);
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2, ENABLE);

  // Connect pins to alternate function for UART1
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource9, GPIO_AF_1);   // UART1
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource10, GPIO_AF_1);  //

#ifndef DEBUG_OVER_UART2
  // Connect pins to alternate function for UART2
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource14, GPIO_AF_1);  // UART2
  GPIO_PinAFConfig(GPIOA, GPIO_PinSource15, GPIO_AF_1);  //
#endif

  // Config UART1 GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureUART;
  GPIO_InitStructureUART.GPIO_Pin   = GPIO_Pin_9 | GPIO_Pin_10;
  GPIO_InitStructureUART.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureUART.GPIO_PuPd  = GPIO_PuPd_UP;
  GPIO_InitStructureUART.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureUART.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_Init(GPIOA, &GPIO_InitStructureUART);

#ifndef DEBUG_OVER_UART2
  // Config UART2 GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureUART2;
  GPIO_InitStructureUART2.GPIO_Pin   = GPIO_Pin_14 | GPIO_Pin_15;
  GPIO_InitStructureUART2.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureUART2.GPIO_PuPd  = GPIO_PuPd_UP;
  GPIO_InitStructureUART2.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureUART2.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_Init(GPIOA, &GPIO_InitStructureUART2);
#endif

  // Setup USART1
  USART_Cmd(USART1, ENABLE);
  USART_InitTypeDef USART_InitStructure;
  USART_InitStructure.USART_BaudRate   = 9600;
  USART_InitStructure.USART_WordLength = USART_WordLength_8b;
  USART_InitStructure.USART_StopBits   = USART_StopBits_1;
  USART_InitStructure.USART_Parity     = USART_Parity_No;
  USART_InitStructure.USART_HardwareFlowControl =
      USART_HardwareFlowControl_None;
  USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
  USART_Init(USART1, &USART_InitStructure);
  USART_Cmd(USART1, ENABLE);

#ifndef DEBUG_OVER_UART2
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
  USART_Cmd(USART2, ENABLE);
#endif

  // USART1 interrupt handler setup
  USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
  NVIC_EnableIRQ(USART1_IRQn);
}

// Serial buffer for UART handling of I2C addresses
#define SB_MAX_SIZE (64)
typedef struct {
  unsigned char data[SB_MAX_SIZE];  // Byte buffer
  unsigned char ind;                // Index (current location)
  unsigned char done;               // Buffer is complete (terminator reached)
  unsigned char ovf;                // Buffer has overflowed!
} SerialBuffer;
volatile SerialBuffer UART_Preamp_RxBuffer;
volatile SerialBuffer UART_Preamp_TxBuffer;

// Add a character to the serial buffer (UART)
void RxBuf_Add(volatile SerialBuffer* sb, unsigned char data_in) {
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

// Clear the serial buffer
void RxBuf_Clear(volatile SerialBuffer* sb) {
  // Clear flags
  sb->ind  = 0;
  sb->done = 0;
  sb->ovf  = 0;
  // Clear data
  int i = 0;
  while (i < SB_MAX_SIZE) {
    sb->data[i] = 0x00;
    i++;
  }
}

int main(void) {
  // VARIABLES
  uint8_t reg;          // The register that AmpliPi is reading/writing to. See
                        // "preamp_i2c_regs.xlsx"
  uint8_t  data;        // The actual value being written to the register
  uint8_t  ch, src;     // variables holding zone and source information
  uint8_t  i2c_addr;    // I2C address received via UART
  uint32_t blink;       // Counter for alternating the Standby/On LED
  uint8_t  red_on = 1;  // Used for switching the Standby/On LED

  // INIT
  init_gpio();  // UART and I2C require GPIO pins
  init_uart();  // The preamp will receive its I2C network address via UART
  init_i2c2();  // Need I2C2 initialized for the front panel functionality
                // during the address loop
  enableFrontPanel();  // setup the I2C->GPIO chip
  enablePowerBoard();  // setup the power supply chip
  enablePSU();         // turn on 9V/12V power
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality

  // RESET AND PIN SETUP
  Pin f0 = {'F', 0};  // NRST_OUT
  Pin f1 = {'F', 1};  // BOOT0_OUT
  clearPin(f0);  // Low-pulse on NRST_OUT so expansion boards are reset by the
                 // controller board
  clearPin(f1);  // Needs to be low so the subsequent preamp board doesn't start
                 // in 'Boot Mode'
  delay_ms(1);   // Hold low for 1 ms
  setPin(f0);  // Needs to be high so the subsequent preamp board is not held in
               // 'Reset Mode'

  while (1) {
    if (UART_Preamp_RxBuffer.done == 1) {
      // "A" - address identifier. Defends against potential noise on the wire
      if (UART_Preamp_RxBuffer.data[0] == 0x41) {
        // This will be the device address on I2C1.
        i2c_addr             = UART_Preamp_RxBuffer.data[1];
        UART_Preamp_TxBuffer = UART_Preamp_RxBuffer;
        // Subsequent boards. The left digit is incremented.
        // Ex. A00 -> A10 -> A20 ...
        UART_Preamp_TxBuffer.data[UART_Preamp_TxBuffer.ind - 3] =
            UART_Preamp_TxBuffer.data[UART_Preamp_TxBuffer.ind - 3] + 16;
#ifndef DEBUG_OVER_UART2
        // Send the new address to the next preamp unless UART2 is used by the
        // debugger
        USART_PutString(USART2, UART_Preamp_TxBuffer.data);
#endif
        break;
      }
      // Allow time for any extra garbage data to shift in
      delay_ms(2);
      // Only necessary for multiple runs without cycling power
      RxBuf_Clear(&UART_Preamp_RxBuffer);
    } else if (UART_Preamp_RxBuffer.ovf == 1) {
      // Clear the buffers if they overflow
      RxBuf_Clear(&UART_Preamp_RxBuffer);
      RxBuf_Clear(&UART_Preamp_TxBuffer);
    }

    // Alternate red light status once per second
    blink = millis() / 1000;
    if (red_on != (blink % 2)) {
      red_on = blink % 2;
      updateFrontPanel(red_on);
    }
  }

  // Stabilize the blinking red LED once an address is given
  updateFrontPanel(true);
  // Initialize I2C with the new address
  init_i2c1(i2c_addr);
  // Initialize each channel's volume state
  // (does not write to volume control ICs)
  initChannels();
  // Initialize each source's analog/digital state
  initSources();

  // Used as the pass through for various device data traveling to the Pi
  uint8_t msg = 0;

  // Main loop, awaiting I2C commands
  while (1) {
    // Wait for address match
    while (I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR) == RESET) {}
    I2C_ClearFlag(I2C1, I2C_FLAG_ADDR);

    // wait for reg address
    while (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET) {}
    reg = I2C_ReceiveData(I2C1);

    // Determine if the controller is trying to read/write from/to you
    int reading = 0;
    for (int i = 0; i < 100; i++) {
      reading |= I2C_GetFlagStatus(I2C1, 0x10000);
    }

    // Provide registers to be read
    if (reading == 1) {
      // During reads, the address flag is set twice
      while (I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR) == RESET) {}
      I2C_ClearFlag(I2C1, I2C_FLAG_ADDR);

      while (I2C_GetFlagStatus(I2C1, I2C_FLAG_TXIS) == RESET) {}
      switch (reg) {
        case REG_POWER_GOOD:
          msg               = readI2C2(pwr_temp_mntr_gpio);
          uint8_t pg_mask   = 0xf3;  // 1111 0011
          uint8_t pg_status = 0;

          // Gets the value of PG_12V, PG_9V, and nothing else
          msg &= ~(pg_mask);
          pg_status = msg >> 2;
          I2C_SendData(I2C1, pg_status);  // Desired value is 0x03 - both good
          break;
        case REG_FAN_STATUS:
          msg                = readI2C2(pwr_temp_mntr_gpio);
          uint8_t fan_mask   = 0x4f;  // 0100 1111
          uint8_t fan_status = 0;

          // Gets the value of FAN_ON, OVR_TMP, FAN_FAIL, and nothing else
          msg &= ~(fan_mask);
          fan_status = msg >> 4;
          I2C_SendData(I2C1, fan_status);
          break;
        case REG_EXTERNAL_GPIO:
          msg               = readI2C2(pwr_temp_mntr_gpio);
          uint8_t io_mask   = 0xbf;  // 1011 1111
          uint8_t io_status = 0;

          msg &= ~(io_mask);  // Gets the value of EXT_GPIO and nothing else
          io_status = msg >> 6;
          I2C_SendData(I2C1, io_status);
          break;
        case REG_LED_OVERRIDE:
          msg = readI2C2(front_panel);  // Current state of the front panel
          I2C_SendData(I2C1, msg);
          break;
        case REG_HV1_VOLTAGE:
          write_ADC(0x61);  // Selects HV1 (AIN0)
          msg = read_ADC();
          I2C_SendData(I2C1, msg);
          break;
        case REG_HV2_VOLTAGE:
          write_ADC(0x63);  // Selects HV2 (AIN1)
          msg = read_ADC();
          I2C_SendData(I2C1, msg);
          break;
        case REG_HV1_TEMP:
          write_ADC(0x65);  // Selects NTC1 (AIN2)
          msg = read_ADC();
          I2C_SendData(I2C1, msg);
          break;
        case REG_HV2_TEMP:
          write_ADC(0x67);  // Selects NTC2 (AIN3)
          msg = read_ADC();
          I2C_SendData(I2C1, msg);
          break;
        case REG_VERSION_MAJOR:
          I2C_SendData(I2C1, VERSION_MAJOR);
          break;
        case REG_VERSION_MINOR:
          I2C_SendData(I2C1, VERSION_MINOR);
          break;
        case REG_GIT_HASH_6_5:
          I2C_SendData(I2C1, GIT_HASH_6_5);
          break;
        case REG_GIT_HASH_4_3:
          I2C_SendData(I2C1, GIT_HASH_4_3);
          break;
        case REG_GIT_HASH_2_1:
          I2C_SendData(I2C1, GIT_HASH_2_1);
          break;
        case REG_GIT_HASH_0_D:
          // LSB is the clean/dirty status according to Git
          I2C_SendData(I2C1, GIT_HASH_0_D);
          break;
        default:
          // Return FF if a non-existent register is selected
          I2C_SendData(I2C1, 0xFF);
      }
    } else if (reading == 0) {  // Writing
      // Wait for reg data
      while (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET) {}
      data = I2C_ReceiveData(I2C1);

      // Act on command
      switch (reg) {
        case REG_SRC_AD:
          for (src = 0; src < NUM_SRCS; src++) {
            // Analog = low, Digital = high
            InputType type = data % 2 ? IT_DIGITAL : IT_ANALOG;
            configInput(src, type);
            data = data >> 1;
          }
          break;

        case REG_CH321:
          for (ch = 0; ch < 3; ch++) {
            src = data % 4;
            // Places one of the four sources on the lower three channels
            connectChannel(src, ch);
            data = data >> 2;
          }
          break;

        case REG_CH654:
          for (ch = 3; ch < 6; ch++) {
            src = data % 4;
            // Places one of the four sources on the upper three channels
            connectChannel(src, ch);
            data = data >> 2;
          }
          break;

        case REG_MUTE:
          for (ch = 0; ch < 6; ch++) {
            if (data % 2) {
              mute(ch);
            } else {
              unmute(ch);
            }
            data = data >> 1;
          }
          break;

        case REG_STANDBY:
          // Writes to this register now directly handle standby and audio power
          if (data == 0) {
            standby();
          } else {
            unstandby();
          }
          break;

        case REG_VOL_CH1:
        case REG_VOL_CH2:
        case REG_VOL_CH3:
        case REG_VOL_CH4:
        case REG_VOL_CH5:
        case REG_VOL_CH6:
          ch = reg - REG_VOL_CH1;
          setChannelVolume(ch, data);
          break;
        case REG_FAN_STATUS:
          // Writing to this register is only used for turning the fan on 100%
          msg               = readI2C2(pwr_temp_mntr_gpio);
          uint8_t full_mask = 0x80;  // 1000 0000

          if (data == 0) {  // Set FAN_ON to ON/OFF
            msg &= ~(full_mask);
          } else if (data == 1) {
            msg |= full_mask;
          }
          writeI2C2(pwr_temp_mntr_olat, msg);
          break;
        case REG_EXTERNAL_GPIO:
          msg               = readI2C2(pwr_temp_mntr_gpio);
          uint8_t gpio_mask = 0x40;  // 0100 0000

          if (data == 0) {  // Set EXT_GPIO to 0 or 1
            msg &= ~(gpio_mask);
          } else if (data == 1) {
            msg |= gpio_mask;
          }
          writeI2C2(pwr_temp_mntr_olat, msg);
          break;
        case REG_LED_OVERRIDE:
          writeI2C2(front_panel, data);  // Full front panel control
          break;
        case REG_EXPANSION:
          // NRST_OUT
          if (data & 0x01) {
            setPin(f0);
          } else {
            clearPin(f0);
          }
          // BOOT0_OUT
          if (data & 0x02) {
            setPin(f1);
          } else {
            clearPin(f1);
          }

          // Allow UART messages to be forwarded to expansion units
          uart_passthrough_ = (data & 0x04) == 0x04;

          // Expansion UART (USART2) interrupt enable
          if (data & 0x08) {
            USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
            NVIC_EnableIRQ(USART2_IRQn);
          } else {
            USART_ITConfig(USART2, USART_IT_RXNE, DISABLE);
            NVIC_DisableIRQ(USART2_IRQn);
          }
          break;
        case 0x99:
          // Free write to the ADC for debug purposes
          // (writing to setup byte is possible)
          write_ADC(data);
          break;
        default:
          // do nothing
          break;
      }
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
  // delay time in ms. Increase to send out message more slowly. At 9600 baud,
  // UART sends roughly 1 char each millisecond
  int dt = 2;
  while (*str != 0) {
    USART_SendData(USARTx, *str);
    str++;
    delay_ms(dt);
  }
  delay_ms(dt);
  //	USART_SendData(USARTx, 0x0D); // Use these for terminal comms
  //	delay_ms(dt);                 // The message from ctrl bd should
  //	USART_SendData(USARTx, 0x0A); // already have \r\n at the end
  //	delay_ms(dt);
}

// Handles the interrupt on UART data reception
void USART1_IRQHandler(void) {
  if (USART_GetITStatus(USART1, USART_IT_RXNE) != RESET) {
    uint16_t m = USART_ReceiveData(USART1);
    if (uart_passthrough_) {
      USART_SendData(USART2, m);
    } else {
      RxBuf_Add(&UART_Preamp_RxBuffer, (uint8_t)m);
    }
  }
}

void USART2_IRQHandler(void) {
  if (USART_GetITStatus(USART2, USART_IT_RXNE) != RESET) {
    uint16_t m = USART_ReceiveData(USART2);
    USART_SendData(USART1, m);
  }
}
