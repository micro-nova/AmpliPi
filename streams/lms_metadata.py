#!/usr/bin/python3
"""LMS Metadata Reader - a script for finding an LMS player with a given name and extracting the name of the song, album, and artist as well as getting the album picture"""

import os
import argparse
import re
import json
import time
from typing import Optional
import subprocess
import requests
from dataclasses import dataclass

@dataclass
class MetadataHolder:
  """Contains metadata"""
  album: str
  artist: str
  track: str
  image_url: str

  def print_meta(self):
    """Prints contents of metadata"""
    # Encased in line breaks because when it is being constantly printed, it visually mucks up the console a lot
    print(f"\nAlbum: {self.album}\nArtist: {self.artist}\nTrack: {self.track}\nImage: {self.image_url}\n")

  def save_file(self, player):
    data = {
      'album': self.album,
      'artist': self.artist,
      'track': self.track,
      'image_url': self.image_url
    }
    player_name = str(player).replace(' ', '_')

    with open(f"lms_{player_name}_metadata_temp.json", 'wt', encoding='utf-8') as f:
      json.dump(data, f, indent = 2)
    os.replace(f"lms_{player_name}_metadata_temp.json", f"lms_{player_name}_metadata.json")


class LMSMetadataReader:
  """A class for getting metadata from a Logitech Media Server."""

  # meta_ref is probably an unneccessary variable to pass as an arg since it's obscured from the user, but we can eventually make it an optional setting for the user
  def __init__(self, name: str, server: Optional[str] = None, meta_ref: Optional[int] = 2, debug: Optional[bool] = False):
    self.player_name = name
    self.server = server
    self.address = None # {ip}:{port}
    self.meta_ref_rate = meta_ref
    self.debug = debug
    self.meta = MetadataHolder(artist = 'Loading...',
                          album = 'Loading...',
                          track = 'Loading...',
                          image_url = 'static/imgs/lms.png')
    if not server:
      self.meta.album =  'If loading takes a long time,'
      self.meta.track = 'consider adding hostname to stream config'


  def flatten(self, lms_info: dict) -> dict:
    """ LMS returns data in a very verbose piecewise format to avoid name collisions,
          this makes it easier to use, by disregarding possible collisions"""
    x = 0
    flat_data = {}
    for item in lms_info:
      for info in item:
        flat_data[info] = lms_info[x][info]
      x += 1
    return flat_data

  def connect(self):
    """Discovers LMS Player and then requests metadata repetitively"""
    connected = False
    self.meta.save_file(self.player_name)

    # When not connected, search for player to connect to by the proper name
    while not connected:
      try:
        if self.server is not None:
          self.address = f"{self.server}:9000" #TODO: add port selection option (this mirrors todo from streams.py)
        else:
          # Much faster method of connecting to the metadata server using code from: https://github.com/ralph-irving/squeezelite/blob/master/tools/find_server.c
          ip_find = subprocess.run(['streams/find_lms_server'], check=True, capture_output=True, text=True)
          # Uses regex because ip_find spits out as '{Hostname}:{port} ({ip})', data is then formatted to output ip and port
          ip = re.search(r'\((.*?)\)', ip_find.stdout).group(1)
          port = re.search(r':(\d{4})', ip_find.stdout).group(1)
          self.address = f"{ip}:{port}"

        if self.debug:
          print(f"Found LMS Server: {self.address}", flush=True)

        player_json = {"id": 1,	"method": "slim.request",	"params": [self.player_name, ["players", "-", 100, "playerid"]]}
        player_info = requests.get(f'http://{self.address}/jsonrpc.js', json=player_json, timeout=200)
        player_load = json.loads(player_info.text)
        if self.debug:
          print(f"Loaded: {player_load}")
        players = player_load['result']['players_loop']

        for player in players:
          connected = player['connected']
          if connected and player['name'] == self.player_name:
            if self.debug:
              print(f'LMS Metadata connected to player: {self.player_name}')
            connected = True
          else:
            time.sleep(0.1)
      except Exception as e:
        # When first creating an LMS stream, there can be random errors that will close the while loop
        # typically when asking the player for info when there isn't a player linked to the stream yet
        if self.debug:
          print(f"Could not find server: {e}", flush=True)
        time.sleep(self.meta_ref_rate)

    while connected:
      try:
        track_json = {"id": 1, "method": "slim.request", "params": [ self.player_name, ["status", "-",100] ]}
        track_info = requests.post(f'http://{self.address}/jsonrpc.js', json=track_json, timeout=1000)
        track_load = json.loads(track_info.text)

        track_id = track_load["result"]["playlist_loop"][0]["id"]
        song_json = {"id":2,"method":"slim.request","params":[ self.player_name, ["songinfo","-",100,f"track_id:{track_id}"]]}
        song_info = requests.post(f'http://{self.address}/jsonrpc.js', json=song_json, timeout=1000)
        song_load = json.loads(song_info.text)

        song_data = self.flatten(song_load['result']['songinfo_loop'])
        track_data = self.flatten(track_load['result']['playlist_loop'])


        if song_data.get('artist'):
          self.meta.artist = song_data.get('artist') or "Loading..."
          self.meta.album = song_data.get('album') or "Loading..."
          self.meta.track = song_data.get('title') or "Loading..."
        else:
          self.meta.artist = song_data.get('title') or "Loading..."
          self.meta.album = song_data.get('remote_title') or "Loading..."
          self.meta.track = track_data.get('title') or "Loading..."


        if song_data.get('artwork_url'):
          self.meta.image_url = song_data.get('artwork_url')
        elif song_data.get('coverid'):
          self.meta.image_url = f"http://{self.address}/music/{song_data['coverid']}/cover.jpg?id={song_data['coverid']}"
        else:
          self.meta.image_url = 'static/imgs/lms.png'

        try:
          self.meta.save_file(self.player_name)
        except:
          pass

        if self.debug:
          self.meta.print_meta()
          filename_prefix = str(self.player_name).replace(' ', '_')
          with open(f"{filename_prefix}_track_raw.json", "w", encoding="UTF-8") as f:
            json.dump(track_load, f, indent = 2)
          with open(f"{filename_prefix}_song_raw.json", "w", encoding="UTF-8") as f:
            json.dump(song_load, f, indent = 2)
      except Exception as e:
        print(f"Error: {e}, trying again in {self.meta_ref_rate} seconds...")

      time.sleep(self.meta_ref_rate)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="LMS Metadata Reader - a script for finding an LMS player with a given name and extracting the name of the song, album, and artist as well as getting the album picture")
  parser.add_argument('--name', type=str, required=True, help='The name of the LMS Player')
  parser.add_argument('--server', type=str, help='The hostname of the server running the LMS server', metavar="HOSTNAME")
  parser.add_argument('--ref', type=int, default=2, help='The frequency of metadata refresh cycles')
  parser.add_argument('--debug', action='store_true', help='''d''ebug mode, activates various console logs so that you can debug in the command line,
                      also creates json dumps in the main directory: {player name}_track_raw.json and {player name}_song_raw.json''')
  args = parser.parse_args()

  LMSMetadataReader(args.name, args.server, args.ref, args.debug).connect()
