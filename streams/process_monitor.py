#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time

args = sys.argv[1:]
print(f'Starting process monitor for process: {args}')

_START_TIME_THRESHOLD = 10  # seconds — consider a run "successful" if it lasted this long
_DEVICE_PROBE_TIMEOUT = 5   # seconds — hard cap on a single aplay readiness probe
_ORPHAN_KILL_AFTER = 4      # failed probes in a row before killing a stale holder


def _alsa_out_device(argv):
  """Return the ALSA loopback output device (-o lbXX) if the monitored
   process plays to one, else None. All of the device gating below is
   skipped for processes without such an argument."""
  for i, a in enumerate(argv[:-1]):
    if a == '-o' and argv[i + 1].startswith('lb'):
      return argv[i + 1]
  return None


OUT_DEV = _alsa_out_device(args)


def device_ready(dev):
  """True if the ALSA device can be opened for playback right now.
   Mirrors squeezelite's open path (loopback dmix): fails with EINVAL
   while a stale holder keeps the device busy, succeeds once it is free.
   Writes 1s of silence to a loopback nobody is reading — harmless."""
  try:
    res = subprocess.run(
        ['aplay', '-D', dev, '-r', '48000', '-f', 'S16_LE', '-c', '2',
         '-d', '1', '-q', '/dev/zero'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=_DEVICE_PROBE_TIMEOUT)
    return res.returncode == 0
  except Exception:
    return False


def print_device_diagnostics(dev):
  """Dump who currently holds the sound devices so a wedge is explained
   in the journal rather than inferred afterwards."""
  print(f'Device {dev} not ready — current /dev/snd holders:', flush=True)
  try:
    out = subprocess.run('fuser -v /dev/snd/pcm* 2>&1', shell=True,
                         capture_output=True, text=True, timeout=10)
    print((out.stdout + out.stderr).strip(), flush=True)
  except Exception as e:
    print(f'(fuser failed: {e})', flush=True)


def find_stale_holders(dev, own_child_pid):
  """PIDs of squeezelite processes (argv0 ends in 'squeezelite') playing
   to this exact device via -o <dev>, excluding ourselves and our own
   child. Strict match — cannot hit the monitor or unrelated processes."""
  pids = []
  for entry in os.listdir('/proc'):
    if not entry.isdigit():
      continue
    pid = int(entry)
    if pid in (own_child_pid, os.getpid()):
      continue
    try:
      with open(f'/proc/{pid}/cmdline', 'rb') as f:
        argv = f.read().decode(errors='replace').split('\0')
    except OSError:
      continue
    if not argv or not argv[0].endswith('squeezelite'):
      continue
    for i, a in enumerate(argv[:-1]):
      if a == '-o' and argv[i + 1] == dev:
        pids.append(pid)
        break
  return pids


def wait_for_device(dev, own_child_pid):
  """Block until the output device is openable. Converts the old
   crash-loop (spawn → EINVAL → die → respawn, silent for hours) into a
   quiet wait, and clears a stale squeezelite holder if one is wedging
   the loopback."""
  failures = 0
  while not device_ready(dev):
    failures += 1
    if failures == 1:
      print_device_diagnostics(dev)
    if failures == _ORPHAN_KILL_AFTER:
      for pid in find_stale_holders(dev, own_child_pid):
        print(f'Killing stale squeezelite holder pid={pid} on {dev}', flush=True)
        try:
          os.kill(pid, signal.SIGKILL)
        except OSError as e:
          print(f'(kill {pid} failed: {e})', flush=True)
    delay = min(2 ** failures, 30)
    print(f'Device {dev} busy (probe {failures} failed) — retrying in {delay}s...',
          flush=True)
    time.sleep(delay)
  if failures:
    print(f'Device {dev} ready again after {failures} failed probe(s).', flush=True)


proc = None
last_child_pid = -1


def signal_handler(sig, frame):
  """Signal handler function that sends the received signal to the
   subprocess and exits the script for certain signals."""
  print(f'Forwarding signal {sig} to subprocess.', flush=True)
  if proc is not None and proc.poll() is None:
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
  # Don't spawn into a busy loopback — the child would just exit with
  # EINVAL and we'd crash-loop while staying silent for hours.
  if OUT_DEV:
    wait_for_device(OUT_DEV, last_child_pid)

  start_time = time.monotonic()
  proc = subprocess.Popen(args)
  last_child_pid = proc.pid

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
