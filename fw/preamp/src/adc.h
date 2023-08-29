/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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

#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef union {
  // All temps in UQ7.1 + 20 degC format
  struct {
    uint8_t hv1_f1;   // PSU 1 temp (always present)
    uint8_t hv2_f1;   // PSU 2 temp (only present on high-power units)
    uint8_t amp1_f1;  // Amp heatsink 1 temp
    uint8_t amp2_f1;  // Amp heatsink 2 temp
    uint8_t pi_f1;    // Control board Raspberry Pi temp
  };
  uint8_t temps[5];  // All temperatures in 1 array
} Temps;

typedef union {
  // All temps in Q7.8 format
  struct {
    int16_t hv1_f8;   // PSU 1 temp (always present)
    int16_t hv2_f8;   // PSU 2 temp (only present on high-power units)
    int16_t amp1_f8;  // Amp heatsink 1 temp
    int16_t amp2_f8;  // Amp heatsink 2 temp
    int16_t pi_f8;    // Control board Raspberry Pi temp
  };
  int16_t temps[5];  // All temperatures in 1 array
} Temps16;

typedef union {
  // All voltages in UQ6.2 format
  struct {
    uint8_t hv1_f2;  // PSU 1 voltage (always present)
    uint8_t hv2_f2;  // PSU 2 voltage (only present on high-power units)
  };
  uint8_t voltages[2];  // All voltages in 1 array
} Voltages;

void      updateAdc();
Temps*    getTemps();    // UQ7.1 + 20 degC format
Temps16*  getTemps16();  // Q7.8 format
Voltages* getVoltages();
bool      isHV2Present();

void setPiTemp_f1(uint8_t temp_f1);

int16_t getHV1Temp_f8();
int16_t getHV2Temp_f8();
int16_t getAmp1Temp_f8();
int16_t getAmp2Temp_f8();
int16_t getPiTemp_f8();
