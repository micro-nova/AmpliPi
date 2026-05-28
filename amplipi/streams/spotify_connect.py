

import io
import os
import threading
import re
import sys
import subprocess
import time
from typing import ClassVar, Optional
import yaml
import logging
import json
from amplipi import models, utils
from .base_streams import PersistentStream, InvalidStreamField
from .. import tasks

# Our subprocesses run behind the scenes, is there a more standard way to do this?
# pylint: disable=consider-using-with

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


class SpotifyConnect(PersistentStream):
  """ A SpotifyConnect Stream based off librespot-go """

  stream_type: ClassVar[str] = 'spotify'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate)
    self.supported_cmds = [
      'play',
      'pause',
      'next',
      'prev'
    ]
    self._connect_time = 0.0
    self._log_file: Optional[io.TextIOBase] = None
    self._api_port: int
    self.proc2: Optional[subprocess.Popen] = None
    self.volume_sync_process: Optional[subprocess.Popen] = None  # Runs the actual vol sync script
    self.volume_watcher_process: Optional[threading.Thread] = None  # Populates the fifo that the vol sync script depends on
    self.src_config_folder: Optional[str] = None
    self.meta_file: str = ''
    self._volume_fifo = None

  def watch_vol(self):
    """Creates and supplies a FIFO with volume data for volume sync"""
    while True:
      try:
        if self.src is not None:
          if self._volume_fifo is None and self.src_config_folder is not None:
            fifo_path = f"{self.src_config_folder}/vol"
            if not os.path.isfile(fifo_path):
              os.mkfifo(fifo_path)
            self._volume_fifo = os.open(fifo_path, os.O_WRONLY, os.O_NONBLOCK)
          data = json.dumps({
            'zones': self.connected_zones,
            'volume': self.volume,
          })
          os.write(self._volume_fifo, bytearray(f"{data}\r\n", encoding="utf8"))
      except Exception as e:
        logger.error(f"{self.name} volume thread ran into exception: {e}")
      time.sleep(0.1)

  def reconfig(self, **kwargs):
    self.validate_stream(**kwargs)
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect to a given audio source
    """

    self.src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    try:
      os.remove(f'{self.src_config_folder}/currentSong')
    except FileNotFoundError:
      pass
    self._connect_time = time.time()
    self._api_port = 3678 + vsrc

    logger.info("setting up config")

    config = {
      'device_name': self.name,
      'device_type': 'stb',  # set top box
      'audio_device': utils.virtual_output_device(vsrc),
      'external_volume': True,  # False indicates volume user controllable, volume synchronization is needed for this to be enabled
      'mixer_device': '',  # where volume control is applied, for '' volume changes are not actually applied to output
      'credentials': {
        'type': 'zeroconf'
      },
      'server': {
        'enabled': True,
        'port': self._api_port
      }
    }

    # make all of the necessary dir(s) & files
    os.makedirs(self.src_config_folder, exist_ok=True)

    config_file = f'{self.src_config_folder}/config.yml'
    with open(config_file, 'w', encoding='utf8') as f:
      f.write(yaml.dump(config))

    self.meta_file = f'{self.src_config_folder}/metadata.json'

    self._log_file = open(f'{self.src_config_folder}/log', mode='w', encoding='utf8')
    player_args = f"{utils.get_folder('streams')}/go-librespot --config_dir {self.src_config_folder}".split(' ')
    logger.debug(f'spotify player args: {player_args}')

    self.proc = subprocess.Popen(args=player_args, stdin=subprocess.PIPE,
                                 stdout=self._log_file, stderr=self._log_file)

    url = f"http://localhost:{self._api_port}"
    meta_reader = f"{utils.get_folder('streams')}/spot_connect_meta.py"
    meta_args = [sys.executable, meta_reader, url, self.meta_file, '--debug']  # TODO: remove --debug for production
    logger.info(f'{self.name}: starting metadata reader: {meta_args}')
    self.proc2 = subprocess.Popen(args=meta_args, stdout=self._log_file, stderr=self._log_file)

    vol_sync = f"{utils.get_folder('streams')}/spotify_volume_handler.py"
    vol_args = [sys.executable, vol_sync, str(self._api_port), self.src_config_folder, "--debug"]
    logger.info(f'{self.name}: starting vol synchronizer: {vol_args}')
    self.volume_sync_process = subprocess.Popen(args=vol_args, stdout=self._log_file, stderr=self._log_file)

    self.volume_watcher_process = threading.Thread(target=self.watch_vol, daemon=True)
    self.volume_watcher_process.start()

  def _deactivate(self):
    if self._is_running():
      self.proc.stdin.close()
      logger.info(f'{self.name}: stopping player')

      # Call terminate on all processes
      self.proc.terminate()
      self.proc2.terminate()
      if self.volume_sync_process:
        self.volume_sync_process.terminate()

      # Ensure the processes have closed, by force if necessary
      if self.proc.wait(1) != 0:
        logger.info(f'{self.name}: killing player')
        self.proc.kill()

      if self.proc2.wait(1) != 0:
        logger.info(f'{self.name}: killing metadata reader')
        self.proc2.kill()

      if self.volume_sync_process:
        if self.volume_sync_process.wait(1) != 0:
          logger.info(f'{self.name}: killing volume synchronizer')
          self.volume_sync_process.kill()

      # Validate on the way out
      self.proc.communicate()
      self.proc2.communicate()
      if self.volume_sync_process:
        self.volume_sync_process.communicate()

    if self.proc and self._log_file:  # prevent checking _log_file when it may not exist, thanks validation!
      self._log_file.close()
    if self.src:
      try:
        subprocess.run(f'rm -r {utils.get_folder("config")}/srcs/{self.src}/*', shell=True, check=True)
      except Exception as e:
        logger.exception(f'{self.name}: Error removing config files: {e}')
    self._disconnect()

    self.proc = None
    self.proc2 = None
    self.volume_sync_process = None
    self.volume_watcher_process = None
    self._volume_fifo = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=f"Connect to {self.name} on Spotify Connect",
      state=self.state,
      img_url='static/imgs/spotify.png',
      type=self.stream_type
    )

    if not self.meta_file:
      logger.error(f'{self.name}: no metadata file. info() called on un-activated stream')
      return source

    if not os.path.exists(self.meta_file):
      return source

    try:
      # start with a usable state, just in case metadata is invalid
      source.state = "playing"  # or "unknown"
      source.supported_cmds = self.supported_cmds
      # pull in the metadata
      with open(self.meta_file, 'r', encoding='utf8') as f:
        metadata = yaml.safe_load(f)
      if 'track' not in metadata or not metadata['track']['name']:
        return source  # no track info, there is probably no device connected
      source.name = self.full_name()
      source.track = metadata['track']['name']
      source.album = metadata['track']['album_name']
      source.artist = ", ".join(metadata['track']['artist_names'])
      if metadata['stopped']:
        source.state = "stopped"
        source.supported_cmds = ['play']
      elif metadata['paused']:
        source.state = "paused"
        source.supported_cmds = self.supported_cmds

      if metadata['track']['album_cover_url']:
        source.img_url = metadata['track']['album_cover_url']

    except Exception as e:
      logger.exception(f"{self.name}: error munging metadata: {e}")

    return source

  def send_cmd(self, cmd: str) -> None:
    """ Send a command to the Spotify Connect stream

    We use tasks.post to send the command asynchronously avoiding blocking

    see https://github.com/devgianlu/go-librespot/blob/master/api-spec.yml for the API endpoint docs
    """
    url = f"http://localhost:{self._api_port}/player/"
    if cmd == 'play':
      tasks.post.delay(url + 'resume')
    elif cmd == 'pause':
      tasks.post.delay(url + 'pause')
    elif cmd == 'next':
      tasks.post.delay(url + 'next', data={})  # necessary since next had several optional parameters
    elif cmd == 'prev':
      tasks.post.delay(url + 'prev')
    else:
      raise NotImplementedError(f'Spotify command not supported: {cmd}')

  def validate_stream(self, **kwargs):
    NAME = r"[a-zA-Z0-9][A-Za-z0-9\- ]*[a-zA-Z0-9]"
    if 'name' in kwargs and not re.fullmatch(NAME, kwargs['name']):
      raise InvalidStreamField("name", "Invalid stream name")
