"""Script for synchronizing AmpliPi and Bluetooth (AVRCP absolute volume) volumes"""
import argparse
from time import sleep
from typing import Optional
from dasbus.connection import SystemMessageBus
from volume_synchronizer import VolSyncDispatcher, StreamWatcher, VolEvents

# AVRCP absolute volume is a 7-bit value (0-127), per org.bluez.MediaTransport1.Volume
MAX_AVRCP_VOLUME = 127


def _find_transport_path(bus: SystemMessageBus, mac: str) -> Optional[str]:
  """Find the org.bluez.MediaTransport1 object path for the connected device with @mac, if any.
  Enumerates every BlueZ-managed object - expensive enough that callers should cache the result
  rather than call this on every poll."""
  device_fragment = f"dev_{mac.replace(':', '_')}"
  manager = bus.get_proxy("org.bluez", "/", interface_name="org.freedesktop.DBus.ObjectManager")
  for path, interfaces in manager.GetManagedObjects().items():
    if "org.bluez.MediaTransport1" in interfaces and device_fragment in path:
      return path
  return None


class BluetoothWatcher(StreamWatcher):
  """A class that watches and tracks changes to the connected device's AVRCP absolute volume"""

  def __init__(self, device_info_path: str):
    super().__init__()
    self.device_info_path = device_info_path
    """File written by streams/bluetooth.py with the currently-selected device's MAC - same file
    send_cmd() already relies on to target the right device."""
    self.bus = SystemMessageBus()  # BlueZ lives on the system bus, not the session bus MPRIS/Spotify use
    self._cached_mac: Optional[str] = None
    self._cached_transport = None

  def _current_mac(self) -> Optional[str]:
    try:
      with open(self.device_info_path, "rt", encoding="utf-8") as f:
        return f.readline().strip() or None
    except IOError:
      return None

  def _transport(self):
    """The currently-selected device's MediaTransport1 proxy. Cached, and only re-resolved (a full
    BlueZ object enumeration) when the selected device's MAC changes or the cached proxy stops
    working - polling this every 100ms otherwise pegs a CPU core for no reason."""
    mac = self._current_mac()
    if not mac:
      self._cached_mac, self._cached_transport = None, None
      return None
    if mac != self._cached_mac or self._cached_transport is None:
      path = _find_transport_path(self.bus, mac)
      self._cached_mac = mac
      self._cached_transport = (
        self.bus.get_proxy("org.bluez", path, interface_name="org.bluez.MediaTransport1") if path else None
      )
    return self._cached_transport

  async def watch_vol(self):
    """Poll the connected device's AVRCP absolute volume for changes and update AmpliPi volume info accordingly"""
    while True:
      try:
        transport = self._transport()
        if transport is not None:
          new_volume = transport.Volume / MAX_AVRCP_VOLUME
          if self.volume != new_volume:
            self.logger.debug(f"Bluetooth volume changed from {self.volume} to {new_volume}")
            self.volume = new_volume
            self.schedule_event(VolEvents.CHANGE_AMPLIPI)
      except Exception as e:
        self.logger.exception(f"Error: {e}")
        self._cached_transport = None  # force re-resolution - the cached proxy may be stale
      sleep(0.1)

  def set_vol(self, amplipi_volume: float, vol_set_point: float) -> float:
    """Push AmpliPi's volume to the connected device via AVRCP absolute volume"""
    try:
      if amplipi_volume is None:
        return vol_set_point
      transport = self._transport()
      if transport is None:
        return vol_set_point
      transport.Volume = round(amplipi_volume * MAX_AVRCP_VOLUME)
      return amplipi_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")
      self._cached_transport = None
      return vol_set_point


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Synchronize AmpliPi and Bluetooth (AVRCP) volume.")

  parser.add_argument("device_info_path", help="Path to the file tracking the currently-connected device's MAC", type=str)
  parser.add_argument("config_dir", help="The directory of the vsrc config", type=str)
  parser.add_argument("--debug", action="store_true", help="Change log level from WARNING to DEBUG")

  args = parser.parse_args()

  handler = VolSyncDispatcher(BluetoothWatcher(device_info_path=args.device_info_path), args.config_dir, args.debug)
