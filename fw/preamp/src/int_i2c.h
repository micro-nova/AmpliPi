/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * Internal I2C bus control/status
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

#include "eeprom.h"

bool get_rev4();

void    eeprom_write_request(const EepromPage* const data);
void    eeprom_read_request(const EepromCtrl ctrl);
uint8_t eeprom_get_ctrl();
uint8_t eeprom_get_data(uint8_t addr);

void    initInternalI2C();
void    updateInternalI2C(bool initialized);
bool    isDPotSMBus();
uint8_t isInternalI2CDevPresent(uint8_t addr);
