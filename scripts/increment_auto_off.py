#!/usr/bin/env python3
# A program that ticks a counter down until deactivating log_persistence

import logging
import sys
import json

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


response = requests.get('http://localhost:5001/settings/persist_logs', timeout=10)
state = response.json()

if state["persist_logs"] and state["auto_off_delay"] > 0:
  body: dict
  if state["auto_off_delay"] >= 1:
    delay = state["auto_off_delay"] - 1
    body = {
      "persist_logs": True,
      "auto_off_delay": delay,
    }
    logging.info(f"Persist logs will be automatically turned off in {delay} day(s)")
  else:
    body = {
      "persist_logs": False,
      "auto_off_delay": 14,  # Reset to default for next time
    }
    logging.info("Persist logs has been turned off automatically")

  json_data = json.dumps(body)
  requests.post(
    url='http://localhost:5001/settings/persist_logs',
    headers={'Content-Type': 'application/json'},
    data=json_data,
    timeout=10,
  )
