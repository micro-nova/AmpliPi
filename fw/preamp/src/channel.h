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

#ifndef CHANNEL_H_
#define CHANNEL_H_
// Uncomment this line to enable automatic mute control via high/low volume.
// #define AUTO_MUTE_CTRL

#include <stdint.h>

typedef enum{IT_ANALOG, IT_DIGITAL} InputType;

bool isOn(int ch);
bool anyOn();

void standby();
void unstandby();

void mute(int ch);
void unmute(int ch);

void initChannels();
void initSources();
void setChannelVolume(int ch_out, uint8_t vol);
void configInput(int src, InputType type);
void connectChannel(int ch_in, int ch_out);

#endif /* CHANNEL_H_ */
