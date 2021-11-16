/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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
#include "serial.h"
#include "systick.h"

bool led_override_ = false;
Leds leds_;

void setLedOverride(bool override) {
  led_override_ = override;
}

bool getLedOverride() {
  return led_override_;
}

void setLeds(Leds leds) {
  leds_ = leds;
}

Leds getLeds() {
  return leds_;
}

Leds updateLeds() {
  if (led_override_) {
    return leds_;
  }

  leds_.grn = inStandby() ? 0 : 1;
  if (getI2C1Address()) {
    leds_.red = !leds_.grn;
  } else {
    // Blink red light at ~0.5 Hz
    uint32_t mod2k = millis() & ((1 << 11) - 1);
    leds_.red      = mod2k > (1 << 10);
  }

  leds_.zones = 0;
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    leds_.zones |= (muted(zone) ? 0 : 1) << zone;
  }
  return leds_;
}
