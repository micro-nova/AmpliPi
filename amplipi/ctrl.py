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

USER_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')
MUTE_ALL_ID = 10000
LAST_PRESET_ID = 9999
RCAs = [996, 997, 998, 999]

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

  _initialized = False # we need to know when we initialized first
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

  DEFAULT_CONFIG = { # This is the system state response that will come back from the amplipi box
    "sources": [ # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
      {"id": 0, "name": "Player 1", "input": f""},
      {"id": 1, "name": "Player 2", "input": f""},
      {"id": 2, "name": "Player 3", "input": f""},
      {"id": 3, "name": "Player 4", "input": f""},
    ],
    # NOTE: streams and groups seem like they should be stored as dictionaries with integer keys
    #       this does not make sense because JSON only allows string based keys
    "streams": [
      {"id": RCAs[0], "name": "Input 1", "type": "rca", "index": 0, "disabled": False},
      {"id": RCAs[1], "name": "Input 2", "type": "rca", "index": 1, "disabled": False},
      {"id": RCAs[2], "name": "Input 3", "type": "rca", "index": 2, "disabled": False},
      {"id": RCAs[3], "name": "Input 4", "type": "rca", "index": 3, "disabled": False},
      {"id": 1000, "name": "Groove Salad", "type": "internetradio", "url": "http://ice6.somafm.com/groovesalad-32-aac", "logo": "https://somafm.com/img3/groovesalad-400.jpg", "disabled": False},
    ],
    "zones": [ # this is an array of zones, array length depends on # of boxes connected
      {"id": 0, "name": "Zone 1", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
      {"id": 1, "name": "Zone 2", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
      {"id": 2, "name": "Zone 3", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
      {"id": 3, "name": "Zone 4", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
      {"id": 4, "name": "Zone 5", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
      {"id": 5, "name": "Zone 6", "source_id": 0, "mute": True, "disabled": False, "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    ],
    "groups": [
    ],
    "presets" : [
      {"id": MUTE_ALL_ID,
        # NOTE: additional zones are added automatically to this preset
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
    ]
  }
  # TODO: migrate to init setting instance vars to a disconnected state (API requests will throw Api.DisconnectedException() in this state
  # with this reinit will be called connect and will attempt to load the configutation and connect to an AmpliPi (mocked or real)
  # returning a boolean on whether or not it was successful
  def __init__(self, settings: models.AppSettings = models.AppSettings(), change_notifier: Optional[Callable[[models.Status], None]] = None):
    self.reinit(settings, change_notifier)
    self._initialized = True

  def reinit(self, settings: models.AppSettings = models.AppSettings(), change_notifier: Optional[Callable[[models.Status], None]] = None, config: Optional[models.Status] = None):
    """ Initialize or Reinitialize the controller

    Intitializes the system to to base configuration """
    self._change_notifier = change_notifier
    self._mock_hw = settings.mock_ctrl
    self._mock_streams = settings.mock_streams
    self._save_timer = None
    self._delay_saves = settings.delay_saves
    self._settings = settings

    # Create firmware interface. If one already exists delete then re-init.
    if self._initialized:
      # we need to make sure to mute every zone before resetting the fw
      zones_update = models.MultiZoneUpdate(zones=[z.id for z in self.status.zones], update=models.ZoneUpdate(mute=True))
      self.set_zones(zones_update, force_update=True, internal=True)
      try:
        del self._rt # remove the low level hardware connection
      except AttributeError:
        pass
    self._rt = rt.Mock() if settings.mock_ctrl else rt.Rpi() # reset the fw

    # test open the config file, this will throw an exception if there are issues writing to the file
    with open(settings.config_file, 'a'): # use append more to make sure we have read and write permissions, but won't overrite the file
      pass
    self.config_file = settings.config_file
    self.backup_config_file = settings.config_file + '.bak'
    self.config_file_valid = True # initially we assume the config file is valid
    errors = []
    if config:
      self.status = config
      loaded_config = True
    else:
      # try to load the config file or its backup
      config_paths = [self.config_file, self.backup_config_file]
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

    # TODO: detect missing sources

    # populate system info
    self._online_cache = utils.TimeBasedCache(self._check_is_online, 5, 'online')
    self._latest_release_cache = utils.TimeBasedCache(self._check_latest_release, 3600, 'latest release')
    self.status.info = models.Info(
      mock_ctrl=self._mock_hw,
      mock_streams=self._mock_streams,
      config_file=self.config_file,
      version=utils.detect_version(),
    )
    for major, minor, ghash, dirty in self._rt.read_versions():
      fw_info = models.FirmwareInfo(version=f'{major}.{minor}', git_hash=f'{ghash:x}', git_dirty=dirty)
      self.status.info.fw.append(fw_info)
    self._update_sys_info() # TODO: does sys info need to be updated at init time?

    # detect missing zones
    if self._mock_hw:
      # only allow 6 zones when mocked to simplify testing
      # add more if needed by specifying them in the config
      potential_zones = range(6)
    else:
      potential_zones = range(rt.MAX_ZONES)
    added_zone = False
    for zid in potential_zones:
      _, zone = utils.find(self.status.zones, zid)
      if zone is None and self._rt.exists(zid):
        added_zone = True
        self.status.zones.append(models.Zone(id=zid, name=f'Zone {zid+1}'))
    # save new config if zones were added
    if added_zone:
      self.save()

    # populate mute_all preset with all zones
    _, mute_all_pst = utils.find(self.status.presets, MUTE_ALL_ID)
    if mute_all_pst and mute_all_pst.name == 'Mute All':
      if mute_all_pst.state and mute_all_pst.state.zones:
        muted_zones = { z.id for z in mute_all_pst.state.zones }
        for z in self.status.zones:
          if z.id not in muted_zones:
            mute_all_pst.state.zones.append(models.ZoneUpdateWithId(id=z.id, mute=True))

    # add any missing RCA stream, mostly used to migrate old configs where rca inputs were not streams
    for rca_id in RCAs:
      sid, stream = utils.find(self.status.streams, rca_id)
      if sid is None:
        idx = rca_id - RCAs[0]
        # try to use the old name in the source if it was renamed from the default name of 1-4
        input_name = f'Input {idx + 1}'
        try:
          src_name = self.status.sources[idx].name
          if not src_name.isdigit():
            input_name = src_name
        except Exception as e:
          print(f'Error discovering old source name for conversion to RCA stream: {e}')
          print(f'- Defaulting name to: {input_name}')
        rca_stream = models.Stream(id=rca_id, name=input_name, type='rca', index=idx)
        self.status.streams.insert(idx, rca_stream)

    # configure all streams into a known state
    self.streams: Dict[int, amplipi.streams.AnyStream] = {}
    failed_streams: List[int] = []
    for stream in self.status.streams:
      assert stream.id is not None
      if stream.id:
        try:
          self.streams[stream.id] = amplipi.streams.build_stream(stream, self._mock_streams)
        except Exception as exc:
          print(f"Failed to create '{stream.name}' stream: {exc}")
          failed_streams.append(stream.id)
    self._sync_stream_info() # need to update the status with the new streams

    # configure all sources so that they are in a known state
    for src in self.status.sources:
      if src.id is not None:
        try:
          update = models.SourceUpdate(input=src.input)
          self.set_source(src.id, update, force_update=True, internal=True)
        except Exception as e:
          print(f'Error configuring source {src.id}: {e}')
          print(f'defaulting source {src.id} to an empty input')
          update = models.SourceUpdate(input='')
          try:
            self.set_source(src.id, update, force_update=True, internal=True)
          except Exception as e2:
            print(f'Error configuring source {src.id}: {e2}')
            print(f'Source {src.id} left uninitialized')

    # configure all of the zones so that they are in a known state
    #   we mute all zones on startup to keep audio from playing immediately at startup
    for zone in self.status.zones:
      # TODO: disable zones that are not found
      # we likely need an additional field for this, maybe auto-disabled?
      zone_update = models.ZoneUpdate(source_id=zone.source_id, mute=True, vol=zone.vol)
      self.set_zone(zone.id, zone_update, force_update=True, internal=True)
    # configure all of the groups (some fields may need to be updated)
    self._update_groups()

  def __del__(self):
    # stop save in the future so we can save right away
    # we save before shutting everything down to avoid saving disconnected state
    if self._save_timer:
      self._save_timer.cancel()
      self._save_timer = None
    self.save()
    print('stopping streams')
    # stop any streams
    for stream in self.streams.values():
      stream.disconnect()
    print('streams stopped', flush=True)
    # put the firmware in a reset state (should mute all audio)
    self._rt.reset()
    print('controller shutdown complete', flush=True)

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

  def _is_digital(self, sinput: str) -> bool:
    """Determines whether a source input, @sinput, is analog or digital

    sinput is expected to be one of the following:

    | str                  | meaning  | analog or digital? |
    | -------------------- | -------- | ------------------ |
    | ''                   | no input | digital            |
    | 'stream={stream_id}' | a stream | analog or digital (depending on stream_id's stream type) |

    The runtime only has the concept of digital or analog.
    The system defaults to digital as an undriven analog input acts as an antenna,
     producing a small amount of white noise.
    """
    try:
      sid = int(sinput.replace('stream=',''))
      return sid not in RCAs
    except:
      return True

  def get_inputs(self, src: models.Source) -> Dict[Union[str, None], str]:
    """Gets a dictionary of the possible inputs for a source

      Returns:
        A dictionary of the input types and a corresponding user friendly name/string for each
      Example:
        Get the possible inputs for any source (only one stream)

        >>> my_amplipi.get_inputs()
        { None, '', 'stream=9449' }
    """
    inputs: Dict[Union[str, None], str] = {None: ''}
    for sid, stream in self.streams.items():
      connectable = stream.requires_src() in [None, src.id] # TODO: remove this filter when sources can dynamically change output
      connected = src.get_stream()
      if sid == connected:
        assert connectable, print(f'Source {src} has invalid input: stream={connected}')
      if (sid == connected or not stream.disabled) and connectable:
        inputs[f'stream={sid}'] = stream.full_name()
    return inputs

  def _check_is_online(self) -> bool:
    online = False
    try:
      with open(os.path.join(USER_CONFIG_DIR, 'online'), encoding='utf-8') as fonline:
        online = 'online' in fonline.readline()
    except Exception:
      pass
    return online

  def _check_latest_release(self) -> str:
    release = 'unknown'
    try:
      with open(os.path.join(USER_CONFIG_DIR, 'latest_release'), encoding='utf-8') as flatest:
        release = flatest.readline().strip()
    except Exception:
      pass
    return release

  def _update_sys_info(self, throttled = True) -> None:
    """Update current system information"""
    if self.status.info is None:
      raise Exception("No info generated, system in a bad state")
    self.status.info.online = self._online_cache.get(throttled)
    self.status.info.latest_release = self._latest_release_cache.get(throttled)

  def _sync_stream_info(self) -> None:
    """Synchronize the stream list to the stream status"""
    # TODO: figure out how to cache stream info, since it only needs to happen when a stream is added/updated
    streams = []
    for sid, stream_inst in self.streams.items():
      # TODO: this functionality should be in the unimplemented streams base class
      # convert the stream instance info to stream data (serialize its current configuration)
      st_type = type(stream_inst).__name__.lower()
      stream = models.Stream(id=sid, name=stream_inst.name, type=st_type)
      for field in models.optional_stream_fields():
        if field in stream_inst.__dict__:
          stream.__dict__[field] = stream_inst.__dict__[field]
      streams.append(stream)
    self.status.streams = streams

  def get_state(self) -> models.Status:
    """ get the system state """
    self._update_sys_info()
    # update source's info
    # TODO: source info should be updated in a background thread
    for src in self.status.sources:
      self._update_src_info(src)
    return self.status

  def get_info(self) -> models.Info:
    """ Get the system information """
    self._update_sys_info()
    if self.status.info is None:
      raise Exception("No info generated, system in a bad state")
    return self.status.info

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

  def get_stream(self, src: Optional[models.Source] = None, sid: Optional[int] = None) -> Optional[amplipi.streams.AnyStream]:
    """Gets the stream from a source

    Args:
      src: An audio source that may have a stream connected
      sid: ID of an audio source
    Returns:
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

  def _update_src_info(self, src: models.Source):
    """ Update a source's status and song metadata """
    stream_inst = self.get_stream(src)
    if stream_inst is not None:
      src.info = stream_inst.info()
    else:
      src.info = models.SourceInfo(img_url='static/imgs/disconnected.png', name='None', state='stopped')

  def set_source(self, sid: int, update: models.SourceUpdate, force_update: bool = False, internal: bool = False) -> ApiResponse:
    """Modifes the configuration of one of the 4 system sources

      Args:
        sid (int): source id [0,3]
        update: changes to source
        force_update: bool, update source even if no changes have been made (for hw startup)
        internal: called by a higher-level ctrl function:

      Returns:
        'None' on success, otherwise error (dict)
    """
    try:
      idx, src = utils.find(self.status.sources, sid)
      if idx is not None and src is not None:
        name, _ = utils.updated_val(update.name, src.name)
        input_, input_updated = utils.updated_val(update.input, src.input)
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
            stolen_from: Optional[models.Source] = None
            if stream.src is not None and stream.src != idx:
              stolen_from = self.status.sources[stream.src]
              print('stealing {} from source {}'.format(stream.name, stolen_from.name))
              stolen_from.input = ''
            try:
              stream.disconnect()
              stream.connect(idx)
            except Exception as iexc:
              print(f"Failed to update {sid}'s input to {stream.name}: {iexc}")
              stream.disconnect()
              if old_stream:
                print(f'Trying to get back to the previous input: {old_stream.name}')
                old_stream.connect(idx)
                src.input = last_input
              else:
                src.input = ''
              # connect the stream back to its old source
              if stolen_from:
                print(f"Trying to revert src {stolen_from.id}'s input to {stream.name}")
                stream.connect(stolen_from.id)
                stolen_from.input = input_
              # now that we recovered, show that this failed
              raise iexc
          elif src.input and 'stream=' in src.input: # invalid stream id?
            # TODO: should this stream id validation happen in the Source model?
            src.input = last_input
            raise Exception(f'StreamID specified by "{src.input}" not found')
          rt_needs_update = self._is_digital(input_) != self._is_digital(last_input)
          if rt_needs_update or force_update:
            # get the current underlying type of each of the sources, for configuration of the runtime
            src_cfg = [self._is_digital(self.status.sources[s].input) for s in range(4)]
            # update this source
            src_cfg[idx] = self._is_digital(input_)
            if not self._rt.update_sources(src_cfg):
              raise Exception('failed to set source')
          self._update_src_info(src) # synchronize the source's info
        if not internal:
          self.mark_changes()
      else:
        raise Exception(f'failed to set source: index {idx} out of bounds')
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'failed to set source: {exc}')
    return ApiResponse.ok()

  def set_zone(self, zid, update: models.ZoneUpdate, force_update: bool = False, internal: bool = False) -> ApiResponse:
    """Reconfigures a zone

      Args:
        id: any valid zone [0,p*6-1] (6 zones per preamp)
        update: changes to zone
        force_update: update source even if no changes have been made (for hw startup)
        internal: called by a higher-level ctrl function
      Returns:
        ApiResponse
    """
    try:
      idx, zone = utils.find(self.status.zones, zid)
      if idx is not None and zone is not None:
        name, _ = utils.updated_val(update.name, zone.name)
        source_id, update_source_id = utils.updated_val(update.source_id, zone.source_id)
        mute, update_mutes = utils.updated_val(update.mute, zone.mute)
        vol, update_vol = utils.updated_val(update.vol, zone.vol)
        vol_f, update_vol_f = utils.updated_val(update.vol_f, zone.vol_f)
        vol_min, update_vol_min = utils.updated_val(update.vol_min, zone.vol_min)
        vol_max, update_vol_max = utils.updated_val(update.vol_max, zone.vol_max)
        disabled, _ = utils.updated_val(update.disabled, zone.disabled)
        # update non hw state
        zone.name = name
        zone.disabled = disabled

        # any disabled zone should not be able to play anything, mute it to be sure
        if zone.disabled and not mute:
          mute = True
          update_mutes = True

        # update the zone's associated source
        sid = utils.parse_int(source_id, [0, 1, 2, 3])
        zones = self.status.zones
        if update_source_id or force_update:
          zone_sources = [zone.source_id for zone in zones]
          zone_sources[idx] = sid
          if self._rt.update_zone_sources(idx, zone_sources):
            zone.source_id = sid
          else:
            raise Exception('unable to update zone source')

        # update min/max volumes
        if vol_max - vol_min < models.MIN_DB_RANGE:
          raise Exception(f'max - min volume must be greater than {models.MIN_DB_RANGE}')
        zone.vol_min = vol_min
        zone.vol_max = vol_max

        def set_mute():
          mutes = [zone.mute for zone in zones]
          mutes[idx] = mute
          if self._rt.update_zone_mutes(idx, mutes):
            zone.mute = mute
          else:
            raise Exception('unable to update zone mute')

        def set_vol():
          """ Update the zone's volume. Could be triggered by a change in
              vol, vol_f, vol_min, or vol_max.
          """
          # 'vol' (in dB) takes precedence over vol_f
          if update.vol_f is not None and update.vol is None:
            vol_db = utils.vol_float_to_db(vol_f, zone.vol_min, zone.vol_max)
            vol_f_new = vol_f
          else:
            vol_db = utils.clamp(vol, zone.vol_min, zone.vol_max)
            vol_f_new = utils.vol_db_to_float(vol_db, zone.vol_min, zone.vol_max)
          if self._rt.update_zone_vol(idx, vol_db):
            zone.vol = vol_db
            zone.vol_f = vol_f_new
          else:
            raise Exception('unable to update zone volume')

        # To avoid potential unwanted loud output:
        # If muting, mute before setting volumes
        # If un-muting, set desired volume first
        update_volumes = update_vol or update_vol_f or update_vol_min or update_vol_max
        if force_update or (update_mutes and update_volumes):
          if mute:
            set_mute()
            set_vol()
          else:
            set_vol()
            set_mute()
        elif update_volumes:
          set_vol()
        elif update_mutes:
          set_mute()

        if not internal:
          # update the group stats (individual zone volumes, sources, and mute configuration can effect a group)
          self._update_groups()
          self.mark_changes()
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'set zone failed: {exc}')
    else:
      return ApiResponse.ok()

  def set_zones(self, multi_update: models.MultiZoneUpdate, force_update: bool = False, internal: bool = False) -> ApiResponse:
    """Reconfigures a set of zones

      Args:
        update: changes to apply to embedded zones and groups
      Returns:
        ApiResponse
    """
    try:
      # aggregate all of the zones together
      all_zids = utils.zones_from_all(self.status, multi_update.zones, multi_update.groups)
      # update each of the zones
      for zid in all_zids:
        zupdate = multi_update.update.copy() # we potentially need to make changes to the underlying update
        if zupdate.name:
          # ensure all zones don't get named the same
          zupdate.name = f'{zupdate.name} {zid+1}'
        self.set_zone(zid, zupdate, force_update=force_update, internal=True)
      if not internal:
        # update the group stats (individual zone volumes, sources, and mute configuration can effect a group)
        self._update_groups()
        self.mark_changes()
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'set_zones failed: {exc}')
    return ApiResponse.ok()

  def _update_groups(self) -> None:
    """Updates the group's aggregate fields to maintain consistency and simplify app interface"""
    for group in self.status.groups:
      zones = [self.status.zones[z] for z in group.zones]
      mutes = [z.mute for z in zones]
      sources = {z.source_id for z in zones}
      vols = [z.vol_f for z in zones]
      vols.sort()
      group.mute = False not in mutes # group is only considered muted if all zones are muted
      if len(sources) == 1:
        group.source_id = sources.pop() # TODO: how should we handle different sources in the group?
      else: # multiple sources
        group.source_id = None
      group.vol_f = (vols[0] + vols[-1]) / 2 # group volume is the midpoint between the highest and lowest source
      group.vol_delta = utils.vol_float_to_db(group.vol_f)

  def set_group(self, gid, update: models.GroupUpdate, internal: bool = False) -> ApiResponse:
    """Configures an existing group
        parameters will be used to configure each zone in the group's zones
        all parameters besides the group id, @id, are optional

        Args:
          gid: group id (a guid)
          update: changes to group
          internal: called by a higher-level ctrl function
        Returns:
          'None' on success, otherwise error (dict)
    """
    try:
      _, group = utils.find(self.status.groups, gid)
      if group is None:
        raise Exception(f'group {gid} not found')
      name, _ = utils.updated_val(update.name, group.name)
      zones, _ = utils.updated_val(update.zones, group.zones)
      vol_delta, vol_updated = utils.updated_val(update.vol_delta, group.vol_delta)
      vol_f, vol_f_updated = utils.updated_val(update.vol_f, group.vol_f)

      group.name = name
      group.zones = zones

      # determine group volume, 'vol_delta' (in dB) takes precedence over vol_f
      # if vol_updated is true vol_delta can't be none but mypy isn't smart enough to know that
      if vol_updated and vol_delta is not None:
        vol_f = utils.vol_db_to_float(vol_delta)

      # update each of the member zones
      zone_update = models.ZoneUpdate(source_id=update.source_id, mute=update.mute)
      if vol_updated or vol_f_updated:
        # TODO: make this use volume delta adjustment, for now its a fixed group volume
        # use float value so zone calculates appropriate offsets in dB
        zone_update.vol_f = vol_f
      for zone in [self.status.zones[zone] for zone in zones]:
        self.set_zone(zone.id, zone_update, internal=True)

      if not internal:
        # update the group stats
        self._update_groups()
        self.mark_changes()
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'set_group failed: {exc}')
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

  def _new_stream_id(self) -> int:
    def get_stream_id(stream):
      if (stream is not None) and (stream.id is not None):
        return stream.id
      return -1
    stream: Optional[models.Stream] = max(self.status.streams, key=get_stream_id, default=None)
    if stream and stream.id is not None:
      return stream.id + 1
    return 1000

  def create_stream(self, data: models.Stream, internal=False) -> models.Stream:
    """ Create a new stream """
    try:
      if not internal and data.type == 'rca':
        raise Exception(f'Unable to create protected RCA stream, the RCA streams for each RCA input {RCAs} already exist')
      # Make a new stream and add it to streams
      stream = amplipi.streams.build_stream(data, mock=self._mock_streams)
      sid = self._new_stream_id()
      self.streams[sid] = stream
      self._sync_stream_info()
      # Use get state to populate the contents of the newly created stream and find it in the stream list
      _, new_stream = utils.find(self.get_state().streams, sid)
      if new_stream:
        if not internal:
          self.mark_changes()
        return new_stream
      raise Exception('no stream created')
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'create stream failed: {exc}')

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
      self._sync_stream_info()
      return ApiResponse.ok()
    except Exception as exc:
      return ApiResponse.error('Unable to reconfigure stream {}: {}'.format(sid, exc))

  def delete_stream(self, sid: int, internal=False) -> ApiResponse:
    """Deletes an existing stream"""
    try:
      # RCA streams are intrinsic to the hardware and can't be removed
      if sid in RCAs and isinstance(self.streams[sid], amplipi.streams.RCA):
        msg = f'Protected stream {sid} cannot be removed, use disabled=True to hide it'
        raise Exception(msg)
      # if input is connected to a source change that input to nothing
      for src in self.status.sources:
        if src.get_stream() == sid and src.id is not None:
          self.set_source(src.id, models.SourceUpdate(input=''), internal=True)
      # actually delete it
      del self.streams[sid]
      i, _ = utils.find(self.status.streams, sid)
      if i is not None:
        del self.status.streams[i] # delete the cached stream state just in case
      self._sync_stream_info()
      if not internal:
        self.mark_changes()
      return ApiResponse.ok()
    except KeyError :
      msg = f'delete stream failed: {sid} does not exist'
    except Exception as exc:
      msg =  f'delete stream failed: {exc}'
    if internal:
      raise Exception(msg)
    return ApiResponse.error(msg)

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

    try:
      stream.send_cmd(cmd)
    except Exception as exc:
      return ApiResponse.error(f'Failed to execute stream command: {cmd}: {exc}')

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

  def create_preset(self, preset: models.Preset, internal=False) -> Union[ApiResponse, models.Preset]:
    """ Create a new preset """
    try:
      # Make a new preset and add it to presets
      # TODO: validate preset
      pid = self._new_preset_id()
      preset.id = pid
      preset.last_used = None # indicates this preset has never been used
      self.status.presets.append(preset)
      if not internal:
        self.mark_changes()
      return preset
    except Exception as exc:
      if internal:
        raise exc
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
      if src.id is not None:
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

  def load_preset(self, pid: int, internal=False) -> ApiResponse:
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
    try:
      # Get the preset to load
      i, preset = utils.find(self.status.presets, pid)
      if i is None or preset is None:
        raise Exception(f'{pid} does not exist')

      # TODO: acquire lock (all api methods that change configuration will need this)

      # update last config preset for restore capabilities (creating if missing)
      # TODO: "last config" does not currently support restoring streaming state, how would that work? (maybe we could just support play/pause state?)
      last_pid, _ = utils.find(self.status.presets, LAST_PRESET_ID)
      status = self.status
      last_config = models.Preset(
        id=LAST_PRESET_ID,
        name='Restore last config',
        last_used=None, # this need to be in javascript time format
        state=models.PresetState(
          sources=deepcopy(status.sources),
          zones=deepcopy(status.zones),
          groups=deepcopy(status.groups)
        )
      )

      if preset.state is not None:
        try:
          self._load_preset_state(preset.state)
        except Exception as exc:
          # TODO: revert to old state and rollback last config
          raise exc
        else:
          if last_pid is None:
            self.status.presets.append(last_config)
          else:
            self.status.presets[last_pid] = last_config

      # TODO: execute stream commands

      preset.last_used = int(time.time())
    except Exception as exc:
      if internal:
        raise exc
      return ApiResponse.error(f'load_preset failed: {exc}')
    # TODO: release lock
    return ApiResponse.ok()

  def announce(self, announcement: models.Announcement) -> ApiResponse:
    """ Create and play an announcement """
    # create a temporary announcement stream using fileplayer
    resp0 = self.create_stream(models.Stream(type='fileplayer', name='Announcement', url=announcement.media), internal=True)
    if isinstance(resp0, ApiResponse):
      return resp0
    stream = resp0
    # create a temporary preset with all zones connected to the announcement stream and load it
    pa_src = models.SourceUpdateWithId(id=announcement.source_id, input=f'stream={stream.id}') # for now we just use the last source
    if announcement.zones is None and announcement.groups is None:
      zones_to_use = {z.id for z in self.status.zones if z.id is not None and not z.disabled}
    else:
      unique_zones = utils.zones_from_all(self.status, announcement.zones, announcement.groups)
      zones_to_use = utils.enabled_zones(self.status, unique_zones)
    # Set the volume of the announcement, forcing db only if it is specified
    if announcement.vol is not None:
      pa_zones = [models.ZoneUpdateWithId(id=zid, source_id=pa_src.id, mute=False, vol=announcement.vol) for zid in zones_to_use]
    else:
      pa_zones = [models.ZoneUpdateWithId(id=zid, source_id=pa_src.id, mute=False, vol_f=announcement.vol_f) for zid in zones_to_use]
    resp1 = self.create_preset(models.Preset(name='PA - announcement', state=models.PresetState(sources=[pa_src], zones=pa_zones)))
    if isinstance(resp1, ApiResponse):
      return resp1
    pa_preset = resp1
    if pa_preset.id is None or stream.id is None:
      return ApiResponse.error('ID expected to be provided')
    resp2 = self.load_preset(pa_preset.id, internal=True)
    if resp2.code != ApiCode.OK:
      return resp2
    resp3 = self.delete_preset(pa_preset.id)
    if resp3.code != ApiCode.OK:
      return resp3
    # wait for the announcement to be done and switch back to the previous state
    # TODO: what is the longest announcement we should accept?
    stream_inst = self.streams[stream.id]
    while True:
      time.sleep(0.1)
      if stream_inst.state in ['stopped', 'disconnected']:
        break
    resp4 = self.load_preset(LAST_PRESET_ID, internal=True)
    resp5 = self.delete_stream(stream.id, internal=True) # remember to delete the temporary stream
    if resp5.code != ApiCode.OK:
      return resp5
    self.mark_changes()
    return resp4
