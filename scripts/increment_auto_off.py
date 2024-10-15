#!/usr/bin/env python3
"""A program that ticks a counter down until deactivating log_persistence"""

import logging
import sys
import json
import re

import configparser
import requests
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

state_persist: bool
state_delay: int

api_read_failure = False
try:
  response = requests.get('http://localhost:5001/settings/persist_logs', timeout=10)
  state = response.json()

  state_persist = state["persist_logs"]
  state_delay = state["auto_off_delay"]
except KeyError as exc:
  logger.exception("Unable to read log persistence state through the api, attempting to read directly...")
  api_read_failure = True
except Exception as exc:
  logger.exception(f"increment_auto_off.py has failed with the following exception:\n{exc}")
  api_read_failure = True


if api_read_failure:
  try:
    # If the api is inaccessible, assume it is down for whatever reason and extrapolate that there is no race condition to reading it directly
    # This section is a copy of the /settings/persist_logs GET in asgi.py
    journalconf = configparser.ConfigParser(strict=False, allow_no_value=True)
    journalconf.read('/etc/systemd/journald.conf')

    logconf = configparser.ConfigParser(strict=False, allow_no_value=True)
    logconf.read('/var/log/logging.ini')

    persist = journalconf.get("Journal", "Storage", fallback="volatile")
    state_persist = True if persist not in ("volatile", "persistent") else persist == "persistent"  # If value is somehow invalid, assume it's True just in case

    if not logconf.has_option("logging", "auto_off_delay"):
      state_delay = 14
    auto_off = logconf.get("logging", "auto_off_delay", fallback="14")
    if not auto_off.isdigit() and bool(re.fullmatch(r'\d*\.\d+', auto_off)):
      # regex to check decimal state, this would lead to "123.45" and ".45" being true but not "123."
      # Exclude anything that isdigit() as to not overwrite valid user settings
      state_delay = round(float(auto_off)) if round(float(auto_off)) > 0 else 1  # Avoid instances where it could be zero as to not set the "do not deactivate" setting
    else:
      state_delay = int(auto_off) if auto_off.isdigit() else 14
  except Exception as exc:
    logger.exception(f"increment_auto_off.py has failed with the following exception:\n{exc}")


if state_persist and state_delay is not None:
  future_persist_state = state_delay != 1
  delay = state_delay - 1
  body = {
    "persist_logs": future_persist_state,
    "auto_off_delay": delay if future_persist_state else 14,  # If no longer persisting, set to default
  }

  api_write_failure = False
  try:
    json_data = json.dumps(body)
    response = requests.post(
      url='http://localhost:5001/settings/persist_logs',
      headers={'Content-Type': 'application/json'},
      data=json_data,
      timeout=10,
    )
    if response.ok:
      if future_persist_state:
        logging.info(f"Persist logs will be automatically turned off in {delay} day(s)")
      else:
        logging.info("Persist logs has been turned off automatically")
    else:
      logging.exception("Unable to update persist_logs state via api, attempting to write directly...")
      api_write_failure = True
  except Exception as exc:
    logger.exception(f"increment_auto_off.py has failed with the following exception:\n{exc}")
    api_write_failure = True

  if api_write_failure:
    # This section is a copy of the /settings/persist_logs POST in asgi.py
    try:
      conf = '/etc/systemd/journald.conf'
      tmp = '/tmp/journald.conf.tmp'
      journal = configparser.ConfigParser(strict=False, allow_no_value=True)
      journal.read(conf)

      if not journal.has_section("Journal"):
        journal.add_section('Journal')

      # goal_value is true if you wish to turn persistent logging on and false if you wish to turn it off
      if body["persist_logs"]:  # Set persist
        journal.set('Journal', 'Storage', 'persistent')
      else:  # Reset config to default as seen in configure.py
        journal.set('Journal', 'Storage', 'volatile')

      with open(tmp, 'w', encoding="utf-8") as conf_file:
        journal.write(conf_file)

      subprocess.run(['sudo', 'mv', tmp, conf], check=True)
      subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-journald'], check=True)

      if state_delay != body["auto_off_delay"]:
        logini = '/var/log/logging.ini'
        logtmp = '/tmp/logging.ini.tmp'
        log = configparser.ConfigParser(strict=False, allow_no_value=True)
        log.read(logini)
        log.set('logging', 'auto_off_delay', f"{body['auto_off_delay']}")  # Accept auto_off_delay as an int for type checking, parse to str for configParser validity
        with open(logtmp, 'w', encoding='utf-8') as file:
          log.write(file)
        subprocess.run(['sudo', 'mv', logtmp, logini], check=True)
        logging.info(f"Persist logs will be automatically turned off in {body['auto_off_delay']} day(s)")

    except Exception as exc:
      logger.exception(f"increment_auto_off.py has failed with the following exception:\n{exc}")
