#!/usr/bin/python3
""" Spotify Metadata Translator
    This file reads/translates the metadata coming from vollibrespot and
    writes the useful information to currentSong
"""
import socket
import json
import re
import argparse

parser = argparse.ArgumentParser(description="spotify metadata interpreter")
parser.add_argument('metaport', help='port to read from (see metadata-port in config.toml)')
parser.add_argument('cs_loc', help='Folder to write/create the currentSong file')
parser.add_argument('--verbose', '-v', action='count', default=None, help='Prints full metadata')
args = parser.parse_args()

info = {
'state': 'stopped',
'artist': '',
'album': '',
'track': '',
'img_url': None
}

# Write to currentSong so you clear previous metadata from i.e. shairport or old Spotify instances
with open(f'{args.cs_loc}/currentSong', 'w') as csi:
  csi.write(str(info))

metasocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
metasocket.bind(('', int(args.metaport)))
prev_state = ''
with open(f'{args.cs_loc}/spot_meta_log.txt', 'w') as log:
  while True: # Need to check how to kill the script, look at processing load, etc. NEED TO VERIFY
    message, address = metasocket.recvfrom(1024)
    if message:
      decoded = message.decode('utf-8', 'replace')
      parsed = re.split('\n|\r', decoded)
      data = {}
      for item in parsed:
        if len(item) == 0:
          continue
        if 'vollibrespot v' in item:
          continue
        if 'kSp' in item:
          # ksp data seems to be more accurate than info['state']['status'] data
          if item == 'kSpSinkInactive':
            info['state'] = 'paused'
          elif item == 'kSpSinkActive':
            info['state'] = 'playing'
          continue
        try:
          data = json.loads(item)
        except Exception as exc:
          if args.verbose:
            log.write(f'Error parsing json: {exc}\n')
            log.write(f'  from: "{item}"\n')
        if 'metadata' in data:
          # if we get song metadata assume it is playing since spotify only gives a state update on state change
          info['artist'] = data['metadata'].get('artist_name') # .get defaults to 'None'
          info['album'] = data['metadata'].get('album_name') # if nothing found
          info['track'] = data['metadata'].get('track_name')
          al = data['metadata'].get('albumartId')
          if al[0] is not None:
            info['img_url'] = 'https://i.scdn.co/image/' + al[0]
          else:
            info['img_url'] = None
    full_info = f"{info['state']}: {info['track']}"
    if args.verbose:
      log.write(decoded)
      log.write('\n')
      log.flush()
    with open(f'{args.cs_loc}/currentSong', 'w') as csi:
      csi.write(str(info))
