import os
import subprocess
from enum import Enum
from typing import Tuple

class Display:
  def init(self) -> bool:
    """Try initializing. Return True if success or False if failed.
    Must also clean up gpio before returning false."""
    pass

  def run(self):
    """Called after a successful init. Should handle the rendering
    of a new image, displaying that image, and looping."""
    pass

  def stop(self):
    """Called by exit handler. Stops the run method."""
    pass

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
