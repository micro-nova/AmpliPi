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
  REG_SRC_AD        = 0,
  REG_CH321         = 1,
  REG_CH654         = 2,
  REG_MUTE          = 3,
  REG_STANDBY       = 4,
  REG_VOL_CH1       = 5,
  REG_VOL_CH2       = 6,
  REG_VOL_CH3       = 7,
  REG_VOL_CH4       = 8,
  REG_VOL_CH5       = 9,
  REG_VOL_CH6       = 10,
  REG_POWER_GOOD    = 11,
  REG_FAN_STATUS    = 12,
  REG_EXTERNAL_GPIO = 13,
  REG_LED_OVERRIDE  = 14,
  REG_EXPANSION     = 15,
  REG_HV1_VOLTAGE   = 16,
  REG_HV2_VOLTAGE   = 17,
  REG_HV1_TEMP      = 18,
  REG_HV2_TEMP      = 19,
  REG_VERSION_MAJOR = 250,
  REG_VERSION_MINOR = 251,
  REG_GIT_HASH_6_5  = 252,
  REG_GIT_HASH_4_3  = 253,
  REG_GIT_HASH_2_1  = 254,
  REG_GIT_HASH_0_D  = 255,
  NUM_REGS          = 25
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
extern const I2CReg pwr_temp_mntr_gpio;
extern const I2CReg pwr_temp_mntr_olat;
extern const I2CReg pwr_temp_mntr_dir;
extern const I2CReg adc_dev;

#define ALL_OUTPUT 0

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
