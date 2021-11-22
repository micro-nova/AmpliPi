#!/usr/bin/env python3
import argparse
import math
import os
import sys
import time
from datetime import datetime
# Add the directory above this script's location to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import amplipi.rt

def auto_int(x):
  return int(x, 0)

def print_led_state(led: int):
  """ Print the state of the front-panel LEDs """
  if led is not None:
    green = led & 0x01
    red = (led >> 1) & 0x01
    zones = [(led >> i) & 0x01 for i in range(2,8)]
    rg = 'YELLOW' if red and green else 'RED' if red else 'GREEN' if green else 'OFF'
    print('  LEDS:        |         ZONES')
    print('    ON/STANDBY | 1 | 2 | 3 | 4 | 5 | 6')
    print('  ------------------------------------')
    print(f'    {rg:^10} | {zones[0]} | {zones[1]} | {zones[2]} | {zones[3]} | {zones[4]} | {zones[5]}')

def print_status(p: amplipi.rt._Preamps, u: int):
  print(f'Status of unit {u}:')

  # Version
  major, minor, git_hash, dirty = p.read_version(u)
  if major is None:
    print("  Couldn't read preamp version")
    sys.exit(1)
  print(f'  Version {major}.{minor}-{git_hash:07X}, {"dirty" if dirty else "clean"}')

  # Sources/Zones (Doesn't work right now)
  #for zone in range(6*(u-1), 6*u):
  #  p.print_zone_state(zone)

  # Power - note: failed only exists on Rev2 Power Board
  pg_9v, en_9v, pg_12v, en_12v, v12 = p.read_power_status(u)
  print('  Power Board Status')
  print(f'     9V:  EN={en_9v}, PG={pg_9v}')
  print(f'    12V:  EN={en_12v}, PG={pg_12v}, {v12} V')

  # Fans
  ctrl, fans_on, ovr_tmp, failed = p.read_fan_status(u)
  fan_duty = preamps.read_fan_duty(args.u)
  print('  Fan Status')
  if ctrl == amplipi.rt.FanCtrl.MAX6644:
    fan_str = f', Failed={failed}'
  elif ctrl == amplipi.rt.FanCtrl.PWM:
    fan_str = f', Duty={fan_duty}'
  elif ctrl == amplipi.rt.FanCtrl.LINEAR:
    fan_str = f', On={fans_on}'
  elif ctrl == amplipi.rt.FanCtrl.FORCED:
    fan_str = ' ON'
  print(f'    Fans: Control={ctrl.name}{fan_str}')
  print(f'    Overtemp: {ovr_tmp}')

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
  print(f'  HV1: {hv1:5.2f}V, {temp2str(hv1_tmp)}')
  print(f'  Amp Temps: {temp2str(amp1_tmp)}, {temp2str(amp2_tmp)}')

  # LEDs
  print_led_state(p.read_leds(u))

parser = argparse.ArgumentParser(description='Display AmpliPi preamp status.')
parser.add_argument('-u', type=int, choices=range(1,7), default=1, help="which unit's preamp to control. Default=1")
parser.add_argument('-r', action='store_true', default=False, help='reset preamp - does not set address!')
parser.add_argument('-b', action='store_true', default=False, help='enter bootloader mode (implies -r and UART passthrough for any previous units)')
parser.add_argument('-a', action='store_true', default=False, help="set i2c address, currently only can set master's address")
parser.add_argument('-f', action='store_true', default=False, help='force fans on')
parser.add_argument('-l', type=auto_int, metavar='0xXX', help="override the LEDs")
parser.add_argument('-w', action='store_true', default=False, help="wait for key press before exiting")
parser.add_argument('--temps', action='store_true', default=False, help='print temps and exit')
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
preamps = amplipi.rt._Preamps(reset = reset, set_addr = args.a, bootloader = boot0, debug = not args.temps)

# Used for temperature recording
if args.temps:
  fan_duty = preamps.read_fan_duty(args.u)
  hv1_tmp, amp1_tmp, amp2_tmp = preamps.read_temps(args.u)
  with open('/sys/class/thermal/thermal_zone0/temp') as f:
    pi_tmp = int(f.read()) / 1000
  time = datetime.now().strftime('%H:%M:%S')
  print(f'{time},{fan_duty:.1f},{hv1_tmp:.1f},{amp1_tmp:.1f},{amp2_tmp:.1f},{pi_tmp:.1f}')
  sys.exit(0)

if args.u > 1 and args.r:
  print("Reseting expansion units is a work in progress...")
if args.u > 1 and args.b:
  print("Bootloading expansion units is a work in progress...")

if not args.b and len(preamps.preamps) > args.u:
  preamps.force_fans(preamp = args.u, force = args.f)
  preamps.led_override(preamp = args.u, leds = args.l)

  time.sleep(0.1) # Wait a bit to make sure internal I2C writes have finished
  for u in range(len(preamps.preamps)):
    print()
    print_status(preamps, u + 1)

  if args.w:
    input("Press Enter to continue...")

# TODO? 'STANDBY' : 0x04
