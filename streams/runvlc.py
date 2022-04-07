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

""" Play an internet radio stream using vlc """

import os
import sys
import time
import json
import vlc
import argparse
from typing import List, Optional, Any, IO

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

log_file : Optional[IO[Any]] = None
if args.log:
  try:
    os.remove(args.log)
  except Exception:
    pass
  log_file = open(args.log, 'a', encoding='utf-8')

def log(info):
  if log_file:
    try:
      print(info, file=log_file)
      log_file.flush()
    except:
      print(f'Error writing to logfile: {args.log}')
      print(info)
  else:
    print(info)

def update_info(info) -> bool:
  try:
    with open(args.song_info, "wt", encoding='utf-8') as info_file:
      info_file.write(json.dumps(info))
    return True
  except Exception:
    log('Error: %s' % sys.exc_info()[1])
    return False

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
  sys.exit(1)

# Keep track of the current state so we only update on change
cur_url = ''
cur_info = {
  'track':'',
  'artist':'',
  'station': '',
  'state': 'stopped',
}
if args.song_info:
  if not update_info(cur_info):
    sys.exit(1)

restarts: List[float] = []
def restart_vlc():
  global player, media, instance# TODO: This is ugly
  MAX_DELAY_S = 10
  log('Waiting to restart vlc')
  # prune old restarts from over an hour ago
  LAST_HOUR = time.time() - 3600
  while len(restarts) > 0 and restarts[0] < LAST_HOUR:
    restarts.pop(0)
  # wait for a bit to restart if we've had too many restarts recently
  if len(restarts) < 2:
    time.sleep(5)
  else:
    log('VLC restart is delayed, too many recent restarts')
    time.sleep(60 * 10)
  # actually restart vlc
  log('Attempting to restart VLC')
  instance = vlc.Instance(config.split())
  media = instance.media_new(args.url)
  player = instance.media_player_new()
  player.set_media(media)
  player.play()
  restarts.append(time.time())
  # wait for vlc to start playing
  delay = 0
  while str(player.get_state()) != 'State.Playing' and delay <= MAX_DELAY_S:
    time.sleep(1)
    delay += 1
  if delay >= MAX_DELAY_S:
    raise Exception('Waited too long for VLC to start playing')

# Wait for stream to start playing
time.sleep(2)

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
          update_info(cur_info)
    else:
      if args.test:
        log('fail')
        sys.exit(1)
      if latest_info['state'] == "playing":
        curr_info = {
          'track':'',
          'artist':'',
          'station': '',
          'state': 'stopped'
        }
        if args.song_info:
          update_info(cur_info)
        log('State: %s' % player.get_state())
      restart_vlc()

  except Exception:
    log('Error: %s' % sys.exc_info()[1])
    if args.test:
      log('fail')
      sys.exit(1)
    else:
      try:
        curr_info = {
          'track':'',
          'artist':'',
          'station': '',
          'state': 'stopped'
        }
        if args.song_info:
          update_info(cur_info)
        restart_vlc()
      except Exception:
        log(sys.exc_info())
        sys.exit(1)

  time.sleep(1) # throttle metadata
