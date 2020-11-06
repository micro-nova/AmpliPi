#!/usr/bin/python3
# this file starts an ethaudio server

import argparse

# our ethaudio library
import ethaudio

# sleep
from time import sleep

# program termination
import signal
import sys

# setup a signal handler to stop the server
def signal_handler(sig, frame):
  """ Stop the thread and cleanup if this script is stopped"""
  print('\nSIGINT/SIGTERM detected. Preparing to exit...')
  # Exit application
  sys.exit(0)

# parse args
parser = argparse.ArgumentParser(description='Run EthAudio server')
parser.add_argument('--mock', action='store_true', help='Use mock preamp connection')
parser.add_argument('--config', default='saved_state.json', help='config file to load')
args = parser.parse_args()

# register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start HTTP server (behind the scenes it runs in new thread)
ethaudio.Server(ethaudio.Api(ethaudio.api.RpiRt(args.mock), args.config))

while True:
  sleep(0.1)
