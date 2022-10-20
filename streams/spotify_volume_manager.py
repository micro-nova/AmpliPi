"""File for managing Spotify's volume."""
import json
from threading import Thread
from time import sleep

import requests


VOLUME_SAMPLE_DELAY = 0.5
class SpotVolumeManager(Thread):
  """Class for managing Spotify's volume."""
  def __init__(self, metadata_path: str, sid: int) -> None:
    super().__init__()
    self.okay = True
    self.last_volume = 50
    self.sid = sid

    self.metadata_path = metadata_path
    self.start()

  def __del__(self):
    self.okay = False
    self.stop()

  def stop(self):
    self.okay = False
    self.join()

  def run(self) -> None:
    while self.okay:
      try:
        vol = self.last_volume
        with open(self.metadata_path, 'r', encoding='utf-8' ) as f:
          vol = json.load(f)["volume"]

        if self.last_volume != vol:
          adjustment = (vol-self.last_volume)/100
          requests.post(f"http://localhost:5000/api/sources/{self.sid}/vol_inc/{adjustment}")
          self.last_volume = vol
      except Exception as e:
        print("error changing volume: "+str(e))
      sleep(VOLUME_SAMPLE_DELAY)
