from .base_streams import BaseStream, InvalidStreamField, logger
from typing import ClassVar, Optional
from urllib.parse import urlparse
from amplipi import models, utils
import subprocess
import time
import os
import re
import requests
import json
import sys
import validators


class InternetRadio(BaseStream):
  """ An Internet Radio Stream """

  stream_type: ClassVar[str] = 'internetradio'

  def __init__(self, name: str, url: str, logo: Optional[str], disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate, url=url, logo=logo)
    self.url = url
    self.supported_cmds = ['play', 'stop']
    if logo:
      self.default_image_url = logo
    else:
      self.default_image_url = 'static/imgs/internet_radio.png'
    self.stopped_message = None

  def reconfig(self, **kwargs):
    self.validate_stream(**kwargs)
    reconnect_needed = False
    ir_fields = ['url', 'logo']
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
    """ Connect a VLC output to a given audio source
    This will create a VLC process based on the given name
    """
    logger.info(f'connecting {self.name} to {src}...')

    self._connect(src)

    if self.mock:
      logger.info(f'{self.name} connected to {src}')
      self.state = 'playing'
      self.src = src
      return

    # HACK check if url is a playlist and if it is get the first url and play it
    # this is the most general way to deal with playlists for this stream since the alternative is to actually
    # parse each playlist type and get the urls from them
    PLAYLIST_TYPES = ['pls', 'm3u', 'm3u8']
    if self.url.split('.')[-1] in PLAYLIST_TYPES:
      logger.info('Playlist detected, attempting to get playlist...')
      try:
        req = requests.get(self.url)
        urls = re.compile(r'(http.*?)[\r\n]').findall(req.text)
        if len(urls) > 0:
          self.url = urls[0]
          logger.info(f'using first url: {self.url}')
        else:
          raise Exception('No urls found in playlist')
      except Exception as e:
        logger.exception(f'Error getting playlist {e}')

    # Start audio via runvlc.py
    song_info_path = f'{self._get_config_folder()}/metadata.json'
    log_file_path = f'{self._get_config_folder()}/log'
    inetradio_args = [
      sys.executable, f"{utils.get_folder('streams')}/runvlc.py", self.url, utils.real_output_device(src),
      '--song-info', song_info_path, '--log', log_file_path
    ]
    logger.info(f'running: {inetradio_args}')
    self.proc = subprocess.Popen(args=inetradio_args, preexec_fn=os.setpgrp)

    logger.info(f'{self.name} (stream: {self.url}) connected to {src} via {utils.real_output_device(src)}')
    self.state = 'playing'
    self.src = src

  def disconnect(self):
    # try to kill proc gracefully, then forcefully
    if self.proc:
      utils.careful_proc_shutdown(self.proc, "internet radio stream")
    self._disconnect()
    self.proc = None

  # def info(self) -> models.SourceInfo:
  #   src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
  #   loc = f'{src_config_folder}/currentSong'
  #   source = models.SourceInfo(name=self.full_name(),
  #                              state=self.state,
  #                              img_url='static/imgs/internet_radio.png',
  #                              supported_cmds=self.supported_cmds,
  #                              type=self.stream_type)
  #   if self.logo:
  #     source.img_url = self.logo
  #   try:
  #     with open(loc, 'r', encoding='utf-8') as file:
  #       data = json.loads(file.read())
  #       source.artist = data['artist']
  #       source.track = data['track']
  #       source.station = data['station']
  #       source.state = data['state']
  #       return source
  #   except Exception:
  #     pass
  #   return source

  def send_cmd(self, cmd):
    try:
      if cmd in self.supported_cmds and self.src is not None:
        if cmd == 'play':
          if not self._is_running():
            self.connect(self.src)
        elif cmd == 'stop':
          if self._is_running():
            try:
              self.proc.kill()
              self.proc = None
              src_config_folder = f"{utils.get_folder('config')}/srcs/{self.src}"
              song_info_path = f'{src_config_folder}/currentSong'
              os.system(f'rm {song_info_path}')
            except Exception:
              pass
          self.state = 'stopped'
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception:
      pass

  def validate_stream(self, **kwargs):
    if 'url' in kwargs and kwargs['url']:
      if not validators.url(kwargs['url']):
        raise InvalidStreamField("url", "invalid url")
      if urlparse(kwargs['url']).scheme not in ['http', 'https']:
        raise InvalidStreamField("url", "unsupported protocol/scheme in url")

    # Logo is Optional[str]
    if 'logo' in kwargs and kwargs['logo']:
      if not validators.url(kwargs['logo']):
        raise InvalidStreamField("logo", "invalid logo url")
      if urlparse(kwargs['logo']).scheme not in ['http', 'https']:
        raise InvalidStreamField("logo", "unsupported protocol/scheme in logo url")
