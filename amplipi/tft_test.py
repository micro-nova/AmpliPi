#!/usr/bin/env python3
#
# Requirements:
# pip: adafruit-circuitpython-rgb-display pillow numpy
# apt: libatlas-base-dev
#
# TODO:
# Clear screen on exit/failure or provide some other indication that the
#   display is still being updated.
# Why is touch always reading 0x000000

import board
import busio
import cProfile
import digitalio
import pwmio
import RPi.GPIO as GPIO
import random
import socket
import subprocess
import time

# Display
from adafruit_rgb_display import color565
import adafruit_rgb_display.ili9341 as ili9341
from xpt2046 import Touch
from PIL import Image, ImageDraw, ImageFont

# To retrieve system info
import netifaces as ni    # network interfaces
import psutil             # CPU, RAM, etc.


profile = False
update_period = 0.5       # Display update rate in seconds

# Configuration for extra TFT pins:
cs_pin = digitalio.DigitalInOut(board.CE0) #board.D43
dc_pin = digitalio.DigitalInOut(board.D25) #board.D39
led_pin = board.D18
rst_pin = None
t_cs_pin = board.D5
t_irq_pin = board.D6

# Network interface name to get IP address of
iface_name = "eth0"

# The ILI9341 specifies a max write rate of 10 MHz,
#   and a max read rate of 6.66 MHz.
# It appears the Pi's base SPI clock is 200 MHz
#   and can be divided by any integer below:
# Div  ~MHz  fill(0) time
# 13   15.4  93.9 ms Default is 16 MHz
# 12   16.7  87.9 ms
# 11   18.2  81.7 ms
# 10   20.0  75.6 ms
#  9   22.2  69.3 ms Adafruit's example sets 24 MHz
#  8   25.0  63.1 ms
#  7   28.6  56.9 ms
#  6   33.3  50.7 ms
#  5   40.0  44.7 ms
#  4   50.0  38.6 ms
#  3   66.7  32.5 ms
#  2  100.0  26.3 ms Fails on breadboard setup
spi_baud = 50 * 10**6

# Dummy info until AmpliPi integration
sources = ('Michael\'s AmpliPi Spotify', 'Matt and Kim Radio', 'test', '123456789 123456789 123456789 1234567890')
random.seed(0)
volumes = [random.randint(-79,0) for i in range(36)]
volumes[0] = 0
volumes[-1] = -79
volumes[4] = -40
volumes[5] = -40

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


# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK, MOSI=board.MOSI, MISO=board.MISO)

# Create the ILI9341 display:
display = ili9341.ILI9341(spi, cs=cs_pin, dc=dc_pin, rst=rst_pin, baudrate=spi_baud, rotation=270)

# Set backlight brightness out of 65535
# Turn off until first image is written to work around not having RST
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
led.duty_cycle = 0


# Create the touch controller:
touch_cs = digitalio.DigitalInOut(t_cs_pin)
touch_cs.direction = digitalio.Direction.OUTPUT
touch_cs.value = True

touch_irq = digitalio.DigitalInOut(t_irq_pin)
touch_irq.direction = digitalio.Direction.INPUT

# touch callback
def touch_callback(pin_num):
  GPIO.remove_event_detect(t_irq_pin.id)

  print('Touch event!')

  # try to access SPI, wait if someone else (i.e. screen) is busy
  while not spi.try_lock():
    pass
  spi.configure(baudrate=5000)
  touch_cs.value = False
  spi.write(bytes([0b11010000]))
  rx_buf = bytearray(3)
  spi.readinto(rx_buf)
  touch_cs.value = True
  spi.configure(baudrate=spi_baud)
  spi.unlock()

  print('RX = ', rx_buf)

  GPIO.add_event_detect(t_irq_pin.id, GPIO.RISING, callback=touch_callback)

# Get touch events
GPIO.setup(t_irq_pin.id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(t_irq_pin.id, GPIO.RISING, callback=touch_callback)

# Load image and convert to RGB
logo = Image.open('micronova-320x240.png').convert('RGB')
display.image(logo)

# Turn on display backlight now that an image is loaded
led.duty_cycle = 32000

# Get fonts
fontname = 'DejaVuSansMono'
try:
  font = ImageFont.truetype(fontname, 14)
except:
  print('Failed to load font')

# Create a blank image for drawing.
# Swap height/width to rotate it to landscape
# TODO: Reduce size if possible to save CPU time
height = display.width
width = display.height
image = Image.new('RGB', (width, height)) # Fill entire screen with drawing space
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0)) # Black background

if profile:
  pr = cProfile.Profile()
  pr.enable()

frame_num = 0
frame_times = []
cpu_load = []
while frame_num < 10:
  start = time.time()

  # Get stats
  try:
    ip_str = ni.ifaddresses(iface_name)[ni.AF_INET][0]['addr'] + ', ' + socket.gethostname() + '.local'
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
  draw.rectangle((0, 0, width, height), fill=0) # Clear image
  draw.text((0*cw, 0*ch), 'IP:',      font=font, fill='#FFFFFF')
  draw.text((0*cw, 1*ch), 'CPU:',     font=font, fill='#FFFFFF')
  draw.text((0*cw, 2*ch), 'Mem:',     font=font, fill='#FFFFFF')
  draw.text((0*cw, 3*ch), 'Disk:',    font=font, fill='#FFFFFF')

  draw.text((6*cw, 0*ch), ip_str,     font=font, fill='#FFFFFF')
  draw.text((6*cw, 1*ch), cpu_str1,   font=font, fill=gradient(cpu_pcnt))
  draw.text((6*cw, 2*ch), ram_str1,   font=font, fill=gradient(ram_pcnt))
  draw.text((6*cw, 3*ch), disk_str1,  font=font, fill=gradient(disk_pcnt))

  # BCM2837 is rated for [-40, 85] C
  # For now show green for anything below room temp
  draw.text((13*cw, 1*ch), cpu_str2,  font=font, fill=gradient(cpu_temp, min_val=20, max_val=85))
  draw.text((13*cw, 2*ch), ram_str2,  font=font, fill='#FFFFFF')
  draw.text((13*cw, 3*ch), disk_str2, font=font, fill='#FFFFFF')

  # Show source input names
  draw.text((0*cw, 4*ch), 'Source inputs:', font=font, fill='#FFFFFF')
  draw.line(((0, 5*ch), (width-1, 5*ch)), fill='#FFFFFF')
  draw.text((0*cw, 5*ch), sources[0], font=font, fill='#F0E68C')
  draw.text((0*cw, 6*ch), sources[1], font=font, fill='#F0E68C')
  draw.text((0*cw, 7*ch), sources[2], font=font, fill='#F0E68C')
  draw.text((0*cw, 8*ch), sources[3], font=font, fill='#F0E68C')

  # Volume bars: center line
  # Spacing: 7 pixels per bar, 36 bars max = 252 pixels.
  #          1 pixel between each bar (within groups of 6) = 30 pixels
  #          6 pixels between each group of 6 = 30 pixels.
  #          4 extra pixels on both sides = 8 pixels.
  #
  # First bar = 4+3-1 = 6
  bar_h = 80  # Height of the volume bars
  #bar_y = height - bar_h
  for i in range(36):
    x = 6 + 8*i + 5*int(i/6)
    draw.line(((x, height-1), (x, height-bar_h)), fill='#999999')
    draw.line(((x-3, height-bar_h-volumes[i]), (x+3, height-bar_h-volumes[i])), fill='#0096ff')

  # Send the updated image to the display
  display.image(image)
  end = time.time()
  frame_times.append(end - start)
  #print(f'frame time: {sum(frame_times)/len(frame_times):.3f}s, {sum(cpu_load)/len(cpu_load):.1f}%')
  sleep_time = update_period - (end-start)
  if sleep_time > 0:
    time.sleep(sleep_time)
  else:
    print('Warning: frame took too long')

  if profile:
    frame_num = frame_num + 1

if profile:
  pr.disable()
  pr.print_stats(sort='time')
