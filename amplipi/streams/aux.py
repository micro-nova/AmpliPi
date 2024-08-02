from typing import ClassVar
from amplipi import models, utils
from .base_streams import BaseStream, logger
import subprocess


class Aux(BaseStream):
  """ A stream to play from the aux input. """

  stream_type: ClassVar[str] = 'aux'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)

  def reconfig(self, **kwargs):
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs:
      self.name = kwargs['name']

  def connect(self, src):
    """ Use VLC to connect audio output to audio source """
    logger.info(f'connecting {self.name} to {src}...')

    if self.mock:
      self._connect(src)
      return

    # Set input source
    utils.enable_aux_input()

    # Start audio via runvlc.py
    vlc_args = f'cvlc -A alsa --alsa-audio-device {utils.real_output_device(src)} alsa://plughw:cmedia8chint,0 vlc://quit'
    logger.info(f'running: {vlc_args}')
    self.proc = subprocess.Popen(args=vlc_args.split(), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self._connect(src)
    return

  def disconnect(self):
    if self._is_running():
      self.proc.kill()
    self.proc = None
    self._disconnect()

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(name=self.full_name(),
                               img_url='static/imgs/aux_input.svg',
                               state=self.state,
                               type=self.stream_type)
    return source
