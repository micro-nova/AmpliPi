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
#include <stdint.h>

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

static void delayUs(uint32_t us) {
  for (uint32_t i = 0; i < us; i++) {
    // Create a ~1 us delay based on the CPU clock
    for (size_t n = 0; n < HSI_VALUE / 1000000; n++) {
      __ASM volatile("nop");
    }
  }
}

/* Ensure no transactions are in-progress on the bus
 * Time required: 66 us to 552 us.
 * Max time seen in practice: 150 us.
 */
void quiesceI2C() {
  const uint32_t HALF_PERIOD = 3;  // 4 us period = 166.7 kHz I2C clock
  // Ensure the I2C peripheral is disabled and pins are set as GPIO
  // Pins will be configured to HI-Z (pulled up externally)
  deinitI2C2();

  const uint32_t NUM_CONSECUTIVE_ONES = 9;
  // Require NUM_CONSECUTIVE_ONES on I2C's SDA before proceeding.
  uint32_t tries = 0;
  uint32_t count = 0;
  while (tries < 10 && count < NUM_CONSECUTIVE_ONES) {
    tries++;

    bool success = true;
    for (count = 0; count < NUM_CONSECUTIVE_ONES && success; count++) {
      delayUs(HALF_PERIOD);  // Hold time for clock high

      // If the I2C SDA line is low, start over and try again.
      success = readPin(i2c2_sda_);

      writePin(i2c2_scl_, false);  // Falling edge on the I2C clock line
      delayUs(HALF_PERIOD);        // Hold time for clock low
      writePin(i2c2_scl_, true);   // Set the I2C clock line high
    }
  }

  delayUs(HALF_PERIOD);        // Hold time for clock and data high
  writePin(i2c2_sda_, false);  // Set low the I2C data line. (Start)
  delayUs(HALF_PERIOD * 2);    // Double hold time for clock high and data low
  writePin(i2c2_sda_, true);   // Rising edge on the I2C data line. (Stop)
  delayUs(HALF_PERIOD);        // Hold time for clock and data high.

  // Initialize the STM32's I2C2 bus as a master and control pins by peripheral
  initI2C2();
}

void initInternalI2C() {
  // Make sure any interrupted transactions are cleared out
  quiesceI2C();

  // Set the direction for the power board GPIO
  writeRegI2C2(pwr_io_dir_, 0x7C);  // 0=output, 1=input

  // Enable power supplies
  set9vEn(true);
  set12vEn(true);

  initLeds();
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

    // Update the LED Board's LED state (possible I2C write)
    updateLeds();
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

  updateAudio();
}
