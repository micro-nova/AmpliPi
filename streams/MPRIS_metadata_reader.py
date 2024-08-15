"""MPRIS metadata reader, waits for an update on MPRIS interface specified and outputs the
   content to a JSON file."""

import json
import signal
import sys
import time
from typing import Any, Dict, Optional
from dasbus.connection import SessionMessageBus
from dasbus.client.proxy import disconnect_proxy, InterfaceProxy
from dasbus.loop import EventLoop
import logging
import argparse

METADATA_MAPPINGS = [
  ('artist', 'xesam:artist'),
  ('track', 'xesam:title'),
  ('img_url', 'mpris:artUrl'),
  ('album', 'xesam:album')
]

METADATA_RESET_DELAY = 3.0


class MPRISMetadataReader:
  """A class for getting metadata from an MPRIS MediaPlayer2 over dbus."""

  def __init__(self, service_suffix, metadata_path, logger):
    signal.signal(signal.SIGTERM, self.sigterm_handler)

    self.logger = logger

    self.service_suffix = service_suffix
    self.metadata_path = metadata_path

    self.mpris: Optional[InterfaceProxy] = None
    self.properties_changed: Optional[InterfaceProxy] = None

    self.last_sent: Dict[str, Any] = {'state_changed_time': 0, 'state': ''}
    self.last_raw = {}

    self.ok = True

  def sigterm_handler(self, _1: None, _2: None):
    """Handle sigterm."""
    logger.debug(f"MPRIS metadata process for {self.service_suffix} exiting")
    self.ok = False
    sys.exit(0)

  def run(self):
    """Run the mpris metadata process."""

    while self.ok:
      metadata: Dict[str, Any] = {}
      try:
        logger.debug(f'connecting to {self.service_suffix}')

        mpris = SessionMessageBus().get_proxy(
          service_name=f"org.mpris.MediaPlayer2.{self.service_suffix}",
          object_path="/org/mpris/MediaPlayer2",
          interface_name="org.mpris.MediaPlayer2.Player"
        )

        properties_changed = SessionMessageBus().get_proxy(
          service_name=f"org.mpris.MediaPlayer2.{self.service_suffix}",
          object_path="/org/mpris/MediaPlayer2",
          interface_name="org.freedesktop.DBus.Properties"
        )

        def read_metadata(_a, _b, _c):
          logger.debug('reading metadata')

          # grab the raw metadata
          try:
            raw_metadata = mpris.Metadata
          except Exception as e:
            metadata['connected'] = False
            logger.error(f"Dbus error getting MPRIS metadata: {e}")

          # iterate over the metadata mappings and try to add them to the metadata dict
          for mapping in METADATA_MAPPINGS:
            try:
              metadata[mapping[0]] = str(raw_metadata[mapping[1]]).strip("[]'")
            except KeyError as e:
              # not error since some metadata might not be available on all streams
              logger.debug(f"Metadata mapping error: {e}")

          # Strip playback status of single quotes (for some reason these only appear on stopped?)
          # and convert to lowercase
          state = mpris.PlaybackStatus.strip("'").lower()

          metadata['state'] = state

          # if state != self.last_sent['state']:
          #   metadata['state_changed_time'] = time.time()
          # else:
          #   metadata['state_changed_time'] = self.last_sent['state_changed_time']

          metadata['connected'] = True

          self.last_sent = metadata

          with open(self.metadata_path, 'w', encoding='utf-8') as metadata_file:
            json.dump(metadata, metadata_file)

        properties_changed.PropertiesChanged.connect(read_metadata)

        # setup and run event loop
        try:
          loop = EventLoop()
          loop.run()
        except Exception as e:
          logger.error(f"Error running event loop: {e}. Restarting")

      except Exception as e:
        logger.debug(f"Error getting or writing MPRIS metadata to file at {self.metadata_path}: {e}")
        try:
          disconnect_proxy(mpris)
          disconnect_proxy(properties_changed)
        except Exception as e_proxy:
          logger.error(f'Error disconnecting MPRIS/properties proxies: {e_proxy}')
          # if we can't disconnect the proxy, we should probably just stop
          self.ok = False
        finally:
          mpris = None

      # if we get here, something has broken or the stream isn't completely started,
      # if we're still ok then try to restart
      if self.ok:
        # wait a bit before restarting
        time.sleep(METADATA_RESET_DELAY)
      else:
        break

    logger.debug('metadata reader thread stopped')
    if mpris:
      try:
        logger.debug('disconnecting from MPRIS proxy')
        disconnect_proxy(mpris)
        disconnect_proxy(properties_changed)
      except Exception as e:
        logger.error(e)


logger = logging.getLogger(__name__)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

parser = argparse.ArgumentParser(description='Script to read MPRIS metadata and write it to a file.')
parser.add_argument('service_suffix', metavar='service_suffix', type=str, help='end of the MPRIS service name, e.g. "vlc" for org.mpris.MediaPlayer2.vlc')
parser.add_argument('metadata_path', metavar='metadata_path', type=str, help='path to the metadata file')
parser.add_argument('-d', '--debug', action='store_true', help='print debug messages')
args = parser.parse_args()

if args.debug:
  logger.setLevel(logging.DEBUG)

MPRISMetadataReader(args.service_suffix, args.metadata_path, logger).run()
