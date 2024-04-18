#!/usr/bin/python3
"""
LMS Metadata Reader - a script for finding an LMS player
with a given name and extracting the name of the song, album,
and artist as well as getting the album picture
"""

import os
import argparse
import platform
import re
import json
import logging
import sys
import time
from typing import Optional
import socket
import subprocess
from dataclasses import dataclass
import requests
from typing import Tuple

@dataclass
class MetadataHolder:
  """Contains metadata"""
  album: str
  artist: str
  track: str
  image_url: str
  logger: logging.Logger

  def log_meta(self):
    """logs contents of metadata to the console"""
    # Encased in line breaks because when it is being constantly printed, it visually mucks up the console a lot
    self.logger.debug(f"\nAlbum: {self.album}\nArtist: {self.artist}\nTrack: {self.track}\nImage: {self.image_url}\n")

  def save_file(self, folder):
    """Saves metadata to a file at the given folder"""
    data = {
      'album': self.album,
      'artist': self.artist,
      'track': self.track,
      'image_url': self.image_url
    }

    with open(f"{folder}/lms_metadata_temp.json", 'wt', encoding='utf-8') as f:
      json.dump(data, f, indent = 2)
    os.replace(f"{folder}/lms_metadata_temp.json", f"{folder}/lms_metadata.json")


class LMSMetadataReader:
  """A class for getting metadata from a Logitech Media Server."""

  # meta_ref is probably an unneccessary variable to pass as an arg since it's obscured from the user, but we can eventually make it an optional setting for the user
  def __init__(self, name: str, vsrc: int, server: Optional[str] = None, port: Optional[int] = 9000, meta_ref: Optional[int] = 2):
    self.player_name = name
    self.folder = f'config/srcs/v{vsrc}'
    self.server = server
    self.port = port
    self.meta_ref_rate = meta_ref
    self.debug = os.environ.get('DEBUG', False)

    self.logger = logging.getLogger(__name__)
    if self.debug:
      self.logger.setLevel(logging.DEBUG)
    else:
      self.logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    self.logger.addHandler(sh)

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    self.logger.setLevel(logging.DEBUG)
    self.meta = MetadataHolder(artist = 'Loading...',
                          album = 'Loading...',
                          track = 'Loading...',
                          image_url = 'static/imgs/lms.png',
                          logger = self.logger,)
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

  def verify_server(self, ip):
    """Verifies if a given IP has the player we're looking for"""
    try:
      player_json = {"id": 1,	"method": "slim.request",	"params": [self.player_name, ["players", "-", 100, "playerid"]]}
      player_info = requests.get(f'http://{ip}:{self.port}/jsonrpc.js', json=player_json, timeout=5)
      player_load = json.loads(player_info.text)

      self.logger.info(f"Loaded: {player_load}")

      players = player_load['result']['players_loop']

      for player in players:
        connected = player['connected']
        if connected and player['name'] == self.player_name:
          self.logger.info(f'\nLMS Metadata connected to player: {self.player_name} at {ip}:{self.port}\n')
          self.server = ip
          return True

      time.sleep(0.1)
      return False
    except Exception:
      time.sleep(0.1)
      return False


  def resolve_host(self) -> Tuple[bool, str]:
    """Checks if self.server is a hostname or an IP; if hostname try to resolve to IP"""
    try:
      if self.server is None:
        self.logger.info("No hostname provided, bailing on hostname resolution")
        raise Exception("No hostname provided, bailing on hostname resolution")
      ip_regex = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
      resolved_server: str = str(self.server)
      ret: bool = False

      if re.match(ip_regex, self.server): #Does the given string fit the format of an IP?
        ret = True #If the hostname is already an IP, return True
      else:
        host = socket.gethostbyname(self.server)
        if re.match(ip_regex, host):
          self.logger.info(f"hostname: {self.server}")
          self.logger.info(f"ip: {host}")
          resolved_server = host
          ret = True #If the resolved hostname is an IP, return True
        else:
          ret = False #If the hostname is resolvable but somehow still not an IP, return False

      return (ret, resolved_server)

    except Exception:
      self.logger.info("Could not resolve hostname, trying to find LMS server manually")
      self.logger.info("Set local network DNS settings or set 'server' in config to be an IP to avoid this issue in the future")
      return (False, "") #If there is an error, or the hostname is unresolvable, return false

  def connect(self):
    """Discovers LMS Player and then requests metadata repetitively"""
    connected = False
    self.meta.save_file(self.folder)

    # When not connected, search for player to connect to by the proper name
    while not connected:
      try:
        resolution_function_success, resolved_host = self.resolve_host() # Attempt to resolve hostname, if unresolvable then find host with find_lms_server script
        if resolution_function_success:
          connected = self.verify_server(resolved_host)

        if not resolution_function_success or not connected:
          # Checks for not connected as there is a chance that a provided hostname is resolvable but does not contain a server
          machine = platform.machine()
          self.logger.debug(f"platform.machine() output: {machine}")

          find_lms_server = None
          if machine == "x86_64":
            find_lms_server = "bin/x64/find_lms_server"
          elif machine == "armv7l":
            find_lms_server = "bin/arm/find_lms_server"
          else:
            self.meta.artist = "Unsupported CPU architecture for LMS MetaData"
            self.meta.album = "Please set 'server' in LMS config to an IP"
            self.meta.track = "or contact AmpliPi Support:support@micro-nova.com"
            self.logger.warning("LMS metadata reader has detected an unsupported chipset")
            self.logger.warning("Aborting LMS metadata search")
            break

          # Much faster method of connecting to the metadata server using code from: https://github.com/ralph-irving/squeezelite/blob/master/tools/find_server.c
          # faster relative to the original method, using NMAP to go door to door (ip to ip) and ask if self.name is home
          ip_find = subprocess.run([find_lms_server], check=True, capture_output=True, text=True)
          ip_output = ip_find.stdout.splitlines()

          for count, line in enumerate(ip_output):
            self.logger.debug(f"find_lms_server output number {count + 1}:")
            self.logger.debug(line)
            # Uses regex because ip_find spits out as '{Hostname}:{port} ({ip})'
            ip = re.search(r'\((.*?)\)', line).group(1)
            connected = self.verify_server(ip)

      except KeyError:
        self.logger.info("Awaiting Metadata...")
        time.sleep(self.meta_ref_rate)
      except requests.exceptions.ConnectionError:
        self.logger.warning("Connection refused by host")
        time.sleep(self.meta_ref_rate)
      except subprocess.CalledProcessError as e:
        self.logger.warning(f"Something went wrong while finding an LMS server: {e}")
        time.sleep(self.meta_ref_rate)
      except Exception as e:
        # When first creating an LMS stream, there can be random errors that will close the while loop
        # typically when asking the player for info when there isn't a player linked to the stream yet
        self.logger.warning(f"Could not find server: {e}")
        time.sleep(self.meta_ref_rate)

    while connected:
      try:
        track_json = {"id": 1, "method": "slim.request", "params": [ self.player_name, ["status", "-",100] ]}
        track_info = requests.post(f'http://{self.server}:{self.port}/jsonrpc.js', json=track_json, timeout=1000)
        track_load = json.loads(track_info.text)

        track_id = track_load["result"]["playlist_loop"][0]["id"]
        song_json = {"id":2,"method":"slim.request","params":[ self.player_name, ["songinfo","-",100,f"track_id:{track_id}"]]}
        song_info = requests.post(f'http://{self.server}:{self.port}/jsonrpc.js', json=song_json, timeout=1000)
        song_load = json.loads(song_info.text)

        song_data = self.flatten(song_load['result']['songinfo_loop'])
        track_data = self.flatten(track_load['result']['playlist_loop'])

        if song_data.get('artist'): # Some stream types (radio streams primarily) dont advertise the artist over LMS
          self.meta.artist = song_data.get('artist') or ""
          self.meta.album = song_data.get('album') or ""
          self.meta.track = song_data.get('title') or ""
        else:
          self.meta.artist = song_data.get('title') or ""
          self.meta.album = song_data.get('remote_title') or ""
          self.meta.track = track_data.get('title') or ""

        if song_data.get('artwork_url'):
          self.meta.image_url = song_data.get('artwork_url')
        elif song_data.get('coverid'):
          self.meta.image_url = f"http://{self.server}:{self.port}/music/{song_data['coverid']}/cover.jpg?id={song_data['coverid']}"
        else:
          self.meta.image_url = 'static/imgs/lms.png'

        try:
          self.meta.save_file(self.folder)
        except:
          pass

        if self.debug:
          self.meta.log_meta()
          with open(f"{self.folder}/track_raw.json", "w", encoding="UTF-8") as f:
            json.dump(track_load, f, indent = 2)
          with open(f"{self.folder}/song_raw.json", "w", encoding="UTF-8") as f:
            json.dump(song_load, f, indent = 2)
      except Exception as e:
        self.logger.info(f"Error: {e}, trying again in {self.meta_ref_rate} seconds...")

      time.sleep(self.meta_ref_rate)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="LMS Metadata Reader - a script for finding an LMS server and extracting the name of the song, album, and artist as well as getting the album picture of the currently playing song")
  parser.add_argument('--name', type=str, required=True, help='The name of the LMS Player')
  parser.add_argument('--vsrc', type=str, required=True, help='The numbered source that the player is on')
  parser.add_argument('--server', type=str, default=None, help='The hostname or IP of the computer running the LMS server', metavar="HOSTNAME")
  parser.add_argument('--port', type=int, default=9000, help='The port the LMS server uses')
  parser.add_argument('--ref', type=int, default=2, help='The frequency of metadata refresh cycles', metavar="REFRESH_RATE")
  args = parser.parse_args()

  # There's a few args here that aren't currently used by the system, but can be helpful for debugging in the field
  # some are also there so we can implement future features easier, or so the devs at home can do the same with a minimal lift
  LMSMetadataReader(args.name, args.vsrc, args.server, args.port, args.ref).connect()

