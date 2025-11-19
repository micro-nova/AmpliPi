"""Script for synchronizing AmpliPi and Spotify volumes"""
import argparse
import json
import logging
import sys
from time import sleep

from volume_synchronizer import VolumeSynchronizer, StreamData

from dasbus.connection import SessionMessageBus


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


class ShairportData(StreamData):
  """A class that watches and tracks changes to spotify-side volume"""

  def __init__(self, service_suffix: str):
    self.mpris = SessionMessageBus().get_proxy(
      service_name=f"org.mpris.MediaPlayer2.{service_suffix}",
      object_path="/org/mpris/MediaPlayer2",
      interface_name="org.mpris.MediaPlayer2.Player"
    )
    super().__init__()

  async def watch_vol(self):
    """Watch the shairport mpris stream for volume changes and update local volume info accordingly"""
    while True:
      try:
        if self.volume is not None and self.volume != self.mpris.Volume:
          self.logger.debug(f"Airplay volume changed from {self.volume} to {self.mpris.Volume}")
          self.callback("stream_volume_changed")
        self.volume = float(self.mpris.Volume)

      except Exception as e:
        self.logger.exception(f"Error: {e}")
        return
      sleep(1)

  def set_vol(self, amplipi_volume: float, shared_vol: float) -> float:
    """Update Airplay's volume slider to match AmpliPi"""
    try:
      # Airplay does not allow external devices to set the volume of a users system

      # There are two values this could realistically return as the new set_point_vol, and they each have their own drawbacks:

      # amplipi_volume: If amplipi_volume is the set point, any changes to airplay volume will send the volume to an odd
      # spot as it just sets the vol average of amplipi to be the same as the value of airplay's vol

      # shared_vol: if shared_vol is the set point, any changes to amplipi will reflect for 1-2 seconds at most and then
      # bounce back to where it had been, resulting in a glitchy front end interface
      return amplipi_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("service_suffix", help="Name of mpris instance", type=str)
  parser.add_argument("stream_id", help="The stream's amplipi side stream_id", type=int)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolumeSynchronizer(ShairportData, {"service_suffix": args.service_suffix}, args.stream_id, args.debug)
  handler.watcher_loop()
