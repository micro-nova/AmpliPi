#! /usr/bin/python3
# -*- coding: utf-8 -*-

""" Bluetooth command line interface for media controls and metadata

Currently only supports at most one Bluetooth stream.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time

from dataclasses import dataclass, asdict
from typing import Optional, List

from bluezero import dbus_tools, media_player

parser = argparse.ArgumentParser(prog='bluetooth', description='track bluetooth metadata and control playback')
parser.add_argument('--command', type=str, help='playback command (play, pause, next, previous)', nargs='?',
                    default=None)
parser.add_argument('--song-info', type=str, help='file to update with current song information in json format')
parser.add_argument('--device-info', type=str, help='file to store the path and mac of the selected bluetooth device')
parser.add_argument('--output-device', type=str, help='output device to connect bluealsa-aplay to')
parser.add_argument('--log', type=str, help='log file (defaults to stdout)', default=None)
parser.add_argument('--verbose', action='store_true', help='show more verbose output')
args = parser.parse_args()

@dataclass
class MediaInfo:
  """Dataclass to represent the metadata."""
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
if args.command is not None and args.device_info is not None:
  mac_addr = None
  try:
    with open(args.device_info, "rt") as f:
      mac_addr = f.readline()
  except IOError as e:
    print(f'bluetooth.py: Error reading device_info file: {e}')

  found = False
  for dbus_path in dbus_tools.get_managed_objects():
    if dbus_tools.get_device_address_from_dbus_path(dbus_path) == mac_addr:
      found = True
      break

  if mac_addr and not found:
    print(f"bluetooth.py: WARNING: Tried sending command {args.command} to device {mac_addr}, but {mac_addr} doesn't exist")

  if mac_addr and found:
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

def get_playing_devices_path_and_mac() -> List[tuple]:
  """Returns a list of tuples of every bt device that is connected and currently playing media. Tuple is (addr,
  dbus_path)."""
  playing_devices = []
  for dbus_path in dbus_tools.get_managed_objects():
    if dbus_path.endswith('player0'):
      addr = dbus_tools.get_device_address_from_dbus_path(dbus_path)
      try:
        if addr and media_player.MediaPlayer(addr).status == 'playing':
          playing_devices.append(addr)
      except Exception as e:
        print(f"bluetooth.py: WARNING: {e}")
  return playing_devices

def get_all_devices_path_and_mac() -> List[tuple]:
  """Returns a list of tuples of every bt device that is connected. Tuple is (addr, dbus_path)."""
  devices = []
  for dbus_path in dbus_tools.get_managed_objects():
    if dbus_path.endswith('player0'):
      addr = dbus_tools.get_device_address_from_dbus_path(dbus_path)
      if addr:
        devices.append(addr)
  return devices

def mac_to_device_name(mac: str) -> Optional[str]:
  try:
    devices = subprocess.run('bluetoothctl devices'.split(), timeout=0.5, check=True, capture_output=True).stdout.decode()
  except Exception:
    devices = ''
  for line in devices.splitlines():
    if line.split()[1].lower() == mac.lower():
      return ' '.join(line.split()[2:])
  return None

def update_selected_device(selected_device, selected_playing_device) -> tuple:
  """Determines which bluetooth device to select based on the previously playing and selected devices"""
  all_devices = get_all_devices_path_and_mac()
  playing_devices = get_playing_devices_path_and_mac()

  # if the selected playing device is still playing, keep using it
  if selected_playing_device in playing_devices:
    return selected_playing_device, selected_playing_device

  # selected playing devices is no longer playing. try finding another
  if len(playing_devices) > 0:
    # just grab the first available one. order shouldn't matter when selecting a new one.
    return playing_devices[0], playing_devices[0]

  # couldn't find another, return selected device if it still exists
  if selected_device in all_devices:
    return selected_device, None

  # that device no longer exists. pick a connected device
  if len(all_devices) > 0:
    return all_devices[0], None

  # there's no players, return None
  return None, None

def alter_title(title, device_name) -> str:
  """Adds device name or pairing instructions to the title."""
  if device_name:
    if len(title) > 0:
      return title + " - " + device_name
    return device_name
  else:
    if len(title) > 0:
      print('WARNING: Bluetooth media player has song title, but no device name!')
      return title + " - Unknown device"
    return "Unknown device"

def main():
  p_info = MediaInfo()
  last_mac_addr = ''
  device_name = None
  bluealsa_proc = None
  p_selected_device = None
  selected_device = None
  selected_playing_device = None

  try:
    while True:
      selected_device, selected_playing_device = update_selected_device(selected_device, selected_playing_device)

      # if the device changes from the previous state,
      if p_selected_device != selected_device and args.device_info is not None:
        p_selected_device = selected_device
        if selected_device is not None:
          device_name = mac_to_device_name(selected_device)

        # kill he bluealsa process
        if bluealsa_proc is not None:
          try:
            # kill it
            bluealsa_proc.kill()
            bluealsa_proc = None
          except Exception:
            pass

        # open a new bluealsa process with the new mac address
        if bluealsa_proc is None and args.output_device is not None and selected_device is not None:
          baplay_args = f'bluealsa-aplay -d {args.output_device} {selected_device} --single-audio'
          bluealsa_proc = subprocess.Popen(args=baplay_args.split(), preexec_fn=os.setpgrp)
        # write the new mac address to the device info file, used by streams.py bluetooth send command
        with open(args.device_info, "wt") as f:
          f.write(selected_device)
          print(f'Writing {selected_device} to {args.device_info}')

      if selected_device:
        try:
          # get the media player associated with the bluetooth mac, retrieve track details
          mp = media_player.MediaPlayer(selected_device)
          track_details = mp.track
          artist = track_details.get("Artist", "")
          album = track_details.get("Album", "")
          title = track_details.get("Title", "")
          duration = track_details.get("Duration", "")

          # alter/generate a title to include device name
          title = alter_title(title, device_name)
          info = MediaInfo(artist, title, album, duration, mp.status)
        except:
          # getting info from media player crashed somehow
          info = MediaInfo(status='stopped')

      else:  # selected_device is None
        info = MediaInfo(status='stopped', title=f"No device connected - Pair device to '{socket.gethostname()}'")
        if args.verbose:
          log('No media player connected')

      # if the info changed from last state,
      if p_info != info and args.song_info is not None:
        p_info = info
        # Update song_info file with new information
        try:
          with open(args.song_info, "wt") as f:
            f.write(info.as_json())

          if args.verbose:
            log('Updated song_info')
            log(info.as_json())

        except Exception:
          log(f'song_info file: {args.song_info}')
          log(f'Error: {sys.exc_info()[1]}')

      sys.stdout.flush()
      time.sleep(1)  # might want to reduce this - currently doesn't feel very responsive

  # TODO: should we sys.exit on these excepts?
  except KeyboardInterrupt:
    print('exit')

  except Exception:
    log(sys.exc_info())


if __name__ == "__main__":
  main()
