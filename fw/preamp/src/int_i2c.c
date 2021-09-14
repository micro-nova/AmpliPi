/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Control for front panel LEDs
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

#include "int_i2c.h"

#include <math.h>
#include <stdbool.h>

#include "channel.h"
#include "port_defs.h"
#include "ports.h"
#include "stm32f0xx.h"

// I2C GPIO registers
const I2CReg pwr_io_dir_  = {0x42, 0x00};
const I2CReg pwr_io_gpio_ = {0x42, 0x09};
const I2CReg pwr_io_olat_ = {0x42, 0x0A};

// LED Board registers
const I2CReg led_dir_  = {0x40, 0x00};
const I2CReg led_gpio_ = {0x40, 0x09};
const I2CReg led_olat_ = {0x42, 0x0A};

void InitI2C2() {
  /* I2C-2 is internal to a single AmpliPi unit.
   * The STM32 is the master and controls the volume chips, power, fans,
   * and front panel LEDs.
   *
   * Bus Capacitance
   * | Device           | Capacitance (pF)
   * | STM32            | 5
   * | MAX11601 (ADC)   | 15 (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.15? t_SU.DAT>0.1 t_r<.3 t_f<.3)
   * | MCP23008 (Power) | ?? (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.9   t_SU.DAT>0.1 t_r<.3 t_f<.3)
   * | MCP23008 (LEDs)  | ??
   * | MCP4017 (DPot)   | 10 (t_HD.STA>.6 t_LOW>1.3 t_HIGH>0.6 t_SU.STA>.6
   *                          t_HD.DAT<.9   t_SU.DAT>0.1 t_r<.3 t_f<.04)
   * | TDA7448 (Vol1)   | ??????????????
   * | TDA7448 (Vol2)   | Doesn't even specify max frequency...
   * ~70 pF for all devices, plus say ~20 pF for all traces and wires = ~90 pF
   * So rise time t_r ~= 0.8473 * 1 kOhm * 90 pF = 76 ns
   * Measured rise time: 72 ns
   * Measured fall time:  4 ns
   *
   * Pullup Resistor Values
   *   Max output current for I2C Standard/Fast mode is 3 mA, so min pullup is:
   *    Rp > [V_DD - V_OL(max)] / I_OL = (3.3 V - 0.4 V) / 3 mA = 967 Ohm
   *   Max bus capacitance (with only resistor for pullup) is 200 pF.
   *   Standard mode rise-time t_r(max) = 1000 ns
   *    Rp_std < t_r(max) / (0.8473 * C_b) = 1000 / (0.8473 * 0.2) = 5901 Ohm
   *   Fast mode rise-time t_r(max) = 300 ns
   *    Rp_fast < t_r(max) / (0.8473 * C_b) = 1000 / (0.8473 * 0.2) = 1770 Ohm
   *   For Standard mode: 1k <= Rp <= 5.6k
   *   For Fast mode: 1k <= Rp <= 1.6k
   */

  // Enable peripheral clock for I2C2
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);

  // Enable SDA1, SDA2, SCL1, SCL2 clocks
  // Enabled here since this is called before I2C1
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);

  // Connect pins to alternate function for I2C2
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource10, GPIO_AF_1);  // I2C2_SCL
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource11, GPIO_AF_1);  // I2C2_SDA

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C;
  GPIO_InitStructureI2C.GPIO_Pin   = pSCL_VOL | pSDA_VOL;
  GPIO_InitStructureI2C.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
  GPIO_InitStructureI2C.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

  // Setup I2C2
  I2C_InitTypeDef I2C_InitStructure2;
  I2C_InitStructure2.I2C_Mode                = I2C_Mode_I2C;
  I2C_InitStructure2.I2C_AnalogFilter        = I2C_AnalogFilter_Enable;
  I2C_InitStructure2.I2C_DigitalFilter       = 0x00;
  I2C_InitStructure2.I2C_OwnAddress1         = 0x00;
  I2C_InitStructure2.I2C_Ack                 = I2C_Ack_Enable;
  I2C_InitStructure2.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;

  // Datasheet example: 100 kHz: 0x10420F13, 400 kHz: 0x10310309
  // Excel tool, rise/fall 76/15 ns: 100 kHz: 0x00201D2B (0.5935% error)
  //                                 400 kHz: 0x0010020A (2.4170% error)

  // Common parameters
  // t_I2CCLK = 1 / 8 MHz = 125 ns
  // t_AF(min) = 50 ns
  // t_AF(max) = 260 ns
  // t_r = 72 ns
  // t_f = 4 ns
  // Fall time must be < 300 ns
  // For Standard mode (100 kHz), rise time < 1000 ns
  // For Fast mode (400 kHz), rise time < 300 ns
  // tR = 0.8473*Rp*Cb = 847.3*Cb

  // Standard mode, max 100 kHz
  // t_LOW > 4.7 us
  // t_HIGH > 4 us
  // t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (4700 - 50) / 4 = 1.1625 ns
  // t_I2CCLK < t_HIGH = 4000 ns
  // Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
  // t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
  // SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
  // SDADEL >= [t_f - 50 - 375] / 125 --- This will be < 0, so SDASEL >= 0
  // SDADEL <= [t_HD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
  // SDADEL <= (3450 - 76 - 260 - 500) / 125 = 20.912
  // SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
  // SCLDEL >= (76 + 250) / 125 - 1 = 1.608
  // So 0 <= SDADEL <= 20, SCLDEL >= 2
  // I2C_TIMINGR[31:16] = 0x0020
  //
  // t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
  // 4000 <= 50 + 2*125 + 125*(SCLH + 1)
  // 3575 <= 125*SCLH
  // SCLH >= 28.6 = 0x1D
  //
  // t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
  // 4700 <= 50 + 2*125 + 125*(SCLL + 1)
  // 4275 <= 125*SCLL
  // SCLL >= 34.2 = 0x23
  //
  // Need to stay under 100 kHz in "worst" case. Keep SCLH at min,
  // but here we determine final SCLL.
  // t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns (100 kHz max)
  // t_SYNC1(min) = t_f + t_AF(min) + t_DNF + 2*t_I2CCLK
  // t_SYNC1(min) = 6 + 50 + 2*125 = 306 ns
  // t_SYNC2(min) = t_r + t_AF(min) + t_DNF + 2*t_I2CCLK
  // t_SYNC2(min) = 76 + 50 + 2*125 = 376 ns
  // t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns
  // t_LOW + t_HIGH >= 9318 ns
  // t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 9318 ns
  // 125*(SCLL + 1) + 125*30 >= 9318 ns
  // 125*(SCLL + 1) + 125*30 >= 9318 ns
  // SCLL >= 43.544 = 0x2C

  // Fast mode, max 400 kHz
  // TODO?

  I2C_InitStructure2.I2C_Timing = 0x00201D2C;
  I2C_Init(I2C2, &I2C_InitStructure2);
  I2C_Cmd(I2C2, ENABLE);
}

void WriteAdc(uint8_t data) {
  // Wait if I2C2 is busy
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY)) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, adc_dev.dev, 1, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET) {}

  I2C_SendData(I2C2, data);

  // Wait for stop flag to be sent and then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);
}

uint8_t ReadAdc(uint8_t chan) {
  // Set which channel to read from
  WriteAdc(chan);

  // Taken from the latter half of readI2C2(). The ADC only has the one reg
  // to read from, so none of the reg specifying is necessary
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY)) {}

  I2C_TransferHandling(I2C2, adc_dev.dev, 1, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Read);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  uint8_t data = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

  return data;
}

uint8_t AdcToTemp(uint8_t adc_val) {
  // Return:
  //   0x00 if adc_val < MIN_VAL
  //   0xFF if adc_val > MAX_VAL
  //   0xXX otherwise, where 0x01 = -19.5C, 0x5E = 27C, 0xFE = 107C
  // Max resistance = 328996, Min resistance = 358
#define MIN_VAL ((uint8_t)(255 * 4.7 / (328.996 + 4.7)))    // 3
#define MAX_VAL ((uint8_t)(255 * 4.7 / (0.358 + 4.7) + 1))  // 237
#define BETA    (3900.f)                                    // B-Constant
#define R0      (10.f)                                      // Resistance @ KR0
#define KR0     (25.f + 273.15f)                            // degK at Rt=R0

  /* Nominal B-Constant of 3900K, R0 resistance is 10 kOhm at 25dC (T0)
   * Thermocouple resistance = R0*e^[B*(1/T - 1/T0)] = Rt
   * ADC_VAL = 3.3V * 4.7kOhm / (4.7kOhm + Rt kOhm) / 3.3V * 255
   * Rt = 4.7 * (255 / ADC_VAL - 1)
   * T = 1/(ln(Rt/R0)/B + 1/T0)
   * T = 1/(ln(Rt/10)/3900 + 1/(25+273.5)) - 273.15
   */

  uint8_t temp;
  if (adc_val < MIN_VAL) {
    temp = 0x00;
  } else if (adc_val > MAX_VAL) {
    temp = 0xFF;
  } else {
    // float rt   = 4.7f * (255.f / adc_val - 1.f);
    // 7 * 35 cycles / 8 MHz = ~31 us + logf time
    float rt_r0  = (4.7f * 255.f / R0) / adc_val - 4.7f / R0;    // Rt / R0
    float tempf  = BETA / (logf(rt_r0) + BETA / KR0) - 273.15f;  // degC
    float c_q6_2 = 2.f * (tempf + 20.f);  // [UQ7.1 + 20] degC format
    temp         = (uint8_t)c_q6_2;
  }
  return temp;
}

void UpdateAdc(AmpliPiState* state) {
#define ADC_REF_VOLTS 3.3
#define ADC_PD_KOHMS  4700
#define ADC_PU_KOHMS  100000
  // TODO: low-pass filter after intial reading

  // Configuration byte = { config=0b0, scan=0b11, cs=0b00XX, sgl=0b1 }
  uint8_t hv1_adc       = ReadAdc(0x61 | (0 << 1));
  uint8_t amp_temp1_adc = ReadAdc(0x61 | (1 << 1));
  uint8_t hv1_temp_adc  = ReadAdc(0x61 | (2 << 1));
  uint8_t amp_temp2_adc = ReadAdc(0x61 | (3 << 1));

  // Convert HV1 to Volts
  uint32_t hv1_adc2  = (uint32_t)hv1_adc << 2;  // Add fractional bits
  uint32_t hv1_raw_v = ADC_REF_VOLTS * (ADC_PU_KOHMS + ADC_PD_KOHMS) *
                       hv1_adc2 / (UINT8_MAX * ADC_PD_KOHMS);
  state->hv1 = (uint8_t)(hv1_raw_v > UINT8_MAX ? UINT8_MAX : hv1_raw_v);

  // Convert HV1 thermocouple to degC
  state->hv1_temp = AdcToTemp(hv1_temp_adc);

  // Convert amplifier thermocouples to degC
  state->amp_temp1 = AdcToTemp(amp_temp1_adc);
  state->amp_temp2 = AdcToTemp(amp_temp2_adc);
}

void InitInternalI2C(AmpliPiState* state) {
  // Initialize the STM32's I2C2 bus as a master
  InitI2C2();

  // Set the direction for the power board GPIO
  writeI2C2(pwr_io_dir_, 0x7D);  // 0=output, 1=input

  // Set the LED Board's GPIO expander as all outputs
  writeI2C2(led_dir_, 0x00);  // 0=output, 1=input

  UpdateInternalI2C(state);
}

void UpdateInternalI2C(AmpliPiState* state) {
  // Read the Power Board's ADC
  UpdateAdc(state);

  // Update the Power Board's GPIO state
  if (state->fan_override) {
    state->pwr_gpio.fan_on = 1;
  }
  // TODO: Fan control logic
  writeI2C2(pwr_io_olat_, state->pwr_gpio.data);
  state->pwr_gpio.data = readI2C2(pwr_io_gpio_);

  // Update the LED Board's LED state
  if (!state->led_override) {
    state->leds.grn = state->standby ? 0 : 1;
    // state->leds.red = state->standby ? 1 : 0;

    state->leds.zones = 0;
    for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
      state->leds.zones |= (isOn(ch) ? 1 : 0) << ch;
    }
  }
  writeI2C2(led_olat_, state->leds.data);
  state->pwr_gpio.data = readI2C2(led_gpio_);

  // TODO: Can the volume controllers be read?
  // TODO: Write volumes
}
