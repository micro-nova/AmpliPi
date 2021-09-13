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

#include "ports.h"

void CtrlI2CInit(uint8_t addr);
bool CtrlI2CAddrMatch();
void CtrlI2CTransact(Pin exp_nrst, Pin exp_boot0);

bool UartPassthroughEnabled();

#endif /* CTRL_I2C_H_ */
