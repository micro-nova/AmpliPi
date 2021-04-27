/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Port usage and functions for GPIO
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

#ifndef PORTS_H_
#define PORTS_H_

#include <stdbool.h>
#include <stdint.h>

typedef struct{
	char port; // Valid ports in our case are A,B,C,D,F
	unsigned char pin : 4;
}Pin;

void setPin(Pin pp);
void clearPin(Pin pp);
bool readPin(Pin pp);

typedef struct{
	uint8_t dev;
	uint8_t reg;
}I2CReg;

int readI2C2(I2CReg r);
void writeI2C2(I2CReg r, uint8_t data);
void writeI2C1(uint8_t data);

#endif /* PORTS_H_ */
