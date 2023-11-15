/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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

#include "stm32f0xx.h"

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
    {{'A', 3}, {'F', 5}, {'A', 4}, {'F', 4}},  {{'A', 5}, {'A', 7}, {'C', 4}, {'A', 6}},
    {{'C', 5}, {'B', 1}, {'B', 2}, {'B', 0}},  {{'C', 1}, {'B', 8}, {'C', 11}, {'C', 0}},
    {{'F', 7}, {'B', 3}, {'C', 12}, {'B', 5}}, {{'C', 10}, {'A', 2}, {'A', 1}, {'A', 0}},
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

/* Configure the internal I2C pins (I2C2) as either I2C or GPIO.
 * @param gpio: Set to true to configure as I2C alternate function, false for GPIO.
 */
void config_int_i2c_pins(bool i2c) {
  if (i2c) {
    // Config I2C pins as AF1
    GPIOB->MODER  = 0x55A5A555;  // Set Port B pins 11,10 as alternative function.
    GPIOB->AFR[1] = 0x00001100;  // Set Port B pins 11,10 as AF1, rest as AF0
  } else {
    // Default pins High-Z
    write_pin(i2c2_scl_, true);
    write_pin(i2c2_sda_, true);

    // Config I2C2 pins as GPIO
    GPIOB->MODER  = 0x5555A555;  // Set Port B pins 11,10 as general-purpose output.
    GPIOB->AFR[1] = 0x00000000;  // Set Port B pins 15:8 as AF0
  }
}

// Initialize all pins to proper GPIO/Alternative Function state.
void init_pins() {
  // Enable peripheral clocks for GPIO ports
  RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN | RCC_AHBENR_GPIOCEN | RCC_AHBENR_GPIODEN |
                 RCC_AHBENR_GPIOFEN;

  // Setup PORT A pins used as GPIO
  //  9: UART1 TX - AF1
  // 10: UART1 RX - AF1, pullup
  // 13: SWDIO    - input, pullup
  // 14: UART2 TX - AF1
  // 15: UART2 RX - AF1, pullup
  GPIOA->OSPEEDR = 0;           // Set to low speed.
  GPIOA->OTYPER  = 0;           // Set to push-pull.
  GPIOA->MODER   = 0xA1695555;  // Set as general purpose output or alternative function.
  GPIOA->PUPDR   = 0x44100000;  // Set 15,13,10 to pullup, rest to no pullup or pulldown.

  // Setup Port A pins with alternate functions.
  GPIOA->AFR[1] = 0x11000110;  // Set Port A pins 15,14,10,9 as AF1 for UART, rest as AF0

  // Setup PORT B pins used as GPIO
  //  6, 7: I2C1 - AF1, open-drain
  // 10,11: I2C2 - Leave as GPIO initially, open-drain
  GPIOB->OSPEEDR = 0;           // Set to low speed.
  GPIOB->OTYPER  = 0x0CC0;      // Set to push-pull for GPIO, open-drain for I2C.
  GPIOB->MODER   = 0x5555A555;  // Set as general purpose output or alternative function.
  GPIOB->PUPDR   = 0;           // Set to no pullup or pulldown.

  // Setup Port B pins with alternate functions.
  GPIOB->AFR[0] = 0x11000000;  // Set Port B pins 7,6 as AF1 for I2C1, rest as AF0
  GPIOB->AFR[1] = 0;           // Set Port B pins 15:8 as AF0

  // Default I2C2 pins High-Z
  write_pin(i2c2_scl_, true);
  write_pin(i2c2_sda_, true);

  // Setup PORT C pins used as GPIO
  GPIOC->OSPEEDR = 0;           // Set to low speed.
  GPIOC->OTYPER  = 0;           // Set to push-pull.
  GPIOC->MODER   = 0x55555555;  // Set as general purpose output.
  GPIOC->PUPDR   = 0;           // Set to no pull-up or pull-down.

  // Setup PORT D pins used as GPIO (only 1 port D pin exists)
  GPIOD->OSPEEDR = 0;           // Set to low speed.
  GPIOD->OTYPER  = 0;           // Set to push-pull.
  GPIOD->MODER   = 0x00000010;  // Set as general purpose output.
  GPIOD->PUPDR   = 0;           // Set to no pull-up or pull-down.

  // Setup PORT F pins used as GPIO (only 6 port F pins exist)
  // 0, 1: NRST_OUT, BOOT0_OUT
  GPIOF->OSPEEDR = 0;           // Set to low speed.
  GPIOF->OTYPER  = 0x0001;      // Set to push-pull, except open-drain for NRST_OUT.
  GPIOF->MODER   = 0x00005505;  // Set as general purpose output.
  GPIOF->PUPDR   = 0x00000001;  // Set to no pull-up or pull-down, except pullup for NRST_OUT.
}

void write_pin(Pin pp, bool set) {
  GPIO_TypeDef* port = getPort(pp);
  if (set) {
    // Lower 16 bits of BSRR used for setting, upper for clearing
    port->BSRR = 1 << pp.pin;
  } else {
    // Lower 16 bits of BRR used for clearing
    port->BRR = 1 << pp.pin;
  }
}

bool read_pin(Pin pp) {
  GPIO_TypeDef* port = getPort(pp);
  if (port->IDR & (1 << pp.pin)) {
    return true;
  } else {
    return false;
  }
}
