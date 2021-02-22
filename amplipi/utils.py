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
import functools

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

def updated_val(update, val):
  """ get the potentially updated value, @update, defaulting to the current value, @val, if it is None """
  if update is None:
    return val, False
  else:
    return update, update != val

def find(items, id, key='id'):
  return next(filter(lambda ie: ie[1][key] == id, enumerate(items)), (None, None))

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

def vol_string(vol, min_vol=-79, max_vol=0):
  """ Make a visual representation of a volume """
  VOL_RANGE = max_vol - min_vol + 1
  VOL_STR_LEN = 20
  VOL_SCALE = VOL_RANGE / VOL_STR_LEN
  vol_level = int((vol - min_vol)  / VOL_SCALE)
  assert vol_level >= 0 and vol_level < VOL_STR_LEN
  vol_string = ['-'] * VOL_STR_LEN
  vol_string[vol_level] = '|' # place the volume slider bar at its current spot
  return ''.join(vol_string) # turn that char array into a string

def output_device(src):
  return 'ch' + str(src)

def save_on_success(func):
  """ A decorator that calls a class object's save method when successful
        (in the case of our API None=Success)
  """
  @functools.wraps(func) # transfer func's documentation to decorated function to assist documentation generation
  def inner(self, *args, **kwargs):
    result = func(self, *args, **kwargs)
    if result is None:
      self.save()
    return result
  return inner
