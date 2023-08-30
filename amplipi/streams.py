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

"""Digital Audio Streams

This module allows you to connect and control configurable network audio sources
such as Pandora, Spotify, and AirPlay. Each digital source is expected to have
a consistent interface.
"""

import os
import traceback
from re import sub
import sys
import subprocess
import time
from typing import Union, Optional, List
import threading

import ast
import json
import signal
import socket
import hashlib # md5 for string -> MAC generation

from amplipi import models
from amplipi import utils
from amplipi.mpris import MPRIS

# We use Popen for long running process control this error is not useful:
# pylint: disable=consider-using-with

def write_config_file(filename, config):
  """ Write a simple config file (@filename) with key=value pairs given by @config """
  with open(filename, 'wt', encoding='utf-8') as cfg_file:
    for key, value in config.items():
      cfg_file.write(f'{key}={value}\n')

def write_sp_config_file(filename, config):
  """ Write a shairport config file (@filename) with a hierarchy of grouped key=value pairs given by @config """
  with open(filename, 'wt', encoding='utf-8') as cfg_file:
    for group, gconfig in config.items():
      cfg_file.write(f'{group} =\n{{\n')
      for key, value in gconfig.items():
        if isinstance(value, str):
          cfg_file.write(f'  {key} = "{value}"\n')
        else:
          cfg_file.write(f'  {key} = {value}\n')
      cfg_file.write('};\n')

def uuid_gen():
  """ Generates a UUID for use in DLNA and Plexamp streams """
  uuid_proc = subprocess.run(args='uuidgen', capture_output=True, check=False)
  uuid_str = str(uuid_proc).split(',')
  c_check = uuid_str[0]
  val = uuid_str[2]

  if c_check[0:16] == 'CompletedProcess': # Did uuidgen succeed?
    return val[10:46]
  # Generic UUID in case of failure
  return '39ae35cc-b4c1-444d-b13a-294898d771fa'

class BaseStream:
  """ BaseStream class containing methods that all other streams inherit """
  def __init__(self, stype: str, name: str, only_src=None, disabled: bool=False, mock=False):
    self.name = name
    self.disabled = disabled
    self.proc: Optional[subprocess.Popen] = None
    self.mock = mock
    self.src: Optional[int] = None
    self.only_src: Optional[int] = only_src
    self.state = 'disconnected'
    self.stype = stype

  def __del__(self):
    self.disconnect()

  def __str__(self):
    connection = f' connected to src={self.src}' if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return f'{self.full_name()}{connection}{mock}'

  def full_name(self):
    """ Combine name and type of a stream to make a stream easy to identify.

    Many streams will simply be named something like AmpliPi or John, so embedding the '- stype'
    into the name makes the name easier to identify.
    """
    return f'{self.name} - {self.stype}'

  def _disconnect(self):
    print(f'{self.name} disconnected')
    self.state = 'disconnected'
    self.src = None

  def disconnect(self):
    """ Disconnect the stream from an output source """
    if self._is_running() and self.proc is not None:
      try:
        self.proc.kill()
      except Exception:
        pass
    self._disconnect()

  def _connect(self, src):
    print(f'{self.name} connected to {src}')
    self.state = 'connected'
    self.src = src

  def is_connected(self) -> bool:
    return self.src is not None

  def connect(self, src: int):
    """ Connect the stream to an output source """
    self._connect(src)

  def reconfig(self, **kwargs):
    """ Reconfigure a potentially running stream """

  def is_activated(self):
    """ Check if this stream has been activated """
    # activate/deactivate is not supported by the base stream type
    return False

  def _is_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def info(self) -> models.SourceInfo:
    """ Get stream info and song metadata """
    return models.SourceInfo(
      name=self.full_name(),
      state=self.state)

  def requires_src(self) -> Optional[int]:
    """ Check if this stream needs to be connected to a specific source

    returns that source's id or None for any source
    """
    return self.only_src

  def send_cmd(self, cmd: str) -> None:
    """ Generic send_cmd function. If not implemented in a stream,
    and a command is sent, this error will be raised.
    """
    raise NotImplementedError(f'{self.name} does not support commands')

class VirtualSources:
  """ Virtual source allocator to mind ALSA limits"""
  def __init__(self, num_sources: int):
    self._sources : List[Optional[int]] = [None] * num_sources

  def available(self) -> bool:
    """ Are any sources available """
    return None in self._sources

  def alloc(self) -> int:
    """ Allocate an available virtual source if any"""
    if self.available():
      for i, s in enumerate(self._sources):
        if s is None:
          self._sources[i] = i
          return i
    raise Exception('no sources available')

  def free(self, vsrc: int):
    """ make a virtual source available """
    if self._sources[vsrc] is None:
      raise Exception(f'unable to free virtual source {vsrc} it was not allocated')
    self._sources[vsrc] = None

vsources = VirtualSources(12)

class PersistentStream(BaseStream):
  """ Base class for streams that are able to persist without a direct connection to an output """
  def __init__(self, stype: str, name: str, disabled: bool=False, mock=False):
    super().__init__(stype, name, None, disabled, mock)
    self.vsrc: Optional[int] = None
    self._cproc: Optional[subprocess.Popen] = None

  def __del__(self):
    self.deactivate()
    self.disconnect()

  def is_persistent(self):
    """ Does this stream run in the background? """
    # TODO: this should be a runtime configurable field and used to determine streams to start up in the background
    return False

  def activate(self):
    """ Start the stream behind the scenes without connecting to a physical source.
    Stream will @persist after disconnected if is_persistent() returns True
    """
    try:
      vsrc = vsources.alloc()
      self.vsrc = vsrc
      self.state = "connected" # optimistically make this look like a normal stream for now
      if not self.mock:
        self._activate(vsrc) # might override self.state
      print(f"Activating {self.name} ({'persistant' if self.is_persistent() else 'temporarily'})")
    except Exception as e:
      print(f'Failed to activate {self.name}: {e}')
      if vsrc is not None:
        vsources.free(vsrc)
      self.vsrc = None
      self.state = 'disconnected'
      raise e

  def _activate(self, vsrc: int):
    raise NotImplementedError(f'{self.stype} does not support activation')

  def is_activated(self) -> bool:
    """ Is this stream activated? """
    return self.vsrc is not None

  def deactivate(self):
    """ Stop the stream behind the scenes """
    try:
      print(f'deactivating {self.name}')
      self._deactivate()
    except Exception as e:
      raise Exception(f'Failed to deactivate {self.name}: {e}') from e
    finally:
      self.state = "disconnected"  # make this look like a normal stream for now
      if self.vsrc:
        vsrc = self.vsrc
        self.vsrc = None
        vsources.free(vsrc)

  def _deactivate(self):
    raise NotImplementedError(f'{self.stype} does not support deaactivation')

  def reactivate(self):
    """ Stop and restart the stream behind the scenes.
    This should be called after significant paranmeter changes.
    """
    print(f'reactivating {self.name}')
    if self.is_activated():
      self.deactivate()
      time.sleep(0.1) # wait a bit just in case

  def connect(self, src: int):
    """ Connect an output to a given audio source """
    if self.is_connected():
      raise Exception(f"Stream already connected to a source {self.src}, disconnect before trying to connect")
    if self.vsrc is None:
      # activate on the fly
      self.activate()
      if self.vsrc is None:
        raise Exception('No virtual source found/available')
    virt_dev = utils.virtual_connection_device(self.vsrc)
    phy_dev = utils.real_output_device(src)
    if virt_dev is None or self.mock:
      print('  pretending to connect to loopback (unavailable)')
    else:
      # args = f'alsaloop -C {virt_dev} -P {phy_dev} -t 100000'.split()
      args = f'{sys.executable} {utils.get_folder("streams")}/process_monitor.py alsaloop -C {virt_dev} -P {phy_dev} -t 100000'.split()
      try:
        print(f'  starting connection via: {" ".join(args)}')
        self._cproc = subprocess.Popen(args=args)
      except Exception as exc:
        print(f'Failed to start alsaloop connection: {exc}')
        time.sleep(0.1) # Delay a bit
    self.src = src

  def disconnect(self):
    """ Disconnect from a DAC """
    if self._cproc:
      print(f'  stopping connection {self.vsrc} -> {self.src}')
      try:
        # must use terminate as kill() cannot be intercepted
        self._cproc.terminate()

      except Exception as e:
        print(f'PersistentStream disconnect error: {e}')
        pass
    self.src = None

class RCA(BaseStream):
  """ A built-in RCA input """
  def __init__(self, name: str, index: int, disabled: bool = False, mock: bool = False):
    super().__init__('rca', name, only_src=index, disabled=disabled, mock=mock)
    # for serialiation the stream model's field needs to map to a stream's fields
    # index is needed for serialization
    self.index = index

  def reconfig(self, **kwargs):
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']

  def info(self) -> models.SourceInfo:
    src_info = models.SourceInfo(img_url='static/imgs/rca_inputs.svg', name=self.full_name(), state='stopped')
    playing = False
    status_file = f'{utils.get_folder("config")}/srcs/rca_status'
    try:
      if self.src is not None:
        with open(status_file, mode='rb') as file:
          status_all = file.read()[0]
          playing = (status_all & (0b11 << (self.src * 2))) != 0
    except FileNotFoundError as error:
      print(f"Couldn't open RCA audio status file {status_file}:\n  {error}")
    except Exception as error:
      print(f'Error getting RCA audio status:\n  {error}')
    src_info.state = "playing" if playing else "stopped"
    return src_info

  def connect(self, src):
    if src != self.only_src:
      raise Exception(f"Unable to connect RCA {self.only_src} to src {src}, can only be connected to {self.only_src}")
    self._connect(src)

  def disconnect(self):
    self._disconnect()

class AirPlay(PersistentStream):
  """ An AirPlay Stream """
  def __init__(self, name: str, ap2: bool, disabled: bool = False, mock: bool = False):
    super().__init__('airplay', name, disabled=disabled, mock=mock)
    self.mpris: Optional[MPRIS] = None
    self.ap2 = ap2
    self.ap2_exists = False
    self.supported_cmds = [
      'play',
      'pause',
      'next',
      'prev'
      ]
    self.STATE_TIMEOUT = 300 # seconds
    self._connect_time = 0.0
    self._coverart_dir = ''

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if 'ap2' in kwargs and kwargs['ap2'] != self.ap2:
      self.ap2 = kwargs['ap2']
      reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect an AirPlay device to a given audio source
    This creates an AirPlay streaming option based on the configuration
    """

    # if stream is airplay2 check for other airplay2s and error if found
    # pgrep has it's own process that will include the process name so we sub 1 from the results
    if self.ap2:
      if len(os.popen("pgrep -f shairport-sync-ap2").read().strip().splitlines())-1 > 0:
        self.ap2_exists = True
        # TODO: we need a better way of showing errors to user
        print(f'Another Airplay 2 stream is already in use, unable to start {self.name}, mocking connection')
        return

    src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    os.system(f'rm -f {src_config_folder}/currentSong')
    self._connect_time = time.time()
    self._coverart_dir = f'{utils.get_folder("web")}/generated/v{vsrc}'

    config = {
      'general': {
        'name': self.name,
        'port': 5100 + 100 * vsrc, # Listen for service requests on this port
        'udp_port_base': 6101 + 100 * vsrc, # start allocating UDP ports from this port number when needed
        'drift': 2000, # allow this number of frames of drift away from exact synchronisation before attempting to correct it
        'resync_threshold': 0, # a synchronisation error greater than this will cause resynchronisation; 0 disables it
        'log_verbosity': 0, # "0" means no debug verbosity, "3" is most verbose.
        'mpris_service_bus': 'Session',
      },
      'metadata':{
        'enabled': 'yes',
        'include_cover_art': 'yes',
        'cover_art_cache_directory': self._coverart_dir,
      },
      'alsa': {
        'output_device': utils.virtual_output_device(vsrc), # alsa output device
        'audio_backend_buffer_desired_length': 11025 # If set too small, buffer underflow occurs on low-powered machines. Too long and the response times with software mixer become annoying.
      },
    }

    # make all of the necessary dir(s)
    os.system(f'rm -r -f {self._coverart_dir}')
    os.system(f'mkdir -p {self._coverart_dir}')
    os.system(f'mkdir -p {src_config_folder}')
    config_file = f'{src_config_folder}/shairport.conf'
    write_sp_config_file(config_file, config)
    shairport_args = f"{utils.get_folder('streams')}/shairport-sync{'-ap2' if self.ap2 else ''} -c {config_file}".split(' ')
    print(f'shairport_args: {shairport_args}')

    self.proc = subprocess.Popen(args=shairport_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
      mpris_name = 'ShairportSync'
      # If there are multiple shairport-sync processes, add the pid to the mpris name
      # shairport sync only adds the pid to the mpris name if it cannot use the default name
      if len(os.popen("pgrep shairport-sync").read().strip().splitlines()) > 1:
        mpris_name += f".i{self.proc.pid}"
      self.mpris = MPRIS(mpris_name, f'{src_config_folder}/metadata.txt')
    except Exception as exc:
      print(f'Error starting airplay MPRIS reader: {exc}')

  def _deactivate(self):
    if self.mpris:
      self.mpris.close()
    self.mpris = None
    if self._is_running():
      self.proc.stdin.close()
      print('stopping shairport-sync')
      self.proc.terminate()
      if self.proc.wait(1) != 0:
        print('killing shairport-sync')
        self.proc.kill()
    if self.src:
      try:
        subprocess.run(f'rm -r {utils.get_folder("config")}/srcs/{self.src}/*', shell=True, check=True)
      except Exception as e:
        print(f'Error removing airplay config files: {e}')
    self._disconnect()
    self.proc = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=f"Connect to {self.name} on Airplay{'2' if self.ap2 else ''}",
      state=self.state,
      img_url='static/imgs/shairport.png'
    )

    # if stream is airplay2 and other airplay2s exist show error message
    if self.ap2:
      if self.ap2_exists:
        source.name = 'An Airplay2 stream already exists!\n Please disconnect it and try again.'
        return source

    if not self.mpris:
      print(f'Airplay: No MPRIS object for {self.name}!')
      return source

    try:
      md = self.mpris.metadata()

      if self.mpris.is_playing():
        source.state = 'playing'
      else:
        # if we've been paused for a while and the state has changed since connecting, then say
        # we're stopped since shairport-sync doesn't really differentiate between paused and stopped
        if self._connect_time < md.state_changed_time and time.time() - md.state_changed_time < self.STATE_TIMEOUT:
          source.state = 'paused'
        else:
          source.state = 'stopped'

      if source.state != 'stopped':
        source.artist = md.artist
        source.track = md.title
        source.album = md.album
        source.supported_cmds=list(self.supported_cmds)

        if md.title != '':
          #if there is a title, attempt to get coverart
          images = os.listdir(self._coverart_dir)
          if len(images) > 0:
            source.img_url = f'generated/{self.src}/{images[0]}'
        else:
          source.track = "No metadata available"


    except Exception as e:
      print(f"error in airplay: {e}")

    return source

  def send_cmd(self, cmd):
    try:
      if cmd in self.supported_cmds:
        if cmd == 'play':
          self.mpris.play_pause()
        elif cmd == 'pause':
          self.mpris.play_pause()
        elif cmd == 'next':
          self.mpris.next()
        elif cmd == 'prev':
          self.mpris.previous()
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      print(f"error in shairport: {e}")

class Spotify(PersistentStream):
  """ A Spotify Stream """
  def __init__(self, name: str, disabled: bool = False, mock: bool = False):
    super().__init__('spotify', name, disabled=disabled, mock=mock)

    self.connect_port: Optional[int] = None
    self.mpris: Optional[MPRIS] = None
    self.proc_pid: Optional[int] = None
    self.supported_cmds = ['play', 'pause', 'next', 'prev']

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def __del__(self):
    self.disconnect()

  def is_persistent(self):
    return True

  def _activate(self, vsrc: int):
    """ Connect a Spotify output to a given audio source
    This will create a Spotify Connect device based on the given name
    """

    # Make the (per-source) config directory
    src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    os.system(f'mkdir -p {src_config_folder}')

    toml_template = f'{utils.get_folder("streams")}/spot_config.toml'
    toml_useful = f'{src_config_folder}/config.toml'

    # make source folder
    os.system(f'mkdir -p {src_config_folder}')

    # Copy the config template
    os.system(f'cp {toml_template} {toml_useful}')

    # Input the proper values
    self.connect_port = 4070 + 10 * vsrc
    with open(toml_useful, 'r', encoding='utf-8') as TOML:
      data = TOML.read()
      data = data.replace('device_name_in_spotify_connect', f'{self.name.replace(" ", "-")}')
      data = data.replace("alsa_audio_device", utils.virtual_output_device(vsrc))
      data = data.replace('1234', f'{self.connect_port}')
    with open(toml_useful, 'w', encoding='utf-8') as TOML:
      TOML.write(data)

    # PROCESS
    spotify_args = [f'{utils.get_folder("streams")}/spotifyd', '--no-daemon', '--config-path', './config.toml']

    try:
      self.proc = subprocess.Popen(args=spotify_args, cwd=f'{src_config_folder}')
      time.sleep(0.1) # Delay a bit

      self.mpris = MPRIS(f'spotifyd.instance{self.proc.pid}', f'v{vsrc}') # TODO: MPRIS should just need a path!

    except Exception as exc:
      print(f'error starting spotify: {exc}')

  def _deactivate(self):
    try:
      self.proc.kill()
    except Exception:
      pass
    try:
      del self.mpris
    except Exception:
      pass
    self.connect_port = None
    self.mpris = None
    self.proc = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url='static/imgs/spotify.png' # report generic spotify image in place of unspecified album art
    )
    if self.mpris is None:
      return source
    try:
      md = self.mpris.metadata()

      if not self.mpris.is_stopped():
        source.state = 'playing' if self.mpris.is_playing() else 'paused'
        source.artist = md.artist
        source.track = md.title
        source.album = md.album
        source.supported_cmds=self.supported_cmds
        if md.art_url:
          source.img_url = md.art_url

    except Exception as e:
      print(f"error in spotify: {e}")

    return source

  def send_cmd(self, cmd):
    try:
      if cmd in self.supported_cmds:
        if cmd == 'play':
          self.mpris.play()
        elif cmd == 'pause':
          self.mpris.pause()
        elif cmd == 'next':
          self.mpris.next()
        elif cmd == 'prev':
          self.mpris.previous()
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      raise Exception(f"Error sending command {cmd}: {e}") from e

class Pandora(PersistentStream):
  """ A Pandora Stream """
  def __init__(self, name: str, user, password: str, station: str, disabled: bool = False, mock: bool = False):
    super().__init__('pandora', name, disabled=disabled, mock=mock)
    self.user = user
    self.password = password
    self.station = station
    #if station is None:
    #  raise ValueError("station must be specified") # TODO: handle getting station list (it looks like you have to play a song before the station list gets updated through eventcmd)
    self.ctrl = '' # control fifo location
    self.supported_cmds = {
      'play':   {'cmd': 'P\n', 'state': 'playing'},
      'pause':  {'cmd': 'S\n', 'state': 'paused'},
      'stop':   {'cmd': 'q\n', 'state': 'stopped'},
      'next':   {'cmd': 'n\n', 'state': 'playing'},
      'love':   {'cmd': '+\n', 'state': None}, # love does not change state
      'ban':    {'cmd': '-\n', 'state': 'playing'},
      'shelve': {'cmd': 't\n', 'state': 'playing'},
    }

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    pb_fields = ['user', 'password', 'station']
    fields = list(pb_fields) + ['name']
    for k,v in kwargs.items():
      if k in fields and self.__dict__[k] != v:
        self.__dict__[k] = v
        if k in pb_fields:
          reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect pandora output to a given audio source
    This will start up pianobar with a configuration specific to @src
    """
    # make a special home/config to launch pianobar in (this allows us to have multiple pianobars)
    src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    eventcmd_template = f'{utils.get_folder("streams")}/eventcmd.sh'
    pb_home = src_config_folder
    pb_config_folder = f'{pb_home}/.config/pianobar'
    pb_control_fifo = f'{pb_config_folder}/ctl'
    pb_status_fifo = f'{pb_config_folder}/stat'
    pb_config_file = f'{pb_config_folder}/config'
    pb_output_file = f'{pb_config_folder}/output'
    pb_error_file = f'{pb_config_folder}/error'
    pb_eventcmd_file = f'{pb_config_folder}/eventcmd.sh'
    pb_src_config_file = f'{pb_home}/.libao'
    # make all of the necessary dir(s)
    os.system(f'mkdir -p {pb_config_folder}')
    os.system(f'cp {eventcmd_template} {pb_eventcmd_file}') # Copy to retain executable status
    # write pianobar and libao config files
    write_config_file(pb_config_file, {
      'user': self.user,
      'password': self.password,
      'autostart_station': self.station,
      'fifo': pb_control_fifo,
      'event_command': pb_eventcmd_file
    })
    write_config_file(pb_src_config_file, {'default_driver': 'alsa', 'dev': utils.virtual_output_device(vsrc)})
    # create fifos if needed
    if not os.path.exists(pb_control_fifo):
      os.system(f'mkfifo {pb_control_fifo}')
    if not os.path.exists(pb_status_fifo):
      os.system(f'mkfifo {pb_status_fifo}')
    # start pandora process in special home
    print(f'Pianobar config at {pb_config_folder}')
    try:
      self.proc = subprocess.Popen(args='pianobar', stdin=subprocess.PIPE, stdout=open(pb_output_file, 'w', encoding='utf-8'), stderr=open(pb_error_file, 'w', encoding='utf-8'), env={'HOME' : pb_home})
      time.sleep(0.1) # Delay a bit before creating a control pipe to pianobar
      self.ctrl = pb_control_fifo
      self.state = 'playing' # TODO: we need to pause pandora if it isn't playing anywhere
    except Exception as exc:
      print(f'error starting pianobar: {exc}')

  def _deactivate(self):
    if self._is_running():
      self.proc.kill()
    self.proc = None
    self.ctrl = ''

  def info(self) -> models.SourceInfo:
    src_config_folder = f'{utils.get_folder("config")}/srcs/v{self.vsrc}'
    loc = f'{src_config_folder}/.config/pianobar/currentSong'
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      supported_cmds=list(self.supported_cmds.keys()),
      img_url='static/imgs/pandora.png'
    )
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        for line in file.readlines():
          line = line.strip()
          if line:
            data = line.split(',,,')
            source.state = self.state
            source.artist = data[0]
            source.track = data[1]
            source.album = data[2]
            source.img_url = data[3]
            source.station = data[5]
        return source
    except Exception:
      pass
      #print(error('Failed to get currentSong - it may not exist: {}'.format(e)))
    # TODO: report the status of pianobar with station name, playing/paused, song info
    # ie. Playing: "Cameras by Matt and Kim" on "Matt and Kim Radio"
    return source

  def send_cmd(self, cmd):
    """ Pianobar's commands
      cmd: Command string sent to pianobar's control fifo
      state: Expected state after successful command execution
    """
    try:
      if cmd in self.supported_cmds:
        with open(self.ctrl, 'w', encoding='utf-8') as file:
          file.write(self.supported_cmds[cmd]['cmd'])
          file.flush()
        expected_state = self.supported_cmds[cmd]['state']
        if expected_state is not None:
          self.state = expected_state
      elif 'station' in cmd:
        station_id = int(cmd.replace('station=', ''))
        if station_id is not None:
          with open(self.ctrl, 'w', encoding='utf-8') as file:
            file.write('s')
            file.flush()
            file.write(f'{station_id}\n')
            file.flush()
          self.state = 'playing' # TODO: add verification (station could be wrong)
        else:
          raise ValueError(f'station=<int> expected, ie. station=23432423; received "{cmd}"')
      else:
        raise NotImplementedError(f'Command not recognized: {cmd}')
    except Exception as exc:
      raise RuntimeError(f'Command {cmd} failed to send: {exc}') from exc

class DLNA(BaseStream):
  """ A DLNA Stream """
  def __init__(self, name: str, disabled: bool = False, mock: bool = False):
    super().__init__('dlna', name, disabled=disabled, mock=mock)
    self.proc2 = None
    self.uuid = 0

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_running():
        last_src = self.src
        self.disconnect()
        time.sleep(0.1) # delay a bit, is this needed?
        self.connect(last_src)

  def __del__(self):
    self.disconnect()

  def connect(self, src):
    """ Connect a DLNA device to a given audio source
    This creates a DLNA streaming option based on the configuration
    """
    if self.mock:
      self._connect(src)
      return

    # Generate some of the DLNA_Args
    self.uuid = 0
    self.uuid = uuid_gen()
    portnum = 49494 + int(src)

    # Make the (per-source) config directory
    src_config_folder = f'{utils.get_folder("config")}/srcs/{src}'
    os.system(f'mkdir -p {src_config_folder}')

    meta_args = [f'{utils.get_folder("streams")}/dlna_metadata.bash', f'{src_config_folder}']
    dlna_args = ['gmediarender', '--gstout-audiosink', 'alsasink',
                '--gstout-audiodevice', utils.real_output_device(src), '--gstout-initial-volume-db',
                '0.0', '-p', f'{portnum}', '-u', f'{self.uuid}',
                '-f', f'{self.name}', '--logfile',
                f'{src_config_folder}/metafifo']
    self.proc = subprocess.Popen(args=meta_args, preexec_fn=os.setpgrp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.proc2 = subprocess.Popen(args=dlna_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self._connect(src)

  def disconnect(self):
    if self._is_running():
      os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
      self.proc2.kill()
    self._disconnect()
    self.proc = None
    self.proc2 = None

  def info(self) -> models.SourceInfo:
    src_config_folder = f'{utils.get_folder("config")}/srcs/{self.src}'
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(name=self.full_name(), state=self.state, img_url='static/imgs/dlna.png')
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        for line in file.readlines():
          line = line.strip()
          if line:
            d = ast.literal_eval(line)
        if 'state' in d:
          source.state = d['state']
        if 'album' in d:
          source.album = d['album']
        if 'artist' in d:
          source.artist = d['artist']
        if 'title' in d:
          source.track = d['title']
        return source
    except Exception:
      pass
    return source

class InternetRadio(BaseStream):
  """ An Internet Radio Stream """
  def __init__(self, name: str, url: str, logo: Optional[str], disabled: bool = False, mock: bool = False):
    super().__init__('internet radio', name, disabled=disabled, mock=mock)
    self.url = url
    self.logo = logo
    self.supported_cmds = ['play', 'stop']

  def reconfig(self, **kwargs):
    reconnect_needed = False
    ir_fields = ['url', 'logo']
    fields = list(ir_fields) + ['name', 'disabled']
    for k,v in kwargs.items():
      if k in fields and self.__dict__[k] != v:
        self.__dict__[k] = v
        if k in ir_fields:
          reconnect_needed = True
    if reconnect_needed and self._is_running():
      last_src = self.src
      self.disconnect()
      time.sleep(0.1) # delay a bit, is this needed?
      self.connect(last_src)

  def connect(self, src):
    """ Connect a VLC output to a given audio source
    This will create a VLC process based on the given name
    """
    print(f'connecting {self.name} to {src}...')

    if self.mock:
      print(f'{self.name} connected to {src}')
      self.state = 'playing'
      self.src = src
      return

    # Make all of the necessary dir(s)
    src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system(f'mkdir -p {src_config_folder}')

    # Start audio via runvlc.py
    song_info_path = f'{src_config_folder}/currentSong'
    log_file_path = f'{src_config_folder}/log'
    inetradio_args = [sys.executable, f"{utils.get_folder('streams')}/runvlc.py", self.url, utils.real_output_device(src), '--song-info', song_info_path, '--log', log_file_path]
    print(f'running: {inetradio_args}')
    self.proc = subprocess.Popen(args=inetradio_args, preexec_fn=os.setpgrp)

    print(f'{self.name} (stream: {self.url}) connected to {src} via {utils.real_output_device(src)}')
    self.state = 'playing'
    self.src = src

  def disconnect(self):
    if self._is_running():
      self.proc.kill()
    self._disconnect()
    self.proc = None

  def info(self) -> models.SourceInfo:
    src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(name=self.full_name(),
                              state=self.state,
                              img_url='static/imgs/internet_radio.png',
                              supported_cmds=self.supported_cmds)
    if self.logo:
      source.img_url = self.logo
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        source.artist = data['artist']
        source.track = data['track']
        source.station = data['station']
        return source
    except Exception:
      pass
    return source

  def send_cmd(self, cmd):
    try:
      if cmd in self.supported_cmds and self.src != None:
        if cmd == 'play':
          if not self._is_running():
            self.connect(self.src)
        elif cmd == 'stop':
          if self._is_running():
            try:
              self.proc.kill()
              self.proc = None
              src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
              song_info_path = f'{src_config_folder}/currentSong'
              os.system(f'rm {song_info_path}')
            except Exception:
              pass
          self.state = 'stopped'
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception:
      pass

class Plexamp(BaseStream):
  """ A Plexamp Stream
  TODO: old plexamp interface was disabled, integrate support for new PlexAmp
  """
  def __init__(self, name: str, client_id, token, disabled: bool = False, mock: bool = False):
    super().__init__('plexamp', name, disabled=disabled, mock=mock)

  def reconfig(self, **kwargs):
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs:
      self.disabled = kwargs['name']

  def connect(self, src):
    """ Connect plexamp output to a given audio source
    This will start up plexamp with a configuration specific to @src
    """
    if self.mock:
      self._connect(src)
      return

  def disconnect(self):
    self._disconnect()

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(name=self.full_name(), state=self.state, img_url='static/imgs/plexamp.png')
    source.track = "Not currently supported"
    return source

class FilePlayer(BaseStream):
  """ An Single one shot file player - initially intended for use as a part of the PA Announcements """
  def __init__(self, name: str, url: str, disabled: bool = False, mock: bool = False):
    super().__init__('file player', name, disabled=disabled, mock=mock)
    self.url = url
    self.bkg_thread = None

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs:
      self.name = kwargs['name']
    if 'url' in kwargs:
      self.url = kwargs['url']
      reconnect_needed = True
    if reconnect_needed:
      last_src = self.src
      self.disconnect()
      time.sleep(0.1) # delay a bit, is this needed?
      self.connect(last_src)

  def connect(self, src):
    """ Connect a short run VLC process with audio output to a given audio source """
    print(f'connecting {self.name} to {src}...')

    if self.mock:
      self._connect(src)
      # make a thread that waits for a couple of secends and returns after setting info to stopped
      self.bkg_thread = threading.Thread(target=self.wait_on_proc)
      self.bkg_thread.start()
      return

    # Start audio via runvlc.py
    vlc_args = f'cvlc -A alsa --alsa-audio-device {utils.real_output_device(src)} {self.url} vlc://quit'
    print(f'running: {vlc_args}')
    self.proc = subprocess.Popen(args=vlc_args.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self._connect(src)
    # make a thread that waits for a couple of secends and returns after setting info to stopped
    self.bkg_thread = threading.Thread(target=self.wait_on_proc)
    self.bkg_thread.start()
    return

  def wait_on_proc(self):
    """ Wait for the vlc process to finish """
    if self.proc is not None:
      self.proc.wait() # TODO: add a time here
    else:
      time.sleep(0.3) # handles mock case
    self.state = 'stopped' # notify that the audio is done playing

  def disconnect(self):
    if self._is_running():
      self.proc.kill()
      if self.bkg_thread:
        self.bkg_thread.join()
    self.proc = None
    self._disconnect()

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(name=self.full_name(), state=self.state, img_url='static/imgs/plexamp.png')
    return source

class FMRadio(BaseStream):
  """ An FMRadio Stream using RTLSDR """
  def __init__(self, name: str, freq, logo: Optional[str] = None, disabled: bool = False, mock: bool = False):
    super().__init__('fm radio', name, disabled=disabled, mock=mock)
    self.freq = freq
    self.logo = logo

  def reconfig(self, **kwargs):
    reconnect_needed = False
    ir_fields = ['freq', 'logo']
    fields = list(ir_fields) + ['name', 'disabled']
    for k, v in kwargs.items():
      if k in fields and self.__dict__[k] != v:
        self.__dict__[k] = v
        if k in ir_fields:
          reconnect_needed = True
    if reconnect_needed and self._is_running():
      last_src = self.src
      self.disconnect()
      time.sleep(0.1) # delay a bit, is this needed?
      self.connect(last_src)

  def connect(self, src):
    """ Connect a fmradio.py output to a given audio source """

    if self.mock:
      self._connect(src)
      return

    # Make all of the necessary dir(s)
    src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system('mkdir -p {}'.format(src_config_folder))
    song_info_path = f'{src_config_folder}/currentSong'
    log_file_path = f'{src_config_folder}/log'

    fmradio_args = [sys.executable, f"{utils.get_folder('streams')}/fmradio.py", self.freq, utils.real_output_device(src), '--song-info', song_info_path, '--log', log_file_path]
    print(f'running: {fmradio_args}')
    self.proc = subprocess.Popen(args=fmradio_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setpgrp)
    self._connect(src)

  def _is_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_running():
      os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
    self.proc = None
    self._disconnect()

  def info(self) -> models.SourceInfo:
    src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
    loc = f'{src_config_folder}/currentSong'
    if not self.logo:
      self.logo = "static/imgs/fmradio.png"
    source = models.SourceInfo(name=self.full_name(), state=self.state, img_url=self.logo)
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        # Example JSON: "station": "Mixx96.1", "callsign": "KXXO", "prog_type": "Soft rock", "radiotext": "        x96.1"
        #print(json.dumps(data))
        if data['prog_type']:
          source.artist = data['prog_type']
        else:
          source.artist = self.freq + " FM"

        if data['radiotext']:
          source.track = data['radiotext']
        else:
          source.track = self.name

        if data['station']:
          source.station = data['station']
        elif data['callsign']:
          source.station = data['callsign']
        else:
          source.station = ""

        return source
    except Exception:
      pass
      #print('Failed to get currentSong - it may not exist: {}'.format(e))
    return source

class LMS(PersistentStream):
  """ An LMS Stream using squeezelite"""
  def __init__(self, name: str, server: Optional[str] = None, disabled: bool = False, mock: bool = False):
    super().__init__('lms', name, disabled=disabled, mock=mock)
    self.server : Optional[str] = server

  def is_persistent(self):
    return True

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if 'server' in kwargs and kwargs['server'] != self.server:
      self.server = kwargs['server']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_running():
        self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect a sqeezelite output to a given audio source
    This will create a LMS client based on the given name
    """
    try:
      # Make the (per-source) config directory
      src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
      os.system(f'mkdir -p {src_config_folder}')

      # TODO: Add metadata support? This may have to watch the output log?

      # mac address, needs to be unique but not tied to actual NIC MAC hash the name with src id, to avoid aliases on move
      md5 = hashlib.md5()
      md5.update(self.name.encode('utf-8'))
      md5_hex = md5.hexdigest()
      fake_mac = ':'.join([md5_hex[i:i+2] for i in range(0, 12, 2)])

      # Process
      lms_args = [f'{utils.get_folder("streams")}/squeezelite',
                  '-n', self.name,
                  '-m', fake_mac,
                  '-o', utils.virtual_output_device(vsrc),
                  '-f', f'{src_config_folder}/lms_log.txt',
                  '-i', f'{src_config_folder}/lms_remote', # specify this to avoid collisions, even if unused
                ]
      if self.server:
        # specify the server to connect to (if unspecified squeezelite starts in discovery mode)
        server = self.server
        # some versions of amplipi have an LMS server embedded, using localhost avoids hardcoding the hostname
        if 'localhost' ==  server:
          # squeezelite does not support localhost and requires the actual hostname
          # NOTE: port 9000 is assumed
          server.replace('localhost', socket.gethostname())
        lms_args += [ '-s', server]
      # TODO: allow port to be specified with server (embedding it in the server URL does not work)

      self.proc = subprocess.Popen(args=lms_args)
    except Exception as exc:
      print(f'error starting lms: {exc}')

  def _deactivate(self):
    if self._is_running():
      self.proc.kill()
    self.proc = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url='static/imgs/lms.png',
      track='check LMS for song info',
    )
    return source

class Bluetooth(BaseStream):
  """ A source for Bluetooth streams, which requires an external Bluetooth USB dongle """

  def __init__(self, name, disabled=False, mock=False):
    super().__init__('bluetooth', name, disabled=disabled, mock=mock)
    self.logo = "static/imgs/bluetooth.png"
    self.bt_proc = None
    self.supported_cmds = ['play', 'pause', 'next', 'prev', 'stop']

  def __del__(self):
    self.disconnect()

  @staticmethod
  def is_hw_available():
    """Determines if a bluetooth dongle is present"""
    try:
      if subprocess.run('which bluetoothctl'.split(), check=False).returncode != 0:
        return False
      # bluetoothctl show seems to hang sometimes when hardware is not available
      # add a timeout so that we don't get stuck waiting
      btcmd_proc = subprocess.run('bluetoothctl show'.split(), check=True, stdout=subprocess.PIPE, timeout=0.5)
      return 'No default controller available' not in btcmd_proc.stdout.decode('utf-8')
    except Exception as e:
      if 'timed out' not in str(e): # a timeout indicates bluetooth module is missing
        print(f'Error checking for bluetooth hardware: {e}')
      return False

  def connect(self, src):
    """ Connect a bluealsa-aplay process with audio output to a given audio source """
    print(f'connecting {self.name} to {src}...')

    if self.mock:
      self._connect(src)
      return

    # Power on Bluetooth and enable discoverability
    subprocess.run(args='bluetoothctl power on'.split(), preexec_fn=os.setpgrp)
    subprocess.run(args='bluetoothctl discoverable on'.split(), preexec_fn=os.setpgrp)
    subprocess.run(args='sudo btmgmt fast-conn on'.split(), preexec_fn=os.setpgrp)

    # Start metadata watcher
    src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system(f'mkdir -p {src_config_folder}')
    song_info_path = f'{src_config_folder}/currentSong'
    device_info_path = f'{src_config_folder}/btDevice'
    btmeta_args = f'{sys.executable} {utils.get_folder("streams")}/bluetooth.py --song-info={song_info_path} ' \
                  f'--device-info={device_info_path} --output-device={utils.output_device(src)}'
    self.bt_proc = subprocess.Popen(args=btmeta_args.split(), preexec_fn=os.setpgrp)

    self._connect(src)
    return

  def _is_running(self):
    if self.bt_proc:
      return self.bt_proc.poll() is None
    return False

  def disconnect(self):
    if self._is_running():
      os.killpg(os.getpgid(self.bt_proc.pid), signal.SIGKILL)
      self.bt_proc = None

      # Power off Bluetooth and disable discoverability
      subprocess.run(args='bluetoothctl discoverable off'.split(), preexec_fn=os.setpgrp)
      subprocess.run(args='bluetoothctl power off'.split(), preexec_fn=os.setpgrp)

      self._disconnect()

  def info(self) -> models.SourceInfo:
    src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(name=self.full_name(),
                               state=self.state,
                               img_url=self.logo,
                               supported_cmds=self.supported_cmds)
    try:
      with open(loc, 'r') as file:
        data = json.loads(file.read())
        source.artist = data['artist']
        source.track = data['title']
        source.album = data['album']
        source.state = data['status']
        return source
    except Exception as e:
      print(f'bluetooth: exception {e}')
      traceback.print_exc()
    return source

  def send_cmd(self, cmd):
    print(f'bluetooth: sending command {cmd}')
    try:
      if cmd in self.supported_cmds and self.src is not None:
        src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
        device_info_path = f'{src_config_folder}/btDevice'
        btcmd_args = f'{sys.executable} {utils.get_folder("streams")}/bluetooth.py --command={cmd} --device-info={device_info_path}'
        subprocess.run(args=btcmd_args.split(), preexec_fn=os.setpgrp)
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      print(f'bluetooth: exception {e}')
      raise RuntimeError(f'Command {cmd} failed to send: {e}') from e
      traceback.print_exc()

# Simple handling of stream types before we have a type heirarchy
AnyStream = Union[RCA, AirPlay, Spotify, InternetRadio, DLNA, Pandora, Plexamp,
                  FilePlayer, FMRadio, LMS, Bluetooth]

def build_stream(stream: models.Stream, mock=False) -> AnyStream:
  """ Build a stream from the generic arguments given in stream, discriminated by stream.type

  we are waiting on Pydantic's implemenatation of discriminators to fully integrate streams into our model definitions
  """
  # pylint: disable=too-many-return-statements
  args = stream.dict(exclude_none=True)
  name = args.pop('name')
  disabled = args.pop('disabled', False)
  if stream.type == 'rca':
    return RCA(name, args['index'], disabled=disabled, mock=mock)
  if stream.type == 'pandora':
    return Pandora(name, args['user'], args['password'], station=args.get('station', None), disabled=disabled, mock=mock)
  if stream.type in ['shairport', 'airplay']: # handle older configs
    return AirPlay(name, args.get('ap2', False), disabled=disabled, mock=mock)
  if stream.type == 'spotify':
    return Spotify(name, disabled=disabled, mock=mock)
  if stream.type == 'dlna':
    return DLNA(name, disabled=disabled, mock=mock)
  if stream.type == 'internetradio':
    return InternetRadio(name, args['url'], args.get('logo'), disabled=disabled, mock=mock)
  if stream.type == 'plexamp':
    return Plexamp(name, args['client_id'], args['token'], disabled=disabled, mock=mock)
  if stream.type == 'fileplayer':
    return FilePlayer(name, args['url'], disabled=disabled, mock=mock)
  if stream.type == 'fmradio':
    return FMRadio(name, args['freq'], args.get('logo'), disabled=disabled, mock=mock)
  if stream.type == 'lms':
    return LMS(name, args.get('server'), disabled=disabled, mock=mock)
  elif stream.type == 'bluetooth':
    return Bluetooth(name, disabled=disabled, mock=mock)
  raise NotImplementedError(stream.type)
