"""External display runner"""

import argparse
import sys

from loguru import logger as log

from amplipi import formatter
from amplipi.display.einkdisplay import EInkDisplay
from amplipi.display.tftdisplay import TFTDisplay

if __name__ == '__main__':
  if 'venv' not in sys.prefix:
    log.warning(f"Did you mean to run {__file__} from amplipi's venv?\n")

  parser = argparse.ArgumentParser(description='Display AmpliPi information on a TFT display.',
                                   formatter_class=formatter.AmpliPiHelpFormatter)
  parser.add_argument('-u', '--url', default='localhost', help="the AmpliPi's URL to contact")
  parser.add_argument('-r', '--update-rate', metavar='HZ', type=float, default=1.0,
                      help="the display's update rate in Hz")
  parser.add_argument('-s', '--sleep-time', metavar='S', type=float, default=60.0,
                      help="number of seconds to wait before sleeping, 0=don't sleep")
  parser.add_argument('-b', '--brightness', metavar='%', type=float, default=1.0,
                      help='the brightness of the backlight, range=[0.0, 1.0]')
  parser.add_argument('-i', '--iface', default='eth0',
                      help='the network interface to display the IP of')
  parser.add_argument('-t', '--test-board', action='store_true', default=False,
                      help='use SPI0 and test board pins')
  parser.add_argument('-l', '--log', metavar='LEVEL', default='WARNING',
                      help='set logging level as DEBUG, INFO, WARNING, ERROR, or CRITICAL')
  parser.add_argument('--test-timeout', metavar='SECS', type=float, default=0.0,
                      help='if >0, perform a hardware test and exit on success or timeout')
  args = parser.parse_args()

  args.log = args.log.upper()
  log.remove()
  log.add(sys.stderr, level=args.log)
  log.info(f'Running display with args={args}')

  displays = [TFTDisplay(args), EInkDisplay(args.iface, args.log)]
  success = False
  while not success and len(displays) > 0:
    d = displays.pop()
    # we use init to determine if the display is physically present
    if d and d.init():
      # successful init, run this display
      success = True
      d.run()

if not success:
  log.error(f"Display failed to initialize. Exiting.")
