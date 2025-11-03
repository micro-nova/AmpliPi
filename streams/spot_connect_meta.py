"""Spotify metadata reader for interfacing with go-librespot's API

Based on go-librespot's API docs: https://github.com/devgianlu/go-librespot/blob/master/API.md
"""

import argparse
import inspect
from typing import List, Optional, Union
from dataclasses import dataclass, field, asdict
from time import sleep
import json
import requests
from websockets.exceptions import ConnectionClosed, InvalidHandshake
from websockets.sync.client import connect


@dataclass
class Track:
  """Track metadata"""
  context_uri: str = ''  # Where is this event coming from?
  uri: str = ''  # Track URI
  name: str = ''  # Track name
  artist_names: List[str] = field(default_factory=list)  # List of track artist names
  album_name: str = ''  # Track album name
  album_cover_url: str = ''  # Track album cover image URL
  position: int = 0  # Track position in milliseconds
  duration: int = 0  # Track duration in milliseconds
  release_date: str = ''
  track_number: int = 0
  disc_number: int = 0

  @classmethod
  def from_dict(cls, env):
    """Convert a dictionary to a Track instance ignoring extra unknown fields"""
    return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})


@dataclass()
class Status:
  """Spotify status"""
  username: str = ''  # Currently active account's username
  device_id: str = ''  # The player device ID
  device_name: str = ''  # The player device name
  play_origin: str = ''  # Who started the playback, "go-librespot" identifies the API as the play origin, everything else is Spotify own stuff
  stopped: bool = False  # Whether the player is stopped
  paused: bool = False  # Whether the player is paused
  buffering: bool = False  # Whether the player is buffering
  volume: int = 0  # The player current volume from 0 to max
  volume_steps: int = 0  # The player max volume value
  repeat_context: bool = False  # Whether the repeat context feature is enabled
  repeat_track: bool = False  # Whether the repeat track feature is enabled
  shuffle_context: bool = False  # Whether the shuffle context feature is enabled
  track: Track = field(default_factory=Track)  # Track metadata

  @classmethod
  def from_dict(cls, env):
    """Convert a dictionary to a Status instance ignoring extra unknown fields"""
    return cls(**{k: v for k, v in env.items() if k in inspect.signature(cls).parameters})


@dataclass
class OriginChange:
  """Origin change event"""
  context_uri: str = ''  # Where is this event coming from?
  play_origin: str = ''  # Who started the playback


@dataclass
class PlayChange(OriginChange):
  """Play change event"""
  uri: str = ''  # Track URI
  resume: bool = False


@dataclass
class SeekChange(PlayChange):
  """Seek change event"""
  position: int = 0  # Track position in milliseconds
  duration: int = 0  # Track duration in milliseconds


@dataclass
class VolumeChange:
  """Volume change event"""
  value: int = 0  # The volume, ranging from 0 to max
  max: int = 0  # The max volume value


@dataclass
class ValueChange:
  """Value change event"""
  value: bool = False


@dataclass
class Event:
  """
  The websocket endpoint is available at /events. The following events are emitted:

      active: The device has become active
      inactive: The device has become inactive
      metadata: A new track was loaded, the following metadata is available:
          uri: Track URI
          name: Track name
          artist_names: List of track artist names
          album_name: Track album name
          album_cover_url: Track album cover image URL
          position: Track position in milliseconds
          duration: Track duration in milliseconds
      will_play: The player is about to play the specified track
          uri: The track URI
          play_origin: Who started the playback
      playing: The current track is playing
          uri: The track URI
          play_origin: Who started the playback
      not_playing: The current track has finished playing
          uri: The track URI
          play_origin: Who started the playback
      paused: The current track is paused
          uri: The track URI
          play_origin: Who started the playback
      stopped: The current context is empty, nothing more to play
          play_origin: Who started the playback
      seek: The current track was seeked, the following data is provided:
          uri: The track URI
          position: Track position in milliseconds
          duration: Track duration in milliseconds
          play_origin: Who started the playback
      volume: The player volume changed, the following data is provided:
          value: The volume, ranging from 0 to max
          max: The max volume value
      shuffle_context: The player shuffling context setting changed
          value: Whether shuffling context is enabled
      repeat_context: The player repeating context setting changed
          value: Whether repeating context is enabled
      repeat_track: The player repeating track setting changed
          value: Whether repeating track is enabled

  """
  event_type: str
  data: Union[None, Track, PlayChange, VolumeChange, SeekChange, ValueChange] = None

  @staticmethod
  def from_json(parent: "SpotifyMetadataReader", json_data: dict) -> "Event":
    """Create an Event object from a JSON payload"""
    e = Event(event_type=json_data["type"])
    if e.event_type in ["active", "inactive"]:
      e.data = None
    elif e.event_type == "metadata":
      # there are a fair number of extra fields spotify generates, ignore them
      e.data = Track.from_dict(json_data["data"])
    elif e.event_type in ["will_play", "playing", "not_playing", "paused"]:
      e.data = PlayChange(**json_data["data"])
    elif e.event_type == "stopped":
      e.data = OriginChange(**json_data["data"])
    elif e.event_type == "seek":
      e.data = SeekChange(**json_data["data"])
    elif e.event_type == "volume":
      e.data = VolumeChange(**json_data["data"])
    elif e.event_type in ["shuffle_context", "repeat_context", "repeat_track"]:
      e.data = ValueChange(**json_data["data"])
    return e


class SpotifyMetadataReader:

  def __init__(self, url, metadata_file, debug=False):
    self.url: str = url
    self.metadata_file: str = metadata_file
    self.debug: bool = debug
    self._api_port: int = 3678 + int([char for char in metadata_file if char.isdigit()][0])

  def read_metadata(self) -> Optional[Status]:
    """
    Reads metadata from the given URL and writes it to the specified metadata file.
    If the metadata file already exists, it will be overwritten.
    """
    endpoint = self.url + "/status"

    # Send a GET request to the URL to retrieve the metadata
    response = requests.get(endpoint, timeout=2)

    # Check if the request was successful
    if response.status_code == 200:
      # Parse the metadata from the response
      return Status.from_dict(response.json())
    elif response.status_code == 204:
      # the metadata isn't populated yet
      return Status(stopped=True)
    else:
      # If the request failed, print an error message
      print(f"Failed to retrieve metadata from {endpoint}. Status code: {response.status_code}")
      return Status()

  def watch_metadata(self) -> None:
    """
    Watches the api at `url` for metadata updates and writes the current state to `metadata_file`.
    If the metadata file already exists, it will be overwritten.
    """
    # Get the websocket-based event updates
    ws_events = self.url.replace("http://", "ws://") + "/events"
    try:
      # read the initial state
      metadata = self.read_metadata()
      with open(self.metadata_file, 'w', encoding='utf8') as mf:
        mf.write(json.dumps(asdict(metadata)))
      if self.debug:
        print(f"Initial metadata: {metadata}")
      # Connect to the websocket and listen for state changes
      with connect(ws_events, open_timeout=5) as websocket:
        while True:
          try:
            msg = websocket.recv()
            if self.debug:
              print(f"Received: {msg}")
            event = Event.from_json(self, json.loads(msg))
            if event.event_type == "metadata":
              metadata.track = event.data
            elif event.event_type == "playing":
              metadata.stopped = False
              metadata.paused = False
            elif event.event_type == "paused":
              metadata.paused = True
            elif event.event_type == "stopped":
              metadata.stopped = True
              metadata.track = Track()
            else:
              continue
            with open(args.metadata_file, 'w', encoding='utf8') as mf:
              mf.write(json.dumps(asdict(metadata)))
          except (KeyError, ConnectionClosed, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            break
    except (OSError, InvalidHandshake, TimeoutError) as e:
      print(f"Error: {e}")
      return


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("url", help="URL of the metadata to retrieve")
  parser.add_argument("metadata_file", help="File to write the metadata to", default="metadata.json", type=str)
  parser.add_argument("--debug", action="store_true", help="Enable debug output")

  args = parser.parse_args()

  while (True):
    try:
      SpotifyMetadataReader(args.url, args.metadata_file, args.debug).watch_metadata()
    except (KeyboardInterrupt, SystemExit):
      print("Exiting...")
      break
    sleep(5)  # wait a bit before checking again
