
"""File run by the mpris interface."""
import json
import signal
import sys
import time
from typing import Any, Dict, Optional
from dasbus.connection import SessionMessageBus
from dasbus.client.proxy import disconnect_proxy, InterfaceProxy
METADATA_MAPPINGS = [
  ('artist', 'xesam:artist'),
  ('title', 'xesam:title'),
  ('art_url', 'mpris:artUrl'),
  ('album', 'xesam:album')
]

METADATA_REFRESH_RATE = 0.5

class mpris_child_proc:
  def __init__(self, service_suffix, metadata_path):
    signal.signal(signal.SIGTERM, self.sigterm_handler)

    self.service_suffix = service_suffix
    self.metadata_path = metadata_path

    self.mpris: Optional[InterfaceProxy] = None

    self.last_sent = {
      'artist'              : '',
      'title'               : '',
      'art_url'             : '',
      'album'               : '',
      'state'               : 'stopped',
      'connected'           : False,
      'state_changed_time'  : 0
    }

    self.ok = True


  def sigterm_handler(self):
    """Handle sigterm."""
    print(f"MPRIS metadata process for {self.service_suffix} exiting", flush=True)
    self.ok = False
    sys.exit(0)


  def run(self):
    """Run the mpris metadata process."""
    while self.ok:

      metadata: Dict[str, Any] = {}
      if not self.mpris:
        try:
          print(f'connecting to {self.service_suffix}')
          mpris = SessionMessageBus().get_proxy(
            service_name = f"org.mpris.MediaPlayer2.{self.service_suffix}",
            object_path = "/org/mpris/MediaPlayer2",
            interface_name = "org.mpris.MediaPlayer2.Player"
          )
        except Exception as e:
          metadata['connected'] = False
          print(f"failed to connect mpris {e}", flush=True)
          if not self.ok:
            break

      #print(f"getting mrpis metadata from {self.service_suffix}")
      if mpris:
        try:
          raw_metadata = {}
          try:
            raw_metadata = mpris.Metadata
          except Exception as e:
            metadata['connected'] = False
            print(f"Dbus error getting MPRIS metadata: {e}")
            if not self.ok:
              break

          for mapping in METADATA_MAPPINGS:
            try:
              metadata[mapping[0]] = str(raw_metadata[mapping[1]]).strip("[]'")
            except KeyError as e:
              #print(f"Metadata mapping error: {e}")
              pass
            if not self.ok:
              break

          if self.ok:
            metadata['state'] = mpris.PlaybackStatus.strip("'")
            metadata['volume'] = mpris.Volume

            if metadata['state'] != self.last_sent['state']:
              metadata['state_changed_time'] = time.time()
            else:
              metadata['state_changed_time'] = self.last_sent['state_changed_time']

            metadata['connected'] = True

          if metadata != self.last_sent:
            self.last_sent = metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as metadata_file:
              json.dump(metadata, metadata_file)

        except Exception as e:
          # print(f"Error writing MPRIS metadata to file at {self.metadata_path}: {e}"
          #       +"\nThe above is normal if a user is not yet connected to the stream.", flush=True)
          try:
            disconnect_proxy(mpris)
          except Exception as e_proxy:
            print(f'Error disconnecting MPRIS proxy: {e_proxy}', flush=True)
          finally:
            mpris = None
          if not self.ok:
            break

      if self.ok:
        time.sleep(1.0/METADATA_REFRESH_RATE)

    print('metadata reader thread stopped', flush=True)
    if mpris:
      try:
        print('disconnecting from MPRIS proxy', flush=True)
        disconnect_proxy(mpris)
      except Exception as e:
        print(e, flush=True)


if len(sys.argv) != 3:
  print("Usage: mprisdaughterproc.py <service_suffix> <metadata_path>")
  sys.exit(1)

service_suffix = sys.argv[1]
metadata_path = sys.argv[2]

mpris_child_proc(service_suffix, metadata_path).run()
