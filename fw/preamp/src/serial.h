/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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

#pragma once

#include <stdint.h>

typedef enum {
  // USART1, base address 0x40013800, 1kB address space.
  serial_ctrl = 0,  // serial_ctrl is the USART connected to the Controller Board.

  // USART2, base address 0x40004400, 1kB address space.
  serial_exp = 1,  // serial_exp is the USART connected to a Zone Expander.
} serial_port_t;

void setUartPassthrough(bool passthrough);
bool getUartPassthrough();
void serial_init(serial_port_t port);

// Returns new I2C address if one was received via USART1, otherwise 0
void    sendAddressToSlave(uint8_t i2c_addr);
uint8_t getI2C1Address();
