

import io
import os
import sys
import subprocess
import time
from typing import ClassVar, Optional
import yaml
from amplipi import models, utils
from .base_streams import PersistentStream, logger

# Our subprocesses run behind the scenes, is there a more standard way to do this?
# pylint: disable=consider-using-with


class SpotifyConnect(PersistentStream):
  """ A SpotifyConnect Stream based off librespot-go """

  stream_type: ClassVar[str] = 'spotifyconnect'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate)
    # TODO: add command pipe?
    self.supported_cmds = [
      # 'play',
      # 'pause',
      # 'next',
      # 'prev'
    ]
    self._connect_time = 0.0
    self._log_file: Optional[io.TextIOBase] = None
    self._api_port: int
    self.proc2: Optional[subprocess.Popen] = None
    self.meta_file: str = ''

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

    src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    try:
      os.remove(f'{src_config_folder}/currentSong')
    except FileNotFoundError:
      pass
    self._connect_time = time.time()
    self._api_port = 3678 + vsrc

    logger.info("setting up config")

    config = {
      'device_name': self.name,
      'device_type': 'stb',  # set top box
      'audio_device': utils.virtual_output_device(vsrc),
      'external_volume': True,
      'credentials': {
        'type': 'zeroconf'
      },
      'server': {
        'enabled': True,
        'port': self._api_port
      }
    }

    # make all of the necessary dir(s) & files
    os.makedirs(src_config_folder, exist_ok=True)

    config_file = f'{src_config_folder}/config.yml'
    with open(config_file, 'w', encoding='utf8') as f:
      f.write(yaml.dump(config))

    self.meta_file = f'{src_config_folder}/metadata.json'

    self._log_file = open(f'{src_config_folder}/log', mode='w', encoding='utf8')
    player_args = f"{utils.get_folder('streams')}/go-librespot --config_dir {src_config_folder}".split(' ')
    logger.debug(f'spotify player args: {player_args}')

    self.proc = subprocess.Popen(args=player_args, stdin=subprocess.PIPE,
                                 stdout=self._log_file, stderr=self._log_file)

    url = f"http://localhost:{self._api_port}"
    meta_reader = f"{utils.get_folder('streams')}/spot_connect_meta.py"
    logger.info(f'{self.name}: starting metadata reader: {[sys.path, meta_reader, url, self.meta_file]}')
    self.proc2 = subprocess.Popen(args=[sys.executable, meta_reader, url, self.meta_file], stdout=self._log_file, stderr=self._log_file)

  def _deactivate(self):
    if self._is_running():
      self.proc.stdin.close()
      self.proc2.stdin.close()
      logger.info(f'{self.name}: stopping player')
      self.proc.terminate()
      self.proc2.terminate()
      if self.proc.wait(1) != 0:
        logger.info(f'{self.name}: killing player')
        self.proc.kill()
      if self.proc2.wait(1) != 0:
        logger.info(f'{self.name}: killing metadata reader')
        self.proc2.kill()
      self.proc.communicate()
      self.proc2.communicate()
    if self._log_file:
      self._log_file.close()
    if self.src:
      try:
        subprocess.run(f'rm -r {utils.get_folder("config")}/srcs/{self.src}/*', shell=True, check=True)
      except Exception as e:
        logger.exception(f'{self.name}: Error removing config files: {e}')
    self._disconnect()
    self.proc = None
    self.proc2 = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=f"Connect to {self.name} on Spotify Connect",
      state=self.state,
      img_url='static/imgs/spotify.png',
      type=self.stream_type
    )

    if not os.path.exists(self.meta_file):
      return source

    try:
      with open(self.meta_file, 'r', encoding='utf8') as f:
        metadata = yaml.safe_load(f)
      if 'track' not in metadata or not metadata['track']['name']:
        return source  # no track info, there is probably no device connected
      source.name = self.full_name()
      source.track = metadata['track']['name']
      source.album = metadata['track']['album_name']
      artist_string = ", ".join(metadata['track']['artist_names'])
      source.artist = artist_string[:-2]
      if metadata['stopped']:
        source.state = "stopped"
      elif metadata['paused']:
        source.state = "paused"
      else:
        source.state = "playing"  # or "unknown"

      if metadata['track']['album_cover_url']:
        source.img_url = metadata['track']['album_cover_url']

    except Exception as e:
      logger.exception(f"{self.name}: error munging metadata: {e}")

    return source
