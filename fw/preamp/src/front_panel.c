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

#include "front_panel.h"
#include <stdbool.h>
#include "ports.h"
#include "channel.h"

bool audio_power_on = false;

// Simple counter used for time-sensitive operations
void delay(int a) {
	volatile int i,j;
	for (i=0 ; i < a ; i++){
		j++;
	}
	return;
}

// Enables/disables the 9V power supply along with the green LED
void setAudioPower(bool on){
	uint8_t msg = 0;
	uint8_t ap_mask = 0x01;

	audio_power_on = on;
	msg = readI2C2(pwr_temp_mntr_gpio);

	if(on == 0){ // Set EN 9V to Audio Power ON/OFF
		msg &= ~(ap_mask);
	} else if(on == 1){
		msg |= ap_mask;
	}

	writeI2C2(pwr_temp_mntr_olat, msg);
	updateFrontPanel(!on);
	if(on == 1)
	{
		delay(125000); // need time for volume IC to turn on
	}
}

void enableFrontPanel(){
	// init the i2c->gpio chip on the led board
	// this sets all IO pins to output
	// this ic controls all the LEDs on the front of the box
	writeI2C2(front_panel_dir, ALL_OUTPUT);
}

// Updates the LEDs on the front panel depending on the system state
void updateFrontPanel(bool red_on){
	// bit 0: Green "System On" LED
	// bit 1: Red "System Standby" LED
	// bits 2-7: channels 1 to 6 (in that corresponding order)
	uint8_t bits = 0;
	if(audio_power_on == true){
		red_on = false; // Turn off the RED LED when the GREEN LED is going to be on
	}

	bits |= audio_power_on ? 1 : 0; // Green LED if the system is not in standby
	bits |= red_on ? 2 : 0;         // Red LED for general power. Blinks while waiting for an I2C address from the controller board

	uint8_t ch;
	for(ch = 0; ch < NUM_CHANNELS; ch++){
		bits |= (isOn(ch) ? 1 : 0) << (ch + 2);
	}

	writeI2C2(front_panel, bits);
}
