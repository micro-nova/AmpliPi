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

static GPIO_TypeDef * getPort(Pin pp){
	switch(pp.port){
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
		while(1);
		return 0;
	}
}

void setPin(Pin pp){
	GPIO_TypeDef * port = getPort(pp);
	port->BSRR = 1 << pp.pin; // lower 16 bits of BSRR used for setting, upper for clearing
}

void clearPin(Pin pp){
	GPIO_TypeDef * port = getPort(pp);
	port->BRR = 1 << pp.pin; // lower 16 bits of BRR used for clearing
}

bool readPin(Pin pp){
	GPIO_TypeDef * port = getPort(pp);
	if(port->ODR & (1 << pp.pin)){
		return true;
	}else{
		return false;
	}
}

void writeI2C2(I2CReg r,  uint8_t data)
{
	// wait if I2C2 is busy
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_BUSY));

	// setup to send send start, addr, subaddr
	I2C_TransferHandling(I2C2, r.dev, 2, I2C_AutoEnd_Mode, I2C_Generate_Start_Write);

	// wait for transmit interrupted flag
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_TXIS) == RESET);

	// send subaddress and data
	I2C_SendData(I2C2, r.reg);
	I2C_SendData(I2C2, data);

	// wait for stop flag to be sent and then clear it
	while(I2C_GetFlagStatus(I2C2, I2C_FLAG_STOPF) == RESET);
	I2C_ClearFlag(I2C2, I2C_FLAG_STOPF);
}
