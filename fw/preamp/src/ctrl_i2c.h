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

#ifndef CTRL_I2C_H_
#define CTRL_I2C_H_

#include <stdbool.h>
#include <stdint.h>

typedef union {
  struct {
    uint8_t pg_9v    : 1;  // R
    uint8_t en_9v    : 1;  // R/W
    uint8_t pg_12v   : 1;  // R
    uint8_t en_12v   : 1;  // R/W
    uint8_t reserved : 4;
  };
  uint8_t data;
} PwrReg;

typedef union {
  struct {
    uint8_t ctrl : 2;      // R/W - Fan control method currently in use.
                           //       0b11 = force fans on.
    uint8_t on       : 1;  // R   - Fans status
    uint8_t ovr_tmp  : 1;  // R   - Unit over dangerous temperature threshold
    uint8_t fail     : 1;  // R   - Fan fail detection (Power Board 2.A only)
    uint8_t reserved : 3;
  };
  uint8_t data;
} FanReg;

typedef union {
  struct {
    uint8_t nrst             : 1;
    uint8_t boot0            : 1;
    uint8_t uart_passthrough : 1;
    uint8_t reserved         : 5;
  };
  uint8_t data;
} ExpansionReg;

void ctrlI2CInit();
bool ctrlI2CAddrMatch();
void ctrlI2CTransact();

#endif /* CTRL_I2C_H_ */
