/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Pin definitions and functions
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

#ifndef PINS_H_
#define PINS_H_

#include <stdbool.h>
#include <stdint.h>

#include "audio.h"  // NUM_ZONES, NUM_SRCS

typedef struct {
  char    port;  // Valid ports in our case are A,B,C,D,F
  uint8_t pin : 4;
} Pin;

extern const Pin zone_src_[NUM_ZONES][NUM_SRCS];  // Source[1-4]->Zone mux
extern const Pin zone_mute_[NUM_ZONES];
extern const Pin zone_standby_[NUM_ZONES];
extern const Pin src_ad_[NUM_SRCS][2];  // Analog/Digital->Source mux
extern const Pin exp_nrst_;             // Expansion connector NRST_OUT
extern const Pin exp_boot0_;            // Expansion connector BOOT0_OUT
extern const Pin i2c2_scl_;             // Internal I2C bus SCL
extern const Pin i2c2_sda_;             // Internal I2C bus SDA

// Pin configuration
void initPins();
void configUARTPins();
void configI2C1Pins();
void configI2C2Pins();
void configI2C2PinsAsGPIO();

void writePin(Pin pp, bool set);
bool readPin(Pin pp);

#endif /* PINS_H_ */
