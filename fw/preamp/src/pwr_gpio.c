/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
 *
 * Power Board GPIO status and control
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

#include "pwr_gpio.h"

GpioReg gpio_ = {0};

void setPwrGpio(GpioReg val) {
  gpio_ = val;
}

GpioReg getPwrGpio() {
  return gpio_;
}

bool pg9v() {
  return gpio_.pg_9v;
}

bool pg12v() {
  return gpio_.pg_12v;
}

bool overTempMax6644() {
  return !gpio_.fan_fail_n;
}

bool fanFailMax6644() {
  return !gpio_.ovr_tmp_n;
}

bool get9vEn() {
  return gpio_.en_9v;
}

bool get12vEn() {
  return gpio_.en_12v;
}

void setFanOn(bool on) {
  gpio_.fan_on = on;
}
