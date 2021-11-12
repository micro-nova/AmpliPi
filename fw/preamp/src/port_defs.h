/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Port definitions
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERZONEANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef PORT_DEFS_H_
#define PORT_DEFS_H_

#include "ports.h"

#define NUM_SRCS  4
#define NUM_ZONES 6

typedef enum
{
  // Audio control
  REG_SRC_AD    = 0x00,
  REG_ZONE321   = 0x01,
  REG_ZONE654   = 0x02,
  REG_MUTE      = 0x03,
  REG_STANDBY   = 0x04,
  REG_VOL_ZONE1 = 0x05,
  REG_VOL_ZONE2 = 0x06,
  REG_VOL_ZONE3 = 0x07,
  REG_VOL_ZONE4 = 0x08,
  REG_VOL_ZONE5 = 0x09,
  REG_VOL_ZONE6 = 0x0A,

  // Power/Fan control
  REG_POWER       = 0x0B,
  REG_FANS        = 0x0C,
  REG_LED_CTRL    = 0x0D,  // OVERRIDE?
  REG_LED_VAL     = 0x0E,  // ZONE[6,5,4,3,2,1], RED, GRN
  REG_EXPANSION   = 0x0F,  // UART_PASSTHROUGH, BOOT0, NRST
  REG_HV1_VOLTAGE = 0x10,  // Volts in UQ6.2 format (0.25 volt resolution)
  REG_AMP_TEMP1   = 0x11,  // degC in UQ7.1 + 20 format (0.5 degC resolution)
  REG_HV1_TEMP    = 0x12,  //   0x00 = disconnected, 0xFF = shorted
  REG_AMP_TEMP2   = 0x13,  //   0x01 = -19.5C, 0x5E = 27C, 0xFE = 107C
  REG_PI_TEMP     = 0x14,  // RPi's temp sent to the micro, in UQ7.1 + 20 format
  REG_FAN_DUTY    = 0x15,  // Fan PWM duty, [0.0,1.0] in UQ1.7 format
  REG_FAN_VOLTS   = 0x16,  // Fan voltage in UQ3.4 format

  // Version info
  REG_VERSION_MAJOR = 0xFA,
  REG_VERSION_MINOR = 0xFB,
  REG_GIT_HASH_6_5  = 0xFC,
  REG_GIT_HASH_4_3  = 0xFD,
  REG_GIT_HASH_2_1  = 0xFE,
  REG_GIT_HASH_0_D  = 0xFF,
} CmdReg;

extern const Pin zone_src_[NUM_ZONES][NUM_SRCS];  // Source[1-4]->Zone mux
extern const Pin zone_mute_[NUM_ZONES];
extern const Pin zone_standby_[NUM_ZONES];
extern const Pin src_ad_[NUM_SRCS][2];  // Analog/Digital->Source mux
extern const Pin exp_nrst_;             // Expansion connector NRST_OUT
extern const Pin exp_boot0_;            // Expansion connector BOOT0_OUT
extern const Pin i2c2_scl_;             // Internal I2C bus SCL
extern const Pin i2c2_sda_;             // Internal I2C bus SDA

#define PWR_GPIO_OUT_MASK 0x83

typedef union {
  struct {
    uint8_t en_9v      : 1;  // Only on Power Board 1.X
    uint8_t en_12v     : 1;
    uint8_t pg_9v      : 1;  // Only on Power Board 1.X
    uint8_t pg_12v     : 1;
    uint8_t fan_fail_n : 1;
    uint8_t ovr_tmp_n  : 1;
    uint8_t pg_5v      : 1;  // Planned for Power Board 4.A
    uint8_t fan_on     : 1;
  };
  uint8_t data;
} PwrGpio;

typedef union {
  struct {
    uint8_t pg_9v    : 1;  // R
    uint8_t en_9v    : 1;  // R/W
    uint8_t pg_12v   : 1;  // R
    uint8_t en_12v   : 1;  // R/W
    uint8_t reserved : 4;
  };
  uint8_t data;
} PwrMsg;

typedef union {
  struct {
    uint8_t ctrl : 2;      // R/W - Fan control method currently in use.
                           //       0b11 = force fans on.
    uint8_t on       : 1;  // R   - Fans status
    uint8_t ovr_tmp  : 1;  // R   - Unit over dangerous temperature threshold
    uint8_t fail     : 1;  // R   - Fan fail detection (Power Board 2.A only)
    uint8_t reserved : 3;
  };
  uint8_t data;
} FanMsg;

typedef union {
  struct {
    uint8_t grn   : 1;
    uint8_t red   : 1;
    uint8_t zones : 6;
  };
  uint8_t data;
} LedGpio;

typedef union {
  struct {
    uint8_t nrst             : 1;
    uint8_t boot0            : 1;
    uint8_t uart_passthrough : 1;
    uint8_t reserved         : 5;
  };
  uint8_t data;
} Expander;

#define pZONE1_SRC1_EN GPIO_Pin_3  // PA3
#define pZONE1_SRC2_EN GPIO_Pin_5  // PF5
#define pZONE1_SRC3_EN GPIO_Pin_4  // PA4
#define pZONE1_SRC4_EN GPIO_Pin_4  // PF4

#define pZONE2_SRC1_EN GPIO_Pin_5  // PA5
#define pZONE2_SRC2_EN GPIO_Pin_7  // PA7
#define pZONE2_SRC3_EN GPIO_Pin_4  // PC4
#define pZONE2_SRC4_EN GPIO_Pin_6  // PA6

#define pZONE3_SRC1_EN GPIO_Pin_5  // PC5
#define pZONE3_SRC2_EN GPIO_Pin_1  // PB1
#define pZONE3_SRC3_EN GPIO_Pin_2  // PB2
#define pZONE3_SRC4_EN GPIO_Pin_0  // PB0

#define pZONE4_SRC1_EN GPIO_Pin_1   // PC1
#define pZONE4_SRC2_EN GPIO_Pin_8   // PB8
#define pZONE4_SRC3_EN GPIO_Pin_11  // PC11
#define pZONE4_SRC4_EN GPIO_Pin_0   // PC0

#define pZONE5_SRC1_EN GPIO_Pin_7   // PF7
#define pZONE5_SRC2_EN GPIO_Pin_3   // PB3
#define pZONE5_SRC3_EN GPIO_Pin_12  // PC12
#define pZONE5_SRC4_EN GPIO_Pin_5   // PB5

#define pZONE6_SRC1_EN GPIO_Pin_10  // PC10
#define pZONE6_SRC2_EN GPIO_Pin_2   // PA2
#define pZONE6_SRC3_EN GPIO_Pin_1   // PA1
#define pZONE6_SRC4_EN GPIO_Pin_0   // PA0

#define pZONE1_MUTE GPIO_Pin_14  // PB14
#define pZONE2_MUTE GPIO_Pin_6   // PC6
#define pZONE3_MUTE GPIO_Pin_8   // PC8
#define pZONE4_MUTE GPIO_Pin_8   // PA8
#define pZONE5_MUTE GPIO_Pin_12  // PA12
#define pZONE6_MUTE GPIO_Pin_6   // PF6

#define pZONE1_STBY GPIO_Pin_12  // PB12
#define pZONE2_STBY GPIO_Pin_13  // PB13
#define pZONE3_STBY GPIO_Pin_15  // PB15
#define pZONE4_STBY GPIO_Pin_7   // PC7
#define pZONE5_STBY GPIO_Pin_9   // PC9
#define pZONE6_STBY GPIO_Pin_11  // PA11

#define pSRC1_AEN GPIO_Pin_4   // PB4
#define pSRC2_AEN GPIO_Pin_9   // PB9
#define pSRC3_AEN GPIO_Pin_15  // PC15
#define pSRC4_AEN GPIO_Pin_2   // PC2

#define pSRC1_DEN GPIO_Pin_2   // PD2
#define pSRC2_DEN GPIO_Pin_13  // PC13
#define pSRC3_DEN GPIO_Pin_14  // PC14
#define pSRC4_DEN GPIO_Pin_3   // PC3

#define pANALOG_PWDN GPIO_Pin_13  // PA13
#define pNRST_OUT    GPIO_Pin_0   // PF0
#define pBOOT0_OUT   GPIO_Pin_1   // PF1

#define pSCL     GPIO_Pin_6   // PB6
#define pSDA     GPIO_Pin_7   // PB7
#define pSCL_VOL GPIO_Pin_10  // PB10
#define pSDA_VOL GPIO_Pin_11  // PB11

#endif /* PORT_DEFS_H_ */
