"""Script for synchronizing AmpliPi and Spotify volumes"""
import argparse
import json
import logging
import sys

import websockets
import requests

from volume_synchronizer import VolumeSynchronizer, StreamData
from spot_connect_meta import Event


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


class SpotifyData(StreamData):
  """A class that watches and tracks changes to spotify-side volume"""

  def __init__(self, api_port: int):
    self.api_port: int = api_port
    super().__init__()

  async def watch_vol(self):
    """Watch the go-librespot websocket endpoint for volume change events and update local volume info accordingly"""
    try:
      # Connect to the websocket and listen for state changes
      # pylint: disable=E1101
      # E1101: Module 'websockets' has no 'connect' member (no-member)
      async with websockets.connect(f"ws://localhost:{self.api_port}/events", open_timeout=5) as websocket:
        while True:
          try:
            msg = await websocket.recv()
            event = Event.from_json(json.loads(msg))
            if event.event_type == "volume":
              last_volume = float(self.volume) if self.volume is not None else None
              self.volume = event.data.value / 100  # AmpliPi volume is between 0 and 1, Spotify is between 0 and 100. Dividing by 100 is more accurate than multiplying by 100 due to floating point errors.

              self.logger.debug(f"Spotify volume changed from {last_volume} to {self.volume}")
              if last_volume is not None and self.volume != last_volume:
                self.callback("stream_volume_changed")
            elif event.event_type == "will_play" and self.volume is None:
              self.callback("amplipi_volume_changed")  # Intercept the event that occurs when a song starts playing and use that as a trigger for the initial state sync

          except Exception as e:
            self.logger.exception(f"Error: {e}")
            return
    except Exception as e:
      self.logger.exception(f"Error: {e}")
      return

  def set_vol(self, amplipi_volume: float, shared_volume: float) -> float:
    """Update Spotify's volume slider to match AmpliPi"""
    try:
      if amplipi_volume is None:
        return shared_volume

      if abs(amplipi_volume - shared_volume) <= 0.005 and self.volume is not None:
        self.logger.debug("Ignored minor AmpliPi -> Spotify change")
        return shared_volume

      url = f"http://localhost:{self.api_port}/player/volume"
      new_vol = int(amplipi_volume * 100)
      self.logger.debug(f"Setting Spotify volume to {new_vol / 100} from {self.volume}")
      requests.post(url, json={"volume": new_vol}, timeout=5)
      return amplipi_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("port", help="port that go-librespot is running on", type=int)
  parser.add_argument("stream_id", help="The stream's amplipi side stream_id", type=int)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolumeSynchronizer(SpotifyData, {"api_port": args.port}, args.stream_id, args.debug)
  handler.watcher_loop()
