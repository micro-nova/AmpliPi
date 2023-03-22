#!/usr/bin/env python3
import argparse
import sys
import time
from typing import Tuple

from amplipi import formatter
from amplipi.display import epd2in13_V3
import socket
import netifaces as ni
from PIL import Image, ImageDraw, ImageFont

from amplipi.display.common import DefaultPass, Display

class EInkDisplay(Display):
  # fontname = 'DejaVuSansMono'
  fontname = 'DejaVuSansMono-Bold'
  main_fontsize = 20
  width_tolerance = 3

  def __init__(self, args):
    self.args = args
    self.epd = None
    self.font = None
    self.pass_font = None
    self.ch = None
    self.cw = None
    self.width = 0
    self.height = 0
    self.pass_fontsize = 15
    self.refresh_interval = 10
    self.temp_fonts = []

  def init(self) -> bool:
    # Get fonts
    try:
      self.font = ImageFont.truetype(self.fontname, self.main_fontsize)
      # pass font size will change depending on password length
      self.pass_font = ImageFont.truetype(self.fontname, self.pass_fontsize)
    except:
      print(f'Failed to load font {self.fontname}')
      sys.exit(3)

    ascent, descent = self.font.getmetrics()
    self.cw = self.font.getlength(" ")
    self.ch = ascent + descent

    try:
      self.epd = epd2in13_V3.EPD()
      self.height = self.epd.width  # rotated
      self.width = self.epd.height  # rotated
      self.epd.init()
    except IOError as e:
      print(f'Error: {e}')
      return False
    except KeyboardInterrupt:
      print('CTRL+C')
      epd2in13_V3.epdconfig.module_exit()
    return True

  def run(self):
    self.epd.init()

    default_pass = DefaultPass()
    host_name, password, ip_str = None, None, None

    display_change_counter = self.refresh_interval

    while True:
      # poll stale by checking if info differs
      new_host_name, new_password, new_ip_str = get_info(self.args, default_pass)

      if new_host_name != host_name or new_password != password or new_ip_str != ip_str:
        # eink is sticky, partial refreshing requires a full refresh every few draws.
        if display_change_counter >= self.refresh_interval:
          self.display_refresh_base()
          display_change_counter = 0

        host_name = new_host_name
        password = new_password
        ip_str = new_ip_str
        self.pass_font = self.pick_pass_font(password, self.width + self.width_tolerance)
        self.update_display(host_name, password, ip_str)

        display_change_counter += 1
      # wait before polling again
      time.sleep(8)

  def display_refresh_base(self):
    try:
      image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
      draw = ImageDraw.Draw(image)

      interval = (5 / 4) * self.ch
      start = interval / 4
      draw.text((0, start + 0 * interval), 'Host: ', font=self.font, fill=0)
      draw.text((0, start + 1 * interval), 'IP:', font=self.font, fill=0)
      draw.text((0, start + 2 * interval), 'Pass\u21b4', font=self.font, fill=0)

      print('Displaying image')
      self.epd.displayPartBaseImage(self.epd.getbuffer(image))

    except IOError as e:
      print(f'Error: {e}')
    except KeyboardInterrupt:
      print('CTRL+C')
      epd2in13_V3.epdconfig.module_exit()

  def update_display(self, host_name, password, ip_str):
    try:
      image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
      draw = ImageDraw.Draw(image)

      interval = (5 / 4) * self.ch
      start = interval / 4
      draw.text((0, start + 0 * interval), f'Host: {host_name}', font=self.font, fill=0)
      draw.text((0, start + 1 * interval), f'IP:   {ip_str}', font=self.font, fill=0)
      draw.text((0, start + 2 * interval), f'Pass\u21b4', font=self.font, fill=0)
      draw.text((0, start + 3 * interval), password, font=self.pass_font, fill=0)

      print('Displaying image')
      self.epd.displayPartial(self.epd.getbuffer(image))

    except IOError as e:
      print(f'Error: {e}')
    except KeyboardInterrupt:
      print('CTRL+C')
      epd2in13_V3.epdconfig.module_exit()

  def pick_pass_font(self, password, max_length) -> ImageFont:
    try:
      for i in range(20, 10, -1):
        f = ImageFont.truetype(self.fontname, i)
        if f.getlength(password) <= max_length:
          return f
    except:
      print(f'Failed to load font {self.fontname}')
      sys.exit(3)
    return ImageFont.truetype(self.fontname, 10)


def get_info(args, default_pass) -> Tuple[str, str, str]:
  password, _ = default_pass.update()
  try:
    host_name = socket.gethostname() + '.local'
  except:
    host_name = 'None'
  try:
    ip_str = ni.ifaddresses(args.iface)[ni.AF_INET][0]['addr']
  except:
    ip_str = 'Disconnected'

  return host_name, password, ip_str


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Display AmpliPi information on a TFT display.',
                                   formatter_class=formatter.AmpliPiHelpFormatter)
  parser.add_argument('-i', '--iface', default='eth0',
                      help='the network interface to display the IP of')
  args = parser.parse_args()
  disp = EInkDisplay(args)
  disp.init()
  disp.run()
