/*
 * AmpliPi Home Audio
 * Copyright (C) 2023 MicroNova LLC
 *
 * Serial USART interface
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

#pragma once

#include <stdbool.h>
#include <stdint.h>

// Uncomment the line below to use the debugger
// #define DEBUG_OVER_UART2

// Uncomment the line below to enabling debug messages on UART1 to the Pi
// #define DEBUG_PRINT

void setUartPassthrough(bool passthrough);
bool getUartPassthrough();
void initUart1();
void initUart2(uint16_t brr);

// Returns new I2C address if one was received via USART1, otherwise 0
void    sendAddressToSlave(uint8_t i2c_addr);
uint8_t checkForNewAddress();
uint8_t getI2C1Address();

#ifdef DEBUG_PRINT
void debug_putchar(char c);
void debug_print(char* str);
#else
#define debug_putchar(c)
#define debug_print(str)
#endif
