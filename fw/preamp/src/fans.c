/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
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

#include "adc.h"
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

FanCtrl ctrl_;          // Control method currently in use
uint8_t duty_f7_  = 0;  // Fan duty cycle in the range [0,1] in UQ1.7 format
uint8_t dpot_val_ = DEFAULT_DPOT_VAL;  // DPot setting that controls fan voltage
uint8_t volts_f4_ = 12 << 4;  // Fan power supply voltage in UQ4.4 format
bool    ovr_temp_;            // Temp too high

void setFanCtrl(FanCtrl ctrl) {
  if (ctrl == FAN_CTRL_FORCED) {
    // Only allow writing to forced mode
    ctrl_ = FAN_CTRL_FORCED;
  } else {
    // Reset to default mode, auto-control will determine real mode later
    ctrl_ = FAN_CTRL_MAX6644;
  }
}

FanCtrl getFanCtrl() {
  return ctrl_;
}

uint8_t getFanDuty() {
  return duty_f7_;
}

uint8_t getFanDPot() {
  return dpot_val_;
}

uint8_t getFanVolts() {
  return volts_f4_;
}

bool overTemp() {
  return ovr_temp_;
}

bool fansOn() {
  return duty_f7_ > 0;
}

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

/* Determines the fan control method to be used.
 *
 * Inputs
 *    current_control:  Current fan control method.
 *    amp_temp_present: True if amp board temp sensors are readable.
 *    dpot_present:     True if a digital potentiometer was found.
 *
 * Returns the new fan control method.
 */
static FanCtrl updateFanCtrlMethod(FanCtrl current_control,
                                   bool amp_temp_present, bool dpot_present) {
  if (current_control == FAN_CTRL_FORCED) {
    // Fans forced on 100% by the Pi
    return FAN_CTRL_FORCED;
  }
  if (dpot_present) {
    // The digital potentiometer (DPot) can adjust the fan voltage
    return FAN_CTRL_LINEAR;
  }
  if (amp_temp_present) {
    // No DPot, but temp sensors still present. PWM fan voltage.
    return FAN_CTRL_PWM;
  }
  // Power Board 2.A uses MAX6644 but has no HV2/NTC2.
  // If neither of those inputs measures a valid temp, then assume
  // a MAX6644 fan control IC is controlling the fans.
  return FAN_CTRL_MAX6644;
}

/* Updates the fan voltage and duty cycle.
 *
 * Inputs
 *    control:  Fan control method.
 *    amp_temp: Temperature of the amplifier heatsinks
 *    psu_temp: Temperature of the high-voltage PSU
 *    pi_temp:  Temperature of the Raspberry Pi
 */
static void updateFanOutput(FanCtrl ctrl, int16_t amp_temp, int16_t psu_temp,
                            int16_t rpi_temp) {
#define FAN_DUTY_ON    (1 << 7)  // 1.0 in UQ1.7, 100% duty cycle
#define FAN_DUTY_OFF   0         // 0% duty cycle
#define DPOT_MAX_VOLTS 0         // Min resistance = max voltage
#define DPOT_MIN_VOLTS 127       // Max resistance = min voltage

  switch (ctrl) {
    case FAN_CTRL_MAX6644:
      dpot_val_ = DPOT_MAX_VOLTS;  // Max in case a dpot is detected later
      duty_f7_  = FAN_DUTY_OFF;    // Release control to MAX6644.
      break;

    case FAN_CTRL_LINEAR:
    case FAN_CTRL_PWM:
      if (amp_temp <= TEMP_AMP_THRESH_OFF_Q7_8 &&
          psu_temp <= TEMP_PSU_THRESH_OFF_Q7_8 &&
          rpi_temp <= TEMP_RPI_THRESH_OFF_Q7_8) {
        // Cool enough that fans can be left off
        dpot_val_ = DPOT_MIN_VOLTS;
        duty_f7_  = FAN_DUTY_OFF;
      } else {
        // Fans on at some percentage, update duty cycle or voltage
        int16_t pcnt_f8 = fanPercentFromTemps(amp_temp, psu_temp, rpi_temp);
        if (pcnt_f8 > (1 << 8)) {  // 1.0 in Q7.8
          // Temp high, max fan voltage and duty cycle
          dpot_val_ = DPOT_MAX_VOLTS;
          duty_f7_  = FAN_DUTY_ON;
        } else {
          if (ctrl == FAN_CTRL_LINEAR) {
            if (pcnt_f8 > 0) {
              dpot_val_ = dpotValFromPercent(pcnt_f8);
            } else {
              // Hysteresis region, use old duty cycle and min dpot value
              dpot_val_ = DPOT_MIN_VOLTS;
            }
            duty_f7_ = FAN_DUTY_ON;
          } else {  // PWM
            if (pcnt_f8 > 0) {
              duty_f7_ = dutyFromPercent(pcnt_f8);
            } else {
              // Hysteresis region, use old duty cycle (but cap at 30%)
              const uint8_t min_f8 = 0.3 * (1 << 7);
              duty_f7_             = duty_f7_ > min_f8 ? min_f8 : duty_f7_;
            }
            dpot_val_ = DPOT_MAX_VOLTS;
          }
        }
      }
      break;

    case FAN_CTRL_FORCED:
    default:
      dpot_val_ = DPOT_MAX_VOLTS;  // Max voltage if dpot is present
      duty_f7_  = FAN_DUTY_ON;     // 100% fan
      break;
  }
}

/* Updates the fan state based on the current temp
 *
 * Inputs
 *    force:    Force fans on 100%
 *    linear:   Digital potentiometer for linear voltage control is available
 * All temps are in Q7.8 fixed-point format.
 *
 * Returns the desired DPot value.
 */
uint8_t updateFans(bool linear) {
  // Get latest temps
  Temps16* tmp = getTemps16();

  // The two amp heatsinks can be combined by simply taking the max
  int16_t amp_temp = tmp->amp1_f8 > tmp->amp2_f8 ? tmp->amp1_f8 : tmp->amp2_f8;

  // The two PSU temps can be combined by simply taking the max
  int16_t psu_temp = tmp->hv1_f8 > tmp->hv2_f8 ? tmp->hv1_f8 : tmp->hv2_f8;

  // Determine appropriate control method
  ctrl_ = updateFanCtrlMethod(ctrl_, amp_temp > 0, linear);
  // TODO: replace temps and flags with a hw_state struct

  /* Fan temp -> duty regions:
   *        T <= Toff | duty = 0
   * Toff < T <= Ton  | duty = duty (unchanged)
   * Ton  < T <= Tmax | duty = [38, 128) ([0.3, 1.0) in Q1.7)
   * Tmax < T         | duty = 128 (1.0 in Q1.7)
   */

  // Update fan output based on current control method
  updateFanOutput(ctrl_, amp_temp, psu_temp, tmp->pi_f8);

  // Determine if the AmpliPi unit is too hot
  ovr_temp_ = amp_temp > TEMP_AMP_THRESH_OVR_Q7_8 ||
              psu_temp > TEMP_PSU_THRESH_OVR_Q7_8 ||
              tmp->pi_f8 > TEMP_RPI_THRESH_OVR_Q7_8;

  // Determine fan power supply voltage based on dpot value
  // If no dpot present, fans nominally receive 12V.
  if (ctrl_ == FAN_CTRL_LINEAR) {
    // V = 100,000 / (10,000 / 127 * DPOT_VAL + 9,100) + 1
    uint32_t volts_f12 =
        (100000 << 12) / (10000 * dpot_val_ / 127 + 9100) + (1 << 12);
    volts_f4_ = (uint8_t)(volts_f12 >> 8);
  } else {
    volts_f4_ = 12 << 4;
  }

  return dpot_val_;
}

/* Determines the GPIO expander's FAN_ON pin state.
 * Call every millisecond tick.
 *
 * Inputs
 *    duty_f7: Fan duty cycle in the range [0,1] in UQ1.7 format
 *
 * Returns boolean FAN_ON pin state
 */
bool getFanOnFromDuty() {
  uint32_t duty_ms = (FAN_PERIOD_MS * duty_f7_) >> 7;
  uint32_t ms32    = millis() & (FAN_PERIOD_MS - 1);
  return ms32 < duty_ms;
}
