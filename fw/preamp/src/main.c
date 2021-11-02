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

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "audio_mux.h"
#include "ctrl_i2c.h"
#include "int_i2c.h"
#include "port_defs.h"
#include "serial.h"
#include "stm32f0xx.h"
#include "systick.h"

// State of the AmpliPi hardware
AmpliPiState state_;

void initGpio() {
  // Enable peripheral clocks for GPIO ports
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOC, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOD, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);

  // Setup IO pin directions PORT A
  GPIO_InitTypeDef GPIO_InitStructureA;
  GPIO_InitStructureA.GPIO_Pin =
      pZONE1_SRC1_EN | pZONE1_SRC3_EN | pZONE2_SRC1_EN | pZONE2_SRC2_EN |
      pZONE2_SRC4_EN | pZONE6_SRC2_EN | pZONE6_SRC3_EN | pZONE6_SRC4_EN |
      pZONE4_MUTE | pZONE5_MUTE | pZONE6_STBY;
  GPIO_InitStructureA.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureA.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureA.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureA.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOA, &GPIO_InitStructureA);

  // Setup IO pin directions PORT B
  GPIO_InitTypeDef GPIO_InitStructureB;
  GPIO_InitStructureB.GPIO_Pin =
      pZONE3_SRC2_EN | pZONE3_SRC3_EN | pZONE3_SRC4_EN | pZONE3_SRC2_EN |
      pZONE4_SRC2_EN | pZONE5_SRC2_EN | pZONE5_SRC4_EN | pZONE1_MUTE |
      pZONE1_STBY | pZONE2_STBY | pZONE3_STBY | pSRC1_AEN | pSRC2_AEN;
  GPIO_InitStructureB.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureB.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureB.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureB.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOB, &GPIO_InitStructureB);

  // Setup IO pin directions PORT C
  GPIO_InitTypeDef GPIO_InitStructureC;
  GPIO_InitStructureC.GPIO_Pin =
      pZONE2_SRC3_EN | pZONE3_SRC1_EN | pZONE4_SRC1_EN | pZONE4_SRC3_EN |
      pZONE4_SRC4_EN | pZONE5_SRC3_EN | pZONE6_SRC1_EN | pZONE2_MUTE |
      pZONE3_MUTE | pZONE4_STBY | pZONE5_STBY | pSRC3_AEN | pSRC4_AEN |
      pSRC2_DEN | pSRC3_DEN | pSRC4_DEN;
  GPIO_InitStructureC.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureC.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureC.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureC.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOC, &GPIO_InitStructureC);

  // Setup IO pin directions PORT D
  GPIO_InitTypeDef GPIO_InitStructureD;
  GPIO_InitStructureD.GPIO_Pin   = pSRC1_DEN;
  GPIO_InitStructureD.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureD.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureD.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureD.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOD, &GPIO_InitStructureD);

  // Setup IO pin directions PORT F
  GPIO_InitTypeDef GPIO_InitStructureF;
  GPIO_InitStructureF.GPIO_Pin = pZONE1_SRC2_EN | pZONE1_SRC4_EN |
                                 pZONE5_SRC1_EN | pZONE6_MUTE | pNRST_OUT |
                                 pBOOT0_OUT;
  GPIO_InitStructureF.GPIO_Mode  = GPIO_Mode_OUT;
  GPIO_InitStructureF.GPIO_OType = GPIO_OType_PP;
  GPIO_InitStructureF.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_InitStructureF.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_Init(GPIOF, &GPIO_InitStructureF);
}

int main(void) {
  // TODO: Setup watchdog

  // RESET AND PIN SETUP
  writePin(exp_nrst_, false);   // Low-pulse on NRST_OUT so expansion boards are
                                // reset by the controller board
  writePin(exp_boot0_, false);  // Needs to be low so the subsequent preamp
                                // board doesn't start in 'Boot Mode'

  // INIT
  memset(&state_, 0, sizeof(AmpliPiState));
  systickInit();  // Initialize the clock ticks for delay_ms and other timing
                  // functionality
  initGpio();     // UART and I2C require GPIO pins
  // Initialize each channel's volume state
  // (does not write to volume control ICs)
  initZones();
  // Initialize each source's analog/digital state
  initSources();
  initUart1();  // The preamp will receive its I2C network address via UART
  initUart2(9600);
  initInternalI2C(&state_);  // Setup the internal I2C bus

  // RELEASE EXPANSION RESET
  // Needs to be high so the subsequent preamp board is not held in 'Reset Mode'
  writePin(exp_nrst_, true);
  state_.expansion.nrst = true;

  // Main loop, awaiting I2C commands
  uint32_t next_loop_time = millis();
  while (1) {
    // TODO: Clear watchdog

    // Use EXP_BOOT0 as a timer - 4.25 us just for pin set/reset
    // writePin(exp_boot0_, true);

    // Check for incoming UART messages (setting the slave address)
    uint8_t new_addr = checkForNewAddress();
    if (new_addr) {
      state_.i2c_addr = new_addr;
      ctrlI2CInit(state_.i2c_addr);
    }

    // Check for incoming control messages if a slave address has been set
    if (state_.i2c_addr && ctrlI2CAddrMatch()) {
      ctrlI2CTransact(&state_);
    }

    updateInternalI2C(&state_);

    // writePin(exp_boot0_, false);
    next_loop_time += 1;  // Loop currently takes ~800 us
    while (millis() < next_loop_time) {}
  }
}
