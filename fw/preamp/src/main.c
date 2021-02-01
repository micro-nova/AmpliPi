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

#include "main.h"
#include <stdbool.h>
#include "front_panel.h"
#include "channel.h"
#include "port_defs.h"
#include "stm32f0xx.h"

// uncomment the line below to use the debugger
// #define DEBUG_OVER_UART2

void init_gpio()
{
	// Enable peripheral clocks for GPIO ports
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOA, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOC, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOD, ENABLE);
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOF, ENABLE);

	// Setup IO pin directions PORT A
	GPIO_InitTypeDef GPIO_InitStructureA;
	GPIO_InitStructureA.GPIO_Pin =
			pCH1_SRC1_EN | pCH1_SRC3_EN | pCH2_SRC1_EN | pCH2_SRC2_EN | pCH2_SRC4_EN |
			pCH6_SRC2_EN | pCH6_SRC3_EN | pCH6_SRC4_EN | pCH4_MUTE | pCH5_MUTE | pCH6_STBY;
	GPIO_InitStructureA.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructureA.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureA.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_InitStructureA.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructureA);

	// Setup IO pin directions PORT B
	GPIO_InitTypeDef GPIO_InitStructureB;
	GPIO_InitStructureB.GPIO_Pin =
			pCH3_SRC2_EN | pCH3_SRC3_EN | pCH3_SRC4_EN | pCH3_SRC2_EN | pCH4_SRC2_EN |
			pCH5_SRC2_EN | pCH5_SRC4_EN | pCH1_MUTE | pCH1_STBY | pCH2_STBY | pCH3_STBY |
			pSRC1_AEN | pSRC2_AEN;
	GPIO_InitStructureB.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructureB.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureB.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_InitStructureB.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructureB);

	// Setup IO pin directions PORT C
	GPIO_InitTypeDef GPIO_InitStructureC;
	GPIO_InitStructureC.GPIO_Pin =
			pCH2_SRC3_EN | pCH3_SRC1_EN | pCH4_SRC1_EN | pCH4_SRC3_EN | pCH4_SRC4_EN |
			pCH5_SRC3_EN | pCH6_SRC1_EN | pCH2_MUTE | pCH3_MUTE | pCH4_STBY | pCH5_STBY |
			pSRC3_AEN | pSRC4_AEN | pSRC2_DEN | pSRC3_DEN | pSRC4_DEN;
	GPIO_InitStructureC.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructureC.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureC.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_InitStructureC.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_Init(GPIOC, &GPIO_InitStructureC);

	// Setup IO pin directions PORT D
	GPIO_InitTypeDef GPIO_InitStructureD;
	GPIO_InitStructureD.GPIO_Pin = pSRC1_DEN;
	GPIO_InitStructureD.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructureD.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureD.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_InitStructureD.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_Init(GPIOD, &GPIO_InitStructureD);

	// Setup IO pin directions PORT F
	GPIO_InitTypeDef GPIO_InitStructureF;
	GPIO_InitStructureF.GPIO_Pin =
			pCH1_SRC2_EN | pCH1_SRC4_EN | pCH5_SRC1_EN | pCH6_MUTE |
			pNRST_OUT | pBOOT0_OUT;
	GPIO_InitStructureF.GPIO_Mode = GPIO_Mode_OUT;
	GPIO_InitStructureF.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureF.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_InitStructureF.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_Init(GPIOF, &GPIO_InitStructureF);
}

void init_i2c(preamp_addr)
{
	// I2C1 is from control board
	// I2C2 is to volume chips

	// enable peripheral clocks for I2C
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C1, ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_I2C2, ENABLE);

	// enable SDA1, SDA2, SCL1, SCL2 clocks
	RCC_AHBPeriphClockCmd(RCC_AHBPeriph_GPIOB, ENABLE);

	// connect pins to alternate function for I2C1
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource6, GPIO_AF_1); //I2C1_SCL
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource7, GPIO_AF_1); //I2C1_SDA

	// connect pins to alternate function for I2C2
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource10, GPIO_AF_1); //I2C2_SCL
	GPIO_PinAFConfig(GPIOB, GPIO_PinSource11, GPIO_AF_1); //I2C2_SDA

	// config I2C GPIO pins
	GPIO_InitTypeDef  GPIO_InitStructureI2C;
	GPIO_InitStructureI2C.GPIO_Pin  = pSCL | pSDA | pSCL_VOL | pSDA_VOL;
	GPIO_InitStructureI2C.GPIO_Mode = GPIO_Mode_AF;
	GPIO_InitStructureI2C.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_InitStructureI2C.GPIO_OType = GPIO_OType_OD;
	GPIO_InitStructureI2C.GPIO_PuPd = GPIO_PuPd_NOPULL;
	GPIO_Init(GPIOB, &GPIO_InitStructureI2C);

	// setup I2C1
	I2C_InitTypeDef  I2C_InitStructure1;
	I2C_InitStructure1.I2C_Mode = I2C_Mode_I2C;
	I2C_InitStructure1.I2C_AnalogFilter = I2C_AnalogFilter_Enable;
	I2C_InitStructure1.I2C_DigitalFilter = 0x00;
	I2C_InitStructure1.I2C_OwnAddress1 = preamp_addr;
	I2C_InitStructure1.I2C_Ack = I2C_Ack_Enable;
	I2C_InitStructure1.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
	//I2C_InitStructure1.I2C_Timing = 0x10805E89; // From 8-Mhz HSI clock with 100ns rise, 10ns fall -> 100 KHz
	I2C_Init(I2C1, &I2C_InitStructure1);
	I2C_Cmd(I2C1, ENABLE);

	// setup I2C2
	I2C_InitTypeDef  I2C_InitStructure2;
	I2C_InitStructure2.I2C_Mode = I2C_Mode_I2C;
	I2C_InitStructure2.I2C_AnalogFilter = I2C_AnalogFilter_Enable;
	I2C_InitStructure2.I2C_DigitalFilter = 0x00;
	I2C_InitStructure2.I2C_OwnAddress1 = 0x00;
	I2C_InitStructure2.I2C_Ack = I2C_Ack_Enable;
	I2C_InitStructure2.I2C_AcknowledgedAddress = I2C_AcknowledgedAddress_7bit;
	I2C_InitStructure2.I2C_Timing = 0x10805E89; // From 48-MHz PCLK with 100ns rise, 10ns fall -> 100 KHz
	I2C_Init(I2C2, &I2C_InitStructure2);
	I2C_Cmd(I2C2, ENABLE);
}

void init_uart()
{
	// UART allows the control board to set preamp I2C addresses and flash preamp software
	// UART2 is used for debugging with an external debugger

	// enable peripheral clocks for UART
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_USART1,ENABLE);
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART2,ENABLE);

	// connect pins to alternate function for UART1
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource9, GPIO_AF_1);  // UART1
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource10, GPIO_AF_1); //

#ifndef DEBUG_OVER_UART2
	// connect pins to alternate function for UART2
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource14, GPIO_AF_1); // UART2
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource15, GPIO_AF_1); //
#endif

	// config UART1 GPIO pins
	GPIO_InitTypeDef GPIO_InitStructureUART;
	GPIO_InitStructureUART.GPIO_Pin = GPIO_Pin_9 | GPIO_Pin_10;
	GPIO_InitStructureUART.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureUART.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_InitStructureUART.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_InitStructureUART.GPIO_Mode = GPIO_Mode_AF;
	GPIO_Init(GPIOA, &GPIO_InitStructureUART);

#ifndef DEBUG_OVER_UART2
	// config UART2 GPIO pins
	GPIO_InitTypeDef GPIO_InitStructureUART2;
	GPIO_InitStructureUART2.GPIO_Pin = GPIO_Pin_14 | GPIO_Pin_15;
	GPIO_InitStructureUART2.GPIO_OType = GPIO_OType_PP;
	GPIO_InitStructureUART2.GPIO_PuPd = GPIO_PuPd_UP;
	GPIO_InitStructureUART2.GPIO_Speed = GPIO_Speed_2MHz;
	GPIO_InitStructureUART2.GPIO_Mode = GPIO_Mode_AF;
	GPIO_Init(GPIOA, &GPIO_InitStructureUART2);
#endif
	// setup USART1
	USART_Cmd(USART1,ENABLE);
	USART_InitTypeDef USART_InitStructure;
	USART_InitStructure.USART_BaudRate = 9600;
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure.USART_StopBits = USART_StopBits_1;
	USART_InitStructure.USART_Parity = USART_Parity_No;
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART1, &USART_InitStructure);
	USART_Cmd(USART1,ENABLE);

#ifndef DEBUG_OVER_UART2
	// setup USART2
	USART_Cmd(USART2,ENABLE);
	USART_InitTypeDef USART_InitStructure2;
	USART_InitStructure2.USART_BaudRate = 9600;
	USART_InitStructure2.USART_WordLength = USART_WordLength_8b;
	USART_InitStructure2.USART_StopBits = USART_StopBits_1;
	USART_InitStructure2.USART_Parity = USART_Parity_No;
	USART_InitStructure2.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
	USART_InitStructure2.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
	USART_Init(USART2, &USART_InitStructure2);
	USART_Cmd(USART2,ENABLE);
#endif
	// USART1 interrupt handler setup
	USART_ITConfig(USART1, USART_IT_RXNE, ENABLE);
	NVIC_EnableIRQ(USART1_IRQn);
}

// Serial buffer for UART handling of I2C addresses
#define SB_MAX_SIZE (64)
typedef struct {
  unsigned char data[SB_MAX_SIZE];  // byte buffer
  unsigned char ind;        		// index (current location)
  unsigned char done;         		// buffer is complete (terminator reached)
  unsigned char ovf;          		// buffer has overflowed!
} SerialBuffer;
volatile SerialBuffer UART_Preamp_RxBuffer;
volatile SerialBuffer UART_Preamp_TxBuffer;

void RxBuf_Add(volatile SerialBuffer *sb, unsigned char data_in)
{
  // Add new byte to buffer (as long as it isn't complete or overflowed). Post-increment index.
  if(!(sb->done) && !(sb->ovf))
    sb->data[sb->ind++] = data_in;
  // Check for completion (i.e. when last two bytes are <CR><LF>)
  if(sb->ind >= 2 && sb->data[(sb->ind)-2] == 0x0D && sb->data[(sb->ind)-1] == 0x0A)
    sb->done = 1;
  // Check for overflow (i.e. when index exceeds buffer)
  if(sb->ind >= SB_MAX_SIZE)
    sb->ovf = 1;
}

void RxBuf_Clear(volatile SerialBuffer *sb)
{
  // clear flags
  sb->ind = 0; sb->done = 0; sb->ovf = 0;
  // clear data
  int i = 0;
  while(i<SB_MAX_SIZE){
	  sb->data[i] = 0x00;
	  i++;
  }
}


int main(void)
{
	uint8_t reg;      // The first half of an I2C message. 0x00 - 0x0A
	uint8_t data;     // The actual value being written to the register
	uint8_t ch, src;  // variables holding zone and source information
	uint8_t i2c_addr; // I2C address received via UART

	init_gpio();
	init_uart();

	Pin f0 = {'F',0}; // NRST_OUT
	Pin f1 = {'F',1}; // BOOT0_OUT
	setPin(f0);		  // Needs to be high so the subsequent preamp board is not held in 'Reset Mode'
	clearPin(f1);	  // Needs to be low so the subsequent preamp board doesn't turn on in 'Boot Mode'

	while(1){
		if(UART_Preamp_RxBuffer.done == 1)
		{
			if(UART_Preamp_RxBuffer.data[0] == 0x41) // "A" - address identifier. Defends against potential noise on the UART line
			{
				i2c_addr = UART_Preamp_RxBuffer.data[1];
				UART_Preamp_TxBuffer = UART_Preamp_RxBuffer; // Need to send the new address to any subsequent boards. The left digit is incremented
				UART_Preamp_TxBuffer.data[UART_Preamp_TxBuffer.ind-3] = UART_Preamp_TxBuffer.data[UART_Preamp_TxBuffer.ind-3] +16; // Ex. A00 -> A10 -> A20 ...
#ifndef DEBUG_OVER_UART2
				USART_PutString(USART2, UART_Preamp_TxBuffer.data); // Send the new address to the next preamp unless UART2 is used by the debugger
#endif
				break;
			}
			delay(1000); // allow time for any extra garbage data to shift in
			RxBuf_Clear(&UART_Preamp_RxBuffer); // Only necessary for multiple runs without cycling power
		} else if(UART_Preamp_RxBuffer.ovf == 1)
		{
			RxBuf_Clear(&UART_Preamp_RxBuffer); // Clear the buffers if they overflow
			RxBuf_Clear(&UART_Preamp_TxBuffer);
		}
	}

	init_i2c(i2c_addr); // Initialize I2C with the new address
	enableFrontPanel(); // setup the I2C->GPIO chip
	initChannels();     // initialize each channel's volume state (does not write to volume control ICs)
	initSources();      // initialize each source's analog/digital state

	// main loop, awaiting I2C commands
	while(1){

		// wait for address match
		while( I2C_GetFlagStatus(I2C1, I2C_FLAG_ADDR) == RESET);
		I2C_ClearFlag(I2C1,I2C_FLAG_ADDR);

		// wait for reg address
		while( I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET);
		reg = I2C_ReceiveData(I2C1);

		// wait for reg data
		while( I2C_GetFlagStatus(I2C1, I2C_FLAG_RXNE) == RESET);
		data = I2C_ReceiveData(I2C1);

		// act on command
		switch(reg){

			case REG_SRC_AD:
				for(src =0; src < NUM_SRCS; src++){
					InputType type = data % 2 ? IT_DIGITAL : IT_ANALOG; // ?
					configInput(src, type);
					data = data >> 1;
				}
				break;

			case REG_CH321:
				for(ch =0; ch < 3; ch++){
					src = data % 4;
					connectChannel(src, ch);
					data = data >> 2;
				}
				break;

			case REG_CH654:
				for(ch =3; ch < 6; ch++){
					src = data % 4;
					connectChannel(src, ch);
					data = data >> 2;
				}
				break;

			case REG_MUTE:
				for(ch = 0; ch < 6; ch++){
					if(data % 2){
						mute(ch);
					}else{
						unmute(ch);
					}
					data = data >> 1;
				}
				break;

			case REG_STANDBY:
				// Writes to this register now handle standby and audio power
				if (data == 0){
					standby();
				}
				else{
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
			default:
				// do nothing
				break;
		}
		updateFrontPanel();
	}
}

/*
 * Function to send a string over USART
 * Inputs: USARTx (1 or 2), string
 * Process: Sends out string character-by-character and then sends
 * carriage return and line feed when done if needed
 */
void USART_PutString(USART_TypeDef* USARTx, uint8_t * str)
{
	int dt = 1000; // delay time. Increase to send out message more slowly.
	while(*str != 0)
	{
		USART_SendData(USARTx, *str);
		str++;
		delay(dt);
	}
	delay(dt);
//	USART_SendData(USARTx, 0x0D); // Use these for terminal comms
//	delay(dt);					  // The message from ctrl bd should
//	USART_SendData(USARTx, 0x0A); // already have \r\n at the end
//	delay(dt);
}

// Handles the interrupt on UART data reception
void USART1_IRQHandler(void)
{
	if(USART_GetITStatus(USART1, USART_IT_RXNE) != RESET)
	{
		unsigned char m = USART_ReceiveData(USART1);
		RxBuf_Add(&UART_Preamp_RxBuffer, m);
	}
}
