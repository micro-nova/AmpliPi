/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
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

/* The controller interface receives commands and processes them.
 *
 * The STM32's I2C1 interface is connected to the control board,
 * as well as any (other) expansion units' preamp boards.
 */

#include "ctrl_i2c.h"

#include "adc.h"
#include "audio.h"
#include "fans.h"
#include "int_i2c.h"
#include "leds.h"
#include "pins.h"
#include "pwr_gpio.h"
#include "serial.h"
#include "stm32f0xx.h"
#include "version.h"

typedef enum {
  // Audio control
  REG_SRC_AD    = 0x00,
  REG_ZONE321   = 0x01,
  REG_ZONE654   = 0x02,
  REG_MUTE      = 0x03,
  REG_AMP_EN    = 0x04,
  REG_VOL_ZONE1 = 0x05,
  REG_VOL_ZONE2 = 0x06,
  REG_VOL_ZONE3 = 0x07,
  REG_VOL_ZONE4 = 0x08,
  REG_VOL_ZONE5 = 0x09,
  REG_VOL_ZONE6 = 0x0A,

  // Power/Fan control
  REG_POWER       = 0x0B,
  REG_FANS        = 0x0C,
  REG_LED_CTRL    = 0x0D,  // OVERRIDE?
  REG_LED_VAL     = 0x0E,  // ZONE[6,5,4,3,2,1], RED, GRN
  REG_EXPANSION   = 0x0F,  // UART_PASSTHROUGH, BOOT0, NRST
  REG_HV1_VOLTAGE = 0x10,  // Volts in UQ6.2 format (0.25 volt resolution)
  REG_AMP_TEMP1   = 0x11,  // degC in UQ7.1 + 20 format (0.5 degC resolution)
  REG_HV1_TEMP    = 0x12,  //   0x00 = disconnected, 0xFF = shorted
  REG_AMP_TEMP2   = 0x13,  //   0x01 = -19.5C, 0x5E = 27C, 0xFE = 107C
  REG_PI_TEMP     = 0x14,  // RPi's temp sent to the micro, in UQ7.1 + 20 format
  REG_FAN_DUTY    = 0x15,  // Fan PWM duty, [0.0,1.0] in UQ1.7 format
  REG_FAN_VOLTS   = 0x16,  // Fan voltage in UQ4.3 format
  REG_HV2_VOLTAGE = 0x17,  // Volts in UQ6.2 format (0.25 volt resolution)
  REG_HV2_TEMP    = 0x18,  // degC in UQ7.1 + 20 format (0.5 degC resolution)

  // Internal I2C bus detected devices
  REG_INT_I2C     = 0x20,  // Each bit flag represents one I2C address
  REG_INT_I2C_MAX = 0x2F,  // Check I2C_ADDR/8 + REG_INT_I2C bit I2C_ADDR & 0x3

  // Version info
  REG_VERSION_MAJOR = 0xFA,
  REG_VERSION_MINOR = 0xFB,
  REG_GIT_HASH_6_5  = 0xFC,
  REG_GIT_HASH_4_3  = 0xFD,
  REG_GIT_HASH_2_1  = 0xFE,
  REG_GIT_HASH_0_D  = 0xFF,
} CmdReg;

/* Measured rise and fall times of the controller I2C bus.
 * Rise time is from 30% to 70%.
 *
 * (ns)| Main | 1 Exp | 2 Exp | 3 Exp | 4 Exp | 5 Exp |
 * ----+------+-------+-------+-------+-------+-------+
 * t_r |  260 |   420 |   590 |   720 |   880 |  1000 |
 * t_f | 16.4 |  16.4 |  16.4 |  17.2 |  19.6 |  20.0 |
 */
void ctrlI2CInit() {
  // addr must be a 7-bit I2C address shifted left by one, ie: 0bXXXXXXX0

  // Enable peripheral clock for I2C1
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

  // Setup I2C1
  I2C_InitTypeDef i2cInit = {
      .I2C_Mode                = I2C_Mode_I2C,
      .I2C_AnalogFilter        = I2C_AnalogFilter_Enable,
      .I2C_DigitalFilter       = 0x00,
      .I2C_OwnAddress1         = getI2C1Address(),
      .I2C_Ack                 = I2C_Ack_Enable,
      .I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit,
      .I2C_Timing              = 0,  // Clocks not generated in slave mode
  };
  I2C_Init(I2C1, &i2cInit);
  I2C_Cmd(I2C1, ENABLE);
}

bool ctrlI2CAddrMatch() {
  return I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR);
}

uint8_t readReg(uint8_t addr) {
  uint8_t out_msg = 0;
  switch (addr) {
    case REG_SRC_AD:
      for (size_t src = 0; src < NUM_SRCS; src++) {
        if (getSourceAD(src)) {
          out_msg |= (1 << src);
        }
      }
      break;

    case REG_ZONE321:
    case REG_ZONE654: {
      size_t offset = 3 * (addr - REG_ZONE321);
      for (size_t zone = 0; zone < 3; zone++) {
        size_t src = getZoneSource(zone + offset) & 0x3;
        out_msg |= (src << (2 * zone));
      }
      break;
    }

    case REG_MUTE:
      for (size_t zone = 0; zone < NUM_ZONES; zone++) {
        if (muted(zone)) {
          out_msg |= (1 << zone);
        }
      }
      break;

    case REG_AMP_EN:
      for (size_t zone = 0; zone < NUM_ZONES; zone++) {
        if (zoneAmpEnabled(zone)) {
          out_msg |= (1 << zone);
        }
      }
      break;

    case REG_VOL_ZONE1:
    case REG_VOL_ZONE2:
    case REG_VOL_ZONE3:
    case REG_VOL_ZONE4:
    case REG_VOL_ZONE5:
    case REG_VOL_ZONE6:
      out_msg = getZoneVolume(addr - REG_VOL_ZONE1);
      break;

    case REG_POWER: {
      PwrReg msg = {
          .pg_9v    = pg9v(),
          .en_9v    = get9vEn(),
          .pg_12v   = pg12v(),
          .en_12v   = get12vEn(),
          .hv2      = isHV2Present(),
          .reserved = 0,
      };
      out_msg = msg.data;
      break;
    }

    case REG_FANS: {
      FanReg msg = {
          .ctrl       = getFanCtrl(),
          .on         = fansOn(),
          .ovr_tmp    = overTempMax6644() || overTemp(),
          .fail       = fanFailMax6644(),
          .smbus_dpot = isDPotSMBus(),
          .reserved   = 0,
      };
      out_msg = msg.data;
      break;
    }

    case REG_LED_CTRL:
      out_msg = getLedOverride() ? 1 : 0;
      break;

    case REG_LED_VAL:
      out_msg = getLeds().data;
      break;

    case REG_EXPANSION: {
      ExpansionReg reg = {
          .nrst             = readPin(exp_nrst_),
          .boot0            = readPin(exp_boot0_),
          .uart_passthrough = getUartPassthrough(),
      };
      out_msg = reg.data;
      break;
    }

    case REG_HV1_VOLTAGE:
      out_msg = getVoltages()->hv1_f2;
      break;

    case REG_HV1_TEMP:
      out_msg = getTemps()->hv1_f1;
      break;

    case REG_AMP_TEMP1:
      out_msg = getTemps()->amp1_f1;
      break;

    case REG_AMP_TEMP2:
      out_msg = getTemps()->amp2_f1;
      break;

    case REG_PI_TEMP:
      out_msg = getTemps()->pi_f1;
      break;

    case REG_FAN_DUTY:
      out_msg = getFanDuty();
      break;

    case REG_FAN_VOLTS:
      out_msg = getFanVolts();
      break;

    case REG_HV2_VOLTAGE:
      out_msg = getVoltages()->hv2_f2;
      break;

    case REG_HV2_TEMP:
      out_msg = getTemps()->hv2_f1;
      break;

    case REG_VERSION_MAJOR:
      out_msg = VERSION_MAJOR_;
      break;

    case REG_VERSION_MINOR:
      out_msg = VERSION_MINOR_;
      break;

    case REG_GIT_HASH_6_5:
    case REG_GIT_HASH_4_3:
    case REG_GIT_HASH_2_1:
    case REG_GIT_HASH_0_D:
      out_msg = GIT_HASH_[addr - REG_GIT_HASH_6_5];
      break;

    default:
      // Return 0xFF if a non-existent register is selected
      out_msg = 0xFF;
  }
  if (addr >= REG_INT_I2C && addr <= REG_INT_I2C_MAX) {
    out_msg = isInternalI2CDevPresent(addr - REG_INT_I2C);
  }
  return out_msg;
}

void writeReg(uint8_t addr, uint8_t data) {
  switch (addr) {
    case REG_SRC_AD:
      for (size_t src = 0; src < NUM_SRCS; src++) {
        // Analog = low, Digital = high
        InputType type = data & 0x1 ? IT_DIGITAL : IT_ANALOG;
        setSourceAD(src, type);
        data = data >> 1;
      }
      break;

    case REG_ZONE321:
    case REG_ZONE654: {
      size_t start = 3 * (addr - REG_ZONE321);
      for (size_t zone = start; zone < start + 3; zone++) {
        // Connect the zone to the specified source
        size_t src = data & 0x3;
        setZoneSource(zone, src);
        data = data >> 2;
      }
      break;
    }

    case REG_MUTE:
      for (size_t zone = 0; zone < NUM_ZONES; zone++) {
        mute(zone, data & (0x1 << zone));
      }
      break;

    case REG_AMP_EN:
      for (size_t zone = 0; zone < NUM_ZONES; zone++) {
        bool enable = data & (0x1 << zone);
        enZoneAmp(zone, enable);
      }
      break;

    case REG_VOL_ZONE1:
    case REG_VOL_ZONE2:
    case REG_VOL_ZONE3:
    case REG_VOL_ZONE4:
    case REG_VOL_ZONE5:
    case REG_VOL_ZONE6: {
      size_t zone = addr - REG_VOL_ZONE1;
      setZoneVolume(zone, data);
      break;
    }

    case REG_FANS:
      setFanCtrl((FanCtrl)data);
      break;

    case REG_LED_CTRL:
      setLedOverride(data & 0x01);
      break;

    case REG_LED_VAL:
      setLeds((Leds)data);
      break;

    case REG_EXPANSION:
      // Control expansion port's NRST and BOOT0 pins
      writePin(exp_nrst_, ((ExpansionReg)data).nrst);
      writePin(exp_boot0_, ((ExpansionReg)data).boot0);

      // Allow UART messages to be forwarded to expansion units
      setUartPassthrough(((ExpansionReg)data).uart_passthrough);
      break;

    case REG_PI_TEMP:
      setPiTemp_f1(data);
      break;

    default:
      // Do nothing
      break;
  }
}

void ctrlI2CTransact() {
  // Setting I2C_ICR.ADDRCF releases the clock stretch if any then acks
  I2C_ClearFlag(I2C1, I2C_FLAG_ADDR);
  // I2C_ISR.DIR is assumed to be 0 (write)

  // Wait for register address to be written by master (Pi)
  while (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET) {}

  // Reading I2C_RXDR releases the clock stretch if any then acks
  uint8_t reg_addr = I2C_ReceiveData(I2C1);

  // Wait for either another slave address match (read),
  // or data in the RX register (write)
  uint32_t i2c_isr_val;
  do {
    i2c_isr_val = I2C1->ISR;
  } while (!(i2c_isr_val & (I2C_FLAG_ADDR | I2C_FLAG_RXNE)));

  if (i2c_isr_val & I2C_ISR_DIR) {  // Reading
    // Just received a repeated start and slave address again,
    // clear address flag to ACK
    I2C_ClearFlag(I2C1, I2C_FLAG_ADDR);

    // Make sure the I2C_TXDR register is empty before filling it with new
    // data to write
    while (I2C_GetFlagStatus(I2C1, I2C_FLAG_TXE) == RESET) {}

    // Send a response based on the register address
    uint8_t response = readReg(reg_addr);
    I2C_SendData(I2C1, response);

    // We only allow reading 1 byte at a time for now, here we are assuming
    // a NACK was sent by the master to signal the end of the read request.
  } else {  // Writing
    // Just received data from the master (Pi),
    // get it from the I2C_RXDR register
    uint8_t data = I2C_ReceiveData(I2C1);
    writeReg(reg_addr, data);

    // We only allow writing 1 byte at a time for now, here we assume the
    // master stops transmitting and sends a STOP condition to end the write.
  }
}
