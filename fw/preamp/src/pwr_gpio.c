/*
 * AmpliPi Home Audio
 * Copyright (C) 2021-2024 MicroNova LLC
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

#include "int_i2c.h"

GpioReg gpio_ = {0};

void set_pwr_gpio(GpioReg val) {
  gpio_ = val;
}

GpioReg get_pwr_gpio() {
  return gpio_;
}

bool pg_5vd() {
  // Assume the 5VD supply is ok for preamp revisions older than 4 since PG_5VD doesn't exist.
  // Power board rev 4 has nothing connected to GP5 but it is pulled-up so will still report OK.
  return get_rev4() ? gpio_.v4.pg_5vd : true;
}

bool pg_5va() {
  // For preamp revisions 4+, the power board (rev 4+) will have PG_5VA on GP2.
  // Unfortunately power board rev 2 had PG_9V on GP2, so we can't just read that pin on old revs.
  // Also, there is no easy way to detect the case where preamp >= rev4 but power <= rev4.
  // So for now any preamps older than rev 4 will just report PG_5VA is good even if they are
  // paired with a rev 4 power board.
  return get_rev4() ? gpio_.v4.pg_5va : true;
}

bool pg_9v() {
  // Only power board revs 2 and 6 have this signal, but it changed from GP2 to GP4.
  // Since power board rev 4 has PG_5VA on GP2, reading GP2 for preamp revs <4 is not possible.
  // Therefore for all preamp revs <4 PG_9V will be assumed good.
  return get_rev4() ? gpio_.v4.pg_9v : true;
}

bool pg_12v() {
  // All boards so far (up to rev 6) have this signal.
  return gpio_.pg_12v;
}

bool fan_fail_max6644() {
  // FANFAIL_N is an active-low, open-drain output from the MAX6644 fan controller.
  // Removed on power board 4+.
  return get_rev4() ? false : !gpio_.ovr_tmp_n;
}

bool over_temp_max6644() {
  // OT_N is an active-low, open-drain output from the MAX6644 fan controller.
  // Removed on power board 4+.
  return get_rev4() ? false : !gpio_.fan_fail_n;
}

bool get_9v_en() {
  return gpio_.en_9v;
}

bool get_12v_en() {
  return gpio_.en_12v;
}

void set_fan_on(bool on) {
  gpio_.fan_on = on;
}
