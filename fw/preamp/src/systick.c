/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * ARM systick functions, used as system timer.
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

#include "systick.h"

// High-speed internal clock rate. See HSI_VALUE, which unfortunately wraps the
// literal in a type.
#define HSI_CLOCK_HZ 8000000

typedef struct {
  uint32_t csr;  // Control and status register
  uint32_t rvr;  // Reload value register
  uint32_t cvr;  // Current value register
} SysTickRegs;

#define SYSTICK_BASEADDR 0xE000E010
static volatile SysTickRegs* const systick_regs_ = (volatile SysTickRegs*)SYSTICK_BASEADDR;

#define SCB_SHPR3_ADDR 0xE000ED20  // System Handler Priority Register 3.

// The actual tick counter
volatile uint32_t systick_count_ = 0;

void systick_irq_handler() {
  systick_count_++;
}

// Initialize the ARM systick timer, with interrupts.
void systick_init() {
  // Reload value to count down from. Input clock = HCLK / 8 = HSI / 8 = 1 MHz.
  systick_regs_->rvr = HSI_CLOCK_HZ / SYSTICK_FREQ / 8 - 1;

  // Set the priority for the systick interrupt to the lowest possible, which
  // means the max value. Only 2 out of the max 8 priority bits are implemented,
  // so clear all 8 but set the top 2.
  volatile uint32_t scb_shpr3 = (volatile uint32_t)SCB_SHPR3_ADDR;
  scb_shpr3 |= 0xC0000000;

  // Reset the current systick counter value.
  systick_regs_->cvr = 0x000000;

  // Enable systick counter, interrupt, and set the clock source to HCLK / 8
  systick_regs_->csr = 0x000003;
}

// Return the system clock as a number of milliseconds
inline uint32_t millis() {
  return systick_count_;
}

// Synchronous delay in microseconds. Can only delay between 1 and 999 us.
// Don't rely on this to be super precise, especially for shorter delays.
void delay_us(uint32_t t) {
  // Systick input clock is 1 MHz, so 1 us per count.
  uint32_t start = systick_regs_->cvr;  // 24-bit counter.
  int32_t  end   = start - t;
  if (end < 0) {
    // Count has to wrap.
    while (systick_regs_->cvr <= start) {}
    end += 1000;  // Should be positive now.
  }
  // Wait for down-counter to reach target time.
  while (systick_regs_->cvr > (uint32_t)end) {}
}

// Synchronous delay in milliseconds
void delay_ms(uint32_t t) {
  uint32_t start = millis();
  uint32_t end   = start + t;
  if (start < end) {
    while ((millis() >= start) && (millis() < end)) {}
  } else {
    while ((millis() >= start) || (millis() < end)) {}
  }
}
