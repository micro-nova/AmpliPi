#!/usr/bin/env python3

import sys
import subprocess
import signal
import time

args = sys.argv[1:]
print(f'Starting process monitor for process: {args}')

_START_TIME_THRESHOLD = 10  # seconds — consider a run "successful" if it lasted this long


def signal_handler(sig, frame):
  """Signal handler function that sends the received signal to the
   subprocess and exits the script for certain signals."""
  print(f'Forwarding signal {sig} to subprocess.', flush=True)
  proc.send_signal(sig)
  if sig in [signal.SIGINT, signal.SIGTERM, signal.SIGQUIT]:
    sys.exit(0)
  else:
    print(f"Received signal {sig}. Ignoring...", flush=True)


# Set up signal handlers for all signals
for sig in range(1, signal.NSIG):
  # Don't prop
  if sig == signal.SIGCHLD:
    continue
  try:
    signal.signal(sig, signal_handler)
  except:
    pass

consecutive_failures = 0

while True:
  start_time = time.monotonic()
  proc = subprocess.Popen(args)

  try:
    # Wait for the subprocess to complete
    proc.wait()

  except KeyboardInterrupt:
    # If the user presses Ctrl-C, send the interrupt signal to the subprocess
    proc.send_signal(signal.SIGINT)
    print(f'Process interrupted with KeyboardInterrupt. Stopping...', flush=True)
    break

  except Exception as e:
    print(f'Process crashed with error: {e}. Restarting...', flush=True)

  # If the subprocess exits with a zero code, break the loop
  if proc.returncode == 0:
    break

  # If the subprocess exits with a non-zero code, restart it
  print(
      f"Subprocess exited with non-zero code: {proc.returncode}. Restarting...", flush=True)

  # Track consecutive failures for exponential backoff.
  # Reset if the process ran long enough to be considered a successful start.
  elapsed = time.monotonic() - start_time
  if elapsed >= _START_TIME_THRESHOLD:
    consecutive_failures = 0
  else:
    consecutive_failures += 1

  backoff = min(2 ** consecutive_failures, 30)
  print(f"Waiting {backoff}s before restart (consecutive_failures={consecutive_failures})...", flush=True)
  time.sleep(backoff)
