#!/usr/bin/python3
import socket
import json

info = {
'state': 'stopped',
'artist': '',
'album': '',
'track': '',
'cover_art': ''
}

metasocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
metasocket.bind(('', 5040))
while True: # Need to check how to kill the script, look at processing load, etc. NEED TO VERIFY
  message, address = metasocket.recvfrom(1024)
  if message:
    decoded = message.decode('utf-8', 'replace')
    if decoded[0:2] != 'kSp':
      data = json.loads(decoded) # May need try/catch here for the case where a dictionary isn't given
      if 'state' in data:
        info['state'] = data['state']
      elif 'metadata' in data:
        info['artist'] = data['metadata']['artist_name']
        info['album'] = data['metadata']['album_name']
        info['track'] = data['metadata']['track_name'] # Try out get instead - this will freak out if no track name present
        info['cover_art'] = data['metadata'].get('albumartId', None) # Figure out how to make the URL out of this. URL should go in$
    with open('./currentSong', 'a') as CS:
      CS.write(decoded)
    message = None
