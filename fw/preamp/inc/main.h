/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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

#ifndef __MAIN_H
#define __MAIN_H

#include "stm32f0xx.h"

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

#define CH1_MUTE()   GPIOB->BRR  = pCH1_MUTE
#define CH1_UNMUTE() GPIOB->BSRR = pCH1_MUTE

#define CH2_MUTE()   GPIOC->BRR  = pCH2_MUTE
#define CH2_UNMUTE() GPIOC->BSRR = pCH2_MUTE

#define CH3_MUTE()   GPIOC->BRR  = pCH3_MUTE
#define CH3_UNMUTE() GPIOC->BSRR = pCH3_MUTE

#define CH4_MUTE()   GPIOA->BRR  = pCH4_MUTE
#define CH4_UNMUTE() GPIOA->BSRR = pCH4_MUTE

#define CH5_MUTE()   GPIOA->BRR  = pCH5_MUTE
#define CH5_UNMUTE() GPIOA->BSRR = pCH5_MUTE

#define CH6_MUTE()   GPIOF->BRR  = pCH6_MUTE
#define CH6_UNMUTE() GPIOF->BSRR = pCH6_MUTE

#define CH1_STBY()   GPIOB->BRR  = pCH1_STBY
#define CH1_UNSTBY() GPIOB->BSRR = pCH1_STBY

#define CH2_STBY()   GPIOB->BRR  = pCH2_STBY
#define CH2_UNSTBY() GPIOB->BSRR = pCH2_STBY

#define CH3_STBY()   GPIOB->BRR  = pCH3_STBY
#define CH3_UNSTBY() GPIOB->BSRR = pCH3_STBY

#define CH4_STBY()   GPIOC->BRR  = pCH4_STBY
#define CH4_UNSTBY() GPIOC->BSRR = pCH4_STBY

#define CH5_STBY()   GPIOC->BRR  = pCH5_STBY
#define CH5_UNSTBY() GPIOC->BSRR = pCH5_STBY

#define CH6_STBY()   GPIOA->BRR  = pCH6_STBY
#define CH6_UNSTBY() GPIOA->BSRR = pCH6_STBY

#endif



