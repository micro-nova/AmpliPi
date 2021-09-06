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

#define VERSION_MAJOR 0x01
#define VERSION_MINOR 0x01

/* Last 4 bytes of the version:
 * - 7 hex digits of the git hash, as returned from `git rev-parse --short HEAD`
 * - A dirty bit, if set the git hash is to be treated as invalid
 */
#define GIT_HASH_6_5 0xf4
#define GIT_HASH_4_3 0x66
#define GIT_HASH_2_1 0x12
#define GIT_HASH_0_D 0xd0  // LSB is dirty bit

#endif /* VERSION_H_ */
