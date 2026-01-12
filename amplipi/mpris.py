"""A module for interfacing with an MPRIS MediaPlayer2 over dbus."""

from dataclasses import dataclass
from enum import Enum, auto
import json
import os
import sys
import logging
from typing import List
import subprocess
# from dasbus.connection import SessionMessageBus
# from dasbus.client.proxy import disconnect_proxy
from amplipi import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


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
  connected: bool = False
  state_changed_time: float = 0


class MPRIS:
  """A class for interfacing with an MPRIS MediaPlayer2 over dbus."""

  def __init__(self, service_suffix, metadata_path) -> None:
    # self.mpris = SessionMessageBus().get_proxy(
    #   service_name=f"org.mpris.MediaPlayer2.{service_suffix}",
    #   object_path="/org/mpris/MediaPlayer2",
    #   interface_name="org.mpris.MediaPlayer2.Player"
    # )

    self.capabilities: List[CommandTypes] = []

    self.service_suffix = service_suffix
    self.metadata_path = metadata_path
    self._closing = False

    try:
      with open(self.metadata_path, "w", encoding='utf-8') as f:
        m = Metadata()
        m.state = "Stopped"
        json.dump(m.__dict__, f)
    except Exception as e:
      logger.exception(f'Exception clearing metadata file: {e}')

    try:
      child_args = [sys.executable,
                    f"{utils.get_folder('streams')}/MPRIS_metadata_reader.py",
                    self.service_suffix,
                    self.metadata_path]

      self.metadata_process = subprocess.Popen(args=child_args, stdout=sys.stdout, stderr=sys.stderr)
    except Exception as e:
      logger.exception(f'Exception starting MPRIS metadata process: {e}')

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
      logger.exception(f"MPRIS loading metadata at {self.metadata_path} failed: {e}")

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

  def is_connected(self) -> bool:
    """Returns true if we can talk to the MPRIS dbus object."""
    return self._load_metadata().connected

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

  def close(self):
    """Closes the MPRIS object."""

    if self.metadata_process:
      self.metadata_process.terminate()
      if self.metadata_process.wait(1) != 0:
        logger.info('Failed to stop MPRIS metadata process, killing')
        self.metadata_process.kill()
      self.metadata_process.communicate()

    self.metadata_process = None

    if self.mpris:
      logger.info('disconnecting proxy')
      # disconnect_proxy(self.mpris)
    self.mpris = None
    logger.info("mpris closed")

    try:
      os.remove(self.metadata_path)
    except FileNotFoundError:
      pass
    except Exception as e:
      logger.exception(f'Could not remove metadata file: {e}')
    logger.info(f'Closed MPRIS {self.service_suffix}')

  def __del__(self):
    self.close()
