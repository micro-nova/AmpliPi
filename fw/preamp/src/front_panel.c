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

#include "front_panel.h"

#include "channel.h"
#include "ports.h"
#include "systick.h"

bool audio_power_on_ = false;

// Enables/disables the 9V power supply along with the green LED
void setAudioPower(bool on) {
  audio_power_on_ = on;
  updateFrontPanel(!on);
  if (on) {
    delay_ms(250);  // Need time for volume IC to turn on
  }
}

// Init the I2C->GPIO IC on the led board
// This IC controls all the LEDs on the front of the box
// This sets all GPIO pins to output
void enableFrontPanel() {
  writeI2C2(front_panel_dir, ALL_OUTPUT);
}

// Updates the LEDs on the front panel depending on the system state
void updateFrontPanel(bool red_on) {
  // bit 0: Green "System On" LED
  // bit 1: Red "System Standby" LED
  // bits 2-7: channels 1 to 6 (in that corresponding order)

  // Turn off the RED LED when the GREEN LED is going to be on
  if (audio_power_on_ == true) {
    red_on = false;
  }

  // Green LED if the system is not in standby
  uint8_t bits = audio_power_on_ ? 1 : 0;

  // Red LED for general power. Blinks while waiting for an I2C address from the
  // controller board
  bits |= red_on ? 2 : 0;

  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    bits |= (isOn(ch) ? 1 : 0) << (ch + 2);
  }

  writeI2C2(front_panel, bits);
}
