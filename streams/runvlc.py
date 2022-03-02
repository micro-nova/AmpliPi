#! /usr/bin/python3
# -*- coding: utf-8 -*-

# Use libvlc to play internetradio stations to a specific alsa output

# Copyright (C) 2009-2017 the VideoLAN team
# $Id: $
#
# Authors: Olivier Aubert <contact at olivieraubert.net>
#          Jean Brouwers <MrJean1 at gmail.com>
#          Geoff Salmon <geoff.salmon at gmail.com>
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301 USA

import os
import sys
import time
import json
import vlc
import argparse

parser = argparse.ArgumentParser(prog='runvlc', description='play an internet radio station using vlc')
parser.add_argument('url', type=str, help='internet radio station url')
parser.add_argument('output', type=str, help='alsa output', nargs='?', default=None)
parser.add_argument('--song-info', type=str, help='file to update with current song information in json format')
parser.add_argument('--log', type=str, help='log file (defaults to stdout)', default=None)
parser.add_argument('--test', action='store_true', help='verify the url is valid and return')
parser.add_argument('--verbose', action='store_true', help='show more verbose output')
args = parser.parse_args()

config = "--aout=alsa "
if args.test:
  # when we are testing the url, don't use real output, we don't want extra playback
  config += " --alsa-audio-device null"
elif args.output:
  alsa_device = args.output
  config += " --alsa-audio-device {}".format(alsa_device)

if args.log:
  try:
    os.remove(args.log)
  except Exception:
    pass

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

instance = vlc.Instance(config.split())
try:
  media = instance.media_new(args.url)
except (AttributeError, NameError) as e:
  log('%s: %s (%s LibVLC %s)' % (e.__class__.__name__, e, sys.argv[0], vlc.libvlc_get_version()))
  sys.exit(1)
try:
  player = instance.media_player_new()
  player.set_media(media)
  player.play()
except Exception:
  log(sys.exc_info())
  exit(1)

if args.song_info:
  try:
    f = open(args.song_info, "wt")
    f.write(json.dumps({"state": str(player.get_state())}))
    f.close()
  except Exception:
    log(sys.exc_info())
    exit(1)

# Wait for stream to start playing
time.sleep(2)

# Keep track of the current state so we only update on change
cur_url = ''
cur_info = {
  'track':'',
  'artist':'',
  'station': '',
  'state': 'stopped',
}

# Monitor track meta data and update currently_playing file if the track changed
while True:
  try:
    if str(player.get_state()) == 'State.Playing':

      latest_info = {
        'track':'',
        'artist':'',
        'station': '',
        'state': 'playing',
      }

      if args.verbose:
        print(f"""vlc metadata:
          Title: {media.get_meta(vlc.Meta.Title)}
          NowPlaying: {media.get_meta(vlc.Meta.NowPlaying)}
          Artist: {media.get_meta(vlc.Meta.Artist)}
          Album: {media.get_meta(vlc.Meta.Album)}
          Description: {media.get_meta(vlc.Meta.Description)}
        """)

      # Pass along the station name if it exists in Title metadata
      latest_info['station'] = media.get_meta(vlc.Meta.Title)

      # 'nowplaying' metadata is used by some internet radio stations instead of separate artist and title
      nowplaying = media.get_meta(vlc.Meta.NowPlaying)

      if nowplaying:
        # 'nowplaying' metadata is "almost" always: title - artist
        if '-' in nowplaying:
          parts = nowplaying.split(' - ', 1)
          latest_info['artist'] = parts[0]
          latest_info['track'] = parts[1]
        else:
          latest_info['artist'] = None
          latest_info['track'] = nowplaying
      else:
        latest_info['artist'] = media.get_meta(vlc.Meta.Artist)
        latest_info['track'] = media.get_meta(vlc.Meta.Title)

      # Update currently_playing file if the track has changed
      if cur_info != latest_info or cur_url != vlc.bytes_to_str(media.get_mrl()):
        cur_info = latest_info
        cur_url = vlc.bytes_to_str(media.get_mrl())
        log(f"Current track: {latest_info['track']} - {latest_info['artist']}")

        if args.test:
          log('success')
          sys.exit(0)

        if args.song_info:
          try:
            f = open(args.song_info, "wt")
            f.write(json.dumps(cur_info))
            f.close()
          except Exception:
            log('Error: %s' % sys.exc_info()[1])
    else:
      if args.test:
        log('fail')
        sys.exit(1)
      if latest_info['state'] == "playing":
        latest_info['state'] = 'stopped'
        log('State: %s' % player.get_state())

  except Exception:
    log('Error: %s' % sys.exc_info()[1])
    if args.test:
      log('fail')
      sys.exit(1)
    else:
      # try to recover by restarting vlc
      time.sleep(1)
      try:
        del player
        player = instance.media_player_new()
        player.set_media(media)
        player.play()
      except Exception:
        log(sys.exc_info())
        exit(1)

  time.sleep(1) # throttle metadata
