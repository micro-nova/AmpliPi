#!/usr/bin/python3
"""LMS Metadata Reader - a script for finding an LMS player with a given name and extracting the name of the song, album, and artist as well as getting the album picture"""

import logging
import os
import argparse
import platform
import re
import json
import time
from typing import Optional
import socket
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
    logging.info(f"\nAlbum: {self.album}\nArtist: {self.artist}\nTrack: {self.track}\nImage: {self.image_url}\n")

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
  def __init__(self, name: str, server: Optional[str] = None, ip: Optional[str] = None, port: Optional[int] = 9000, meta_ref: Optional[int] = 2, debug: Optional[bool] = False):
    self.player_name = name
    self.server = server
    self.port = port
    self.ip = ip # Generally populated later
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
    attempt_resolution = True # Attempt by name only once, as a common error is a nonresolvable DNS hostname
    abort = False # Used to stop looping without initiating the secondary loop
    while not connected and not abort:
      try:
        if self.server is not None and self.ip is None and attempt_resolution is True:
          host = socket.gethostbyname(self.server)
          logging.debug(f"hostname: {self.server}")
          logging.debug(f"ip: {host}")
          self.ip = host
      except Exception:
        logging.warning("Could not resolve hostname, trying to find LMS server manually")
        logging.warning("Set local network DNS settings to avoid this issue in the future")
        attempt_resolution = False

      try:
        if self.ip is None:
          machine = platform.machine()
          logging.debug(f"platform.machine() output: {machine}")

          find_lms_server = None
          if machine == "x86_64":
            find_lms_server = "bin/x64/find_lms_server"
          elif machine == "armv7l":
            find_lms_server = "bin/arm/find_lms_server"
          else:
            self.meta.artist = "Unsupported CPU architecture for LMS MetaData"
            self.meta.album = "Please contact AmpliPi Support:"
            self.meta.track = "support@micro-nova.com"
            logging.error("LMS metadata reader has detected an unsupported chipset")
            abort = True

          # Much faster method of connecting to the metadata server using code from: https://github.com/ralph-irving/squeezelite/blob/master/tools/find_server.c
          ip_find = subprocess.run([find_lms_server], check=True, capture_output=True, text=True)
          # Uses regex because ip_find spits out as '{Hostname}:{port} ({ip})'
          self.ip = re.search(r'\((.*?)\)', ip_find.stdout).group(1)

        if self.debug:
          logging.debug(f"Found LMS Server: {self.ip}:{self.port}")

        player_json = {"id": 1,	"method": "slim.request",	"params": [self.player_name, ["players", "-", 100, "playerid"]]}
        player_info = requests.get(f'http://{self.ip}:{self.port}/jsonrpc.js', json=player_json, timeout=5)
        player_load = json.loads(player_info.text)
        if self.debug:
          logging.debug(f"Loaded: {player_load}")
        players = player_load['result']['players_loop']

        for player in players:
          connected = player['connected']
          if connected and player['name'] == self.player_name:
            if self.debug:
              logging.debug(f'LMS Metadata connected to player: {self.player_name}')
            connected = True
          else:
            time.sleep(0.1)
      except requests.exceptions.ConnectionError:
        logging.exception("Connection refused by host")
        time.sleep(self.meta_ref_rate)
      except Exception as e:
        # When first creating an LMS stream, there can be random errors that will close the while loop
        # typically when asking the player for info when there isn't a player linked to the stream yet
        logging.exception(f"Could not find server: {e}")
        time.sleep(self.meta_ref_rate)

    while connected:
      try:
        track_json = {"id": 1, "method": "slim.request", "params": [ self.player_name, ["status", "-",100] ]}
        track_info = requests.post(f'http://{self.ip}:{self.port}/jsonrpc.js', json=track_json, timeout=1000)
        track_load = json.loads(track_info.text)

        track_id = track_load["result"]["playlist_loop"][0]["id"]
        song_json = {"id":2,"method":"slim.request","params":[ self.player_name, ["songinfo","-",100,f"track_id:{track_id}"]]}
        song_info = requests.post(f'http://{self.ip}:{self.port}/jsonrpc.js', json=song_json, timeout=1000)
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
          self.meta.image_url = f"http://{self.ip}:{self.port}/music/{song_data['coverid']}/cover.jpg?id={song_data['coverid']}"
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
        logging.exception(f"Error: {e}, trying again in {self.meta_ref_rate} seconds...")

      time.sleep(self.meta_ref_rate)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="LMS Metadata Reader - a script for finding an LMS server and extracting the name of the song, album, and artist as well as getting the album picture of the currently playing song")
  parser.add_argument('--name', type=str, required=True, help='The name of the LMS Player')
  parser.add_argument('--server', type=str, default=None, help='The hostname of the computer running the LMS server', metavar="HOSTNAME")
  parser.add_argument('--ip', type=str, default=None, help='The IPv4 address of the computer running the LMS server')
  parser.add_argument('--port', type=int, default=9000, help='The port the LMS server uses')
  parser.add_argument('--ref', type=int, default=2, help='The frequency of metadata refresh cycles')
  parser.add_argument('--debug', action='store_true', default=False, help='''debug mode, activates various console logs so that you can debug in the command line,
                      also creates json dumps in the main directory: {player name}_track_raw.json and {player name}_song_raw.json''')
  args = parser.parse_args()

  # There's a few args here that aren't currently used by the system, but can be helpful for debugging in the field
  # some are also there so we can implement future features easier, or so the devs at home can do the same with a minimal lift
  LMSMetadataReader(args.name, args.server, args.ip, args.port, args.ref, args.debug).connect()
