from .base_streams import PersistentStream, Browsable, logger
from amplipi import models, utils
from typing import ClassVar, List, Optional
import subprocess
import os
import time
import datetime
import threading
import sys
import pathlib

MUSIC_EXTENSIONS = ('.mp3', '.wav', '.aac', '.m4a', '.m4b', '.flac', '.aiff', '.mp4', '.avi', '.wmv', '.mov', '.mpg', '.mpeg', '.wma')


class MediaDevice(PersistentStream, Browsable):
  """ An external media device plugged into AmpliPro """

  stream_type: ClassVar[str] = 'mediadevice'

  def __init__(self, name: str, url: Optional[str], disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.url = url
    self.directory = '/media'
    self.local_directory = '/media'
    self.bkg_thread: Optional[threading.Thread] = None
    self.song_list: List[str] = []
    self.song_index = 0
    self._prev_timeout = datetime.datetime.now()
    self.playing = None
    self.device: Optional[str] = None
    self.supported_cmds = ['play', 'pause', 'prev']
    self.stopped_message = None
    self.default_image_url = 'static/imgs/no_note.png'

  def reconfig(self, **kwargs):
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs:
      self.name = kwargs['name']
    if 'url' in kwargs:
      self.url = kwargs['url']
      reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.restart()

  def _activate(self, vsrc: int, remake_list: bool = True):
    """ Connect a short run VLC process with audio output to a given audio source """
    if remake_list and self.playing is not None:
      try:
        self.song_list, _ = self.make_song_list(os.path.dirname(self.playing))
      except Exception as e:
        logger.error(f'Error processing request: {e}')
    self.src = vsrc

  def make_song_list(self, path):
    song_list = []
    directory_list = []
    for filename in os.listdir(path):
      f = os.path.join(path, filename)
      if not str(pathlib.Path(f).absolute().resolve()).startswith(path):
        raise Exception(f'File path {f} not in {path}')
      if os.path.isfile(f) and f.endswith(MUSIC_EXTENSIONS):
        song_list.append(f)
      elif not os.path.isfile(f):
        directory_list.append(f)
    return song_list, directory_list

  def _deactivate(self):
    if self._is_running():
      self.proc.kill()
      if self.bkg_thread:
        self.bkg_thread.join()
    self._disconnect()
    self.proc = None

  def wait_on_proc(self):
    """ Wait for the vlc process to finish """
    if self.proc is not None:
      self.proc.wait()  # TODO: add a time here
    else:
      time.sleep(0.3)  # handles mock case

    if self._cached_info.state == 'playing' and self.playing in self.song_list and self.song_index < len(self.song_list) - 1:
      self.next_song()
    elif (self.song_index >= len(self.song_list) - 1 or self.playing not in self.song_list):
      self.send_cmd('paused')

  def next_song(self):
    self.change_song(self.song_index + 1)

  def previous_song(self):
    self.change_song(self.song_index - 1)

  def change_song(self, new_song_id):
    if self._is_running():
      self.proc.kill()
      if self.bkg_thread:
        self.bkg_thread.join()

    self.song_index = new_song_id
    self.playing = self.song_list[self.song_index]
    # Start audio via runvlc.py
    song_info_path = f'{self._get_config_folder()}/metadata.json'
    log_file_path = f'{self._get_config_folder()}/log'
    self.command_file_path = f'{self._get_config_folder()}/cmd'

    if self.song_index < len(self.song_list) and self.device is not None:
      self.url = self.song_list[self.song_index]
      self.vlc_args = [
        sys.executable, f"{utils.get_folder('streams')}/fileplayer.py", self.url, self.device,
        '--song-info', song_info_path, '--log', log_file_path, '--cmd', self.command_file_path
      ]
      logger.info(f'running: {self.vlc_args}')
      self.proc = subprocess.Popen(args=self.vlc_args, preexec_fn=os.setpgrp)

    # make a thread that waits for the playback to be done and returns after info shows playback stopped
    # for the mock condition it just waits a couple seconds
    self.bkg_thread = threading.Thread(target=self.wait_on_proc)
    self.bkg_thread.start()

    f = open(self.command_file_path, 'w')
    f.write('play')
    f.close()
    self._prev_timeout = datetime.datetime.now() + datetime.timedelta(seconds=3)

  def send_cmd(self, cmd):
    super().send_cmd(cmd)

    if cmd == 'stop':
      self._deactivate()
    if self.command_file_path is not None:
      if cmd == 'pause':
        f = open(self.command_file_path, 'w')
        f.write('pause')
        logger.info(f'pausing: {self.vlc_args}')
        f.close()

      if cmd == 'play':
        if not self._is_running():
          logger.info(f'running: {self.vlc_args}')
          self.proc = subprocess.Popen(args=self.vlc_args, preexec_fn=os.setpgrp)
        f = open(self.command_file_path, 'w')
        f.write('play')
        f.close()

      if cmd == 'next':
        self.next_song()

      if cmd == 'prev':
        # Restart current song if we are past the first 3 seconds, otherwise go back

        if self._prev_timeout > datetime.datetime.now() and self.song_index > 0:
          self.previous_song()
        else:
          self.change_song(self.song_index)

  def _read_info(self) -> models.SourceInfo:
    super()._read_info()

    self.supported_cmds = ['play', 'pause', 'prev']
    if self.song_index != len(self.song_list) - 1 and self.playing in self.song_list:
      self.supported_cmds.append('next')

    # replace with file name so currently playing song is correct
    self._cached_info.track = os.path.basename(self.playing) if self.playing is not None else 'No song playing'

    return self._cached_info

  def info(self) -> models.SourceInfo:
    info = super().info()

    if self.playing is None or self._cached_info.state != 'playing':
      info.img_url = 'static/imgs/no_note.png'
    else:
      info.img_url = 'static/imgs/note.png'

    return info

  def browse(self, parent=None, path=None) -> List[models.BrowsableItem]:
    browsables = []
    if path is None:
      if self.playing is None:
        path = self.directory
      else:
        path = os.path.dirname(self.playing)

    song_list, directory_list = self.make_song_list(path)

    if path != self.directory:
      browsables.append(models.BrowsableItem(name='../', playable=True, parent=False, id=os.path.dirname(path), img='static/imgs/folder.png'))
    for directory in directory_list:
      browsables.append(models.BrowsableItem(name=directory.split('/')[-1], playable=True, parent=False, id=directory, img='static/imgs/folder.png'))
    for song in song_list:
      browsables.append(models.BrowsableItem(name=song.split('/')[-1], playable=True, parent=False, id=song, img='static/imgs/note.png'))
    return browsables

  def play(self, path):
    if not str(pathlib.Path(path).absolute().resolve()).startswith(self.directory):
      logger.error(f'Error processing request: Cannot browse path {path}')
      return

    if not os.path.exists(path):
      logger.error(f'Error processing request: Path {path} does not exist')

    if os.path.isdir(path):
      try:
        return path
      except Exception as e:
        logger.error(f'Error processing request: {e}')
    else:
      dir = os.path.dirname(path)
      song_list, directory_list = self.make_song_list(dir)
      if path in song_list:
        self.song_list = song_list
        new_id = self.song_list.index(path)
        self.change_song(new_id)
        return dir
      else:
        logger.error(f'Cannot find song {path}')
    return path  # If an error occurs just return to the original path.

  def is_persistent(self):
    return True
