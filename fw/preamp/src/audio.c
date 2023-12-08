/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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
    {0x88, 0x00}, {0x88, 0x02}, {0x88, 0x04}, {0x8A, 0x00}, {0x8A, 0x02}, {0x8A, 0x04},
};

const I2CReg zone_right_[NUM_ZONES] = {
    {0x88, 0x01}, {0x88, 0x03}, {0x88, 0x05}, {0x8A, 0x01}, {0x8A, 0x03}, {0x8A, 0x05},
};

// -80 is a special value that means mute, and actually sets -90 dB.
#define VOL_MUTE 80

// Zone volumes, range is [-80, 0] dB with 0 as the max (no attenuation).
// Requested volume for each zone, default to  mute (-90 dB)
uint8_t vol_req_[NUM_ZONES] = {VOL_MUTE, VOL_MUTE, VOL_MUTE, VOL_MUTE, VOL_MUTE, VOL_MUTE};

// Actual volume (last written via I2C)
// The TDA7448 volume controller always reports 0x00 on read
uint8_t vol_[NUM_ZONES] = {};

// If any zone uses only the preout, the amp can be 'disabled' which will
// remove it from consideration for leaving standby.
// For example, consider zone 1 is 'disabled' but the rest are 'enabled'.
// If zone 1 is the only zone unmuted, the amps will remain in standby.
// The amps will exit standby if any other zone becomes unmuted.
// A second example:
// If all amps are 'disabled', then the amps will always remain in standby.
bool amp_en_[NUM_ZONES] = {true, true, true, true, true, true};

bool mux_en_level_ = true;
// Preamp boards >=Rev4 use a low-level signal to enable a mux, while
// <=Rev3 uses a high-level signal. Default to a high-level signal.
void audio_set_mux_en_level(bool level) {
  mux_en_level_ = level;
}
bool audio_get_mux_en_level() {
  return mux_en_level_;
}

// Convert a dB attenuation level to the corresponding volume IC register value.
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

// Convert a volume IC register value to the corresponding dB attenuation level.
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

  bool success =
      writeRegI2C2(zone_left_[zone], vol_reg) == 0 && writeRegI2C2(zone_right_[zone], vol_reg) == 0;
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
    pin_write(zone_standby_[zone], !standby);
  }
}

// Checks if any of the zones are in standby
bool inStandby() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // Standby pins are active-low
    if (!pin_read(zone_standby_[zone])) {
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
  pin_write(zone_mute_[zone], !mute);

  // If no zones are on, standby
  standby(!anyZoneAmpOn());
}

bool muted(size_t zone) {
  // Mute pins are active-low
  return !pin_read(zone_mute_[zone]);
}

// Connect a Zone to a Source
void setZoneSource(size_t zone, size_t src) {
  // Mute the zone during the switch to avoid an audible pop
  bool was_muted = muted(zone);
  mute(zone, true);

  // Disconnect zone from all sources first
  for (size_t src = 0; src < NUM_SRCS; src++) {
    pin_write(zone_src_[zone][src], !mux_en_level_);
  }

  // Connect a zone to a source
  if (src < NUM_SRCS) {
    pin_write(zone_src_[zone][src], mux_en_level_);
  }

  // Restore mute status
  mute(zone, was_muted);
}

size_t getZoneSource(size_t zone) {
  // Assume only one source is ever selected
  for (size_t src = 0; src < NUM_SRCS; src++) {
    if (pin_read(zone_src_[zone][src]) == mux_en_level_) {
      return src;
    }
  }
  return 0;  // Should never be reached
}

// Each source can select between a digital or analog input
void setSourceAD(size_t src, InputType type) {
  // Disable both mux inputs first
  pin_write(src_ad_[src][IT_ANALOG], !mux_en_level_);
  pin_write(src_ad_[src][IT_DIGITAL], !mux_en_level_);

  // Enable selected input
  pin_write(src_ad_[src][type], mux_en_level_);
}

InputType getSourceAD(size_t src) {
  // Assume only one input is ever selected
  if (pin_read(src_ad_[src][IT_DIGITAL]) == mux_en_level_) {
    return IT_DIGITAL;
  }
  return IT_ANALOG;
}

// Initialize audio mux. Must be done after determining the polarity of the mux enable signals.
void audio_muxes_init() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    setZoneSource(zone, DEFAULT_SOURCE);
  }

  // Initialize each source's analog/digital mux to select digital to avoid unwanted audio.
  // Also, expanders don't have analog inputs and so must never select analog.
  for (size_t src = 0; src < NUM_SRCS; src++) {
    setSourceAD(src, IT_DIGITAL);
  }
}

void audio_update() {
  for (size_t zone = 0; zone < NUM_ZONES; zone++) {
    // Check if volume update required
    uint8_t new_vol = vol_[zone];
    if (muted(zone)) {
      // The mute pin only affects the amps, set the volume to mute for preouts
      new_vol = VOL_MUTE;  // Instantly mute
    } else {
      // Only change volume 1 dB at a time to reduce crackling
      if (vol_[zone] < vol_req_[zone]) {
        new_vol = vol_[zone] + 1;
      } else if (vol_[zone] > vol_req_[zone]) {
        new_vol = vol_[zone] - 1;
      }
    }

    // Perform volume update if required
    if (vol_[zone] != new_vol && writeVolume(zone, new_vol)) {
      vol_[zone] = new_vol;
    }
  }
}
