#!/usr/bin/env python3
#
# AmpliPi Home Audio
# Copyright (C) 2022 MicroNova LLC
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

"""AmpliPi hardware interface """

# Standard imports
import argparse
from enum import Enum
import subprocess
import sys
import time
import logging
from typing import List, Optional

# Third-party imports
from serial import Serial
from serial.serialutil import SerialException
from smbus2 import SMBus

from amplipi import formatter
from amplipi import utils

if utils.is_amplipi():
  from RPi import GPIO

PI_SERIAL_PORT = '/dev/serial0'


class FwVersion:
  """ Represents the Preamp Board's firmware version """

  major: int
  minor: int
  git_hash: int
  dirty: bool

  def __init__(self, major: int = 0, minor: int = 0, git_hash: int = 0, dirty: bool = False):
    if not 0 <= major <= 255 or not 0 <= minor <= 255:
      raise ValueError(f'Major and minor version must be in the range [0,255]. Found: {major}.{minor}')
    if not 0 <= git_hash <= 0xFFFFFFF:
      raise ValueError('Hash must be an unsigned 28-bit value')
    self.major = major
    self.minor = minor
    self.git_hash = git_hash
    self.dirty = dirty

  def __str__(self):
    return f'{self.major}.{self.minor}-{self.git_hash:07X}{"-dirty" if self.dirty else ""}'

  def __repr__(self):
    return f'FwVersion({self.major}, {self.minor}, {self.git_hash:07X}, {self.dirty})'


class Preamp:
  """ Low level discovery and communication for the AmpliPi Preamp's firmware """

  class Reg(Enum):
    """ Preamp register addresses """
    SRC_AD = 0x00
    ZONE123_SRC = 0x01
    ZONE456_SRC = 0x02
    MUTE = 0x03
    STANDBY = 0x04
    VOL_ZONE1 = 0x05
    VOL_ZONE2 = 0x06
    VOL_ZONE3 = 0x07
    VOL_ZONE4 = 0x08
    VOL_ZONE5 = 0x09
    VOL_ZONE6 = 0x0A
    POWER_STATUS = 0x0B
    FAN_CTRL = 0x0C
    LED_CTRL = 0x0D
    LED_VAL = 0x0E
    EXPANSION = 0x0F
    HV1_VOLTAGE = 0x10
    AMP_TEMP1 = 0x11
    HV1_TEMP = 0x12
    AMP_TEMP2 = 0x13
    VERSION_MAJOR = 0xFA
    VERSION_MINOR = 0xFB
    GIT_HASH_27_20 = 0xFC
    GIT_HASH_19_12 = 0xFD
    GIT_HASH_11_04 = 0xFE
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
    except:  # OSError as err:
      # print(err)
      return False
    return True

  def read_leds(self) -> int:
    """ Read the LED board's status

      Returns:
        leds:   A 1-byte number with each bit corresponding to an LED
                Bit 0 => Green,
                Bit 1 => Red,
                Bit[2-7] => Zone[1-6]
    """
    return self.bus.read_byte_data(self.addr, self.Reg.LED_CTRL.value)

  def write_leds(self, leds: int = 0xFF) -> None:
    """ Override the LED board's LEDs

      Args:
        leds:   A 1-byte number with each bit corresponding to an LED
                Bit 0 => Green,
                Bit 1 => Red,
                Bit[2-7] => Zone[1-6]
    """
    assert 0 <= leds <= 255
    self.bus.write_byte_data(self.addr, self.Reg.LED_CTRL.value, leds)

  def read_version(self) -> FwVersion:
    """ Read the firmware version of the preamp

      Returns:
        major:    The major revision number
        minor:    The minor revision number
        git_hash: The git hash of the build (7-digit abbreviation)
        dirty:    False if the git hash is valid, True otherwise
    """
    major = self.bus.read_byte_data(self.addr, self.Reg.VERSION_MAJOR.value)
    minor = self.bus.read_byte_data(self.addr, self.Reg.VERSION_MINOR.value)
    git_hash = self.bus.read_byte_data(self.addr, self.Reg.GIT_HASH_27_20.value) << 20
    git_hash |= (self.bus.read_byte_data(self.addr, self.Reg.GIT_HASH_19_12.value) << 12)
    git_hash |= (self.bus.read_byte_data(self.addr, self.Reg.GIT_HASH_11_04.value) << 4)
    git_hash4_stat = self.bus.read_byte_data(self.addr, self.Reg.GIT_HASH_STATUS.value)
    git_hash |= (git_hash4_stat >> 4)
    dirty = (git_hash4_stat & 0x01) != 0
    return FwVersion(major, minor, git_hash, dirty)

  def reset_expander(self, bootloader: bool = False) -> None:
    """ Resets expansion unit connected to this preamp, if any """
    # Enter reset state
    reg_val = 0x02 if bootloader else 0x00
    self.bus.write_byte_data(self.addr, self.Reg.EXPANSION.value, reg_val)

    # Hold the reset line low >300 ns, then set high
    time.sleep(0.01)
    reg_val |= 1
    self.bus.write_byte_data(self.addr, self.Reg.EXPANSION.value, reg_val)

    # Each preamps' microcontroller takes ~3ms to startup after releasing
    # NRST. Just to be sure wait 5 ms before sending an I2C address.
    time.sleep(0.01)

  def uart_passthrough(self, passthrough: bool) -> None:
    """ Configures this preamp to passthrough UART1 <-> UART2 """
    reg_val = self.bus.read_byte_data(self.addr, self.Reg.EXPANSION.value)
    if passthrough:
      reg_val |= 0x04
    else:
      reg_val &= ~0x04
    self.bus.write_byte_data(self.addr, self.Reg.EXPANSION.value, reg_val)


class Preamps:
  """ AmpliPi Preamp Board manager """

  MAX_UNITS = 6
  """ The maximum number of AmpliPi units, including the master """

  BAUD_RATES = (1200, 1800, 2400, 4800, 9600, 19200,
                38400, 57600, 115200, 128000, 230400, 256000,
                460800, 500000, 576000, 921600, 1000000)
  """ Valid UART baud rates """

  class Pin(Enum):
    """ Pi GPIO pins to control the master unit's preamp """
    NRST = 4
    BOOT0 = 5

  preamps: List[Preamp]

  def __init__(self, reset: bool = False):
    self._bus = SMBus(1)
    self.preamps = []
    if reset:
      logging.info('Resetting all preamps...')
      self.reset(unit=0, bootloader=False)
    else:
      self.enumerate()

  def __del__(self):
    del self._bus

  def __getitem__(self, key: int) -> Preamp:
    return self.preamps[key]

  def __setitem__(self, key: int, value: Preamp) -> None:
    self.preamps[key] = value

  def __len__(self) -> int:
    return len(self.preamps)

  def unit_num_to_name(self, unit: int):
    """ Convert a unit's number to its name """
    assert 0 <= unit < self.MAX_UNITS
    if unit == 0:
      return 'Main Unit'
    else:
      return f'Expander {unit}'

  def reset(self, unit: int = 0, bootloader: bool = False) -> None:
    """ Resets the master unit's preamp board.
        Any expansion preamps will be reset one-by-one by the previous preamp.
        After resetting, an I2C address is assigned.

      Args:
        unit:       Reset from the given unit number onward. 0=master
        bootloader: If True, set BOOT0 pin high to enter bootloader mode after reset
    """

    if unit == 0:
      # Reset and return if bringing up in bootloader mode
      self._reset_master(bootloader)
      if bootloader:
        time.sleep(0.01)
        return

      # Send I2C address over UART
      self.set_i2c_address()

    else:
      self.preamps[unit - 1].reset_expander(bootloader)
      # TODO: If bootloader=False, set the address either here or in firmware

    # Delay to account for address being set
    # Each box theoretically takes ~5ms to receive its address.
    # Again, estimate for max boxes and include some padding
    time.sleep(0.01 * (self.MAX_UNITS - unit))

    # If resetting the master and not entering bootloader mode, re-enumerate
    if not bootloader and unit == 0:
      self.enumerate()

  def _reset_master(self, bootloader: bool) -> None:
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

    # Each preamps' microcontroller takes ~6ms to startup after releasing
    # NRST. Just to be sure wait 10 ms before sending an I2C address.
    time.sleep(0.01)
    GPIO.cleanup()

  def set_i2c_address(self, baud: int = 9600) -> bool:
    """ Set the preamp's slave I2C address via UART """
    assert baud in self.BAUD_RATES
    addr_arr = bytes((0x41, 0x10, 0x0A))
    try:
      with Serial(PI_SERIAL_PORT, baudrate=baud, timeout=1) as ser:
        ser.write(addr_arr)
        return True
    except SerialException as ser_err:
      logging.exception(ser_err)
      return False

  def enumerate(self, debug: bool = False) -> None:
    """ Re-enumerate preamp connections """
    self.preamps = []
    for i in range(self.MAX_UNITS):
      p = Preamp(i, self._bus)
      if not p.available():
        break
      self.preamps.append(p)
    if debug:
      logging.debug(f'Found {len(self.preamps)} preamp(s)')

  def program(self, filepath: str, unit: int = 0, baud: int = 115200) -> bool:
    """ Attempt to program a single AmpliPi unit

        This function assumes any previous units exist,
        but does not assume the requested unit exists.
        If it does not exist then this function will return False.
    """

    # If the unit is running print its current version info
    preamp = Preamp(unit, self._bus)
    i2c_present = preamp.available()
    logging.info(f"{self.unit_num_to_name(unit)}'s old firmware version: {preamp.read_version() if i2c_present else 'unknown'}")

    # For now the firmware can only pass through 9600 baud to expanders
    baud = 9600 if unit > 0 else baud

    # Reset the unit to be programmed into bootloader mode
    self.reset(unit=unit, bootloader=True)

    # Set UART passthrough on any previous units
    for p in range(unit):
      logging.info(f"Setting {self.unit_num_to_name(p)}'s UART as passthrough")
      self.preamps[p].uart_passthrough(True)

    if unit > 1:
      # Before attempting programming, verify the unit even exists.
      try:
        subprocess.run([f'stm32flash -b {baud} {PI_SERIAL_PORT}'], shell=True,
                       check=True, stdout=subprocess.DEVNULL)
      except subprocess.CalledProcessError:
        # Failed to handshake with the bootloader. Assume unit not present.
        logging.exception(f"Couldn't communicate with {self.unit_num_to_name(unit)}'s bootloader.")
        plural = 's are' if unit != 1 else ' is'
        logging.info(f'Assuming only {unit} unit{plural} present and stopping programming')

        # Reset all units to make sure the UART passthrough and
        # bootloader modes are cleared.
        self.reset()
        return False

    prog_success = False
    try:
      subprocess.run([f'stm32flash -vb {baud} -w {filepath} {PI_SERIAL_PORT}'],
                     shell=True, check=True)
      prog_success = True
    except subprocess.CalledProcessError:
      # TODO: Error handling
      logging.exception(f'Error programming {self.unit_num_to_name(unit)}, stopping programming')

    # Done programming unit, reset to exit bootloader
    self.reset()

    # Verify newly programmed unit communicates
    if preamp.available():
      logging.info(f"{self.unit_num_to_name(unit)}'s new firmware version: {preamp.read_version()}")
    else:
      # Can't communicate to unit, give up
      # TODO: retry?
      logging.critical(f"Couldn't communicate to {self.unit_num_to_name(unit)} after programming, stopping programming")
      return False

    if not prog_success:
      return False
    # Programming succeeded!
    return True

  def program_all(self, filepath: str, num_units: Optional[int] = None, baud: int = 115200) -> bool:
    """ Program all available preamps with a given file
        If num_units is not None, programming will stop after num_units
    """

    if baud not in self.BAUD_RATES:
      raise ValueError(f'Baud rate must be one of {self.BAUD_RATES}')

    # By default assume there could be up to the max number of units.
    # This is an attempt to never leave any units in a bad firmware state.
    program_count = self.MAX_UNITS
    if num_units is not None:
      # Limit the number of units that will be programmed
      program_count = num_units
    if program_count <= 0:
      # No units requested to be programmed, exit
      return False
    previous_unit_count = len(self)
    logging.info(f'Programming up to {program_count} AmpliPi Preamps '
          f'({previous_unit_count} currently detected)')

    # Attempt programming until program_count, but stop if an error occurs
    unit = 0
    success = True
    while success and unit < program_count:
      print() # PR COMMENT: Why the empty print?
      success = self.program(filepath, unit, baud)
      if success:
        unit += 1

    # By default assume programming failed, then check the multiple
    # conditions that mean success.
    success = False
    if num_units is not None:
      # A specific number of units were requested to be programmed
      logging.info(f'\n{unit} of {num_units} AmpliPi preamps programmed.')
      if unit >= num_units:
        # At least as many units were programmed as requested, so success!
        success = True
    else:
      # No specific number requested, so take the amount found before
      # programming as the correct amount.
      plural = 's' if unit != 1 else ''
      logging.info(f'\n{unit} AmpliPi preamp{plural} programmed.')
      if unit >= max(previous_unit_count, 1):
        # Sucessfully programmed at least as many units as were previously available
        # or at least 1 if no units were previously found, so success!
        success = True

    if success:
      logging.info('Programming succeeded.')
      return True
    logging.error('Programming failed.')
    return False


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Interface to AmpliPi's Preamp Board firmware",
                                   formatter_class=formatter.AmpliPiHelpFormatter)
  parser.add_argument('-r', '--reset', action='store_true', default=False,
                      help='reset the preamp(s) before communicating over I2C')
  parser.add_argument('--flash', metavar='FW.bin',
                      help='update the preamp(s) with the firmware in a .bin file')
  parser.add_argument('-b', '--baud', type=int, default=115200,
                      help='baud rate to use for UART communication')
  parser.add_argument('-v', '--version', action='store_true', default=False,
                      help='print preamp firmware version(s)')
  parser.add_argument('-l', '--log', metavar='LEVEL', default='WARNING',
                      help='set logging level as DEBUG, INFO, WARNING, ERROR, or CRITICAL')
  parser.add_argument('-n', '--num-units', metavar='N', type=int, choices=range(1, 7),
                      help='set the number of preamps instead of auto-detecting')
  args = parser.parse_args()

  preamps = Preamps(args.reset)

  if args.flash is not None:
    if not preamps.program_all(filepath=args.flash, num_units=args.num_units, baud=args.baud):
      sys.exit(2)

  if len(preamps) == 0:
    logging.warning('No preamps found, exiting')
    sys.exit(1)

  if args.version:
    main_version = preamps[0].read_version()
    logging.info(f"Main preamp's firmware version: {main_version}")
