#! /usr/bin/python3
# -*- coding: utf-8 -*-

""" Bluetooth currently only supports at most one Bluetooth stream. Handles media controls and audio. """

import time
import json
import argparse
import sys
from bluezero import dbus_tools
from bluezero import media_player

parser = argparse.ArgumentParser(prog='bluetooth', description='track bluetooth metadata and control playback')
parser.add_argument('--command', type=str, help='playback command (play, pause, next, previous)', nargs='?',
                    default=None)
parser.add_argument('--song-info', type=str, help='file to update with current song information in json format')
parser.add_argument('--log', type=str, help='log file (defaults to stdout)', default=None)
parser.add_argument('--verbose', action='store_true', help='show more verbose output')
args = parser.parse_args()

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

if args.song_info:
  try:
    pass
    # with open(args.song_info, "wt") as f:
    #   # TODO:
    #   f.write(json.dumps({"station": str(player.get_state())}))
  except Exception:
    log(sys.exc_info())
    sys.exit(1)

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

def main():
  last_info = ""
  latest_info = {
    'artist': '',
    'title': '',
    'album': '',
    'duration': '',
    'status': ''
  }

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
          status = mp.status
          artist = track_details.get("Artist", "")
          title = track_details.get("Title", "")
          album = track_details.get("Album", "")
          duration = track_details.get("Duration", "")

          latest_info = {
            'artist': artist,
            'title': title,
            'album': album,
            'duration': duration,
            'status': status
          }
        except:
          latest_info = {
            'artist': "",
            'title': "",
            'album': "",
            'duration': "",
            'status': "stopped"
          }

      else:
        latest_info = {
          'artist': '',
          'title': '',
          'album': '',
          'duration': '',
          'status': 'stopped'
        }

        if args.verbose:
          log('Error: No media player connected')

      if last_info != json.dumps(latest_info) and args.song_info is not None:
        # Update song_info file with new information
        try:
          with open(args.song_info, "wt") as f:
            f.write(json.dumps(latest_info))

          last_info = json.dumps(latest_info)

          if args.verbose:
            log('Updated song_info')
            log(json.dumps(latest_info))

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
