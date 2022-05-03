/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * Front-panel LED status and control
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

#include "leds.h"

#include "audio.h"
#include "i2c.h"
#include "serial.h"
#include "systick.h"

// LED Board I2C registers
const I2CReg i2c_led_dir_reg_  = {0x40, 0x00};
const I2CReg i2c_led_gpio_reg_ = {0x40, 0x09};

bool led_override_   = false;
Leds leds_requested_ = {};
Leds leds_           = {};

void setLedOverride(bool override) {
  led_override_ = override;
}

bool getLedOverride() {
  return led_override_;
}

void setLeds(Leds leds) {
  leds_requested_ = leds;
}

Leds getLeds() {
  return leds_;
}

void initLeds() {
  // Set the LED Board's GPIO expander as all outputs
  writeRegI2C2(i2c_led_dir_reg_, 0x00);  // 0=output, 1=input

  // Initialize LEDs as all off
  writeRegI2C2(i2c_led_gpio_reg_, 0x00);
  leds_.data = 0;
}

void updateLeds() {
  // Determine the LEDs based on the system status, unless overriden.
  if (!led_override_) {
    leds_requested_.grn = inStandby() ? 0 : 1;
    if (getI2C1Address()) {
      leds_requested_.red = !leds_requested_.grn;
    } else {
      // Blink red light at ~0.5 Hz
      uint32_t mod2k      = millis() & ((1 << 11) - 1);
      leds_requested_.red = mod2k > (1 << 10);
    }

    leds_requested_.zones = 0;
    for (size_t zone = 0; zone < NUM_ZONES; zone++) {
      leds_requested_.zones |= (muted(zone) ? 0 : 1) << zone;
    }
  }

  if (leds_requested_.data != leds_.data) {
    // Attempt to update led board. If no errors update our state.
    if (writeRegI2C2(i2c_led_gpio_reg_, leds_requested_.data) == 0) {
      leds_ = leds_requested_;
    }
  }
}
