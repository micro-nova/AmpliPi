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
    self.default_image_url = 'static/imgs/lms.png'
    self.stopped_message = None

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
    if 'port' in kwargs and kwargs['port'] != self.port and kwargs['port']:
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
        '-f', f'{self._get_config_folder()}/lms_log.txt',
        '-i', f'{self._get_config_folder()}/lms_remote',  # specify this to avoid collisions, even if unused
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
      utils.careful_proc_shutdown(self.proc)

    if self.meta_proc is not None:
      utils.careful_proc_shutdown(self.meta_proc)

    self.proc = None
    self.meta_proc = None
