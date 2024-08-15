from .base_streams import PersistentStream, InvalidStreamField, logger
from typing import ClassVar, Optional
from amplipi import models, utils
from amplipi.mpris import MPRIS
import subprocess
import time
import os
import re


class Spotify(PersistentStream):
  """ A Spotify Stream """

  stream_type: ClassVar[str] = 'spotify'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate)
    self.connect_port: Optional[int] = None
    self.mpris: Optional[MPRIS] = None
    self.supported_cmds = ['play', 'pause', 'next', 'prev']

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
      time.sleep(0.1)  # Delay a bit

      self.mpris = MPRIS(f'spotifyd.instance{self.proc.pid}', f'{src_config_folder}/metadata.json')  # TODO: MPRIS should just need a path!

    except Exception as exc:
      logger.exception(f'error starting spotify: {exc}')

  def _deactivate(self):
    if self.proc:
      utils.careful_proc_shutdown(self.proc, "spotify stream")
      self.proc = None
    try:
      del self.mpris
    except Exception:
      pass
    self.mpris = None
    self.connect_port = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url='static/imgs/spotify.png',  # report generic spotify image in place of unspecified album art
      type=self.stream_type
    )
    if self.mpris is None:
      return source
    try:
      md = self.mpris.metadata()

      if not self.mpris.is_stopped():
        source.state = 'playing' if self.mpris.is_playing() else 'paused'
        source.artist = str(md.artist).replace("', '", ", ")  # When a song has multiple artists, they are comma-separated but the comma has '' around it
        source.track = md.title
        source.album = md.album
        source.supported_cmds = self.supported_cmds
        if md.art_url:
          source.img_url = md.art_url

    except Exception as e:
      logger.exception(f"error in spotify: {e}")

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

  def validate_stream(self, **kwargs):
    NAME = r"[a-zA-Z0-9][A-Za-z0-9\- ]*[a-zA-Z0-9]"
    if 'name' in kwargs and not re.fullmatch(NAME, kwargs['name']):
      raise InvalidStreamField("name", "Invalid stream name")
