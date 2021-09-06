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

#ifndef FRONT_PANEL_H_
#define FRONT_PANEL_H_

#include <stdbool.h>

#include "port_defs.h"

#define ON  (true)
#define OFF (false)

void setAudioPower(bool on);

void enableFrontPanel();
void updateFrontPanel(bool on);

#endif /* FRONT_PANEL_H_ */
