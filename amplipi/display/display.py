#!/usr/bin/env python3
#
# Requirements:
# pip: adafruit-circuitpython-rgb-display pillow numpy
#      loguru requests rpi.gpio netifaces psutil
# apt: libatlas-base-dev

import sys
if 'venv' not in sys.prefix:
  print(f"Warning: Did you mean to run {__file__} from amplipi's venv?\n")

# pylint: disable=wrong-import-position
import argparse
import busio
import cProfile
import digitalio
from loguru import logger as log
import requests
import signal
import socket
import time
from typing import Any, Dict, List, Tuple, Optional

import amplipi.models as models

# Display
import adafruit_rgb_display.ili9341 as ili9341
from PIL import Image, ImageDraw, ImageFont

# To retrieve system info
import netifaces as ni    # network interfaces
import psutil             # CPU, RAM, etc.

# Remove duplicate metavars
# https://stackoverflow.com/a/23941599/8055271
class AmpliPiHelpFormatter(argparse.HelpFormatter):
  def _format_action_invocation(self, action):
    if not action.option_strings:
      metavar, = self._metavar_formatter(action, action.dest)(1)
      return metavar
    else:
      parts = []
      if action.nargs == 0:                   # -s, --long
        parts.extend(action.option_strings)
      else:                                   # -s, --long ARGS
        args_string = self._format_args(action, action.dest.upper())
        for option_string in action.option_strings:
          parts.append('%s' % option_string)
        parts[-1] += ' %s' % args_string
      return ', '.join(parts)

  def _get_help_string(self, action):
    help_str = action.help
    if '%(default)' not in action.help:
      if action.default is not argparse.SUPPRESS and action.default is not None:
        defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
        if action.option_strings or action.nargs in defaulting_nargs:
          help_str += ' (default: %(default)s)'
    return help_str

parser = argparse.ArgumentParser(description='Display AmpliPi information on a TFT display.',
                                 formatter_class=AmpliPiHelpFormatter)
parser.add_argument('-u', '--url', default='localhost', help="the AmpliPi's URL to contact")
parser.add_argument('-r', '--update-rate', metavar='HZ', type=float, default=1.0,
                    help="the display's update rate in Hz")
parser.add_argument('-s', '--sleep-time', metavar='S', type=float, default=60.0,
                    help="number of seconds to wait before sleeping, 0=don't sleep")
parser.add_argument('-b', '--brightness', metavar='%', type=float, default=1.0,
                    help='the brightness of the backlight, range=[0.0, 1.0]')
parser.add_argument('-i', '--iface', default='eth0',
                    help='the network interface to display the IP of')
parser.add_argument('-t', '--test-board', action='store_true', default=False,
                    help='use SPI0 and test board pins')
parser.add_argument('-l', '--log', metavar='LEVEL', default='WARNING',
                    help='set logging level as DEBUG, INFO, WARNING, ERROR, or CRITICAL')
parser.add_argument('--test-timeout', metavar='SECS', type=float, default=0.0,
                    help='if >0, perform a hardware test and exit on success or timeout')
args = parser.parse_args()

# Setup logging
log_fmt = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> [<level>{level:8}</level>] [{module}:{function}] <level>{message}</level>'
#{elapsed} is a time option as well
log.configure(handlers=[{'sink': sys.stderr, 'format': log_fmt, 'level': args.log}])

# If this is run on anything other than a Raspberry Pi,
# it won't work. Just quit if not on a Pi.
try:
  import board
  import pwmio
  import RPi.GPIO as gpio
except (NotImplementedError, RuntimeError) as err:
  log.critical(err)
  log.critical('Only Raspberry Pi is currently supported')
  sys.exit(1)

profile = False
_touch_test_passed = False

# Configuration for extra TFT pins:
clk_pin = board.SCLK if args.test_board else board.SCLK_2
mosi_pin = board.MOSI if args.test_board else board.MOSI_2
miso_pin = board.MISO if args.test_board else board.MISO_2

cs_pin = board.CE0 if args.test_board else board.D44
dc_pin = board.D25 if args.test_board else board.D39
led_pin = board.D18 if args.test_board else board.D12
rst_pin = None
t_cs_pin = board.D5 if args.test_board else board.D45
t_irq_pin = board.D6 if args.test_board else board.D38

# Number of screens to scroll through
NUM_SCREENS = 1
_active_screen = 0

################################################################################
# A note on Raspberry Pi (BCM2837B0) clocks
################################################################################
# The SPI frequency is based on the "core clock" of the BCM2837B0
# See Section 2.3.1 of BCM2837B0-ARM-Peripherals.pdf, CLK Register CDIV field:
#   SPIx_CLK = system_clock_freq / [2*(speed_field + 1)]
# Best I can tell 'system_clock_freq' is the same as 'core_freq'
# speed_field is 12 bits, so SPI freq is [core_freq/2^13, core_freq/2]
# For a core_freq of 400 MHz: [48.8 kHz, 200 MHz]
#
# To lock the core clock to 400 MHz, in /boot/config.txt set:
#   core_freq=400
#   core_freq_min=400
#
# Also needed to enable SPI1:
#   dtparam=spi=on
#   dtoverlay=spi1-2cs
#
# ARM (CPU) clock frequency in Hz:  vcgencmd measure_clock arm
# Core clock frequency in Hz:       vcgencmd measure_clock core
#
# Specify the max baud rate here. This will be used to find the 'speed_field'
# such that 400*10^6 / [2*(speed_field + 1)] <= 'spi_baud'
# The ILI9341 specifies a max write rate of 10 MHz, and a max read rate of
# 6.66 MHz but much faster speeds seem to work okay.
spi_baud = 16 * 10**6

# Determine the full URL to contact, and if no specific port was specified
# then use port 5000 as a fallback in case the debug webserver is running.
API_URL = 'http://' + args.url + '/api'
API_URL_DEBUG = None
if ':' not in args.url:
  API_URL_DEBUG = 'http://' + args.url + ':5000/api'

# Convert number range to color gradient (min=green, max=red)
def gradient(num, min_val=0, max_val=100):
  #red = round(255*(val - min_val) / (max_val - min_val))
  #grn = round(255-red)#255*(max_val - val) / (max_val - min_val)
  mid = (min_val + max_val) / 2
  scale = 255 / (mid - min_val)
  if num <= min_val:
    red = 0
    grn = 255
  elif num >= max_val:
    red = 255
    grn = 0
  elif num < mid:
    red = round(scale * (num - min_val))
    grn = 255
  else:
    red = 255
    grn = 255 - round(scale * (num - mid))
  return f'#{red:02X}{grn:02X}00'

def get_amplipi_data(base_url: Optional[str]) -> Tuple[bool, List[models.Source], List[models.Zone]]:
  """ Get the AmpliPi's status via the REST API
      Returns true/false on success/failure, as well as the sources and zones
  """
  _zones: List[models.Zone] = []
  _sources: List[models.Source] = []
  success = False
  if base_url is None:
    return False, _sources, _zones
  try:
    """ TODO: If the AmpliPi server isn't available at this url, there is a
    5-second delay introduced by socket.getaddrinfo """
    req = requests.get(base_url, timeout=0.2)
    if req.status_code == 200:
      status = models.Status(**req.json())
      _zones = status.zones
      _sources = status.sources
      success = True
    else:
      log.error('Bad status code returned from AmpliPi')
  except requests.ConnectionError as err:
    log.debug(err.args[0])
  except requests.Timeout:
    log.error('Timeout requesting AmpliPi status')
  except ValueError:
    log.error('Invalid json in AmpliPi status response')

  return success, _sources, _zones

# Draw volumes on bars.
# Draw is a PIL drawing surface
# zones is a list of (names, volumes) of size [6, 12, 18, 24, 30, 36]
# (x,y) is the top-left of the volume bar area
def draw_volume_bars(draw, font, small_font, zones: List[models.Zone], x=0, y=0, width=320, height=240):
  n = len(zones)
  if n == 0: # No zone info from AmpliPi server
    pass
  elif n <= 6: # Draw horizonal bars
    wb = int(width / 2)                   # Each bar's full width
    hb = 12                               # Each bar's height
    sp = int((height - n*hb) / (2*(n-1))) # Spacing between bars
    xb = width - wb
    vol2pix = wb / -78
    for i in range(n):
      yb = y + i*hb + 2*i*sp # Bar starting y-position

      # Draw zone name as text
      draw.text((x, yb), zones[i].name, font=font, fill='#FFFFFF')

      # Draw background of volume bar
      draw.rectangle(((xb, int(yb+2), xb+wb, int(yb+hb))), fill='#999999')

      # Draw volume bar
      if zones[i].vol > -80:
        color = '#666666' if zones[i].mute else '#0080ff'
        xv = xb + (wb - round(zones[i].vol * vol2pix))
        draw.rectangle(((xb, int(yb+2), xv, int(yb+hb))), fill=color)
  elif n <= 18: # Draw vertical bars
    # Get the pixel height of a character, and add vertical margins
    ch = small_font.getbbox('0', anchor='lt')[3] + 4
    wb = 12                               # Each bar's width
    sp = int((width - n*wb) / (2*(n-1)))  # Spacing between bars
    yt = y + height - ch                  # Text top y-position
    vol2pix = (height - ch) / -78         # dB to pixels conversion factor
    for i in range(n):
      xb = x + i*wb + 2*i*sp # Bar starting x-position

      # Draw zone number as centered text
      draw.text((xb + round(wb/2), y + height - round(ch/2)), str(i+1),
                anchor='mm', font=small_font, fill='#FFFFFF')

      # Draw background of volume bar
      draw.rectangle(((xb, y, xb+wb, yt)), fill='#999999')

      # Draw volume bar
      if zones[i].vol > -80:
        color = '#666666' if zones[i].mute else '#0080ff'
        yv = y + round(zones[i].vol * vol2pix)
        draw.rectangle(((xb, yv, xb+wb, yt)), fill=color)
  else:
    log.error("Can't display more than 18 volumes")


# Pins
disp_cs = digitalio.DigitalInOut(cs_pin)
disp_dc = digitalio.DigitalInOut(dc_pin)
touch_cs = digitalio.DigitalInOut(t_cs_pin)
touch_cs.direction = digitalio.Direction.OUTPUT
touch_cs.value = True

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin, MISO=miso_pin)

# Create the ILI9341 display:
display = ili9341.ILI9341(spi, cs=disp_cs, dc=disp_dc, rst=rst_pin, baudrate=spi_baud, rotation=270)

# Set backlight brightness out of 65535
# Turn off until first image is written to work around not having RST
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
def backlight(on: bool):
  if on:
    led.duty_cycle = int(args.brightness*(2**16-1))
  else:
    led.duty_cycle = 0
backlight(False)

# Start bit=1, A[2:0], 12-bit=0, differential=0, power down when done=00
XPT2046_CMD_X   = 0b11010000  # X=101
XPT2046_CMD_Y   = 0b10010000  # Y=001
XPT2046_CMD_T0  = 0b10000100  # TEMP0=000, measured at 1x current
XPT2046_CMD_T1  = 0b11110100  # TEMP1=111, measured at 91x current
_cal = (300, 400, 3600, 3850) # Top-left and bottom-right coordinates as raw ADC output
_max_dist = 0.05 * ((_cal[3] - _cal[1]) ** 2 + (_cal[2] - _cal[0]) ** 2) ** 0.5

def read_xpt2046(tx_buf: bytearray, rx_buf: bytearray):
  # Try to access SPI, wait if someone else (i.e. screen) is busy
  while not spi.try_lock():
    pass
  spi.configure(baudrate=int(2.5*10**6))
  touch_cs.value = False
  spi.write_readinto(tx_buf, rx_buf)
  touch_cs.value = True
  spi.configure(baudrate=spi_baud)
  spi.unlock()
  return rx_buf

def read_xy():
  tx_buf = bytearray(5)
  rx_buf = bytearray(5)
  tx_buf[0] = XPT2046_CMD_X
  tx_buf[2] = XPT2046_CMD_Y
  rx_buf = read_xpt2046(tx_buf, rx_buf)

  x = (rx_buf[1] << 5) | (rx_buf[2] >> 3)
  y = (rx_buf[3] << 5) | (rx_buf[4] >> 3)
  return (x,y)

def read_temp_raw():
  tx_buf = bytearray(5)
  rx_buf = bytearray(5)
  tx_buf[0] = XPT2046_CMD_T0
  tx_buf[2] = XPT2046_CMD_T1
  rx_buf = read_xpt2046(tx_buf, rx_buf)

  v0 = (rx_buf[1] << 5) | (rx_buf[2] >> 3)
  v1 = (rx_buf[3] << 5) | (rx_buf[4] >> 3)
  return v0, v1

def read_temp():
  #
  # From XPT2046 datasheet:
  # degK = dV*q/[k*ln(N)]
  #   dV = V_t1 - V_t0
  #   q = 1.602189*10^-19 C (electron charge)
  #   k = 1.38054*10^-23 eV/degK (Boltzmann's constant)
  #   N = 91 (the current ratio)
  # Vref = 3.3V (Vdd) with 12-bit ADC
  factor = 2.0728 # q/[k*ln(N)] * 3.3/2^12
  v0, v1 = read_temp_raw()
  t = (v1 - v0) * factor - 273.15
  return t

read_temp_raw() # Dummy read
temp0, temp1 = read_temp_raw()
if temp0 == 0 or temp1 == 0:
  # A touch screen doesn't seem to be present
  # TODO: Read ID from display itself as screen presence detection
  log.critical("Couldn't communicate with touch screen")
  sys.exit(2)


def touch_callback(pin_num):
  # TODO: Debounce touches
  global _active_screen
  global _touch_test_passed
  global _sleep_timer

  # Mask the interrupt since reading the position generates a false interrupt
  gpio.remove_event_detect(t_irq_pin.id)

  # Average 16 values
  x_raw_list = []
  y_raw_list = []
  for i in range(16):
    x, y = read_xy()
    #x_sum += x
    #y_sum += y
    if (x >= _cal[0] and y <= _cal[3]): # Valid touch
      x_raw_list.append(x)
      y_raw_list.append(y)
    #print(f'Read point at x: {x}, y: {y}')
  valid_count = len(x_raw_list)
  if valid_count > 0:
    x_raw_mean = round(sum(x_raw_list) / valid_count)
    y_raw_mean = round(sum(y_raw_list) / valid_count)
    x_raw_keep = []
    y_raw_keep = []
    for i in range(valid_count):
      dist = ((x_raw_list[i] - x_raw_mean) ** 2 + (y_raw_list[i] - y_raw_mean) ** 2) ** 0.5
      if dist < _max_dist:
        x_raw_keep.append(x_raw_list[i])
        y_raw_keep.append(y_raw_list[i])
    inlier_count = len(x_raw_keep)
    if inlier_count >= 4: # At least a quarter of the points were valid and inliers
      x_raw = sorted(x_raw_keep)[inlier_count//2]
      y_raw = sorted(y_raw_keep)[inlier_count//2]

      # Use calibration to scale to the range [0,1]
      x_cal = min(max((float(x_raw) - _cal[0]) / (_cal[2] - _cal[0]), 0), 1)
      y_cal = min(max((float(y_raw) - _cal[1]) / (_cal[3] - _cal[1]), 0), 1)

      # Swap x and y and reverse to account for screen rotation
      y = round(height*(1 - x_cal))
      x = round(width*(1 - y_cal))
      log.debug(f'Touch at {x},{y}')
      _touch_test_passed = True
      #if x > (3*width/4):
      #  _active_screen = (_active_screen + 1) % NUM_SCREENS
      #if x < (width/4):
      #  _active_screen = (_active_screen - 1) % NUM_SCREENS
      _active_screen = 0 # 'Wake up' the screen
      _sleep_timer = time.time()
      # TODO: Redraw screen instantly, don't wait for next display period
    else:
      log.debug(f'Not enough inliers: {inlier_count} of 16')
  else:
    log.debug('No valid points')

  gpio.add_event_detect(t_irq_pin.id, gpio.FALLING, callback=touch_callback)

# Get touch events
gpio.setup(t_irq_pin.id, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.add_event_detect(t_irq_pin.id, gpio.FALLING, callback=touch_callback)

# Clear the screen if this program is exited
# TODO: Create a main() and handle KeyboardInterrupt
run = True
def exit_handler(signum, frame):
  global run
  run = False
  print(f'Received signal {signal.Signals(signum).name}, shutting down')
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

# Load image and convert to RGB
mn_logo = Image.open('amplipi/display/imgs/micronova_320x240.png').convert('RGB')
ap_logo = Image.open('amplipi/display/imgs/amplipi_320x126.png').convert('RGB')
display.image(mn_logo)

# Turn on display backlight now that an image is loaded
# TODO: Anything duty cycle less than 100% causes flickering
backlight(True)

# Get fonts
fontname = 'DejaVuSansMono'
try:
  font = ImageFont.truetype(fontname, 14)
  small_font = ImageFont.truetype(fontname, 10)
except:
  log.critical(f'Failed to load font {fontname}')
  sys.exit(3)

# Create a blank image for drawing.
# Swap height/width to rotate it to landscape
height = display.width
width = display.height
image = Image.new('RGB', (width, height)) # Fill entire screen with drawing space
draw = ImageDraw.Draw(image)

# Keep the splash screen displayed a bit
time.sleep(1.0)

if profile:
  pr = cProfile.Profile()
  pr.enable()

# AmpliPi connection
connected = False
connected_once = False
max_connection_retries = 10
connection_retries = 0
sources: List[models.Source] = []
zones: List[models.Zone] = []

frame_num = 0
frame_times = []
cpu_load = []
use_debug_port = False
disp_start_time = time.time()
_sleep_timer = time.time()
while frame_num < 10 and run:
  frame_start_time = time.time()

  log.debug(f'Active screen = {_active_screen}')
  if _active_screen == 0:
    # Get AmpliPi status
    if use_debug_port:
      primary_url, secondary_url = API_URL_DEBUG, API_URL
    else:
      primary_url, secondary_url = API_URL, API_URL_DEBUG
    primary_success, _sources, _zones = get_amplipi_data(primary_url)
    if primary_success:
      sources = _sources
      zones = _zones
    elif API_URL_DEBUG is not None:
      secondary_success, _sources, _zones = get_amplipi_data(secondary_url)
      if secondary_success:
        sources = _sources
        zones = _zones
        use_debug_port = not use_debug_port
        log.warning(f"Couldn't connect at {primary_url} but got a connection at {secondary_url}, switching over")

    if not primary_success and not secondary_success:
      connection_retries += 1
      if not connected_once:
        if connection_retries == 1:
          log.info(f"Waiting for REST API to start at {primary_url}")
        elif connection_retries == max_connection_retries:
          log.error(f"Couldn't connect to REST API at {primary_url}")
      elif connection_retries < max_connection_retries:
        log.error(f'Failure communicating with REST API at {primary_url}')
      elif connection_retries == max_connection_retries:
        log.error(f'Lost connection to REST API at {primary_url}')

      if connection_retries >= max_connection_retries:
        connected = False
    else:
      if not connected:
        url = primary_url if primary_success else secondary_url
        log.info(f'Connected to REST API at {url}')
      connected = True
      connected_once = True
      connection_retries = 0

    # Get stats
    try:
      ip_str = ni.ifaddresses(args.iface)[ni.AF_INET][0]['addr'] + ', ' + socket.gethostname() + '.local'
    except:
      ip_str = 'Disconnected'

    cpu_pcnt = psutil.cpu_percent()
    cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
    cpu_str1 = f'{cpu_pcnt:4.1f}%'
    cpu_str2 = f'{cpu_temp:4.1f}\xb0C'
    cpu_load.append(cpu_pcnt)

    ram_total = int(psutil.virtual_memory().total / (1024*1024))
    ram_used  = int(psutil.virtual_memory().used / (1024*1024))
    ram_pcnt = 100 * ram_used / ram_total
    ram_str1 = f'{ram_pcnt:4.1f}%'
    ram_str2 = f'{ram_used}/{ram_total} MB'

    disk_usage  = psutil.disk_usage('/')
    disk_pcnt = disk_usage.percent
    disk_used = disk_usage.used / (1024**3)
    disk_total = disk_usage.total / (1024**3)
    disk_str1 = f'{disk_pcnt:4.1f}%'
    disk_str2 = f'{disk_used:.2f}/{disk_total:.2f} GB'

    # Render text
    cw = 8    # Character width
    ch = 16   # Character height
    draw.rectangle((0, 0, width-1, height-1), fill=0) # Clear image
    draw.text((1*cw, 0*ch + 2), 'CPU:',     font=font, fill='#FFFFFF')
    draw.text((1*cw, 1*ch + 2), 'Mem:',     font=font, fill='#FFFFFF')
    draw.text((1*cw, 2*ch + 2), 'Disk:',    font=font, fill='#FFFFFF')
    draw.text((1*cw, 3*ch + 2), 'IP:',      font=font, fill='#FFFFFF')

    draw.text((7*cw, 0*ch + 2), cpu_str1,   font=font, fill=gradient(cpu_pcnt))
    draw.text((7*cw, 1*ch + 2), ram_str1,   font=font, fill=gradient(ram_pcnt))
    draw.text((7*cw, 2*ch + 2), disk_str1,  font=font, fill=gradient(disk_pcnt))
    draw.text((7*cw, 3*ch + 2), ip_str,     font=font, fill='#FFFFFF')

    # BCM2837B0 is rated for [-40, 85] C
    # For now show green for anything below room temp
    draw.text((14*cw, 0*ch + 2), cpu_str2,  font=font, fill=gradient(cpu_temp, min_val=20, max_val=85))
    draw.text((14*cw, 1*ch + 2), ram_str2,  font=font, fill='#FFFFFF')
    draw.text((14*cw, 2*ch + 2), disk_str2, font=font, fill='#FFFFFF')

    if connected:
      # Show source input names
      draw.text((1*cw, int(4.5*ch)), 'Source 1:',font=font, fill='#FFFFFF')
      draw.text((1*cw, int(5.5*ch)), 'Source 2:',font=font, fill='#FFFFFF')
      draw.text((1*cw, int(6.5*ch)), 'Source 3:',font=font, fill='#FFFFFF')
      draw.text((1*cw, int(7.5*ch)), 'Source 4:',font=font, fill='#FFFFFF')
      xs = 11*cw
      xp = xs - round(0.5*cw) # Shift playing arrow back a bit
      ys = 4*ch + round(0.5*ch)
      draw.line(((cw, ys-3), (width-2*cw, ys-3)), width=2, fill='#999999')
      for i, src in enumerate(sources):
        sinfo = sources[i].info
        if sinfo is not None:
          if sinfo.state == 'playing':
            draw.polygon([(xp, ys + i*ch + 3), (xp + cw-3, ys + round((i+0.5)*ch)), (xp, ys + (i+1)*ch - 3)], fill='#28a745')
          draw.text((xs + 1*cw, ys + i*ch), sinfo.name, font=font, fill='#F0E68C')
      draw.line(((cw, ys+4*ch+2), (width-2*cw, ys+4*ch+2)), width=2, fill='#999999')

      # Show volumes
      # TODO: only update volume bars if a volume changed
      draw_volume_bars(draw, font, small_font, zones, x=cw, y=9*ch-2, height=height-9*ch, width=width - 2*cw)
    else:
      # Show an error message on the display, and the AmpliPi logo below
      if not connected_once and connection_retries <= max_connection_retries:
        msg = 'Connecting to the REST API' + '.'*connection_retries
        text_c = '#FFFFFF'
      else:
        msg = 'Cannot connect to the REST API at\n' + API_URL
        text_c = '#FF0000'
      text_y = (height - ap_logo.size[1] - 4*ch)//2 + 4*ch
      draw.text((width/2 - 1, text_y), msg, anchor='mm', align='center', font=font, fill=text_c)
      image.paste(ap_logo, box=(0, height - ap_logo.size[1]))

    if time.time() - _sleep_timer > args.sleep_time:
      # Transition to sleep mode, clear screen
      log.debug('Clearing screen then sleeping')
      backlight(False)
      draw.rectangle((0, 0, width-1, height-1), fill='#000000')
      display.image(image)
      _active_screen = 1
    else:
      # Send the updated image to the display
      display.image(image)
      backlight(True)
  elif _active_screen == 1:
    # Sleeping, wait for touch to wake up
    log.debug('Sleeping...')


  end = time.time()
  frame_times.append(end - frame_start_time)
  #print(f'frame time: {sum(frame_times)/len(frame_times):.3f}s, {sum(cpu_load)/len(cpu_load):.1f}%')
  sleep_time = 1/args.update_rate - (end - frame_start_time)
  if sleep_time > 0:
    time.sleep(sleep_time)
  else:
    log.warning('Frame took too long')

  if profile:
    frame_num = frame_num + 1

  # If the test timeout is 0, ignore testing
  if args.test_timeout > 0.0:
    if _touch_test_passed or (time.time() - disp_start_time) > args.test_timeout:
      run = False

if profile:
  pr.disable()
  pr.print_stats(sort='time')

# Stop handling touch events
gpio.remove_event_detect(t_irq_pin.id)

# Clear display on exit
display.image(Image.new('RGB', (width, height)))
backlight(False)

if args.test_timeout > 0.0 and not _touch_test_passed:
  sys.exit(2) # Exit with an error code >0 to indicate test failure
