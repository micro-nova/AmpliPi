from typing import ClassVar, Optional
from amplipi import models, utils
from .base_streams import BaseStream, logger
import subprocess
import os
import time
import threading
import datetime
import sys


class FilePlayer(BaseStream):
  """ An Single one shot file player - initially intended for use as a part of the PA Announcements """

  stream_type: ClassVar[str] = 'fileplayer'

  def __init__(self, name: str, url: str, temporary: bool = False, timeout: Optional[int] = None, has_pause: bool = True, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.url = url
    self.bkg_thread = None
    if has_pause:
      self.supported_cmds = ['play', 'pause', 'stop']
    else:
      self.supported_cmds = ['play', 'stop']
    self.temporary = temporary
    self.timeout = timeout
    self.default_image_url = 'static/imgs/plexamp.png'
    self.stopped_message = None
    self.command_file_path = None

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs:
      self.name = kwargs['name']
    if 'temporary' in kwargs:
      self.temporary = kwargs['temporary']
    if 'timeout' in kwargs:
      self.timeout = kwargs['timeout']
    if 'has_pause' in kwargs:
      self.timeout = kwargs['has_pause']
    if 'url' in kwargs:
      self.url = kwargs['url']
      reconnect_needed = True
    if reconnect_needed:
      last_src = self.src
      self.disconnect()
      time.sleep(0.1)  # delay a bit, is this needed?
      self.connect(last_src)

  def timeout_expired(self):
    return self.timeout is not None and datetime.datetime.now().timestamp() > int(self.timeout)

  def connect(self, src):
    """ Connect a short run VLC process with audio output to a given audio source """
    logger.info(f'connecting {self.name} to {src}...')

    if not self.mock and src is not None:
      # Make all of the necessary dir(s)
      src_config_folder = f"{utils.get_folder('config')}/srcs/{src}"
      os.system(f'mkdir -p {src_config_folder}')

      # Start audio via runvlc.py
      song_info_path = f'{src_config_folder}/metadata.json'
      log_file_path = f'{src_config_folder}/log'
      self.command_file_path = f'{src_config_folder}/cmd'
      self.vlc_args = [
        sys.executable, f"{utils.get_folder('streams')}/fileplayer.py", self.url, utils.real_output_device(src),
        '--song-info', song_info_path, '--log', log_file_path, '--cmd', self.command_file_path
      ]
      logger.info(f'running: {self.vlc_args}')
      self.proc = subprocess.Popen(args=self.vlc_args, preexec_fn=os.setpgrp)

    # make a thread that waits for the playback to be done and returns after info shows playback stopped
    # for the mock condition it just waits a couple seconds
    self.bkg_thread = threading.Thread(target=self.wait_on_proc)
    self.bkg_thread.start()
    self._connect(src)
    return

  def wait_on_proc(self):
    """ Wait for the vlc process to finish """
    if self.proc is not None:
      self.proc.wait()  # TODO: add a time here
      self.send_cmd('stop')  # notify that the audio is done playing
    else:
      time.sleep(0.3)  # handles mock case

  def send_cmd(self, cmd):
    super().send_cmd(cmd)

    if cmd == 'stop':
      if self._is_running():
        self.proc.kill()
        if self.bkg_thread:
          self.bkg_thread.join()
      self.state = 'stopped'
      self.proc = None
    if self.command_file_path is not None:
      if cmd == 'pause':
        f = open(self.command_file_path, 'w')
        f.write('pause')
        f.close()
        self.state = 'paused'

      if cmd == 'play':
        if not self._is_running():
          logger.info(f'running: {self.vlc_args}')
          self.proc = subprocess.Popen(args=self.vlc_args, preexec_fn=os.setpgrp)
        f = open(self.command_file_path, 'w')
        f.write('play')
        f.close()
        self.state = 'playing'

  def disconnect(self):
    if self._is_running():
      self.proc.kill()
      if self.bkg_thread:
        self.bkg_thread.join()
    self._disconnect()
    self.proc = None
