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

typedef enum {
  // I2C1, base address 0x40005400, 1kB address space.
  i2c_ctrl = 0,  // i2c_ctrl is the I2C bus connected to the Controller Board. The STM32 is a slave.

  // I2C2, base address 0x40005800, 1kB address space.
  i2c_int = 1,  // i2c_int is the I2C bus internal to a single AmpliPi unit. The STM32 is a master.
} i2c_bus_t;

typedef uint8_t I2CDev;

typedef struct {
  I2CDev  dev;
  uint8_t reg;
} I2CReg;

void i2c_init(i2c_bus_t bus, uint8_t addr);
void i2c_deinit(i2c_bus_t bus);

bool i2c_detect(uint8_t addr);

uint32_t writeByteI2C2(I2CDev dev, uint8_t val);
uint8_t  readRegI2C2(I2CReg r);
uint32_t writeRegI2C2(I2CReg r, uint8_t data);
