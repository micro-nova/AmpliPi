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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef PORT_DEFS_H_
#define PORT_DEFS_H_

#include "ports.h"

#define NUM_SRCS     4
#define NUM_CHANNELS 6

typedef enum
{
  // Audio control
  REG_SRC_AD  = 0x00,
  REG_CH321   = 0x01,
  REG_CH654   = 0x02,
  REG_MUTE    = 0x03,
  REG_STANDBY = 0x04,
  REG_VOL_CH1 = 0x05,
  REG_VOL_CH2 = 0x06,
  REG_VOL_CH3 = 0x07,
  REG_VOL_CH4 = 0x08,
  REG_VOL_CH5 = 0x09,
  REG_VOL_CH6 = 0x0A,

  // Power/Fan control
  REG_POWER_STATUS = 0x0B,  // FAN_FAIL (Developer units only), OVR_TMP, PG_12V
  REG_FAN_CTRL     = 0x0C,  // FORCE_ON?
  REG_LED_CTRL     = 0x0D,  // OVERRIDE?
  REG_LED_VAL      = 0x0E,  // ZONE[6,5,4,3,2,1], RED, GRN
  REG_EXPANSION    = 0x0F,  // UART_PASSTHROUGH, BOOT0, NRST
  REG_HV1_VOLTAGE  = 0x10,  // Volts in UQ6.2 format (0.25 volt resolution)
  REG_AMP_TEMP1    = 0x11,  // degC in UQ7.1 + 20 format (0.5 degC resolution)
  REG_HV1_TEMP     = 0x12,  //   0x00 = disconnected, 0xFF = shorted
  REG_AMP_TEMP2    = 0x13,  //   0x01 = -19.5C, 0x5E = 27C, 0xFE = 107C

  // Version info
  REG_VERSION_MAJOR = 0xFA,
  REG_VERSION_MINOR = 0xFB,
  REG_GIT_HASH_6_5  = 0xFC,
  REG_GIT_HASH_4_3  = 0xFD,
  REG_GIT_HASH_2_1  = 0xFE,
  REG_GIT_HASH_0_D  = 0xFF,
} CmdReg;

extern const Pin    ch_src[NUM_CHANNELS][NUM_SRCS];
extern const Pin    ch_mute[NUM_CHANNELS];
extern const Pin    ch_standby[NUM_CHANNELS];
extern const Pin    src_aen[NUM_CHANNELS];  // TODO: Change to NUM_SRCS
extern const Pin    src_den[NUM_CHANNELS];  // TODO: Change to NUM_SRCS
extern const I2CReg ch_left[NUM_CHANNELS];
extern const I2CReg ch_right[NUM_CHANNELS];
extern const I2CReg front_panel;
extern const I2CReg front_panel_dir;
extern const I2CReg adc_dev;

typedef union {
  struct {
    uint8_t fan_on   : 1;
    uint8_t gp6      : 1;
    uint8_t ovr_tmp  : 1;
    uint8_t fan_fail : 1;
    uint8_t pg_12v   : 1;
    uint8_t gp2      : 1;
    uint8_t en_12v   : 1;
    uint8_t gp0      : 1;
  };
  uint8_t data;
} PwrGpio;

typedef union {
  struct {
    uint8_t fan_fail : 1;
    uint8_t reserved : 3;
    uint8_t fan_on   : 1;
    uint8_t ovr_tmp  : 1;
    uint8_t en_12v   : 1;
    uint8_t pg_12v   : 1;
  };
  uint8_t data;
} PwrStatusMsg;

typedef union {
  struct {
    uint8_t zones : 6;
    uint8_t red   : 1;
    uint8_t grn   : 1;
  };
  uint8_t data;
} LedGpio;

typedef union {
  struct {
    uint8_t reserved         : 5;
    uint8_t uart_passthrough : 1;
    uint8_t boot0            : 1;
    uint8_t nrst             : 1;
  };
  uint8_t data;
} Expander;

#define pCH1_SRC1_EN GPIO_Pin_3  // PA3
#define pCH1_SRC2_EN GPIO_Pin_5  // PF5
#define pCH1_SRC3_EN GPIO_Pin_4  // PA4
#define pCH1_SRC4_EN GPIO_Pin_4  // PF4

#define pCH2_SRC1_EN GPIO_Pin_5  // PA5
#define pCH2_SRC2_EN GPIO_Pin_7  // PA7
#define pCH2_SRC3_EN GPIO_Pin_4  // PC4
#define pCH2_SRC4_EN GPIO_Pin_6  // PA6

#define pCH3_SRC1_EN GPIO_Pin_5  // PC5
#define pCH3_SRC2_EN GPIO_Pin_1  // PB1
#define pCH3_SRC3_EN GPIO_Pin_2  // PB2
#define pCH3_SRC4_EN GPIO_Pin_0  // PB0

#define pCH4_SRC1_EN GPIO_Pin_1   // PC1
#define pCH4_SRC2_EN GPIO_Pin_8   // PB8
#define pCH4_SRC3_EN GPIO_Pin_11  // PC11
#define pCH4_SRC4_EN GPIO_Pin_0   // PC0

#define pCH5_SRC1_EN GPIO_Pin_7   // PF7
#define pCH5_SRC2_EN GPIO_Pin_3   // PB3
#define pCH5_SRC3_EN GPIO_Pin_12  // PC12
#define pCH5_SRC4_EN GPIO_Pin_5   // PB5

#define pCH6_SRC1_EN GPIO_Pin_10  // PC10
#define pCH6_SRC2_EN GPIO_Pin_2   // PA2
#define pCH6_SRC3_EN GPIO_Pin_1   // PA1
#define pCH6_SRC4_EN GPIO_Pin_0   // PA0

#define pCH1_MUTE GPIO_Pin_14  // PB14
#define pCH2_MUTE GPIO_Pin_6   // PC6
#define pCH3_MUTE GPIO_Pin_8   // PC8
#define pCH4_MUTE GPIO_Pin_8   // PA8
#define pCH5_MUTE GPIO_Pin_12  // PA12
#define pCH6_MUTE GPIO_Pin_6   // PF6

#define pCH1_STBY GPIO_Pin_12  // PB12
#define pCH2_STBY GPIO_Pin_13  // PB13
#define pCH3_STBY GPIO_Pin_15  // PB15
#define pCH4_STBY GPIO_Pin_7   // PC7
#define pCH5_STBY GPIO_Pin_9   // PC9
#define pCH6_STBY GPIO_Pin_11  // PA11

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
