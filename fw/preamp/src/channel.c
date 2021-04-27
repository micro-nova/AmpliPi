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

#include <stdbool.h>
#include "channel.h"
#include "ports.h"
#include "front_panel.h"
#include "port_defs.h"

#define DEFAULT_VOL (79) // The minimum volume. Scale goes from 0-79 with 0 being maximum

// Keep track of volumes so they are not lost when we standby
uint8_t volumes[NUM_CHANNELS];

static void writeVolume(int ch, uint8_t vol);
static void restoreVolumes();

// returns true if ch unmuted (HI)
bool isOn(int ch){
	return readPin(ch_mute[ch]);
}

//static inline bool isMuted(int ch){
//	return !isOn(ch);
//}

// returns true if any ch unmuted (HI)
bool anyOn(){
	bool on = false;
	uint8_t ch;
	for(ch = 0; ch < NUM_CHANNELS; ch++){
		on = on | isOn(ch);
	}
	return on;
}

//static inline bool allMuted(){
//	return !anyOn();
//}

// pull all pins LOW to standby all amps
void standby(){
	uint8_t ch;
	for(ch = 0; ch < NUM_CHANNELS; ch++){
		clearPin(ch_standby[ch]);
	}
	delay(16000); // 8000 is the cutoff value at which the delay prevents speaker popping. 2x factor for safety.
	setAudioPower(OFF);
}

// pull all pins HI to un-standby all amps
void unstandby(){
	setAudioPower(ON);
	uint8_t ch;
	for(ch = 0; ch < NUM_CHANNELS; ch++){
		setPin(ch_standby[ch]);
	}
	// After returning from standby we need to configure each of the volumes again
	restoreVolumes();
}

bool instandby(){
	// Checks if any of the channels are in standby
	uint8_t ch;
	bool in_stby = false;
	for(ch = 0; ch < NUM_CHANNELS; ch++){
		in_stby = in_stby || (!readPin(ch_standby[ch]));
	}
	return in_stby;
}

static inline void quick_mute(int ch){
	clearPin(ch_mute[ch]);
}

static inline void quick_unmute(int ch){
	setPin(ch_mute[ch]);
}

// pull pin LOW to mute
void mute(int ch){
	quick_mute(ch);
	updateFrontPanel(true);
}

// pull pin HI to unmute
void unmute(int ch){
	quick_unmute(ch);
	updateFrontPanel(true);
}

void writeVolume(int ch, uint8_t vol){
	// Writes volume level to the volume ICs
	if (!instandby()){ // we can't write to the volume registers if they are disabled
		writeI2C2(ch_left[ch], vol);
		writeI2C2(ch_right[ch], vol);
	}
}

static void restoreVolumes() {
	// restores the volume state when returning from standby
	uint8_t ch;
	for (ch = 0; ch < NUM_CHANNELS; ch++) {
		writeVolume(ch, volumes[ch]);
	}
}

void initChannels(){
	// initialize each channel's volume state (does not write to volume control ICs)
	uint8_t ch;
	for (ch = 0; ch < NUM_CHANNELS; ch++) {
		volumes[ch] = DEFAULT_VOL;
		connectChannel(0,  ch);
		mute(ch);
	}
	standby();
}

void initSources(){
	// initialize each source's analog/digital state
	uint8_t src;
	for (src=0; src < NUM_SRCS; src++) {
		configInput(src, IT_DIGITAL);
	}
}

void setChannelVolume(int ch, uint8_t vol){
#ifdef AUTO_MUTE_CTRL
	// automatic On-Off control
	if (vol > 78){
		mute(ch);
	} else if (!isOn(ch)){
		unmute(ch);
	}
#endif

	// keep track of the volume so it is not lost when we standby
	volumes[ch] = vol;

	// actually write the volume to the volume control IC
	writeVolume(ch, vol);
}

static inline void clearConnection(int src, int ch){
	// Removes a source/channel dependency
	clearPin(ch_src[ch][src]);
}

static inline void addConnection(int src, int ch){
	// Connects a source to a channel
	setPin(ch_src[ch][src]);
}

void configInput(int src, InputType type){
	// each input can select between a digital source and an analog one
	switch(type){
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

void connectChannel(int src, int ch){
	// mute the channel during the switch to avoid an audible pop
	bool was_unmuted = isOn(ch);
	if (was_unmuted) {
		quick_mute(ch);
	}

	uint8_t asrc;
	for(asrc = 0; asrc < NUM_SRCS; asrc++){
		clearConnection(asrc, ch);
	}

	if(src < NUM_SRCS){
		addConnection(src, ch);
	}

	if (was_unmuted) {
		quick_unmute(ch);
	}

}
