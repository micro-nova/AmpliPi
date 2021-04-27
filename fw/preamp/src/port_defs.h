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

#define NUM_SRCS (4)
#define NUM_CHANNELS (6)

typedef enum {
	REG_SRC_AD = 0,
	REG_CH321 = 1,
	REG_CH654 = 2,
	REG_MUTE =3,
	REG_STANDBY = 4,
	REG_VOL_CH1 = 5,
	REG_VOL_CH2 = 6,
	REG_VOL_CH3 = 7,
	REG_VOL_CH4 = 8,
	REG_VOL_CH5 = 9,
	REG_VOL_CH6 = 10,
	REG_POWER_GOOD = 11,
	REG_FAN_STATUS = 12,
	REG_EXTERNAL_GPIO = 13,
	REG_LED_OVERRIDE = 14,
	REG_HV1_VOLTAGE = 16,
	REG_HV2_VOLTAGE = 17,
	REG_HV1_TEMP = 18,
	REG_HV2_TEMP = 19,
	REG_VERSION_MAJOR = 250,
	REG_VERSION_MINOR = 251,
	REG_GIT_HASH_27_20 = 252,
	REG_GIT_HASH_19_12 = 253,
	REG_GIT_HASH_11_04 = 254,
	REG_GIT_HASH_STATUS = 255,
	NUM_REGS = 25
} CmdReg;

extern const Pin ch_src[NUM_CHANNELS][NUM_SRCS];
extern const Pin ch_mute[NUM_CHANNELS];
extern const Pin ch_standby[NUM_CHANNELS];
extern const Pin src_aen[NUM_CHANNELS];
extern const Pin src_den[NUM_CHANNELS];
extern const I2CReg ch_left[NUM_CHANNELS];
extern const I2CReg ch_right[NUM_CHANNELS];
extern const I2CReg front_panel;
extern const I2CReg front_panel_dir;
extern const I2CReg pwr_temp_mntr_gpio;
extern const I2CReg pwr_temp_mntr_olat;
extern const I2CReg pwr_temp_mntr_dir;
extern const I2CReg adc_dev;

#define ALL_OUTPUT (0)

#define pCH1_SRC1_EN               GPIO_Pin_3  	// A
#define pCH1_SRC2_EN               GPIO_Pin_5	// F
#define pCH1_SRC3_EN               GPIO_Pin_4	// A
#define pCH1_SRC4_EN               GPIO_Pin_4	// F

#define pCH2_SRC1_EN               GPIO_Pin_5   // A
#define pCH2_SRC2_EN               GPIO_Pin_7	// A
#define pCH2_SRC3_EN               GPIO_Pin_4	// C
#define pCH2_SRC4_EN               GPIO_Pin_6	// A

#define pCH3_SRC1_EN               GPIO_Pin_5	// C
#define pCH3_SRC2_EN               GPIO_Pin_1	// B
#define pCH3_SRC3_EN               GPIO_Pin_2	// B
#define pCH3_SRC4_EN               GPIO_Pin_0	// B

#define pCH4_SRC1_EN               GPIO_Pin_1	// C
#define pCH4_SRC2_EN               GPIO_Pin_8	// B
#define pCH4_SRC3_EN               GPIO_Pin_11	// C
#define pCH4_SRC4_EN               GPIO_Pin_0	// C

#define pCH5_SRC1_EN               GPIO_Pin_7	// F
#define pCH5_SRC2_EN               GPIO_Pin_3	// B
#define pCH5_SRC3_EN               GPIO_Pin_12	// C
#define pCH5_SRC4_EN               GPIO_Pin_5	// B

#define pCH6_SRC1_EN               GPIO_Pin_10	// C
#define pCH6_SRC2_EN               GPIO_Pin_2	// A
#define pCH6_SRC3_EN               GPIO_Pin_1	// A
#define pCH6_SRC4_EN               GPIO_Pin_0	// A

#define pCH1_MUTE                  GPIO_Pin_14	// B
#define pCH2_MUTE                  GPIO_Pin_6	// C
#define pCH3_MUTE                  GPIO_Pin_8	// C
#define pCH4_MUTE                  GPIO_Pin_8	// A
#define pCH5_MUTE                  GPIO_Pin_12	// A
#define pCH6_MUTE                  GPIO_Pin_6	// F

#define pCH1_STBY                  GPIO_Pin_12	// B
#define pCH2_STBY                  GPIO_Pin_13	// B
#define pCH3_STBY                  GPIO_Pin_15	// B
#define pCH4_STBY                  GPIO_Pin_7	// C
#define pCH5_STBY                  GPIO_Pin_9	// C
#define pCH6_STBY                  GPIO_Pin_11	// A

#define pSRC1_AEN                  GPIO_Pin_4	// B
#define pSRC2_AEN                  GPIO_Pin_9	// B
#define pSRC3_AEN                  GPIO_Pin_15	// C
#define pSRC4_AEN                  GPIO_Pin_2	// C

#define pSRC1_DEN                  GPIO_Pin_2	// D
#define pSRC2_DEN                  GPIO_Pin_13	// C
#define pSRC3_DEN                  GPIO_Pin_14	// C
#define pSRC4_DEN                  GPIO_Pin_3	// C

#define pANALOG_PWDN               GPIO_Pin_13	// A
#define pNRST_OUT                  GPIO_Pin_0	// F
#define pBOOT0_OUT                 GPIO_Pin_1	// F

#define pSCL                       GPIO_Pin_6  // B
#define pSDA                       GPIO_Pin_7  // B
#define pSCL_VOL                   GPIO_Pin_10 // B
#define pSDA_VOL                   GPIO_Pin_11 // B

#endif /* PORT_DEFS_H_ */
