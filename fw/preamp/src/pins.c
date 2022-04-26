/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * Pin definitions and functions
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

#include "pins.h"

#include "audio.h"  // NUM_ZONES, NUM_SRCS
#include "stm32f0xx.h"

/*
#define pTX1 GPIO_Pin_9   // PA9
#define pRX1 GPIO_Pin_10  // PA10
#define pTX2 GPIO_Pin_14  // PA14
#define pRX2 GPIO_Pin_15  // PA15

#define pSCL     GPIO_Pin_6   // PB6
#define pSDA     GPIO_Pin_7   // PB7
#define pSCL_VOL GPIO_Pin_10  // PB10
#define pSDA_VOL GPIO_Pin_11  // PB11
*/

static GPIO_TypeDef* getPort(Pin pp) {
  switch (pp.port) {
    case 'A':
      return GPIOA;
    case 'B':
      return GPIOB;
    case 'C':
      return GPIOC;
    case 'D':
      return GPIOD;
    case 'F':
      return GPIOF;
    default:
      return 0;
  }
}

// Enable pin mapping for each zone's four sources
// Each zone can enable all or none of its sources. This firmware currently
// allows only one to be enabled at a time
const Pin zone_src_[NUM_ZONES][NUM_SRCS] = {
    {{'A', 3}, {'F', 5}, {'A', 4}, {'F', 4}},
    {{'A', 5}, {'A', 7}, {'C', 4}, {'A', 6}},
    {{'C', 5}, {'B', 1}, {'B', 2}, {'B', 0}},
    {{'C', 1}, {'B', 8}, {'C', 11}, {'C', 0}},
    {{'F', 7}, {'B', 3}, {'C', 12}, {'B', 5}},
    {{'C', 10}, {'A', 2}, {'A', 1}, {'A', 0}},
};

const Pin zone_mute_[NUM_ZONES] = {
    {'B', 14}, {'C', 6}, {'C', 8}, {'A', 8}, {'A', 12}, {'F', 6},
};

const Pin zone_standby_[NUM_ZONES] = {
    {'B', 12}, {'B', 13}, {'B', 15}, {'C', 7}, {'C', 9}, {'A', 11},
};

// Analog is first column, digital is second column
const Pin src_ad_[NUM_SRCS][2] = {
    {{'B', 4}, {'D', 2}},
    {{'B', 9}, {'C', 13}},
    {{'C', 15}, {'C', 14}},
    {{'C', 2}, {'C', 3}},
};

const Pin exp_nrst_  = {'F', 0};
const Pin exp_boot0_ = {'F', 1};

const Pin uart1_tx_ = {'A', 9};
const Pin uart1_rx_ = {'A', 10};
const Pin uart2_tx_ = {'A', 14};
const Pin uart2_rx_ = {'A', 15};

const Pin i2c1_scl_ = {'B', 6};
const Pin i2c1_sda_ = {'B', 7};
const Pin i2c2_scl_ = {'B', 10};
const Pin i2c2_sda_ = {'B', 11};

void initPins() {
  // Enable peripheral clocks for GPIO ports
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOC, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOD, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);

  // Setup IO pin directions PORT A
  GPIO_InitTypeDef aInit;
  aInit.GPIO_Pin = (1 << zone_src_[0][0].pin) | (1 << zone_src_[0][2].pin) |
                   (1 << zone_src_[1][0].pin) | (1 << zone_src_[1][1].pin) |
                   (1 << zone_src_[1][3].pin) | (1 << zone_src_[5][1].pin) |
                   (1 << zone_src_[5][2].pin) | (1 << zone_src_[5][3].pin) |
                   (1 << zone_mute_[3].pin) | (1 << zone_mute_[4].pin) |
                   (1 << zone_standby_[5].pin);
  aInit.GPIO_Mode  = GPIO_Mode_OUT;
  aInit.GPIO_Speed = GPIO_Speed_2MHz;
  aInit.GPIO_OType = GPIO_OType_PP;
  aInit.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOA, &aInit);

  // Setup IO pin directions PORT B
  GPIO_InitTypeDef bInit;
  bInit.GPIO_Pin = (1 << zone_src_[2][1].pin) | (1 << zone_src_[2][2].pin) |
                   (1 << zone_src_[2][3].pin) | (1 << zone_src_[3][1].pin) |
                   (1 << zone_src_[4][1].pin) | (1 << zone_src_[4][3].pin) |
                   (1 << zone_mute_[0].pin) | (1 << zone_standby_[0].pin) |
                   (1 << zone_standby_[1].pin) | (1 << zone_standby_[2].pin) |
                   (1 << src_ad_[0][0].pin) | (1 << src_ad_[1][0].pin);
  bInit.GPIO_Mode  = GPIO_Mode_OUT;
  bInit.GPIO_Speed = GPIO_Speed_2MHz;
  bInit.GPIO_OType = GPIO_OType_PP;
  bInit.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOB, &bInit);

  // Setup IO pin directions PORT C
  GPIO_InitTypeDef cInit;
  cInit.GPIO_Pin = (1 << zone_src_[1][2].pin) | (1 << zone_src_[2][0].pin) |
                   (1 << zone_src_[3][0].pin) | (1 << zone_src_[3][2].pin) |
                   (1 << zone_src_[3][3].pin) | (1 << zone_src_[4][2].pin) |
                   (1 << zone_src_[5][0].pin) | (1 << zone_mute_[1].pin) |
                   (1 << zone_mute_[2].pin) | (1 << zone_standby_[3].pin) |
                   (1 << zone_standby_[4].pin) | (1 << src_ad_[2][0].pin) |
                   (1 << src_ad_[3][0].pin) | (1 << src_ad_[1][1].pin) |
                   (1 << src_ad_[2][1].pin) | (1 << src_ad_[3][1].pin);
  cInit.GPIO_Mode  = GPIO_Mode_OUT;
  cInit.GPIO_Speed = GPIO_Speed_2MHz;
  cInit.GPIO_OType = GPIO_OType_PP;
  cInit.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOC, &cInit);

  // Setup IO pin directions PORT D
  GPIO_InitTypeDef dInit = {
      .GPIO_Pin   = 1 << src_ad_[0][1].pin,
      .GPIO_Mode  = GPIO_Mode_OUT,
      .GPIO_Speed = GPIO_Speed_2MHz,
      .GPIO_OType = GPIO_OType_PP,
      .GPIO_PuPd  = GPIO_PuPd_NOPULL,
  };
  GPIO_Init(GPIOD, &dInit);

  // Setup IO pin directions PORT F
  GPIO_InitTypeDef fInit;
  fInit.GPIO_Pin = (1 << zone_src_[0][1].pin) | (1 << zone_src_[0][3].pin) |
                   (1 << zone_src_[4][0].pin) | (1 << zone_mute_[5].pin) |
                   (1 << exp_nrst_.pin) | (1 << exp_boot0_.pin);
  fInit.GPIO_Mode  = GPIO_Mode_OUT;
  fInit.GPIO_Speed = GPIO_Speed_2MHz;
  fInit.GPIO_OType = GPIO_OType_PP;
  fInit.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOF, &fInit);

  // Configure special function pins
  configUARTPins();
  configI2C1Pins();
  configI2C2PinsAsGPIO();
}

void configUARTPins() {
  // Connect pins to alternate function for UART1 and UART2
  GPIO_PinAFConfig(getPort(uart1_tx_), uart1_tx_.pin, GPIO_AF_1);
  GPIO_PinAFConfig(getPort(uart1_rx_), uart1_rx_.pin, GPIO_AF_1);
  GPIO_PinAFConfig(getPort(uart2_tx_), uart2_tx_.pin, GPIO_AF_1);
  GPIO_PinAFConfig(getPort(uart2_rx_), uart2_rx_.pin, GPIO_AF_1);

  // Config UART1 and UART2 GPIO pins
  GPIO_InitTypeDef uartInit = {
      .GPIO_Pin = (1 << uart1_tx_.pin) | (1 << uart1_rx_.pin) |
                  (1 << uart2_tx_.pin) | (1 << uart2_rx_.pin),
      .GPIO_Mode  = GPIO_Mode_AF,
      .GPIO_Speed = GPIO_Speed_2MHz,
      .GPIO_OType = GPIO_OType_PP,
      .GPIO_PuPd  = GPIO_PuPd_UP,
  };
  GPIO_Init(getPort(uart1_tx_), &uartInit);
}

void configI2C1Pins() {
  // Connect pins to alternate function for I2C1 and I2C2
  GPIO_PinAFConfig(getPort(i2c1_scl_), i2c1_scl_.pin, GPIO_AF_1);
  GPIO_PinAFConfig(getPort(i2c1_sda_), i2c1_sda_.pin, GPIO_AF_1);

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C = {
      .GPIO_Pin   = (1 << i2c1_scl_.pin) | (1 << i2c1_sda_.pin),
      .GPIO_Mode  = GPIO_Mode_AF,
      .GPIO_Speed = GPIO_Speed_2MHz,
      .GPIO_OType = GPIO_OType_OD,
      .GPIO_PuPd  = GPIO_PuPd_NOPULL,
  };
  GPIO_Init(getPort(i2c1_scl_), &GPIO_InitStructureI2C);
}

void configI2C2Pins() {
  // Connect pins to alternate function for I2C1 and I2C2
  GPIO_PinAFConfig(getPort(i2c2_scl_), i2c2_scl_.pin, GPIO_AF_1);
  GPIO_PinAFConfig(getPort(i2c2_sda_), i2c2_sda_.pin, GPIO_AF_1);

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C = {
      .GPIO_Pin   = (1 << i2c2_scl_.pin) | (1 << i2c2_sda_.pin),
      .GPIO_Mode  = GPIO_Mode_AF,
      .GPIO_Speed = GPIO_Speed_2MHz,
      .GPIO_OType = GPIO_OType_OD,
      .GPIO_PuPd  = GPIO_PuPd_NOPULL,
  };
  GPIO_Init(getPort(i2c2_scl_), &GPIO_InitStructureI2C);
}

void configI2C2PinsAsGPIO() {
  // Default pins High-Z
  writePin(i2c2_scl_, true);
  writePin(i2c2_sda_, true);

  // Config I2C2 GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C = {
      .GPIO_Pin   = (1 << i2c2_scl_.pin) | (1 << i2c2_sda_.pin),
      .GPIO_Mode  = GPIO_Mode_OUT,
      .GPIO_Speed = GPIO_Speed_2MHz,
      .GPIO_OType = GPIO_OType_OD,
      .GPIO_PuPd  = GPIO_PuPd_NOPULL,
  };
  GPIO_Init(getPort(i2c2_scl_), &GPIO_InitStructureI2C);
}

void writePin(Pin pp, bool set) {
  GPIO_TypeDef* port = getPort(pp);
  // getPort(pp)->BSRR = (1 << pp.pin)
  if (set) {
    // Lower 16 bits of BSRR used for setting, upper for clearing
    port->BSRR = 1 << pp.pin;
  } else {
    // Lower 16 bits of BRR used for clearing
    port->BRR = 1 << pp.pin;
  }
}

bool readPin(Pin pp) {
  GPIO_TypeDef* port = getPort(pp);
  if (port->IDR & (1 << pp.pin)) {
    return true;
  } else {
    return false;
  }
}
