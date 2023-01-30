#! /usr/bin/python3
# -*- coding: utf-8 -*-

""" Bluetooth command line interface for media controls and metadata

Currently only supports at most one Bluetooth stream.
"""

import argparse
import json
import subprocess
import sys
import time

from dataclasses import dataclass, asdict
from typing import Optional

from bluezero import dbus_tools, media_player

parser = argparse.ArgumentParser(prog='bluetooth', description='track bluetooth metadata and control playback')
parser.add_argument('--command', type=str, help='playback command (play, pause, next, previous)', nargs='?',
                    default=None)
parser.add_argument('--song-info', type=str, help='file to update with current song information in json format')
parser.add_argument('--log', type=str, help='log file (defaults to stdout)', default=None)
parser.add_argument('--verbose', action='store_true', help='show more verbose output')
args = parser.parse_args()

@dataclass
class MediaInfo:
  artist: str = ''
  title: str = ''
  album: str = ''
  duration: str = ''
  status: str = ''

  def as_json(self):
    return json.dumps(asdict(self))

def log(info):
  if args.log:
    try:
      with open(args.log, 'a') as f:
        print(info, file=f)
    except:
      print(f'Error writing to logfile: {args.log}')
      print(info)
  else:
    print(info)

# Run command on bluetooth device (next, pause, etc)
if args.command is not None:
  # Find the mac address of the first media player connected over Bluetooth
  mac_addr = None
  for dbus_path in dbus_tools.get_managed_objects():
    if dbus_path.endswith('player0'):
      mac_addr = dbus_tools.get_device_address_from_dbus_path(dbus_path)

  if mac_addr:
    try:
      mp = media_player.MediaPlayer(mac_addr)
      if args.command == 'play':
        mp.play()
        print('bluetooth: play')
      elif args.command == 'pause':
        mp.pause()
        print('bluetooth: pause')
      elif args.command == 'next':
        mp.next()
      elif args.command == 'prev':
        mp.previous()
      elif args.command == 'stop':
        mp.stop()
      elif args.command == 'position':
        log(f'position: {mp.position}')

      if args.verbose:
        log(f'Executed command: {args.command}')

    except:
      if args.verbose:
        log('Error: No media player connected')

  sys.exit(1)

def mac_to_device_name(mac: str) -> Optional[str]:
  devices = subprocess.run('bluetoothctl devices'.split(), timeout=0.5, check=True, capture_output=True).stdout.decode()
  for line in devices.splitlines():
    if line.split()[1].lower() == mac.lower():
      return ' '.join(line.split()[2:])
  return None

def main():
  last_info = MediaInfo()
  last_mac_addr = ''
  device_name = None

  try:
    while True:
      # Find the mac address of the first media player connected over Bluetooth
      mac_addr = None
      for dbus_path in dbus_tools.get_managed_objects():
        if dbus_path.endswith('player0'):
          mac_addr = dbus_tools.get_device_address_from_dbus_path(dbus_path)

      if mac_addr:
        try:
          mp = media_player.MediaPlayer(mac_addr)
          track_details = mp.track
          artist = track_details.get("Artist", "")
          album = track_details.get("Album", "")
          title = track_details.get("Title", "Unknown")
          duration = track_details.get("Duration", "")

          if last_mac_addr != mac_addr:
            last_mac_addr = mac_addr
            device_name = mac_to_device_name(mac_addr)

          if device_name:
            title += " - " + device_name
          else:
            if len(title) > 0:
              print('WARNING: Bluetooth media player has song title, but no device!')
              title += "- Unknown device"
            else:
              title = "Unknown device"

          latest_info = MediaInfo(artist, title, album, duration, mp.status)
        except:
          latest_info = MediaInfo(status='stopped')

      else:
        latest_info = MediaInfo(status='stopped', title="No device connected - Pair device to 'amplipi'")

        if args.verbose:
          log('Error: No media player connected')

      if last_info != latest_info and args.song_info is not None:
        # Update song_info file with new information
        try:
          with open(args.song_info, "wt") as f:
            f.write(latest_info.as_json())

          last_info = latest_info

          if args.verbose:
            log('Updated song_info')
            log(latest_info.as_json())

        except Exception:
          log(f'song_info file: {args.song_info}')
          log(f'Error: {sys.exc_info()[1]}')

      time.sleep(1)

  except KeyboardInterrupt:
    print('exit')

  except Exception:
    log(sys.exc_info())


if __name__ == "__main__":
  main()
