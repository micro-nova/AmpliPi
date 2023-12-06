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
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

#include <stdint.h>
#include <stdio.h>

#include "audio.h"
#include "ctrl_i2c.h"
#include "int_i2c.h"
#include "pins.h"
#include "serial.h"
#include "systick.h"
#include "watchdog.h"

int main() {
  pins_init();               // Setup pins to the correct GPIO, UART, and I2C functionality.
  watchdog_init();           // Setup the watchdog counter with a 60 ms period.
  systick_init();            // Setup the 1-ms clock ticks.
  serial_init(serial_ctrl);  // Setup the UART connections with the controller board.
  serial_init(serial_exp);   // Setup the UART connection with the expander, if any.
  initInternalI2C();         // Setup the internal I2C bus (~1.75 ms). Also drives NRST_OUT high.

  // TODO: Set NRST_OUT as an input or open-drain so that the expander can reset itself on failure.
  // Currently doing so breaks expansion resets for programming, so that has to be re-thought first.
  // exp_nrst_release();  // Set NRST_OUT as open-drain so that the expander can reset itself.

  audio_muxes_init();  // Setup the audio mux

  // Main loop, awaiting I2C commands
  uint32_t next_loop_time = millis();
  uint8_t  i2c_addr       = 0;
  while (1) {
    watchdog_reload();

    if ((next_loop_time & ((1 << 12) - 1)) == 0) {
      printf("%lu\n", next_loop_time);
    }

    // Check if a new I2C slave address has been received over UART from the controller board.
    uint8_t new_i2c_addr = getI2C1Address();
    if (new_i2c_addr != i2c_addr) {
      i2c_addr = new_i2c_addr;
      ctrl_i2c_init(i2c_addr);

      // Increment this unit's address by 0x10 to get the address for the next preamp.
      sendAddressToSlave(i2c_addr + 0x10);

      printf("Got address\n");
    }

    // Check for incoming control messages if a slave address has been set
    if (i2c_addr && ctrl_i2c_addr_match()) {
      ctrl_i2c_transact();
    }

    updateInternalI2C(i2c_addr != 0);

    next_loop_time++;  // Loop currently takes ~800 us
    while (millis() < next_loop_time) {}
  }
}
