
import argparse
from time import sleep
import requests
import websockets
from spot_connect_meta import Event
import json
import asyncio
import threading


class SpotifyData:

  def __init__(self, api_port, debug=False):
    self.api_port: int = api_port
    self.debug = debug

    self.volume: int = None

    threading.Thread(target=self.run_async_watch, daemon=True).start()

  def run_async_watch(self):
    asyncio.run(self.watch_vol())

  async def watch_vol(self):
    try:
      # Connect to the websocket and listen for state changes
      async with websockets.connect(f"ws://localhost:{self.api_port}/events", open_timeout=5) as websocket:
        while True:
          print("Watching volume!")
          try:
            msg = await websocket.recv()
            event = Event.from_json(json.loads(msg))
            if event.event_type == "volume":
              self.volume = event.data.value

          except Exception as e:
            print(f"Error: {e}")
            return
    except Exception as e:
      print(f"Error: {e}")
      return


class AmpliPiData:

  def __init__(self, source_id, debug=False):
    self.source_id = source_id
    self.debug = debug
    self.status: dict = None

    self.connected_zones: list = []

  def get_status(self):
    self.status = requests.get("http://localhost/api", timeout=5).json()

    self.connected_zones = [zone for zone in self.status["zones"] if zone["source_id"] == self.source_id]

  def get_volume(self):
    if not self.status:
      self.get_status()

    if self.connected_zones:
      total_vol_f = sum([zone["vol_f"] for zone in self.connected_zones])
      return round(total_vol_f / len(self.connected_zones), 3)  # Round down to 2 decimals


class SpotifyVolumeHandler:

  def __init__(self, port, debug=False):
    self.amplipi = AmpliPiData(port - 3679, debug)
    self.spotify = SpotifyData(port, debug)
    self.debug: bool = debug
    self.shared_volume = self.amplipi.get_volume()

  def update_amplipi_volume(self, amplipi_volume):
    """Update AmpliPi's volume via the Spotify client volume slider"""
    delta = float((self.spotify.volume / 100) - amplipi_volume)
    requests.patch("http://localhost/api/zones", json={"zones": [zone["id"] for zone in self.amplipi.connected_zones], "update": {"vol_delta_f": delta, "mute": False}}, timeout=5)
    self.shared_volume = self.spotify.volume / 100

  def update_spotify_volume(self, amplipi_volume):
    """Update the Spotify client's volume slider position based on the averaged volume of all connected zones in AmpliPi"""
    if self.debug:
      print(f"Spotify vol updated: {amplipi_volume}")
    url = f"http://localhost:{self.spotify.api_port}"
    new_vol = int(amplipi_volume * 100)
    requests.post(url + '/player/volume', json={"volume": new_vol}, timeout=5)
    self.shared_volume = amplipi_volume

  def handle_volumes(self):
    while True:
      try:
        self.amplipi.get_status()
        amplipi_volume = self.amplipi.get_volume()

        if self.debug:
          print(f"amplipi: {amplipi_volume}, spotify: {self.spotify.volume}, shared: {self.shared_volume}")
          print("\n\n\n")

        if self.spotify.volume is None:  # Useful for getting spotify's initial state (by forcibly setting it)
          self.update_spotify_volume(amplipi_volume)
        elif self.spotify.volume != (self.shared_volume * 100):
          if self.debug:
            print("Updating AmpliPi vol...")
          self.update_amplipi_volume(amplipi_volume)
        elif amplipi_volume != self.shared_volume or (int(amplipi_volume * 100) != self.spotify.volume):
          if self.debug:
            print("Updating Spotify vol...")
          self.update_spotify_volume(amplipi_volume)
      except Exception as e:
        print(f"Error: {e}")
      sleep(2)


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("port", help="The port that go-librespot is running on", type=int)
  parser.add_argument("--debug", action="store_true", help="Enable debug output")

  args = parser.parse_args()

  handler = SpotifyVolumeHandler(args.port, args.debug)
  while (True):
    try:
      handler.handle_volumes()
    except (KeyboardInterrupt, SystemExit):
      print("Exiting...")
      break
    except Exception as e:
      print(f"Error 139: {e}")
      sleep(5)
      continue
