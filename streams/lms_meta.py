#!/usr/bin/python3
# Gather LMS Metadata from LMS Server
import json
from time import sleep
import argparse
from requests import post

parser = argparse.ArgumentParser(description='LMS Metadata reader')
parser.add_argument('-s', '--server', default='0.0.0.0:9000', help='LMS Server IP, port 9000 is assumed unless specified with :PORT')
parser.add_argument('mac', help='MAC Address of the client to get metadata for like: 17:cd:c4:ee:a4:94')
args = parser.parse_args()

# TODO: make this a class?

server = args.server
if 'http://' not in server: # TODO: https
  server = f'http://{args.server}'
if len(server.split(':')) < 3:
  server += ':9000'
rpc_server = server + '/jsonrpc.js'
print(rpc_server)

resp = post(timeout=1.0, url=rpc_server, json={"id": 1, "method": "slim.request", 'params': ["FF:FF:FF:FF", ["players","0", 4]]})
print(resp.json())
status_req = {"id":1, "method": "slim.request", "params": [args.mac, ['status',"-",1]]}
print(json.dumps(status_req))
resp = post(timeout=1.0, url=rpc_server, json=status_req)
status = resp.json()['result']
print(status)
metadata = status.get('remoteMeta')
if not metadata:
  metadata = status.get('playlist_loop')
  if len(metadata) > 0:
    metadata = metadata[0]
  else:
    metadata = None

mode = status.get('mode')

# LMS assumes play and pause are always available
supported_cmds = ['play', 'pause']
buttons = metadata.get('buttons')
if buttons:
  if buttons.get('fwd') == 1:
    supported_cmds.append('next')
  if buttons.get('rew') == 1:
    supported_cmds.append('prev')
# TODO: document the play/pause/next/prev command

if not metadata:
  print(f'status: {mode}, supported_cmds: {supported_cmds},  No metadata available')
  exit(0)

track_id = metadata.get('id')
title = metadata.get('title')

resp = post(timeout=1.0, url=rpc_server, json={"id":1, "method": "slim.request", "params": [args.mac, ['songinfo',"-",100,f'track_id:{track_id}']]})
try:
  song_info = resp.json()['result']['songinfo_loop']
  print(song_info)
except:
  song_info = None

info = {}
# flatten song info into a single dict
for d in song_info:
  info.update(d)
print(info)


# TODO: handle multiple url paths since a local url is reported differently
album_art_url = info.get("artwork_url")
cover_id = info.get("coverid")
print(f'aau {album_art_url}, ci {cover_id}')
if album_art_url:
  # local urls aren't full?
  if not album_art_url.startswith('http'):
    album_art_url = server + album_art_url
elif cover_id:
  # generate a local url
  album_art_url = f'{server}/music/{cover_id}/cover.jpg'

# TODO: to avoid CORS we will need to cache local images somewhere accessible in the web interface

print(f''' song-info:
  title: {info.get("title")}
  artist: {info.get("artist")}
  album: {info.get("album")}
  url: {album_art_url}
  status: {mode}
  supported_cmds: {supported_cmds}''')


# TODO: do this all in a loop and write out to a file?
