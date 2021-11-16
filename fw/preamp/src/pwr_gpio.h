/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Power Board GPIO status and control
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

#ifndef PWR_GPIO_H_
#define PWR_GPIO_H_

#include <stdbool.h>
#include <stdint.h>

#define PWR_GPIO_OUT_MASK 0x83

typedef union {
  struct {
    uint8_t en_9v      : 1;  // Only on Power Board 1.X
    uint8_t en_12v     : 1;
    uint8_t pg_9v      : 1;  // Only on Power Board 1.X
    uint8_t pg_12v     : 1;
    uint8_t fan_fail_n : 1;
    uint8_t ovr_tmp_n  : 1;
    uint8_t pg_5v      : 1;  // Planned for Power Board 4.A
    uint8_t fan_on     : 1;
  };
  uint8_t data;
} GpioReg;

void    setPwrGpio(GpioReg val);
GpioReg getPwrGpio();

// Inputs
bool pg9v();
bool pg12v();
bool fanFailMax6644();
bool overTempMax6644();

// Outputs
// TODO: Are all of these necessary?
void set9vEn(bool en);
bool get9vEn();
void set12vEn(bool en);
bool get12vEn();
void setFanOn(bool on);
bool getFanOn();

#endif /* PWR_GPIO_H_ */
