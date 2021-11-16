/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Configure each of the preamp controller's six zones.
 * Each zone has four configurable properties:
 *   - Attenuation
 *   - Standby
 *   - Mute
 *   - Audio Source
 *
 * Also controls each of the 4 audio sources.
 * Each source can have an analog or digital source selected as its input.
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

#include "audio.h"

#include "i2c.h"
#include "pins.h"
#include "systick.h"

// The minimum volume. Volume range is [-80, 0] dB.
// 0 dB is no attenuation so max volume. -80 dB corresponds to mute.
#define DEFAULT_VOL 80

// The source to connect all zones to at startup
#define DEFAULT_SOURCE 0

const I2CReg zone_left_[NUM_ZONES] = {
    {0x88, 0x00}, {0x88, 0x02}, {0x88, 0x04},
    {0x8A, 0x00}, {0x8A, 0x02}, {0x8A, 0x04},
};

const I2CReg zone_right_[NUM_ZONES] = {
    {0x88, 0x01}, {0x88, 0x03}, {0x88, 0x05},
    {0x8A, 0x01}, {0x8A, 0x03}, {0x8A, 0x05},
};

// Keep track of volumes so they are not lost when we standby
uint8_t volumes[NUM_ZONES];

// Mute the specified zone
void mute(size_t zone, bool mute) {
  // Set pin low to mute
  writePin(zone_mute_[zone], !mute);
}

bool muted(size_t zone) {
  return !readPin(zone_mute_[zone]);
}

// Writes volume level to the volume ICs via the internal I2C bus
void writeVolume(size_t zone, uint8_t vol) {
  // We can't write to the volume registers if they are disabled
  if (!inStandby()) {
    writeRegI2C2(zone_left_[zone], vol);
    writeRegI2C2(zone_right_[zone], vol);
  }
}

// Standby all amps at once
void standby(bool standby) {
  bool prev_stby_state = inStandby();
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // Set pin low to standby
    writePin(zone_standby_[zone], !standby);
  }
  // After returning from standby we need to configure each of the volumes again
  if (prev_stby_state && !standby) {
    for (size_t zone = 0; zone < NUM_ZONES; zone++) {
      writeVolume(zone, volumes[zone]);
    }
  }
}

// Checks if any of the zones are in standby
bool inStandby() {
  bool in_stby = false;
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    in_stby = in_stby || (!readPin(zone_standby_[zone]));
  }
  return in_stby;
  // TODO: Shortcut
}

// Initialize each zone's volume state (does not write to volume control ICs)
void initZones() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    volumes[zone] = DEFAULT_VOL;
    mute(zone, true);
    setZoneSource(zone, DEFAULT_SOURCE);
  }
  standby(true);
}

// Set a zone's volume (required I2C write)
void setZoneVolume(size_t zone, uint8_t vol) {
#ifdef AUTO_MUTE_CTRL
  // Automatic On-Off control
  if (vol > 78) {
    mute(zone, true);
  } else if (!IsOn(zone)) {
    mute(zone, false);
  }
#endif

  // Keep track of the volume so it is not lost when we standby
  volumes[zone] = vol;

  // Actually write the volume to the volume control IC
  writeVolume(zone, vol);
}

uint8_t getZoneVolume(size_t zone) {
  return volumes[zone];
}

// Connect a Zone to a Source
void setZoneSource(size_t zone, size_t src) {
  // Mute the zone during the switch to avoid an audible pop
  bool was_muted = muted(zone);
  mute(zone, !was_muted);

  // Disconnect zone from all sources first
  for (size_t src = 0; src < NUM_SRCS; src++) {
    writePin(zone_src_[zone][src], false);
  }

  // Connect a zone to a source
  if (src < NUM_SRCS) {
    writePin(zone_src_[zone][src], true);
  }

  // Restore mute status
  mute(zone, was_muted);
}

size_t getZoneSource(size_t zone) {
  // Assume only one source is ever selected
  for (size_t src = 0; src < NUM_SRCS; src++) {
    if (readPin(zone_src_[zone][src])) {
      return src;
    }
  }
  return 0;  // Should never be reached
}

// Initialize each source's analog/digital state
void initSources() {
  for (size_t src = 0; src < NUM_SRCS; src++) {
    setSourceAD(src, IT_DIGITAL);
  }
}

// Each source can select between a digital or analog input
void setSourceAD(size_t src, InputType type) {
  // Disable both mux inputs first
  writePin(src_ad_[src][IT_ANALOG], false);
  writePin(src_ad_[src][IT_DIGITAL], false);

  // Enable selected input
  writePin(src_ad_[src][type], true);
}

InputType getSourceAD(size_t src) {
  // Assume only one input is ever selected
  if (readPin(src_ad_[src][IT_DIGITAL])) {
    return IT_DIGITAL;
  }
  return IT_ANALOG;
}
