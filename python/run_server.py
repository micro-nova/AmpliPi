#!/usr/bin/python3
# this file starts an ethaudio server

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

# register signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start HTTP server (behind the scenes it runs in new thread)
ethaudio.Server(ethaudio.Api(ethaudio.api.MockRt()))

while True:
  sleep(0.1)
