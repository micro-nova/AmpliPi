from .base_streams import PersistentStream, logger
from typing import ClassVar, Optional
from amplipi import models, utils
import subprocess
import os
import json
import hashlib
import sys
import signal
import socket


class LMS(PersistentStream):
  """ An LMS Stream using squeezelite"""

  stream_type: ClassVar[str] = 'lms'

  def __init__(self, name: str, server: Optional[str] = None, port: Optional[int] = 9000, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.server: Optional[str] = server
    self.port: Optional[int] = port
    self.meta_proc: Optional[subprocess.Popen] = None
    self.meta = {'artist': 'Launching metadata reader', 'album': 'If this step takes a long time,',
                 'track': 'please restart the unit/stream, or contact support', 'image_url': 'static/imgs/lms.png'}

  def is_persistent(self):
    return True

  def reconfig(self, **kwargs):
    reconnect_needed = False

    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if 'server' in kwargs and kwargs['server'] != self.server:
      self.server = kwargs['server']
      reconnect_needed = True
    if 'port' in kwargs and kwargs['port'] != self.port:
      self.port = kwargs['port']
      reconnect_needed = True
    if reconnect_needed:
      if self._is_running():
        self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect a squeezelite output to a given audio source
    This will create a LMS client based on the given name
    """
    if self.mock:
      self._connect(vsrc)
      return
    try:
      # Make the (per-source) config directory
      self.vsrc = vsrc
      src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
      os.system(f'mkdir -p {src_config_folder}')
      with open(f"{src_config_folder}/lms_metadata.json", "w", encoding="UTF-8") as f:
        json.dump(self.meta, f, indent=2)

      # mac address, needs to be unique but not tied to actual NIC MAC hash the name with src id, to avoid aliases on move
      md5 = hashlib.md5()
      md5.update(self.name.encode('utf-8'))
      md5_hex = md5.hexdigest()
      fake_mac = ':'.join([md5_hex[i:i + 2] for i in range(0, 12, 2)])

      # Process
      lms_args = [
        f'{utils.get_folder("streams")}/process_monitor.py',
        '/usr/bin/squeezelite',
        '-n', self.name,
        '-m', fake_mac,
        '-o', utils.virtual_output_device(vsrc),
        '-f', f'{src_config_folder}/lms_log.txt',
        '-i', f'{src_config_folder}/lms_remote',  # specify this to avoid collisions, even if unused
      ]
      if self.server:
        # specify the server to connect to (if unspecified squeezelite starts in discovery mode)
        server = self.server
        # some versions of amplipi have an LMS server embedded, using localhost avoids hardcoding the hostname
        if 'localhost' == server:
          # squeezelite does not support localhost and requires the actual hostname
          server.replace('localhost', socket.gethostname())

        lms_args += ['-s', server]

      meta_args = ['python3', 'streams/lms_metadata.py', "--name", f"{self.name}", "--vsrc", f"{self.vsrc}"]
      if self.server is not None:
        meta_args.extend(["--server", f"{self.server}"])
      if self.port is not None:
        meta_args.extend(["--port", f"{self.port}"])
      self.meta_proc = subprocess.Popen(args=meta_args, stdout=sys.stdout, stderr=sys.stderr)

      self.proc = subprocess.Popen(args=lms_args)
    except Exception as exc:
      logger.exception(f'error starting lms: {exc}')

  def _deactivate(self):
    if self._is_running():
      try:
        src_config_folder = f'{utils.get_folder("config")}/srcs/v{self.vsrc}'
        os.system(f'rm -f {src_config_folder}')
        self.proc.terminate()
        self.proc.communicate(timeout=10)
      except Exception as e:
        logger.exception(f"failed to gracefully terminate LMS stream {self.name}: {e}")
        logger.warning(f"forcefully killing LMS stream {self.name}")
        os.killpg(self.proc.pid, signal.SIGKILL)
        self.proc.communicate(timeout=3)

    if self.meta_proc is not None:
      try:
        self.meta_proc.terminate()
        self.meta_proc.communicate(timeout=10)
      except Exception as e:
        logger.exception(f"failed to gracefully terminate LMS meta proc for {self.name}: {e}")
        logger.warning(f"forcefully killing LMS meta proc for {self.name}")
        os.killpg(self.meta_proc.pid, signal.SIGKILL)
        self.meta_proc.communicate(timeout=3)

    self.proc = None
    self.meta_proc = None

  def info(self) -> models.SourceInfo:
    # Opens and reads the metadata.json file every time the info def is called
    try:
      src_config_folder = f"{utils.get_folder('config')}/srcs/v{self.vsrc}"
      with open(f"{src_config_folder}/lms_metadata.json", "r", encoding="utf-8") as meta_read:
        self.meta = json.loads(meta_read.read())
    except:
      self.meta = {
        'track': 'Trying again shortly...',
        'album': 'Make sure your lms player is connected to this source',
        'artist': 'Error: Could Not Find LMS Server',
        'image_url': 'static/imgs/lms.png'
      }
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      img_url=self.meta.get('image_url', ''),
      track=self.meta.get('track', ''),
      album=self.meta.get('album', ''),
      artist=self.meta.get('artist', ''),
      type=self.stream_type
    )
    return source
