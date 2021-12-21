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

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "audio.h"
#include "ctrl_i2c.h"
#include "int_i2c.h"
#include "pins.h"
#include "serial.h"
#include "systick.h"

int main(void) {
  // TODO: Setup watchdog

  // RESET AND PIN SETUP
  writePin(exp_nrst_, false);   // Low-pulse on NRST_OUT so expansion boards are
                                // reset by the controller board
  writePin(exp_boot0_, false);  // Needs to be low so the subsequent preamp
                                // board doesn't start in 'Boot Mode'

  // INIT
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality
  initPins();     // UART and I2C require GPIO pins
  initAudio();    // Initialize audio mux, volumes, mute and standby
  initUart1();    // The preamp will receive its I2C network address via UART
  initUart2(9600);
  initInternalI2C();  // Setup the internal I2C bus - worst case ~2.2 ms

  // RELEASE EXPANSION RESET
  // Needs to be high so the subsequent preamp board is not held in 'Reset Mode'
  writePin(exp_nrst_, true);

  // Main loop, awaiting I2C commands
  uint32_t next_loop_time = millis();
  while (1) {
    // TODO: Clear watchdog

    // Use EXP_BOOT0 as a timer - 4.25 us just for pin set/reset
    // writePin(exp_boot0_, true);

    // Check for incoming UART messages (setting the slave address)
    if (checkForNewAddress()) {
      ctrlI2CInit();
    }

    // Check for incoming control messages if a slave address has been set
    if (getI2C1Address() && ctrlI2CAddrMatch()) {
      ctrlI2CTransact();
    }

    updateInternalI2C();

    // writePin(exp_boot0_, false);
    next_loop_time += 1;  // Loop currently takes ~800 us
    while (millis() < next_loop_time) {}
  }
}
