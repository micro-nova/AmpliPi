/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
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

#include "i2c.h"
#include "stm32f0xx_i2c.h"

// Power Board I2C ADC device
const I2CDev adc_dev_ = 0xC8;

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

typedef struct {
  uint8_t hv1;
  uint8_t amp_temp1;
  uint8_t hv1_temp;
  uint8_t amp_temp2;
} AdcVals;

typedef union {
  // All temps in UQ7.1 + 20 degC format
  struct {
    uint8_t hv1_f1;   // PSU temp
    uint8_t amp1_f1;  // Amp heatsink 1 temp
    uint8_t amp2_f1;  // Amp heatsink 2 temp
    uint8_t pi_f1;    // Control board Raspberry Pi temp
  };
  uint8_t temps[4];  // All temperatures in 1 array
} Temps;
Temps temps_ = {0};

uint8_t hv1_f2_ = 0;

void initAdc() {
  // Write ADC setup byte
  // REG=1 (setup byte), SEL[2:0] = 000 (VDD), CLK = 0 (internal),
  // BIP/UNI=0 (unipolar), RST=0 (reset config register), X=0 (don't care)
  uint32_t result = writeByteI2C2(adc_dev_, 0x80);
  // TODO: Handle errors here
  (void)result;
}

// TODO: Make standard i2c function
AdcVals readAdc() {
  /****************************************************************************
   *  Configure ADC to scan all 4 channels
   ****************************************************************************/

  // Wait if I2C2 is busy
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY)) {}

  // Setup to send send start, addr, subaddr
  I2C_TransferHandling(I2C2, adc_dev_, 1, I2C_SoftEnd_Mode,
                       I2C_Generate_Start_Write);

  // Wait for transmit interrupted flag
  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET) {}

  // Configuration byte = { config=0b0, scan=0b11, cs=0b00XX, sgl=0b1 }
  // Scan all 4 channels in single-ended mode
  I2C_SendData(I2C2, 0x01 | (3 << 1));

  // Wait for transfer complete flag
  while (I2C_GetFlagStatus(I2C2, I2C_ISR_TC) == RESET) {}

  /****************************************************************************
   *  Read all 4 channels
   ****************************************************************************/
  AdcVals vals = {};
  // Restart and setup a read transfer
  I2C_TransferHandling(I2C2, adc_dev_, 4, I2C_AutoEnd_Mode,
                       I2C_Generate_Start_Read);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.hv1 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.amp_temp1 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.hv1_temp = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET) {}
  vals.amp_temp2 = I2C_ReceiveData(I2C2);

  while (I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET) {}
  I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

  return vals;
}

void updateAdc() {
#define ADC_REF_VOLTS 3.3
#define ADC_PD_KOHMS  4700
#define ADC_PU_KOHMS  100000
  // TODO: low-pass filter after initial reading
  AdcVals adc = readAdc();

  // Convert HV1 to Volts (multiply by 4 to add 2 fractional bits)
  uint32_t num     = 4 * ADC_REF_VOLTS * (ADC_PU_KOHMS + ADC_PD_KOHMS);
  uint32_t den     = UINT8_MAX * ADC_PD_KOHMS;
  uint32_t hv1_raw = num * adc.hv1 / den;
  hv1_f2_          = (uint8_t)(hv1_raw > UINT8_MAX ? UINT8_MAX : hv1_raw);

  // Convert HV1 thermocouple to degC
  temps_.hv1_f1 = THERM_LUT_[adc.hv1_temp];

  // Convert amplifier thermocouples to degC
  temps_.amp1_f1 = THERM_LUT_[adc.amp_temp1];
  temps_.amp2_f1 = THERM_LUT_[adc.amp_temp2];
}

uint8_t getHV1_f2() {
  return hv1_f2_;
}

uint8_t getHV1Temp_f1() {
  return temps_.hv1_f1;
}

int16_t getHV1Temp_f8() {
  // TODO: Filter
  return ((int16_t)temps_.hv1_f1 - (20 << 1)) << 7;
}

uint8_t getAmp1Temp_f1() {
  return temps_.amp1_f1;
}

int16_t getAmp1Temp_f8() {
  // TODO: Filter
  return ((int16_t)temps_.amp1_f1 - (20 << 1)) << 7;
}

uint8_t getAmp2Temp_f1() {
  return temps_.amp2_f1;
}

int16_t getAmp2Temp_f8() {
  // TODO: Filter
  return ((int16_t)temps_.amp2_f1 - (20 << 1)) << 7;
}

uint8_t getPiTemp_f1() {
  return temps_.pi_f1;
}

int16_t getPiTemp_f8() {
  return ((int16_t)temps_.pi_f1 - (20 << 1)) << 7;
}

void setPiTemp_f1(uint8_t temp_f1) {
  temps_.pi_f1 = temp_f1;
}
