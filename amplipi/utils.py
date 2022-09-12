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

"""Utility functions

This module contains helper functions are used across the amplipi python library.
"""

import functools
import io
import json
import time
import os
import re
import subprocess
from typing import Dict, Iterable, List, Optional, Set, Tuple, TypeVar, Union

import pkg_resources # version

import amplipi.models as models

# pylint: disable=bare-except

# Helper functions
def encode(pydata):
  """ Encode a dictionary as JSON """
  return json.dumps(pydata)

def decode(j):
  """ Decode JSON into dictionary """
  return json.loads(j)

def parse_int(i, options):
  """ Parse an integer into one of the given options """
  if int(i) in options:
    return int(i)
  raise ValueError('{} is not in [{}]'.format(i, options))

def error(msg):
  """ wrap the error message specified by msg into an error """
  print('Error: {}'.format(msg))
  return {'error': msg}

VT = TypeVar("VT")

def updated_val(update: Optional[VT], val: VT) -> Tuple[VT, bool]:
  """ get the potentially updated value, @update, defaulting to the current value, @val, if it is None """
  if update is None:
    return val, False
  return update, update != val

BT = TypeVar("BT", bound='models.Base', covariant=True)

def find(items: Iterable[BT], item_id: int, key='id') -> Union[Tuple[int, BT], Tuple[None, None]]:
  """ Find an item by id """
  for i, item in enumerate(items):
    if item.__dict__[key] == item_id:
      return i, item
  return None, None

def next_available_id(items: Iterable[BT], default: int = 0) -> int:
  """ Get a new unique id among @items """
  # TODO; use `largest_item = max(items, key=lambda item: item.id, default=None)` to find max if models.Base changes id to be required
  largest_id = None
  for item in items:
    if item.id is not None:
      if largest_id is not None:
        largest_id = max(largest_id, item.id)
      else:
        largest_id = item.id
  if largest_id is not None:
    return largest_id + 1
  return default

def clamp(xval, xmin, xmax):
  """ Clamp and value between min and max """
  return max(xmin, min(xval, xmax))

def compact_str(list_:List):
  """ stringify a compact list"""
  return str(list_).replace(' ', '')

def max_len(items, len_determiner=len):
  """ Determine the item with the max len, based on the @len_determiner's definition of length

  Args:
    items: iterable items
    len_determiner: function that returns an integer

  Returns:
    len: integer

  This is useful for lining up lists printed in a table-like format
  """
  largest = max(items, key=len_determiner)
  return len_determiner(largest)

def abbreviate_src(src_type):
  """ Abbreviate source's type for pretty printing """
  return src_type[0].upper() if src_type else '_'

def src_zones(status: models.Status) -> Dict[int, List[int]]:
  """ Get a mapping from source ids to zones """
  return { src.id : [ zone.id for zone in status.zones if zone.id is not None and zone.source_id == src.id] for src in status.sources if src.id is not None}

@functools.lru_cache(1)
def available_outputs():
  """ get the available alsa outputs (we are expecting ch0-ch3).

  Returns:
    outputs: iterable list of alsa outputs

  This will cache the result since alsa outputs do not change dynamically (unless you edit a config file).
  """
  try:
    outputs = [ o for o in subprocess.check_output('aplay -L'.split()).decode().split('\n') if o and o[0] != ' ' ]
  except:
    outputs = []
  if 'ch0' not in outputs:
    print('WARNING: ch0, ch1, ch2, ch3 audio devices not found. Is this running on an AmpliPi?')
  return outputs

def output_device(sid: int) -> str:
  """ Get a source's corresponding ALSA output device string """
  dev = 'ch' + str(sid)
  if dev in available_outputs():
    return dev
  return 'default' # fallback to default

def zones_from_groups(status: models.Status, groups: List[int]) -> Set[int]:
  """ Get the set of zones from some groups """
  zones = set()
  for gid in groups:
    # add all of the groups zones
    _, match = find(status.groups, gid)
    if match is not None:
      zones.update(match.zones)
  return zones

def zones_from_all(status: models.Status, zones: Optional[List[int]], groups: Optional[List[int]]) -> Set[int]:
  """ Find the unique set of enabled zones given some zones and some groups of zones """
  # add all of the zones given
  z_unique = set(zones or [])
  # add all of the zones in the groups given
  z_unique.update(zones_from_groups(status, groups or []))
  return z_unique

def enabled_zones(status: models.Status, zones: Set[int]) -> Set[int]:
  """ Get only enabled zones """
  z_disabled = {z.id for z in status.zones if z.id is not None and z.disabled}
  return zones.difference(z_disabled)

@functools.lru_cache(maxsize=8)
def get_folder(folder):
  """ Get a directory
  Abstracts the directory structure """
  if not os.path.exists(folder):
    try:
      os.mkdir(folder)
    except:
      print(f'Error creating dir: {folder}')
  return os.path.abspath(folder)

TOML_VERSION_STR = re.compile(r'version\s*=\s*"(.*)"')

@functools.lru_cache(1)
def detect_version() -> str:
  """ Get the AmpliPi software version from the project TOML file """
  # assume the application is running in its base directory and check the pyproject.toml file to determine the version
  # this is needed for a straight github checkout (the common developement paradigm at MicroNova)
  version = 'unknown'
  script_folder = os.path.dirname(os.path.realpath(__file__))
  try:
    with open(os.path.join(script_folder, '..', 'pyproject.toml')) as proj_file:
      for line in proj_file.readlines():
        if 'version' in line:
          match = TOML_VERSION_STR.search(line)
          if match is not None:
            version = match.group(1)
  except:
    pass
  if version == 'unknown':
    try:
      version = pkg_resources.get_distribution('amplipi').version
    except:
      pass
  return version

def is_amplipi():
  """ Check if the current hardware is an AmpliPi

    Checks if the system is a Raspberry Pi Compute Module 3 Plus
    with the proper serial port and I2C bus

    Returns:
      True if current hardware is an AmpliPi, False otherwise
  """
  amplipi = True

  # Check for Raspberry Pi
  try:
    # Also available in /proc/device-tree/model, and in /proc/cpuinfo's "Model" field
    with io.open('/sys/firmware/devicetree/base/model', 'r') as model:
      desired_model = 'Raspberry Pi Compute Module 3 Plus'
      current_model = model.read()
      if desired_model.lower() not in current_model.lower():
        print(f"Device model '{current_model}'' doesn't match '{desired_model}*'")
        amplipi = False
  except Exception:
    print('Not running on a Raspberry Pi')
    amplipi = False

  # Check for the serial port
  if not os.path.exists('/dev/serial0'):
    print('Serial port /dev/serial0 not found')
    amplipi = False

  # Check for the i2c bus
  if not os.path.exists('/dev/i2c-1'):
    print('I2C bus /dev/i2c-1 not found')
    amplipi = False

  return amplipi

_is_online = False
_last_online_check = 0
def is_online():
  """Throttled check if the system is conencted to the internet, throttle allows for simple polling by controller"""
  global _is_online, _last_online_check
  if time.time() > _last_online_check + 2:
    status_dir = f"{get_folder('config')}/status"
    _is_online = False
    _last_online_check = time.time()
    try:
      with open(os.path.join(status_dir,'online'), encoding='utf-8') as fonline:
        _is_online = 'online' in fonline.readline()
    except Exception:
      pass
  return _is_online

_latest_release = 'unknown'
_last_release_check = 0
def latest_release():
  """Throttled check for latest release, throttle allows for simple polling by controller"""
  global _latest_release, _last_release_check
  now = time.time()
  if now > _last_release_check + 60:
    status_dir = f"{get_folder('config')}/status"
    _latest_release = 'unknown'
    _last_release_check = time.time()
    try:
      print('checking latest release')
      with open(os.path.join(status_dir,'latest_release'), encoding='utf-8') as flatest:
        _latest_release = flatest.readline().strip()
    except Exception as exc:
      print(f'Error getting latest_release: {exc}')
      pass
  else:
    print(f'using cached latest release {now} (now) <= {_last_release_check} + 60')
  return _latest_release

def vol_float_to_db(vol: float, db_min: int = models.MIN_VOL_DB, db_max: int = models.MAX_VOL_DB) -> int:
  """ Convert floating-point volume to dB """
  # A linear conversion works here because the volume control IC directly takes dB.
  # Alternatively a logarithmic function or power <1 could be used:
  # dB = log_{s+1}(s*x+1) where s is a scaling factor
  # dB = x^0.5
  range_f = models.MAX_VOL_F - models.MIN_VOL_F
  range_db = db_max - db_min
  vol_db = round((vol - models.MIN_VOL_F) * range_db / range_f + db_min)
  vol_db_clamped = clamp(vol_db, models.MIN_VOL_DB, models.MAX_VOL_DB)
  return vol_db_clamped

def vol_db_to_float(vol: int, db_min: int = models.MIN_VOL_DB, db_max: int = models.MAX_VOL_DB) -> float:
  """ Convert volume in a dB range to floating-point """
  range_f = models.MAX_VOL_F - models.MIN_VOL_F
  range_db = db_max - db_min
  vol_f = (vol - db_min) * range_f / range_db + models.MIN_VOL_F
  vol_f_clamped = clamp(vol_f, models.MIN_VOL_F, models.MAX_VOL_F)
  return vol_f_clamped
