"""Script for synchronizing AmpliPi and Spotify volumes"""
from time import sleep
import json
import asyncio
import threading
import queue
import logging
import sys
from typing import Callable, List

import requests


class StreamData:
  """A class that is used as a blueprint for stream volume watchers"""

  def __init__(self):
    self.callback: Callable

    self.volume: float = None
    self.logger: logging.Logger

    self.thread: threading.Thread = threading.Thread(target=self.run_async_watch, daemon=True).start()

  def run_async_watch(self):
    """Middleman function for creating an asyncio run inside of a new threading.Thread"""
    asyncio.run(self.watch_vol())

  async def watch_vol(self):
    """A function to be implemented by child classes that must contain a while True loop and do self.callback('stream_vol_changed') when new_vol != old_vol"""
    raise NotImplementedError("Function must be implemented by child classes")

  def set_vol(self, new_vol: float, shared_vol: float) -> float:
    """A function to be implemented by child classes to update the stream's volume and returns the new shared volume"""
    raise NotImplementedError("Function must be implemented by child classes")


class AmpliPiData:
  """A class to record amplipi's api output and calculate the volume of a given source"""

  def __init__(self, config_dir: str, callback: Callable, logger: logging.Logger):
    self.callback: Callable = callback
    self.logger: logging.Logger = logger
    self.status: dict = None
    self.volume: float = None
    self.config_dir = config_dir

    self.status_file: str = ""

    self.connected_zones: List[int] = []

    threading.Thread(target=self.get_vol, daemon=True).start()

  def get_vol(self):
    """Calculate the average vol_f from all connected zones. If no zones are connected, or if the api has yet to be hit up, return 0."""
    with open(f'{self.config_dir}/vol', 'r') as fifo:
      while True:
        data = json.loads(fifo.readline().strip())
        if self.volume != data["volume"]:
          self.callback("amplipi_volume_changed")
          self.volume = data["volume"]
        self.connected_zones = data["zones"]

  def set_vol(self, stream_volume: float, vol_set_point: float):
    """Update AmpliPi's volume to match the stream volume"""
    try:
      if stream_volume is None:
        return vol_set_point

      if abs(stream_volume - vol_set_point) <= 0.005:
        self.logger.debug("Ignored minor Stream -> AmpliPi change")
        return vol_set_point

      delta = float(stream_volume - vol_set_point)
      expected_volume = self.volume + delta
      self.logger.debug(f"Setting AmpliPi volume to {expected_volume} from {self.volume}")
      requests.patch(
        "http://localhost/api/zones",
        json={
          "zones": self.connected_zones,
          "update": {"vol_delta_f": delta, "mute": False},
        },
        timeout=5,
      )
      return expected_volume
    except Exception as e:
      self.logger.exception(f"Exception: {e}")


class VolumeSynchronizer:
  """Volume synchronizer for AmpliPi and another volume-providing stream"""

  def __init__(self, stream: StreamData, config_dir: str, debug=False):

    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    sh = logging.StreamHandler(sys.stdout)
    self.logger.addHandler(sh)

    self.event_queue = queue.Queue()
    self.amplipi = AmpliPiData(config_dir, self.on_child_event, self.logger)

    self.stream: StreamData = stream

    # Set these directly so children don't need to add them to their constructors
    self.stream.logger = self.logger
    self.stream.callback = self.on_child_event

    self.vol_set_point = self.amplipi.volume

  def on_child_event(self, event_type):
    """When an event occurs in a child, that child can use this callback function to schedule the response to said event in the event queue"""
    self.event_queue.put(event_type)

  def watcher_loop(self):
    while True:
      try:
        if self.vol_set_point is None:
          self.vol_set_point = self.amplipi.volume

        event = self.event_queue.get()
        if event == "stream_volume_changed":
          self.vol_set_point = self.amplipi.set_vol(self.stream.volume, self.vol_set_point)
        elif event == "amplipi_volume_changed":
          self.vol_set_point = self.stream.set_vol(self.amplipi.volume, self.vol_set_point)
      except queue.Empty:
        continue
      except (KeyboardInterrupt, SystemExit):
        self.logger.exception("Exiting...")
        break
      except Exception as e:
        self.logger.exception(f"Exception: {e}")
        continue
