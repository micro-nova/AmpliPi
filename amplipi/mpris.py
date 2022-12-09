"""A module for interfacing with an MPRIS MediaPlayer2 over dbus."""

from dataclasses import dataclass
from enum import Enum, auto
import json
from multiprocessing import Process
import time
from datetime import datetime
from typing import List
from dasbus.connection import SessionMessageBus

from amplipi import utils


METADATA_MAPPINGS = [
  ('artist', 'xesam:artist'),
  ('title', 'xesam:title'),
  ('art_url', 'mpris:artUrl'),
  ('album', 'xesam:album')
]

METADATA_REFRESH_RATE = 0.5
METADATA_FILE_NAME = "metadata.txt"
ERROR_LOG_NAME = "MPRIS_log.txt"

class CommandTypes(Enum):
  PLAY = auto()
  PAUSE = auto()
  NEXT = auto()
  PREVIOUS = auto()

@dataclass
class Metadata:
  """A data class for storing metadata on a song."""
  artist: str = ''
  title: str = ''
  art_url: str = ''
  album: str = ''
  state: str = ''


class MPRIS:
  """A class for interfacing with an MPRIS MediaPlayer2 over dbus."""

  def __init__(self, service_suffix, src, log_fname = None) -> None:
    self.mpris = SessionMessageBus().get_proxy(
        service_name = f"org.mpris.MediaPlayer2.{service_suffix}",
        object_path = "/org/mpris/MediaPlayer2",
        interface_name = "org.mpris.MediaPlayer2.Player"
    )

    self.capabilities: List[CommandTypes] = []

    self.service_suffix = service_suffix
    self.src = src
    self.metadata_path = f'{utils.get_folder("config")}/srcs/{self.src}/{METADATA_FILE_NAME}'

    if log_fname:
      self.log_path = f'{utils.get_folder("config")}/srcs/{self.src}/{log_fname}'
    else:
      self.log_path = None

    try:
      with open(self.metadata_path, "w", encoding='utf-8') as f:
        m = Metadata()
        m.state = "Stopped"
        json.dump(m.__dict__, f)
    except Exception as e:
      self._log("creating metadata file", e)

    self.metadata_process = Process(target=self._metadata_reader)
    self.metadata_process.start()

  def _log(self, message: str, e: Exception):
    if self.log_path:
      with open(self.log_path, 'a', encoding="utf-8") as log_file:
        log_file.write(f"[{datetime.now().isoformat()}] MPRIS error while {message}: {e}\n")

  def play(self) -> None:
    """Plays."""
    self.mpris.Play()

  def pause(self) -> None:
    """Pauses."""
    self.mpris.Pause()

  def next(self) -> None:
    """Skips song."""
    self.mpris.Next()

  def previous(self) -> None:
    """Goes back a song."""
    self.mpris.Previous()

  def play_pause(self) -> None:
    """Plays or pauses depending on current state."""
    self.mpris.PlayPause()

  def _load_metadata(self):
    try:
      with open(self.metadata_path, 'r', encoding='utf-8') as f:
        metadata_dict = json.load(f)
        metadata_obj = Metadata()

        for k in metadata_dict.keys():
          metadata_obj.__dict__[k] = metadata_dict[k]

        return metadata_obj
    except Exception as e:
      self._log("loading metadata file", e)
    return None


  def metadata(self) -> Metadata:
    """Returns metadata from MPRIS."""
    return self._load_metadata()

  def is_playing(self) -> bool:
    """Playing?"""
    return self._load_metadata().state == 'Playing'

  def is_stopped(self) -> bool:
    """Stopped?"""
    return self._load_metadata().state == 'Stopped'

  def get_capabilities(self) -> List[CommandTypes]:
    """Returns a list of supported commands."""

    if len(self.capabilities) == 0:

      if self.mpris.CanPlay:
        self.capabilities.append(CommandTypes.PLAY)

      if self.mpris.CanPause:
        self.capabilities.append(CommandTypes.PAUSE)

      if self.mpris.CanGoNext:
        self.capabilities.append(CommandTypes.NEXT)

      if self.mpris.CanGoPrevious:
        self.capabilities.append(CommandTypes.PREVIOUS)

    return self.capabilities

  def __del__(self):
    try:
      self.metadata_process.kill()
    except Exception as e:
      self._log("shutting down", e)

  def _metadata_reader(self):
    """Method run by the metadata process, also handles playing/paused."""

    mpris = SessionMessageBus().get_proxy(
      service_name = f"org.mpris.MediaPlayer2.{self.service_suffix}",
      object_path = "/org/mpris/MediaPlayer2",
      interface_name = "org.mpris.MediaPlayer2.Player"
    )

    m = Metadata()
    m.state = 'Stopped'

    last_sent = m.__dict__

    while True:
      try:
        raw_metadata = mpris.Metadata
        metadata = {}

        for mapping in METADATA_MAPPINGS:
          try:
            metadata[mapping[0]] = str(raw_metadata[mapping[1]]).strip("[]'")
          except KeyError as e:
            self._log("mapping keys", e)

        metadata['state'] = mpris.PlaybackStatus.strip("'")

        if metadata != last_sent:
          last_sent = metadata
          with open(self.metadata_path, 'w', encoding='utf-8') as metadata_file:
            json.dump(metadata, metadata_file)

      except Exception as e:
        self._log("polling mpris", e)
      time.sleep(1.0/METADATA_REFRESH_RATE)
