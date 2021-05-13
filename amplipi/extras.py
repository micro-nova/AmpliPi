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

"""AmpliPi Extras

Additional AmpliPi methods
"""

from amplipi import models
from amplipi import utils

def _vol_string(vol, min_vol=-79, max_vol=0):
  """ Make a visual representation of a volume """
  VOL_RANGE = max_vol - min_vol + 1
  VOL_STR_LEN = 20
  VOL_SCALE = VOL_RANGE / VOL_STR_LEN
  vol_level = int((vol - min_vol)  / VOL_SCALE)
  assert vol_level >= 0 and vol_level < VOL_STR_LEN
  vol_string = ['-'] * VOL_STR_LEN
  vol_string[vol_level] = '|' # place the volume slider bar at its current spot
  return ''.join(vol_string) # turn that char array into a string

def visualize_api(status : models.Status):
  """Creates a command line visualization of the system state, mostly the volume levels of each zone and group

  Returns:
    A string meant to visualize the system state in a minimal way.
  Example:
    Visualize the current state of the running amplipi

    >>> extras.visualize_api(ctrl.get_status())
    sources:
      [stream=90891, stream=44590, local, local]
    zones:
      0(S) --> Local           vol [---|----------------]
      0(S) --> Office          vol [-------|------------]
      0(S) --> Laundry Room    vol [--------|-----------]
      0(S) --> Dining Room     vol [--------|-----------] muted
      0(S) --> Guest Bedroom   vol [----|---------------] muted
      0(S) --> Main Bedroom    vol [---|----------------] muted
      0(S) --> Main Bathroom   vol [--------|-----------] muted
      0(S) --> Master Bathroom vol [---------|----------] muted
      0(S) --> Kitchen High    vol [------|-------------] muted
      0(S) --> kitchen Low     vol [------|-------------] muted
      0(S) --> Living Room     vol [--------|-----------] muted
    groups:
      ( ) --> Whole House    [0,1,2,3,5,6,7,8,9,10,11] vol [------|-------------]
      ( ) --> KitchLivDining [3,9,10,11]               vol [-------|------------] muted
  """
  viz = ''
  # visualize source configuration
  viz += 'sources:\n'
  src_cfg = [s.input for s in status.sources]
  viz += f"  [{', '.join(src_cfg)}]\n"
  # visualize zone configuration
  enabled_zones = [z for z in status.zones if not z.disabled]
  viz += 'zones:\n'
  zone_len = utils.max_len(enabled_zones, lambda z: len(z.name))
  for z in enabled_zones:
    src = z.source_id
    src_type = utils.abbreviate_src(src_cfg[src])
    muted = 'muted' if z.mute else ''
    viz += f'  {src}({src_type}) --> {z.name:{zone_len}} vol [{_vol_string(z.vol)}] {muted}\n'
  # print group configuration
  viz += 'groups:\n'
  enabled_groups = status.groups
  gzone_len = utils.max_len(enabled_groups, lambda g: len(utils.compact_str(g.zones)))
  gname_len = utils.max_len(enabled_groups, lambda g: len(g.name))
  for g in enabled_groups:
    if g.source_id:
      src = g.source_id
      src_type = utils.abbreviate_src(src_cfg[src])
    else:
      src = ' '
      src_type = ' '
    muted = 'muted' if g.mute else ''
    vol = _vol_string(g.vol_delta)
    zone_str = utils.compact_str(g.zones)
    viz += f'  {src}({src_type}) --> {g.name:{gname_len}} {zone_str:{gzone_len}} vol [{vol}] {muted}\n'
  return viz

