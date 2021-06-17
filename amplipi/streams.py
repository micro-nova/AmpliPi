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

"""Digital Audio Streams

This module allows you to connect and control configurable network audio sources
such as Pandora, Spotify, and Airplay. Each digital source is expected to have
a consistent interface.
"""

import os
import sys
import subprocess
import time
from typing import Union

# Used by InternetRadio
import json
import signal

import amplipi.models as models
import amplipi.utils as utils

# TODO: how to implement base stream class in Python?, there is a lot of duplication between shairport and pandora streams...
#class Stream:
#  def connect(self, src):
#    """ Connect the stream's output to src """
#    return None
#  def disconnect(self):
#    """ Disconnect the stream's output from any connected source """
#    return None
#  def status(self):
#    return 'Status not available'

def write_config_file(filename, config):
  """ Write a simple config file (@filename) with key=value pairs given by @config """
  with open(filename, 'wt') as cfg_file:
    for key, value in config.items():
      cfg_file.write('{}={}\n'.format(key, value))

def write_sp_config_file(filename, config):
  """ Write a shairport config file (@filename) with a hierarchy of grouped key=value pairs given by @config """
  with open(filename, 'wt') as cfg_file:
    for group, gconfig in config.items():
      cfg_file.write('{} =\n{{\n'.format(group))
      for key, value in gconfig.items():
        if type(value) is str:
          cfg_file.write('  {} = "{}"\n'.format(key, value))
        else:
          cfg_file.write('  {} = {}\n'.format(key, value))
      cfg_file.write('};\n')

def uuid_gen():
  # Get new UUID for the DLNA endpoint
  u_args = 'uuidgen'
  uuid_proc = subprocess.run(args=u_args, capture_output=True)
  uuid_str = str(uuid_proc).split(',')
  c_check = uuid_str[0]
  val = uuid_str[2]

  if c_check[0:16] == 'CompletedProcess':
    return val[10:46]
  else:
    return '39ae35cc-b4c1-444d-b13a-294898d771fa' # Generic UUID in case of failure

class Shairport:
  """ An Airplay Stream """
  def __init__(self, name, mock=False):
    self.name = name
    self.proc = None
    self.proc2 = None
    self.mock = mock
    self.src = None
    self.state = 'disconnected'
    # TODO: see here for adding play/pause functionality: https://github.com/mikebrady/shairport-sync/issues/223
    # TLDR: rebuild with some flag and run shairport-sync as a daemon, then use another process to control it

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_sp_running():
        last_src = self.src
        self.disconnect()
        time.sleep(0.1) # delay a bit, is this needed?
        self.connect(last_src)

  def __del__(self):
    self.disconnect()

  def connect(self, src):
    """ Connect an Airplay device to a given audio source
    This creates an Airplay streaming option based on the configuration
    """
    if self.mock:
      print('{} connected to {}'.format(self.name, src))
      self.state = 'connected'
      self.src = src
      return
    config = {
      'general': {
        'name': self.name,
        'port': 5100 + 100 * src, # Listen for service requests on this port
        'udp_port_base': 6101 + 100 * src, # start allocating UDP ports from this port number when needed
        'drift': 2000, # allow this number of frames of drift away from exact synchronisation before attempting to correct it
        'resync_threshold': 0, # a synchronisation error greater than this will cause resynchronisation; 0 disables it
        'log_verbosity': 0, # "0" means no debug verbosity, "3" is most verbose.
      },
      'metadata':{
        'enabled': 'yes',
        'include_cover_art': 'yes',
        'pipe_name': '{}/srcs/{}/shairport-sync-metadata'.format(utils.get_folder('config'), src),
        'pipe_timeout': 5000,
      },
      'alsa': {
        'output_device': utils.output_device(src), # alsa output device
        'audio_backend_buffer_desired_length': 11025 # If set too small, buffer underflow occurs on low-powered machines. Too long and the response times with software mixer become annoying.
      },
    }
    src_config_folder = '{}/srcs/{}'.format(utils.get_folder('config'), src)
    web_dir = f"{utils.get_folder('web/generated')}/shairport/srcs/{src}"
    # make all of the necessary dir(s)
    os.system('rm -r -f {}'.format(web_dir))
    os.system('mkdir -p {}'.format(web_dir))
    os.system('mkdir -p {}'.format(src_config_folder))
    config_file = '{}/shairport.conf'.format(src_config_folder)
    write_sp_config_file(config_file, config)
    shairport_args = 'shairport-sync -c {}'.format(config_file).split(' ')
    meta_args = [f"{utils.get_folder('streams')}/shairport_metadata.bash", src_config_folder, web_dir]
    print(f'shairport_args: {shairport_args}')
    print(f'meta_args: {meta_args}')
    # TODO: figure out how to get status from shairport
    self.proc = subprocess.Popen(args=shairport_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.proc2 = subprocess.Popen(args=meta_args, preexec_fn=os.setpgrp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print('{} connected to {}'.format(self.name, src))
    self.state = 'connected'
    self.src = src

  def _is_sp_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_sp_running():
      os.killpg(os.getpgid(self.proc2.pid), signal.SIGKILL)
      self.proc.kill()
      print('{} disconnected'.format(self.name))
    self.state = 'disconnected'
    self.proc2 = None
    self.proc = None
    self.src = None

  def info(self) -> models.SourceInfo:
    src_config_folder = '{}/srcs/{}'.format(utils.get_folder('config'), self.src)
    loc = '{}/currentSong'.format(src_config_folder)
    source = models.SourceInfo()
    source.img_url = f"{utils.get_folder('web/static')}/imgs/shairport.png"
    try:
      with open(loc, 'r') as file:
        for line in file.readlines():
          if line:
            data = line.strip('".').split(',,,')
            source.artist = data[0]
            source.track = data[1]
            source.album = data[2]
            source.state = data[3]
            if int(data[4]):
              source.img_url = f"{utils.get_folder('web/generated')}/shairport/srcs/{self.src}/{data[5]}"
    except Exception:
      pass
      # TODO: Log actual exception here?
    return source

  def status(self):
    return self.state

  def __str__(self):
    connection = ' connected to src={}'.format(self.src) if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return 'airplay: {}{}{}'.format(self.name, connection, mock)

class Spotify:
  """ A Spotify Stream """
  def __init__(self, name, mock=False):
    self.name = name
    self.proc = None
    self.mock = mock
    self.src = None
    self.state = 'disconnected'

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_spot_running():
        last_src = self.src
        self.disconnect()
        time.sleep(0.1) # delay a bit, is this needed?
        self.connect(last_src)

  def __del__(self):
    self.disconnect()

  def connect(self, src):
    """ Connect a Spotify output to a given audio source
    This will create a Spotify Connect device based on the given name
    """
    if self.mock:
      print('{} connected to {}'.format(self.name, src))
      self.state = 'connected'
      self.src = src
      return
    # TODO: Figure out the config for Spotify. Potentially need to get song info & play/pause ctrl
    spotify_args = ['librespot', '-n', '{}'.format(self.name), '--device', utils.output_device(src), '--initial-volume', '100']
    self.proc = subprocess.Popen(args=spotify_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print('{} connected to {}'.format(self.name, src))
    self.state = 'connected'
    self.src = src

  def _is_spot_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_spot_running():
      self.proc.kill()
      print('{} disconnected'.format(self.name))
    self.state = 'disconnected'
    self.proc = None
    self.src = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/spotify.png")
    return source

  def status(self):
    return self.state

  def __str__(self):
    connection = ' connected to src={}'.format(self.src) if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return 'spotify connect: {}{}{}'.format(self.name, connection, mock)

class Pandora:
  """ A Pandora Stream """

  class Control:
    """ Controlling a running pianobar instance via its fifo control """
    def __init__(self, pb_fifo='.config/pianobar/ctl'):
      # open the CTL fifo ('ctl' name specified in pianobar 'config' file)
      self.fifo = open(pb_fifo, 'w')
      print('Controlling pianobar with FIFO = {}'.format(pb_fifo))
      self.state = 'unknown'
    def __del__(self):
      if self.fifo:
        self.fifo.close()
    def play(self):
      self.fifo.write('P\n') # Exclusive 'play' instead of 'p'
      self.fifo.flush()
      self.state = 'playing'
    def pause(self):
      self.fifo.write('S\n') # Exclusive 'pause'
      self.fifo.flush()
      self.state = 'paused'
    def stop(self):
      self.fifo.write('q\n')
      self.fifo.flush()
      self.state = 'stopped'
    def next(self):
      self.fifo.write('n\n')
      self.fifo.flush()
    def love(self):
      self.fifo.write('+\n')
      self.fifo.flush()
    def ban(self):
      self.fifo.write('-\n')
      self.fifo.flush()
    def shelve(self):
      self.fifo.write('t\n')
      self.fifo.flush()
    def station(self, index):
      self.fifo.write('s')
      self.fifo.flush()
      self.fifo.write('{}\n'.format(index))
      self.fifo.flush()

  def __init__(self, name, user, password, station, mock=False):
    self.name = name
    self.user = user
    self.mock = mock
    self.password = password
    self.station = station
    #if station is None:
    #  raise ValueError("station must be specified") # TODO: handle getting station list (it looks like you have to play a song before the station list gets updated through eventcmd)
    self.proc = None  # underlying pianobar process
    self.ctrl = None # control fifo to pianobar
    self.state = 'disconnected'
    self.src = None # source_id pianobar is connecting to

  def reconfig(self, **kwargs):
    reconnect_needed = False
    pb_fields = ['user', 'password', 'station']
    fields = list(pb_fields) + ['name']
    for k,v in kwargs.items():
      if k in fields and self.__dict__[k] != v:
        self.__dict__[k] = v
        if k in pb_fields:
          reconnect_needed = True
    if reconnect_needed and self._is_pb_running():
      last_src = self.src
      self.disconnect()
      time.sleep(0.1) # delay a bit, is this needed?
      self.connect(last_src)

  def __del__(self):
    self.disconnect()

  def __str__(self):
    connection = ' connected to src={}'.format(self.src) if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return 'pandora: {}{}{}'.format(self.name, connection, mock )

  def connect(self, src):
    """ Connect pandora output to a given audio source
    This will start up pianobar with a configuration specific to @src
    """
    if self.mock:
      print('{} connected to {}'.format(self.name, src))
      self.src = src
      self.state = 'connected'
      return
    # TODO: future work, make pandora and shairport use audio fifos that makes it simple to switch their sinks
    # make a special home, with specific config to launch pianobar in (this allows us to have multiple pianobars)

    src_config_folder = '{}/srcs/{}'.format(utils.get_folder('config'), src)
    eventcmd_template = '{}/eventcmd.sh'.format(utils.get_folder('streams'))
    pb_home = src_config_folder
    pb_config_folder = '{}/.config/pianobar'.format(pb_home)
    pb_control_fifo = '{}/ctl'.format(pb_config_folder)
    pb_status_fifo = '{}/stat'.format(pb_config_folder)
    pb_config_file = '{}/config'.format(pb_config_folder)
    pb_output_file = '{}/output'.format(pb_config_folder)
    pb_error_file = '{}/error'.format(pb_config_folder)
    pb_eventcmd_file = '{}/eventcmd.sh'.format(pb_config_folder)
    pb_src_config_file = '{}/.libao'.format(pb_home)
    # make all of the necessary dir(s)
    os.system('mkdir -p {}'.format(pb_config_folder))
    os.system('cp {} {}'.format(eventcmd_template, pb_eventcmd_file)) # Copy to retains necessary executable status
    # write pianobar and libao config files
    write_config_file(pb_config_file, {
      'user': self.user,
      'password': self.password,
      'autostart_station': self.station,
      'fifo': pb_control_fifo,
      'event_command': pb_eventcmd_file
    })
    write_config_file(pb_src_config_file, {'default_driver': 'alsa', 'dev': utils.output_device(src)})
    # create fifos if needed
    if not os.path.exists(pb_control_fifo):
      os.system('mkfifo {}'.format(pb_control_fifo))
    if not os.path.exists(pb_status_fifo):
      os.system('mkfifo {}'.format(pb_status_fifo))
    # start pandora process in special home
    print('Pianobar config at {}'.format(pb_config_folder))
    try:
      self.proc = subprocess.Popen(args='pianobar', stdin=subprocess.PIPE, stdout=open(pb_output_file, 'w'), stderr=open(pb_error_file, 'w'), env={'HOME' : pb_home})
      time.sleep(0.1) # Delay a bit before creating a control pipe to pianobar
      self.ctrl = Pandora.Control(pb_control_fifo)
      self.src = src
      self.state = 'connected'
      print('{} connected to {}'.format(self.name, src))
    except Exception as e:
      print('error starting pianobar: {}'.format(e))

  def _is_pb_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_pb_running():
      self.ctrl.stop()
      self.proc.kill()
      print('{} disconnected'.format(self.name))
    self.state = 'disconnected'
    self.proc = None
    self.ctrl = None
    self.src = None

  def info(self) -> models.SourceInfo:
    src_config_folder = '{}/srcs/{}'.format(utils.get_folder('config'), self.src)
    loc = '{}/.config/pianobar/currentSong'.format(src_config_folder)
    source = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/pandora.png")
    try:
      with open(loc, 'r') as file:
        for line in file.readlines():
          line = line.strip()
          if line:
            data = line.split(',,,')
            if self.ctrl is not None and self.ctrl.state == 'unknown':
              self.ctrl.state = 'playing' # guess that the song is playing
            source.state = self.ctrl.state
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

  def status(self):
    return self.state

class DLNA:
  """ A DLNA Stream """
  def __init__(self, name, mock=False):
    self.name = name
    self.proc = None
    self.proc2 = None
    self.mock = mock
    self.src = None
    self.state = 'disconnected'
    self.uuid = 0

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_dlna_running():
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
      print(f'{self.name} connected to {src}')
      self.state = 'connected'
      self.src = src
      return

    # Generate some of the DLNA_Args
    self.uuid = 0
    self.uuid = uuid_gen()
    portnum = 49494 + int(src)

    src_config_folder = f'{utils.get_folder("config")}/srcs/{src}'
    meta_args = [f'{utils.get_folder("streams")}/dlna_metadata.bash', f'{src_config_folder}']
    dlna_args = ['gmediarender', '--gstout-audiosink', 'alsasink',
                '--gstout-audiodevice', utils.output_device(src), '--gstout-initial-volume-db',
                '0.0', '-p', f'{portnum}', '-u', f'{self.uuid}',
                '-f', f'{self.name}', '--logfile',
                f'{src_config_folder}/metafifo']
    self.proc = subprocess.Popen(args=meta_args, preexec_fn=os.setpgrp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.proc2 = subprocess.Popen(args=dlna_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'{self.name} connected to {src}')
    self.state = 'connected'
    self.src = src

  def _is_dlna_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_dlna_running():
      os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
      self.proc2.kill()
      print(f'{self.name} disconnected')
    self.state = 'disconnected'
    self.proc = None
    self.proc2 = None
    self.src = None

  def info(self) -> models.SourceInfo:
    src_config_folder = f'{utils.get_folder("config")}/srcs/{self.src}'
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/dlna.png")
    try:
      with open(loc, 'r') as file:
        for line in file.readlines():
          line = line.strip()
          if line:
            d = eval(line)
            # TODO: what fields are populated by gmrenderer?
        return source
    except Exception:
      pass
    return source

  def status(self):
    return self.state

  def __str__(self):
    connection = f' connected to src={self.src}' if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return f'DLNA: {self.name}{connection}{mock}'

class InternetRadio:
  """ An Internet Radio Stream """
  def __init__(self, name, url, logo, mock=False):
    self.name = name
    self.url = url
    self.logo = logo
    self.proc = None
    self.mock = mock
    self.src = None
    self.state = 'disconnected'

  def reconfig(self, **kwargs):
    reconnect_needed = False
    ir_fields = ['url', 'logo']
    fields = list(ir_fields) + ['name']
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

  def __del__(self):
    self.disconnect()

  def connect(self, src):
    """ Connect a VLC output to a given audio source
    This will create a VLC process based on the given name
    """
    print(f'connecting {self.name} to {src}...')

    if self.mock:
      print(f'{self.name} connected to {src}')
      self.state = 'connected'
      self.src = src
      return

    # Make all of the necessary dir(s)
    src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system('mkdir -p {}'.format(src_config_folder))

    # Start audio via runvlc.py
    song_info_path = f'{src_config_folder}/currentSong'
    log_file_path = f'{src_config_folder}/log'
    inetradio_args = [sys.executable, f"{utils.get_folder('streams')}/runvlc.py", self.url, utils.output_device(src), '--song-info', song_info_path, '--log', log_file_path]
    print(f'running: {inetradio_args}')
    self.proc = subprocess.Popen(args=inetradio_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setpgrp)

    print(f'{self.name} (stream: {self.url}) connected to {src} via {utils.output_device(src)}')
    self.state = 'connected'
    self.src = src

  def _is_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_running():
      self.proc.kill()
      print(f'{self.name} disconnected')
    self.state = 'disconnected'
    self.proc = None
    self.src = None

  def info(self) -> models.SourceInfo:
    src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(img_url=self.logo)
    try:
      with open(loc, 'r') as file:
        data = json.loads(file.read())
        source.artist = data['artist']
        source.track = data['track']
        source.station = data['station']
        return source
    except Exception:
      pass
      #print('Failed to get currentSong - it may not exist: {}'.format(e))
    # TODO: report the status of pianobar with station name, playing/paused, song info
    # ie. Playing: "Cameras by Matt and Kim" on "Matt and Kim Radio"
    return source

  def status(self):
    return self.state

  def __str__(self):
    connection = f' connected to src={self.src}' if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return 'internetradio connect: {self.name}{connection}{mock}'

class Plexamp:
  """ A Plexamp Stream """

  def __init__(self, name, client_id, token, mock=False):
    self.name = name
    self.client_id = client_id
    self.token = token
    self.mock = mock
    self.proc = None  # underlying plexamp process
    self.state = 'disconnected'
    self.src = None # source_id plexamp is connecting to

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_plexamp_running():
        last_src = self.src
        self.disconnect()
        time.sleep(0.1) # delay a bit, is this needed?
        self.connect(last_src)

  def __del__(self):
    self.disconnect()

  def __str__(self):
    connection = f' connected to src={self.src}' if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return f'plexamp: {self.name}{connection}{mock}'

  def connect(self, src):
    """ Connect plexamp output to a given audio source
    This will start up plexamp with a configuration specific to @src
    """
    if self.mock:
      print(f'{self.name} connected to {src}')
      self.state = 'connected'
      self.src = src
      return

    src_config_folder = f'{utils.get_folder("config")}/srcs/{src}'
    mpd_template = f'{utils.get_folder("streams")}/mpd.conf'
    plexamp_template = f'{utils.get_folder("streams")}/server.json'
    plexamp_home = src_config_folder
    plexamp_config_folder = f'{plexamp_home}/.config/Plexamp'
    mpd_conf_file = f'{plexamp_home}/mpd.conf'
    server_json_file = f'{plexamp_config_folder}/server.json'
    # make all of the necessary dir(s)
    os.system(f'mkdir -p {plexamp_config_folder}')
    os.system(f'cp {mpd_template} {mpd_conf_file}')
    os.system(f'cp {plexamp_template} {server_json_file}')
    self.uuid = uuid_gen()
    # server.json config (Proper server.json file must be copied over for this to work)
    with open(server_json_file) as json_file:
      contents = json.load(json_file)
      r_token = contents['user']['token']
      if r_token != '_': # Dummy value from template
        self.token = r_token

    # Double quotes required for Python -> JSON translation
    json_config = {
      "player": {
        "name": f"{self.name}",
        "identifier": f"{self.client_id}"
      },
      "user": {
        "token": self.token
      },
      "state": "null",
      "server": "null",
      "audio": {
        "normalize": "false",
        "crossfade": "false",
        "mpd_path": f"{mpd_conf_file}"
      }
    }

    with open(server_json_file, 'w') as new_json:
      json.dump(json_config, new_json, indent=2)

    # mpd.conf creation
    with open(mpd_conf_file, 'r') as MPD:
      data = MPD.read()
      data = data.replace('ch', f'ch{src}')
      data = data.replace('GENERIC_LOGFILE_LOCATION', f'{plexamp_config_folder}/mpd.log')
    with open(mpd_conf_file, 'w') as MPD:
      MPD.write(data)
    # PROCESS
    plexamp_args = ['/usr/bin/node', '/home/pi/plexamp/server/server.prod.js']
    try:
      self.proc = subprocess.Popen(args=plexamp_args, preexec_fn=os.setpgrp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'HOME' : plexamp_home})
      time.sleep(0.1) # Delay a bit
      self.src = src
      print(f'{self.name} connected to {src}')
    except Exception as e:
      print(f'error starting plexamp: {e}')

  def _is_plexamp_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def disconnect(self):
    if self._is_plexamp_running():
      os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
      print(f'{self.name} disconnected')
    self.state = 'disconnected'
    self.proc = None
    self.src = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(img_url=f"{utils.get_folder('web/static')}/imgs/plexamp.png")
    return source

  def status(self):
    return self.state

# Simple handling of stream types before we have a type heirarchy
AnyStream = Union[Shairport, Spotify, InternetRadio, DLNA, Pandora, Plexamp]

def build_stream(stream: models.Stream, mock=False) -> AnyStream:
  """ Build a stream from the generic arguments given in stream, discriminated by stream.type

  we are waiting on Pydantic's implemenatation of discriminators to fully integrate streams into our model definitions
  """
  args = stream.dict(exclude_none=True)
  if stream.type == 'pandora':
    return Pandora(args['name'], args['user'], args['password'], station=args.get('station'), mock=mock)
  elif stream.type == 'shairport':
    return Shairport(args['name'], mock=mock)
  elif stream.type == 'spotify':
    return Spotify(args['name'], mock=mock)
  elif stream.type == 'dlna':
    return DLNA(args['name'], mock=mock)
  elif stream.type == 'internetradio':
    return InternetRadio(args['name'], args['url'], args['logo'], mock=mock)
  elif stream.type == 'plexamp':
    return Plexamp(args['name'], args['client_id'], args['token'], mock=mock)
  raise NotImplementedError(stream.type)

