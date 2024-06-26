#!/usr/bin/env python3

""" Test USB Ports """

import os.path
import signal
import sys
import time
from textwrap import dedent

PORTS = {
    '/sys/bus/usb/devices/1-1.2': 'INTERNAL',
    '/sys/bus/usb/devices/1-1.4': 'TOP',
    '/sys/bus/usb/devices/1-1.5': 'BOTTOM',
}

RED = '\033[0;31m'
GRN = '\033[0;32m'
NC = '\033[0m'

# Holds which ports have been detected.
detections = {f: False for f in PORTS}


def check_missing():
  """Report if all USB ports were detected or if any were missing."""
  missing = [PORTS[file]
             for file, exists in detections.items() if not exists]
  if len(missing) > 1:
    print(f'\n{RED}Test FAILED, {missing} usb ports were not detected.{NC}')
  elif len(missing) == 1:
    print(
        f'\n{RED}Test FAILED, {missing[0]} usb port was not detected.{NC}')
  else:
    print(f'{GRN}Test PASSED, all usb PORTS work!{NC}')


def exit_handler(_sig, _frame):
  """Handle SIGINT"""
  check_missing()
  sys.exit(0)


def usb_test():
  """\
  Verify all USB PORTS are working by connecting a device to each one.
  Test will timeout in 30 seconds. Press CTRL+C to exit early."""
  signal.signal(signal.SIGINT, exit_handler)
  print(dedent(usb_test.__doc__))
  count = 0
  tic = time.time()
  while not all(detections.values()):
    for file, exists in detections.items():
      if not exists and os.path.exists(file):
        count = count + 1
        print(
            f' - detected {PORTS[file]} usb port ({count}/{len(PORTS)} devices)')
        detections[file] = True
    if time.time() - tic > 30:
      break
  check_missing()
  # Stall to keep the terminal open so test results are visible.
  input("Press any key to exit...")


if __name__ == '__main__':
  usb_test()
