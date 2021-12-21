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

// -80 is a special value that means mute, and actually sets -90 dB.
#define VOL_MUTE 80

// Zone volumes, range is [-80, 0] dB with 0 as the max (no attenuation).
// Requested volume for each zone, default to  mute (-90 dB)
uint8_t vol_req_[NUM_ZONES] = {VOL_MUTE};

// Actual volume (last written via I2C)
// The TDA7448 volume controller always reports 0x00 on read
uint8_t vol_[NUM_ZONES] = {0};

// If only preouts are used, the amplifier for a zone can be disabled
bool amp_en_[NUM_ZONES] = {};

// Convert a requested dB to the corresponding volume IC register value.
static inline uint8_t dB2VolReg(uint8_t db) {
  /* The volume IC has a discontinuity in its register value to attenuation
   * conversion after -71dB. To set -72dB the value 128 must be written.
   * Aditionally, mute (-90dB) is set by any value 192 to 255.
   */
  uint8_t vol_reg;
  if (db < 72) {
    vol_reg = db;
  } else if (db < 80) {
    vol_reg = db + 56;
  } else {
    vol_reg = 255;
  }
  return vol_reg;
}

// Convert a requested dB to the corresponding volume IC register value.
static inline uint8_t volReg2dB(uint8_t vol) {
  uint8_t db;
  if (vol < 72) {
    db = vol;
  } else if (vol < 80 + 56) {
    db = vol - 56;
  } else {
    db = 80;
  }
  return db;
}

// Writes volume level to the volume ICs via the internal I2C bus
static bool writeVolume(size_t zone, uint8_t vol) {
  // Convert dB to volume controller register value
  uint8_t vol_reg = dB2VolReg(vol);

  bool success = writeRegI2C2(zone_left_[zone], vol_reg) == 0 &&
                 writeRegI2C2(zone_right_[zone], vol_reg) == 0;
  return success;
}

// Set a zone's volume from 0 to 80
void setZoneVolume(size_t zone, uint8_t vol) {
  // Request a volume change
  vol_req_[zone] = vol;
}

uint8_t getZoneVolume(size_t zone) {
  if (muted(zone)) {
    // If muted the real volume will be VOL_MUTE.
    // Instead, report to the user the value which will be set upon unmuting.
    return vol_req_[zone];
  } else {
    return vol_[zone];
  }
}

// All amps must be in standby together due to the SYNCLK
static void standby(bool standby) {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // Set pin low to standby
    writePin(zone_standby_[zone], !standby);
  }
}

// Checks if any of the zones are in standby
bool inStandby() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // Standby pins are active-low
    if (!readPin(zone_standby_[zone])) {
      return true;
    }
  }
  return false;
}

// Returns true if any zone is unmuted and has amps enabled
static bool anyZoneAmpOn() {
  for (uint8_t zone = 0; zone < NUM_ZONES; zone++) {
    if (!muted(zone) && amp_en_[zone]) {
      return true;
    }
  }
  return false;
}

void enZoneAmp(size_t zone, bool en) {
  amp_en_[zone] = en;

  // If no zones are on, standby
  standby(!anyZoneAmpOn());
}

bool zoneAmpEnabled(size_t zone) {
  return amp_en_[zone];
}

// Mute the specified zone
void mute(size_t zone, bool mute) {
  // Set pin low to mute
  writePin(zone_mute_[zone], !mute);

  // If no zones are on, standby
  standby(!anyZoneAmpOn());
}

bool muted(size_t zone) {
  // Mute pins are active-low
  return !readPin(zone_mute_[zone]);
}

// Connect a Zone to a Source
void setZoneSource(size_t zone, size_t src) {
  // Mute the zone during the switch to avoid an audible pop
  bool was_muted = muted(zone);
  mute(zone, true);

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

void initAudio() {
  // Initialize each zone's audio state (does not write to volume control ICs)
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    enZoneAmp(zone, true);
    mute(zone, true);
    setZoneSource(zone, DEFAULT_SOURCE);
  }

  /* Initialize each source's analog/digital mux to select digital.
   * Upon AmpliPi startup the digital input won't have any audio playing so
   * selecting digital avoids unwanted playback.
   * Also audio is input to expanders through the digital inputs,
   * so analog inputs must never be selected.
   * This firmware supports both main units and expanders.
   */
  for (size_t src = 0; src < NUM_SRCS; src++) {
    setSourceAD(src, IT_DIGITAL);
  }
}

void updateAudio() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // The mute pin only affects the amps, set the volume to mute for preouts
    if (muted(zone)) {
      if (vol_[zone] != VOL_MUTE && writeVolume(zone, VOL_MUTE)) {
        vol_[zone] = VOL_MUTE;
      }
    } else if (vol_[zone] != vol_req_[zone]) {
      // Actually write the volume to the volume control IC
      if (writeVolume(zone, vol_req_[zone])) {
        vol_[zone] = vol_req_[zone];
      }
    }
  }
}
