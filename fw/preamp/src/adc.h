/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * ADC related functions including reading the I2C ADC, voltage and temperature
 * conversions, and a thermistor temperature conversion look-up table.
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

#ifndef ADC_H_
#define ADC_H_

#include <stdint.h>

void initAdc();
void updateAdc();

uint8_t getHV1_f2();
uint8_t getHV1Temp_f1();
int16_t getHV1Temp_f8();
uint8_t getAmp1Temp_f1();
int16_t getAmp1Temp_f8();
uint8_t getAmp2Temp_f1();
int16_t getAmp2Temp_f8();
uint8_t getPiTemp_f1();
int16_t getPiTemp_f8();
void    setPiTemp_f1(uint8_t temp_f1);

#endif /* ADC_H_ */
