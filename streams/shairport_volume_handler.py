"""Script for synchronizing AmpliPi and Spotify volumes"""
import argparse
from time import sleep
from dasbus.connection import SessionMessageBus
from dasbus.typing import Variant
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

    self.dbus = SessionMessageBus().get_proxy(
      service_name=f"org.mpris.MediaPlayer2.{service_suffix}",
      object_path="/org/mpris/MediaPlayer2",
      interface_name="org.freedesktop.DBus.Properties"
    )

  async def watch_vol(self):
    """Watch the shairport mpris stream for volume changes and update amplipi volume info accordingly"""
    while True:
      try:
        if self.volume != self.mpris.Volume:
          self.logger.debug(f"Airplay volume changed from {self.volume} to {self.mpris.Volume}")
          self.volume = float(self.mpris.Volume)
          self.schedule_event(VolEvents.CHANGE_AMPLIPI)
          # self.delta = self.mpris.Volume - self.volume

      except Exception as e:
        self.logger.exception(f"Error: {e}")
        return
      sleep(0.1)

  def set_vol(self, amplipi_volume: float, vol_set_point: float) -> float:  # This has unused variable vol_set_point to keep up with the underlying StreamData.set_vol function schema
    """Update Airplay's volume slider to match AmpliPi"""
    try:
      # Airplay does not allow external devices to set the volume of a users system

      # Airplay is a fully authoritative volume source, meaning it forces amplipi volume to equal its volume now. If that ever changes, this will be relevant:
        # There are two values this could realistically be returned and become the new vol_set_point, and they each have their own drawbacks:

        # amplipi_volume: If amplipi_volume is the new set point, any changes to airplay volume will send the volume to an odd
        # spot as it just sets the vol average of amplipi to be the same as the value of airplay's vol

        # vol_set_point: if vol_set_point is retained as the set point, any changes to amplipi will reflect for 1-2 seconds at most and then
        # bounce back to where it had been, resulting in a glitchy front end interface

      # In any future MPRIS based volume synchronizers, you can check if self.mpris.CanControl is true and then potentially directly set self.mpris.Volume
      # Note that we cannot do this due to this line: <property name='Volume' type='d' access='read'/>
      # That exists in the MPRIS config xml at https://github.com/mikebrady/shairport-sync/blob/master/org.mpris.MediaPlayer2.xml

      # self.dbus.Set(
      #   'org.mpris.MediaPlayer2',
      #   'Volume',
      #   Variant("d", amplipi_volume)
      # )

      return amplipi_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Read metadata from a given URL and write it to a file.")

  parser.add_argument("service_suffix", help="Name of mpris instance", type=str)
  parser.add_argument("config_dir", help="The directory of the vsrc config", type=str)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolSyncDispatcher(ShairportWatcher(service_suffix=args.service_suffix), args.config_dir, args.debug)
