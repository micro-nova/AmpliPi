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

def vol_string(vol, min_vol=-80, max_vol=0):
  """ Make a visual representation of a volume """
  vol_range = max_vol - min_vol + 1
  vol_str_len = 20
  vol_scale = vol_range / vol_str_len
  vol_level = int((vol - min_vol)  / vol_scale)
  assert 0 <= vol_level < vol_str_len
  vol_str = ['-'] * vol_str_len
  vol_str[vol_level] = '|' # place the volume slider bar at its current spot
  return ''.join(vol_str) # turn that char array into a string

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
  enabled_zones = [zone for zone in status.zones if not zone.disabled]
  viz += 'zones:\n'
  zone_len = utils.max_len(enabled_zones, lambda zone: len(zone.name))
  for zone in enabled_zones:
    sid = zone.source_id
    src_type = utils.abbreviate_src(src_cfg[sid])
    muted = 'muted' if zone.mute else ''
    viz += f'  {sid}({src_type}) --> {zone.name:{zone_len}} vol [{vol_string(zone.vol)}] {muted}\n'
  # print group configuration
  viz += 'groups:\n'
  gzone_len = utils.max_len(status.groups, lambda group: len(utils.compact_str(group.zones)))
  gname_len = utils.max_len(status.groups, lambda group: len(group.name))
  for group in status.groups:
    if group.source_id:
      sid = group.source_id
      src = str(sid)
      src_type = utils.abbreviate_src(src_cfg[sid])
    else:
      src = ' '
      src_type = ' '
    muted = 'muted' if group.mute else ''
    vol = vol_string(group.vol_delta)
    zone_str = utils.compact_str(group.zones)
    viz += f'  {src}({src_type}) --> {group.name:{gname_len}} {zone_str:{gzone_len}} vol [{vol}] {muted}\n'
  return viz
