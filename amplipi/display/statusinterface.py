#!/usr/bin/env python3
"""Display Status Interface"""

import datetime

from loguru import logger as log
from typing import Optional, Union
from enum import IntEnum

# Status is stored and written/read here
STATUS_FILENAME = 'display-status.txt'


class DisplayStatus:
  # Status as either a string (working normally) or int (error)
  status: Optional[Union[str, int]]

  # When this status is set to expire, default is 10 seconds
  expiration: Optional[datetime.datetime]

  def __init__(self, status: Optional[Union[str, int]], expiration: Optional[datetime.datetime] =
               datetime.datetime.now() + datetime.timedelta(seconds=10)):
    self.status = status
    self.expiration = expiration


class DisplayError(IntEnum):
  NO_AMPLIPI_SERVICE = 0
  NO_IP = 1
  API_CANNOT_CONNECT = 10
  API_TIME_OUT = 11
  API_INVALID_RESPONSE = 12
  API_ERROR_UNKNOWN = 13
  FILE_READ_ERROR = 14
  NO_SERIAL_NUMBER = 15
  EXPANDER_EXCEPTION = 16
  API_NO_EXPANDER = 17
  API_CANNOT_FIND_STATUS = 18


def set_custom_display_status(status: DisplayStatus) -> None:
  """Set a custom status for the amplipi system info, as either a string status or int error code, optionally with an expiration date/time"""
  try:
    with open(STATUS_FILENAME, "w+") as f:
      f.write(str(status.status) + "," + str(status.expiration))
  except Exception as e:
    log.error(f'Failed to set status {status.status}: {e}')
