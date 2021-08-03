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
parser.add_argument('metaport', help='port to read metadata from (see config.toml)')
parser.add_argument('cs_loc', help='Folder to write currentSong')
args = parser.parse_args()

info = {
'state': 'stopped',
'artist': '',
'album': '',
'track': '',
'img_url': ''
}

# Write to currentSong so you clear previous metadata from i.e. shairport or old Spotify instances
with open(f'{args.cs_loc}/currentSong', 'w') as CS:
  CS.write(str(info))

metasocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
metasocket.bind(('', int(args.metaport)))
while True: # Need to check how to kill the script, look at processing load, etc. NEED TO VERIFY
  message, address = metasocket.recvfrom(1024)
  if message:
    decoded = message.decode('utf-8', 'replace')
    print(decoded)
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
          info['img_url'] = 'https://i.scdn.co/image/' + al[0]
    with open(f'{args.cs_loc}/currentSong', 'w') as CS:
      CS.write(str(info))
    message = None
