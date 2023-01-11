#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import time

from amplipi import formatter
from amplipi.display import epd2in13_V3
import socket
import netifaces as ni
from PIL import Image,ImageDraw,ImageFont

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

  def update(self) -> str:
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
        return self.default_password
      # Default Pi password is still in use, this isn't secure.
      return self.default_password
    # Current password has been changed from the default
    return 'User Set'

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


def update_display(host_name, password, ip_str):
  print('update_display')
  # Get fonts
  #fontname = 'DejaVuSansMono'
  fontname = 'DejaVuSansMono-Bold'
  fontsize=20
  try:
    font = ImageFont.truetype(fontname, fontsize)
  except:
    print(f'Failed to load font {fontname}')
    sys.exit(3)

  ascent, descent = font.getmetrics()
  cw = font.getlength(" ")
  ch = ascent + descent
  print(f'Font height = {ch}, width = {cw}')

  try:
    epd = epd2in13_V3.EPD()
    height = epd.width # rotated
    width = epd.height # rotated
    print(f'Screen height = {height}, width = {width}')
    epd.init()
    epd.Clear(0xFF)
    image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    draw = ImageDraw.Draw(image)

    interval = (4/3) * ch
    start = interval/2
    draw.text((0, start + 0*interval), f'Host: {host_name}', font=font, fill=0)
    draw.text((0, start + 1*interval), f'Pass: {password}', font=font, fill=0)
    draw.text((0, start + 2*interval), f'IP:   {ip_str}', font=font, fill=0)

    image = image.rotate(180) # flip
    print('displaying image')
    epd.display(epd.getbuffer(image))

    epd.sleep()
  except IOError as e:
    print(f'Error: {e}')
  except KeyboardInterrupt:
    print('CTRL+C')
    epd2in13_V3.epdconfig.module_exit()

def get_info(args, default_pass):
  password = default_pass.update()
  try:
    host_name = socket.gethostname() + '.local'
  except:
    # TODO: uhh can this even happen
    host_name = 'None'
  try:
    ip_str = ni.ifaddresses(args.iface)[ni.AF_INET][0]['addr']
  except:
    ip_str = 'Disconnected'

  return host_name, password, ip_str

def run(args=None):
  print('eink run')
  default_pass = DefaultPass()
  host_name, password, ip_str = get_info(args, default_pass)

  update_display(host_name, password, ip_str)
  time.sleep(8)

  while True:
    print('eink loop')
    # poll stale by checking if info differs
    new_host_name, new_password, new_ip_str = get_info(args, default_pass)

    if new_host_name != host_name or new_password != password or new_ip_str != ip_str:
      host_name = new_host_name
      password = new_password
      ip_str = new_ip_str
      update_display(host_name, password, ip_str)

    # wait before polling again
    time.sleep(8)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Display AmpliPi information on a TFT display.',
                                   formatter_class=formatter.AmpliPiHelpFormatter)
  parser.add_argument('-i', '--iface', default='eth0',
                      help='the network interface to display the IP of')
  args = parser.parse_args()
  run(args)
