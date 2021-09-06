#!/usr/bin/env python3
#
# AmpliPi Home Audio
# Copyright (C) 2021 MicroNova LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""AmpliPi hardware interface
"""

import argparse
from enum import Enum
import RPi.GPIO as GPIO
from serial import Serial
from smbus2 import SMBus
import subprocess
import time

class Preamp:
  """ Low level discovery and communication for the AmpliPi Preamp's firmware
  """

  # Preamp register addresses
  class Reg(Enum):
    SRC_AD          = 0x00
    CH123_SRC       = 0x01
    CH456_SRC       = 0x02
    MUTE            = 0x03
    STANDBY         = 0x04
    CH1_ATTEN       = 0x05
    CH2_ATTEN       = 0x06
    CH3_ATTEN       = 0x07
    CH4_ATTEN       = 0x08
    CH5_ATTEN       = 0x09
    CH6_ATTEN       = 0x0A
    POWER_GOOD      = 0x0B
    FAN_STATUS      = 0x0C
    EXTERNAL_GPIO   = 0x0D
    LED_OVERRIDE    = 0x0E
    HV1_VOLTAGE     = 0x10
    HV2_VOLTAGE     = 0x11
    HV1_TEMP        = 0x12
    HV2_TEMP        = 0x13
    VERSION_MAJOR   = 0xFA
    VERSION_MINOR   = 0xFB
    GIT_HASH_27_20  = 0xFC
    GIT_HASH_19_12  = 0xFD
    GIT_HASH_11_04  = 0xFE
    GIT_HASH_STATUS = 0xFF

  def __init__(self, unit: int, bus: SMBus):
    """ Preamp constructor

      Args:
        unit: integer unit number, master = 0, expansion #1 = 1, etc.
    """
    self.addr = (unit + 1) * 0x8
    self.bus = bus

  def available(self) -> bool:
    """ Check if a unit is available on the I2C bus by attempting to write to
        its Version register. The write will be discarded as this is a
        read-only register, however no error will be thrown so long as an
        ACK is received on the I2C bus.
    """
    try:
      self.bus.write_byte_data(self.addr, self.Reg.VERSION_MAJOR.value, 0)
    except OSError as e:
      #print(e)
      return False
    return True


  def read_version(self, preamp: int = 1):
    """ Read the firmware version of the preamp

      Returns:
        major:    The major revision number
        minor:    The minor revision number
        git_hash: The git hash of the build (7-digit abbreviation)
        dirty:    False if the git hash is valid, True otherwise
    """
    assert 1 <= preamp <= 15
    if self.bus is not None:
      major = self.bus.read_byte_data(preamp*8, self.Reg.VERSION_MAJOR.value)
      minor = self.bus.read_byte_data(preamp*8, self.Reg.VERSION_MINOR.value)
      git_hash = self.bus.read_byte_data(preamp*8, self.Reg.GIT_HASH_27_20.value) << 20
      git_hash |= (self.bus.read_byte_data(preamp*8, self.Reg.GIT_HASH_19_12.value) << 12)
      git_hash |= (self.bus.read_byte_data(preamp*8, self.Reg.GIT_HASH_11_04.value) << 4)
      git_hash4_stat = self.bus.read_byte_data(preamp*8, self.Reg.GIT_HASH_STATUS.value)
      git_hash |= (git_hash4_stat >> 4)
      dirty = (git_hash4_stat & 0x01) != 0
      return major, minor, git_hash, dirty
    return None


class Preamps:
  """ AmpliPi Preamp Board manager """

  """ The maximum number of AmpliPi units, including the master """
  MAX_UNITS = 6

  class Pin(Enum):
    """ Pi GPIO pins to control the master unit's preamp """
    NRST  = 4
    BOOT0 = 5

  def __init__(self, reset: bool = False, update: bool = False):
    self.bus = SMBus(1)
    self.preamps = []
    if reset:
      self.reset(unit = 0, bootloader = False)
    if update:
      self.flash('') # TODO: add filepath to arg

    print(f'Preamps found: {len(self.preamps)}')

  def reset(self, unit: int = 0, bootloader: bool = False):
    """ Resets the master unit's preamp board.
        Any expansion preamps will be reset one-by-one by the previous preamp.
        After resetting, an I2C address is assigned.

      Args:
        unit:       Reset from the given unit number onward. 0=master
        bootloader: If True, set BOOT0 pin high to enter bootloader mode after reset
    """

    # TODO: If unit=1,2,3,4, or 5, only reset those units and onward

    # Reset, then send I2C address over UART
    self._reset_master(bootloader)
    with Serial('/dev/serial0', baudrate=115200) as ser:
      ser.write((0x41, 0x10, 0x0D, 0x0A))
    if not Preamp(0, self.bus).available():
      print('Falling back to 9600 baud, is firmware version >=1.2?')
      # The failed attempt at 115200 baud seems to put v1.1 firmware in a bad
      # state, so reset and try again at 9600 baud.
      self._reset_master(bootloader)
      with Serial('/dev/serial0', baudrate=9600) as ser:
        ser.write((0x41, 0x10, 0x0D, 0x0A))

    # Delay to account for address being set
    # Each box theoretically takes ~5ms to receive its address. Again, estimate for six boxes and include some padding
    time.sleep(0.01 * self.MAX_UNITS)

    self.enumerate()

  def _reset_master(self, bootloader: bool):
    # Reset the master (and by extension any expansion units)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(self.Pin.NRST.value, GPIO.OUT)
    GPIO.output(self.Pin.NRST.value, 0)

    # After reset the BOOT0 pin is sampled to determine whether to boot
    # from the bootloader ROM or flash.
    GPIO.setup(self.Pin.BOOT0.value, GPIO.OUT)
    GPIO.output(self.Pin.BOOT0.value, bootloader)

    # Hold the reset line low >300 ns
    time.sleep(0.001)
    GPIO.output(self.Pin.NRST.value, 1)

    # Each preamps' microcontroller takes ~3ms to startup after releasing
    # NRST. Just to be sure wait 5 ms before sending an I2C address.
    time.sleep(0.005)
    GPIO.cleanup()

  def enumerate(self):
    """ Re-enumerate preamp connections """
    self.preamps = []
    for i in range(self.MAX_UNITS):
      p = Preamp(i, self.bus)
      if not p.available():
        break
      self.preamps.append(p)

  def flash(self, filepath: str):
    """ Flash all available preamps with a given file """
    self.reset(unit = 0)
    flash = subprocess.run([f'stm32flash -vb 115200 -w {filepath} /dev/serial0'])

#class PeakDetect:
  #""" """


# Remove duplicate metavars
# https://stackoverflow.com/a/23941599/8055271
class AmpliPiHelpFormatter(argparse.HelpFormatter):
  def _format_action_invocation(self, action):
    if not action.option_strings:
      metavar, = self._metavar_formatter(action, action.dest)(1)
      return metavar
    parts = []
    if action.nargs == 0:                   # -s, --long
      parts.extend(action.option_strings)
    else:                                   # -s, --long ARGS
      args_string = self._format_args(action, action.dest.upper())
      for option_string in action.option_strings:
        parts.append('%s' % option_string)
      parts[-1] += ' %s' % args_string
    return ', '.join(parts)

  def _get_help_string(self, action):
    help_str = action.help
    if '%(default)' not in action.help:
      if action.default is not argparse.SUPPRESS and action.default is not None:
        defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
        if action.option_strings or action.nargs in defaulting_nargs:
          help_str += ' (default: %(default)s)'
    return help_str


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Interface to AmpliPi's Preamp Board firmware",
                                 formatter_class=AmpliPiHelpFormatter)
  parser.add_argument('-r', '--reset', action='store_true', default=False,
                      help='reset the preamp(s) before communicating over I2C')
  parser.add_argument('-u', '--update', action='store_true', default=False,
                      help='update the preamp(s) with the latest released firmware')
  parser.add_argument('-l', '--log', metavar='LEVEL', default='WARNING',
                      help='set logging level as DEBUG, INFO, WARNING, ERROR, or CRITICAL')
  args = parser.parse_args()

  preamps = Preamps(args.reset, args.update)
