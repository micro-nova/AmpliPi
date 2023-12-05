/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * EEPROM definitions.
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

#pragma once

#include <stdint.h>

// TODO: constexpr. Waiting on EDG parser to support C23 better, see
// https://www.edg.com/c23_features.html
#define EEPROM_PAGE_SIZE     16
#define EEPROM_I2C_ADDR_BASE 0xA0

typedef union {
  uint8_t byte;
  struct {
    uint8_t rd_wrn   : 1;  // Read = 1, write = 0.
    uint8_t i2c_addr : 3;
    uint8_t page_num : 4;
  };
} EepromCtrl;

typedef struct {
  EepromCtrl ctrl;
  uint8_t    data[EEPROM_PAGE_SIZE];
} EepromPage;
static_assert(sizeof(EepromPage) == EEPROM_PAGE_SIZE + 1, "Error: Eeprom wrong size.");
