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

def print_status(p: amplipi.rt._Preamps, u: int):
  # Version
  major, minor, git_hash, dirty = p.read_version(u)
  if major is None:
    print("Couldn't read preamp version")
    sys.exit(1)
  print(f'Version {major}.{minor}-{git_hash:07X}, {"dirty" if dirty else "clean"}')

  # Sources/Zones
  for zone in range(6*(u-1), 6*u):
    p.print_zone_state(zone)

  # Power board - note: failed only exists on Rev2 Power Board
  pg_12v, en_12v, ovr_tmp, fan_on, fan_fail = p.read_power_status(u)
  print('Power Board Status')
  print(f'  12V:  EN={en_12v}, PG={pg_12v}')
  print(f'  Fans: On={fan_on}, Failed={fan_fail}')
  print(f'  Overtemp: {ovr_tmp}')

  # 24V and temp
  hv1 = p.read_hv(u)
  hv1_tmp, amp1_tmp, amp2_tmp = p.read_temps(u)
  def temp2str(tmp: int):
    if tmp == -math.inf:
      tmp_str = 'Thermistor disconnected'
    elif tmp == math.inf:
      tmp_str = 'Thermistor shorted'
    else:
      tmp_str = f'{tmp:5.1f}\N{DEGREE SIGN}C'
    return tmp_str
  print(f'HV1: {hv1:5.2f}V, {temp2str(hv1_tmp)}')
  print(f'Amp Temps: {temp2str(amp1_tmp)}, {temp2str(amp2_tmp)}')

  # LEDs
  p.print_led_state(u)

parser = argparse.ArgumentParser(description='Display AmpliPi preamp status.')
parser.add_argument('-u', type=int, choices=range(1,7), default=1, help="which unit's preamp to control. Default=1")
parser.add_argument('-r', action='store_true', default=False, help='reset preamp - does not set address!')
parser.add_argument('-b', action='store_true', default=False, help='enter bootloader mode (implies -r and UART passthrough for any previous units)')
parser.add_argument('-a', action='store_true', default=False, help="set i2c address, currently only can set master's address")
parser.add_argument('-f', action='store_true', default=False, help='force fans on')
parser.add_argument('-l', type=auto_int, metavar='0xXX', help="override the LEDs")
args = parser.parse_args()

# Force a reset if bootloader is requested
if args.b:
  args.r = True

# If unit > 0, there is no way to set the address
if args.a and args.u > 1:
  print("Can't set the address of an expansion unit directly, ignoring -a.")
  args.a = False

# If resetting into bootloader mode, we can't set the address
if args.a and args.b:
  print("Can't enter bootloader mode and also set address. NOT setting address.")
  args.a = False

# Setup preamp connection. args.r = Optionally reset master (unit 0)
reset = args.u == 1 and args.r
boot0 = args.u == 1 and args.b
preamps = amplipi.rt._Preamps(reset = reset, set_addr = args.a, bootloader = boot0)

if args.u > 1 and args.r:
  print("Reseting expansion units is a work in progress...")
if args.u > 1 and args.b:
  print("Bootloading expansion units is a work in progress...")

if not args.b:
  preamps.force_fans(preamp = args.u, force = args.f)
  if args.l:
    preamps.led_override(preamp = args.u, leds = args.l)
  else:
    preamps.led_override(preamp = args.u, override=False)

  print_status(preamps, args.u)

# TODO? 'STANDBY' : 0x04
