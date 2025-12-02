"""Script for synchronizing AmpliPi and Spotify volumes"""
import json
import asyncio
import threading
import queue
import logging
import sys
from typing import Callable, List, Optional
from enum import Enum
import requests


class VolEvents(Enum):
  CHANGE_STREAM = "change_stream"
  CHANGE_AMPLIPI = "change_amplipi"


class StreamData:
  """
    A class that is used as a blueprint for stream volume watchers
    Child classes must provide the following functions. Both of these functions are automatically used by the VolumeSynchronizer, so there's no need to do anything with them:

    watch_vol: a function that contains a while True loop that collects the remote volume, sets self.volume, and calls self.schedule_event(VolEvents.CHANGE_AMPLIPI) when the volume changes

    set_vol: a function that takes the new_volume as well as the previous volume_set_point (both floats) and returns the new set point volume (either the previous set point if the change was unsuccessful or the newly recognized volume)
  """

  def __init__(self):
    self.schedule_event: Callable[[VolEvents]]
    """Event scheduler function provided by VolumeSynchronizer, has limited valid inputs that can be seen in the VolEvents enum"""

    self._volume: float = None
    """Value between 0 and 1, or None if not yet initialized by the upstream"""

    self.logger: logging.Logger
    """logging.Logger instance provided by VolumeSynchronizer,"""

    self.thread: threading.Thread = threading.Thread(target=self.run_async_watch, daemon=True).start()

  @property
  def volume(self) -> Optional[float]:
    """Value between 0 and 1, or None if not yet initialized by the upstream"""
    return self._volume

  @volume.setter
  def volume(self, value: float) -> None:
    if 0 > value or value > 1:
      raise ValueError("Volume must be between 0 and 1")
    self._volume = value

  def run_async_watch(self):
    """Middleman function for creating an asyncio run inside of a new threading.Thread"""
    asyncio.run(self.watch_vol())

  async def watch_vol(self):
    """A function to be implemented by child classes that must contain a while True loop and do self.schedule_event(VolEvents.CHANGE_AMPLIPI) when new_vol != old_vol"""
    raise NotImplementedError("Function must be implemented by child classes")

  def set_vol(self, new_vol: float, shared_vol: float) -> float:
    """A function to be implemented by child classes to update the stream's volume and returns the new set point volume"""
    raise NotImplementedError("Function must be implemented by child classes")


class AmpliPiData:
  """
    A class to watch changes to a streams vol fifo and change the volume of connected zones
    Already fully handled by volumeSynchronizer and should not be used by itself
  """

  def __init__(self, config_dir: str, schedule_event: Callable, logger: logging.Logger):
    self.schedule_event: Callable[[VolEvents]] = schedule_event
    """Event scheduler function provided by VolumeSynchronizer, has limited valid inputs that can be seen in the VolEvents enum"""

    self.logger: logging.Logger = logger
    self.volume: float = None
    self.config_dir: str = config_dir

    self.connected_zones: List[int] = []  # List of zone ids, used to send volume change requests to these connected zones

    threading.Thread(target=self.get_vol, daemon=True).start()

  def get_vol(self):
    """
      Read the volume FIFO from .config/amplipi/srcs/v{vsrc}/vol to load the currently connected zones and the averaged volume of them
      If the read volume is different than the previous volume, send a volume change event to the stream
    """
    with open(f'{self.config_dir}/vol', 'r') as fifo:
      while True:
        data = json.loads(fifo.readline().strip())
        if self.volume != data["volume"]:
          self.volume = data["volume"]
          self.schedule_event(VolEvents.CHANGE_STREAM)
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
  """
    Volume synchronizer for AmpliPi and another volume-providing stream

    Takes a few args:

    stream: A fully constructed instance of a class that extends StreamData

    config_dir: the path to the .config/amplipi/srcs/v{vsrc} folder for this persistent stream

    debug: bool that decides whether log level is DEBUG (if True) or WARNING (if False). False by default.


    Example Usage:

      class SomeStream(StreamData):
        __init__(**kwargs):
          super().__init__()
          ...

        def get_vol(self):
          ...

        def set_vol(self, new_vol: float, vol_set_point: float):
          ...

        {
          build argsparser here
        }

        handler = VolumeSynchronizer(SomeStream(**kwargs), args.config_dir, args.debug)
        handler.watcher_loop()
  """

  # All you need to do to use this class is build a StreamData extension and then follow the above example with a simple argsparse flow, everything else is handled automatically

  def __init__(self, stream: StreamData, config_dir: str, debug=False):

    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    sh = logging.StreamHandler(sys.stdout)
    self.logger.addHandler(sh)

    self.event_queue = queue.Queue()
    self.amplipi = AmpliPiData(config_dir, self.schedule_event, self.logger)

    self.stream: StreamData = stream

    # Set these directly so children don't need to add them to their constructors
    self.stream.logger = self.logger
    self.stream.schedule_event = self.schedule_event

    self.vol_set_point = self.amplipi.volume

  def schedule_event(self, event_type: VolEvents):
    """When an event occurs in a child, that child can use this callback function to schedule the response to said event in the event queue"""
    self.event_queue.put(event_type)

  def watcher_loop(self):
    """Watch for events coming from amplipi and the stream to then change the volume of the other"""
    while True:
      try:
        if self.vol_set_point is None:
          self.vol_set_point = self.amplipi.volume

        event = self.event_queue.get()
        if event == VolEvents.CHANGE_AMPLIPI:
          self.vol_set_point = self.amplipi.set_vol(self.stream.volume, self.vol_set_point)
        elif event == VolEvents.CHANGE_STREAM:
          self.vol_set_point = self.stream.set_vol(self.amplipi.volume, self.vol_set_point)
      except queue.Empty:
        continue
      except (KeyboardInterrupt, SystemExit):
        self.logger.exception("Exiting...")
        break
      except Exception as e:
        self.logger.exception(f"Exception: {e}")
        continue
