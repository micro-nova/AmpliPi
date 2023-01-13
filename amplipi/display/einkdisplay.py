#!/usr/bin/env python3
import argparse
import sys
import time

from amplipi import formatter
from amplipi.display import epd2in13_V3
import socket
import netifaces as ni
from PIL import Image, ImageDraw, ImageFont

from amplipi.display.common import DefaultPass, Display

class EInkDisplay(Display):
  # fontname = 'DejaVuSansMono'
  fontname = 'DejaVuSansMono-Bold'
  fontsize = 20

  def __init__(self, args):
    self.args = args
    self.epd = None
    self.font = None
    self.ch = None
    self.cw = None

  def init(self) -> bool:
    # Get fonts
    try:
      self.font = ImageFont.truetype(self.fontname, self.fontsize)
    except:
      print(f'Failed to load font {self.fontname}')
      sys.exit(3)

    ascent, descent = self.font.getmetrics()
    self.cw = self.font.getlength(" ")
    self.ch = ascent + descent
    print(f'Font height = {self.ch}, width = {self.cw}')

    try:
      self.epd = epd2in13_V3.EPD()
      height = self.epd.width  # rotated
      width = self.epd.height  # rotated
      print(f'Screen height = {height}, width = {width}')
      self.epd.init()
    except IOError as e:
      print(f'Error: {e}')
      return False
    except KeyboardInterrupt:
      print('CTRL+C')
      epd2in13_V3.epdconfig.module_exit()
    return True

  def run(self):
    default_pass = DefaultPass()
    host_name, password, ip_str = None, None, None

    while True:
      # poll stale by checking if info differs
      new_host_name, new_password, new_ip_str = get_info(self.args, default_pass)

      if new_host_name != host_name or new_password != password or new_ip_str != ip_str:
        host_name = new_host_name
        password = new_password
        ip_str = new_ip_str
        self.update_display(host_name, password, ip_str)

      # wait before polling again
      time.sleep(8)

  def update_display(self, host_name, password, ip_str):
    print('update_display')

    try:
      self.epd.Clear(0xFF)
      image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
      draw = ImageDraw.Draw(image)

      interval = (4 / 3) * self.ch
      start = interval / 2
      draw.text((0, start + 0 * interval), f'Host: {host_name}', font=self.font, fill=0)
      draw.text((0, start + 1 * interval), f'Pass: {password}', font=self.font, fill=0)
      draw.text((0, start + 2 * interval), f'IP:   {ip_str}', font=self.font, fill=0)

      image = image.rotate(180)  # flip
      print('displaying image')
      self.epd.display(self.epd.getbuffer(image))
      self.epd.sleep()  # TODO: what does sleep do?
    except IOError as e:
      print(f'Error: {e}')
    except KeyboardInterrupt:
      print('CTRL+C')
      epd2in13_V3.epdconfig.module_exit()

def get_info(args, default_pass):
  password, _ = default_pass.update()
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


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Display AmpliPi information on a TFT display.',
                                   formatter_class=formatter.AmpliPiHelpFormatter)
  parser.add_argument('-i', '--iface', default='eth0',
                      help='the network interface to display the IP of')
  args = parser.parse_args()
  disp = EInkDisplay(args)
  disp.init()
  disp.run()



