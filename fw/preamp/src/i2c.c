/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
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

#include <stdio.h>

#include "stm32f0xx.h"
#include "stm32f0xx_i2c.h"

// Initialize an I2C bus.
// @param bus:  The I2C bus to initialize.
// @param addr: A 7-bit slave I2C address in the 7 MSBs, ie: 0bXXXXXXX0.
//              If 0, the I2C bus will be set as master instead of slave.
void i2c_init(i2c_bus_t bus, uint8_t addr) {
  // Peripheral clocks for both busses should always be enabled.
  RCC->APB1ENR |= RCC_APB1ENR_I2C1EN | RCC_APB1ENR_I2C2EN;

  // TODO: Disable clock stretching by setting I2C_CR1_NOSTRETCH
  I2C_TypeDef* i2c_regs = bus == i2c_ctrl ? I2C1 : I2C2;
  i2c_regs->CR1         = 0;  // Disable I2C1 peripheral (set PE=0).
  i2c_regs->CR2         = 0;  // Defaults OK. ACK bytes received.
  i2c_regs->OAR1        = 0;  // Clear OAR1 register (bits can't be modified while OA1EN=1).
  i2c_regs->OAR2        = 0;  // Clear OAR2 register, don't need a second slave address.
  i2c_regs->TIMEOUTR    = 0;  // Timeouts only used in SMBUS mode.
  if (addr) {
    // Slave mode, set slave address.
    i2c_regs->TIMINGR = 0;                               // Clocks not generated in slave mode.
    i2c_regs->OAR1    = I2C_OAR1_OA1EN | (addr & 0xFE);  // Set slave address to ACK.
  } else {
    // Master mode, set timing. Both I2C controllers are effectively clocked by PCLK = 8 MHz.
    // See the STM32F030 reference manual section 22.4.9 "I2C master mode" or AN4235 for I2C
    // timing calculations. Full math done in i2c_calcs.md
    // Excel tool, rise/fall 72/4 ns: 100 kHz: 0x00201D2C (0.5074% error)
    //                                400 kHz: 0x0010020B (1.9992% error)
    i2c_regs->TIMINGR = 0x0010020B;  // 400 kHz Fast Mode.
  }

  i2c_regs->CR1 = I2C_CR1_PE;  // Enable the I2C1 Peripheral
}

// Disable an I2C bus.
// @param bus: The I2C bus to deinitialize.
void i2c_deinit(i2c_bus_t bus) {
  // Ensure I2C peripheral clocks are enabled in case this function is called before i2c_init().
  RCC->APB1ENR |= RCC_APB1ENR_I2C1EN | RCC_APB1ENR_I2C2EN;

  // Disable I2C2 peripheral
  I2C_TypeDef* i2c_regs = bus == i2c_ctrl ? I2C1 : I2C2;
  i2c_regs->CR1 &= ~I2C_CR1_PE;
}

// Check for an ack from a slave device on the internal I2C bus, indicating its presence.
// @param addr: The 7-bit I2C address, in the uppermost 7-bits (LSB is 0).
bool i2c_detect(uint8_t addr) {
  // Wait for bus free
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Send a start condition, the address (0 bytes of data), and a stop condition
  I2C2->CR2 = I2C_CR2_AUTOEND | I2C_CR2_STOP | I2C_CR2_START | addr;

  // Wait for stop condition
  uint32_t isr;
  bool     error = false;
  do {
    // TODO: Add timeout
    isr = I2C2->ISR;
    if (isr & I2C_ISR_NACKF) {
      I2C2->ICR = I2C_ICR_NACKCF;
      error     = true;
      break;
    }
    if (isr & I2C_ISR_BERR) {
      I2C2->ICR = I2C_ICR_BERRCF;
      error     = true;
      printf("BERR\n");
      break;
    }
    if (isr & I2C_ISR_ARLO) {
      I2C2->ICR = I2C_ICR_ARLOCF;
      error     = true;
      printf("ARLO\n");
      break;
    }
  } while (!(isr & I2C_ISR_STOPF));

  // Clear detected stop condition
  I2C2->ICR = I2C_ICR_STOPCF;
  return !error;
}

uint32_t writeByteI2C2(I2CDev dev, uint8_t val) {
  // TODO: Add timeout conditions for all while loops

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, dev, 1, I2C_AutoEnd_Mode, I2C_Generate_Start_Write);

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
  I2C_TransferHandling(I2C2, r.dev, 1, I2C_SoftEnd_Mode, I2C_Generate_Start_Write);

  // Wait for transmit flag
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET) {}

  // Send register address
  I2C_SendData(I2C2, r.reg);

  // Wait for transfer complete flag
  while (I2C_GetFlagStatus(I2C2, I2C_ISR_TC) == RESET) {}

  // This is the actual read transfer setup
  I2C_TransferHandling(I2C2, r.dev, 1, I2C_AutoEnd_Mode, I2C_Generate_Start_Read);

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
  I2C_TransferHandling(I2C2, r.dev, 2, I2C_AutoEnd_Mode, I2C_Generate_Start_Write);

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

// Write multiple bytes of data to an I2C device.
// @param addr: A 7-bit slave I2C address in the 7 MSBs, ie: 0bXXXXXXX0.
// @param data: An array of bytes to write.
// @param num:  The number of bytes to write.
// @return      0 if no error, or the ISR flag of an error.
uint32_t i2c_int_write_data(const uint8_t addr, const uint8_t* const data, const uint8_t num) {
  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to write slave address, write bit, then 'num' bytes.
  // This assumes CR2 is normally left at the defaults of all 0's.
  I2C2->CR2 = I2C_CR2_AUTOEND | I2C_CR2_START | ((uint32_t)num << 16) | addr;
  // I2C_TransferHandling(I2C2, addr, num, I2C_AutoEnd_Mode, I2C_Generate_Start_Write);

  for (size_t n = 0; n < num; n++) {
    // Wait for the transmit interrupt flag to be set (meaning that the TXDR register is empty and
    // awaiting more data), or an error.
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
      // TODO: Timeout
    } while (!(isr & I2C_ISR_TXIS));

    // Write the next byte of data
    I2C2->TXDR = data[n];
  }

  // Wait for stop condition to occur or an error
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
    // TODO: Timeout
  } while (!(isr & I2C_ISR_STOPF));
  I2C2->ICR = I2C_ICR_STOPCF;  // Clear stop flag
  return 0;
}

// Read multiple bytes of data from an I2C device.
// @param addr: A 7-bit slave I2C address in the 7 MSBs, ie: 0bXXXXXXX0.
// @param data: The buffer to write the read bytes into. Must have space for at least `num` bytes.
// @param num:  The number of bytes to read.
// @return      0 if no error, or the ISR flag of an error.
uint32_t i2c_int_read_data(const uint8_t addr, uint8_t* const data, const uint8_t num) {
  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to write slave address and write bit, then read 'num' bytes.
  // This assumes CR2 is normally left at the defaults of all 0's.
  I2C2->CR2 = I2C_CR2_AUTOEND | I2C_CR2_START | I2C_CR2_RD_WRN | ((uint32_t)num << 16) | addr;

  for (size_t n = 0; n < num; n++) {
    // Wait for a byte to be received, or an error.
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
    } while (!(isr & I2C_ISR_RXNE));

    // Read the next byte of data
    data[n] = (uint8_t)I2C2->RXDR;
  }

  // Wait for stop condition to occur or an error
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
  } while (!(isr & I2C_ISR_STOPF));
  I2C2->ICR = I2C_ICR_STOPCF;  // Clear stop flag
  return 0;
}
