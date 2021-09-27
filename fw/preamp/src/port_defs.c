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

// Enable pin mapping for each zone's four sources
// Each zone can enable all or none of its sources. This firmware currently
// allows only one to be enabled at a time
const Pin zone_src_[NUM_ZONES][NUM_SRCS] = {
    {{'A', 3}, {'F', 5}, {'A', 4}, {'F', 4}},
    {{'A', 5}, {'A', 7}, {'C', 4}, {'A', 6}},
    {{'C', 5}, {'B', 1}, {'B', 2}, {'B', 0}},
    {{'C', 1}, {'B', 8}, {'C', 11}, {'C', 0}},
    {{'F', 7}, {'B', 3}, {'C', 12}, {'B', 5}},
    {{'C', 10}, {'A', 2}, {'A', 1}, {'A', 0}},
};

const Pin zone_mute_[NUM_ZONES] = {
    {'B', 14}, {'C', 6}, {'C', 8}, {'A', 8}, {'A', 12}, {'F', 6},
};

const Pin zone_standby_[NUM_ZONES] = {
    {'B', 12}, {'B', 13}, {'B', 15}, {'C', 7}, {'C', 9}, {'A', 11},
};

// Analog is first column, digital is second column
const Pin src_ad_[NUM_SRCS][2] = {
    {{'B', 4}, {'D', 2}},
    {{'B', 9}, {'C', 13}},
    {{'C', 15}, {'C', 14}},
    {{'C', 2}, {'C', 3}},
};

const Pin exp_nrst_  = {'F', 0};
const Pin exp_boot0_ = {'F', 1};
