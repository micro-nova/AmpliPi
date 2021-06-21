
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
import amplipi.extras as extras

# TODO: move constants like this to their own file
DEBUG_PREAMPS = False # print out preamp state after register write

from serial import Serial
from smbus2 import SMBus

# Preamp register addresses
_REG_ADDRS = {
  'SRC_AD'          : 0x00,
  'CH123_SRC'       : 0x01,
  'CH456_SRC'       : 0x02,
  'MUTE'            : 0x03,
  'STANDBY'         : 0x04,
  'CH1_ATTEN'       : 0x05,
  'CH2_ATTEN'       : 0x06,
  'CH3_ATTEN'       : 0x07,
  'CH4_ATTEN'       : 0x08,
  'CH5_ATTEN'       : 0x09,
  'CH6_ATTEN'       : 0x0A,
  'POWER_GOOD'      : 0x0B,
  'FAN_STATUS'      : 0x0C,
  'EXTERNAL_GPIO'   : 0x0D,
  'LED_OVERRIDE'    : 0x0E,
  'HV1_VOLTAGE'     : 0x10,
  'HV2_VOLTAGE'     : 0x11,
  'HV1_TEMP'        : 0x12,
  'HV2_TEMP'        : 0x13,
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
_DEV_ADDRS = [0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78]

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
  def __init__(self):
    self.preamps = dict()
    if not is_amplipi():
      self.bus = None # TODO: Use i2c-stub
      print('Not running on AmpliPi hardware, mocking preamp connection')
    else:
      self.reset_preamps()

      # Setup self._bus as I2C1 from the RPi
      self.bus = SMBus(1)

      # Discover connected preamp boards
      for p in _DEV_ADDRS:
        if self.probe_preamp(p):
          print('Preamp found at address {}'.format(p))
          self.new_preamp(p)
        else:
          if p == _DEV_ADDRS[0]:
            print('Error: no preamps found')
          break

  def reset_preamps(self):
    """ Resets the preamp board.
        Any slave preamps will be reset one-by-one by the previous preamp.
        After resetting, an I2C address is assigned.
    """
    import RPi.GPIO as GPIO

    # Reset preamp board before establishing a communication channel
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.OUT)
    GPIO.output(4, 0) # Low pulse on the reset line (GPIO4)
    time.sleep(0.001)
    GPIO.output(4, 1)
    GPIO.cleanup()    # Done with GPIO

    # Each box theoretically takes ~11ms to undergo a reset. Estimating for six boxes, including some padding, wait 100ms for the resets to propagate down the line
    time.sleep(0.1)

    # Setup serial connection via UART pins - set I2C addresses for preamps
    addr = 0x41, 0x10, 0x0D, 0x0A
    with Serial('/dev/serial0', baudrate=9600) as ser:
      ser.write(addr)

    # Delay to account for addresses being set
    # Each box theoretically takes ~5ms to receive its address. Again, estimate for six boxes and include some padding
    time.sleep(0.1)

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
    try:
      self.bus.write_byte_data(addr, _REG_ADDRS['SRC_AD'], 0x0F)
      return True
    except Exception:
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
    assert 1 <= preamp <= 15
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
    return None

  def read_power_good(self, preamp: int = 1):
    """ Read the 'power good' signals of the first preamp if present

      Returns:
        pg_12v: True if the 12V rail is good
        pg_9v:  True if the 9V rail is good
    """
    assert 1 <= preamp <= 15
    if self.bus is not None:
      pgood = self.bus.read_byte_data(preamp*8, _REG_ADDRS['POWER_GOOD'])
      pg_12v = (pgood & 0x02) != 0
      pg_9v = (pgood & 0x01) != 0
      return pg_12v, pg_9v
    return None

  def read_fan_status(self, preamp: int = 1):
    """ Read the fan status of a single preamp

      Args:
        preamp: preamp number from 1 to 15

      Returns:
        fan_on:   True if the fan is on, False otherwise
        ovr_tmp:  True if the AmpliPi is over temp, False otherwise
        fan_fail: True if the fan has failed, False otherwise
    """
    assert 1 <= preamp <= 15
    fan_on = False
    ovr_tmp = False
    fan_fail = False
    if self.bus is not None:
      val = self.bus.read_byte_data(preamp*8, _REG_ADDRS['FAN_STATUS'])
      fan_on = (val & 0x8) != 0
      ovr_tmp = (val & 0x2) != 0x2 # Active-low
      fan_fail = (val & 0x1) != 0x1 # Active-low
      return fan_on, ovr_tmp, fan_fail
    return None

  def read_hv(self, preamp: int = 1):
    """ Read the high-voltage voltages and temps of the first preamp if present

      Args:
        preamp: preamp number from 1 to 15

      Returns:
        hv1:  Voltage of the HV1 rail
        hv2:  Voltage of the HV2 rail
        tmp1: Temperature of HV1 in degC
        tmp2: Temperature of HV2 in degC
    """
    assert 1 <= preamp <= 15
    if self.bus is not None:
      adc_to_volts = (100 + 4.7) / 4.7 * 3.3 / 255
      hv1_adc = self.bus.read_byte_data(preamp*8, _REG_ADDRS['HV1_VOLTAGE'])
      hv2_adc = self.bus.read_byte_data(preamp*8, _REG_ADDRS['HV2_VOLTAGE'])
      hv1 = hv1_adc * adc_to_volts
      hv2 = hv2_adc * adc_to_volts

      # Nominal B-Constant of 3900K, R0 resistance is 10 kOhm at 25dC (T0)
      # Thermocouple resistance = R0*e^[B*(1/T - 1/T0)] = Rt
      # ADC_VAL = 3.3V * 4.7kOhm / (4.7kOhm + Rt kOhm) / 3.3V * 255
      # Rt = 4.7 * (255 / ADC_VAL - 1)
      # T = 1/(ln(Rt/R0)/B + 1/T0)
      # T = 1/(ln(Rt/10)/3900 + 1/(25+273.5)) - 273.15
      def read_temp(reg: str):
        temp_adc = self.bus.read_byte_data(preamp*8, _REG_ADDRS[reg])
        if temp_adc == 0: # 0 causes divide-by-zero
          temp = -math.inf
        elif temp_adc == 255: # 255 causes Rt=0 which leads to ln(0)
          temp = math.inf
        else:
          rt = 4.7 * (255 / temp_adc - 1)
          temp = 1/(math.log(rt/10, math.e)/3900 + 1/(25+273.5)) - 273.15
        return temp
      tmp1 = read_temp('HV1_TEMP')
      tmp2 = read_temp('HV2_TEMP')
      return hv1, hv2, tmp1, tmp2
    return None

  def force_fans(self, preamp: int = 1, force: bool = True):
    assert 1 <= preamp <= 15
    if self.bus is not None:
      self.bus.write_byte_data(preamp*8, _REG_ADDRS['FAN_STATUS'],
                               1 if force is True else 0)

  def led_override(self, preamp: int = 1, leds: int = 0xFF):
    """ Override the LED board's LEDs

      Args:
        preamp: preamp number from 1 to 15
        leds:   A 1-byte number with each bit corresponding to an LED
                Green => Bit 0
                Red => Bit 1
                Zone[1-6] => Bit[2-7]
    """
    assert 1 <= preamp <= 15
    assert 0 <= leds <= 255
    if self.bus is not None:
      self.bus.write_byte_data(preamp*8, _REG_ADDRS['LED_OVERRIDE'], leds)

  def print(self):
    for preamp_addr in self.preamps.keys():
      preamp = int(preamp_addr / 8)
      print('preamp {}:'.format(preamp))
      src_types = self.preamps[0x08][_REG_ADDRS['SRC_AD']]
      src_cfg = []
      for src in range(4):
        src_type = _SRC_TYPES.get((src_types >> src) & 0b01)
        src_cfg += ['{}'.format(src_type)]
      print('  [{}]'.format(', '.join(src_cfg)))
      for zone in range(6):
        self.print_zone_state(6 * (preamp - 1) + zone)

  def print_zone_state(self, zone):
    assert zone >= 0
    preamp = (int(zone / 6) + 1) * 8
    zone = zone % 6
    regs = self.preamps[preamp]
    src_types = self.preamps[0x08][_REG_ADDRS['SRC_AD']]
    src = ((regs[_REG_ADDRS['CH456_SRC']] << 8) | regs[_REG_ADDRS['CH123_SRC']] >> 2 * zone) & 0b11
    src_type = _SRC_TYPES.get((src_types >> src) & 0b01)
    vol = -regs[_REG_ADDRS['CH1_ATTEN'] + zone]
    muted = (regs[_REG_ADDRS['MUTE']] & (1 << zone)) > 0
    state = []
    if muted:
      state += ['muted']
    print('  {}({}) --> zone {} vol [{}] {}'.format(src, src_type[0], zone, extras.vol_string(vol), ', '.join(state)))

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
    assert 0 <= preamp <= 15
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
    self._bus.write_byte_data(_DEV_ADDRS[preamp], _REG_ADDRS['CH123_SRC'], source_cfg123)
    self._bus.write_byte_data(_DEV_ADDRS[preamp], _REG_ADDRS['CH456_SRC'], source_cfg456)

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

    chan_reg = _REG_ADDRS['CH1_ATTEN'] + chan
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
      preamp = zone // 6
      return preamp in self._bus.preamps
    else:
      return True
