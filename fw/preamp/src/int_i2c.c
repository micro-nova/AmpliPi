/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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

#include "int_i2c.h"

#include <stdbool.h>

#include "audio_mux.h"
#include "fans.h"
#include "port_defs.h"
#include "ports.h"
#include "stm32f0xx.h"
#include "systick.h"
#include "thermistor.h"

// I2C GPIO registers
const I2CReg pwr_io_dir_  = {0x42, 0x00};
const I2CReg pwr_io_gpio_ = {0x42, 0x09};
const I2CReg pwr_io_olat_ = {0x42, 0x0A};

// LED Board registers
const I2CReg led_dir_  = {0x40, 0x00};
const I2CReg led_gpio_ = {0x40, 0x09};
const I2CReg led_olat_ = {0x40, 0x0A};

// Power Board ADC register (no registers)
const I2CReg adc_dev_ = {0xC8, 0xFF};

// DPOT register (no registers)
const I2CReg dpot_dev_ = {0x5E, 0xFF};

void initI2C2() {
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
   * Rise time t_r = 0.8473*Rp*Cb ~= 0.8473 * 1 kOhm * 90 pF = 76 ns
   * Measured rise time: 72 ns
   * Measured fall time:  4 ns
   *
   * Pullup Resistor Values
   *   Max output current for I2C Standard/Fast mode is 3 mA, so min pullup is:
   *    Rp > [V_DD - V_OL(max)] / I_OL = (3.3 V - 0.4 V) / 3 mA = 967 Ohm
   *   Max bus capacitance (with only resistor for pullup) is 200 pF.
   *   Standard mode rise-time t_r(max) = 1000 ns
   *    Rp_std < t_r(max) / (0.8473 * Cb) = 1000 / (0.8473 * 0.2) = 5901 Ohm
   *   Fast mode rise-time t_r(max) = 300 ns
   *    Rp_fast < t_r(max) / (0.8473 * Cb) = 1000 / (0.8473 * 0.2) = 1770 Ohm
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

  // See the STM32F030 reference manual section 22.4.9 "I2C master mode" or
  // AN4235 for I2C timing calculations.
  // Excel tool, rise/fall 72/4 ns: 100 kHz: 0x00201D2C (0.5074% error)
  //                                400 kHz: 0x0010020B (1.9992% error)

  /* Common parameters
   * t_I2CCLK = 1 / 8 MHz = 125 ns
   * t_AF(min) = 50 ns  - Analog filter minimum input delay
   * t_AF(max) = 260 ns - Analog filter maximum input delay
   * t_DNF = 0          - Digital filter input delay
   * t_r = 72 ns        - Rise time
   *   For Standard mode (100 kHz), rise time < 1000 ns
   *   For Fast mode (400 kHz), rise time < 300 ns
   * t_f = 4 ns         - Fall time (must be < 300 ns)
   *
   * t_SYNC1(min) = t_f + t_AF(min) + t_DNF + 2*t_I2CCLK
   * t_SYNC1(min) = 4 + 50 + 2*125 = 306 ns
   * t_SYNC2(min) = t_r + t_AF(min) + t_DNF + 2*t_I2CCLK
   * t_SYNC2(min) = 76 + 50 + 2*125 = 376 ns
   */

  /* Standard mode, max 100 kHz
   * t_LOW > 4.7 us,t_HIGH > 4 us
   * t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (4700 - 50) / 4 = 1162.5 ns
   * t_I2CCLK < t_HIGH = 4000 ns
   * Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
   * t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
   * SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
   * SDADEL >= [4 - 50 - 375] / 125 = -3.368 < 0, so SDASEL >= 0
   * SDADEL <= [t_VD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
   * SDADEL <= (3450 - 72 - 260 - 500) / 125 = 20.944
   * SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
   * SCLDEL >= (72 + 250) / 125 - 1 = 1.576
   * So 0 <= SDADEL <= 20, SCLDEL >= 2
   * I2C_TIMINGR[31:16] = 0x0020
   *
   * t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
   * 4000 <= 50 + 2*125 + 125*(SCLH + 1)
   * 3575 <= 125*SCLH
   * SCLH >= 28.6 = 0x1D
   *
   * t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
   * 4700 <= 50 + 2*125 + 125*(SCLL + 1)
   * 4275 <= 125*SCLL
   * SCLL >= 34.2 = 0x23
   *
   * Need to stay under 100 kHz in "worst" case. Keep SCLH at min,
   * but here we determine final SCLL.
   * t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns (100 kHz max)
   * t_LOW + t_HIGH >= 10000 - 304 - 372 ns = 9324 ns
   * t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 9324 ns
   * 125*(SCLL + 1) + 125*30 >= 9324 ns
   * SCLL >= 43.592 = 0x2C
   *
   * I2C_TIMINGR[31:0] = 0x00101D2C
   */

  /* Fast mode, max 400 kHz
   * t_LOW > 1.3 us, t_HIGH > 0.6 us
   * t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (1300 - 50) / 4 = 312.5 ns
   * t_I2CCLK < t_HIGH = 600 ns
   * Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
   * t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
   * SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
   * SDADEL >= [4 - 50 - 375] / 125 = -3.368 < 0, so SDASEL >= 0
   * SDADEL <= [t_VD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
   * SDADEL <= (900 - 72 - 260 - 500) / 125 = 0.544
   * SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
   * SCLDEL >= (72 + 100) / 125 - 1 = 0.376
   * So 0 <= SDADEL <= 0, SCLDEL >= 1
   * I2C_TIMINGR[31:16] = 0x0010
   *
   * t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
   * 600 <= 50 + 2*125 + 125*(SCLH + 1)
   * 175 <= 125*SCLH
   * SCLH >= 1.4 = 0x02
   *
   * t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
   * 1300 <= 50 + 2*125 + 125*(SCLL + 1)
   * 875 <= 125*SCLL
   * SCLL >= 7 = 0x07
   *
   * Need to stay under 400 kHz in "worst" case. Keep SCLH at min,
   * but here we determine final SCLL.
   * t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 2500 ns (400 kHz max)
   * t_LOW + t_HIGH >= 2500 - 304 - 372 ns = 1824 ns
   * t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 1824 ns
   * 125*(SCLL + 1) + 125*3 >= 1824 ns
   * SCLL >= 10.592 = 0x0B
   *
   * I2C_TIMINGR[31:0] = 0x0010020B
   */

  I2C_InitStructure2.I2C_Timing = 0x0010020B;
  I2C_Init(I2C2, &I2C_InitStructure2);
  I2C_Cmd(I2C2, ENABLE);
}

typedef struct {
  uint8_t hv1;
  uint8_t amp_temp1;
  uint8_t hv1_temp;
  uint8_t amp_temp2;
} AdcVals;

AdcVals readAdc() {
  /****************************************************************************
   *  Configure ADC to scan all 4 channels
   ****************************************************************************/

  // Wait if I2C2 is busy
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY)) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, adc_dev_.dev, 1, I2C_SoftEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET) {}

  // Configuration byte = { config=0b0, scan=0b11, cs=0b00XX, sgl=0b1 }
  // Scan all 4 channels in single-ended mode
  I2C_SendData(I2C2, 0x01 | (3 << 1));

  // Wait for transfer complete flag
  while (I2C_GetFlagStatus(I2C2, I2C_ISR_TC) == RESET) {}

  /****************************************************************************
   *  Read all 4 channels
   ****************************************************************************/
  AdcVals vals = {};
  // Restart and setup a read transfer
  I2C_TransferHandling(I2C2, adc_dev_.dev, 4, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Read);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.hv1 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.amp_temp1 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.hv1_temp = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.amp_temp2 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

  return vals;
}

// Returns true if thermistors are present, false otherwise
bool updateAdc(AmpliPiState* state) {
#define ADC_REF_VOLTS 3.3
#define ADC_PD_KOHMS  4700
#define ADC_PU_KOHMS  100000
  // TODO: low-pass filter after intial reading
  AdcVals adc = readAdc();

  // Convert HV1 to Volts (multiply by 4 to add 2 fractional bits)
  uint32_t num       = 4 * ADC_REF_VOLTS * (ADC_PU_KOHMS + ADC_PD_KOHMS);
  uint32_t den       = UINT8_MAX * ADC_PD_KOHMS;
  uint32_t hv1_raw_v = num * adc.hv1 / den;
  state->hv1         = (uint8_t)(hv1_raw_v > UINT8_MAX ? UINT8_MAX : hv1_raw_v);

  // Convert HV1 thermocouple to degC
  state->hv1_temp = THERM_LUT_[adc.hv1_temp];

  // Convert amplifier thermocouples to degC
  state->amp_temp1 = THERM_LUT_[adc.amp_temp1];
  state->amp_temp2 = THERM_LUT_[adc.amp_temp2];

  // Power Board 2.A doesn't have thermistors. Instead, it has HV2/NTC2 inputs.
  // Neither of those were used and are pulled low. So if either input measures
  // more than 0 assume thermistors are present, otherwise not.
  return adc.amp_temp1 || adc.amp_temp2;
}

uint32_t writeDpot(uint8_t val) {
  // TODO: add more I2C read/write functions in ports.c and use here and ADC

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, dpot_dev_.dev, 1, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag or an error
  uint32_t isr = I2C2->ISR;
  do {
    if (isr & I2C_ISR_NACKF) {
      I2C2->ICR = I2C_ICR_NACKCF;
      return I2C_ISR_NACKF;
    }
    if (isr & I2C_ISR_BERR) {
      I2C2->ICR = I2C_ICR_BERRCF;
      return I2C_ISR_BERR;
    }
    if (isr & I2C_ISR_ARLO) {
      I2C2->ICR = I2C_ICR_ARLOCF;
      return I2C_ISR_ARLO;
    }
    isr = I2C2->ISR;
  } while (!(isr & I2C_ISR_TXIS));

  // Send subaddress and data
  I2C_SendData(I2C2, val);

  // Wait for stop flag to be sent and then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C2->ICR = I2C_ICR_STOPCF;
  return 0;
}

LedGpio updateLeds(bool addr_set) {
  LedGpio leds = {0};

  leds.grn = inStandby() ? 0 : 1;
  if (addr_set) {
    leds.red = !leds.grn;
  } else {
    // Blink red light at ~0.5 Hz
    uint32_t mod2k = millis() & ((1 << 11) - 1);
    leds.red       = mod2k > (1 << 10);
  }

  leds.zones = 0;
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    leds.zones |= (isOn(zone) ? 1 : 0) << zone;
  }
  return leds;
}

void initInternalI2C(AmpliPiState* state) {
  // Initialize the STM32's I2C2 bus as a master
  initI2C2();

  // Set the direction for the power board GPIO
  // Retry if failed, the bus may be in a bad state if the micro was
  // reset in the middle of a transaction.
  uint32_t tries = 255;
  while (tries--) {
    uint32_t status = writeI2C2(pwr_io_dir_, 0x7C);  // 0=output, 1=input
    if (status == I2C_ISR_NACKF) {
      // Received a NACK, will try again
    } else if (status == I2C_ISR_ARLO) {
      // Arbitation lost (SDA low when master tried to set high).
      // Reset I2C since the peripheral auto-sets itself into slave mode.
      // Then, send 9 clocks to finish whichever slave transaction was ongoing.

      // Disable I2C peripheral to reset it if previously enabled
      I2C_Cmd(I2C2, DISABLE);

      // Config I2C GPIO pins
      GPIO_InitTypeDef GPIO_InitStructureI2C;
      GPIO_InitStructureI2C.GPIO_Pin   = pSCL_VOL | pSDA_VOL;
      GPIO_InitStructureI2C.GPIO_Mode  = GPIO_Mode_OUT;
      GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
      GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
      GPIO_InitStructureI2C.GPIO_PuPd  = GPIO_PuPd_NOPULL;
      GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

      // Generate 9 clocks to clear bus
      writePin(i2c2_scl_, true);
      writePin(i2c2_sda_, false);  // Keep SDA low even after slave releases it
      for (size_t i = 0; i < 9; i++) {
        delayMs(1);
        writePin(i2c2_scl_, false);
        delayMs(1);
        writePin(i2c2_scl_, true);
      }

      // Stop condition
      delayMs(1);
      writePin(i2c2_sda_, true);

      // Re-init I2C2 now that the bus is un-stuck
      initI2C2();

      /* TODO: Figure out why the below method doesn't work.
      I2C_TransferHandling(I2C2, 0x00, 0, I2C_AutoEnd_Mode,
                           I2C_Generate_Start_Write);

      // Wait until the transaction is done then reset I2C again
      delayMs(1);
      initI2C2();
      uint32_t isr = I2C2->ISR;
      do {
        if (isr & I2C_ISR_NACKF) {
          I2C2->ICR = I2C_ICR_NACKCF;
          break;
        }
        if (isr & I2C_ISR_ARLO) {
          I2C2->ICR = I2C_ICR_ARLOCF;
          break;
        }
        if (isr & I2C_FLAG_STOPF) {
          I2C2->ICR = I2C_ICR_STOPCF;
          break;
        }
        isr = I2C2->ISR;
      } while (1);
      */
    } else {
      tries = 0;
    }
  }

  // Set the LED Board's GPIO expander as all outputs
  writeI2C2(led_dir_, 0x00);  // 0=output, 1=input
  writeI2C2(led_gpio_, state->leds.data);

  updateInternalI2C(state);
}

void updateInternalI2C(AmpliPiState* state) {
  uint32_t mod8 = millis() & ((1 << 3) - 1);
  if (mod8 == 0) {
    // Read ADC and update fans every 8 ms
    // Reading the Power Board's ADC takes ~248 us
    bool thermistors = updateAdc(state);

    // In UQ7.1 + 20, convert to Q7.8
    // TODO: do this conversion in ADC filter when added
    int16_t amp_temp1_q7_8 = ((int16_t)state->amp_temp1 - (20 << 1)) << 7;
    int16_t amp_temp2_q7_8 = ((int16_t)state->amp_temp1 - (20 << 1)) << 7;
    int16_t hv1_temp_q7_8  = ((int16_t)state->hv1_temp - (20 << 1)) << 7;
    int16_t rpi_temp_q7_8  = ((int16_t)state->pi_temp - (20 << 1)) << 7;

    // The two amp heatsinks can be combined by simply taking the max
    int16_t amp_temp_q7_8 =
        amp_temp1_q7_8 > amp_temp2_q7_8 ? amp_temp1_q7_8 : amp_temp2_q7_8;

    // No I2C reads/writes, just fan calculations
    static bool dpot_present = false;
    state->fans  = updateFans(amp_temp_q7_8, hv1_temp_q7_8, rpi_temp_q7_8,
                             state->fan_override, thermistors, dpot_present);
    dpot_present = writeDpot(state->fans->dpot_val) == 0;
  } else {
    state->pwr_gpio.data = readI2C2(pwr_io_gpio_);
    if (state->fans->ctrl != FAN_CTRL_MAX6644) {
      // No fan control IC to determine this
      state->pwr_gpio.fan_fail_n = !false;
      state->pwr_gpio.ovr_tmp_n  = !false;
    }

    // Update the LED Board's LED state
    if (!state->led_override) {
      state->leds = updateLeds(state->i2c_addr != 0);
    }
    // TODO: only write on change
    writeI2C2(led_gpio_, state->leds.data);
  }

  // Update the Power Board's GPIO state, only writing when necessary
  PwrGpio gpio_request = {
      .en_9v  = true,  // Always enable 9V
      .en_12v = true,  // Always enable 12V
      .fan_on = getFanOnFromDuty(state->fans->duty_f7),
  };
  if (gpio_request.data != (PWR_GPIO_OUT_MASK & state->pwr_gpio.data)) {
    writeI2C2(pwr_io_gpio_, gpio_request.data);
  }

  // TODO: Can the volume controllers be read?
  // TODO: Write volumes
}
