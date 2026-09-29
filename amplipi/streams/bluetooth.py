from amplipi import models, utils
from .base_streams import BaseStream, logger
from typing import ClassVar, Optional
import subprocess
import os
import json
import sys
import signal
import threading
import time
import traceback


class Bluetooth(BaseStream):
  """ A source for Bluetooth streams, which requires an external Bluetooth USB dongle """

  stream_type: ClassVar[str] = 'bluetooth'

  def __init__(self, name, disabled=False, mock=False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.logo = "static/imgs/bluetooth.png"
    self.bt_proc = None
    self.supported_cmds = ['play', 'pause', 'next', 'prev', 'stop']
    self.src_config_folder: Optional[str] = None
    self.volume_watcher_process: Optional[threading.Thread] = None
    """Populates the fifo that the vol sync process depends on"""
    self.volume_sync_process: Optional[subprocess.Popen] = None
    self._volume_fifo: Optional[int] = None

  def __del__(self):
    self.disconnect()

  def watch_vol(self):
    """Creates and supplies a FIFO with volume data for volume sync"""
    while True:
      try:
        if self.src is not None:
          if self._volume_fifo is None and self.src_config_folder is not None:
            fifo_path = f"{self.src_config_folder}/vol"
            # os.path.isfile() is always False for a FIFO (it only recognizes regular files),
            # so it never actually detects one left over from a prior connection - use exists()
            if not os.path.exists(fifo_path):
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

  @staticmethod
  def _adapter_powered() -> bool:
    """ Whether bluetoothctl currently reports the adapter as powered on """
    try:
      result = subprocess.run('bluetoothctl show'.split(), stdout=subprocess.PIPE, text=True, timeout=2, check=False)
      return 'Powered: yes' in result.stdout
    except Exception:
      return False

  def connect(self, src):
    """ Connect a bluealsa-aplay process with audio output to a given audio source """
    logger.info(f'connecting {self.name} to {src}...')

    if self.mock:
      self._connect(src)
      return

    # Power on Bluetooth and enable discoverability.
    # timeout=10: these have been observed to hang indefinitely against some adapters/states
    # (e.g. a still-settling USB Bluetooth radio), which would otherwise take the whole service
    # down with them since this runs synchronously on the startup path.
    # Bluetooth adapters can also just forget to turn on, so we need a retry loop to ensure they report an "on" state
    for attempt in range(5):
      for cmd in ('bluetoothctl power on', 'bluetoothctl discoverable on', 'sudo btmgmt fast-conn on'):
        try:
          subprocess.run(args=cmd.split(), preexec_fn=os.setpgrp, timeout=10, check=False)
        except subprocess.TimeoutExpired:
          logger.error(f'{self.name}: "{cmd}" timed out (attempt {attempt + 1}/5)')
      if self._adapter_powered():
        break
      logger.error(f'{self.name}: adapter not powered on after attempt {attempt + 1}/5')
      time.sleep(2)
    else:
      logger.error(f'{self.name}: bluetooth adapter never powered on after 5 attempts, continuing anyway')

    # Start metadata watcher
    self.src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
    os.system(f'mkdir -p {self.src_config_folder}')
    song_info_path = f'{self.src_config_folder}/currentSong'
    device_info_path = f'{self.src_config_folder}/btDevice'
    btmeta_args = f'{sys.executable} {utils.get_folder("streams")}/bluetooth.py --song-info={song_info_path} ' \
                  f'--device-info={device_info_path} --output-device={utils.real_output_device(src)}'
    self.bt_proc = subprocess.Popen(args=btmeta_args.split(), preexec_fn=os.setpgrp)

    vol_sync = f"{utils.get_folder('streams')}/bluetooth_volume_handler.py"
    vol_args = [sys.executable, vol_sync, device_info_path, self.src_config_folder]
    logger.info(f'{self.name}: starting vol synchronizer: {vol_args}')
    self.volume_watcher_process = threading.Thread(target=self.watch_vol, daemon=True)
    self.volume_watcher_process.start()
    self.volume_sync_process = subprocess.Popen(args=vol_args, preexec_fn=os.setpgrp)

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

      if self.volume_sync_process is not None:
        os.killpg(os.getpgid(self.volume_sync_process.pid), signal.SIGKILL)

      # Power off Bluetooth and disable discoverability
      subprocess.run(args='bluetoothctl discoverable off'.split(), preexec_fn=os.setpgrp)
      subprocess.run(args='bluetoothctl power off'.split(), preexec_fn=os.setpgrp)

      self._disconnect()

    if self._volume_fifo is not None:
      try:
        os.close(self._volume_fifo)
      except OSError:
        pass
    self.volume_sync_process = None
    self.volume_watcher_process = None
    self._volume_fifo = None

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
