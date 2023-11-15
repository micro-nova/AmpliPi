/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * System Window Watchdog (WWDG) initialization and reloading.
 *
 * This program is free software: you can redistribute it and/or modify it under the terms of the
 * GNU General Public License as published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along with this program.
 * If not, see <https://www.gnu.org/licenses/>.
 */

#include "watchdog.h"

#include "rcc.h"

// These registers are 16-bit or 32-bit accessible, but since we are typically writing the entire
// registers here doing 32-bit writes is more efficient since it doesn't require masking.

// Reset value = 0x0000_007F
typedef struct {
  uint32_t counter : 6;  // T[5:0]: Value of the down-counter.
  uint32_t nrst    : 1;  // T[6]: If this bit goes low (from down-counting or otherwise), reset.
  uint32_t enable  : 1;  // When set the WWDG is enabled and can generate a reset.
} WwdgRegCr;
_Static_assert(sizeof(WwdgRegCr) == 4, "Error: WwdgRegCr wrong size.");

// Reset value = 0x0000_007F
typedef struct {
  uint32_t window    : 6;  // W[5:0]: Window value to compare to the down-counter value.
  uint32_t one       : 1;  // W[6]: If 0 a reload/refresh of the down-counter is never allowed.
  uint32_t prescaler : 2;  // WDGTB: Timer base = PCLK/4096/2^prescaler
  uint32_t ewi       : 1;  // Early wakeup interrupt enable.
} WwdgRegCfr;
_Static_assert(sizeof(WwdgRegCfr) == 4, "Error: WwdgRegCfr wrong size.");

typedef struct {
  WwdgRegCr  control;  // Control register
  WwdgRegCfr config;   // Configuration register
  uint32_t   status;   // Status register. 1 if Early Wakeup, 0 otherwise. Write 0 to clear EWIF.
} WwdgRegs;

#define WWDG_BASE_ADDR 0x40002C00
static volatile WwdgRegs *const wwdg_regs_ = (volatile WwdgRegs *)WWDG_BASE_ADDR;

// Setup watchdog timer for 1ms/count, disable the window feature, and perform initial counter load.
void watchdog_init() {
  clock_enable_wwdg();  // Enable WWDG peripheral clock (PCLK=HCLK=HSI=8MHz)

  wwdg_regs_->config = (WwdgRegCfr){
      .window    = 63,  // Set the window as large as possible (63)
      .one       = 1,
      .prescaler = 3,  // WWDG prescaler = 2^WDGTB[1:0] = 8
  };
  watchdog_reload();

  // Check previous reset reason
  // if (RCC->CSR & RCC_CSR_WWDGRSTF) {
  //   RCC->CSR |= RCC_CSR_RMVF;  // Clear reset flags
  // }
}

// Reload counter to avoid a reset for another ~50 ms.
void watchdog_reload() {
  // Timeout in ms:
  //   4096 * 2^config.prescaler * (counter + 1) / F_PCLK_KHZ
  // = 4096 * 8 * (12 + 1) / 8000 = 53.248 ms
  wwdg_regs_->control = (WwdgRegCr){.counter = 24, .nrst = 1, .enable = 1};
}
