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

#include "fans.h"

#include <stdbool.h>

#include "systick.h"

// 2-wire fan control PWM works well around 30 Hz
// 1000 Hz systick / 32 = 31.25 Hz
#define FAN_PERIOD_MS 32

#define C_TO_Q7_8(x) ((int16_t)x << 8)

// Amplifiers: TDA7492E max temp = 85C
#define TEMP_AMP_THRESH_OFF_C     40  // Below this fans turn off
#define TEMP_AMP_THRESH_LOW_C     45  // Above this turn fans on 30%
#define TEMP_AMP_THRESH_HIGH_C    60  // Above this fans turn on 100%
#define TEMP_AMP_THRESH_OVR_C     70  // Above this warn of overtemp
#define TEMP_AMP_THRESH_OFF_Q7_8  C_TO_Q7_8(TEMP_AMP_THRESH_OFF_C)
#define TEMP_AMP_THRESH_LOW_Q7_8  C_TO_Q7_8(TEMP_AMP_THRESH_LOW_C)
#define TEMP_AMP_THRESH_HIGH_Q7_8 C_TO_Q7_8(TEMP_AMP_THRESH_HIGH_C)
#define TEMP_AMP_THRESH_OVR_Q7_8  C_TO_Q7_8(TEMP_AMP_THRESH_OVR_C)

// Power supply: MEAN WELL LRS-350 max temp = 70C, fans on at 50 C
#define TEMP_PSU_THRESH_OFF_C     35  // Below this fans turn off
#define TEMP_PSU_THRESH_LOW_C     40  // Above this turn fans on 30%
#define TEMP_PSU_THRESH_HIGH_C    55  // Above this fans turn on 100%
#define TEMP_PSU_THRESH_OVR_C     70  // Above this warn of overtemp
#define TEMP_PSU_THRESH_OFF_Q7_8  C_TO_Q7_8(TEMP_PSU_THRESH_OFF_C)
#define TEMP_PSU_THRESH_LOW_Q7_8  C_TO_Q7_8(TEMP_PSU_THRESH_LOW_C)
#define TEMP_PSU_THRESH_HIGH_Q7_8 C_TO_Q7_8(TEMP_PSU_THRESH_HIGH_C)
#define TEMP_PSU_THRESH_OVR_Q7_8  C_TO_Q7_8(TEMP_PSU_THRESH_OVR_C)

// Raspberry Pi: BCM2837 max temp = 85C, CM3+ max temp = 80C
#define TEMP_RPI_THRESH_OFF_C     55  // Below this fans turn off
#define TEMP_RPI_THRESH_LOW_C     60  // Above this turn fans on 30%
#define TEMP_RPI_THRESH_HIGH_C    80  // Above this fans turn on 100%
#define TEMP_RPI_THRESH_OVR_C     85  // Above this warn of overtemp
#define TEMP_RPI_THRESH_OFF_Q7_8  C_TO_Q7_8(TEMP_RPI_THRESH_OFF_C)
#define TEMP_RPI_THRESH_LOW_Q7_8  C_TO_Q7_8(TEMP_RPI_THRESH_LOW_C)
#define TEMP_RPI_THRESH_HIGH_Q7_8 C_TO_Q7_8(TEMP_RPI_THRESH_HIGH_C)
#define TEMP_RPI_THRESH_OVR_Q7_8  C_TO_Q7_8(TEMP_RPI_THRESH_OVR_C)

/* Updates the fan state based on the current temp
 *
 * Inputs
 *    amp1_temp: Temperature of the first amplifier heatsink
 *    amp2_temp: Temperature of the second amplifier heatsink
 *    psu_temp:  Temperature of the high-voltage PSU
 *    pi_temp:   Temperature of the Raspberry Pi
 *    force:     Force fans on 100%
 * All temps are in Q7.8 fixed-point format.
 *
 * Returns the current fan state.
 */
FanState* updateFans(int16_t amp_temp1, int16_t amp_temp2, int16_t psu_temp,
                     int16_t rpi_temp, bool force) {
// Minimum fan PWM duty value based on the period. ~30% duty is the min,
// round up to the nearest integer.
#define MINVAL ((int32_t)((0.3 * (FAN_PERIOD_MS - .01)) + 1))

  static FanState state = {
      .ctrl     = FAN_CTRL_MAX6644,
      .ovr_temp = false,
      .duty_f7  = 0,
  };

  // The two amp heatsinks can be combined by simply taking the max
  int16_t amp_temp = amp_temp1 > amp_temp2 ? amp_temp1 : amp_temp2;

  // First, determine hardware fan control capabilities
  // So far, no Power Boards (2.A) with a MAX6644 have used HV2/NTC2.
  // If either of those inputs measures a valid temp, then assume
  // no MAX6644 fan control IC is present, and thermisters are.
  state.ctrl = amp_temp ? FAN_CTRL_PWM : FAN_CTRL_MAX6644;

  state.ovr_temp = amp_temp > TEMP_AMP_THRESH_OVR_Q7_8 ||
                   psu_temp > TEMP_PSU_THRESH_OVR_Q7_8 ||
                   rpi_temp > TEMP_RPI_THRESH_OVR_Q7_8;

  /* Fan temp -> duty regions:
   *        T <= Toff | duty = 0
   * Toff < T <= Ton  | duty = duty (unchanged)
   * Ton  < T <= Tmax | duty = [38, 128) ([0.3, 1.0) in Q1.7)
   * Tmax < T         | duty = 128 (1.0 in Q1.7)
   */

  if (force) {
    // 100% fans, 1.0 in UQ1.7
    state.duty_f7 = 1 << 7;
  } else if (state.ctrl == FAN_CTRL_MAX6644) {
    // Fans are controlled by the MAX6644 fan controller
    state.duty_f7 = 0;
  } else if (amp_temp <= TEMP_AMP_THRESH_OFF_Q7_8 &&
             psu_temp <= TEMP_PSU_THRESH_OFF_Q7_8 &&
             rpi_temp <= TEMP_RPI_THRESH_OFF_Q7_8) {
    // Cool enough that fans can be left off
    state.duty_f7 = 0;
  } else {
    // Calculate duty cycles for each temp
    // measurement in Q7.8 format, 1.0 = 100%
    int16_t amp_duty = (amp_temp - TEMP_AMP_THRESH_LOW_Q7_8) /
                       (TEMP_AMP_THRESH_HIGH_C - TEMP_AMP_THRESH_LOW_C);
    int16_t psu_duty = (psu_temp - TEMP_PSU_THRESH_LOW_Q7_8) /
                       (TEMP_PSU_THRESH_HIGH_C - TEMP_PSU_THRESH_LOW_C);
    int16_t rpi_duty = (rpi_temp - TEMP_RPI_THRESH_LOW_Q7_8) /
                       (TEMP_RPI_THRESH_HIGH_C - TEMP_RPI_THRESH_LOW_C);

    // Take the max duty cycle requested.
    int16_t max_duty1   = amp_duty > psu_duty ? amp_duty : psu_duty;
    int16_t max_duty_f8 = max_duty1 > rpi_duty ? max_duty1 : rpi_duty;

    if (max_duty_f8 > (1 << 8)) {  // 1.0 in Q7.8
      // 100% fans, 1.0 in UQ1.7
      state.duty_f7 = 1 << 7;
    } else if (max_duty_f8 > 0) {
      // Fans partially on, convert [0.0,1.0] in Q7.8 to [0.3,1.0] in UQ1.7
      const int32_t scale_f16 = (1.0 - 0.3) * (1 << 16);
      const int32_t min_f16   = 0.3 * (1 << 24);
      int32_t       duty_f24  = scale_f16 * max_duty_f8 + min_f16;
      state.duty_f7           = (uint8_t)(duty_f24 >> (24 - 7));
    } else {
      // Hysteresis region, use old duty cycle (but cap at 30%)
      const uint8_t min_f8 = 0.3 * (1 << 7);
      state.duty_f7        = state.duty_f7 > min_f8 ? min_f8 : state.duty_f7;
    }
  }

  return &state;
}

/* Determines the GPIO expander's FAN_ON pin state.
 * Call every millisecond tick.
 *
 * Inputs
 *    duty_f7: Fan duty cycle in the range [0,1] in UQ1.7 format
 *
 * Returns boolean FAN_ON pin state
 */
bool getFanOnFromDuty(uint8_t duty_f7) {
  uint32_t duty_ms = FAN_PERIOD_MS * duty_f7 / (1 << 7);
  uint32_t ms32    = millis() & (FAN_PERIOD_MS - 1);
  return ms32 < duty_ms;
}
