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

#include "adc.h"
#include "audio.h"
#include "fans.h"
#include "i2c.h"
#include "leds.h"
#include "pins.h"
#include "pwr_gpio.h"
#include "serial.h"
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

uint8_t i2c_dev_present_[16] = {};

uint8_t isInternalI2CDevPresent(uint8_t addr) {
  return i2c_dev_present_[addr];
}

//#define SCAN_I2C
#ifdef SCAN_I2C

#ifdef DEBUG_PRINT
#include <stdio.h>
#else
// TODO: The I2C scanning only works if DEBUG_PRINT is enabled. Timing issue?
#error "SCAN_I2C enabled but DEBUG_PRINT not enabled"
#endif

// Devices used in AmpliPi so far: (address are in LSB position)
// MCP23008 GPIO: 0x20-0x27
// MCP4017  DPOT: 0x2E-0x2F
// TDA7448   VOL: 0x44-0x45
// MAX1160X ADC : 0x64-0x65, 0x6D
bool scan_i2c() {
  // Scan I2C1 for valid device addresses 0x08-0x77
  // (0x00-0x07 and 0x78-0x7F are reserved)
  // TODO: When set to 0x08 something is found at 0x0D and then this crashes...
  static uint8_t a = 0x20;

  // Wait for bus free
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Send a start condition, the address (0 bytes of data), and a stop condition
  I2C2->CR2 = I2C_CR2_AUTOEND | I2C_CR2_STOP | I2C_CR2_START | (a << 1);

  // Wait for stop condition
  uint32_t isr   = I2C2->ISR;
  bool     error = false;
  do {
    isr = I2C2->ISR;
    if (isr & I2C_ISR_NACKF) {
      I2C2->ICR = I2C_ICR_NACKCF;
      error     = true;
      break;
    }
    if (isr & I2C_ISR_BERR) {
      I2C2->ICR = I2C_ICR_BERRCF;
      error     = true;
      debug_print("BERR\r\n");
      break;
    }
    if (isr & I2C_ISR_ARLO) {
      I2C2->ICR = I2C_ICR_ARLOCF;
      error     = true;
      debug_print("ARLO\r\n");
      break;
    }
  } while (!(isr & I2C_ISR_STOPF));

  // Clear detected stop condition
  I2C2->ICR = I2C_ICR_STOPCF;

  if (!error) {
    // ACK was received, a device must be present
    i2c_dev_present_[a >> 3] |= (1 << (a & 0x7));
#ifdef DEBUG_PRINT
    static char str[32] = {};
    snprintf(str, sizeof(str), "Found I2C dev @0x%02X\r\n", a << 1);
    debug_print(str);
#endif
  }

  a++;
  if (a < 0x78) {
    return false;
  }
  debug_print("Finished I2C scan\r\n");
  return true;
}
#endif  // SCAN_I2C

void initInternalI2C() {
  // Make sure any interrupted transactions are cleared out
  quiesceI2C();

  // Set the direction for the power board GPIO
  writeRegI2C2(pwr_io_dir_, 0x7C);  // 0=output, 1=input

  initLeds();
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

    // Update fans based on temps. Ideally use a DPot for linear control.
    uint8_t dpot_val = updateFans(dpot_type_ != DPOT_NONE);
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

#ifdef SCAN_I2C
  static bool i2c_scan_done = false;
  if (!i2c_scan_done) {
    i2c_scan_done = scan_i2c();
  }
#endif  // SCAN_I2C
}
