#!/usr/bin/env python3
import argparse
import math
import os
import sys
import time
from datetime import datetime
from enum import IntEnum
from typing import Optional

# Add the directory above this script's location to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from amplipi import formatter  # nopep8
from amplipi import rt         # nopep8


class ExitCode(IntEnum):
  """Exit error code"""
  SUCCESS = 0
  UNIT_NOT_FOUND = 1
  BAD_VERSION = 2
  SELF_TEST_FAILED = 3
  HEAT_TEST_FAILED = 4


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
    zones = [(led >> i) & 0x01 for i in range(2, 8)]
    rg = 'YELLOW' if red and green else 'RED' if red else 'GREEN' if green else 'OFF'
    print('  LEDS:        |         ZONES')
    print('    ON/STANDBY | 1 | 2 | 3 | 4 | 5 | 6')
    print('  ------------------------------------')
    print(f'    {rg:^10} | {zones[0]} | {zones[1]} | {zones[2]} | {zones[3]} | {zones[4]} | {zones[5]}')


def print_status(p: rt._Preamps, u: int):
  """ Print the status of a single AmpliPi unit """
  print(f'Status of unit {u}:')

  # Version
  major, minor, git_hash, dirty = p.read_version(u)
  if major is None:
    print("  Couldn't read preamp version")
    sys.exit(ExitCode.BAD_VERSION)
  print(f'  Version {major}.{minor}-{git_hash:07X}, {"dirty" if dirty else "clean"}')

  # Power - note: failed only exists on Rev2 Power Board
  pg_9v, en_9v, pg_12v, en_12v, v12 = p.read_power_status(u)
  print(f'   9V: EN={en_9v}, PG={pg_9v}')
  print(f'  12V: EN={en_12v}, PG={pg_12v}, {v12} V')

  # 24V and temp
  hv1, hv2 = p.read_hv(u)
  hv1_tmp, hv2_tmp, amp1_tmp, amp2_tmp = p.read_temps(u)
  print(f'  HV1: {hv1:5.2f}V, {temp2str(hv1_tmp)}')
  if (hv2 is not None):
    print(f'  HV2: {hv2:5.2f}V, {temp2str(hv2_tmp)}')
  print(f'  Amp Temps: {temp2str(amp1_tmp)}, {temp2str(amp2_tmp)}')

  # Fans
  ctrl, fans_on, ovr_tmp, failed, smbus = p.read_fan_status(u)
  fan_duty = 100 * p.read_fan_duty(u)  # Percent
  if ctrl == rt.FanCtrl.MAX6644:
    fan_str = f'Failed={failed}, '
  elif ctrl == rt.FanCtrl.PWM:
    fan_str = f'Duty={fan_duty:.0f}%, '
  elif ctrl == rt.FanCtrl.LINEAR:
    fan_str = f'{"On" if fans_on else "Off"}, '
  elif ctrl == rt.FanCtrl.FORCED:
    fan_str = 'On, '
  print(f'  Fans: {fan_str}Control={ctrl.name}, Overtemp={ovr_tmp}, SMBus={smbus}')

  # LEDs
  print_led_state(p.read_leds(u))


def self_check(p: rt._Preamps, unit: Optional[int] = None) -> bool:
  """ Perform a self-check of voltage and temperature on every AmpliPi Unit """
  def unit_to_name(u: int):
    if u == 0:
      return 'Main'
    return f'Expander {u}'

  def print_cond(u: int, ok: bool, s: str):
    return print(f'\033[0;3{2 if ok else 1}m{unit_to_name(u)}: {s}\033[0m')
  success = True
  for u in range(len(p.preamps)):
    if not unit or u + 1 == unit:  # u is 0-based, unit is 1-based
      _, _, pg_12v, _, v12 = p.read_power_status(u + 1)
      v12_ok = 6 < v12 < 12.5
      success &= pg_12v and v12_ok
      print_cond(u, pg_12v, f'PG_12V {"ok" if pg_12v else "bad"}')
      print_cond(u, v12_ok, f'12V supply {"ok" if v12_ok else "bad"} - {v12:.2f}V')
      hv1_tmp, hv2_tmp, amp1_tmp, amp2_tmp = p.read_temps(u + 1)
      hv2_present = hv2_tmp is not None
      hv1_ok = -19 <= hv1_tmp <= 106
      hv2_ok = True
      if hv2_present:
        hv2_ok = -19 <= hv2_tmp <= 106
      amp1_ok = -19 < amp1_tmp <= 106
      amp2_ok = -19 < amp2_tmp <= 106
      success &= hv1_ok and hv2_ok and amp1_ok and amp2_ok
      print_cond(u, amp1_ok, f'AMP1 Temp {"ok" if amp1_ok else "bad"}  - {temp2str(amp1_tmp)}')
      print_cond(u, amp2_ok, f'AMP2 Temp {"ok" if amp2_ok else "bad"}  - {temp2str(amp2_tmp)}')
      print_cond(u, hv1_ok, f'HV1 Temp {"ok" if hv1_ok else "bad"}   - {temp2str(hv1_tmp)}')
      if hv2_present:
        print_cond(u, hv2_ok, f'HV2 Temp {"ok" if hv2_ok else "bad"}   - {temp2str(hv2_tmp)}')
      print()
  return success


def heat_test(p: rt._Preamps, unit: int, timeout: int):
  """ Requires manual heating, check for a 5 degC temp rise in ANY unit
      Timeout after `timeout` seconds.
      Note: `unit` is a 1-based index.
  """
  # Get initial temps
  _, _, a1t_s, a2t_s = p.read_temps(unit)
  start_time = time.time()
  success = False
  while not success and time.time() < start_time + timeout:
    _, _, a1t, a2t = p.read_temps(unit)
    if a1t > a1t_s + 5 or a2t > a2t_s + 5:
      success = True
  return success


parser = argparse.ArgumentParser(description='Display AmpliPi preamp status.',
                                 formatter_class=formatter.AmpliPiHelpFormatter)
parser.add_argument('-u', '--unit', type=int, choices=range(1, 7), default=1,
                    help="which unit's preamp to control. Default=1")
parser.add_argument('-r', '--reset', action='store_true', default=False,
                    help='reset preamp - does not set address!')
parser.add_argument('-b', '--bootload', action='store_true', default=False,
                    help='enter bootloader mode (implies -r and UART passthrough for any previous units)')
parser.add_argument('-a', '--address', action='store_true', default=False,
                    help="set i2c address, currently only can set master's address")
parser.add_argument('-f', '--force-fans', action='store_true', default=False,
                    help='force fans on')
parser.add_argument('-l', '--leds', type=auto_int, metavar='0xXX',
                    help="override the LEDs")
parser.add_argument('-q', '--quiet', action='store_true', default=False,
                    help="don't print status")
parser.add_argument('-t', '--self-test', action='store_true', default=False,
                    help='perform a voltage and temperature self-test')
parser.add_argument('-w', '--wait', action='store_true', default=False,
                    help="wait for key press before exiting")
parser.add_argument('--temps', action='store_true', default=False,
                    help='print temps and exit')
parser.add_argument('--heat', type=int, metavar='TIMEOUT',
                    help='perform a manually-heated temp rise test')
args = parser.parse_args()

# Force a reset if bootloader is requested
if args.bootload:
  args.reset = True

# If unit > 0, there is no way to set the address
if args.address and args.unit > 1:
  print("Can't set the address of an expansion unit directly, ignoring -a.")
  args.address = False

# If resetting into bootloader mode, we can't set the address
if args.address and args.bootload:
  print("Can't enter bootloader mode and also set address. NOT setting address.")
  args.address = False

# Setup preamp connection. args.reset = Optionally reset master (unit 0)
reset = args.unit == 1 and args.reset
boot0 = args.unit == 1 and args.bootload
preamps = rt._Preamps(reset=reset, set_addr=args.address,
                      bootloader=boot0, debug=False)

# Used for temperature recording
if args.temps:
  fan_duty = preamps.read_fan_duty(args.unit)
  hv1_tmp, hv2_tmp, amp1_tmp, amp2_tmp = preamps.read_temps(args.unit)
  with open('/sys/class/thermal/thermal_zone0/temp') as f:
    pi_tmp = int(f.read()) / 1000
  time = datetime.now().strftime('%H:%M:%S')
  print(f'{time},{fan_duty:.1f},{hv1_tmp:.1f},{amp1_tmp:.1f},{amp2_tmp:.1f},{pi_tmp:.1f}')
  sys.exit(ExitCode.SUCCESS)

if args.unit > 1 and args.reset:
  print("Resetting expansion units is a work in progress...")
if args.unit > 1 and args.bootload:
  print("Bootloading expansion units is a work in progress...")

# Print status if not entering bootloader mode
error = ExitCode.SUCCESS
if not args.bootload:
  if len(preamps.preamps) < args.unit:
    print('Error: desired unit does not exist', file=sys.stderr)
    error = ExitCode.UNIT_NOT_FOUND
  else:
    preamps.force_fans(preamp=args.unit, force=args.force_fans)
    preamps.led_override(preamp=args.unit, leds=args.leds)

    if not args.quiet:
      time.sleep(0.1)       # Wait a bit to make sure internal I2C writes have finished
      # Useless until rt.py reads from micro directly
      # print(f'{preamps}\n') # Print zone info for main unit
      for u in range(len(preamps.preamps)):
        print_status(preamps, u + 1)

if args.self_test:
  if not self_check(preamps, args.unit):
    error = ExitCode.SELF_TEST_FAILED
if args.heat:
  if not heat_test(preamps, args.unit, args.heat):
    error = ExitCode.HEAT_TEST_FAILED

if args.wait:
  input("Press Enter to continue...")

sys.exit(error)

# TODO? 'STANDBY' : 0x04
