"""Common external display libraries"""

import os
import subprocess
import datetime
import requests
import socket

import netifaces as ni

from loguru import logger as log
from enum import Enum
from typing import Tuple, Optional, Union, Dict
from collections import namedtuple
from amplipi.display.statusinterface import set_custom_display_status, STATUS_FILENAME, DisplayStatus, DisplayError

from amplipi import models
from amplipi import auth

SysInfo = namedtuple('SysInfo', ['hostname', 'password', 'ip', 'status_code', "serial_number", "ext_count"])


STARTUP_MSG = "Starting Up"


def request_params() -> Optional[Dict]:
  if not auth.no_user_passwords_set():
    user = auth.list_users()[0]
    try:
      access_key = auth.get_access_key(user)
      return {'api-key': access_key}
    except:
      return None
  return None


class Display:
  """Abstract External Display
  Used to display system information like password and IP address"""

  def init(self) -> bool:
    """Try initializing. Return True if success or False if failed.
    Must also clean up gpio before returning false."""
    raise NotImplementedError('Display.init')

  def display_delivery_message(self):
    """Display the delivery message and exit"""
    raise NotImplementedError('Display.display_delivery_message')

  def run(self):
    """Called after a successful init. Should handle the rendering
    of a new image, displaying that image, and looping."""
    raise NotImplementedError('Display.run')

  def stop(self):
    """Called by exit handler. Stops the run method."""
    raise NotImplementedError('Display.stop')


class Color(Enum):
  """ Colors used in the AmpliPi front-panel display """
  GREEN = '#28a745'
  YELLOW = '#F0E68C'
  RED = '#FF0000'
  BLUE = '#0080ff'
  BLACK = '#000000'
  DARKGRAY = '#666666'
  LIGHTGRAY = '#999999'
  WHITE = '#FFFFFF'


class DefaultPass:
  """Helper class to read and verify the current pi user's password against
     the stored default AmpliPi password."""

  # Password config location
  PASS_DIR = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')
  PASS_FILE = os.path.join(PASS_DIR, 'default_password.txt')
  DEFAULT_PI_PASSWORD = 'raspberry'

  def __init__(self):
    self.default_password = ''
    self.pass_file_present = False
    self.update()

  def update(self) -> Tuple[str, Color]:
    """Check if the default password file has changed and if so
       verify if it is the pi user's current password.
    """
    old_presence = self.pass_file_present
    new_default = self.get_default_pw()
    if self.default_password != new_default or self.pass_file_present != old_presence:
      self.default_password = new_default
      self.default_in_use = self.check_pw(self.default_password)

    if self.default_in_use:
      if self.pass_file_present:
        # A random password has been set as the default for AmpliPi.
        return self.default_password, Color.YELLOW
      # Default Pi password is still in use, this isn't secure.
      return self.default_password, Color.RED
    # Current password has been changed from the default
    return 'User Set', Color.GREEN

  def get_default_pw(self) -> str:
    if os.path.exists(self.PASS_FILE):
      with open(self.PASS_FILE, 'r', encoding='utf-8') as pass_file:
        self.pass_file_present = True
        return pass_file.readline().rstrip()
    self.pass_file_present = False
    return self.DEFAULT_PI_PASSWORD

  @staticmethod
  def check_pw(pw: str) -> bool:
    """ Check if the given password is the pi user's current password. """
    try:
      subprocess.run(f'sudo python3 amplipi/display/check_pass {pw}', shell=True, check=True)
      return True
    except subprocess.CalledProcessError:
      return False


def load_status_from_file() -> Optional[Union[str, int]]:
  """Load a status from the status file"""
  try:
    with open(STATUS_FILENAME, "r") as f:
      data = f.read().split(",")
      if len(data) == 0:
        return None
      # Ignore the status if it is past its expiration date
      if data[1] != "None":
        expiration_date = datetime.datetime.strptime(data[1], '%Y-%m-%d %H:%M:%S.%f')
        if expiration_date < datetime.datetime.now():
          return None

      if data[0] == "None":
        return None
      if data[0].isdigit():
        return int(data[0])
      return data[0]
  except FileNotFoundError:
    return None
  except Exception as e:
    log.error(f"Failed to load status: {type(e).__name__}")
  return DisplayError.FILE_READ_ERROR


def get_num_expanders(url: str) -> int:
  """Returns the number of expanders connected to the AmpliPro"""
  try:
    req = requests.get(url, timeout=0.2, params=request_params())
    if req.status_code == 200:
      status = models.Status(**req.json())
      info = status.info
      if info is not None:
        return len(info.expanders)
      else:
        set_custom_display_status(DisplayStatus(int(DisplayError.API_NO_EXPANDER)))
        return 0
    else:
      set_custom_display_status(DisplayStatus(int(DisplayError.API_NO_EXPANDER)))
      return 0
  except Exception as e:
    log.error(f'Error getting number of expanders: {type(e).__name__}')
    set_custom_display_status(DisplayStatus(int(DisplayError.EXPANDER_EXCEPTION)))
    return 0


def get_status(url: str, no_serial_ok: bool = False) -> Tuple[Union[str, int], Optional[int], int]:
  """Returns the system's status code as either a str or int, a serial number, and how many expanders are hooked up"""

  serial: Optional[int] = None
  result_status: Union[str, int] = 0
  st: Optional[Union[str, int]] = load_status_from_file()
  starting_up = st == STARTUP_MSG
  if starting_up and st is not None:
    result_status = st

  # Check if API is running
  api_on = subprocess.run("systemctl --user is-active amplipi.service".split(), stdout=subprocess.DEVNULL)
  if api_on.returncode != 0:
    return DisplayError.NO_AMPLIPI_SERVICE, None, 0

  if url is None:
    return DisplayError.API_CANNOT_CONNECT, None, 0
  try:
    req = requests.get(url, timeout=0.2, params=request_params())
    if req.status_code == 200:
      status = models.Status(**req.json())
      zones = status.zones
      sources = status.sources
      if starting_up:
        set_custom_display_status(DisplayStatus(None, None))

      result_status = "READY"
      if (status.info is not None and status.info.serial.isdigit()) or no_serial_ok:
        if status.info is not None and status.info.serial.isdigit():
          serial = int(status.info.serial)

        if status.info is not None and status.info.is_streamer:
          for source in sources:
            if source.info is not None and source.info.state == "playing":
              result_status = "PLAYING"
            elif result_status is None:
              result_status = "READY"

        else:
          for zone in zones:
            source_for_zone = sources[zone.source_id].info
            if source_for_zone is not None:
              if source_for_zone.state == "playing":
                if zone.mute and result_status != "PLAYING":
                  result_status = "MUTED"
                else:
                  result_status = "PLAYING"
      elif status.info is not None and not status.info.serial.isdigit():
        if not starting_up and not no_serial_ok:
          result_status = DisplayError.NO_SERIAL_NUMBER
    else:
      if not starting_up:
        return DisplayError.API_NO_EXPANDER, 0, 0
  except requests.Timeout:
    if not starting_up:
      log.error('Timeout requesting AmpliPi status')
      return DisplayError.API_TIME_OUT, None, 0
  except ValueError:
    if not starting_up:
      log.error('Invalid json in AmpliPi status response')
      return DisplayError.API_INVALID_RESPONSE, None, 0
  except Exception as e:
    if not starting_up:
      log.error(f'Exception getting status: {type(e).__name__}')
      return DisplayError.API_ERROR_UNKNOWN, None, 0

  if serial is None and not no_serial_ok:
    if not starting_up:
      return DisplayError.NO_SERIAL_NUMBER, None, 0
  st = load_status_from_file()
  if st is not None:
    result_status = st

  return result_status, serial, get_num_expanders(url) if not starting_up else 0


def get_info(iface, default_pass, boot) -> SysInfo:
  """Get amplipi system info to display"""
  password, _ = default_pass.update()
  try:
    hostname = socket.gethostname() + '.local'
  except:
    hostname = 'None'
  try:
    ip_str = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
  except Exception as e:
    ip_str = 'Disconnected'
    if boot:
      return SysInfo(hostname, password, ip_str, STARTUP_MSG, -1, 0)
    else:
      _, serial, expanders = get_status("http://localhost/api")
      log.error(f'Failed to get IP address: {type(e).__name__}')
      return SysInfo(hostname, password, ip_str, DisplayError.NO_IP, serial, expanders)
  status, serial, expanders = get_status("http://localhost/api")
  return SysInfo(hostname, password, ip_str, status, serial, expanders)
