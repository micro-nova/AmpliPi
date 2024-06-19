/*
 * AmpliPi Home Audio
 * Copyright (C) 2021-2024 MicroNova LLC
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

#pragma once

#include <stdint.h>

// The output mask defines which bits of the GPIO expander are configured as outputs.
#define PWR_GPIO_OUT_MASK 0x83

// Power Board Revisions and GPIO Expander Connections:
//
// Rev | GP0   | GP1    | GP2    | GP3    | GP4    | GP5    | GP6      | GP7    | Preamp Rev4+? |
// ----+-------+--------+--------+--------+--------+--------+----------+--------+---------------+
// 2.A | EN_9V | EN_12V | PG_9V  | PG_12V | FAN_OK | TMP_OK | EXT_GPIO | FAN_ON |            No |
// 3.B |       | EN_12V |        | PG_12V | FAN_OK | TMP_OK |          | FAN_ON |            No |
// 4.A |       |        | PG_5VA | PG_12V |        |        |          | FAN_ON |        Yes/No |
// 6.A |       |        | PG_5VA | PG_12V |  PG_9V | PG_5VD |          | FAN_ON |           Yes |

typedef union {
  struct {
    uint8_t en_9v      : 1;  // Only on Power Board 1.X
    uint8_t en_12v     : 1;
    uint8_t pg_9v      : 1;  // Only on Power Board 1.X
    uint8_t pg_12v     : 1;
    uint8_t fan_fail_n : 1;
    uint8_t ovr_tmp_n  : 1;
    uint8_t ext_gpio   : 1;  // Only on Power Board 2.X
    uint8_t fan_on     : 1;
  };
  struct {
    uint8_t gp0    : 1;  // Unused
    uint8_t gp1    : 1;  // Unused
    uint8_t pg_5va : 1;
    uint8_t pg_12v : 1;
    uint8_t pg_9v  : 1;
    uint8_t pg_5vd : 1;
    uint8_t gp6    : 1;  // Unused
    uint8_t fan_on : 1;
  } v4;
  uint8_t data;
} GpioReg;

void    set_pwr_gpio(GpioReg val);
GpioReg get_pwr_gpio();

// Inputs
bool pg_9v();
bool pg_12v();
bool pg_5va();
bool pg_5vd();
bool fan_fail_max6644();
bool over_temp_max6644();

// Outputs
bool get_9v_en();
bool get_12v_en();
void set_fan_on(bool on);
