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

#ifndef CTRL_I2C_H_
#define CTRL_I2C_H_

#include <stdbool.h>
#include <stdint.h>

#include "fans.h"
#include "port_defs.h"
#include "ports.h"

typedef struct {
  PwrGpio  pwr_gpio;   // Power Board GPIO expander's state
  LedGpio  leds;       // LED Board's state
  Expander expansion;  // Expansion connector settings
  uint8_t  hv1;        // High-voltage in Q6.2 Volts
  union {
    // All temps in UQ7.1 + 20 degC format
    struct {
      uint8_t hv1_temp;   // PSU temp
      uint8_t amp_temp1;  // Amp heatsink 1 temp
      uint8_t amp_temp2;  // Amp heatsink 2 temp
      uint8_t pi_temp;    // Control board Raspberry Pi temp
    };
    uint8_t temps[4];  // All temperatures in 1 array
  };
  uint8_t   i2c_addr;      // Slave I2C1 address
  bool      led_override;  // Override LED Board logic and force to 'leds'
  bool      fan_override;  // Override fan control logic and force 100% on
  FanState* fans;
} AmpliPiState;

void ctrlI2CInit(uint8_t addr);
bool ctrlI2CAddrMatch();
void ctrlI2CTransact(AmpliPiState* state);

#endif /* CTRL_I2C_H_ */
