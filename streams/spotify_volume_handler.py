"""Script for synchronizing AmpliPi and Spotify volumes"""
import argparse
import json
import logging
import sys

import websockets
import requests

from volume_synchronizer import VolSyncDispatcher, StreamWatcher, VolEvents
from spot_connect_meta import Event


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


class SpotifyWatcher(StreamWatcher):
  """A class that watches and tracks changes to spotify-side volume"""

  def __init__(self, api_port: int):
    super().__init__()

    self.api_port: int = api_port
    """What port is go-librespot running on? Typically set to 3678 + vsrc."""

  async def watch_vol(self):
    """Watch the go-librespot websocket endpoint for volume change events and update AmpliPi volume info accordingly"""
    try:
      # pylint: disable=E1101
      # E1101: Module 'websockets' has no 'connect' member (no-member)
      async with websockets.connect(f"ws://localhost:{self.api_port}/events", open_timeout=5) as websocket:
        while True:
          try:
            msg = await websocket.recv()
            event = Event.from_json(json.loads(msg))
            if event.event_type == "volume":
              last_volume = float(self.volume) if self.volume is not None else None
              self.volume = event.data.value / 100  # Translate spotify volume (0 - 100) to amplipi volume (0 - 1)

              self.logger.debug(f"Spotify volume changed from {last_volume} to {self.volume}")
              if last_volume is not None and self.volume != last_volume:
                self.schedule_event(VolEvents.CHANGE_AMPLIPI)
            elif event.event_type == "will_play" and self.volume is None:
              self.schedule_event(VolEvents.CHANGE_STREAM)  # Intercept the event that occurs when a song starts playing and use that as a trigger for the initial state sync

          except Exception as e:
            self.logger.exception(f"Error: {e}")
            return
    except Exception as e:
      self.logger.exception(f"Error: {e}")
      return

  def set_vol(self, new_vol: float, vol_set_point: float) -> float:
    """Update Spotify's volume slider"""
    try:
      if new_vol is None:
        return vol_set_point

      if abs(new_vol - vol_set_point) <= 0.005 and self.volume is not None:
        self.logger.debug("Ignored minor AmpliPi -> Spotify change")
        return vol_set_point

      url = f"http://localhost:{self.api_port}/player/volume"
      spot_vol = int(new_vol * 100)
      self.logger.debug(f"Setting Spotify volume to {new_vol} from {self.volume}")
      requests.post(url, json={"volume": spot_vol}, timeout=5)
      return new_vol
    except Exception as e:
      self.logger.exception(f"Exception: {e}")


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("port", help="port that go-librespot is running on", type=int)
  parser.add_argument("config_dir", help="The directory of the vsrc config", type=str)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolSyncDispatcher(SpotifyWatcher(api_port=args.port), args.config_dir, args.debug)
