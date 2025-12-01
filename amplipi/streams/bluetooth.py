from amplipi import models, utils
from .base_streams import BaseStream, logger
from typing import ClassVar
import subprocess
import os
import json
import sys
import signal
import traceback


class Bluetooth(BaseStream):
  """ A source for Bluetooth streams, which requires an external Bluetooth USB dongle """

  stream_type: ClassVar[str] = 'bluetooth'

  def __init__(self, name, disabled=False, mock=False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.logo = "static/imgs/bluetooth.png"
    self.bt_proc = None
    self.supported_cmds = ['play', 'pause', 'next', 'prev', 'stop']

  def __del__(self):
    self.disconnect()

  @staticmethod
  def is_hw_available():
    """Determines if a bluetooth dongle is present"""
    try:
      if subprocess.run('which bluetoothctl'.split(), check=False, stdout=subprocess.DEVNULL).returncode != 0:
        return False
      # bluetoothctl show seems to hang sometimes when hardware is not available
      # add a timeout so that we don't get stuck waiting
      btcmd_proc = subprocess.run('bluetoothctl show'.split(), check=True, stdout=subprocess.PIPE, timeout=0.5)
      return 'No default controller available' not in btcmd_proc.stdout.decode('utf-8')
    except Exception as e:
      if 'timed out' not in str(e):  # a timeout indicates bluetooth module is missing
        logger.exception(f'Error checking for bluetooth hardware: {e}')
      return False

  def connect(self, src):
    """ Connect a bluealsa-aplay process with audio output to a given audio source """
    logger.info(f'connecting {self.name} to {src}...')

    if self.mock:
      self._connect(src)
      return

    # Power on Bluetooth and enable discoverability
    subprocess.run(args='bluetoothctl power on'.split(), preexec_fn=os.setpgrp)
    subprocess.run(args='bluetoothctl discoverable on'.split(), preexec_fn=os.setpgrp)
    subprocess.run(args='sudo btmgmt fast-conn on'.split(), preexec_fn=os.setpgrp)

    # Start metadata watcher
    src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system(f'mkdir -p {src_config_folder}')
    song_info_path = f'{src_config_folder}/currentSong'
    device_info_path = f'{src_config_folder}/btDevice'
    btmeta_args = f'{sys.executable} {utils.get_folder("streams")}/bluetooth.py --song-info={song_info_path} ' \
                  f'--device-info={device_info_path} --output-device={utils.real_output_device(src)}'
    self.bt_proc = subprocess.Popen(args=btmeta_args.split(), preexec_fn=os.setpgrp)

    self._connect(src)
    return

  def _is_running(self):
    if 'bt_proc' in self.__dir__() and self.bt_proc:
      return self.bt_proc.poll() is None
    return False

  def disconnect(self):
    if self._is_running():
      os.killpg(os.getpgid(self.bt_proc.pid), signal.SIGKILL)
      self.bt_proc = None

      # Power off Bluetooth and disable discoverability
      subprocess.run(args='bluetoothctl discoverable off'.split(), preexec_fn=os.setpgrp)
      subprocess.run(args='bluetoothctl power off'.split(), preexec_fn=os.setpgrp)

      self._disconnect()

  def info(self) -> models.SourceInfo:
    src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
    loc = f'{src_config_folder}/currentSong'
    source = models.SourceInfo(name=self.full_name(),
                               state=self.state,
                               img_url=self.logo,
                               supported_cmds=self.supported_cmds,
                               type=self.stream_type)
    try:
      with open(loc, 'r') as file:
        data = json.loads(file.read())
        source.artist = data['artist']
        source.track = data['title']
        source.album = data['album']
        source.state = data['status']
        return source
    except Exception as e:
      logger.exception(f'bluetooth: exception {e}')
      traceback.print_exc()
    return source

  def send_cmd(self, cmd):
    logger.info(f'bluetooth: sending command {cmd}')
    try:
      if cmd in self.supported_cmds and self.src is not None:
        src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
        device_info_path = f'{src_config_folder}/btDevice'
        btcmd_args = f'{sys.executable} {utils.get_folder("streams")}/bluetooth.py --command={cmd} --device-info={device_info_path}'
        subprocess.run(args=btcmd_args.split(), preexec_fn=os.setpgrp)
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      print(f'bluetooth: exception {e}')
      raise RuntimeError(f'Command {cmd} failed to send: {e}') from e
