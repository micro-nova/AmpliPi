
import argparse
from time import sleep
import requests


class SpotifyData:

  def __init__(self, api_port, debug=False):
    self.api_port: int = api_port
    self.debug = debug

    self.status: dict = self.get_status()
    self.last_volume: int = self.get_volume()

  def get_status(self):
    self.status = requests.get(f"http://localhost:{self.api_port}/status", timeout=5).json()

  def get_volume(self):  # Not terribly useful, but it's nice to have parity with the AmpliPiData object
    if self.status:
      if self.debug:
        print(f"Got Spotify volume: {self.status['volume']}")
      return self.status["volume"]


class AmpliPiData:

  def __init__(self, source_id, debug=False):
    self.source_id = source_id
    self.debug = debug

    self.status: dict = self.get_status()
    self.last_volume: float = self.get_volume()

    self.connected_zones: list = []

  def get_status(self):
    self.status = requests.get("http://localhost/api", timeout=5).json()

    self.connected_zones = [zone for zone in self.status["zones"] if zone["source_id"] == self.source_id]

  def get_volume(self):
    if self.connected_zones:
      total_vol_f = 0
      for zone in self.connected_zones:
        total_vol_f += zone["vol_f"]
      if self.debug:
        print(f"Got AmpliPi volume: {total_vol_f / len(self.connected_zones)}")
      return total_vol_f / len(self.connected_zones)


class SpotifyVolumeHandler:

  def __init__(self, port, debug=False):
    self.amplipi = AmpliPiData(port - 3679, debug)
    self.spotify = SpotifyData(port, debug)
    self.debug: bool = debug

  def update_amplipi_volume(self, volume):
    """Update AmpliPi's volume via the Spotify client volume slider"""
    delta = float((volume - self.spotify.last_volume) / 100)
    requests.patch("http://localhost/api/zones", json={"zones": [zone["id"] for zone in self.amplipi.connected_zones], "update": {"vol_delta_f": delta, "mute": False}}, timeout=5)
    self.spotify.last_volume = volume

  def update_spotify_volume(self, volume):
    """Update the Spotify client's volume slider position based on the averaged volume of all connected zones in AmpliPi"""
    if self.debug:
      print(f"Spotify vol updated: {volume}")
    url = f"http://localhost:{self.spotify.api_port}"
    new_vol = int(volume * 100)
    print(f"vol: {volume}, last_vol: {self.amplipi.last_volume}")
    requests.post(url + '/player/volume', json={"volume": new_vol}, timeout=5)
    self.amplipi.last_volume = volume
    self.spotify.last_volume = new_vol

  def get_statuses(self):
    self.amplipi.get_status()
    if self.amplipi.last_volume is None:
      self.amplipi.last_volume = self.amplipi.get_volume()

    self.spotify.get_status()
    if self.spotify.last_volume is None:
      self.spotify.last_volume = self.spotify.get_volume()

  def handle_volumes(self):
    while True:
      try:
        self.get_statuses()
        amplipi_volume = self.amplipi.get_volume()
        spotify_volume = self.spotify.get_volume()

        if self.debug:
          print(f"amplipi: {amplipi_volume}, last: {self.amplipi.last_volume}")
          print(f"spotify: {spotify_volume}, last: {self.spotify.last_volume}")
          print("\n\n\n")
        if spotify_volume != self.spotify.last_volume:
          if self.debug:
            print("Updating spotify vol...")
          self.update_amplipi_volume(spotify_volume)
        elif amplipi_volume != self.amplipi.last_volume or int(amplipi_volume * 100) != spotify_volume:
          if self.debug:
            print("Updating amplipi vol...")
          self.update_spotify_volume(amplipi_volume)
      except Exception as e:
        print(f"ERROR: {e}")
      sleep(2)


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("port", help="The port that go-librespot is running on", type=int)
  parser.add_argument("--debug", action="store_true", help="Enable debug output")

  args = parser.parse_args()

  while (True):
    try:
      SpotifyVolumeHandler(args.port, args.debug).handle_volumes()
    except (KeyboardInterrupt, SystemExit):
      print("Exiting...")
      break
    except Exception as e:
      print(f"Error: {e}")
      sleep(5)
      continue
