#!/usr/bin/env python3
import argparse
import os
import sys
import time

# Add the directory above this script's location to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import amplipi.rt

parser = argparse.ArgumentParser(description='Display AmpliPi fan status and optionally force on.')
parser.add_argument('-f', '--force', action='store_true', default=False, help="force the fans full on")
args = parser.parse_args()

preamp = amplipi.rt._Preamps()
preamp.force_fans(force=args.force)
while True:
  fan_on, ovr_tmp, fan_fail = preamp.read_fan_status()
  print(f'Fans: on={fan_on}, overtemp={ovr_tmp}, failed={fan_fail}')
  time.sleep(1.0)
