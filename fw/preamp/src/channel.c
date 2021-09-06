/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Configure each of the preamp controller's six channels.
 * Each channel has four configurable properties:
 *   - Attenuation
 *   - Standby
 *   - Mute
 *   - Audio Source
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

#include "channel.h"

#include "front_panel.h"
#include "port_defs.h"
#include "ports.h"
#include "systick.h"

// The minimum volume. Scale goes from 0-79 with 0 being maximum
#define DEFAULT_VOL 79

// Keep track of volumes so they are not lost when we standby
uint8_t volumes[NUM_CHANNELS];

static void writeVolume(int ch, uint8_t vol);
static void restoreVolumes();

// Returns true if ch unmuted (HI)
bool isOn(int ch) {
  return readPin(ch_mute[ch]);
}

// Returns true if any ch unmuted (HI)
bool anyOn() {
  bool on = false;
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    on = on | isOn(ch);
  }
  return on;
}

// Pull all pins LOW to standby all amps
void standby() {
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    clearPin(ch_standby[ch]);
  }
  // 16ms is the cutoff value at which the delay prevents speaker popping.
  // 2x factor for safety.
  delay_ms(32);
  setAudioPower(OFF);
}

// Pull all pins HI to un-standby all amps
void unstandby() {
  setAudioPower(ON);
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    setPin(ch_standby[ch]);
  }
  // After returning from standby we need to configure each of the volumes again
  restoreVolumes();
}

// Checks if any of the channels are in standby
bool inStandby() {
  bool in_stby = false;
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    in_stby = in_stby || (!readPin(ch_standby[ch]));
  }
  return in_stby;
}

static inline void quick_mute(int ch) {
  clearPin(ch_mute[ch]);
}

static inline void quick_unmute(int ch) {
  setPin(ch_mute[ch]);
}

// Pull pin LOW to mute
void mute(int ch) {
  quick_mute(ch);
  updateFrontPanel(true);
}

// Pull pin HI to unmute
void unmute(int ch) {
  quick_unmute(ch);
  updateFrontPanel(true);
}

// Writes volume level to the volume ICs
void writeVolume(int ch, uint8_t vol) {
  // We can't write to the volume registers if they are disabled
  if (!inStandby()) {
    writeI2C2(ch_left[ch], vol);
    writeI2C2(ch_right[ch], vol);
  }
}

// Restores the volume state when returning from standby
static void restoreVolumes() {
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    writeVolume(ch, volumes[ch]);
  }
}

// Initialize each channel's volume state (does not write to volume control ICs)
void initChannels() {
  for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
    volumes[ch] = DEFAULT_VOL;
    connectChannel(0, ch);
    mute(ch);
  }
  standby();
}

// Initialize each source's analog/digital state
void initSources() {
  for (uint8_t src = 0; src < NUM_SRCS; src++) {
    configInput(src, IT_DIGITAL);
  }
}

void setChannelVolume(int ch, uint8_t vol) {
#ifdef AUTO_MUTE_CTRL
  // Automatic On-Off control
  if (vol > 78) {
    mute(ch);
  } else if (!isOn(ch)) {
    unmute(ch);
  }
#endif

  // Keep track of the volume so it is not lost when we standby
  volumes[ch] = vol;

  // Actually write the volume to the volume control IC
  writeVolume(ch, vol);
}

// Removes a source/channel dependency
static inline void clearConnection(int src, int ch) {
  clearPin(ch_src[ch][src]);
}

// Connects a source to a channel
static inline void addConnection(int src, int ch) {
  setPin(ch_src[ch][src]);
}

// Each input can select between a digital source and an analog one
void configInput(int src, InputType type) {
  switch (type) {
    case IT_ANALOG:
      setPin(src_aen[src]);
      clearPin(src_den[src]);
      break;
    case IT_DIGITAL:
      setPin(src_den[src]);
      clearPin(src_aen[src]);
      break;
  }
}

// Mute the channel during the switch to avoid an audible pop
void connectChannel(int src, int ch) {
  bool was_unmuted = isOn(ch);
  if (was_unmuted) {
    quick_mute(ch);
  }

  for (uint8_t asrc = 0; asrc < NUM_SRCS; asrc++) {
    clearConnection(asrc, ch);
  }

  if (src < NUM_SRCS) {
    addConnection(src, ch);
  }

  if (was_unmuted) {
    quick_unmute(ch);
  }
}
