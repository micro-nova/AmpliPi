#!/usr/bin/env python3

""" Test USB Ports """

import time
import os.path

PORTS = {
  '/sys/bus/usb/devices/1-1.2': 'INTERNAL',
  '/sys/bus/usb/devices/1-1.4': 'TOP',
  '/sys/bus/usb/devices/1-1.5': 'BOTTOM',
}

def usb_test():
  """ Verify all USB PORTS are working by connecting a device to each one """
  print(usb_test.__doc__)
  detections = { f: False for f in PORTS }
  count = 0
  tic = time.time()
  while not all(detections.values()):
    for file, exists in detections.items():
      if not exists and os.path.exists(file):
        count = count + 1
        print(f' - detected {PORTS[file]} usb port ({count}/{len(PORTS)} devices)')
        detections[file] = True
    if time.time() - tic > 30:
      missing = [PORTS[file] for file, exists in detections.items() if not exists]
      if len(missing) > 1:
        print(f'Test FAILED, {missing} usb PORTS were not detected')
      else:
        print(f'Test FAILED, {missing[0]} usb port was not detected')
      break
  if all(detections.values()):
    print('Test PASSED, all usb PORTS work!')
  # For now let's stall to keep the terminal open
  while True:
    pass

if __name__ == '__main__':
  usb_test()
