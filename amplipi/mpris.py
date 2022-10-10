"""A module for interfacing with an MPRIS MediaPlayer2 over dbus."""

from dataclasses import dataclass
from enum import Enum, auto
import json
import time
import os
import sys
from typing import List
from multiprocessing import Process
from dasbus.connection import SessionMessageBus
from dasbus.client.proxy import disconnect_proxy


METADATA_MAPPINGS = [
  ('artist', 'xesam:artist'),
  ('title', 'xesam:title'),
  ('art_url', 'mpris:artUrl'),
  ('album', 'xesam:album')
]

METADATA_REFRESH_RATE = 0.5

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

  def __init__(self, service_suffix, metadata_path) -> None:
    self.mpris = SessionMessageBus().get_proxy(
        service_name = f"org.mpris.MediaPlayer2.{service_suffix}",
        object_path = "/org/mpris/MediaPlayer2",
        interface_name = "org.mpris.MediaPlayer2.Player"
    )

    self.capabilities: List[CommandTypes] = []

    self.service_suffix = service_suffix
    self.metadata_path = metadata_path
    self.ok = True

    try:
      with open(self.metadata_path, "w", encoding='utf-8') as f:
        m = Metadata()
        m.state = "Stopped"
        json.dump(m.__dict__, f)
    except Exception as e:
      print (f'Exception clearing metadata file: {e}')

    try:
      self.metadata_process = Process(target=self._metadata_reader)
      self.metadata_process.start()
    except Exception as e:
      print(f'Exception starting MPRIS metadata process: {e}')

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

  def _load_metadata(self) -> Metadata:
    try:
      with open(self.metadata_path, 'r', encoding='utf-8') as f:
        metadata_dict = json.load(f)
        metadata_obj = Metadata()

        for k in metadata_dict.keys():
          metadata_obj.__dict__[k] = metadata_dict[k]

        return metadata_obj
    except Exception as e:
      print(f"MPRIS loading metadata at {self.metadata_path} failed: {e}")

    return Metadata()


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
    self.ok = False

    try:
      self.metadata_process.kill()
      os.wait() # does this work?
    except Exception as e:
      print(f'Could not stop MPRIS metadata process: {e}')
    disconnect_proxy(self.mpris)

  def _metadata_reader(self):
    """Method run by the metadata process, also handles playing/paused."""

    m = Metadata()
    m.state = 'Stopped'

    last_sent = m.__dict__

    while True:
      mpris = SessionMessageBus().get_proxy(
        service_name = f"org.mpris.MediaPlayer2.{self.service_suffix}",
        object_path = "/org/mpris/MediaPlayer2",
        interface_name = "org.mpris.MediaPlayer2.Player"
      )

      print("getting metadata")
      try:
        raw_metadata = {}
        try:
          raw_metadata = mpris.Metadata
        except Exception as e:
          print(f"Dbus error getting MPRIS metadata: {e}")

        metadata = {}

        for mapping in METADATA_MAPPINGS:
          try:
            metadata[mapping[0]] = str(raw_metadata[mapping[1]]).strip("[]'")
          except KeyError as e:
            print(f"Metadata mapping error: {e}")

        metadata['state'] = mpris.PlaybackStatus.strip("'")

        if metadata != last_sent:
          last_sent = metadata
          with open(self.metadata_path, 'w', encoding='utf-8') as metadata_file:
            json.dump(metadata, metadata_file)

      except Exception as e:
        print(f"Error writing MPRIS metadata to file at {self.metadata_path}: {e}\nThe above is normal if a user is not yet connected to Spotifyd.")

      sys.stdout.flush() # forces stdout to print

      time.sleep(1.0/METADATA_REFRESH_RATE)

      disconnect_proxy(mpris)
