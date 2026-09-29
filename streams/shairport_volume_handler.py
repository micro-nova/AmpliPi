"""Script for synchronizing AmpliPi and AirPlay (shairport-sync) volumes"""
import argparse
from time import sleep
from dasbus.connection import SessionMessageBus
from volume_synchronizer import VolSyncDispatcher, StreamWatcher, VolEvents


class ShairportWatcher(StreamWatcher):
  """A class that watches and tracks changes to airplay-side volume"""

  def __init__(self, service_suffix: str):
    super().__init__()
    self.mpris = SessionMessageBus().get_proxy(
      service_name=f"org.mpris.MediaPlayer2.{service_suffix}",
      object_path="/org/mpris/MediaPlayer2",
      interface_name="org.mpris.MediaPlayer2.Player"
    )

  async def watch_vol(self):
    """Watch the shairport mpris stream for volume changes and update amplipi volume info accordingly"""
    while True:
      try:
        if self.volume != self.mpris.Volume:
          self.logger.debug(f"Airplay volume changed from {self.volume} to {self.mpris.Volume}")
          self.volume = float(self.mpris.Volume)
          self.schedule_event(VolEvents.CHANGE_AMPLIPI)
      except Exception as e:
        self.logger.exception(f"Error: {e}")
        return
      sleep(0.1)

  def set_vol(self, amplipi_volume: float, vol_set_point: float) -> float:
    """Push AmpliPi's volume to the connected AirPlay client.

    shairport-sync's MPRIS "Volume" *property* is read-only (see its own
    org.mpris.MediaPlayer2.xml) - setting it via the standard DBus.Properties.Set does nothing.
    "SetVolume" is a separate DBus *method* shairport-sync exposes alongside it that does work,
    confirmed live: it's the same mechanism amplipi.mpris.MPRIS.set_volume() uses to zero a
    client's volume before disconnecting.
    """
    try:
      if amplipi_volume is None:
        return vol_set_point
      self.mpris.SetVolume(amplipi_volume)
      return amplipi_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")
      return vol_set_point


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Synchronize AmpliPi and AirPlay volume.")

  parser.add_argument("service_suffix", help="Name of mpris instance", type=str)
  parser.add_argument("config_dir", help="The directory of the vsrc config", type=str)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolSyncDispatcher(ShairportWatcher(service_suffix=args.service_suffix), args.config_dir, args.debug)
