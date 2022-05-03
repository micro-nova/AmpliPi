/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * Base I2C functionality
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

#include "i2c.h"

#include "stm32f0xx.h"

// addr must be a 7-bit I2C address shifted left by one, ie: 0bXXXXXXX0
void initI2C1(uint8_t addr) {
  // Enable peripheral clock for I2C1
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

  // Enable SDA1, SDA2, SCL1, SCL2 clocks
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);

  // Setup I2C1
  I2C_InitTypeDef I2C_InitStructure1;
  I2C_InitStructure1.I2C_Mode                = I2C_Mode_I2C;
  I2C_InitStructure1.I2C_AnalogFilter        = I2C_AnalogFilter_Enable;
  I2C_InitStructure1.I2C_DigitalFilter       = 0x00;
  I2C_InitStructure1.I2C_OwnAddress1         = addr;
  I2C_InitStructure1.I2C_Ack                 = I2C_Ack_Enable;
  I2C_InitStructure1.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
  I2C_InitStructure1.I2C_Timing = 0;  // Clocks not generated in slave mode
  I2C_Init(I2C1, &I2C_InitStructure1);
  I2C_Cmd(I2C1, ENABLE);
}

/* Init the second I2C bus. I2C2 is internal to a single AmpliPi unit.
 * The STM32 is the master and controls the volume chips, power, fans,
 * and front panel LEDs.
 */
void initI2C2() {
  // Enable peripheral clock for I2C2
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);

  // Enable SDA1, SDA2, SCL1, SCL2 clocks
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);

  // Setup I2C2
  I2C_InitTypeDef I2C_InitStructure2;
  I2C_InitStructure2.I2C_Mode                = I2C_Mode_I2C;
  I2C_InitStructure2.I2C_AnalogFilter        = I2C_AnalogFilter_Enable;
  I2C_InitStructure2.I2C_DigitalFilter       = 0x00;
  I2C_InitStructure2.I2C_OwnAddress1         = 0x00;
  I2C_InitStructure2.I2C_Ack                 = I2C_Ack_Enable;
  I2C_InitStructure2.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;

  /* See the STM32F030 reference manual section 22.4.9 "I2C master mode" or
   * AN4235 for I2C timing calculations.
   * Excel tool, rise/fall 72/4 ns: 100 kHz: 0x00201D2C (0.5074% error)
   *                                400 kHz: 0x0010020B (1.9992% error)
   * Full math done in i2c_calcs.md
   */
  I2C_InitStructure2.I2C_Timing = 0x0010020B;
  I2C_Init(I2C2, &I2C_InitStructure2);
  I2C_Cmd(I2C2, ENABLE);
}

/* Disable the I2C2 peripheral */
void deinitI2C2() {
  // Ensure I2C peripheral clock is enabled in case this function is called
  // before the I2C init function.
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);

  // Disable I2C2 peripheral
  I2C_Cmd(I2C2, DISABLE);
}

uint32_t writeByteI2C2(I2CDev dev, uint8_t val) {
  // TODO: Add timeout conditions for all while loops

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, dev, 1, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag or an error
  uint32_t isr = I2C2->ISR;
  do {
    if (isr & I2C_ISR_NACKF) {
      I2C2->ICR = I2C_ICR_NACKCF;
      return I2C_ISR_NACKF;
    }
    if (isr & I2C_ISR_BERR) {
      I2C2->ICR = I2C_ICR_BERRCF;
      return I2C_ISR_BERR;
    }
    if (isr & I2C_ISR_ARLO) {
      I2C2->ICR = I2C_ICR_ARLOCF;
      return I2C_ISR_ARLO;
    }
    isr = I2C2->ISR;
  } while (!(isr & I2C_ISR_TXIS));

  // Send data
  I2C_SendData(I2C2, val);

  // Wait for stop flag to be sent and then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C2->ICR = I2C_ICR_STOPCF;
  return 0;
}

uint8_t readRegI2C2(I2CReg r) {
  // TODO: Add timeout conditions for all while loops

  // Wait if I2C2 is busy
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY)) {}

  // Setup to write start, addr, subaddr
  I2C_TransferHandling(I2C2, r.dev, 1, I2C_SoftEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit flag
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET) {}

  // Send register address
  I2C_SendData(I2C2, r.reg);

  // Wait for transfer complete flag
  while (I2C_GetFlagStatus(I2C2, I2C_ISR_TC) == RESET) {}

  // This is the actual read transfer setup
  I2C_TransferHandling(I2C2, r.dev, 1, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Read);

  // Wait until we get the rx data then read it out
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  uint8_t data = I2C_ReceiveData(I2C2);

  // Wait for stop condition to get sent then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

  // Return data that was read
  return data;
}

uint32_t writeRegI2C2(I2CReg r, uint8_t data) {
  // TODO: Add timeout conditions for all while loops

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send start, addr, subaddr
  I2C_TransferHandling(I2C2, r.dev, 2, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag or an error
  uint32_t isr = I2C2->ISR;
  do {
    if (isr & I2C_ISR_NACKF) {
      I2C2->ICR = I2C_ICR_NACKCF;
      return I2C_ISR_NACKF;
    }
    if (isr & I2C_ISR_BERR) {
      I2C2->ICR = I2C_ICR_BERRCF;
      return I2C_ISR_BERR;
    }
    if (isr & I2C_ISR_ARLO) {
      I2C2->ICR = I2C_ICR_ARLOCF;
      return I2C_ISR_ARLO;
    }
    isr = I2C2->ISR;
  } while (!(isr & I2C_ISR_TXIS));

  // Send subaddress and data
  I2C_SendData(I2C2, r.reg);
  I2C_SendData(I2C2, data);

  // Wait for stop flag to be sent and then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C2->ICR = I2C_ICR_STOPCF;
  return 0;
}
