/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * Port definitions
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

#include "port_defs.h"

// Enable pin mapping for each channel's four sources
// Each channel can enable all or none of its sources. This firmware currently allows only one to be enabled at a time
const Pin ch_src[NUM_CHANNELS][NUM_SRCS] = {
	{{'A', 3},{'F', 5},{'A', 4},{'F', 4}},
	{{'A', 5},{'A', 7},{'C', 4},{'A', 6}},
	{{'C', 5},{'B', 1},{'B', 2},{'B', 0}},
	{{'C', 1},{'B', 8},{'C',11},{'C', 0}},
	{{'F', 7},{'B', 3},{'C',12},{'B', 5}},
	{{'C',10},{'A', 2},{'A', 1},{'A', 0}}
};

const Pin ch_mute[NUM_CHANNELS] = {
	{'B',14},
	{'C', 6},
	{'C', 8},
	{'A', 8},
	{'A',12},
	{'F', 6}
};

const Pin ch_standby[NUM_CHANNELS] = {
	{'B',12},
	{'B',13},
	{'B',15},
	{'C', 7},
	{'C', 9},
	{'A',11}
};

const Pin src_aen[NUM_CHANNELS] = {
	{'B', 4},
	{'B', 9},
	{'C',15},
	{'C', 2}
};

const Pin src_den[NUM_CHANNELS] = {
	{'D', 2},
	{'C',13},
	{'C',14},
	{'C', 3}
};

const I2CReg ch_left[NUM_CHANNELS] = {
		{ 0x88, 0x00 },
		{ 0x88, 0x02 },
		{ 0x88, 0x04 },
		{ 0x8A, 0x00 },
		{ 0x8A, 0x02 },
		{ 0x8A, 0x04 },
};

const I2CReg ch_right[NUM_CHANNELS] = {
		{ 0x88, 0x01 },
		{ 0x88, 0x03 },
		{ 0x88, 0x05 },
		{ 0x8A, 0x01 },
		{ 0x8A, 0x03 },
		{ 0x8A, 0x05 },
};

const I2CReg front_panel = { 0x40, 0x09 };

const I2CReg front_panel_dir = { 0x40, 0x00 };

const I2CReg pwr_temp_mntr_dir = { 0x42, 0x00 };

const I2CReg pwr_temp_mntr_gpio = { 0x42, 0x09 };

const I2CReg pwr_temp_mntr_olat = { 0x42, 0x0A };

const I2CReg adc_dev = { 0xC8, 0xFF };
