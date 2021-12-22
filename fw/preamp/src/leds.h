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

#ifndef LEDS_H_
#define LEDS_H_

#include <stdbool.h>
#include <stdint.h>

typedef union {
  struct {
    uint8_t grn   : 1;
    uint8_t red   : 1;
    uint8_t zones : 6;
  };
  uint8_t data;
} Leds;

void setLedOverride(bool override);
bool getLedOverride();
void setLeds(Leds leds);
Leds getLeds();

void initLeds();
void updateLeds();

#endif /* LEDS_H_ */
