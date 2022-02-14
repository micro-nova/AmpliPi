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

def temp2str(tmp: float):
  if tmp == -math.inf:
    tmp_str = 'Thermistor disconnected'
  elif tmp == math.inf:
    tmp_str = 'Thermistor shorted'
  else:
    tmp_str = f'{tmp:.1f}\N{DEGREE SIGN}C'
  return tmp_str

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

  # Power - note: failed only exists on Rev2 Power Board
  pg_9v, en_9v, pg_12v, en_12v, v12 = p.read_power_status(u)
  print('  Power Board Status')
  print(f'     9V:  EN={en_9v}, PG={pg_9v}')
  print(f'    12V:  EN={en_12v}, PG={pg_12v}, {v12} V')

  # Fans
  ctrl, fans_on, ovr_tmp, failed = p.read_fan_status(u)
  fan_duty = p.read_fan_duty(u)
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
  print(f'  HV1: {hv1:5.2f}V, {temp2str(hv1_tmp)}')
  print(f'  Amp Temps: {temp2str(amp1_tmp)}, {temp2str(amp2_tmp)}')

  # LEDs
  print_led_state(p.read_leds(u))

def self_check(p: amplipi.rt._Preamps):
  def unit_to_name(u: int):
    if u == 0:
      return 'Main'
    return f'Expander {u}'
  def print_err(u: int, s: str):
    print(f'\033[0;31m{unit_to_name(u)}: {s}\033[0m')
  def print_ok(u: int, s: str):
    print(f'\033[0;32m{unit_to_name(u)}: {s}\033[0m')
  success = True
  for u in range(len(p.preamps)):
    _, _, pg_12v, en_12v, v12 = p.read_power_status(u + 1)
    success &= pg_12v and en_12v and 6 < v12 < 12.5
    if pg_12v:
      print_ok(u, 'PG_12V ok')
    else:
      print_err(u, 'PG_12V bad')
    if en_12v:
      print_ok(u, 'EN_12V ok')
    else:
      print_err(u, 'EN_12V bad')
    if 6 < v12 < 12.5:
      print_ok(u, f'12V supply ok - {v12:.2f}V')
    else:
      print_err(u, f'12V supply bad - {v12:.2f}V')
    hv1_tmp, amp1_tmp, amp2_tmp = p.read_temps(u + 1)
    if 10 < hv1_tmp < 45:
      print_ok(u, f'HV1 Temp ok - {temp2str(hv1_tmp)}')
    else:
      success = False
      print_err(u, f'HV1 Temp bad - {temp2str(hv1_tmp)}')
    if 10 < amp1_tmp < 60:
      print_ok(u, f'AMP1 Temp ok - {temp2str(amp1_tmp)}')
    else:
      success = False
      print_err(u, f'AMP1 Temp bad - {temp2str(amp1_tmp)}')
    if 10 < amp2_tmp < 60:
      print_ok(u, f'AMP2 Temp ok - {temp2str(amp2_tmp)}')
    else:
      success = False
      print_err(u, f'AMP2 Temp bad - {temp2str(amp2_tmp)}')
    print()
  return success

def heat_test(p: amplipi.rt._Preamps, timeout: int):
  """ Requires manual heating, check for a 5 degC temp rise in ANY unit
      Timeout after 30 seconds
  """
  # Get initial temps
  a1t_s = []
  a2t_s = []
  for u in range(len(p.preamps)):
    _, a1t_temp, a2t_temp = p.read_temps(u + 1)
    a1t_s.append(a1t_temp)
    a2t_s.append(a2t_temp)
  start_time = time.time()
  success = False
  while not success and time.time() < start_time + timeout:
    for u in range(len(p.preamps)):
      _, a1t, a2t = p.read_temps(u + 1)
      if a1t > a1t_s[u] + 5:
        success = True
      if a2t > a2t_s[u] + 5:
        success = True
  return success

parser = argparse.ArgumentParser(description='Display AmpliPi preamp status.')
parser.add_argument('-u', type=int, choices=range(1,7), default=1, help="which unit's preamp to control. Default=1")
parser.add_argument('-r', action='store_true', default=False, help='reset preamp - does not set address!')
parser.add_argument('-b', action='store_true', default=False, help='enter bootloader mode (implies -r and UART passthrough for any previous units)')
parser.add_argument('-a', action='store_true', default=False, help="set i2c address, currently only can set master's address")
parser.add_argument('-f', action='store_true', default=False, help='force fans on')
parser.add_argument('-l', type=auto_int, metavar='0xXX', help="override the LEDs")
parser.add_argument('-q', action='store_true', default=False, help="don't print status")
parser.add_argument('-t', action='store_true', default=False, help='perform a voltage and temperature self-test')
parser.add_argument('-w', action='store_true', default=False, help="wait for key press before exiting")
parser.add_argument('--temps', action='store_true', default=False, help='print temps and exit')
parser.add_argument('--heat', type=int, metavar='TIMEOUT', help='perform a mannually-heated temp rise test')
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
preamps = amplipi.rt._Preamps(reset = reset, set_addr = args.a, bootloader = boot0, debug = False)

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

if not args.b:
  for u in range(len(preamps.preamps)):
    preamps.force_fans(preamp = u + 1, force = args.f)
  preamps.led_override(preamp = args.u, leds = args.l)

  if not args.q:
    time.sleep(0.1)       # Wait a bit to make sure internal I2C writes have finished
    print(f'{preamps}\n') # Print zone info for main unit
    for u in range(len(preamps.preamps)):
      print()
      print_status(preamps, u + 1)

  if args.w:
    input("Press Enter to continue...")

if args.t:
  if not self_check(preamps):
    sys.exit(2)
if args.heat:
  if not heat_test(preamps, args.heat):
    sys.exit(2)


# TODO? 'STANDBY' : 0x04
