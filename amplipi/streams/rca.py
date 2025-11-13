from .base_streams import BaseStream, logger
from typing import ClassVar
from amplipi import models, utils


class RCA(BaseStream):
  """ A built-in RCA input """

  stream_type: ClassVar[str] = 'rca'

  def __init__(self, name: str, stream_id: int, index: int, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, stream_id, only_src=index, disabled=disabled, mock=mock)
    # for serialiation the stream model's field needs to map to a stream's fields
    # index is needed for serialization
    self.index = index

  def reconfig(self, **kwargs):
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']

  def info(self) -> models.SourceInfo:
    src_info = models.SourceInfo(
      type=self.stream_type,
      img_url='static/imgs/rca_inputs.svg',
      name=self.full_name(),
      state='stopped')
    playing = False
    status_file = f'{utils.get_folder("config")}/srcs/rca_status'
    try:
      if self.src is not None:
        with open(status_file, mode='rb') as file:
          status_all = file.read()[0]
          playing = (status_all & (0b11 << (self.src * 2))) != 0
    except FileNotFoundError as error:
      logger.exception(f"Couldn't open RCA audio status file {status_file}:\n  {error}")
    except Exception as error:
      logger.exception(f'Error getting RCA audio status:\n  {error}')
    src_info.state = "playing" if playing else "stopped"
    return src_info

  def connect(self, src):
    if src != self.only_src:
      raise Exception(f"Unable to connect RCA {self.only_src} to src {src}, can only be connected to {self.only_src}")
    self._connect(src)

  def disconnect(self):
    self._disconnect()
