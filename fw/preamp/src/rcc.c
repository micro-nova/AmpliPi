/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * STM32F030 Reset and Clock Control
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

#include "rcc.h"

// Reset value = 0x0000_XX83
typedef union {
  uint32_t reg;
  struct {
    uint8_t hsi_on   : 1;  // Internal high speed (HSI) clock enable.
    uint8_t hsi_rdy  : 1;  // HSI clock ready flag. Read-only.
    uint8_t          : 1;
    uint8_t hsi_trim : 5;  // HSI clock trimming. 8 MHz nominal = 16. +/-1=>+/-40 kHz.

    uint8_t hsi_cal;  // HSI clock calibration. Read-only.

    uint8_t hse_on  : 1;  // External high speed clock (HSE) enable.
    uint8_t hse_rdy : 1;  // HSE clock ready flag. Read-only.
    uint8_t hse_byp : 1;  // HSE clock bypass (external clock instead of oscillator).
    uint8_t css_on  : 1;  // Clock Security System (CSS) enable.
    uint8_t         : 4;

    uint8_t pll_on  : 1;  // PLL enable.
    uint8_t pll_rdy : 1;  // PLL clock ready (locked). Read-only.
    uint8_t         : 6;
  };
} RccRegCr;
_Static_assert(sizeof(RccRegCr) == 4, "Error: RccRegCr wrong size.");

// Reset value = 0x0000_0000
typedef union {
  uint32_t reg;
  struct {
    uint8_t sw   : 2;  // System clock switch. SYSCLK=[HSI, HSE, PLL, Reserved]
    uint8_t sws  : 2;  // System clock switch status. SYSCLK=[HSI, HSE, PLL, Reserved]
    uint8_t hpre : 4;  // HCLK prescaler: 0x0-0x7 = /1, 0x8-0xF = /2-/512.

    uint8_t ppre    : 3;  // PCLK prescaler: 0x0-0x3 = /1, 0x4-0x7 = /2-/16.
    uint8_t         : 3;
    uint8_t adc_pre : 1;  // ADC prescaler: Obsolete. Proper ADC clock selection is in ADC_CFGR2
    uint8_t         : 1;

    uint8_t pll_src   : 1;  // PLL entry clock source. 0=HSI/2, 1=HSE/PREDIV (from RCC_CFGR2).
    uint8_t pll_xtpre : 1;  // PLL input divider bit 0. Same as CFGR2.prediv[0].
    uint8_t pll_mul   : 4;  // PLL multiplication factor = pll_mul + 2. 0xFF reserved.
    uint8_t           : 2;

    uint8_t mco     : 4;  // MCO pin clock: [None, HSI14, LSI, LSE, SYSCLK, HSI, HSE, PLL, ...RSVD].
    uint8_t mco_pre : 3;  // MCO divided by 2^mco_pre.
    uint8_t         : 1;
  };
} RccRegCfgr;
_Static_assert(sizeof(RccRegCfgr) == 4, "Error: RccRegCfgr wrong size.");

typedef union {
  uint32_t reg;
  struct {
    uint8_t lsi_ready_flag   : 1;  // LSI ready interrupt flag.
    uint8_t lse_ready_flag   : 1;  // LSE ready interrupt flag.
    uint8_t hsi_ready_flag   : 1;  // HSI ready interrupt flag.
    uint8_t hse_ready_flag   : 1;  // HSE ready interrupt flag.
    uint8_t pll_ready_flag   : 1;  // PLL ready interrupt flag.
    uint8_t hsi14_ready_flag : 1;  // HSI14 ready interrupt flag.
    uint8_t                  : 1;
    uint8_t css_flag         : 1;  // CSS interrupt flag. Set on failure of the HSE oscillator.

    uint8_t lsi_ready_int_en   : 1;  // LSI ready interrupt enable.
    uint8_t lse_ready_int_en   : 1;  // LSE ready interrupt enable.
    uint8_t hsi_ready_int_en   : 1;  // HSI ready interrupt enable.
    uint8_t hse_ready_int_en   : 1;  // HSE ready interrupt enable.
    uint8_t pll_ready_int_en   : 1;  // PLL ready interrupt enable.
    uint8_t hsi14_ready_int_en : 1;  // HSI14 ready interrupt enable.
    uint8_t                    : 2;

    uint8_t lsi_ready_clear   : 1;  // LSI ready interrupt clear.
    uint8_t lse_ready_clear   : 1;  // LSE ready interrupt clear.
    uint8_t hsi_ready_clear   : 1;  // HSI ready interrupt clear.
    uint8_t hse_ready_clear   : 1;  // HSE ready interrupt clear.
    uint8_t pll_ready_clear   : 1;  // PLL ready interrupt clear.
    uint8_t hsi14_ready_clear : 1;  // HSI14 ready interrupt clear.
    uint8_t                   : 1;
    uint8_t css_clear         : 1;  // Clock Security System interrupt clear.
  };
} RccRegCir;
_Static_assert(sizeof(RccRegCir) == 4, "Error: RccRegCir wrong size.");

// Reset value = 0x0000_0000
typedef union {
  uint32_t reg;
  struct {
    uint8_t syscfg : 1;  // SYSCFG
    uint8_t        : 7;

    uint8_t        : 1;
    uint8_t adc    : 1;  // ADC
    uint8_t        : 1;
    uint8_t timer1 : 1;  // TIM1
    uint8_t spi1   : 1;  // SPI1
    uint8_t        : 1;
    uint8_t usart1 : 1;  // USART1
    uint8_t        : 1;

    uint8_t timer15   : 1;  // TIM15 (general purpose)
    uint8_t timer16   : 1;  // TIM16 (general purpose)
    uint8_t timer17   : 1;  // TIM17 (general purpose)
    uint8_t           : 3;
    uint8_t debug_mcu : 1;  // Debug MCU
    uint8_t           : 1;
  };
} RccRegApb2;
_Static_assert(sizeof(RccRegApb2) == 4, "Error: RccRegApb2 wrong size.");

// Reset value = 0x0000_0000
typedef union {
  uint32_t reg;
  struct {
    uint8_t        : 1;
    uint8_t timer3 : 1;  // TIM3 (general purpose)
    uint8_t        : 2;
    uint8_t timer6 : 1;  // TIM6 (basic)
    uint8_t        : 3;

    uint8_t timer14 : 1;  // TIM14 (general purpose)
    uint8_t         : 2;
    uint8_t wwdg    : 1;  // System Window Watchdog (WWDG)
    uint8_t         : 2;
    uint8_t spi2    : 1;  // SPI2
    uint8_t         : 1;

    uint8_t        : 1;
    uint8_t usart2 : 1;  // USART2
    uint8_t        : 3;
    uint8_t i2c1   : 1;  // I2C1
    uint8_t i2c2   : 1;  // I2C2
    uint8_t usb    : 1;  // USB

    uint8_t     : 4;
    uint8_t pwr : 1;  // Power interface
    uint8_t     : 3;
  };
} RccRegApb1;
_Static_assert(sizeof(RccRegApb1) == 4, "Error: RccRegApb1 wrong size.");

// Reset value = 0x0000_0014
typedef union {
  uint32_t reg;
  struct {
    uint8_t dma   : 1;  // DMA clock enable.
    uint8_t       : 1;
    uint8_t sram  : 1;  // SRAM interface clock enable.
    uint8_t       : 1;
    uint8_t flitf : 1;  // Flash Interface (FLITF) clock enable.
    uint8_t       : 1;
    uint8_t crc   : 1;  // CRC clock enable.
    uint8_t       : 1;

    uint8_t : 8;

    uint8_t      : 1;
    uint8_t iopa : 1;  // I/O Port A clock enable.
    uint8_t iopb : 1;  // I/O Port B clock enable.
    uint8_t iopc : 1;  // I/O Port C clock enable.
    uint8_t iopd : 1;  // I/O Port D clock enable.
    uint8_t      : 1;
    uint8_t iopf : 1;  // I/O Port E clock enable.
    uint8_t      : 1;
  };
} RccRegAhbEn;
_Static_assert(sizeof(RccRegAhbEn) == 4, "Error: RccRegAhbEn wrong size.");

// Reset value = 0x0000_0018
typedef union {
  uint32_t reg;
  struct {
    uint8_t lse_on     : 1;  // LSE oscillator enable.
    uint8_t lse_rdy    : 1;  // LSE oscillator ready (stable).
    uint8_t lse_bypass : 1;  // LSE oscillator bypass (external clock instead of oscillator).
    uint8_t lse_drive  : 2;  // LSE oscillator drive capability = [low, med-high, med-low, high].
    uint8_t            : 3;

    uint8_t rtc_sel : 2;  // RTC clock source = [None, LSE, LSI, HSE/32]
    uint8_t         : 5;
    uint8_t rtc_en  : 1;  // RTC clock enable.

    uint8_t rtc_rst : 1;  // BDRSET: RTC domain software reset.
  };
} RccRegBdcr;
_Static_assert(sizeof(RccRegBdcr) == 4, "Error: RccRegBdcr wrong size.");

// Reset value = 0xXXX0_0000
typedef union {
  uint32_t reg;
  struct {
    uint8_t lsi_on  : 1;  // LSI clock enable.
    uint8_t lsi_rdy : 1;  // LSI ready flag (clock stable). Read-only.
    uint8_t         : 6;

    uint8_t reserved1;

    uint8_t                  : 7;
    uint8_t v18_pwr_rst_flag : 1;  // Reset flag of the 1.8V domain. Read-only.

    uint8_t rmvf          : 1;  // Remove reset flag. Write 1 to clear the reset flags.
    uint8_t obl_rst_flag  : 1;  // OBL reset flag. Read-only.
    uint8_t pin_rst_flag  : 1;  // PIN reset flag. Read-only.
    uint8_t por_rst_flag  : 1;  // POR/PDR reset flag. Read-only.
    uint8_t sft_rst_flag  : 1;  // Software reset flag. Read-only.
    uint8_t iwdg_rst_flag : 1;  // Independent watchdog (IWDG) reset flag. Read-only.
    uint8_t wwdg_rst_flag : 1;  // System Window Watchdog (WWDG) reset flag. Read-only.
    uint8_t lpwr_rst_flag : 1;  // Low-power reset flag. Read-only.
  };
} RccRegCsr;
_Static_assert(sizeof(RccRegCsr) == 4, "Error: RccRegCsr wrong size.");

// Reset value = 0x0000_0000
typedef union {
  uint32_t reg;
  struct {
    uint16_t : 16;

    uint8_t      : 1;
    uint8_t iopa : 1;  // I/O Port A clock reset.
    uint8_t iopb : 1;  // I/O Port B clock reset.
    uint8_t iopc : 1;  // I/O Port C clock reset.
    uint8_t iopd : 1;  // I/O Port D clock reset.
    uint8_t      : 1;
    uint8_t iopf : 1;  // I/O Port E clock reset.
    uint8_t      : 1;
  };
} RccRegAhbRst;
_Static_assert(sizeof(RccRegAhbRst) == 4, "Error: RccRegAhbRst wrong size.");

// Reset value = 0x0000_0000
typedef struct {
  uint32_t prediv : 4;  // PREDIV: divide input clock to PLL by prediv+1.
  uint32_t        : 28;
} RccRegCfgr2;
_Static_assert(sizeof(RccRegCfgr2) == 4, "Error: RccRegCfgr2 wrong size.");

// Reset value = 0x0000_0000
typedef union {
  uint32_t reg;
  struct {
    uint8_t usart1_sw : 2;  // USART1 clock source = [PCLK, SYSCLK, LSE, HSI]
    uint8_t           : 2;
    uint8_t i2c1_sw   : 1;  // I2C1 clock source = [HSI, SYSCLK]
  };
} RccRegCfgr3;
_Static_assert(sizeof(RccRegCfgr3) == 4, "Error: RccRegCfgr3 wrong size.");

// Reset value = 0xXX00_XX80
typedef union {
  uint32_t reg;
  struct {
    uint8_t hsi14_on       : 1;  // HSI14 clock enable.
    uint8_t hsi14_rdy      : 1;  // HSI14 ready flag (clock stable).
    uint8_t hsi14_disabled : 1;  // When set, ADC interface can't turn on HSI14.
    uint8_t hsi14_trim     : 5;  // HSI14 clock trimming: 14 MHz nominal = 16. +/-1=>+/-50 kHz.

    uint8_t hsi14_cal;  // HSI14 clock calibration. Read-only.
  };
} RccRegCr2;
_Static_assert(sizeof(RccRegCr2) == 4, "Error: RccRegCr2 wrong size.");

typedef struct {
  RccRegCr     clock_control1;   // Clock control register 1.
  RccRegCfgr   clock_config1;    // Clock configuration register 1.
  RccRegCir    clock_interrupt;  // Clock interrupt register.
  RccRegApb2   apb_reset2;       // Advanced Peripheral Bus (APB) peripheral reset register 2.
  RccRegApb1   apb_reset1;       // Advanced Peripheral Bus (APB) peripheral reset register 1.
  RccRegAhbEn  ahb_enable;       // AHB peripheral clock enable register.
  RccRegApb2   apb_enable2;      // APB peripheral clock enable register 2.
  RccRegApb1   apb_enable1;      // APB peripheral clock enable register 1.
  RccRegBdcr   rtc_control;      // Real-time Clock (RTC) and Backup Domain (BD) control register.
  RccRegCsr    control_status;   // Clock control & status register.
  RccRegAhbRst ahb_reset;        // Advanced High-performance Bus (AHB) peripheral reset register.
  RccRegCfgr2  clock_config2;    // Clock configuration register 2.
  RccRegCfgr3  clock_config3;    // Clock configuration register 3.
  RccRegCr2    clock_control2;   // Clock control register 2.
} RccRegs;

#define RCC_BASE_ADDR 0x40021000
static volatile RccRegs *const rcc_regs_ = (volatile RccRegs *)RCC_BASE_ADDR;

void clock_enable_wwdg() {
  rcc_regs_->apb_enable1.wwdg = 1;
}
