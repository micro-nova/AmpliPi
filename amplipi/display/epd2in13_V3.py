"""Waveshare Eink Display Driver for the 2in13_V3

originally developed by the Waveshare team
"""

# *****************************************************************************
# * | File    :	  epd2in13_V3.py
# * | Author    :   Waveshare team
# * | Function  :   Electronic paper driver
# * | Info    :
# *----------------
# * | This version:   V1.2
# * | Date    :   2022-08-9
# # | Info    :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import sys
from time import sleep
from loguru import logger as log

try:
  from spidev import SpiDev
  from RPi import GPIO
except ImportError:
  pass

# Display resolution
EPD_WIDTH  = 122
EPD_HEIGHT = 250

class RaspberryPi:
  """Raspberry Pi driver for display, modfied for AmpliPi and readability"""
  RST_PIN = 12
  DC_PIN = 39
  CS_PIN = 44
  BUSY_PIN = 38

  def __init__(self):
    self._initialized = False
    self.spi = SpiDev()

  def __del__(self):
    if self._initialized:
      self.module_exit()

  def digital_write(self, pin, value):
    GPIO.output(pin, value)

  def digital_read(self, pin):
    return GPIO.input(pin)

  def delay_ms(self, delaytime):
    sleep(delaytime / 1000.0)

  def spi_writebyte(self, data):
    self.spi.writebytes(data)

  def spi_writebyte2(self, data):
    self.spi.writebytes2(data)

  def module_init(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(self.RST_PIN, GPIO.OUT)
    GPIO.setup(self.DC_PIN, GPIO.OUT)
    GPIO.setup(self.CS_PIN, GPIO.OUT)
    GPIO.setup(self.BUSY_PIN, GPIO.IN)
    self.spi.open(2, 1)
    self.spi.max_speed_hz = 4000000
    self.spi.mode = 0b00
    self._initialized = True

  def module_exit(self):
    log.debug("spi end")
    self.spi.close()

    log.debug("close 5V, Module enters 0 power consumption ...")
    GPIO.output(self.RST_PIN, 0)
    GPIO.output(self.DC_PIN, 0)

    GPIO.cleanup([self.RST_PIN, self.DC_PIN, self.CS_PIN, self.BUSY_PIN])

class EPD:
  """Electronic paper driver"""

  PARTIAL_UPDATE = [
    0x0,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x14,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
    0x22,0x17,0x41,0x00,0x32,0x36,
  ]

  FULL_UPDATE = [
    0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0xF,0x0,0x0,0x0,0x0,0x0,0x0,
    0xF,0x0,0x0,0xF,0x0,0x0,0x2,
    0xF,0x0,0x0,0x0,0x0,0x0,0x0,
    0x1,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x0,0x0,0x0,0x0,0x0,0x0,0x0,
    0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
    0x22,0x17,0x41,0x0,0x32,0x36,
  ]

  def __init__(self, log_level='WARNING'):
    log.remove()
    log.add(sys.stderr, level=log_level)
    self.driver = RaspberryPi()
    self.reset_pin = self.driver.RST_PIN
    self.dc_pin = self.driver.DC_PIN
    self.cs_pin = self.driver.CS_PIN
    self.busy_pin = self.driver.BUSY_PIN

    self.width = EPD_WIDTH
    self.height = EPD_HEIGHT

  def reset(self):
    """Reset display hardware"""
    self.driver.digital_write(self.reset_pin, 1)
    self.driver.delay_ms(20)
    self.driver.digital_write(self.reset_pin, 0)
    self.driver.delay_ms(2)
    self.driver.digital_write(self.reset_pin, 1)
    self.driver.delay_ms(20)

  def send_command(self, command):
    """Send simple command"""
    self.driver.digital_write(self.dc_pin, 0)
    self.driver.digital_write(self.cs_pin, 0)
    self.driver.spi_writebyte([command])
    self.driver.digital_write(self.cs_pin, 1)

  def send_data(self, data):
    """Write data to display"""
    self.driver.digital_write(self.dc_pin, 1)
    self.driver.digital_write(self.cs_pin, 0)
    self.driver.spi_writebyte([data])
    self.driver.digital_write(self.cs_pin, 1)

  # send a lot of data
  def send_data2(self, data):
    """Write lots of data to display

    Buffered and more efficient than send_data.
    Use this to write full images to the display."""
    self.driver.digital_write(self.dc_pin, 1)
    self.driver.digital_write(self.cs_pin, 0)
    self.driver.spi_writebyte2(data)
    self.driver.digital_write(self.cs_pin, 1)

  def _is_bus_busy(self):
    return self.driver.digital_read(self.busy_pin) == 1

  def wait_done(self):
    """Wait until the busy_pin goes LOW"""
    if self._is_bus_busy():
      log.debug("e-Paper busy")
      while self._is_bus_busy():
        self.driver.delay_ms(10)
      log.debug("e-Paper busy release")

  def enable_display(self):
    """Turn on display"""
    self.send_command(0x22) # Display Update Control
    self.send_data(0xC7)
    self.send_command(0x20) # Activate Display Update Sequence
    self.wait_done()

  def enable_partial_display(self):
    """Turn on display, partial"""
    self.send_command(0x22) # Display Update Control
    self.send_data(0x0f)  # fast:0x0c, quality:0x0f, 0xcf
    self.send_command(0x20) # Activate Display Update Sequence
    self.wait_done()

  def set_lut(self, lut):
    """Send lut data and configuration"""
    self.send_command(0x32)
    for i in range(0, 153):
      self.send_data(lut[i])
    self.wait_done()
    self.send_command(0x3f)
    self.send_data(lut[153])
    self.send_command(0x03)   # gate voltage
    self.send_data(lut[154])
    self.send_command(0x04)   # source voltage
    self.send_data(lut[155])  # VSH
    self.send_data(lut[156])  # VSH2
    self.send_data(lut[157])  # VSL
    self.send_command(0x2c)   # VCOM
    self.send_data(lut[158])

  def set_window(self, x_start, y_start, x_end, y_end):
    """Configure the display window"""
    self.send_command(0x44) # SET_RAM_X_ADDRESS_START_END_POSITION
    # x point must be the multiple of 8 or the last 3 bits will be ignored
    self.send_data((x_start>>3) & 0xFF)
    self.send_data((x_end>>3) & 0xFF)

    self.send_command(0x45) # SET_RAM_Y_ADDRESS_START_END_POSITION
    self.send_data(y_start & 0xFF)
    self.send_data((y_start >> 8) & 0xFF)
    self.send_data(y_end & 0xFF)
    self.send_data((y_end >> 8) & 0xFF)

  def set_cursor(self, x, y):
    """ Set cursor position in x and y"""
    self.send_command(0x4E) # SET_RAM_X_ADDRESS_COUNTER
    # x point must be the multiple of 8 or the last 3 bits will be ignored
    self.send_data(x & 0xFF)

    self.send_command(0x4F) # SET_RAM_Y_ADDRESS_COUNTER
    self.send_data(y & 0xFF)
    self.send_data((y >> 8) & 0xFF)

  def init(self):
    """ Initialize e-Paper's registers"""
    if self.driver.module_init() != 0:
      return -1
    # EPD hardware init start
    self.reset()

    self.wait_done()
    self.send_command(0x12)  #SWRESET
    self.wait_done()

    self.send_command(0x01) #Driver output control
    self.send_data(0xf9)
    self.send_data(0x00)
    self.send_data(0x00)

    self.send_command(0x11) #data entry mode
    self.send_data(0x03)

    self.set_window(0, 0, self.width-1, self.height-1)
    self.set_cursor(0, 0)

    self.send_command(0x3c)
    self.send_data(0x05)

    self.send_command(0x21) #  Display update control
    self.send_data(0x00)
    self.send_data(0x80)

    self.send_command(0x18)
    self.send_data(0x80)

    self.wait_done()

    self.set_lut(self.FULL_UPDATE)
    return 0

  def get_buffer(self, image):
    """ Get display buffer"""
    img = image
    imwidth, imheight = img.size
    if imwidth == self.width and imheight == self.height:
      img = img.convert('1')
    elif imwidth == self.height and imheight == self.width:
      # image has correct dimensions, but needs to be rotated
      img = img.rotate(90, expand=True).convert('1')
    else:
      log.warning(f"Wrong image dimensions: must be {self.width}x{self.height}")
      # return a blank buffer
      return [0x00] * (int(self.width/8) * self.height)

    buf = bytearray(img.tobytes('raw'))
    return buf

  def display(self, image):
    """Send image buffer in RAM to e-Paper and displays"""
    if self.width%8 == 0:
      linewidth = int(self.width/8)
    else:
      linewidth = int(self.width/8) + 1

    self.send_command(0x24)
    for j in range(0, self.height):
      for i in range(0, linewidth):
        self.send_data(image[i + j * linewidth])
    self.enable_display()

  def display_partial(self, image):
    """Send image buffer in RAM to e-Paper and perform partial refresh"""
    self.driver.digital_write(self.reset_pin, 0)
    self.driver.delay_ms(1)
    self.driver.digital_write(self.reset_pin, 1)

    self.set_lut(self.PARTIAL_UPDATE)
    self.send_command(0x37)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x40)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x00)
    self.send_data(0x00)

    self.send_command(0x3C) #BorderWavefrom
    self.send_data(0x80)

    self.send_command(0x22)
    self.send_data(0xC0)
    self.send_command(0x20)
    self.wait_done()

    self.set_window(0, 0, self.width - 1, self.height - 1)
    self.set_cursor(0, 0)

    self.send_command(0x24) # WRITE_RAM
    # for j in range(0, self.height):
    #   for i in range(0, linewidth):
    #     self.send_data(image[i + j * linewidth])
    self.send_data2(image)
    self.enable_partial_display()

  def display_partial_base(self, base_image):
    """Refresh the base image with @image

    Base image is the common portion of image that is not being refreshed
    """
    self.send_command(0x24)
    self.send_data2(base_image)

    self.send_command(0x26)
    self.send_data2(base_image)
    self.enable_display()

  def clear(self, color):
    """Clear screen"""
    if self.width%8 == 0:
      linewidth = int(self.width/8)
    else:
      linewidth = int(self.width/8) + 1

    self.send_command(0x24)
    self.send_data2([color] * int(self.height * linewidth))
    self.enable_display()

  def sleep(self):
    """ Enter deep sleep mode """
    self.send_command(0x10) #enter deep sleep
    self.send_data(0x01)

    self.driver.delay_ms(2000)
    self.driver.module_exit()
