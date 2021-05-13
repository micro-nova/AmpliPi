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

"""Utility functions

This module contains helper functions are used across the amplipi python library.
"""

import json
import os
import functools
import wrapt
import subprocess
import re
import pkg_resources # version

from typing import Collection, Optional, Tuple, TypeVar

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
  else:
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
  else:
    return update, update != val

def find(items: Collection[VT], id, key='id') -> Tuple[Optional[int], Optional[VT]]:
  return next(filter(lambda ie: ie[1].__dict__['id'] == id, enumerate(items)), (None, None))

def clamp(x, xmin, xmax):
    return max(xmin, min(x, xmax))

def compact_str(l):
  """ stringify a compact list"""
  assert type(l) == list
  return str(l).replace(' ', '')

def max_len(items, len_determiner=len):
  """ determine the item with the max len, based on the @len_determiner's definition of length

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
  return src_type[0].upper() if src_type else '_'

cached_outputs = None
def available_outputs():
  """ get the available alsa outputs (we are expecting ch0-ch3).

  Returns:
    outputs: iterable list of alsa outputs

  This will cache the result since alsa outputs do not change dynamically (unless you edit a config file).
  """
  global cached_outputs
  if cached_outputs is None:
    try:
      cached_outputs = [ o for o in subprocess.check_output('aplay -L'.split()).decode().split('\n') if o and o[0] != ' ' ]
    except:
      cached_outputs = []
    if 'ch0' not in cached_outputs:
      print('WARNING: ch0, ch1, ch2, ch3 audio devices not found. Is this running on an AmpliPi?')
  return cached_outputs

def output_device(src):
  dev = 'ch' + str(src)
  if dev in available_outputs():
    return dev
  else:
    return 'default' # fallback to default

@functools.lru_cache(maxsize=8)
def get_folder(folder):
  if not os.path.exists(folder):
    try:
      os.mkdir(folder)
    except:
      print(f'Error creating dir: {folder}')
  return os.path.abspath(folder)

@wrapt.decorator
def save_on_success(wrapped, instance, args, kwargs):
  result = wrapped(*args, **kwargs)
  if result is None:
    # call postpone_save instead of save to reduce the load/delay of a request
    instance.postpone_save()
    pass
  return result

def with_id(elements: Optional[Collection[VT]]) -> Optional[VT]:
  if elements is None:
    return []
  return [ e for e in elements if 'id' in e ]

def detect_version() -> str:
  version = 'unknown'
  try:
    version = pkg_resources.get_distribution('amplipi').version()
  except:
    pass
  if 'unknown' in version:
    # assume the application is running in its base directory and check the pyproject.toml file to determine the version
    # this is needed for a straight github checkout (the common developement paradigm at MicroNova)
    TOML_VERSION_STR = re.compile(r'version\s*=\s*"(.*)"')
    script_folder = os.path.dirname(os.path.realpath(__file__))
    try:
      with open(os.path.join(script_folder, '..', 'pyproject.toml')) as f:
        for line in f.readlines():
          if 'version' in line:
            match = TOML_VERSION_STR.search(line)
            if match is not None:
              version = match.group(1)
    except:
      pass
  return version
