"""A module for interfacing with an MPRIS MediaPlayer2 over dbus."""

from dataclasses import dataclass
from enum import Enum, auto
from tokenize import String
from typing import List
from dasbus.connection import SessionMessageBus
from dasbus.identifier import DBusServiceIdentifier


METADATA_MAPPINGS = [
  ('artist', 'xesam:artist'),
  ('title', 'xesam:title'),
  ('art_url', 'mpris:artUrl'),
  ('album', 'xesam:album')
]

class CommandTypes(Enum):
  PLAY = auto()
  PAUSE = auto()
  NEXT = auto()
  PREVIOUS = auto()

@dataclass
class Metadata:
  """A data class for storing metadata on a song."""
  artist: String = ''
  title: String = ''
  art_url: String = ''
  album: String = ''


class MPRIS:
  """A class for interfacing with an MPRIS MediaPlayer2 over dbus."""

  def __init__(self, service_suffix) -> None:
    self.mpris = SessionMessageBus().get_proxy(
        service_name = f"org.mpris.MediaPlayer2.{service_suffix}",
        object_path = "/org/mpris/MediaPlayer2",
        interface_name = "org.mpris.MediaPlayer2.Player"
    )

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

  def metadata(self) -> Metadata:
    """Returns metadata from MPRIS."""
    raw_metadata = self.mpris.Metadata
    metadata_obj = Metadata()

    for mapping in METADATA_MAPPINGS:
      try:
        metadata_obj.__dict__[mapping[0]] = str(raw_metadata[mapping[1]]).strip("[]'")
      except KeyError:
        pass

    return metadata_obj

  def is_playing(self) -> bool:
    """Playing?"""
    return self.mpris.PlaybackStatus.strip("'") == 'Playing'

  def is_stopped(self) -> bool:
    """Stopped?"""
    return self.mpris.PlaybackStatus.strip("'") == 'Stopped'

  def get_capabilities(self) -> List[CommandTypes]:
    """Returns a list of supported commands."""
    capabilities = []

    if self.mpris.CanPlay:
      capabilities.append(CommandTypes.PLAY)

    if self.mpris.CanPause:
      capabilities.append(CommandTypes.PAUSE)

    if self.mpris.CanGoNext:
      capabilities.append(CommandTypes.NEXT)

    if self.mpris.CanGoPrevious:
      capabilities.append(CommandTypes.PREVIOUS)

    return capabilities
