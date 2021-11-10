/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Fan control based on temperatures
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

#ifndef FANS_H_
#define FANS_H_

#include <stdbool.h>
#include <stdint.h>

// Possible fan control methods:
// - MAX6644 (5 developer units with Power Board 2.A)
// - Thermistors with FAN_ON PWM control (Power Board 3.A)
// - Thermistors with DPOT linear voltage control (Power Board 4.A)
// - Overridden (forced on) by the Pi
typedef enum
{
  FAN_CTRL_MAX6644,
  FAN_CTRL_PWM,
  FAN_CTRL_LINEAR,
  FAN_CTRL_FORCED,
} FanCtrl;

typedef struct {
  FanCtrl ctrl;      // Control method currently in use
  bool    ovr_temp;  // Temp too high
  uint8_t duty_f7;   // Fan duty cycle in the range [0,1] in UQ1.7 format
  uint8_t dpot_val;  // Digital pot setting that controls power supply voltage
  uint8_t volts_f4;  // Fan power supply voltage in UQ4.4 format
} FanState;

FanState* updateFans(int16_t amp_temp, int16_t psu_temp, int16_t rpi_temp,
                     bool force, bool thermistors, bool linear);
bool      getFanOnFromDuty(uint8_t duty_f7);

#endif /* FANS_H_ */
