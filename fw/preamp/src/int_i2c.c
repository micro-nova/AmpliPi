/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Internal I2C bus control/status
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

#include "int_i2c.h"

#include <stdbool.h>

#include "adc.h"
#include "audio.h"
#include "fans.h"
#include "i2c.h"
#include "leds.h"
#include "pins.h"
#include "pwr_gpio.h"
#include "stm32f0xx.h"
#include "systick.h"

// I2C GPIO registers
const I2CReg pwr_io_dir_  = {0x42, 0x00};
const I2CReg pwr_io_gpio_ = {0x42, 0x09};
const I2CReg pwr_io_olat_ = {0x42, 0x0A};

// LED Board registers
const I2CReg led_dir_  = {0x40, 0x00};
const I2CReg led_gpio_ = {0x40, 0x09};
const I2CReg led_olat_ = {0x40, 0x0A};

// DPOT register (no registers)
const I2CReg dpot_dev_ = {0x5E, 0xFF};

uint32_t writeDpot(uint8_t val) {
  // TODO: add more I2C read/write functions in ports.c and use here and ADC

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, dpot_dev_.dev, 1, I2C_AutoEnd_Mode,
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
  I2C_SendData(I2C2, val);

  // Wait for stop flag to be sent and then clear it
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C2->ICR = I2C_ICR_STOPCF;
  return 0;
}

void initInternalI2C() {
  // Initialize the STM32's I2C2 bus as a master
  initI2C2();

  // Set the direction for the power board GPIO
  // Retry if failed, the bus may be in a bad state if the micro was
  // reset in the middle of a transaction.
  uint32_t tries = 255;
  while (tries--) {
    uint32_t status = writeRegI2C2(pwr_io_dir_, 0x7C);  // 0=output, 1=input
    if (status == I2C_ISR_NACKF) {
      // Received a NACK, will try again
    } else if (status == I2C_ISR_ARLO) {
      // Arbitation lost (SDA low when master tried to set high).
      // Reset I2C since the peripheral auto-sets itself into slave mode.
      // Then, send 9 clocks to finish whichever slave transaction was ongoing.

      // Disable I2C peripheral to reset it if previously enabled
      I2C_Cmd(I2C2, DISABLE);

      // Config I2C GPIO pins
      configI2C2PinsAsGPIO();

      // Generate 9 clocks to clear bus
      writePin(i2c2_scl_, true);
      writePin(i2c2_sda_, false);  // Keep SDA low even after slave releases it
      for (size_t i = 0; i < 9; i++) {
        delayMs(1);
        writePin(i2c2_scl_, false);
        delayMs(1);
        writePin(i2c2_scl_, true);
      }

      // Stop condition
      delayMs(1);
      writePin(i2c2_sda_, true);

      // Re-init I2C2 now that the bus is un-stuck
      initI2C2();
      // Reset pin config to I2C
      configI2CPins();

      /* TODO: Figure out why the below method doesn't work.
      I2C_TransferHandling(I2C2, 0x00, 0, I2C_AutoEnd_Mode,
                           I2C_Generate_Start_Write);

      // Wait until the transaction is done then reset I2C again
      delayMs(1);
      initI2C2();
      uint32_t isr = I2C2->ISR;
      do {
        if (isr & I2C_ISR_NACKF) {
          I2C2->ICR = I2C_ICR_NACKCF;
          break;
        }
        if (isr & I2C_ISR_ARLO) {
          I2C2->ICR = I2C_ICR_ARLOCF;
          break;
        }
        if (isr & I2C_FLAG_STOPF) {
          I2C2->ICR = I2C_ICR_STOPCF;
          break;
        }
        isr = I2C2->ISR;
      } while (1);
      */
    } else {
      tries = 0;
    }
  }

  // Set the LED Board's GPIO expander as all outputs
  writeRegI2C2(led_dir_, 0x00);  // 0=output, 1=input

  // Enable power supplies
  set9vEn(true);
  set12vEn(true);

  updateInternalI2C();
}

void updateInternalI2C() {
  /* I2C transaction times (us):
   *   writeRegI2C2() 92.5
   *   readRegI2C2()  132
   *   updateAdc()    242
   *   writeDpot()    65.8
   */
  uint32_t mod8 = millis() & ((1 << 3) - 1);
  if (mod8 == 0) {
    // Read ADC and update fans every 8 ms
    updateAdc();

    // The two amp heatsinks can be combined by simply taking the max
    int16_t amp1t       = getAmp1Temp_f8();
    int16_t amp2t       = getAmp2Temp_f8();
    int16_t amp_temp_f8 = amp1t > amp2t ? amp1t : amp2t;

    // TODO: only write dpot when necessary
    static bool dpot_present = false;
    updateFans(amp_temp_f8, getHV1Temp_f8(), getPiTemp_f8(), dpot_present);
    dpot_present = writeDpot(getFanDPot()) == 0;
  } else {
    // Read the power board's GPIO inputs
    GpioReg pwr_gpio = {.data = readRegI2C2(pwr_io_gpio_)};
    if (getFanCtrl() != FAN_CTRL_MAX6644) {
      // No fan control IC to determine this
      pwr_gpio.fan_fail_n = !false;
      pwr_gpio.ovr_tmp_n  = !false;
    }
    setPwrGpio(pwr_gpio);

    // Update the LED Board's LED state
    Leds leds_old = getLeds();
    Leds leds     = updateLeds();
    if (leds.data != leds_old.data) {
      writeRegI2C2(led_gpio_, leds.data);
    }
  }

  // Update the Power Board's GPIO outputs, only writing when necessary
  GpioReg gpio_request = {
      .en_9v  = true,  // Always enable 9V
      .en_12v = true,  // Always enable 12V
      .fan_on = getFanOnFromDuty(),
  };
  if (gpio_request.data != (PWR_GPIO_OUT_MASK & getPwrGpio().data)) {
    writeRegI2C2(pwr_io_gpio_, gpio_request.data);
  }

  // TODO: Can the volume controllers be read?
  // TODO: Write volumes
  // setZoneVolume(size_t zone, uint8_t vol)
}
