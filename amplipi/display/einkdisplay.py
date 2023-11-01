#!/usr/bin/env python3
""" EInk display handler """


from collections import namedtuple
import sys
from time import sleep
from typing import List, Optional

import socket
import netifaces as ni
from PIL import Image, ImageDraw, ImageFont
from loguru import logger as log

from amplipi.display import epd2in13_V3
from amplipi.display.common import DefaultPass, Display

SysInfo = namedtuple('SysInfo', ['hostname', 'password', 'ip'])

class EInkDisplay(Display):
  """ Display system infomation on EInk Panel"""

  fontname = 'DejaVuSansMono-Bold'
  main_fontsize = 20
  width_tolerance = 3
  REFRESH_DELAY_S = 8

  def __init__(self, iface: str = 'eth0', log_level: str = 'WARNING'):
    self.iface = iface
    self.epd : Optional[epd2in13_V3.EPD] = None
    self.font : Optional[ImageFont.FreeTypeFont] = None
    self.pass_font : Optional[ImageFont.FreeTypeFont] = None
    self.char_height : int = 0
    self.char_width : int = 0
    self.width = 0
    self.height = 0
    self.pass_fontsize = 15
    self.refresh_interval = 10
    self.temp_fonts: List = []
    self._ok = False
    self._log_level = log_level
    log.remove()
    log.add(sys.stderr, level=log_level)

  def init(self) -> bool:
    # Get fonts
    try:
      self.font = ImageFont.truetype(self.fontname, self.main_fontsize)
      # pass font size will change depending on password length
      self.pass_font = ImageFont.truetype(self.fontname, self.pass_fontsize)
    except:
      log.error(f'Failed to load {self.fontname} font')

    if self.font is None or self.pass_font is None:
      return False

    ascent, descent = self.font.getmetrics()
    self.char_width = self.font.getlength(" ")
    self.char_height = ascent + descent

    try:
      self.epd = epd2in13_V3.EPD(self._log_level)
      self.height = self.epd.width  # rotated
      self.width = self.epd.height  # rotated
      self.epd.init()
    except IOError as e:
      log.error(f'Failed to load driver: {e}')
      return False
    return True

  def run(self):
    self._ok = True
    try:
      default_pass = DefaultPass()
      info = SysInfo(None, None, None)

      display_change_counter = self.refresh_interval

      while self._ok:
        # poll stale by checking if info differs
        new_info = get_info(self.iface, default_pass)

        if new_info != info:
          info = new_info

          # eink is sticky, partial refreshing requires a full refresh every few draws.
          if display_change_counter >= self.refresh_interval:
            self.display_refresh_base()
            display_change_counter = 0

          self.pass_font = self.pick_pass_font(info.password, self.width + self.width_tolerance)
          self.update_display(info)

          display_change_counter += 1
        # wait before polling again, checking if we got stopped
        for _ in range(self.REFRESH_DELAY_S * 10):
          if not self._ok:
            break
          sleep(0.1)
    except KeyboardInterrupt:
      self._ok = False
      log.debug('Stopped')
    except Exception as e:
      self._ok = False
      log.error(f'Stopped, {e}')

  def stop(self):
    self._ok = False

  def display_refresh_base(self):
    """Draw the base image used for partial refresh"""
    self.update_display(draw_base=True)

  def update_display(self, info: SysInfo=SysInfo(None, None, None), draw_base=False):
    """Update display with new info using partial refresh"""
    if not self.epd:
      log.error('Failed to update display, display driver not initialized')
      return
    try:
      image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
      draw = ImageDraw.Draw(image)

      interval = (5 / 4) * self.char_height
      start = interval / 4
      draw.text((0, start + 0 * interval), f'Host: {info.hostname}', font=self.font, fill=0)
      draw.text((0, start + 1 * interval), f'IP:   {info.ip}', font=self.font, fill=0)
      draw.text((0, start + 2 * interval), 'Pass\u21b4', font=self.font, fill=0)
      if info.password:
        draw.text((0, start + 3 * interval), info.password, font=self.pass_font, fill=0)

      if not draw_base:
        log.debug('Displaying image')
        self.epd.display_partial(self.epd.get_buffer(image))
      else:
        log.debug('Displaying base image')
        self.epd.display_partial_base(self.epd.get_buffer(image))

    except IOError as e:
      log.error(e)

  def pick_pass_font(self, password, max_length) -> ImageFont.FreeTypeFont:
    """Pick the password font so it fits in the display"""
    try:
      for i in range(20, 10, -1):
        font = ImageFont.truetype(self.fontname, i)
        if font.getlength(password) <= max_length:
          return font
    except Exception as exc:
      raise Exception(f'Failed to load {self.fontname} font') from exc
    return ImageFont.truetype(self.fontname, 10)


def get_info(iface, default_pass) -> SysInfo:
  """Get amplipi system info to display"""
  password, _ = default_pass.update()
  try:
    hostname = socket.gethostname() + '.local'
  except:
    hostname = 'None'
  try:
    ip_str = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
  except:
    ip_str = 'Disconnected'

  return SysInfo(hostname, password, ip_str)
