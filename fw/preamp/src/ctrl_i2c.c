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

#include "channel.h"
#include "port_defs.h"
#include "power_board.h"
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

static bool uart_passthrough_ = false;

void CtrlI2CInit(uint8_t addr) {
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

bool CtrlI2CAddrMatch() {
  return I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR);
}

void CtrlI2CTransact(Pin exp_nrst, Pin exp_boot0) {
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
  uint8_t  msg;
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
    switch (reg) {
      case REG_POWER_GOOD:
        msg               = readI2C2(pwr_temp_mntr_gpio);
        uint8_t pg_mask   = 0xf3;  // 1111 0011
        uint8_t pg_status = 0;

        // Gets the value of PG_12V, PG_9V, and nothing else
        msg &= ~(pg_mask);
        pg_status = msg >> 2;
        I2C_SendData(I2C1, pg_status);  // Desired value is 0x03 - both good
        break;
      case REG_FAN_STATUS:
        msg                = readI2C2(pwr_temp_mntr_gpio);
        uint8_t fan_mask   = 0x4f;  // 0100 1111
        uint8_t fan_status = 0;

        // Gets the value of FAN_ON, OVR_TMP, FAN_FAIL, and nothing else
        msg &= ~(fan_mask);
        fan_status = msg >> 4;
        I2C_SendData(I2C1, fan_status);
        break;
      case REG_EXTERNAL_GPIO:
        msg               = readI2C2(pwr_temp_mntr_gpio);
        uint8_t io_mask   = 0xbf;  // 1011 1111
        uint8_t io_status = 0;

        msg &= ~(io_mask);  // Gets the value of EXT_GPIO and nothing else
        io_status = msg >> 6;
        I2C_SendData(I2C1, io_status);
        break;
      case REG_LED_OVERRIDE:
        msg = readI2C2(front_panel);  // Current state of the front panel
        I2C_SendData(I2C1, msg);
        break;
      case REG_HV1_VOLTAGE:
        write_ADC(0x61);  // Selects HV1 (AIN0)
        msg = read_ADC();
        I2C_SendData(I2C1, msg);
        break;
      case REG_HV2_VOLTAGE:
        write_ADC(0x63);  // Selects HV2 (AIN1)
        msg = read_ADC();
        I2C_SendData(I2C1, msg);
        break;
      case REG_HV1_TEMP:
        write_ADC(0x65);  // Selects NTC1 (AIN2)
        msg = read_ADC();
        I2C_SendData(I2C1, msg);
        break;
      case REG_HV2_TEMP:
        write_ADC(0x67);  // Selects NTC2 (AIN3)
        msg = read_ADC();
        I2C_SendData(I2C1, msg);
        break;
      case REG_VERSION_MAJOR:
        I2C_SendData(I2C1, VERSION_MAJOR);
        break;
      case REG_VERSION_MINOR:
        I2C_SendData(I2C1, VERSION_MINOR);
        break;
      case REG_GIT_HASH_6_5:
        I2C_SendData(I2C1, GIT_HASH_6_5);
        break;
      case REG_GIT_HASH_4_3:
        I2C_SendData(I2C1, GIT_HASH_4_3);
        break;
      case REG_GIT_HASH_2_1:
        I2C_SendData(I2C1, GIT_HASH_2_1);
        break;
      case REG_GIT_HASH_0_D:
        // LSB is the clean/dirty status according to Git
        I2C_SendData(I2C1, GIT_HASH_0_D);
        break;
      default:
        // Return FF if a non-existent register is selected
        I2C_SendData(I2C1, 0xFF);
    }

    // We only allow reading 1 byte at a time for now, here we are assuming
    // a NACK was sent by the master to signal the end of the read request.
  } else {  // Writing
    // Just received data from the master (Pi),
    // get it from the I2C_RXDR register
    uint8_t data = I2C_ReceiveData(I2C1);

    // Perform appropriate action based on register address and new data
    uint8_t ch;
    uint8_t src;
    switch (reg) {
      case REG_SRC_AD:
        for (src = 0; src < NUM_SRCS; src++) {
          // Analog = low, Digital = high
          InputType type = data % 2 ? IT_DIGITAL : IT_ANALOG;
          configInput(src, type);
          data = data >> 1;
        }
        break;

      case REG_CH321:
        for (ch = 0; ch < 3; ch++) {
          src = data % 4;  // TODO: & 0x3
          // Places one of the four sources on the lower three channels
          connectChannel(src, ch);
          data = data >> 2;
        }
        break;

      case REG_CH654:
        for (ch = 3; ch < 6; ch++) {
          src = data % 4;
          // Places one of the four sources on the upper three channels
          connectChannel(src, ch);
          data = data >> 2;
        }
        break;

      case REG_MUTE:
        for (ch = 0; ch < 6; ch++) {
          if (data % 2) {
            mute(ch);
          } else {
            unmute(ch);
          }
          data = data >> 1;
        }
        break;

      case REG_STANDBY:
        // Writes to this register now directly handle standby and audio power
        if (data == 0) {
          standby();
        } else {
          unstandby();
        }
        break;

      case REG_VOL_CH1:
      case REG_VOL_CH2:
      case REG_VOL_CH3:
      case REG_VOL_CH4:
      case REG_VOL_CH5:
      case REG_VOL_CH6:
        ch = reg - REG_VOL_CH1;
        setChannelVolume(ch, data);
        break;
      case REG_FAN_STATUS:
        // Writing to this register is only used for turning the fan on 100%
        msg               = readI2C2(pwr_temp_mntr_gpio);
        uint8_t full_mask = 0x80;  // 1000 0000

        if (data == 0) {  // Set FAN_ON to ON/OFF
          msg &= ~(full_mask);
        } else if (data == 1) {
          msg |= full_mask;
        }
        writeI2C2(pwr_temp_mntr_olat, msg);
        break;
      case REG_EXTERNAL_GPIO:
        msg               = readI2C2(pwr_temp_mntr_gpio);
        uint8_t gpio_mask = 0x40;  // 0100 0000

        if (data == 0) {  // Set EXT_GPIO to 0 or 1
          msg &= ~(gpio_mask);
        } else if (data == 1) {
          msg |= gpio_mask;
        }
        writeI2C2(pwr_temp_mntr_olat, msg);
        break;
      case REG_LED_OVERRIDE:
        writeI2C2(front_panel, data);  // Full front panel control
        break;
      case REG_EXPANSION:
        // NRST_OUT
        if (data & 0x01) {
          setPin(exp_nrst);
        } else {
          clearPin(exp_nrst);
        }
        // BOOT0_OUT
        if (data & 0x02) {
          setPin(exp_boot0);
        } else {
          clearPin(exp_boot0);
        }

        // Allow UART messages to be forwarded to expansion units
        if (data & 0x04) {
          uart_passthrough_ = true;
          USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
          NVIC_EnableIRQ(USART2_IRQn);
        } else {
          uart_passthrough_ = false;
          USART_ITConfig(USART2, USART_IT_RXNE, DISABLE);
          NVIC_DisableIRQ(USART2_IRQn);
        }
        break;
      case 0x99:
        // Free write to the ADC for debug purposes
        // (writing to setup byte is possible)
        write_ADC(data);
        break;
      default:
        // Do nothing
        break;
    }
    // We only allow writing 1 byte at a time for now, here we assume the
    // master stops transmitting and sends a STOP condition to end the write.
  }
}

bool UartPassthroughEnabled() {
  return uart_passthrough_;
}
