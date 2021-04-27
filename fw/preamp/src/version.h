/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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

#ifndef VERSION_H_
#define VERSION_H_

#include "main.h"

// Potentially obsolete before it was even useful
#define VERSION_MAJOR 0x01 //            Major version, the 1 of 1.0
#define VERSION_MINOR 0x02 //            Minor version, the 2 of 1.2
#define GIT_HASH_27_20 0xfe //           Two leftmost hex digits of the commit hash string, 74 of 0x74568921
#define GIT_HASH_19_12 0xed //           Two following hex digits of the commit hash string, 56 of 0x74568921
#define GIT_HASH_11_04 0xdc //           Two following hex digits of the commit hash string, 89 of 0x74568921
#define GIT_HASH_03_00_STATUS 0xc1 //    The final hex digit of the commit hash string, as well as the "dirty" flag (LSB). 2 and 1 of 0x74568921

#endif /* VERSION_H_ */
