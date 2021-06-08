/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Watchdog timer functions
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

#include "stm32f0xx.h"

// Setup the Independent Watchdog (IWDG)
void wdg_init() {
  // TODO: Do we have to enable the LSI in the RCC?
  IWDG->KR = 0xCCCC; // Magic key that enables the watchdog timer
  IWDG->KR = 0x5555; // Magic key that enables write access to the other IWDG registers
  IWDG->PR = 0x02;   // Divide 40 kHz LSI clock by 2^(2+PR), max PR=6
  IWDG->RLR = 250;   // Reload this value. 100 ms @ 2.5 kHz
  while (IWDG->SR) {}// TODO: Timeout
  wdg_rst();
}

// Reload the watchdog counter to avoid a system reset
void wdg_rst() {
	// Magic key that reloads the watchdog timer.
	// Also locks other registers if they were unlocked.
	IWDG->KR = 0xAAAA;
}
