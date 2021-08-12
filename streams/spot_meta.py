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
'img_url': ''
}

# Write to currentSong so you clear previous metadata from i.e. shairport or old Spotify instances
with open(f'{args.cs_loc}/currentSong', 'w') as csi:
  csi.write(str(info))

metasocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
metasocket.bind(('', int(args.metaport)))
prev_state = ''
while True: # Need to check how to kill the script, look at processing load, etc. NEED TO VERIFY
  message, address = metasocket.recvfrom(1024)
  if message:
    decoded = message.decode('utf-8', 'replace')
    parsed = re.split('\n|\r', decoded)
    if 'kSp' not in decoded:
      data = {}
      for item in parsed:
        try:
          data = json.loads(item)
        except:
          pass
        if 'state' in data:
          simplestate = str(data['state'])
          ss = simplestate[11:].strip("'}")
          if 'play' in ss:
            info['state'] = 'playing' # JavaScript looks for 'playing', not 'play'
          else:
            info['state'] = ss
        elif 'metadata' in data:
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
      print(decoded)
    elif full_info != prev_state:
      prev_state = full_info
      print(prev_state)
    with open(f'{args.cs_loc}/currentSong', 'w') as csi:
      csi.write(str(info))
    message = None
