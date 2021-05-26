#!/usr/bin/env python3
# Show touch positions

import board
import busio
import digitalio
import pwmio
import RPi.GPIO as GPIO
import time

# Display
from adafruit_rgb_display import color565
import adafruit_rgb_display.ili9341 as ili9341
from xpt2046 import Touch
from PIL import Image, ImageDraw

# Configuration for extra TFT pins:
cs_pin = digitalio.DigitalInOut(board.CE0) #board.D43
dc_pin = digitalio.DigitalInOut(board.D25) #board.D39
led_pin = board.D18
rst_pin = None
t_cs_pin = board.D5
t_irq_pin = board.D6

spi_baud = 16 * 10**6 #int(20.0/3 * 10**6) + 1

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK, MOSI=board.MOSI, MISO=board.MISO)

# Create the ILI9341 display:
display = ili9341.ILI9341(spi, cs=cs_pin, dc=dc_pin, rst=rst_pin, baudrate=spi_baud, rotation=270)

# Swap height/width to rotate it to landscape
height = display.width
width = display.height

# Create a blank image for drawing.
image = Image.new('RGB', (width, height)) # Fill entire screen with drawing space
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width-1, height-1), fill=0) # Clear image

# Set backlight brightness out of 65535
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
led.duty_cycle = 32000

# Create the touch controller:
touch_cs = digitalio.DigitalInOut(t_cs_pin)
touch_cs.direction = digitalio.Direction.OUTPUT
touch_cs.value = True

# Start bit=1, A[2:0], 12-bit=0, differential=0, power down when done=00
XPT2046_CMD_X = 0b11010000  # X=101
XPT2046_CMD_Y = 0b10010000  # Y=001
_cal = (300, 400, 3600, 3850) # Top-left and bottom-right coordinates as raw ADC output
_max_dist = 0.05 * ((_cal[3] - _cal[1]) ** 2 + (_cal[2] - _cal[0]) ** 2) ** 0.5
print(f'_max_dist={_max_dist}')
tx_buf = bytearray(5)
rx_buf = bytearray(5)
tx_buf[0] = XPT2046_CMD_X
tx_buf[2] = XPT2046_CMD_Y
def read_xy():
  # Try to access SPI, wait if someone else (i.e. screen) is busy
  while not spi.try_lock():
    pass
  spi.configure(baudrate=int(2.5*10**6))
  touch_cs.value = False
  spi.write_readinto(tx_buf, rx_buf)
  touch_cs.value = True
  spi.configure(baudrate=spi_baud)
  spi.unlock()

  x = (rx_buf[1] << 5) | (rx_buf[2] >> 3)
  y = (rx_buf[3] << 5) | (rx_buf[4] >> 3)
  return (x,y)

def touch_callback(pin_num):
  # Mask the interrupt since reading the position generates a false interrupt
  GPIO.remove_event_detect(t_irq_pin.id)

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
      print(f'x: {x}, y: {y}')
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

      draw.rectangle((0, 0, width-1, height-1), fill=0) # Clear image
      draw.rectangle((x, y, x, y), fill='#FF0000')
      print(f'Touch at {x},{y} [Raw: {x_raw},{y_raw}]')
    else:
      print(f'Not enough inliers: {inlier_count} of 16')
  else:
    print(f'No valid points')

  try:
    GPIO.add_event_detect(t_irq_pin.id, GPIO.FALLING, callback=touch_callback)
  except RuntimeError as e:
    print(e)

# Get touch events
GPIO.setup(t_irq_pin.id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(t_irq_pin.id, GPIO.FALLING, callback=touch_callback)

# Create the XPT2046 touch controller
#def touchscreen_press(x, y):
#    print(f'Touch at ({x},{y})')
#touch_irq = digitalio.DigitalInOut(t_irq_pin)
#xpt = Touch(spi, cs=touch_cs, int_pin=touch_irq, int_handler=touchscreen_press)

while True:
  display.image(image)
  time.sleep(0.5)
