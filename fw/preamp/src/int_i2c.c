/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
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
#include <stdint.h>

#include "adc.h"
#include "audio.h"
#include "fans.h"
#include "i2c.h"
#include "leds.h"
#include "pins.h"
#include "pwr_gpio.h"
#include "stm32f0xx.h"
#include "systick.h"

// I2C GPIO registers
const I2CReg pwr_io_dir_  = {0x42, 0x00};
const I2CReg pwr_io_gpio_ = {0x42, 0x09};
const I2CReg pwr_io_olat_ = {0x42, 0x0A};

// DPOT address (no registers)
const I2CDev dpot_dev_ = 0x5E;
// DPOT with a mandatory SMBUS command
const I2CReg dpot_cmd_  = {0x5C, 0x00};
DPotType     dpot_type_ = DPOT_NONE;

static void delayUs(uint32_t us) {
  for (uint32_t i = 0; i < us; i++) {
    // Create a ~1 us delay based on the CPU clock
    for (size_t n = 0; n < HSI_VALUE / 1000000; n++) {
      __ASM volatile("nop");
    }
  }
}

/* This function resolves an I2C Arbitration Lost error by clearing any
 * in-progress transactions on the bus. Also run at startup since the bus is
 * in an unknown state.
 *
 * Arbitration is lost if SDA is low when the I2C master is attempting to
 * send a high on the bus. Usually this only occurs if another I2C master is
 * sending at the same time, but there is only one master in AmpliPi's setup.
 * Another way this error occurs is if the preamp's micro is reset during
 * the middle of a read transaction. The slave could still be sending data.
 * Ideally all slaves would be reset to fix this second case, but that control
 * doesn't exist in AmpliPi hardware. So this function attempts to finish out
 * the transaction by sending more clocks and verifying SDA is untouched.
 *
 * Time required: 44 us to 370 us.
 * Max time seen in practice: 100 us.
 */
void quiesceI2C() {
  const uint32_t HALF_PERIOD = 2;  // 4 us period = 250 kHz I2C clock
  // Ensure the I2C peripheral is disabled and pins are set as GPIO
  // Pins will be configured to HI-Z (pulled up externally)
  deinitI2C2();
  configI2C2PinsAsGPIO();

  const uint32_t NUM_CONSECUTIVE_ONES = 9;
  // Require NUM_CONSECUTIVE_ONES on I2C's SDA before proceeding.
  // As of now all transactions are 8-bits, so 8 clocks plus one more for the
  // ACK should finish any ongoing transaction.
  uint32_t tries = 0;
  uint32_t count = 0;
  while (tries < 10 && count < NUM_CONSECUTIVE_ONES) {
    tries++;

    // Produce the SCL clocks. Read SDA while SCL is high since the slave
    // will not change SDA while SCL is high.
    // If the I2C SDA line is low, start over and try again.
    bool success = true;
    for (count = 0; count < NUM_CONSECUTIVE_ONES && success; count++) {
      delayUs(HALF_PERIOD);          // Hold clock high
      success = readPin(i2c2_sda_);  // Start over if SDA low
      writePin(i2c2_scl_, false);    // Falling edge on the I2C clock line
      delayUs(HALF_PERIOD);          // Hold clock low
      writePin(i2c2_scl_, true);     // Rising edge on the I2C clock line
    }
  }

  delayUs(HALF_PERIOD);        // Hold time for clock and data high
  writePin(i2c2_sda_, false);  // Falling edge on SDA while SCL is high: START
  delayUs(HALF_PERIOD * 2);    // Double hold time for clock high and data low
  writePin(i2c2_sda_, true);   // Rising edge on SDA while SCL is high: STOP
  delayUs(HALF_PERIOD);        // Hold time for clock and data high.

  // Initialize the STM32's I2C2 bus as a master and control pins by peripheral
  initI2C2();
  configI2C2Pins();
}

bool isDPotSMBus() {
  return dpot_type_ == DPOT_MCP40D17;
}

static void updateDPot(uint8_t val) {
  // Unfortunately multiple types of DPots exist. Keep track of what's
  // present and what's been tried.
  static uint8_t dpot_val = DEFAULT_DPOT_VAL;

  // If a DPot hasn't been found, check for one. Try the MCP4017 first.
  static DPotType dpot_check = DPOT_MCP4017;

  bool update = dpot_val != val;  // Only write when necessary
  if ((dpot_type_ == DPOT_MCP4017 && update) || dpot_check == DPOT_MCP4017) {
    uint32_t err = writeByteI2C2(dpot_dev_, val);
    if (err) {
      // Couldn't communicate to MCP4017, assume it's not present
      // and try MCP40D17 next.
      dpot_type_ = DPOT_NONE;
      dpot_check = DPOT_MCP40D17;
      dpot_val   = DEFAULT_DPOT_VAL;
    } else {
      // Updated MCP4017! We know it's present now.
      dpot_type_ = DPOT_MCP4017;
      dpot_check = DPOT_NONE;
      dpot_val   = val;
    }
  } else if ((dpot_type_ == DPOT_MCP40D17 && update) ||
             dpot_check == DPOT_MCP40D17) {
    uint32_t err = writeRegI2C2(dpot_cmd_, val);
    if (err) {
      // Couldn't communicate to MCP40D17, assume it's not present
      // and try MCP4017 next.
      dpot_type_ = DPOT_NONE;
      dpot_check = DPOT_MCP4017;
      dpot_val   = DEFAULT_DPOT_VAL;
    } else {
      // Updated MCP40D17! We know it's present now.
      dpot_type_ = DPOT_MCP40D17;
      dpot_check = DPOT_NONE;
      dpot_val   = val;
    }
  }
}

void initInternalI2C() {
  // Make sure any interrupted transactions are cleared out
  quiesceI2C();

  // Set the direction for the power board GPIO
  writeRegI2C2(pwr_io_dir_, 0x7C);  // 0=output, 1=input

  initLeds();
  initAdc();
  updateInternalI2C();
}

void updateInternalI2C() {
  /* I2C transaction times (us):
   *   writeRegI2C2() 92.5
   *   readRegI2C2()  132
   *   updateAdc()    242
   *   writeDpot()    65.8
   */
  uint32_t mod8 = millis() & ((1 << 3) - 1);
  if (mod8 == 0) {
    // Read ADC and update fans every 8 ms
    updateAdc();

    // The two amp heatsinks can be combined by simply taking the max
    int16_t amp1t       = getAmp1Temp_f8();
    int16_t amp2t       = getAmp2Temp_f8();
    int16_t amp_temp_f8 = amp1t > amp2t ? amp1t : amp2t;

    // Update fans based on temps. Ideally use a DPot for linear control.
    uint8_t dpot_val = updateFans(amp_temp_f8, getHV1Temp_f8(), getPiTemp_f8(),
                                  dpot_type_ != DPOT_NONE);
    updateDPot(dpot_val);
  } else {
    // Read the power board's GPIO inputs
    GpioReg pwr_gpio = {.data = readRegI2C2(pwr_io_gpio_)};
    if (getFanCtrl() != FAN_CTRL_MAX6644) {
      // No fan control IC to determine this
      pwr_gpio.fan_fail_n = !false;
      pwr_gpio.ovr_tmp_n  = !false;
    }
    setPwrGpio(pwr_gpio);

    // Update the LED Board's LED state (possible I2C write)
    updateLeds();
  }

  // Update the Power Board's GPIO outputs, only writing when necessary
  GpioReg gpio_request = {
      .en_9v  = true,  // Always enable 9V
      .en_12v = true,  // Always enable 12V
      .fan_on = getFanOnFromDuty(),
  };
  if (gpio_request.data != (PWR_GPIO_OUT_MASK & getPwrGpio().data)) {
    writeRegI2C2(pwr_io_gpio_, gpio_request.data);
  }

  updateAudio();
}
