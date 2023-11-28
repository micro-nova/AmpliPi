/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * Base I2C functionality
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

typedef uint8_t I2CDev;

typedef struct {
  I2CDev  dev;
  uint8_t reg;
} I2CReg;

void initI2C1(uint8_t addr);
void initI2C2();
void deinitI2C2();

bool i2c_detect(uint8_t addr);

uint32_t writeByteI2C2(I2CDev dev, uint8_t val);
uint8_t  readRegI2C2(I2CReg r);
uint32_t writeRegI2C2(I2CReg r, uint8_t data);
