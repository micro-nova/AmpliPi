#! /usr/bin/python3
# -*- coding: utf-8 -*-

# Uses rtl_fm to access an RTL-SDR dongle, redsea to process RDS data (if any), and aplay to output to audio device

import time
import json
import argparse
import os
import sys
import traceback
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
    f = open(args.song_info, "wt")

    # TODO:
    # f.write(json.dumps({"station": str(player.get_state())}))
    f.close()
  except Exception:
    log(sys.exc_info())
    exit(1)

# Run command on bluetooth device (next, pause, etc)
if args.command != None:
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
      elif args.command == 'pause':
        mp.pause()
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

  exit(1)

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
          try:
            artist = track_details["Artist"]
          except:
            artist = ""

          try:
            title = track_details["Title"]
          except:
            title = ""

          try:
            album = track_details["Album"]
          except:
            album = ""

          try:
            duration = track_details["Duration"]
          except:
            duration = ""

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

      if last_info != json.dumps(latest_info) and args.song_info != None:
        # Update song_info file with new information
        try:
          f = open(args.song_info, "wt")
          f.write(json.dumps(latest_info))
          f.close()

          last_info = json.dumps(latest_info)

          if args.verbose:
            log('Updated song_info')
            log(json.dumps(latest_info))

        except Exception:
          log('song_info file: %s' % args.song_info)
          log('Error: %s' % sys.exc_info()[1])

      time.sleep(1)

  except KeyboardInterrupt:
    print('exit')

  except KeyboardInterrupt:
    print("Shutdown requested...exiting")
    sys.exit(0)
  except Exception:
    log(sys.exc_info())

if __name__ == "__main__":
  main()
