#! /usr/bin/python3
# -*- coding: utf-8 -*-

# Uses rtl_fm to access an RTL-SDR dongle, redsea to process RDS data (if any), and aplay to output to audio device
# fmradio.png file that accompanies this is from PixelKit (http://pixelkit.com) and is licensed under CC Attribution 4.0.

import time
import json
import vlc
import argparse
import subprocess
import os
import sys
import traceback

parser = argparse.ArgumentParser(prog='runfm', description='play a radio station using an RTL-SDR dongle')
parser.add_argument('freq', type=str, help='radio station frequency (ex: 96.1)')
parser.add_argument('output', type=str, help='alsa output', nargs='?', default=None)
parser.add_argument('--song-info', type=str, help='file to update with current song information in json format')
parser.add_argument('--log', type=str, help='log file (defaults to stdout)', default=None)
parser.add_argument('--test', action='store_true', help='verify the frequency is valid and return')
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

freq = ""
if args.freq:
  freq = args.freq + 'M'
else:
  log('Missing or invalid frequency.')
  sys.exit(1)

if args.song_info:
  try:
    f = open(args.song_info, "wt")

    #TODO:
    #f.write(json.dumps({"station": str(player.get_state())}))
    f.close()
  except Exception:
    log(sys.exc_info())
    exit(1)


def main():
  latest_info = {
    'station':'',
    'callsign':'',
    'prog_type': '',
    'radiotext': ''
  }

  update = False

  rtlfm_args = f'rtl_fm -M fm -f {freq}M -s 171k -A std -p 0 -l 0 -E deemp -g 20 -F 9'.split()
  redsea_args = ['redsea', '-u', '-p', '--feed-through']
  aplay_args = ['aplay', '-r', '171000', '-f', 'S16_LE', '--device', '{}'.format(args.output)]

  rtlfm_proc = subprocess.Popen(args=rtlfm_args, bufsize=1024, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  redsea_proc = subprocess.Popen(args=redsea_args, bufsize=1024, stdin=rtlfm_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  aplay_proc = subprocess.Popen(args=aplay_args, bufsize=1024, stdin=redsea_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  try:
    if args.test:
      log('success')
      sys.exit(0)

    while redsea_proc.returncode is None:
      # Read RDS data stored in the JSON data from redsea, which is available from redsea's stderr pipe
      try:
        redsea_proc.poll()
        rds_raw = redsea_proc.stderr.readline()
        if len(rds_raw) > 0:
          if args.verbose:
            log(f"""RDS metadata:
              {rds_raw}
            """)

          rds = json.loads(rds_raw)
          if "ps" in rds:
            if rds["ps"] != latest_info["station"]:
              latest_info["station"] = rds["ps"]
              update = True
          if "callsign" in rds:
            if rds["callsign"] != latest_info["callsign"]:
              latest_info["callsign"] = rds["callsign"]
              update = True
          if "prog_type" in rds:
            if rds["prog_type"] != latest_info["prog_type"]:
              latest_info["prog_type"] = rds["prog_type"]
              update = True
          if "radiotext" in rds:
            if rds["radiotext"] != latest_info["radiotext"]:
              latest_info["radiotext"] = rds["radiotext"]
              update = True
            print(f'rt; "{rds["radiotext"]}"')
          #elif "partial_radiotext" in rds:
            # this data is bad a lot of times, probably worth updating on
          #  if rds["partial_radiotext"] != latest_info["radiotext"]:
          #    latest_info["radiotext"] = rds["partial_radiotext"]
          #    update = True
          #  print(f'pr: "{rds["partial_radiotext"]}"')
        else:
          if args.verbose:
            log("No RDS data")

      except json.JSONDecodeError:
        #print ("JSONDecodeError. Line was: ")
        #print(fmradio_proc.stderr.readline())
        pass


      if args.test:
        log('success')
        sys.exit(0)

      # If any of the fields have changed from its previous value, update args.song-info
      if args.song_info and update:
        try:
          f = open(args.song_info, "wt")
          f.write(json.dumps(latest_info))
          f.close()

          if args.verbose:
            log('Updated song_info')
            log(json.dumps(latest_info))
        except Exception:
          log('Error: %s' % sys.exc_info()[1])

      update = False

  except KeyboardInterrupt:
    print ("Shutdown requested...exiting")
    os.system("killall -9 rtl_fm")
    traceback.print_exc(file=sys.stdout)
    sys.exit(0)
  except Exception:
    os.system("killall -9 rtl_fm")
    traceback.print_exc(file=sys.stdout)
    sys.exit(0)

if __name__ == "__main__":
  main()
