"""Script for synchronizing AmpliPi and Spotify volumes"""
import argparse
from time import sleep
import json
import asyncio
import threading
import queue

import websockets
import requests

from spot_connect_meta import Event


class SpotifyData:
  """A class that watches and tracks changes to spotify-side volume"""

  def __init__(self, api_port: int, callback, debug: bool = False):
    self.api_port: int = api_port
    self.callback = callback
    self.debug = debug

    self.volume: float = None

    threading.Thread(target=self.run_async_watch, daemon=True).start()

  def run_async_watch(self):
    """Middleman function for creating an asyncio run inside of a new thread"""
    asyncio.run(self.watch_vol())

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
              self.volume = event.data.value / 100  # AmpliPi volume is between 0 and 1, Spotify is between 0 and 100. Dividing by 100 is more accurate than multiplying by 100 due to floating point errors.
              self.callback("spotify_volume_changed")

          except Exception as e:
            print(f"Error: {e}")
            return
    except Exception as e:
      print(f"Error: {e}")
      return


class AmpliPiData:
  """A class to record amplipi's api output and calculate the volume of a given source"""

  def __init__(self, source_id: int, callback, debug: bool = False):
    self.source_id = source_id
    self.callback = callback
    self.debug = debug
    self.status: dict = None
    self.volume: float = None

    self.connected_zones: list = []

    threading.Thread(target=self.get_status, daemon=True).start()

  def get_status(self):
    """Call up the amplipi API and send the output to self.consume_status"""
    while True:
      last_vol = float(self.volume) if self.volume is not None else None

      self.consume_status(requests.get("http://localhost/api", timeout=5).json())

      if last_vol != self.volume:
        self.callback("amplipi_volume_changed")

  def consume_status(self, status):
    """Consume an API response into the local object"""
    self.status = status

    self.connected_zones = [zone for zone in self.status["zones"] if zone["source_id"] == self.source_id]
    self.volume = self.get_volume()

  def get_volume(self):
    """Calculate the average vol_f from all connected zones. If no zones are connected, or if the api has yet to be hit up, return 0."""
    if self.connected_zones:
      total_vol_f = sum([zone["vol_f"] for zone in self.connected_zones])  # Note that accounting for the vol_f overflow variables here would make it impossible to use those overflows while also using this volume bar
      return round(total_vol_f / len(self.connected_zones), 2)  # Round down to 2 decimals to assist with float accuracy
    return 0


class SpotifyVolumeHandler:
  """Volume synchronizer for Spotify and AmpliPi volume sliders"""

  def __init__(self, port, debug=False):
    self.event_queue = queue.Queue()
    self.amplipi = AmpliPiData(port - 3679, self.on_child_event, debug)
    self.spotify = SpotifyData(port, self.on_child_event, debug)
    self.debug: bool = debug

    self.shared_volume = self.amplipi.get_volume()
    self.tolerance = 0.005  # Reduces jitters from floating point inaccuracy from either side

  def on_child_event(self, event_type):
    """When an event occurs in a child, that child can use this callback function to schedule the response to said event in the event queue"""
    self.event_queue.put(event_type)

  def update_amplipi_volume(self):
    """Update AmpliPi's volume via the Spotify client volume slider"""
    spotify_volume = self.spotify.volume
    if spotify_volume is None:
      return

    if abs(spotify_volume - self.shared_volume) <= self.tolerance:
      if self.debug:
        print("Ignored minor Spotify -> AmpliPi change")
      return

    delta = float(spotify_volume - self.shared_volume)
    self.amplipi.consume_status(requests.patch(
      "http://localhost/api/zones",
      json={
        "zones": [zone["id"] for zone in self.amplipi.connected_zones],
        "update": {"vol_delta_f": delta, "mute": False},
      },
      timeout=5,
    ).json())
    self.shared_volume = spotify_volume

  def update_spotify_volume(self):
    """Update Spotify's volume slider to match AmpliPi"""
    amplipi_volume = self.amplipi.volume
    if amplipi_volume is None:
      return

    if abs(amplipi_volume - self.shared_volume) <= self.tolerance:
      if self.debug:
        print("Ignored minor AmpliPi -> Spotify change")
      return

    url = f"http://localhost:{self.spotify.api_port}"
    new_vol = int(amplipi_volume * 100)
    requests.post(url + '/player/volume', json={"volume": new_vol}, timeout=5)
    self.shared_volume = amplipi_volume


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("port", help="The port that go-librespot is running on", type=int)
  parser.add_argument("--debug", action="store_true", help="Enable debug output")

  args = parser.parse_args()

  handler = SpotifyVolumeHandler(args.port, args.debug)
  while True:
    try:
      event = handler.event_queue.get(timeout=2)
      if event in "spotify_volume_changed":
        handler.update_amplipi_volume()
      elif event in "amplipi_volume_changed":
        handler.update_spotify_volume()
    except queue.Empty:
      continue
    except (KeyboardInterrupt, SystemExit):
      print("Exiting...")
      break
    except Exception as e:
      print(f"Error: {e}")
      sleep(5)
      continue
  sleep(2)
