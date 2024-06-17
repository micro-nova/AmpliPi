#!/usr/bin/env python3
""" EInk display handler """

import math
import json
import datetime
import os

from collections import namedtuple
import sys
import pathlib
from time import sleep
from typing import List, Optional, Union

from PIL import Image, ImageDraw, ImageFont
from loguru import logger as log

from amplipi.display import epd2in13_V3
from amplipi.display.common import DefaultPass, Display, SysInfo, get_info, STARTUP_MSG
from amplipi.display.statusinterface import set_custom_display_status, DisplayStatus


class EInkDisplay(Display):
  """ Display system information on EInk Panel"""

  fontname = 'DejaVuSansMono-Bold'
  main_fontsize = 16
  pass_fontsize = 12
  pass_min_fontsize = 8
  width_tolerance = 3
  REFRESH_DELAY_S = 8

  def __init__(self, iface: str = 'eth0', log_level: str = 'INFO'):
    self.iface = iface
    self.epd: Optional[epd2in13_V3.EPD] = None
    self.font: Optional[ImageFont.FreeTypeFont] = None
    self.pass_font: Optional[ImageFont.FreeTypeFont] = None
    self.char_height: int = 0
    self.char_width: int = 0
    self.width = 0
    self.height = 0
    self.refresh_interval = 10
    self.temp_fonts: List = []
    self._ok = False
    self._log_level = log_level
    self._boot = True
    self._boot_timeout = datetime.datetime.now() + datetime.timedelta(seconds=60)
    self._displayed_boot = False
    self._cached_status: Optional[Union[str, int]] = None
    log.remove()
    log.add(sys.stderr, level=log_level)

  def init(self) -> bool:
    set_custom_display_status(DisplayStatus(STARTUP_MSG, expiration=(
      datetime.datetime.now() + datetime.timedelta(seconds=60))))
    # Get fonts
    try:
      self.font = ImageFont.truetype(self.fontname, self.main_fontsize)
      # pass font size will change depending on password length
      self.pass_font = ImageFont.truetype(self.fontname, self.main_fontsize)
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

  def display_delivery_message(self):
    """Display the delivery message and exit"""
    image = Image.open(f'{pathlib.Path(__file__).parent.resolve()}/imgs/delivery_message.png').convert('1')
    self.epd.display(self.epd.get_buffer(image))

  def display_boot_message(self):
    """Display the boot message"""
    if not self._displayed_boot:
      image = Image.open(f'{pathlib.Path(__file__).parent.resolve()}/imgs/startupscreen.png').convert('1')
      self.epd.display(self.epd.get_buffer(image))
      self._displayed_boot = True

  def run(self):
    self._ok = True
    try:
      default_pass = DefaultPass()
      info = SysInfo(None, None, None, None, None, None)

      display_change_counter = self.refresh_interval

      while self._ok:
        # poll stale by checking if info differs
        new_info = get_info(self.iface, default_pass, self._boot)

        # Ensure start up screen times out when 60 seconds pass
        if self._boot and datetime.datetime.now() > self._boot_timeout:
          self._boot = False
          set_custom_display_status(None)

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
    self.epd.init()
    self.epd.clear(0xFF)

  def display_refresh_base(self):
    """Draw the base image used for partial refresh"""
    self.update_display(draw_base=True)

  def update_display(self, info: SysInfo = SysInfo(None, None, None, None, None, None), draw_base=False):
    """Update display with new info using partial refresh"""
    if not self.epd:
      log.error('Failed to update display, display driver not initialized')
      return
    try:
      image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
      draw = ImageDraw.Draw(image)

      if info.status_code != self._cached_status:
        self._cached_status = info.status_code
        log.info(f'E-Ink Display: Changed Status to {info.status_code}')

      interval = (5 / 4) * self.char_height
      start = interval / 4
      if info.status_code == 0:
        draw.text((0, start + 0 * interval), f'AMPLIPI WEB SERVER DOWN!', font=self.font, fill=0)
      else:
        draw.text((0, start + 0 * interval), f'Host: {info.hostname}', font=self.font, fill=0)
      draw.text((0, start + 1 * interval), f'IP:   {info.ip}', font=self.font, fill=0)

      expander_string = ""

      if info.ext_count is not None and info.ext_count > 0:
        expander_string = "+ " + str(info.ext_count) + " more"

      if info.serial_number == -1:
        draw.text((0, start + 2 * interval), f'SN:   ??? {expander_string}', font=self.font, fill=0)
      else:
        draw.text((0, start + 2 * interval), f'SN:   {info.serial_number} {expander_string}', font=self.font, fill=0)

      if type(info.status_code) is str:
        draw.text((0, start + 3 * interval), f'Status:   {info.status_code}', font=self.font, fill=0)
        if info.status_code != STARTUP_MSG and self._boot:
          self._boot = False
          draw_base = True
      else:
        draw.text((0, start + 3 * interval), f'ERROR! - Code: {info.status_code}', font=self.font, fill=0)

      if info.password:
        draw.text((0, start + 4 * interval), f'Pass: {info.password}', font=self.pass_font, fill=0)

      if self._boot:
        self.display_boot_message()
      elif not draw_base:
        log.debug('Displaying image')
        self.epd.display_partial(self.epd.get_buffer(image))
      else:
        log.debug('Displaying base image')
        self.epd.display_partial_base(self.epd.get_buffer(image))

    except IOError as e:
      log.error(e)

  def pick_pass_font(self, password, max_length) -> ImageFont.FreeTypeFont:
    """Pick the password font so it fits in the display"""
    max_size = self.pass_fontsize
    min_size = math.floor(self.pass_min_fontsize)
    try:
      for i in range(max_size, min_size, -1):
        font = ImageFont.truetype(self.fontname, i)
        if font.getlength("Pass: " + password) <= max_length:
          return font
    except Exception as exc:
      raise Exception(f'Failed to load {self.fontname} font') from exc
    return ImageFont.truetype(self.fontname, 10)
