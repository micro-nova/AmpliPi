from typing import ClassVar, Optional
from amplipi import models, utils
from .base_streams import PersistentStream, InvalidStreamField, logger
from amplipi.mpris import MPRIS
import subprocess
import requests
import shutil
import yaml
import time
import os
import io


class SpotifyConnect(PersistentStream):
  """ A SpotifyConnect Stream based off librespot-go """

  stream_type: ClassVar[str] = 'spotifyconnect'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate)
    self.mpris: Optional[MPRIS] = None
    self.supported_cmds = [
      #'play',
      #'pause',
      #'next',
      #'prev'
    ]
    self.STATE_TIMEOUT = 300  # seconds
    self._connect_time = 0.0
    self._coverart_dir = ''
    self._log_file: Optional[io.TextIOBase] = None
    self._api_port: int

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
    self._coverart_dir = f'{utils.get_folder("web")}/generated/v{vsrc}'
    self._api_port = 3678 + vsrc

    logger.info("setting up config")

    config = {
      'device_name': self.name,
      'device_type': 'stb', # set top box
      'audio_device': utils.virtual_output_device(vsrc),
      'external_volume': True,
      'credentials': {
        'type': 'zeroconf'
      },
      'server': {
        'enabled': True,
        'port': self._api_port,
        'address': '',
        'allow_origin': 'http://amplipi.local' # TODO: actually get the hostname and use it here
      }
    }

    # make all of the necessary dir(s) & files
    try:
      shutil.rmtree(self._coverart_dir)
    except FileNotFoundError:
      pass
    os.makedirs(self._coverart_dir, exist_ok=True)
    os.makedirs(src_config_folder, exist_ok=True)

    config_file = f'{src_config_folder}/config.yml'
    with open(config_file, 'w') as f:
        f.write(yaml.dump(config))

    self._log_file = open(f'{src_config_folder}/log', mode='w')
    player_args = f"{utils.get_folder('streams')}/go-librespot --config_dir {src_config_folder}".split(' ')
    logger.debug(f'player args: {player_args}')

    self.proc = subprocess.Popen(args=player_args, stdin=subprocess.PIPE,
                                 stdout=self._log_file, stderr=self._log_file)

    '''  Yes, this is ripped directly from the shairport sync one. We'll do metadata another way, another day.
    try:
      mpris_name = 'ShairportSync'
      # If there are multiple shairport-sync processes, add the pid to the mpris name
      # shairport sync only adds the pid to the mpris name if it cannot use the default name
      if len(os.popen("pgrep shairport-sync").read().strip().splitlines()) > 1:
        mpris_name += f".i{self.proc.pid}"
      self.mpris = MPRIS(mpris_name, f'{src_config_folder}/metadata.txt')
    except Exception as exc:
      logger.exception(f'Error starting airplay MPRIS reader: {exc}')
    '''

  def _deactivate(self):
    if self._is_running():
      self.proc.stdin.close()
      logger.info(f'{self.name}: stopping player')
      self.proc.terminate()
      if self.proc.wait(1) != 0:
        logger.info(f'{self.name}: killing player')
        self.proc.kill()
      self.proc.communicate()
    if '_log_file' in self.__dir__() and self._log_file:
      self._log_file.close()
    if self.src:
      try:
        subprocess.run(f'rm -r {utils.get_folder("config")}/srcs/{self.src}/*', shell=True, check=True)
      except Exception as e:
        logger.exception(f'{self.name}: Error removing config files: {e}')
    self._disconnect()
    self.proc = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=f"Connect to {self.name} on Spotify Connect",
      state=self.state,
      img_url='static/imgs/spotify.png',
      type=self.stream_type
    )

    try:
      r = requests.get(f"http://127.0.0.1:{self._api_port}/status")
      r.raise_for_status()
    except Exception as e:
      logger.debug(f"{self.name}: failed to query go-librespot: {e}")
      return source

    if r.status_code == 204: # No Content; occurs before spotify connects to go-librespot
      return source

    try:
      metadata = r.json()
      source.name = self.full_name()
      source.track = metadata['track']['name']
      source.album = metadata['track']['album_name']
      artist_string = ""
      for i in metadata['track']['artist_names']:
        artist_string += f"{i}, "
      source.artist = artist_string[:-2]
      if metadata['stopped']:
        source.state = "stopped"
      elif metadata['paused']:
        source.state = "paused"
      else:
        source.state = "playing" # or "unknown"

      cover_art = metadata['track']['album_cover_url']
      if cover_art:
        aa_filename = f"{cover_art.split('/')[-1]}.jpg"
        if aa_filename not in os.listdir(self._coverart_dir):
          aa = requests.get(cover_art)
          if aa.headers['Content-Type'] != 'image/jpeg':
            logger.warning(f"album art not a JPEG? {cover_art}")
          with open(f"{self._coverart_dir}/{aa_filename}", "wb") as f:
            f.write(aa.content)
        source.img_url = f"generated/v{self.vsrc}/{aa_filename}"
        
    except Exception as e:
      logger.exception(f"{self.name}: error munging metadata: {e}")

    return source


  ''' TODO: mpris
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
      logger.exception(f"error in shairport: {e}")

  def validate_stream(self, **kwargs):
    if 'name' in kwargs and len(kwargs['name']) > 50:
      raise InvalidStreamField("name", "name cannot exceed 50 characters")
  '''
