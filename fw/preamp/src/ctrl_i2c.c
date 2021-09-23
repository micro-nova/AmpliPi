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

/* The controller interface receives commands and processes them.
 *
 * The STM32's I2C1 interface is connected to the control board,
 * as well as any (other) expansion units' preamp boards.
 */

#include "ctrl_i2c.h"

#include "audio_mux.h"
#include "int_i2c.h"
#include "port_defs.h"
#include "serial.h"
#include "stm32f0xx.h"
#include "version.h"

/* Measured rise and fal times of the controller I2C bus
 *
 * Single AmpliPi unit:
 *  t_r = ~370 ns
 *  t_f = ~5.3 ns
 * Single expansion unit:
 *  t_r = ~450 ns
 *  t_f = ~7.2 ns
 * Two expansion units:
 *  t_r = ~600 ns
 *  t_f = ~9.4 ns
 */

void ctrlI2CInit(uint8_t addr) {
  // addr must be a 7-bit I2C address shifted left by one, ie: 0bXXXXXXX0

  // Enable peripheral clock for I2C1
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);

  // Connect pins to alternate function for I2C1
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource6, GPIO_AF_1);  // I2C1_SCL
  GPIO_PinAFConfig(GPIOB, GPIO_PinSource7, GPIO_AF_1);  // I2C1_SDA

  // Config I2C GPIO pins
  GPIO_InitTypeDef GPIO_InitStructureI2C;
  GPIO_InitStructureI2C.GPIO_Pin   = pSCL | pSDA;
  GPIO_InitStructureI2C.GPIO_Mode  = GPIO_Mode_AF;
  GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
  GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
  GPIO_InitStructureI2C.GPIO_PuPd  = GPIO_PuPd_NOPULL;
  GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

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

bool ctrlI2CAddrMatch() {
  return I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR);
}

uint8_t readReg(const AmpliPiState* state, uint8_t addr) {
  uint8_t out_msg = 0;
  switch (addr) {
    case REG_SRC_AD:
      out_msg = 0;  // TODO
      break;

    case REG_ZONE321:
      out_msg = 0;  // TODO
      break;

    case REG_ZONE654:
      out_msg = 0;  // TODO
      break;

    case REG_MUTE:
      out_msg = 0;  // TODO
      break;

    case REG_STANDBY:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE1:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE2:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE3:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE4:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE5:
      out_msg = 0;  // TODO
      break;

    case REG_VOL_ZONE6:
      out_msg = 0;  // TODO
      break;

    case REG_POWER_STATUS: {
      PwrStatusMsg msg = {
          .pg_12v   = state->pwr_gpio.pg_12v,
          .en_12v   = state->pwr_gpio.en_12v,
          .ovr_tmp  = !state->pwr_gpio.ovr_tmp,  // Active-low
          .fan_on   = state->pwr_gpio.fan_on,
          .reserved = 0,
          // (Developer units only)
          .fan_fail = !state->pwr_gpio.fan_fail,  // Active-low
      };
      out_msg = msg.data;
      break;
    }

    case REG_FAN_CTRL:
      out_msg = state->fan_override ? 1 : 0;
      break;

    case REG_LED_CTRL:
      out_msg = state->led_override ? 1 : 0;
      break;

    case REG_LED_VAL:
      out_msg = state->leds.data;
      break;

    case REG_EXPANSION:
      out_msg = state->expansion.data;
      break;

    case REG_HV1_VOLTAGE:
      out_msg = state->hv1;
      break;

    case REG_HV1_TEMP:
      out_msg = state->hv1_temp;
      break;

    case REG_AMP_TEMP1:
      out_msg = state->amp_temp1;
      break;

    case REG_AMP_TEMP2:
      out_msg = state->amp_temp2;
      break;

    case REG_VERSION_MAJOR:
      out_msg = VERSION_MAJOR;
      break;

    case REG_VERSION_MINOR:
      out_msg = VERSION_MINOR;
      break;

    case REG_GIT_HASH_6_5:
      out_msg = GIT_HASH_6_5;
      break;

    case REG_GIT_HASH_4_3:
      out_msg = GIT_HASH_4_3;
      break;

    case REG_GIT_HASH_2_1:
      out_msg = GIT_HASH_2_1;
      break;

    case REG_GIT_HASH_0_D:
      // LSB is the clean/dirty status according to Git
      out_msg = GIT_HASH_0_D;
      break;

    default:
      // Return 0xFF if a non-existent register is selected
      out_msg = 0xFF;
  }
  return out_msg;
}

void ctrlI2CTransact(AmpliPiState* state) {
  // Setting I2C_ICR.ADDRCF releases the clock stretch if any then acks
  I2C_ClearFlag(I2C1, I2C_FLAG_ADDR);
  // I2C_ISR.DIR is assumed to be 0 (write)

  // Wait for register address to be written by master (Pi)
  while (I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET) {}
  // Reading I2C_RXDR releases the clock stretch if any then acks
  uint8_t reg = I2C_ReceiveData(I2C1);

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
    uint8_t response = readReg(state, reg);
    I2C_SendData(I2C1, response);

    // We only allow reading 1 byte at a time for now, here we are assuming
    // a NACK was sent by the master to signal the end of the read request.
  } else {  // Writing
    // Just received data from the master (Pi),
    // get it from the I2C_RXDR register
    uint8_t data = I2C_ReceiveData(I2C1);

    // Perform appropriate action based on register address and new data
    switch (reg) {
      case REG_SRC_AD:
        for (size_t src = 0; src < NUM_SRCS; src++) {
          // Analog = low, Digital = high
          InputType type = data & 0x1 ? IT_DIGITAL : IT_ANALOG;
          selectSourceAD(src, type);
          data = data >> 1;
        }
        break;

      case REG_ZONE321:
      case REG_ZONE654: {
        size_t start = 3 * (reg - REG_ZONE321);
        for (size_t zone = start; zone < start + 3; zone++) {
          // Connect the zone to the specified source
          size_t src = data & 0x3;
          selectZoneSource(zone, src);
          data = data >> 2;
        }
        break;
      }

      case REG_MUTE:
        for (size_t zone = 0; zone < NUM_ZONES; zone++) {
          mute(zone, data & (0x1 << zone));
        }
        break;

      case REG_STANDBY:
        // Standby is active-low and all channels must be put in standby at once
        standby(data == 0);
        break;

      case REG_VOL_ZONE1:
      case REG_VOL_ZONE2:
      case REG_VOL_ZONE3:
      case REG_VOL_ZONE4:
      case REG_VOL_ZONE5:
      case REG_VOL_ZONE6: {
        size_t zone = reg - REG_VOL_ZONE1;
        setZoneVolume(zone, data);
        break;
      }

      case REG_FAN_CTRL:
        state->fan_override = data & 0x01;
        break;

      case REG_LED_CTRL:
        state->led_override = data & 0x01;
        break;

      case REG_LED_VAL:
        state->leds.data = data;
        break;

      case REG_EXPANSION:
        // Control expansion port's NRST and BOOT0 pins
        state->expansion.nrst  = (data & 0x01) != 0;
        state->expansion.boot0 = (data & 0x02) != 0;

        // TODO: Move these out of i2c handler
        writePin(exp_nrst_, state->expansion.nrst);
        writePin(exp_boot0_, state->expansion.boot0);

        // Allow UART messages to be forwarded to expansion units
        state->expansion.uart_passthrough = (data & 0x04) != 0;
        setUartPassthrough(state->expansion.uart_passthrough);
        break;

      default:
        // Do nothing
        break;
    }
    // We only allow writing 1 byte at a time for now, here we assume the
    // master stops transmitting and sends a STOP condition to end the write.
  }
}
