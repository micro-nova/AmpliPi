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

from typing import List, Dict, Set, Union, Optional, Callable

from enum import Enum

from copy import deepcopy
import os # files
import time

import threading
import wrapt

import amplipi.models as models
import amplipi.rt as rt
import amplipi.streams
import amplipi.utils as utils

_DEBUG_API = False # print out a graphical state of the api after each call

@wrapt.decorator
def save_on_success(wrapped, instance: 'Api', args, kwargs):
  """ Check if a ctrl API call is successful and saves the state if so """
  result = wrapped(*args, **kwargs)
  if result is None:
    # call mark_changes instead of save to reduce the load/delay of a series of requests
    instance.mark_changes()
  return result

class ApiCode(Enum):
  """ Ctrl Api Response code """
  OK = 1
  ERROR = 2

class ApiResponse:
  """ Ctrl Api Response object """
  def __init__(self, code: ApiCode, msg: str = ''):
    self.code = code
    self.msg = msg

  def __str__(self):
    if self.code == ApiCode.OK:
      return 'OK'
    return f'ERROR: {self.msg}'

  @staticmethod
  def error(msg: str):
    """ create an error response """
    return ApiResponse(ApiCode.ERROR, msg)

  @staticmethod
  def ok():
    """ create a successful response """
    return ApiResponse(ApiCode.OK)

  OK = ApiCode.OK
  ERROR = ApiCode.ERROR

class Api:
  """ Amplipi Controller API"""
  # pylint: disable=too-many-instance-attributes
  # pylint: disable=too-many-public-methods

  _mock_hw: bool
  _mock_streams: bool
  _save_timer: Optional[threading.Timer] = None
  _delay_saves: bool
  _change_notifier: Optional[Callable[[models.Status], None]] = None
  _rt: Union[rt.Rpi, rt.Mock]
  config_file: str
  backup_config_file: str
  config_file_valid: bool
  status: models.Status
  streams: Dict[int, amplipi.streams.AnyStream]

  _LAST_PRESET_ID = 9999
  DEFAULT_CONFIG = { # This is the system state response that will come back from the amplipi box
    "sources": [ # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
      {"id": 0, "name": "1", "input": "local"},
      {"id": 1, "name": "2", "input": "local"},
      {"id": 2, "name": "3", "input": "local"},
      {"id": 3, "name": "4", "input": "local"}
    ],
    # NOTE: streams and groups seem like they should be stored as dictionaries with integer keys
    #       this does not make sense because JSON only allows string based keys
    "streams": [
      # an example for each type of stream
      {"id": 1000, "name": "AmpliPi", "type": "shairport"},
      {"id": 1001, "name": "Radio Station, needs user/pass/station-id", "type": "pandora", "user": "change@me.com", "password": "CHANGEME", "station": "CHANGEME"},
      {"id": 1002, "name": "AmpliPi", "type": "spotify"},
      {"id": 1003, "name": "Beatles Radio", "type": "internetradio", "url": "http://www.beatlesradio.com:8000/stream/1/", "logo": "http://www.beatlesradio.com/content/images/thumbs/0000587.gif"},
      {"id": 1004, "name": "AmpliPi", "type": "dlna"}
    ],
    "zones": [ # this is an array of zones, array length depends on # of boxes connected
      {"id": 0, "name": "Zone 1", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
      {"id": 1, "name": "Zone 2", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
      {"id": 2, "name": "Zone 3", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
      {"id": 3, "name": "Zone 4", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
      {"id": 4, "name": "Zone 5", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
      {"id": 5, "name": "Zone 6", "source_id": 0, "mute": True, "disabled": False, "vol": -79},
    ],
    # TODO: make groups a dictionary
    "groups": [ # this is an array of groups that have been created , each group has a friendly name and an array of member zones
      {"id": 100, "name": "Group 1", "zones": [1, 2], "source_id": 0, "mute": True, "vol_delta": -79},
      {"id": 101, "name": "Group 2", "zones": [3, 4], "source_id": 0, "mute": True, "vol_delta": -79},
      {"id": 102, "name": "Group 3", "zones": [5], "source_id": 0, "mute": True, "vol_delta": -79},
    ],
    "presets" : [
      {"id": 10000,
        # TODO: generate the mute all preset based on # of zones
        "name": "Mute All",
        "state" : {
          "zones" : [
            {"id": 0, "mute": True},
            {"id": 1, "mute": True},
            {"id": 2, "mute": True},
            {"id": 3, "mute": True},
            {"id": 4, "mute": True},
            {"id": 5, "mute": True},
          ]
        }
      },
      # We need this for testing
      {"id": 10001,
        "name": "Play Pandora",
        "state" : {
          "sources" : [
            {"id": 1, "input": "stream=1001"},
          ],
          "groups" : [
            {"id": 100, "source_id": 1},
            {"id": 101, "source_id": 1},
          ]
        }
      }
    ]
  }
  # TODO: migrate to init setting instance vars to a disconnected state (API requests will throw Api.DisconnectedException() in this state
  # with this reinit will be called connect and will attempt to load the configutation and connect to an AmpliPi (mocked or real)
  # returning a boolean on whether or not it was successful
  def __init__(self, settings: models.AppSettings = models.AppSettings(), change_notifier: Optional[Callable[[models.Status], None]] = None):
    self.reinit(settings, change_notifier)

  def reinit(self, settings: models.AppSettings = models.AppSettings(), change_notifier: Optional[Callable[[models.Status], None]] = None):
    """ Initialize or Reinitialize the controller

    Intitializes the system to to base configuration """
    self._change_notifier = change_notifier
    self._mock_hw = settings.mock_ctrl
    self._mock_streams = settings.mock_streams
    self._save_timer = None
    self._delay_saves = settings.delay_saves
    self._rt = rt.Mock() if settings.mock_ctrl else rt.Rpi()
    # test open the config file, this will throw an exception if there are issues writing to the file
    with open(settings.config_file, 'a'): # use append more to make sure we have read and write permissions, but won't overrite the file
      pass
    self.config_file = settings.config_file
    self.backup_config_file = settings.config_file + '.bak'
    self.config_file_valid = True # initially we assume the config file is valid
    # try to load the config file or its backup
    config_paths = [self.config_file, self.backup_config_file]
    errors = []
    loaded_config = False
    for cfg_path in config_paths:
      try:
        if os.path.exists(cfg_path):
          self.status = models.Status.parse_file(cfg_path)
          loaded_config = True
          break
        errors.append('config file "{}" does not exist'.format(cfg_path))
      except Exception as exc:
        self.config_file_valid = False # mark the config file as invalid so we don't try to back it up
        errors.append('error loading config file: {}'.format(exc))

    if not loaded_config:
      print(errors[0])
      print('using default config')
      self.status = models.Status.parse_obj(self.DEFAULT_CONFIG)
      self.save()

    self.status.info = models.Info(
      mock_ctrl=self._mock_hw,
      mock_streams=self._mock_streams,
      config_file=self.config_file,
      version=utils.detect_version()
    )

    # configure all streams into a known state
    self.streams: Dict[int, amplipi.streams.AnyStream] = {}
    for stream in self.status.streams:
      if stream.id:
        self.streams[stream.id] = amplipi.streams.build_stream(stream, self._mock_streams)
    # configure all sources so that they are in a known state
    for src in self.status.sources:
      if src.id is not None:
        update = models.SourceUpdate(input=src.input)
        self.set_source(src.id, update, force_update=True, internal=True)
    # configure all of the zones so that they are in a known state
    #   we mute all zones on startup to keep audio from playing immediately at startup
    for zone in self.status.zones:
      # TODO: disable zones that are not found and add zones that are found
      zone_update = models.ZoneUpdate(source_id=zone.source_id, mute=True, vol=zone.vol)
      self.set_zone(zone.id, zone_update, force_update=True, internal=True)
    # configure all of the groups (some fields may need to be updated)
    self._update_groups()

  def __del__(self):
    # stop save in the future so we can save right away
    if self._save_timer:
      self._save_timer.cancel()
      self._save_timer = None
    self.save()

  def save(self) -> None:
    """ Saves the system state to json"""
    try:
      # save a backup copy of the config file (assuming its valid)
      if os.path.exists(self.config_file) and self.config_file_valid:
        if os.path.exists(self.backup_config_file):
          os.remove(self.backup_config_file)
        os.rename(self.config_file, self.backup_config_file)
      with open(self.config_file, 'w') as cfg:
        cfg.write(self.status.json(exclude_none=True, indent=2))
      self.config_file_valid = True
    except Exception as exc:
      print('Error saving config: {}'.format(exc))

  def mark_changes(self):
    """ Mark api changes to update listeners and save the system state in the future

    This attempts to avoid excessive saving and the resulting delays by only saving a small delay after the last change
    """
    if self._change_notifier:
      self._change_notifier(self.get_state())
    if self._delay_saves:
      if self._save_timer:
        self._save_timer.cancel()
        self._save_timer = None
      # start can only be called once on a thread
      self._save_timer = threading.Timer(5.0, self.save)
      self._save_timer.start()
    else:
      self.save()

  @staticmethod
  def _is_digital(src_type: str) -> bool:
    """Determines whether a source type, @src_type, is analog or digital

      'local' is the analog input, anything else is some sort of digital streaming source.
      The runtime only has the concept of digital or analog
    """
    return src_type != 'local'

  def get_inputs(self) -> Dict[Union[str, None], str]:
    """Gets a dictionary of the possible inputs for a source

      Returns:
        A dictionary of the input types and a corresponding user friendly name/string for each
      Example:
        Get the possible inputs for any source (only one stream)

        >>> my_amplipi.get_inputs()
        { None, '', 'local', 'Local', 'stream=9449' }
    """
    inputs = {None: '', 'local' : 'Local - RCA'}
    for stream in self.get_state().streams:
      inputs['stream={}'.format(stream.id)] = f'{stream.name} - {stream.type}'
    return inputs

  def get_state(self) -> models.Status:
    """ get the system state """
    # update the state with the latest stream info
    # TODO: figure out how to cache stream info
    optional_fields = ['station', 'user', 'password', 'url', 'logo', 'token', 'client_id'] # optional configuration fields
    streams = []
    for sid, stream_inst in self.streams.items():
      # TODO: this functionality should be in the unimplemented streams base class
      # convert the stream instance info to stream data (serialize its current configuration
      st_type = type(stream_inst).__name__.lower()
      stream = models.Stream(id=sid, name=stream_inst.name, type=st_type)
      for field in optional_fields:
        if field in stream_inst.__dict__:
          stream.__dict__[field] = stream_inst.__dict__[field]
      streams.append(stream)
    self.status.streams = streams
    # update source's info
    # TODO: stream/source info should be updated in a background thread
    for src in self.status.sources:
      stream_inst2 = self.get_stream(src)
      if stream_inst2 is not None:
        src.info = stream_inst2.info()
      elif src.input is None or src.input == '':
        src.info = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/disconnected.png")
      elif src.input == 'local' and src.id is not None:
        # RCA
        src.info = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/rca_inputs.svg", track=f'Input {src.id + 1}')
      else:
        src.info = models.SourceInfo()
    return self.status

  def get_items(self, tag: str) -> Optional[List[models.Base]]:
    """ Gets one of the lists of elements contained in status named by @t (or t's plural

    This makes it easy to programmatically access zones using t='zones' or groups using t='groups'.
    We use this to generate some documentation.
    """
    item_lists = ['streams', 'presets', 'sources', 'zones', 'groups']
    plural_tag = tag + 's'
    items = []
    if tag in item_lists:
      items = self.get_state().__dict__[tag]
    elif plural_tag in item_lists:
      items = self.get_state().__dict__[plural_tag]
    return items

  def get_stream(self, src: models.Source = None, sid: int = None) -> Optional[amplipi.streams.AnyStream]:
    """Gets the stream from a source

    Args:
      src: An audio source that may have a stream connected
      sid: ID of an audio source
    Returns
      a stream, or None if input does not specify a valid stream
    """
    if sid is not None:
      _, src = utils.find(self.status.sources, sid)
    if src is None:
      return None
    idx = src.get_stream()
    if idx is not None:
      return self.streams.get(idx, None)
    return None

  def set_source(self, sid: int, update: models.SourceUpdate, force_update: bool = False, internal: bool = False) -> ApiResponse:
    """Modifes the configuration of one of the 4 system sources

      Args:
        id (int): source id [0,3]
        update: changes to source
        force_update: bool, update source even if no changes have been made (for hw startup)
        internal: called by a higher-level ctrl function:

      Returns:
        'None' on success, otherwise error (dict)
    """
    idx, src = utils.find(self.status.sources, sid)
    if idx is not None and src is not None:
      name, _ = utils.updated_val(update.name, src.name)
      input_, input_updated = utils.updated_val(update.input, src.input)
      try:
        # update the name
        src.name = str(name)
        if input_updated or force_update:
          # shutdown old stream
          old_stream = self.get_stream(src)
          if old_stream:
            old_stream.disconnect()
          # start new stream
          last_input = src.input
          src.input = input_ # reconfigure the input so get_stream knows which stream to get
          stream = self.get_stream(src)
          if stream:
            # update the streams last connected source to have no input, since we have stolen its input
            if stream.src is not None and stream.src != idx:
              other_src = self.status.sources[stream.src]
              print('stealing {} from source {}'.format(stream.name, other_src.name))
              other_src.input = ''
            stream.disconnect()
            stream.connect(idx)
          rt_needs_update = self._is_digital(input_) != self._is_digital(last_input)
          if rt_needs_update or force_update:
            # get the current underlying type of each of the sources, for configuration of the runtime
            src_cfg = [self._is_digital(self.status.sources[s].input) for s in range(4)]
            # update this source
            src_cfg[idx] = self._is_digital(input_)
            if not self._rt.update_sources(src_cfg):
              return ApiResponse.error('failed to set source')
        if not internal:
          self.mark_changes()
        return ApiResponse.ok()
      except Exception as exc:
        return ApiResponse.error('failed to set source: ' + str(exc))
    else:
      return ApiResponse.error('failed to set source: index {} out of bounds'.format(idx))

  def set_zone(self, zid, update: models.ZoneUpdate, force_update: bool = False, internal: bool = False) -> ApiResponse:
    """Reconfigures a zone

      Args:
        id: any valid zone [0,p*6-1] (6 zones per preamp)
        update: changes to zone
        force_update: update source even if no changes have been made (for hw startup)
        internal: called by a higher-level ctrl function
      Returns:
        'None' on success, otherwise error (dict)
    """
    idx, zone = utils.find(self.status.zones, zid)
    if idx is not None and zone is not None:
      name, _ = utils.updated_val(update.name, zone.name)
      source_id, update_source_id = utils.updated_val(update.source_id, zone.source_id)
      mute, update_mutes = utils.updated_val(update.mute, zone.mute)
      vol, update_vol = utils.updated_val(update.vol, zone.vol)
      disabled, _ = utils.updated_val(update.disabled, zone.disabled)
      try:
        sid = utils.parse_int(source_id, [0, 1, 2, 3])
        vol = utils.parse_int(vol, range(-79, 79)) # hold additional state for group delta volume adjustments, output volume will be saturated to 0dB
        zones = self.status.zones
        # update non hw state
        zone.name = name
        zone.disabled = disabled
        # TODO: figure out an order of operations here, like does mute need to be done before changing sources?
        if update_source_id or force_update:
          zone_sources = [zone.source_id for zone in zones]
          zone_sources[idx] = sid
          if self._rt.update_zone_sources(idx, zone_sources):
            zone.source_id = sid
          else:
            return ApiResponse.error('set zone failed: unable to update zone source')
        if update_mutes or force_update:
          mutes = [zone.mute for zone in zones]
          mutes[idx] = mute
          if self._rt.update_zone_mutes(idx, mutes):
            zone.mute = mute
          else:
            return ApiResponse.error('set zone failed: unable to update zone mute')
        if update_vol or force_update:
          real_vol = utils.clamp(vol, -79, 0)
          if self._rt.update_zone_vol(idx, real_vol):
            zone.vol = vol
          else:
            return ApiResponse.error('set zone failed: unable to update zone volume')

        if not internal:
          # update the group stats (individual zone volumes, sources, and mute configuration can effect a group)
          self._update_groups()
          self.mark_changes()

        return ApiResponse.ok()
      except Exception as exc:
        return ApiResponse.error('set zone: '  + str(exc))
    else:
        return ApiResponse.error('set zone: index {} out of bounds'.format(idx))

  def _update_groups(self) -> None:
    """Updates the group's aggregate fields to maintain consistency and simplify app interface"""
    for group in self.status.groups:
      zones = [self.status.zones[z] for z in group.zones]
      mutes = [z.mute for z in zones]
      sources = {z.source_id for z in zones}
      vols = [z.vol for z in zones]
      vols.sort()
      group.mute = False not in mutes # group is only considered muted if all zones are muted
      if len(sources) == 1:
        group.source_id = sources.pop() # TODO: how should we handle different sources in the group?
      else: # multiple sources
        group.source_id = None
      group.vol_delta = (vols[0] + vols[-1]) // 2 # group volume is the midpoint between the highest and lowest source

  def set_group(self, gid, update: models.GroupUpdate, internal: bool = False) -> ApiResponse:
    """Configures an existing group
        parameters will be used to configure each sone in the group's zones
        all parameters besides the group id, @id, are optional

        Args:
          gid: group id (a guid)
          update: changes to group
          internal: called by a higher-level ctrl function
        Returns:
          'None' on success, otherwise error (dict)
    """
    _, group = utils.find(self.status.groups, gid)
    if group is None:
      return ApiResponse.error('set group failed, group {} not found'.format(gid))
    name, _ = utils.updated_val(update.name, group.name)
    zones, _ = utils.updated_val(update.zones, group.zones)
    vol_delta, vol_updated = utils.updated_val(update.vol_delta, group.vol_delta)
    if vol_updated and (group.vol_delta is not None and vol_delta is not None):
      vol_change = vol_delta - group.vol_delta
    else:
      vol_change = 0

    group.name = name
    group.zones = zones

    # update each of the member zones
    zone_update = models.ZoneUpdate(source_id=update.source_id, mute=update.mute)
    if vol_change != 0:
      # TODO: make this use volume delta adjustment, for now its a fixed group volume
      zone_update.vol = vol_delta # vol = z.vol + vol_change
    for zone in [self.status.zones[zone] for zone in zones]:
      self.set_zone(zone.id, zone_update, internal=True)

    # save the volume
    group.vol_delta = vol_delta

    if not internal:
      # update the group stats
      self._update_groups()
      self.mark_changes()

    return ApiResponse.ok()

  def _new_group_id(self):
    """ get next available group id """
    return utils.next_available_id(self.status.groups, default=100)

  def create_group(self, group: models.Group) -> models.Group:
    """Creates a new group with a list of zones

    Refer to the returned system state to obtain the id for the newly created group
    """
    # verify new group's name is unique
    names = [g.name for g in self.status.groups]
    if group.name in names:
      return ApiResponse.error('create group failed: {} already exists'.format(group.name))

    # get the new groug's id
    group.id = self._new_group_id()


    # add the new group
    self.status.groups.append(group)

    # update the group stats and populate uninitialized fields of the group
    self._update_groups()

    self.mark_changes()
    return group

  @save_on_success
  def delete_group(self, gid: int) -> ApiResponse:
    """Deletes an existing group"""
    try:
      i, _ = utils.find(self.status.groups, gid)
      if i is not None:
        del self.status.groups[i]
        return ApiResponse.ok()
      return ApiResponse.error('delete group failed: {} does not exist'.format(gid))
    except KeyError:
      return ApiResponse.error('delete group failed: {} does not exist'.format(gid))

  def _new_stream_id(self):
    stream: Optional[models.Stream] = max(self.status.streams, key=lambda stream: stream.id)
    if stream and stream.id:
      return stream.id + 1
    return 1000

  def create_stream(self, data: models.Stream) -> models.Stream:
    """ Create a new stream """
    try:
      # Make a new stream and add it to streams
      stream = amplipi.streams.build_stream(data, mock=self._mock_streams)
      sid = self._new_stream_id()
      self.streams[sid] = stream
      # Use get state to populate the contents of the newly created stream and find it in the stream list
      _, new_stream = utils.find(self.get_state().streams, sid)
      if new_stream:
        self.mark_changes()
        return new_stream
      return ApiResponse.error('create stream failed: no stream created')
    except Exception as exc:
      return ApiResponse.error('create stream failed: {}'.format(exc))

  @save_on_success
  def set_stream(self, sid: int, update: models.StreamUpdate) -> ApiResponse:
    """ Configure a stream """
    if sid not in self.streams:
      return ApiResponse.error('Stream id {} does not exist'.format(sid))
    try:
      stream = self.streams[sid]
    except Exception as exc:
      return ApiResponse.error('Unable to get stream {}: {}'.format(sid, exc))
    try:
      changes = update.dict(exclude_none=True)
      stream.reconfig(**changes)
      return ApiResponse.ok()
    except Exception as exc:
      return ApiResponse.error('Unable to reconfigure stream {}: {}'.format(sid, exc))

  @save_on_success
  def delete_stream(self, sid: int) -> ApiResponse:
    """Deletes an existing stream"""
    try:
      # if input is connected to a source change that input to nothing
      for src in self.status.sources:
        if src.get_stream() == sid and src.id is not None:
          self.set_source(src.id, models.SourceUpdate(input=''), internal=True)
      # actually delete it
      del self.streams[sid]
      i, _ = utils.find(self.status.streams, sid)
      if i is not None:
        del self.status.streams[i] # delete the cached stream state just in case
      return ApiResponse.ok()
    except KeyError:
      return ApiResponse.error('delete stream failed: {} does not exist'.format(sid))

  @save_on_success
  def exec_stream_command(self, sid: int, cmd: str) -> ApiResponse:
    """Sets play/pause on a specific pandora source """
    # TODO: this needs to be handled inside the stream itself, each stream can have a set of commands available
    if int(sid) not in self.streams:
      return ApiResponse.error('Stream id {} does not exist'.format(sid))

    try:
      stream = self.streams[sid]
    except Exception as exc:
      return ApiResponse.error('Unable to get stream {}: {}'.format(sid, exc))

    if not isinstance(stream, amplipi.streams.Pandora) or stream.mock:
      return ApiResponse.error(f'Stream "{stream}" does not support commands yet')

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
        station_id = int(cmd.replace('station=', ''))
        if station_id is not None:
          stream.ctrl.station(station_id)
        else:
          return ApiResponse.error('station=<int> expected where <int> is a valid integer, ie. station=23432423, received "{}"'.format(cmd))
      else:
        return ApiResponse.error('Command "{}" not recognized.'.format(cmd))
    except Exception as exc:
      return ApiResponse.error('Failed to execute stream command: {}: {}'.format(cmd, exc))

    return ApiResponse.ok()

  @save_on_success
  def get_stations(self, sid, stream_index=None) -> Union[ApiResponse, Dict[str, str]]:
    """Gets a pandora stream's station list"""
    # TODO: this should be moved to be a command of the Pandora stream interface
    if sid not in self.streams:
      return ApiResponse.error('Stream id {} does not exist!'.format(sid))
    # TODO: move the rest of this into streams
    if stream_index is not None:
      root = '{}/srcs/{}/'.format(utils.get_folder('config'), stream_index)
    else:
      root = ''
    stat_dir = root + '.config/pianobar/stationList'

    try:
      with open(stat_dir, 'r') as file:
        stations = {}
        for line in file.readlines():
          line = line.strip()
          if line:
            name_and_id = line.split(':')
            stations[name_and_id[0]] = name_and_id[1]
        return stations
    except Exception:
      # TODO: throw useful exceptions to next level
      pass
      #print(utils.error('Failed to get station list - it may not exist: {}'.format(e)))
    # TODO: Change these prints to returns in final state
    return {}

  def _new_preset_id(self) -> int:
    """ get next available preset id """
    return utils.next_available_id(self.status.presets, default=10000)

  def create_preset(self, preset: models.Preset) -> Union[ApiResponse, models.Preset]:
    """ Create a new preset """
    try:
      # Make a new preset and add it to presets
      # TODO: validate preset
      pid = self._new_preset_id()
      preset.id = pid
      preset.last_used = None # indicates this preset has never been used
      self.status.presets.append(preset)
      self.mark_changes()
      return preset
    except Exception as exc:
      return ApiResponse.error('create preset failed: {}'.format(exc))

  @save_on_success
  def set_preset(self, pid: int, update: models.PresetUpdate) -> ApiResponse:
    """ Reconfigure a preset """
    i, preset = utils.find(self.status.presets, pid)
    changes = update.dict(exclude_none=True)
    if i is None:
      return ApiResponse.error('Unable to find preset to redefine')

    try:
      # TODO: validate preset
      for field in changes.keys():
        preset.__dict__[field] = update.__dict__[field]
      return ApiResponse.ok()
    except Exception as exc:
      return ApiResponse.error('Unable to reconfigure preset {}: {}'.format(pid, exc))

  @save_on_success
  def delete_preset(self, pid: int) -> ApiResponse:
    """ Deletes an existing preset """
    try:
      idx, _ = utils.find(self.status.presets, pid)
      if idx is not None:
        del self.status.presets[idx] # delete the cached preset state just in case
        return ApiResponse.ok()
      return ApiResponse.error('delete preset failed: {} does not exist'.format(pid))
    except KeyError:
      return ApiResponse.error('delete preset failed: {} does not exist'.format(pid))

  def _effected_zones(self, preset_state: models.PresetState) -> Set[int]:
    """ Aggregate the zones that will be modified by changes """
    status = self.status
    effected: Set[int] = set()
    src_zones = utils.src_zones(status)
    for src_update in preset_state.sources or []:
      if src_update.id in src_zones:
        effected.update(src_zones[src_update.id])
    for group_update in preset_state.groups or []:
      if group_update.id:
        _, group_found = utils.find(status.groups, group_update.id)
        if group_found:
          effected.update(group_found.zones)
    for zone_update in preset_state.zones or []:
      if zone_update.id:
        effected.add(zone_update.id)
    return effected

  def _load_preset_state(self, preset_state: models.PresetState) -> None:
    """ Load a preset configuration """

    # determine which zones will be effected and mute them
    # we do this just in case there is intermediate state that causes audio issues. TODO: test with and without this feature (it adds a lot of complexity to presets, lets make sure its worth it)
    zones_effected = self._effected_zones(preset_state)
    zones_temp_muted = [zid for zid in zones_effected if not self.status.zones[zid].mute]
    zone_update = models.ZoneUpdate(mute=True)
    for zid in zones_temp_muted:
      self.set_zone(zid, zone_update, internal=True)

    # keep track of the zones muted by the preset configuration
    zones_muted: Set[int] = set()

    # execute changes source by source in increasing order
    for src in preset_state.sources or []:
      if src.id:
        self.set_source(src.id, src.as_update(), internal=True)
      else:
        pass # TODO: support some id-less source concept that allows dynamic source allocation

    # execute changes group by group in increasing order
    for group in preset_state.groups or []:
      _, groups_to_update = utils.find(self.status.groups, group.id)
      if groups_to_update is None:
        raise NameError('group {} does not exist'.format(group.id))
      self.set_group(group.id, group.as_update(), internal=True)
      if group.mute is not None:
        # use the updated group's zones just in case the group's zones were just changed
        _, g_updated = utils.find(self.status.groups, group.id)
        if g_updated is not None:
          zones_changed = g_updated.zones
          if group.mute:
            # keep track of the muted zones
            zones_muted.update(zones_changed)
          else:
            # handle odd mute thrashing case where zone was muted by one group then unmuted by another
            zones_muted.difference_update()

    # execute change zone by zone in increasing order
    for zone in preset_state.zones or []:
      self.set_zone(zone.id, zone.as_update(), internal=True)
      if zone.mute is not None:
        if zone.mute:
          zones_muted.add(zone.id)
        elif zone.id in zones_muted:
          zones_muted.remove(zone.id)

    # unmute effected zones that were not muted by the preset configuration
    zones_to_unmute = set(zones_temp_muted).difference(zones_muted)
    zone_update = models.ZoneUpdate(mute=False)
    for zid in zones_to_unmute:
      self.set_zone(zid, zone_update, internal=True)

    # update stats
    self._update_groups()

  @save_on_success
  def load_preset(self, pid: int) -> ApiResponse:
    """ To avoid any issues with audio coming out of the wrong speakers, we will need to carefully load a preset configuration.
    Below is an idea of how a preset configuration could be loaded to avoid any weirdness.
    We are also considering adding a "Last config" preset that allows us to easily revert the configuration changes.

    1. Grab system modification mutex to avoid accidental changes (requests during this time return some error)
    2. Save current configuration as "Last config" preset
    3. Mute any effected zones
    4. Execute changes to source, zone, group each in increasing order
    5. Unmute effected zones that were not muted
    6. Execute any stream commands
    7. Release system mutex, future requests are successful after this
    """
    # Get the preset to load
    i, preset = utils.find(self.status.presets, pid)
    if i is None or preset is None:
      return ApiResponse.error('load preset failed: {} does not exist'.format(pid))

    # TODO: acquire lock (all api methods that change configuration will need this)

    # update last config preset for restore capabilities (creating if missing)
    # TODO: "last config" does not currently support restoring streaming state, how would that work? (maybe we could just support play/pause state?)
    last_pid, _ = utils.find(self.status.presets, self._LAST_PRESET_ID)
    status = self.status
    last_config = models.Preset(
      id=9999,
      name='Restore last config',
      last_used=None, # this need to be in javascript time format
      state=models.PresetState(
        sources=deepcopy(status.sources),
        zones=deepcopy(status.zones),
        groups=deepcopy(status.groups)
      )
    )
    if last_pid is None:
      self.status.presets.append(last_config)
    else:
      self.status.presets[last_pid] = last_config

    if preset.state is not None:
      try:
        self._load_preset_state(preset.state)
      except Exception as exc:
        return ApiResponse.error(str(exc))

    # TODO: execute stream commands

    preset.last_used = int(time.time())

    # TODO: release lock
    return ApiResponse.ok()
