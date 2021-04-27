/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Control for front panel LEDs
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

#include "power_board.h"
#include <stdbool.h>
#include "ports.h"
#include "channel.h"
#include "stm32f0xx.h"

void enablePowerBoard(){
	// init the direction for the power board GPIO
	writeI2C2(pwr_temp_mntr_dir, 0x3C); // Input or Output based on 0011 1100
}

void enable12V(){
	// 12V supply controls the fans, so it should typically be on
	uint8_t msg = 0;
	uint8_t fp_mask = 0x02;

	// Get current GPIO values from power board
	msg = readI2C2(pwr_temp_mntr_gpio);

	// Enable 12V power supply
	msg |= fp_mask;
	writeI2C2(pwr_temp_mntr_olat, msg);
}

void write_ADC(uint8_t data){
	// wait if I2C2 is busy
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY));

	// setup to send send start, addr, subaddr
	I2C_TransferHandling(I2C2, adc_dev.dev, 1, I2C_AutoEnd_Mode, I2C_Generate_Start_Write);

	// wait for transmit interrupted flag
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET);

	I2C_SendData(I2C2, data);

	// wait for stop flag to be sent and then clear it
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET);
	I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);
}

int read_ADC(){

	uint8_t data;

	// Taken from the latter half of readI2C2(). The ADC only has the one reg to read from, so none of the reg specifying is necessary
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY));

	I2C_TransferHandling(I2C2, adc_dev.dev, 1, I2C_AutoEnd_Mode, I2C_Generate_Start_Read);

	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_RXNE) == RESET);
	data = I2C_ReceiveData(I2C2);

	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET);
	I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);

	return data;

}

