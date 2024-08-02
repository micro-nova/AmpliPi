from .base_streams import BaseStream
from typing import ClassVar
from amplipi import models


class Plexamp(BaseStream):
  """ A Plexamp Stream
  TODO: old plexamp interface was disabled, integrate support for new PlexAmp
  """

  stream_type: ClassVar[str] = 'plexamp'

  def __init__(self, name: str, client_id, token, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)

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
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url='static/imgs/plexamp.png',
      type=self.stream_type
    )
    source.track = "Not currently supported"
    return source
