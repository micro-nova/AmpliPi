/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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

#include <stdint.h>

#include "audio.h"
#include "ctrl_i2c.h"
#include "int_i2c.h"
#include "pins.h"
#include "serial.h"
#include "systick.h"

int main() {
  // TODO: Setup watchdog

  // RESET AND PIN SETUP
  initPins();                   // UART and I2C require GPIO pins
  writePin(exp_nrst_, false);   // Low-pulse on NRST_OUT so expansion boards are
                                // reset by the controller board
  writePin(exp_boot0_, false);  // Needs to be low so the subsequent preamp
                                // board doesn't start in 'Boot Mode'

  // INIT
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality
  initAudio();    // Initialize audio mux, volumes, mute and standby
  initUart1();    // The preamp will receive its I2C network address via UART
  initUart2(9600);
  initInternalI2C();  // Setup the internal I2C bus - worst case ~2.4 ms

  // RELEASE EXPANSION RESET
  // Needs to be high so the subsequent preamp board is not held in 'Reset Mode'
  writePin(exp_nrst_, true);

  // Main loop, awaiting I2C commands
  uint32_t next_loop_time = millis();
  uint8_t  i2c_addr       = 0;
  while (1) {
    // TODO: Clear watchdog

    // Use EXP_BOOT0 as a timer - 4.25 us just for pin set/reset
    // writePin(exp_boot0_, true);

    // Check if a new I2C slave address has been received over UART from the controller board.
    uint8_t new_i2c_addr = checkForNewAddress();
    if (new_i2c_addr != i2c_addr) {
      i2c_addr = new_i2c_addr;
      ctrlI2CInit(i2c_addr);

      // Increment this unit's address by 0x10 to get the address for the next preamp.
      sendAddressToSlave(i2c_addr + 0x10);
    }

    // Check for incoming control messages if a slave address has been set
    if (i2c_addr && ctrlI2CAddrMatch()) {
      ctrlI2CTransact();
    }

    updateInternalI2C(i2c_addr != 0);

    // writePin(exp_boot0_, false);
    next_loop_time += 1;  // Loop currently takes ~800 us
    while (millis() < next_loop_time) {}
  }
}
