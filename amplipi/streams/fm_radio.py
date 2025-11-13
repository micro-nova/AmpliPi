from typing import ClassVar, Optional
from amplipi import models, utils
from .base_streams import BaseStream, logger
import subprocess
import os
import json
import sys
import signal
import time
import re


class FMRadio(BaseStream):
  """ An FMRadio Stream using RTLSDR """

  stream_type: ClassVar[str] = 'fmradio'

  def __init__(self, name: str, stream_id: int, freq, logo: Optional[str] = None, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, stream_id, disabled=disabled, mock=mock)
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
      time.sleep(0.1)  # delay a bit, is this needed?
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

    fmradio_args = [
      sys.executable, f"{utils.get_folder('streams')}/fmradio.py", self.freq, utils.real_output_device(src),
      '--song-info', song_info_path, '--log', log_file_path
    ]
    logger.info(f'running: {fmradio_args}')
    self.proc = subprocess.Popen(args=fmradio_args, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setpgrp)
    self._connect(src)

  def _is_running(self):
    if 'proc' in self.__dir__() and self.proc:
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
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url=self.logo,
      type=self.stream_type
    )
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
        # Example JSON: "station": "Mixx96.1", "callsign": "KXXO", "prog_type": "Soft rock", "radiotext": "        x96.1"
        # logger.debug(json.dumps(data))
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
      # logger.exception('Failed to get currentSong - it may not exist: {}'.format(e))
    return source

  @staticmethod
  def is_hw_available():
    """Determines if an FM Radio dongle is present"""
    try:
      if subprocess.run('which rtl_fm'.split(), check=False, stdout=subprocess.DEVNULL).returncode != 0:
        return False
      rtlcmd_proc = subprocess.run('rtl_fm -f 88.3 /dev/null'.split(), check=True, timeout=1, capture_output=True)
      # If there is FM hardware, we should time out - we should not reach this point otherwise. We could check
      # for the output 'No supported devices found.', but that feels extra.
      return False
    except subprocess.TimeoutExpired as e:
      # Timing out is a good sign, because we're fully tuning in to a channel and streaming it to /dev/null.
      # Still need to check that we actually found adaptors...
      r = re.compile(r'^Found \d+ device\(s\):$', re.MULTILINE)
      return r.match(e.stderr.decode('utf-8')) is not None
    except subprocess.CalledProcessError as e:
      # rtl_fm returns a non-zero exit status when it cannot find a device. If it returned a non-zero
      # exit, but for reasons other than not finding hardware, report it below.
      r = re.compile(r'^No supported devices found.$', re.MULTILINE)
      if not r.match(e.stderr.decode('utf-8')):
        logger.info(f'Error checking for FM hardware: {e}')
      return False
    except Exception as e:
      logger.exception(f'Error checking for FM hardware: {e}')
      return False
