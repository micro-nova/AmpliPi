/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Port usage and functions for GPIO
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

#include "ports.h"

#include "stm32f0xx.h"

static GPIO_TypeDef* getPort(Pin pp) {
  switch (pp.port) {
    case 'A':
      return GPIOA;
    case 'B':
      return GPIOB;
    case 'C':
      return GPIOC;
    case 'D':
      return GPIOD;
    case 'F':
      return GPIOF;
    default:
      return 0;
  }
}

void writePin(Pin pp, bool set) {
  GPIO_TypeDef* port = getPort(pp);
  // getPort(pp)->BSRR = (1 << pp.pin)
  if (set) {
    // Lower 16 bits of BSRR used for setting, upper for clearing
    port->BSRR = 1 << pp.pin;
  } else {
    // Lower 16 bits of BRR used for clearing
    port->BRR = 1 << pp.pin;
  }
}

bool readPin(Pin pp) {
  GPIO_TypeDef* port = getPort(pp);
  if (port->ODR & (1 << pp.pin)) {
    return true;
  } else {
    return false;
  }
}

uint8_t readI2C2(I2CReg r) {
  uint8_t data;

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
  data = I2C_ReceiveData(I2C2);

  // Wait for stop condition to get sent then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

  // Return data that was read
  return data;
}

uint32_t writeI2C2(I2CReg r, uint8_t data) {
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
