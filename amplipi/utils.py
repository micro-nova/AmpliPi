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
import logging
import sys
import time
import os
import re
import subprocess
import shlex
import pathlib
import pwd
from typing import Dict, Iterable, List, Optional, Set, Tuple, TypeVar, Union
from fastapi import HTTPException, status, Depends

import pkg_resources  # version

from amplipi import models
from amplipi.defaults import USER_CONFIG_DIR

# pylint: disable=bare-except

IDENTITY_FILE = os.path.join(USER_CONFIG_DIR, "identity")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

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
  raise ValueError(f'{i} is not in [{options}]')


def error(msg):
  """ wrap the error message specified by msg into an error """
  logger.error(f'Error: {msg}')
  return {'error': msg}


VT = TypeVar("VT")


def updated_val(update: Optional[VT], val: VT) -> Tuple[VT, bool]:
  """ get the potentially updated value, @update, defaulting to the current value, @val, if it is None """
  if update is None:
    return val, False
  return update, update != val


BT_co = TypeVar("BT_co", bound='models.Base', covariant=True)


def find(items: Iterable[BT_co], item_id: Optional[int], key='id') -> Union[Tuple[int, BT_co], Tuple[None, None]]:
  """ Find an item by id """
  if item_id is None:
    return None, None
  for i, item in enumerate(items):
    if item.__dict__[key] == item_id:
      return i, item
  return None, None


def next_available_id(items: Iterable[BT_co], default: int = 0) -> int:
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


def compact_str(list_: List):
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
  return {src.id: [zone.id for zone in status.zones if zone.id is not None and zone.source_id == src.id] for src in status.sources if src.id is not None}


@functools.lru_cache(1)
def available_outputs():
  """ get the available alsa outputs (we are expecting ch0-ch3).

  Returns:
    outputs: iterable list of alsa outputs

  This will cache the result since alsa outputs do not change dynamically (unless you edit a config file).
  """
  try:
    outputs = [o for o in subprocess.check_output('aplay -L'.split()).decode().split('\n') if o and o[0] != ' ']
  except:
    outputs = []
  if 'ch0' not in outputs:
    logger.critical('WARNING: ch0, ch1, ch2, ch3 audio devices not found. Is this running on an AmpliPi?')
  return outputs


def virtual_output_device(vsid: int) -> str:
  """ Get a virtual source's corresponding ALSA output device string """
  # NOTE: we use the other side (DEV=1) for devices 6-11 since we only have 6 loopbacks
  lb_id = vsid % 6
  lb_dev_in = vsid // 6
  assert vsid < 12, "only 12 virtual outputs are supported"
  # dev = f'plughw:CARD=Loopback_{lb_id},DEV={lb_dev_in}'.replace('_0', '') # use the loopback dmixer (plughw and hw don't work here)
  dev = f'lb{vsid}c'
  if dev in available_outputs():
    return dev
  return 'default'  # for now we want basic streams to play for testing


def configure_inputs():
  """ The IEC598 and Aux inputs are being muted/misconfigured during system startup

    Enable the capture capability for Aux and IEC958 and set capture volume to 100% (unmuted) """
  if is_amplipi():
    # setup usb soundcard input volumes and unmute
    try:
      # is 'set Speaker 100%' required??
      subprocess.run(shlex.split(r'amixer -D hw:cmedia8chint set Speaker 100% unmute'), check=True)
      subprocess.run(shlex.split('amixer -D hw:cmedia8chint set Line capture cap 0dB playback mute 0%'), check=True)
      subprocess.run(shlex.split('amixer -D hw:cmedia8chint set "IEC958 In" cap'), check=True)
    except Exception as e:
      logger.exception(f'Failed to configure inputs: {e}')


def virtual_connection_device(vsid: int) -> Optional[str]:
  """ Get a virtual source's corresponding connection (capture device) string for use with alsaloop """
  # NOTE: we use the other side (DEV=0) for devices 6-11 since we only have 6 loopbacks
  lb_id = vsid % 6
  lb_dev_in = vsid // 6
  lb_dev_out = {0: 1, 1: 0}[lb_dev_in]  # loopback output is on the opposite side
  assert vsid < 12, "only 12 virtual outputs are supported"
  # dev = f'hw:CARD=Loopback_{lb_id},DEV={lb_dev_out}'.replace('_0', '') # here we use the hw side
  dev = f'lb{vsid}p'
  if dev in available_outputs():
    return dev.replace('CARD=', '').replace('DEV=', '')  # alsaloop doesn't like these specifiers
  return None


def real_output_device(sid: int) -> str:
  """ Get the plug ALSA device connected directly to an output DAC """
  dev = f'ch{sid}'
  if dev in available_outputs():
    return dev
  return 'default'


def enable_aux_input():
  """ Select the Aux input as the capture source """
  try:
    subprocess.check_call('amixer -D hw:cmedia8chint set "PCM Capture Source",0 Line',
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  except subprocess.CalledProcessError as e:
    logger.exception(f'Failed to enable Aux input: {e}')


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
def get_folder(relative_folder, mock=False):
  """ Get a directory
  Abstracts the directory structure. TODO: This does not find the correct directory when testing.
  """
  if relative_folder == "config":
    folder = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')
  elif relative_folder == "web":
    folder = os.path.join(os.path.expanduser('~'), '.config', 'amplipi', 'web')
  else:
    folder = os.path.join(os.path.expanduser('~'), 'amplipi-dev', relative_folder)

  if not os.path.exists(folder) and not mock:
    try:
      os.mkdir(folder)
    except:
      logger.exception(f'Error creating dir: {folder}')
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
    with open(os.path.join(script_folder, '..', 'pyproject.toml'), encoding='utf-8') as proj_file:
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
    with io.open('/sys/firmware/devicetree/base/model', 'r', encoding='utf-8') as model:
      desired_model = 'Raspberry Pi Compute Module 3 Plus'
      current_model = model.read()
      if desired_model.lower() not in current_model.lower():
        logger.info(f"Device model '{current_model}'' doesn't match '{desired_model}*'")
        amplipi = False
  except Exception:
    logger.exception('Not running on a Raspberry Pi')
    amplipi = False

  # Check for the serial port
  if not os.path.exists('/dev/serial0'):
    logger.critical('Serial port /dev/serial0 not found')
    amplipi = False

  # Check for the i2c bus
  if not os.path.exists('/dev/i2c-1'):
    logger.critical('I2C bus /dev/i2c-1 not found')
    amplipi = False

  return amplipi


class TimeBasedCache:
  """ Cache the value of a timely but costly method, @updater, for @keep_for s """

  def __init__(self, updater, keep_for: float, name):
    self.name = name
    self._updater = updater
    self._keep_for = keep_for
    self._update()

  def _update(self):
    self._val = self._updater()
    self._last_check = time.time()

  def get(self, throttled=True):
    """ Get the potentially cached value """
    now = time.time()
    if not throttled or now > self._last_check + self._keep_for:
      self._update()
    return self._val


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


def debug_enabled() -> bool:
  """ Returns true or false if debug is enabled """
  return pathlib.Path.home().joinpath(".config/amplipi/debug.json").exists()


def get_identity() -> dict:
  """ Returns the identity file contents """
  identity: Dict[str, str] = {
    'name': 'AmpliPi',
    'website': 'http://www.amplipi.com',
    'touch_logo': 'amplipi/display/imgs/amplipi_320x126.png'
  }
  # Load fields from special identity file (if it exists), falling back to default values above
  try:
    with open(IDENTITY_FILE, encoding='utf-8') as identity_file:
      potential_identity = json.load(identity_file)
      identity.update(potential_identity)
  except FileNotFoundError as e:
    logger.exception(f'Error loading identity file: {e}')
    logger.info('Creating an identity file from defaults.')
    os.makedirs(USER_CONFIG_DIR, mode=0o700, exist_ok=True)
    with open(IDENTITY_FILE, encoding='utf-8', mode='w') as repair_file:
      json.dump(identity, repair_file)
  except json.JSONDecodeError as e:
    logger.exception(f'Error loading identity file as JSON: {e}')
    logger.info('Moving the old one to a backup and creating an identity file from defaults.')
    os.rename(IDENTITY_FILE, f"{IDENTITY_FILE}.{time.time()}")
    with open(IDENTITY_FILE, encoding='utf-8', mode='w') as repair_file:
      json.dump(identity, repair_file)
  except Exception as e:
    logger.exception(f'Error loading identity file: {e}')
    raise e
  return identity


def set_identity(settings: Dict):
  identity = get_identity()
  identity.update(settings)
  with open(os.path.join(USER_CONFIG_DIR, 'identity'), encoding='utf-8', mode='w') as identity_file:
    json.dump(identity, identity_file)


def load_extra_fields(filename: str = 'extra_fields.json') -> Optional[Dict]:
  """ This function is used to scrape extra fields for 3rd party integrations from a
      local file on the filesystem. At present, these fields end up populating in the
      `Info` model.
  """
  try:
    with open(os.path.join(USER_CONFIG_DIR, filename), encoding='utf-8', mode='r') as extra_fields_file:
      return json.load(extra_fields_file)
  except Exception:
    return None


def careful_proc_shutdown(proc: subprocess.Popen, proc_name="process"):
  """ Shutdown a process, waiting for it to exit """
  try:
    proc.terminate()
    proc.wait(timeout=3)
  except Exception as e:
    logger.exception(f"failed to terminate {proc_name}: {e}")
    proc.kill()
    proc.wait(timeout=3)


def clear_custom_configs():
  """ This clears out any custom configs on the appliance for a factory reset, including:
      * support tunnels
      * user configs (as of Aug 2024, just an "admin" user with a password set)
  """
  # Attempt to clear any support tunnels before wiping configs.
  try:
    running_support_tunnels = subprocess.run(
      "/opt/support_tunnel/venv/bin/python -m invoke list-running-tunnels".split(),
      cwd="/opt/support_tunnel",
      capture_output=True,
      text=True,
      check=True
    )
  except Exception as e:
    logger.exception(f"failed to list support tunnels: {e}")
  try:
    if running_support_tunnels and running_support_tunnels.stdout:
      for tunnel in [i.split()[0] for i in running_support_tunnels.stdout.split(sep='\n')]:
        subprocess.run(
          f"/opt/support_tunnel/venv/bin/python -m invoke stop {tunnel}".split(),
          cwd="/opt/support_tunnel",
          check=True
        )
  except Exception as e:
    logger.exception(f"failed to stop support tunnel: {e}")

  # Explicitly clear any wireguard configs, in spite of the above cleanup.
  # We use subprocess instead of python native file operations to get priv esc.
  try:
    wg_configs = subprocess.run("sudo ls /etc/wireguard".split(), capture_output=True, text=True, check=True)
    if wg_configs.stdout:
      for wg_config in wg_configs.stdout.split():
        subprocess.run(f"sudo rm /etc/wireguard/{wg_config}".split(), check=True)
  except Exception as e:
    logger.exception(f"failed to remove wireguard configs: {e}")

  # Remove any user/group that starts with support*, but leave their home directories.
  # We leave the home directories in case there is important troubleshooting data, audit logs,
  # et al, in case a second support tunnel is necessary for a recurring issue or similar.
  support_users = [u for u in pwd.getpwall() if u.pw_name.startswith("support")]
  try:
    for user in support_users:
      subprocess.run(f"sudo deluser {user.pw_name}".split(), check=True)
  except Exception as e:
    logger.exception(f"failed to delete user {user.pw_name}: {e}")

  # Remove these paths whole-cloth. They do not need special permissions.
  for path in ["/var/lib/support_tunnel/device.db", "/home/pi/.config/amplipi/users.json"]:
    try:
      os.remove(path)
    except Exception as e:
      logger.exception(f"failed to clear device configuration: {e}")
