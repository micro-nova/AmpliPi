from .base_streams import BaseStream, uuid_gen, logger
from typing import ClassVar
from amplipi import models, utils
import subprocess
import time
import os
import json
import sys
import uuid


class DLNA(BaseStream):  # TODO: make DLNA a persistent stream to fix the uuid issue, figure out next and prev
  """ A DLNA Stream """

  stream_type: ClassVar[str] = 'dlna'

  def __init__(self, name: str, disabled: bool = False, mock: bool = False):
    super().__init__('dlna', name, disabled=disabled, mock=mock)
    self.supported_cmds = ['play', 'pause']
    self._metadata_proc = None
    self._uuid = 0
    self._src_config_folder = ''
    self._src_web_folder = ''
    self._got_data = False
    self._fifo_open = False
    self._fifo = None

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
        time.sleep(0.1)  # delay a bit, is this needed?
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
    self._uuid = 0
    self._uuid = uuid_gen()
    portnum = 49494 + int(src)

    # Make the (per-source) config and web directories
    self._src_config_folder = f'{utils.get_folder("config")}/srcs/{src}'
    os.system(f'rm -r {self._src_config_folder}')
    os.system(f'mkdir -p {self._src_config_folder}')

    self._src_web_folder = f'{utils.get_folder("web")}/generated/{src}'
    os.system(f'rm -r {self._src_web_folder}')
    os.system(f'mkdir -p {self._src_web_folder}')

    # Make the fifo to be used for commands
    os.mkfifo(f'{self._src_config_folder}/cmd')  # lazily open fifo so startup is faster

    # startup the metadata process and the DLNA process
    dlna_args = ['gmediarender', '--gstout-audiosink', 'alsasink',
                 '--gstout-audiodevice', utils.real_output_device(src), '--gstout-initial-volume-db',
                 '0.0', '-p', f'{portnum}', '-u', f'{self._uuid}',
                 '-f', f'{self.name}']
    meta_args = [sys.executable,
                 f'{utils.get_folder("streams")}/dlna_meta.py',
                 f'{self.name}',
                 f'{self._src_config_folder}/cmd',
                 f'{self._src_config_folder}/meta.json',
                 self._src_web_folder,
                 ]
    # '-d']

    self.proc = subprocess.Popen(args=dlna_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self._metadata_proc = subprocess.Popen(args=meta_args, stdin=subprocess.PIPE, stdout=sys.stdout, stderr=sys.stderr)

    self._connect(src)

  def disconnect(self):
    if self._is_running():
      utils.careful_proc_shutdown(self._metadata_proc, "dlna metadata process")
      utils.careful_proc_shutdown(self.proc, "dlna process")
      if self._fifo_open:
        os.close(self._fifo)
    self._disconnect()
    self._metadata_proc = None
    self.dlna_proc = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url='static/imgs/dlna.png',
      type=self.stream_type
    )
    try:

      data = json.load(open(f'{self._src_config_folder}/meta.json'))
      source.state = data.get('state', 'stopped') if data else 'stopped'
      if source.state != 'stopped':  # if the state is stopped, just use default values
        source.artist = data.get('artist', '')
        source.track = data.get('title', '')
        source.album = data.get('album', '')
        if data.get('album_art', '') != '':
          source.img_url = f'generated/{self.src}/{data.get("album_art", "")}'

      source.supported_cmds = self.supported_cmds  # set supported commands only if we hear back from the DLNA server
      self._got_data = True
    except Exception as e:
      if self._got_data:  # ignore if we havent gotten data yet since we're still waiting for the metadata process to start
        logger.exception(f'Error getting DLNA info: {e}')
      pass

    return source

  def send_cmd(self, cmd):
    if not self._fifo_open:
      # open the fifo for writing but don't block in case something goes wrong
      self._fifo = os.open(f'{self._src_config_folder}/cmd', os.O_WRONLY, os.O_NONBLOCK)
      self._fifo_open = True

    try:
      if cmd in self.supported_cmds and self.src is not None:
        # must end line since metadata_reader uses readline()
        os.write(self._fifo, bytearray(cmd + '\r\n', encoding="utf8"))
        os.fsync(self._fifo)
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      logger.exception(f'Error sending command to DLNA "{cmd}": {e}')
      pass
