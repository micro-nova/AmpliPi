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

"""Control of the whole AmpliPi Audio System.

This module provides complete control of the AmpliPi Audio System's sources,
zones, groups and streams.
"""

import json
from copy import deepcopy
import deepdiff

import pprint
import os # files

import amplipi.rt as rt
import amplipi.streams as streams
import amplipi.utils as utils

_DEBUG_API = False # print out a graphical state of the api after each call

class Api:
  """ Amplipi Controller API"""

  _DEFAULT_CONFIG = { # This is the system state response that will come back from the amplipi box
    "sources": [ # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
      { "id": 0, "name": "1", "input": "local" },
      { "id": 1, "name": "2", "input": "local" },
      { "id": 2, "name": "3", "input": "local" },
      { "id": 3, "name": "4", "input": "local" }
    ],
    # NOTE: streams and groups seem like they should be stored as dictionaries with integer keys
    #       this does not make sense because JSON only allows string based keys
    "streams": [
      # an example for each type of stream
      { "id": 1000, "name": "My Airplay", "type": "shairport"},
      { "id": 1001, "name": "My Pandora", "type": "pandora", "user": "", "password": "", "station": ""},
      { "id": 1002, "name": "My Spotify", "type": "spotify"},
    ],
    "zones": [ # this is an array of zones, array length depends on # of boxes connected
      { "id": 0,  "name": "Zone 1",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
      { "id": 1,  "name": "Zone 2",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
      { "id": 2,  "name": "Zone 3",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
      { "id": 3,  "name": "Zone 4",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
      { "id": 4,  "name": "Zone 5",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
      { "id": 5,  "name": "Zone 6",  "source_id": 0, "mute": True, "disabled": False, "vol": -79 },
    ],
    # TODO: make groups a dictionary
    "groups": [ # this is an array of groups that have been created , each group has a friendly name and an array of member zones
      { "id": 100, "name": "Group 1", "zones": [0,1,2], "source_id": 0, "mute": True, "vol_delta": -79 },
      { "id": 101, "name": "Group 2", "zones": [2,3,4], "source_id": 0, "mute": True, "vol_delta": -79 },
      { "id": 102, "name": "Group 3", "zones": [5],     "source_id": 0, "mute": True, "vol_delta": -79 },
    ],
    "presets" : [
      { "id": 10000,
        # TODO: generate the mute all preset based on # of zones
        "name": "Mute All",
        "zones" : [
          { "id": 0, "mute": True },
          { "id": 1, "mute": True },
          { "id": 2, "mute": True },
          { "id": 3, "mute": True },
          { "id": 4, "mute": True },
          { "id": 5, "mute": True },
        ]
      }
    ]
  }

  def __init__(self, _rt=rt.Mock(), mock_streams=True, config_file='config/house.json'):
    self._rt = _rt
    self._mock_hw = type(_rt) is rt.Mock
    self._mock_streams = mock_streams
    """Intitializes the mock system to to base configuration """
    # test open the config file, this will throw an exception if there are issues writing to the file
    with open(config_file, 'a'): # use append more to make sure we have read and write permissions, but won't overrite the file
      pass
    self.config_file = config_file
    self.backup_config_file = config_file + '.bak'
    self.config_file_valid = True # initially we assume the config file is valid
    # try to load the config file or its backup
    config_paths = [self.config_file, self.backup_config_file]
    errors = []
    loaded_config = False
    for cfg_path in config_paths:
      try:
        if os.path.exists(cfg_path):
          with open(cfg_path, 'r') as cfg:
            self.status = json.load(cfg)
          loaded_config = True
          break
        else:
          errors.append('config file "{}" does not exist'.format(cfg_path))
      except Exception as e:
        self.config_file_valid = False # mark the config file as invalid so we don't try to back it up
        errors.append('error loading config file: {}'.format(e))

    if not loaded_config:
      print(errors[0])
      print('using default config')
      self.status = deepcopy(self._DEFAULT_CONFIG) # only make a copy of the default config so we can make changes to it
      self.save()
    # configure all streams into a known state
    self.streams = {}
    for stream in self.status['streams']:
      self.streams[stream['id']] = streams.build_stream(stream, self._mock_streams)
    # configure all sources so that they are in a known state
    for src in self.status['sources']:
      self.set_source(src['id'], input=src['input'], force_update=True)
    # configure all of the zones so that they are in a known state
    #   we mute all zones on startup to keep audio from playing immediately at startup
    for z in self.status['zones']:
      # TODO: disbale zones that are not found
      self.set_zone(z['id'], source_id=z['source_id'], mute=True, vol=z['vol'], force_update=True)
    # configure all of the groups (some fields may need to be updated)
    self._update_groups()

  def save(self):
    """ Saves the system state to json"""
    try:
      # save a backup copy of the config file (assuming its valid)
      if os.path.exists(self.config_file) and self.config_file_valid:
        if os.path.exists(self.backup_config_file):
          os.remove(self.backup_config_file)
        os.rename(self.config_file, self.backup_config_file)
      with open(self.config_file, 'w') as cfg:
        json.dump(self.status, cfg, indent=2)
      self.config_file_valid = True
    except Exception as e:
      print('Error saving config: {}'.format(e))

  def visualize_api(self, prev_status=None):
    """Creates a command line visualization of the system state, mostly the volume levels of each zone and group

    Returns:
      A string meant to visualize the system state in a minimal way.
    Example:
      Visualize the current state of the running amplipi

      >>> my_amplipi.visualize_api()
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
    src_cfg = [s['input'] for s in self.status['sources']]
    viz += '  [{}]\n'.format(', '.join(src_cfg))
    # visualize zone configuration
    enabled_zones = [z for z in self.status['zones'] if not z['disabled']]
    viz += 'zones:\n'
    zone_len = utils.max_len(enabled_zones, lambda z: len(z['name']))
    for z in enabled_zones:
      src = z['source_id']
      src_type = utils.abbreviate_src(src_cfg[src])
      muted = 'muted' if z['mute'] else ''
      zone_fmt = '  {}({}) --> {:' + str(zone_len) + '} vol [{}] {}\n'
      viz += zone_fmt.format(src, src_type, z['name'], utils.vol_string(z['vol']), muted)
    # print group configuration
    viz += 'groups:\n'
    enabled_groups = self.status['groups']
    gzone_len = utils.max_len(enabled_groups, lambda g: len(utils.compact_str(g['zones'])))
    gname_len = utils.max_len(enabled_groups, lambda g: len(g['name']))
    for g in enabled_groups:
      if g['source_id']:
        src = g['source_id']
        src_type = utils.abbreviate_src(src_cfg[src])
      else:
        src = ' '
        src_type = ' '
      muted = 'muted' if g['mute'] else ''
      vol = utils.vol_string(g['vol_delta'])
      group_fmt = '  {}({}) --> {:' + str(gname_len) + '} {:' + str(gzone_len) + '} vol [{}] {}\n'
      viz += group_fmt.format(src, src_type, g['name'], utils.compact_str(g['zones']), vol, muted)
    return viz

  @staticmethod
  def _is_digital(src_type):
    """Determines whether a source type, @src_type, is analog or digital

      'local' is the analog input, anything else is some sort of digital streaming source.
      The runtime only has the concept of digital or analog
    """
    return src_type != 'local'

  def get_inputs(self):
    """Gets a dictionary of the possible inputs for a source

      Returns:
        A dictionary of the input types and a corresponding user friendly name/string for each
      Example:
        Get the possible inputs for any source (only one stream)

        >>> my_amplipi.get_inputs()
        { None, '', 'local', 'Local', 'stream=9449' }
    """
    inputs = { None: '', 'local' : 'Local'}
    for s in self.get_state()['streams']:
      inputs['stream={}'.format(s['id'])] = s['name']
    return inputs

  def get_state(self):
    """ get the system state (dict) """
    # update the state with the latest stream info and status
    optional_fields = ['station', 'user', 'password'] # optional configuration fields
    streams = []
    for sid, sc in self.streams.items():
      # TODO: this functionality should be in the unimplemented streams base class
      # convert the stream class info to a dict (serialize its current configuration and status information)
      s = {}
      s['id'] = sid
      s['name'] = sc.name
      s['type'] = type(sc).__name__.lower()
      s['info'] = sc.info()
      s['status'] = sc.status()
      for f in optional_fields:
        if f in sc.__dict__:
          s[f] = sc.__dict__[f]
      streams.append(s)
    self.status['streams'] = streams
    return self.status

  def _get_stream(self, input):
    """Gets the stream from an input configuration

    Args:
      input: input configuration either ['local', 'stream=ID']
    Returns
      a stream, or None if input does not specify a valid stream
    """
    if 'stream=' in input:
      stream_id = int(input.split('=')[1])
      return self.streams[stream_id]
    else:
      return None

  @utils.save_on_success
  def set_source(self, id, name=None, input=None, force_update=False):
    """Modifes the configuration of one of the 4 system sources

      Args:
        id (int): source id [0,3]
        name (str): user friendly source name, ie. "cd player" or "stream 1"
        input: method of audio input ('local', 'stream=ID')
        force_update: bool, update source even if no changes have been made (for hw startup)

      Returns:
        'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['sources']):
      if s['id'] == id:
        idx = i
    if idx is not None:
      try:
        src = self.status['sources'][idx]
        name, _ = utils.updated_val(name, src['name'])
        input, input_updated = utils.updated_val(input, src['input'])
      except Exception as e:
        return utils.error('failed to set source, error getting current state: {}'.format(e))
      try:
        # update the name
        src['name'] = str(name)
        if input_updated or force_update:
          # shutdown old stream
          old_stream = self._get_stream(src['input'])
          if old_stream:
            old_stream.disconnect()
          # start new stream
          stream = self._get_stream(input)
          if stream:
            # update the streams last connected source to have no input, since we have stolen its input
            if stream.src is not None and stream.src != idx:
              other_src = self.status['sources'][stream.src]
              print('stealing {} from source {}'.format(stream.name, other_src['name']))
              other_src['input'] = ''
            else:
              print('stream.src={} idx={}'.format(stream.src, idx))
            stream.disconnect()
            stream.connect(idx)
          rt_needs_update = self._is_digital(input) != self._is_digital(src['input'])
          if rt_needs_update or force_update:
            # get the current underlying type of each of the sources, for configuration of the runtime
            src_cfg = [ self._is_digital(self.status['sources'][s]['input']) for s in range(4) ]
            # update this source
            src_cfg[idx] = self._is_digital(input)
            if self._rt.update_sources(src_cfg):
              # update the status
              src['input'] = input
              return None
            else:
              return utils.error('failed to set source')
          else:
            src['input'] = input
      except Exception as e:
        return utils.error('failed to set source: ' + str(e))
    else:
      return utils.error('failed to set source: index {} out of bounds'.format(idx))

  @utils.save_on_success
  def set_zone(self, id, name=None, source_id=None, mute=None, vol=None, disabled=None, force_update=False):
    """Configures a zone

      Args:
        id (int): any valid zone [0,p*6-1] (6 zones per preamp)
        name(str): friendly name for the zone, ie "bathroom" or "kitchen 1"
        source_id (int): source to connect to [0,4]
        mute (bool): mute the zone regardless of set volume
        vol (int): attenuation [-79,0] 0 is max volume, -79 is min volume
        disabled (bool): disable zone, for when the zone is not connected to any speakers and not in use
        force_update: bool, update source even if no changes have been made (for hw startup)
      Returns:
        'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['zones']):
      if s['id'] == int(id):
        idx = i
    if idx is not None:
      try:
        z = self.status['zones'][idx]
        # TODO: use updated? value
        name, _ = utils.updated_val(name, z['name'])
        source_id, update_source_id = utils.updated_val(source_id, z['source_id'])
        mute, update_mutes = utils.updated_val(mute, z['mute'])
        vol, update_vol = utils.updated_val(vol, z['vol'])
        disabled, _ = utils.updated_val(disabled, z['disabled'])
      except Exception as e:
        return utils.error('failed to set zone, error getting current state: {}'.format(e))
      try:
        sid = utils.parse_int(source_id, [0, 1, 2, 3, 4])
        vol = utils.parse_int(vol, range(-79, 79)) # hold additional state for group delta volume adjustments, output volume will be saturated to 0dB
        zones = self.status['zones']
        # update non hw state
        z['name'] = name
        z['disabled'] = disabled
        # TODO: figure out an order of operations here, like does mute need to be done before changing sources?
        if update_source_id or force_update:
          zone_sources = [ zone['source_id'] for zone in zones ]
          zone_sources[idx] = sid
          if self._rt.update_zone_sources(idx, zone_sources):
            z['source_id'] = sid
          else:
            return utils.error('set zone failed: unable to update zone source')
        if update_mutes or force_update:
          mutes = [ zone['mute'] for zone in zones ]
          mutes[idx] = mute
          if self._rt.update_zone_mutes(idx, mutes):
            z['mute'] = mute
          else:
            return utils.error('set zone failed: unable to update zone mute')
        if update_vol or force_update:
          real_vol = utils.clamp(vol, -79, 0)
          if self._rt.update_zone_vol(idx, real_vol):
            z['vol'] = vol
          else:
            return utils.error('set zone failed: unable to update zone volume')

        # update the group stats (individual zone volumes, sources, and mute configuration can effect a group)
        self._update_groups()

        return None
      except Exception as e:
        return utils.error('set zone: '  + str(e))
    else:
        return utils.error('set zone: index {} out of bounds'.format(idx))

  def _update_groups(self):
    """Updates the group's aggregate fields to maintain consistency and simplify app interface"""
    for g in self.status['groups']:
      zones = [ self.status['zones'][z] for z in g['zones'] ]
      mutes = [ z['mute'] for z in zones ]
      sources  = set([ z['source_id'] for z in zones ])
      vols = [ z['vol'] for z in zones ]
      vols.sort()
      g['mute'] = False not in mutes # group is only considered muted if all zones are muted
      if len(sources) == 1:
        g['source_id'] = sources.pop() # TODO: how should we handle different sources in the group?
      else: # multiple sources
        g['source_id'] = None
      g['vol_delta'] = (vols[0] + vols[-1]) // 2 # group volume is the midpoint between the highest and lowest source

  @utils.save_on_success
  def set_group(self, id, name=None, source_id=None, zones=None, mute=None, vol_delta=None):
    """Configures an existing group
        parameters will be used to configure each sone in the group's zones
        all parameters besides the group id, @id, are optional

        Args:
          id: group id (a guid)
          name: group name
          source_id: group source
          zones: zones that belong to the group
          mute: group mute setting (muted=True)
          vol_delta: volume adjustment to apply to each zone [-79,79]
        Returns:
            'None' on success, otherwise error (dict)
    """
    _, g = utils.find(self.status['groups'], id)
    if g is None:
      return utils.error('set group failed, group {} not found'.format(id))
    if type(zones) is str:
      try:
        zones = eval(zones)
      except Exception as e:
        return utils.error('failed to configure group, error parsing zones: {}'.format(e))
    try:
      name, _ = utils.updated_val(name, g['name'])
      zones, _ = utils.updated_val(zones, g['zones'])
      vol_delta, vol_updated = utils.updated_val(vol_delta, g['vol_delta'])
      if vol_updated:
        vol_change = vol_delta - g['vol_delta']
      else:
        vol_change = 0
    except Exception as e:
      return utils.error('failed to configure group, error getting current state: {}'.format(e))

    g['name'] = name
    g['zones'] = zones

    for z in [ self.status['zones'][zone] for zone in zones ]:
      if vol_change != 0:
        # TODO: make this use volume delta adjustment, for now its a fixed group volume
        vol = vol_delta # vol = z['vol'] + vol_change
      else:
        vol = None
      self.set_zone(z['id'], None, source_id, mute, vol)
    g['vol_delta'] = vol_delta

    # update the group stats
    self._update_groups()

  def _new_group_id(self):
    """ get next available group id """
    g = max(self.status['groups'], key=lambda g: g['id'])
    if g is not None:
      return g['id'] + 1
    else:
      return 100

  @utils.save_on_success
  def create_group(self, name, zones):
    """Creates a new group with a list of zones

    Refer to the returned system state to obtain the id for the newly created group
    """
    # verify new group's name is unique
    names = [ g['name'] for g in self.status['groups'] ]
    if name in names:
      return utils.error('create group failed: {} already exists'.format(name))

    if type(zones) is str:
      try:
        zones = eval(zones)
      except Exception as e:
        return utils.error('failed to configure group, error parsing zones: {}'.format(e))

    # get the new groug's id
    id = self._new_group_id()

    # add the new group
    group = { 'id': id, 'name' : name, 'zones' : zones, 'vol_delta' : 0 }
    self.status['groups'].append(group)

    # update the group stats and populate uninitialized fields of the group
    self._update_groups()

    return group

  @utils.save_on_success
  def delete_group(self, id):
    """Deletes an existing group"""
    try:
      i, _ = utils.find(self.status['groups'], id)
      if i is not None:
        del self.status['groups'][i]
    except KeyError:
      return utils.error('delete group failed: {} does not exist'.format(id))

  def _new_stream_id(self):
    s = max(self.status['streams'], key=lambda s: s['id'])
    if s is not None:
      return s['id'] + 1
    else:
      return 1000

  @utils.save_on_success
  def create_stream(self, **kwargs):
    try:
      # Make a new stream and add it to streams
      s = streams.build_stream(args=kwargs, mock=self._mock_streams)
      id = self._new_stream_id()
      self.streams[id] = s
      # Get the stream as a dictionary (we use get_state() to convert it from its stream type into a dict)
      for s in self.get_state()['streams']:
        if s['id'] == id:
          return s
      return utils.error('create stream failed: no stream created')
    except Exception as e:
      return utils.error('create stream failed: {}'.format(e))

  @utils.save_on_success
  def set_stream(self, id, **kwargs):
    if int(id) not in self.streams:
      return utils.error('Stream id {} does not exist'.format(id))

    try:
      stream = self.streams[int(id)]
    except Exception as e:
      return utils.error('Unable to get stream {}: {}'.format(id, e))

    try:
      stream.reconfig(**kwargs)
    except Exception as e:
      return utils.error('Unable to reconfigure stream {}: {}'.format(id, e))

  @utils.save_on_success
  def delete_stream(self, id):
    """Deletes an existing stream"""
    try:
      del self.streams[id]
      i, _ = utils.find(self.status['streams'], id)
      if i is not None:
        del self.status['streams'][i] # delete the cached stream state just in case
    except KeyError:
      return utils.error('delete stream failed: {} does not exist'.format(id))

  @utils.save_on_success
  def exec_stream_command(self, id, cmd):
    """Sets play/pause on a specific pandora source """
    # TODO: this needs to be handled inside the stream itself, each stream can have a set of commands available
    if int(id) not in self.streams:
      return utils.error('Stream id {} does not exist'.format(id))

    try:
      stream = self.streams[int(id)]
    except Exception as e:
      return utils.error('Unable to get stream {}: {}'.format(id, e))

    try:
      if cmd is None:
        pass
      elif cmd == 'play':
        print('playing')
        stream.state = 'playing'
        stream.ctrl.play()
      elif cmd == 'pause':
        print('paused')
        stream.state = 'paused'
        stream.ctrl.pause()
      elif cmd == 'stop':
        stream.state = "stopped"
        stream.ctrl.stop()
      elif cmd == 'next':
        print('next')
        stream.ctrl.next()
      elif cmd == 'love':
        stream.ctrl.love()
      elif cmd == 'ban':
        stream.ctrl.ban()
      elif cmd == 'shelve':
        stream.ctrl.shelve()
      elif 'station' in cmd:
        station_id = int(cmd.replace('station=',''))
        if station_id is not None:
          stream.ctrl.station(station_id)
        else:
          return utils.error('station=<int> expected where <int> is a valid integer, ie. station=23432423, received "{}"'.format(cmd))
      else:
        return utils.error('Command "{}" not recognized.'.format(cmd))
    except Exception as e:
      return utils.error('Failed to execute stream command: {}: {}'.format(cmd, e))

  @utils.save_on_success
  def get_stations(self, id, stream_index=None):
    """Gets a pandora stream's station list"""
    # TODO: this should be moved to be a command of the Pandora stream interface
    if id not in self.streams:
      return utils.error('Stream id {} does not exist!'.format(id))
    # TODO: move the rest of this into streams
    if stream_index is not None:
      root = '/home/pi/config/srcs/{}/'.format(stream_index)
    else:
      root = '/home/pi/'
    stat_dir = root + '.config/pianobar/stationList'

    try:
      with open(stat_dir, 'r') as file:
        d= {}
        for line in file.readlines():
          line = line.strip()
          if line:
            data = line.split(':')
            d[data[0]] = data[1]
        return(d)
    except Exception as e:
      # TODO: throw useful exceptions to next level
      pass
      #print(utils.error('Failed to get station list - it may not exist: {}'.format(e)))
    # TODO: Change these prints to returns in final state

  def _new_preset_id(self):
    """ get next available preset id """
    g = max(self.status['presets'], key=lambda g: g['id'])
    if g is not None:
      return g['id'] + 1
    else:
      return 10000

  @utils.save_on_success
  def create_preset(self, preset):
    try:
      # Make a new preset and add it to presets
      # TODO: validate preset
      id = self._new_preset_id()
      preset['id'] = id
      self.status['presets'][id] = preset
      return utils.error('create preset failed: no preset created')
    except Exception as e:
      return utils.error('create preset failed: {}'.format(e))

  @utils.save_on_success
  def set_preset(self, id, preset):
    i, old_preset = utils.find(self.status['presets'], id)

    if i is None:
      return utils.error('Unable to find preset to redefine')

    try:
      # TODO: validate preset
      preset['id'] = i
      self.status['presets'][i] = preset
    except Exception as e:
      return utils.error('Unable to reconfigure preset {}: {}'.format(id, e))

  @utils.save_on_success
  def delete_preset(self, id):
    """Deletes an existing preset"""
    try:
      i, _ = utils.find(self.status['presets'], id)
      if i is not None:
        del self.status['presets'][i] # delete the cached preset state just in case
    except KeyError:
      return utils.error('delete preset failed: {} does not exist'.format(id))

  @utils.save_on_success
  def load_preset(self, id, cmd):
    """
    To avoid any issues with audio coming out of the wrong speakers, we will need to carefully load a preset configuration. Below is an idea of how a preset configuration could be loaded to avoid any weirdness. We are also considering adding a "Last config" preset that allows us to easily revert the configuration changes.

    1. Grab system modification mutex to avoid accidental changes (requests during this time return some error)
    1. Save current configuration as "Last config" preset
    1. Mute any effected zones
    1. Execute any stream changes (configuration then commands)
    1. Execute changes source by source in increasing order
    1. Execute change zone by zone in increasing order
    1. Execute changes group by group in increasing order
    1. Unmute effected zones that were not muted
    1. Force web client refresh to fixup website
    1. Release system mutex, future requests are successful after this
    """
    # TODO: implement preset load
    pass
