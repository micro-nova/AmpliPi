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

/* Calculates the desired fan percent based on the current system temps
 *
 * Inputs
 *    amp_temp: Temperature of the amplifier heatsinks
 *    psu_temp: Temperature of the high-voltage PSU
 *    pi_temp:  Temperature of the Raspberry Pi
 * All temps are in Q7.8 fixed-point format.
 *
 * Returns the desired fan percent in Q7.8 fixed-point format.
 */
int16_t fanPercentFromTemps(int16_t amp_temp, int16_t psu_temp,
                            int16_t rpi_temp) {
  // Calculate fan percent for each temp
  // measurement in Q7.8 format, 1.0 = 100%
  int16_t amp_pcnt = (amp_temp - TEMP_AMP_THRESH_LOW_Q7_8) /
                     (TEMP_AMP_THRESH_HIGH_C - TEMP_AMP_THRESH_LOW_C);
  int16_t psu_pcnt = (psu_temp - TEMP_PSU_THRESH_LOW_Q7_8) /
                     (TEMP_PSU_THRESH_HIGH_C - TEMP_PSU_THRESH_LOW_C);
  int16_t rpi_pcnt = (rpi_temp - TEMP_RPI_THRESH_LOW_Q7_8) /
                     (TEMP_RPI_THRESH_HIGH_C - TEMP_RPI_THRESH_LOW_C);

  // Take the max percentage requested.
  int16_t max_pcnt1   = amp_pcnt > psu_pcnt ? amp_pcnt : psu_pcnt;
  int16_t max_pcnt_f8 = max_pcnt1 > rpi_pcnt ? max_pcnt1 : rpi_pcnt;
  return max_pcnt_f8;
}

/* Calculates the fan duty cycle based on the desired fan percent
 *
 * Inputs
 *    pcnt_f8: Desired fan percent in Q7.8 fixed-point format.
 *
 * Returns the duty cycle in UQ1.7 fixed-point format
 */
uint8_t dutyFromPercent(int16_t pcnt_f8) {
  const int32_t scale_f16 = (1.0 - 0.3) * (1 << 16);
  const int32_t min_f24   = 0.3 * (1 << 24);
  int32_t       duty_f24  = scale_f16 * pcnt_f8 + min_f24;
  return (uint8_t)(duty_f24 >> (24 - 7));
}

/* Calculates the digital potentiometer value to use to achieve the desired
 * voltage. The dpot is nominally 10k Ohms.
 *
 * Inputs
 *    pcnt_f8: Desired fan percent in Q7.8 fixed-point format.
 *
 * Returns the dpot value in the range [0x00,0x7F]
 */
uint8_t dpotValFromPercent(int16_t pcnt_f8) {
  // Fans partially on, convert [0.0,1.0] in Q7.8 to [0x00,0x7F] dpot val
  // Rpot (kOhms) = 10k * DPOT_VAL / 127 + 0.1
  // V = 100k / (Rpot + 9k) + 1
  //   = 100k / (10k * DPOT_VAL / 127 + 0.1 + 9k) + 1
  //   = 100k / (10k / 127 * DPOT_VAL + 9.1k) + 1
  // 10k / 127 * DPOT_VAL + 9.1k = 100k / (V - 1)
  // DPOT_VAL = 127 / 10k * [100k / (V - 1) - 9.1k]
  // DPOT_VAL = 1270 / (V - 1) - 115.57
  const int32_t v_scale_f8  = (100 / 9.1 - 100 / 19.1) * (1 << 8);
  const int32_t v_min_f16   = (100 / 19.1 + 1) * (1 << 16);
  int32_t       v_fan_f16   = v_scale_f8 * pcnt_f8 + v_min_f16;
  const int32_t numer_f20   = 1270 * (1 << 20);
  const int32_t offset_f4   = 115.57 * (1 << 4);
  int32_t       dpot_val_f4 = numer_f20 / (v_fan_f16 - (1 << 16)) - offset_f4;
  return (uint8_t)(dpot_val_f4 >> 4);
}

/* Updates the fan state based on the current temp
 *
 * Inputs
 *    amp_temp: Temperature of the amplifier heatsinks
 *    psu_temp: Temperature of the high-voltage PSU
 *    pi_temp:  Temperature of the Raspberry Pi
 *    force:    Force fans on 100%
 *    linear:   Digital potentiometer for linear voltage control is available
 * All temps are in Q7.8 fixed-point format.
 *
 * Returns the current fan state.
 */
FanState* updateFans(int16_t amp_temp, int16_t psu_temp, int16_t rpi_temp,
                     bool force, bool thermistors, bool linear) {
#define FAN_DUTY_ON    (1 << 7)  // 1.0 in UQ1.7, 100% duty cycle
#define FAN_DUTY_OFF   0         // 0% duty cycle
#define DPOT_MAX_VOLTS 0         // Min resistance = max voltage
#define DPOT_MIN_VOLTS 127       // Max resistance = min voltage

  static FanState state = {
      .ctrl     = FAN_CTRL_MAX6644,
      .ovr_temp = false,
      .duty_f7  = 0,
      .dpot_val = 0,
      .volts_f4 = 0,
  };
  // Leave at max by default in case a dpot is detected later
  state.dpot_val = DPOT_MAX_VOLTS;

  state.ovr_temp = amp_temp > TEMP_AMP_THRESH_OVR_Q7_8 ||
                   psu_temp > TEMP_PSU_THRESH_OVR_Q7_8 ||
                   rpi_temp > TEMP_RPI_THRESH_OVR_Q7_8;

  /* Fan temp -> duty regions:
   *        T <= Toff | duty = 0
   * Toff < T <= Ton  | duty = duty (unchanged)
   * Ton  < T <= Tmax | duty = [38, 128) ([0.3, 1.0) in Q1.7)
   * Tmax < T         | duty = 128 (1.0 in Q1.7)
   */

  // Determine appropriate control method
  if (force) {
    state.ctrl    = FAN_CTRL_FORCED;
    state.duty_f7 = FAN_DUTY_ON;
  } else if (!thermistors) {
    // Power Board 2.A uses a MAX6644 fan controller IC and has no
    // thermistor inputs.
    state.ctrl    = FAN_CTRL_MAX6644;
    state.duty_f7 = FAN_DUTY_OFF;  // Release control to MAX6644.
  } else {
    state.ctrl = linear ? FAN_CTRL_LINEAR : FAN_CTRL_PWM;
    if (amp_temp <= TEMP_AMP_THRESH_OFF_Q7_8 &&
        psu_temp <= TEMP_PSU_THRESH_OFF_Q7_8 &&
        rpi_temp <= TEMP_RPI_THRESH_OFF_Q7_8) {
      // Cool enough that fans can be left off
      state.duty_f7  = FAN_DUTY_OFF;
      state.dpot_val = DPOT_MIN_VOLTS;
    } else {
      // Fans on at some percentage, update duty cycle or voltage
      int16_t pcnt_f8 = fanPercentFromTemps(amp_temp, psu_temp, rpi_temp);
      if (pcnt_f8 > (1 << 8)) {  // 1.0 in Q7.8
        // Temp high, max fan voltage and duty cycle
        state.duty_f7 = FAN_DUTY_ON;
      } else if (linear) {
        if (pcnt_f8 > 0) {
          state.dpot_val = dpotValFromPercent(pcnt_f8);
          state.duty_f7  = FAN_DUTY_ON;
        } else {
          // Hysteresis region, use old duty cycle and min dpot value
          state.dpot_val = DPOT_MIN_VOLTS;
        }
      } else {
        if (pcnt_f8 > 0) {
          state.duty_f7 = dutyFromPercent(pcnt_f8);
        } else {
          // Hysteresis region, use old duty cycle (but cap at 30%)
          const uint8_t min_f8 = 0.3 * (1 << 7);
          state.duty_f7 = state.duty_f7 > min_f8 ? min_f8 : state.duty_f7;
        }
      }
    }
  }

  // Determine fan power supply voltage based on dpot value
  // If no dpot present, fans nominally receive 12V.
  if (linear) {
    // V = 100,000 / (10,000 / 127 * DPOT_VAL + 9,100) + 1
    uint32_t volts_f12 =
        (100000 << 12) / (10000 * state.dpot_val / 127 + 9100) + (1 << 12);
    state.volts_f4 = (uint8_t)(volts_f12 >> 8);
  } else {
    state.volts_f4 = 12 << 4;
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
  uint32_t duty_ms = (FAN_PERIOD_MS * duty_f7) >> 7;
  uint32_t ms32    = millis() & (FAN_PERIOD_MS - 1);
  return ms32 < duty_ms;
}
