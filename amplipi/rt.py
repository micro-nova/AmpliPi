
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

"""Runtimes to communicate with the AmpliPi hardware
"""

import math
import io
import os
import time
from enum import Enum

from typing import Dict, List, Tuple, Union

# TODO: move constants like this to their own file
DEBUG_PREAMPS = False # print out preamp state after register write

from serial import Serial
from smbus2 import SMBus

# Preamp register addresses
_REG_ADDRS = {
  'SRC_AD'          : 0x00,
  'ZONE123_SRC'     : 0x01,
  'ZONE456_SRC'     : 0x02,
  'MUTE'            : 0x03,
  'STANDBY'         : 0x04,
  'VOL_ZONE1'       : 0x05,
  'VOL_ZONE2'       : 0x06,
  'VOL_ZONE3'       : 0x07,
  'VOL_ZONE4'       : 0x08,
  'VOL_ZONE5'       : 0x09,
  'VOL_ZONE6'       : 0x0A,
  'POWER'           : 0x0B,
  'FANS'            : 0x0C,
  'LED_CTRL'        : 0x0D,
  'LED_VAL'         : 0x0E,
  'EXPANSION'       : 0x0F,
  'HV1_VOLTAGE'     : 0x10,
  'AMP_TEMP1'       : 0x11,
  'HV1_TEMP'        : 0x12,
  'AMP_TEMP2'       : 0x13,
  'PI_TEMP'         : 0x14,
  'FAN_DUTY'        : 0x15,
  'FAN_VOLTS'       : 0x16,
  'VERSION_MAJOR'   : 0xFA,
  'VERSION_MINOR'   : 0xFB,
  'GIT_HASH_27_20'  : 0xFC,
  'GIT_HASH_19_12'  : 0xFD,
  'GIT_HASH_11_04'  : 0xFE,
  'GIT_HASH_STATUS' : 0xFF,
}
_SRC_TYPES = {
  1 : 'Digital',
  0 : 'Analog',
}
_DEV_ADDRS = [0x08, 0x10, 0x18, 0x20, 0x28, 0x30]

MAX_ZONES = 6 * len(_DEV_ADDRS)

class FanCtrl(Enum):
  MAX6644 = 0
  PWM     = 1
  LINEAR  = 2
  FORCED  = 3

def is_amplipi():
  """ Check if the current hardware is an AmpliPi

    Checks if the system is a Raspberry Pi Compute Module 3 Plus
    with the proper serial port and I2C bus

    Returns:
      True if current hardware is an AmpliPi, False otherwise
  """
  is_amplipi = True

  # Check for Raspberry Pi
  try:
    # Also available in /proc/device-tree/model, and in /proc/cpuinfo's "Model" field
    with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
      desired_model = 'Raspberry Pi Compute Module 3 Plus'
      current_model = m.read()
      if desired_model.lower() not in current_model.lower():
        print(f"Device model '{current_model}'' doesn't match '{desired_model}*'")
        is_amplipi = False
  except Exception:
    print(f'Not running on a Raspberry Pi')
    is_amplipi = False

  # Check for the serial port
  if not os.path.exists('/dev/serial0'):
    print('Serial port /dev/serial0 not found')
    is_amplipi = False

  # Check for the i2c bus
  if not os.path.exists('/dev/i2c-1'):
    print('I2C bus /dev/i2c-1 not found')
    is_amplipi = False

  return is_amplipi


class _Preamps:
  """ Low level discovery and communication for the AmpliPi firmware
  """

  preamps: Dict[int, List[int]] # Key: i2c address, Val: register values

  def __init__(self, reset: bool = True, set_addr: bool = True, bootloader: bool = False, debug = True):
    self.preamps = dict()
    if not is_amplipi():
      self.bus = None # TODO: Use i2c-stub
      print('Not running on AmpliPi hardware, mocking preamp connection')
    else:
      if reset:
        self.reset_preamps(bootloader)
      if set_addr:
        self.set_i2c_addr()

      # Setup self._bus as I2C1 from the RPi
      self.bus = SMBus(1)

      # Discover connected preamp boards
      for p in _DEV_ADDRS:
        if self.probe_preamp(p):
          if debug:
            print(f'Preamp found at address {p}')
          self.new_preamp(p)
        else:
          if p == _DEV_ADDRS[0] and debug:
            print('Error: no preamps found')
          break

  def __del__(self):
    if self.bus:
      self.bus.close()


  def reset_preamps(self, bootloader: bool = False):
    """ Resets the preamp board.
        Any slave preamps will be reset one-by-one by the previous preamp.
        After resetting, an I2C address is assigned.

      Args:
        bootloader: if True set BOOT0 pin
    """
    import RPi.GPIO as GPIO
    boot0 = 1 if bootloader else 0

    # Reset preamp board before establishing a communication channel
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.OUT)
    GPIO.output(4, 0) # Low pulse on the reset line (GPIO4)
    GPIO.setup(5, GPIO.OUT)
    GPIO.output(5, boot0) # Ensure BOOT0 is set (GPIO5)
    time.sleep(0.1)
    GPIO.output(4, 1)

    # Each box theoretically takes ~11ms to undergo a reset.
    # Estimating for six boxes, including some padding,
    # wait 100ms for the resets to propagate down the line
    time.sleep(0.1)

    # Done with GPIO, they will default back to inputs with pullups
    GPIO.cleanup()

  def set_i2c_addr(self):
    """ Sends the first preamp's I2C address via UART
        The master preamp will set any expansion unit addresses
    """
    # Setup serial connection via UART pins
    with Serial('/dev/serial0', baudrate=9600) as ser:
      ser.write((0x41, 0x10, 0x0D, 0x0A))

    # Delay to account for addresses being set
    # Each box theoretically takes ~5ms to receive its address. Again, estimate for six boxes and include some padding
    time.sleep(0.1)

  def reset_expander(self, preamp: int, bootload: bool = False):
    """ Resets an expansion unit's preamp board.
        Any slave preamps will be reset one-by-one by the previous preamp.
        After resetting, an I2C address is assigned.

      Args:
        preamp:     preamp unit number [2,6]
        bootloader: if True set BOOT0 pin
    """
    assert 2 <= preamp <= 6
    # TODO: release firmware and add support here

  def new_preamp(self, addr: int):
    """ Populate initial register values """
    self.preamps[addr] = [
                            0x0F,
                            0x00,
                            0x00,
                            0x3F,
                            0x00,
                            0x4F,
                            0x4F,
                            0x4F,
                            0x4F,
                            0x4F,
                            0x4F,
                          ]

  def write_byte_data(self, preamp_addr, reg, data):
    assert preamp_addr in _DEV_ADDRS
    assert type(preamp_addr) == int
    assert type(reg) == int
    assert type(data) == int
    # dynamically update preamps (to support mock)
    if preamp_addr not in self.preamps:
      if self.bus is None:
        self.new_preamp(preamp_addr)
      else:
        return None # Preamp is not connected, do nothing

    if DEBUG_PREAMPS:
      print("writing to 0x{:02x} @ 0x{:02x} with 0x{:02x}".format(preamp_addr, reg, data))
    self.preamps[preamp_addr][reg] = data
    # TODO: need to handle volume modifying mute state in mock
    if self.bus is not None:
      try:
        time.sleep(0.001) # space out sequential calls to avoid bus errors
        self.bus.write_byte_data(preamp_addr, reg, data)
      except Exception:
        time.sleep(0.001)
        self.bus = SMBus(1)
        self.bus.write_byte_data(preamp_addr, reg, data)

  def probe_preamp(self, addr: int):
    # Scan for preamps, and set source registers to be completely digital
    # TODO: This should read version instead, but I haven't checked what relies on this yet.
    if self.bus is not None:
      try:
        self.bus.read_byte_data(addr, _REG_ADDRS['VERSION_MAJOR'])
        return True
      except Exception:
        return False
    else:
      return False

  def print_regs(self):
    """ Read all registers of every preamp and print """
    if self.bus is not None:
      for preamp in self.preamps:
        print(f'Preamp {preamp // 8}:')
        for reg, addr in _REG_ADDRS.items():
          val = self.bus.read_byte_data(preamp, addr)
          print(f'  0x{addr:02X}:{reg:<15} = 0x{val:02X}')

  def read_version(self, preamp: int = 1):
    """ Read the version of the first preamp if present

      Returns:
        major:    The major revision number
        minor:    The minor revision number
        git_hash: The git hash of the build (7-digit abbreviation)
        dirty:    False if the git hash is valid, True otherwise
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      major = self.bus.read_byte_data(preamp*8, _REG_ADDRS['VERSION_MAJOR'])
      minor = self.bus.read_byte_data(preamp*8, _REG_ADDRS['VERSION_MINOR'])
      git_hash = self.bus.read_byte_data(preamp*8, _REG_ADDRS['GIT_HASH_27_20']) << 20
      git_hash |= (self.bus.read_byte_data(preamp*8, _REG_ADDRS['GIT_HASH_19_12']) << 12)
      git_hash |= (self.bus.read_byte_data(preamp*8, _REG_ADDRS['GIT_HASH_11_04']) << 4)
      git_hash4_stat = self.bus.read_byte_data(preamp*8, _REG_ADDRS['GIT_HASH_STATUS'])
      git_hash |= (git_hash4_stat >> 4)
      dirty = (git_hash4_stat & 0x01) != 0
      return major, minor, git_hash, dirty
    return None, None, None, None

  def read_power_status(self, preamp: int = 1) -> Tuple[Union[bool, None],
    Union[bool, None], Union[bool, None], Union[bool, None], Union[float, None]]:
    """ Read the status of the power supplies

      Returns:
        pg_9v:    True if the 9V rail is good
        en_9v:    True if the 9V rail is enabled
        pg_12v:   True if the 12V rail is good
        en_12v:   True if the 12V rail is enabled
        v12:      Fan power supply voltage, nominally 12V
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      pstat = self.bus.read_byte_data(preamp*8, _REG_ADDRS['POWER'])
      en_12v = (pstat & 0x08) != 0
      pg_12v = (pstat & 0x04) != 0
      en_9v = (pstat & 0x02) != 0
      pg_9v = (pstat & 0x01) != 0
      fvstat = self.bus.read_byte_data(preamp*8, _REG_ADDRS['FAN_VOLTS'])
      v12 = fvstat / 2**4
      return pg_9v, en_9v, pg_12v, en_12v, v12
    return None, None, None, None, None

  def read_fan_status(self, preamp: int = 1) -> Tuple[Union[FanCtrl, None],
    Union[bool, None], Union[bool, None], Union[bool, None]]:
    """ Read the status of the fans

      Returns:
        ctrl:      Fan control method currently in use
        fans_on:   True if the fans are on
        ovr_tmp:   True if the amplifiers or PSU are overtemp
        failed:    True if the fans failed (only available on developer units)
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      fstat = self.bus.read_byte_data(preamp*8, _REG_ADDRS['FANS'])
      ctrl = FanCtrl(fstat & 0x03)
      fans_on = (fstat & 0x04) != 0
      ovr_tmp = (fstat & 0x08) != 0
      failed = (fstat & 0x10) != 0
      return ctrl, fans_on, ovr_tmp, failed
    return None, None, None, None

  def read_fan_duty(self, preamp: int = 1) -> Union[float, None]:
    """ Read the fans' duty cycle

      Returns:
        duty: 0-100%
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      duty = self.bus.read_byte_data(preamp*8, _REG_ADDRS['FAN_DUTY'])
      return duty / (1 << 7)
    return None

  @staticmethod
  def _fix2temp(fval: int) -> float:
    """ Convert UQ7.1 + 20 degC format to degC """
    if fval == 0: # Disconnected
      temp = -math.inf
    elif fval == 255: # Shorted
      temp = math.inf
    else:
      temp = fval/2 - 20
    return temp

  def read_temps(self, preamp: int = 1) -> Tuple[Union[float, None], Union[float, None], Union[float, None]]:
    """ Measure the temperature of the power supply and both amp heatsinks

      Args:
        preamp: preamp number from 1 to 6

      Returns:
        hv1:  Temperature of the HV1 power supply in degrees C
        amp1: Temperature of the heatsink over zones 1-3 in degrees C
        amp2: Temperature of the heatsink over zones 4-6 in degrees C
    """
    if self.bus is not None:
      temp_hv1_f = self.bus.read_byte_data(preamp*8, _REG_ADDRS['HV1_TEMP'])
      temp_amp1_f = self.bus.read_byte_data(preamp*8, _REG_ADDRS['AMP_TEMP1'])
      temp_amp2_f = self.bus.read_byte_data(preamp*8, _REG_ADDRS['AMP_TEMP2'])
      temp_hv1 = self._fix2temp(temp_hv1_f)
      temp_amp1 = self._fix2temp(temp_amp1_f)
      temp_amp2 = self._fix2temp(temp_amp2_f)
      return temp_hv1, temp_amp1, temp_amp2
    return None, None, None

  def read_hv(self, preamp: int = 1) -> Union[float, None]:
    """ Measure the High-Voltage power supply voltage

      Args:
        preamp: preamp number from 1 to 6

      Returns:
        hv1:  Voltage of the HV1 rail in Volts
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      hv1_f = self.bus.read_byte_data(preamp*8, _REG_ADDRS['HV1_VOLTAGE'])
      hv1 = hv1_f / 4 # Convert from UQ6.2 format
      return hv1
    return None

  def force_fans(self, preamp: int = 1, force: bool = True):
    assert 1 <= preamp <= 6
    if self.bus is not None:
      self.bus.write_byte_data(preamp*8, _REG_ADDRS['FANS'],
                               3 if force is True else 0)

  def read_leds(self, preamp: int = 1):
    """ Read the state of the front-panel LEDs

      Args:
        preamp: preamp number from 1 to 6

      Returns:
        leds:   A 1-byte number with each bit corresponding to an LED
                Green => Bit 0
                Red => Bit 1
                Zone[1-6] => Bit[2-7]
    """
    assert 1 <= preamp <= 6
    if self.bus is not None:
      leds = self.bus.read_byte_data(preamp*8, _REG_ADDRS['LED_VAL'])
      return leds
    return None

  def led_override(self, preamp: int = 1, leds: Union[int, None] = 0xFF):
    """ Override the LED board's LEDs

      Args:
        preamp: preamp number from 1 to 6
        leds:   A 1-byte number with each bit corresponding to an LED
                Green => Bit 0
                Red => Bit 1
                Zone[1-6] => Bit[2-7]
                None = return control to AmpliPi
    """
    assert 1 <= preamp <= 6
    assert leds is None or 0 <= leds <= 255
    if self.bus is not None:
      if leds is None:
        self.bus.write_byte_data(preamp*8, _REG_ADDRS['LED_CTRL'], 0)
      else:
        self.bus.write_byte_data(preamp*8, _REG_ADDRS['LED_CTRL'], 1)
        self.bus.write_byte_data(preamp*8, _REG_ADDRS['LED_VAL'], leds)

  def __str__(self):
    preamp_str = ''
    for preamp_addr in self.preamps.keys():
      if preamp_addr > _DEV_ADDRS[0]:
        preamp_str += '\n'
      preamp = int(preamp_addr / 8)
      preamp_str += f'Preamp {preamp}:'
      for zone in range(6):
        preamp_str += '\n' + self.get_zone_state_str(6 * (preamp - 1) + zone)
    return preamp_str

  def get_zone_state_str(self, zone):
    assert zone >= 0
    preamp = (int(zone / 6) + 1) * 8
    zone = zone % 6
    regs = self.preamps[preamp]
    src_types = self.preamps[0x08][_REG_ADDRS['SRC_AD']]
    src = ((regs[_REG_ADDRS['ZONE456_SRC']] << 8) | regs[_REG_ADDRS['ZONE123_SRC']] >> 2 * zone) & 0b11
    src_type = _SRC_TYPES.get((src_types >> src) & 0b01)
    vol = -regs[_REG_ADDRS['VOL_ZONE1'] + zone]
    muted = (regs[_REG_ADDRS['MUTE']] & (1 << zone)) > 0
    return f'  {src}({src_type[0]}) --> zone {zone} vol {vol}{" (muted)" if muted else ""}'

class Mock:
  """ Mock of an Amplipi Runtime

      This pretends to be the runtime of Amplipi, but actually does nothing
  """

  def __init__(self):
    pass

  def update_sources(self, digital):
    """ modify all of the 4 system sources

      Args:
        digital [bool*4]: array of configuration for sources where
          Analog is False and Digital True

      Returns:
        True on success, False on hw failure
    """
    assert len(digital) == 4
    for flag in digital:
      assert isinstance(flag, bool)
    return True

  def update_zone_mutes(self, zone, mutes):
    """ Update the mute level to all of the zones

      Args:
        zone int: zone to muted/unmute
        mutes [bool*zones]: array of configuration for zones where unmuted is False and Muted True

      Returns:
        True on success, False on hw failure
    """
    assert len(mutes) >= 6
    num_preamps = int(len(mutes) / 6)
    assert len(mutes) == num_preamps * 6
    for preamp in range(num_preamps):
      for zid in range(6):
        assert isinstance(mutes[preamp * 6 + zid], bool)
    return True

  def update_zone_sources(self, zone, sources):
    """ Update the sources to all of the zones

      Args:
        zid int: zone to change source
        sources [int*zones]: array of source ids for zones (None in place of source id indicates disconnect)

      Returns:
        True on success, False on hw failure
    """
    assert len(sources) >= 6
    num_preamps = int(len(sources) / 6)
    assert len(sources) == num_preamps * 6
    for preamp in range(num_preamps):
      for zid in range(6):
        src = sources[preamp * 6 + zid]
        assert isinstance(src, int) or src is None
    return True

  def update_zone_vol(self, zone, vol):
    """ Update the sources to all of the zones

      Args:
        zone: zone to adjust vol
        vol: int in range[-79, 0]

      Returns:
        True on success, False on hw failure
    """
    preamp = zone // 6
    assert zone >= 0
    assert 0 <= preamp <= 5
    assert 0 >= vol >= -79
    return True

  def exists(self, zone):
      return True

class Rpi:
  """ Actual Amplipi Runtime

      This acts as an Amplipi Runtime, expected to be executed on a raspberrypi
  """

  def __init__(self):
    self._bus = _Preamps()
    self._all_muted = True # preamps start up in muted/standby state


  def __del__(self):
    del self._bus

  def update_zone_mutes(self, zone, mutes):
    """ Update the mute level to all of the zones

      Args:
        zone int: zone to muted/unmute
        mutes [bool*zones]: array of configuration for zones where unmuted is False and Muted True

      Returns:
        True on success, False on hw failure
    """
    assert len(mutes) >= 6
    num_preamps = int(len(mutes) / 6)
    assert len(mutes) == num_preamps * 6
    preamp = zone // 6
    mute_cfg = 0x00
    for z in range(6):
      assert type(mutes[preamp * 6 + z]) == bool
      if mutes[preamp * 6 + z]:
        mute_cfg = mute_cfg | (0x01 << z)
    self._bus.write_byte_data(_DEV_ADDRS[preamp], _REG_ADDRS['MUTE'], mute_cfg)

    # Audio power needs to be on each box when subsequent boxes are playing audio
    all_muted = False not in mutes
    if self._all_muted != all_muted:
      if all_muted:
        for p in self._bus.preamps.keys():
          # Standby all preamps
          self._bus.write_byte_data(p, _REG_ADDRS['STANDBY'], 0x00)
        time.sleep(0.1)
      else:
        for p in self._bus.preamps.keys():
          # Unstandby all preamps
          self._bus.write_byte_data(p, _REG_ADDRS['STANDBY'], 0x3F)
        time.sleep(0.3)
      self._all_muted = all_muted
    return True

  def update_zone_sources(self, zone, sources):
    """ Update the sources to all of the zones

      Args:
        zone int: zone to change source
        sources [int*zones]: array of source ids for zones (None in place of source id indicates disconnect)

      Returns:
        True on success, False on hw failure
    """
    assert len(sources) >= 6
    num_preamps = int(len(sources) / 6)
    assert len(sources) == num_preamps * 6
    preamp = zone // 6

    source_cfg123 = 0x00
    source_cfg456 = 0x00
    for z in range(6):
      src = sources[preamp * 6 + z]
      assert type(src) == int or src == None
      if z < 3:
        source_cfg123 = source_cfg123 | (src << (z*2))
      else:
        source_cfg456 = source_cfg456 | (src << ((z-3)*2))
    self._bus.write_byte_data(_DEV_ADDRS[preamp], _REG_ADDRS['ZONE123_SRC'], source_cfg123)
    self._bus.write_byte_data(_DEV_ADDRS[preamp], _REG_ADDRS['ZONE456_SRC'], source_cfg456)

    # TODO: Add error checking on successful write
    return True

  def update_zone_vol(self, zone, vol):
    """ Update the volume to the specific zone

      Args:
        zone: zone to adjust vol
        vol: int in range[-79, 0]

      Returns:
        True on success, False on hw failure
    """
    preamp = int(zone / 6) # int(x/y) does the same thing as (x // y)
    assert zone >= 0
    assert preamp < 15
    assert vol <= 0 and vol >= -79

    chan = zone - (preamp * 6)
    hvol = abs(vol)

    chan_reg = _REG_ADDRS['VOL_ZONE1'] + chan
    self._bus.write_byte_data(_DEV_ADDRS[preamp], chan_reg, hvol)

    # TODO: Add error checking on successful write
    return True

  def update_sources(self, digital):
    """ modify all of the 4 system sources

      Args:
        digital [bool*4]: array of configuration for sources where
          Analog is False and Digital True

      Returns:
        True on success, False on hw failure
    """

    # Start with a fresh byte - only update on Digital (True)
    output = 0x00

    # When digital is true, set the appropriate bit to 1
    assert len(digital) == 4
    for d in digital:
      assert type(d) == bool

    for i in range(4):
      if digital[i]:
        output = output | (0x01 << i)

    # Send out the updated source information to the appropriate preamp
    self._bus.write_byte_data(_DEV_ADDRS[0], _REG_ADDRS['SRC_AD'], output)

    # TODO: update this to allow for different preamps on the bus
    # TODO: Add error checking on successful write
    return True

  def exists(self, zone):
    if self._bus:
      preamp_addr = 8 * (zone // 6 + 1)
      return preamp_addr in self._bus.preamps
    else:
      return True
