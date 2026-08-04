#!/usr/bin/env python3
"""A program that ticks a counter down until deactivating log_persistence"""

import json
import logging
import subprocess
import sys
import time

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

PERSIST_LOGS_URL = 'http://localhost:5001/settings/persist_logs'


def restart_updater_and_wait():
  """ If the updater API isn't responding, the most likely cause is that the amplipi-updater
  service itself is down (crashed, mid-restart, etc.), not something specific to persist_logs.
  Restarting it and retrying once is simpler - and far less likely to drift out of sync - than
  reimplementing asgi.py's journald/logging.ini handling a second time here (see GitHub #971,
  where the previous copy of that logic had done exactly that and gone stale/buggy). """
  logger.warning("Updater API call failed, restarting amplipi-updater and retrying once...")
  subprocess.run(['sudo', 'systemctl', 'restart', 'amplipi-updater'], check=False)
  time.sleep(5)


def get_persist_state() -> dict:
  try:
    response = requests.get(PERSIST_LOGS_URL, timeout=10)
    response.raise_for_status()
    return response.json()
  except Exception:
    restart_updater_and_wait()
    response = requests.get(PERSIST_LOGS_URL, timeout=10)
    response.raise_for_status()
    return response.json()


try:
  state = get_persist_state()
  state_persist = state["persist_logs"]
  state_delay = state["auto_off_delay"]
except Exception as exc:
  logger.exception(f"increment_auto_off.py could not read persist_logs state, skipping this run:\n{exc}")
  sys.exit(1)


if state_persist and state_delay is not None:
  future_persist_state = state_delay != 1
  delay = state_delay - 1
  body = {
    "persist_logs": future_persist_state,
    "auto_off_delay": delay if future_persist_state else 14,  # If no longer persisting, set to default
  }

  def post_persist_state():
    return requests.post(
      url=PERSIST_LOGS_URL,
      headers={'Content-Type': 'application/json'},
      data=json.dumps(body),
      timeout=10,
    )

  try:
    response = post_persist_state()
    if not response.ok:
      restart_updater_and_wait()
      response = post_persist_state()

    if response.ok:
      if future_persist_state:
        logger.info(f"Persist logs will be automatically turned off in {delay} day(s)")
      else:
        logger.info("Persist logs has been turned off automatically")
    else:
      logger.error(f"Unable to update persist_logs state via api: {response.status_code} {response.text}")
  except Exception as exc:
    logger.exception(f"increment_auto_off.py failed to update persist_logs state:\n{exc}")
