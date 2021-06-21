#!/usr/bin/env python3
import argparse
import math
import os
import sys

# Add the directory above this script's location to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import amplipi.rt

def auto_int(x):
  return int(x, 0)

parser = argparse.ArgumentParser(description='Display AmpliPi preamp status.')
parser.add_argument('--led', type=auto_int, metavar='0xXX', help="override the LEDs")
args = parser.parse_args()

preamp = amplipi.rt._Preamps()

# Version
major, minor, git_hash, dirty = preamp.read_version()
if major is None:
  print("Couldn't read preamp version")
  sys.exit(1)
print(f'Version {major}.{minor}-{git_hash:07X}, {"dirty" if dirty else "clean"}')

# Sources/Zones
for zone in range(6):
  preamp.print_zone_state(zone)

# Power
pg_12v, pg_9v = preamp.read_power_good()
print(f'PGood 12V: {pg_12v}, 9V: {pg_9v}')

# Fans
fan_on, ovr_tmp, fan_fail = preamp.read_fan_status()
print(f'Fans: overridden={fan_on}, overtemp={ovr_tmp}, failed={fan_fail}')

# 24V and temp
hv1, hv2, tmp1, tmp2 = preamp.read_hv()
def temp2str(tmp: int):
  if tmp == -math.inf:
    tmp_str = 'Thermistor disconnected'
  elif tmp == math.inf:
    tmp_str = 'Thermistor shorted'
  else:
    tmp_str = f'{tmp:5.1f}\N{DEGREE SIGN}C'
  return tmp_str
print(f'HV1: {hv1:5.2f}V, {temp2str(tmp1)}')
print(f'HV2: {hv2:5.2f}V, {temp2str(tmp2)}')

# LEDs
if args.led:
  preamp.led_override(leds=args.led)

# TODO?
#'STANDBY'         : 0x04,
#'EXTERNAL_GPIO'   : 0x0D,
