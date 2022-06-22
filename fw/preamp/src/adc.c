/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * Temperature related functions including a thermistor temperature conversion
 * look-up table.
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

#include "adc.h"

#include <assert.h>
#include <stddef.h>
#include <string.h>

#include "i2c.h"
#include "pins.h"
#include "stm32f0xx_i2c.h"

#define ADC_REF_VOLTS 3.3
#define ADC_PD_KOHMS  4700
#define ADC_PU_KOHMS  100000
#define ADC_BITS      8

// Convert a fixed-point temperature from 1 to 8 bits of fractional component.
#define TEMP_F1_TO_F8(f1) (((int16_t)f1 - (20 << 1)) << 7)

typedef union {
  struct {
    // The order here must match the order of ADC channels in hardware.
    uint8_t hv1;
    uint8_t amp_temp1;
    uint8_t hv1_temp;
    uint8_t amp_temp2;
    uint8_t hv2;
    uint8_t hv2_temp;
  };
  uint8_t chan[6];
} AdcVals;
static_assert(sizeof(AdcVals) == 6, "AdcVals not packed.");

Temps    temps_    = {};
Voltages voltages_ = {};

typedef struct {
  const I2CDev  dev;     // I2C address
  const uint8_t nchans;  // Number of ADC channels to read
} AdcDev;

// Power Board I2C ADC device with 4 channels (1 HV power supply)
const AdcDev adc4_ = {
    .dev    = 0xC8,  // MAX11601
    .nchans = 4,
};

// Power Board I2C ADC device with 6 channels (2 HV power supplies).
// Either an 8-channel or 12-channel (pin compatible) IC is used.
const AdcDev adc8_ = {
    .dev    = 0xDA,  // MAX11603
    .nchans = 6,     // Last two channels of MAX11603 unused.
};
const AdcDev adc12_ = {
    .dev    = 0xCA,  // MAX11605
    .nchans = 6,     // Last six channels of MAX11605 unused.
};

// Detected ADC. Assume 4-channel to begin.
const AdcDev* adc_ = &adc4_;

// NCP21XV103J03RA - 0805 SMD, R0 = 10k @ 25 degC, B = 3900K
const uint8_t THERM_LUT_[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x02, 0x05, 0x08, 0x0A, 0x0D, 0x0F, 0x11, 0x13, 0x15, 0x17, 0x19, 0x1B,
    0x1C, 0x1E, 0x20, 0x21, 0x23, 0x24, 0x26, 0x27, 0x28, 0x2A, 0x2B, 0x2C,
    0x2E, 0x2F, 0x30, 0x31, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A,
    0x3B, 0x3C, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x43, 0x44, 0x45, 0x46,
    0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x4F, 0x50, 0x51,
    0x52, 0x53, 0x54, 0x55, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x5A, 0x5B,
    0x5C, 0x5D, 0x5E, 0x5E, 0x5F, 0x60, 0x61, 0x62, 0x62, 0x63, 0x64, 0x65,
    0x66, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6E,
    0x6F, 0x70, 0x71, 0x71, 0x72, 0x73, 0x74, 0x75, 0x75, 0x76, 0x77, 0x78,
    0x79, 0x79, 0x7A, 0x7B, 0x7C, 0x7D, 0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x81,
    0x82, 0x83, 0x84, 0x85, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x8A, 0x8B,
    0x8C, 0x8D, 0x8E, 0x8F, 0x90, 0x91, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96,
    0x97, 0x98, 0x99, 0x9A, 0x9A, 0x9B, 0x9C, 0x9D, 0x9E, 0x9F, 0xA0, 0xA1,
    0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAB, 0xAC, 0xAD, 0xAE,
    0xAF, 0xB0, 0xB1, 0xB2, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBA, 0xBB, 0xBC,
    0xBD, 0xBF, 0xC0, 0xC1, 0xC3, 0xC4, 0xC6, 0xC7, 0xC9, 0xCA, 0xCC, 0xCD,
    0xCF, 0xD0, 0xD2, 0xD4, 0xD5, 0xD7, 0xD9, 0xDB, 0xDD, 0xDF, 0xE0, 0xE3,
    0xE5, 0xE7, 0xE9, 0xEB, 0xED, 0xF0, 0xF2, 0xF5, 0xF7, 0xFA, 0xFD, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF,
};

// Exponential Moving Average filter:
// O3dB = 2*pi*f_3dB/Fs
// alpha = cos(O3dB) + sqrt[cos(O3dB)^2 - 4cos(O3dB) + 3] - 1
// y[n] = (1 - alpha)*y[n-1] + alpha*x[n]

// TODO: Make standard i2c function
// TODO: Timeouts
uint32_t readAdcI2C2(const AdcDev* adc, AdcVals* vals) {
  /****************************************************************************
   *  Configure ADC to scan all 4 channels
   ****************************************************************************/

  // Wait if I2C2 is busy
  while (I2C2->ISR & I2C_ISR_BUSY) {}

  // Setup to send start condition, slave address, and write bit.
  I2C_TransferHandling(I2C2, adc->dev, 1, I2C_SoftEnd_Mode,
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

  // Configuration byte = { config=0b0, scan=0b00, cs=0b0XXX, sgl=0b1 }
  // Scan all 4 channels in single-ended mode
  uint8_t config = ((adc->nchans - 1) << 1) | 0x01;
  I2C2->TXDR     = config;

  // Wait for transmit complete flag or an error
  isr = I2C2->ISR;
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
  } while (!(isr & I2C_ISR_TC));

  /****************************************************************************
   *  Read all channels
   ****************************************************************************/
  // Restart and setup a read transfer
  I2C_TransferHandling(I2C2, adc->dev, adc->nchans, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Read);

  for (uint32_t i = 0; i < adc->nchans; i++) {
    // Wait for receive data register not empty or an error
    isr = I2C2->ISR;
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

    // Read data
    vals->chan[i] = I2C2->RXDR;
  }

  // Wait for stop condition to occur or an error
  isr = I2C2->ISR;
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
  I2C2->ICR = I2C_ICR_STOPCF;
  return 0;
}

AdcVals* readAdc() {
  static bool    adc_found = false;
  static AdcVals vals;
  memset(&vals, 0, sizeof(vals));
  if (adc_found) {
    // Read the ADC. If an error occurs assume the ADC is missing.
    adc_found = readAdcI2C2(adc_, &vals) == 0;
  } else {
    // Check for ADC presence by attempting to send the ADC setup byte
    // REG=1 (setup byte), SEL[2:0] = 000 (VDD), CLK = 0 (internal),
    // BIP/UNI=0 (unipolar), RST=0 (reset config register), X=0 (don't care)
    uint32_t error = writeByteI2C2(adc_->dev, 0x80);
    if (error == 0) {
      // Success! Found an ADC.
      adc_found = true;
    } else if (adc_ == &adc4_) {
      // Failed to communicate to the 4-channel ADC, try the 8-channel ADC next
      adc_ = &adc8_;
    } else if (adc_ == &adc8_) {
      // Failed to communicate to the 8-channel ADC, try the 12-channel ADC next
      adc_ = &adc12_;
    } else if (adc_ == &adc12_) {
      // Failed to communicate to the 12-channel ADC, try the 4-channel ADC next
      adc_ = &adc4_;
    }
  }
  return &vals;
}

void updateAdc() {
  // TODO: low-pass filter after initial reading
  AdcVals* vals = readAdc();

  // Convert HV1 and HV2 to Volts (multiply by 4 to add 2 fractional bits)
  uint32_t num     = ADC_REF_VOLTS * (ADC_PU_KOHMS + ADC_PD_KOHMS);
  uint32_t den     = (1 << (ADC_BITS - 2)) * ADC_PD_KOHMS;
  uint32_t hv1_raw = num * vals->hv1 / den;
  voltages_.hv1_f2 = (uint8_t)(hv1_raw > UINT8_MAX ? UINT8_MAX : hv1_raw);
  uint32_t hv2_raw = num * vals->hv2 / den;
  voltages_.hv2_f2 = (uint8_t)(hv2_raw > UINT8_MAX ? UINT8_MAX : hv2_raw);

  // Convert HV1 and HV2 thermocouples to degC
  temps_.hv1_f1 = THERM_LUT_[vals->hv1_temp];
  temps_.hv2_f1 = THERM_LUT_[vals->hv2_temp];

  // Convert amplifier thermocouples to degC
  temps_.amp1_f1 = THERM_LUT_[vals->amp_temp1];
  temps_.amp2_f1 = THERM_LUT_[vals->amp_temp2];
}

Temps* getTemps() {
  return &temps_;
}

Temps16* getTemps16() {
  static Temps16 temps;
  temps.hv1_f8  = TEMP_F1_TO_F8(temps_.hv1_f1);
  temps.hv2_f8  = TEMP_F1_TO_F8(temps_.hv2_f1);
  temps.amp1_f8 = TEMP_F1_TO_F8(temps_.amp1_f1);
  temps.amp2_f8 = TEMP_F1_TO_F8(temps_.amp2_f1);
  temps.pi_f8   = TEMP_F1_TO_F8(temps_.pi_f1);
  return &temps;
}

Voltages* getVoltages() {
  return &voltages_;
}

bool isHV2Present() {
  return adc_ != &adc4_;
}

void setPiTemp_f1(uint8_t temp_f1) {
  temps_.pi_f1 = temp_f1;
}
