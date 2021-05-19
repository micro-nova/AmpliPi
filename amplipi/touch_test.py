#!/usr/bin/env python3
# Graph touch positions

import board
import busio
import digitalio
import pwmio
import RPi.GPIO as GPIO
import subprocess
import time
import matplotlib

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

# Set backlight brightness out of 65535
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
led.duty_cycle = 32000

# Create the touch controller:
touch_cs = digitalio.DigitalInOut(t_cs_pin)
touch_cs.direction = digitalio.Direction.OUTPUT
touch_cs.value = True

touch_irq = digitalio.DigitalInOut(t_irq_pin)
touch_irq.direction = digitalio.Direction.INPUT

# touch callback
def touch_callback(pin_num):
  GPIO.remove_event_detect(t_irq_pin.id)

  # try to access SPI, wait if someone else (i.e. screen) is busy
  while not spi.try_lock():
    pass
  spi.configure(baudrate=2*10**6)
  touch_cs.value = False
  spi.write(bytes([0b11011000]))
  x_buf = bytearray(1)
  spi.readinto(x_buf)
  touch_cs.value = True
  time.sleep(0.001)
  touch_cs.value = False
  spi.write(bytes([0b10010000]))
  y_buf = bytearray(2)
  spi.readinto(y_buf)
  touch_cs.value = True
  spi.configure(baudrate=spi_baud)
  spi.unlock()

  # Swap x and y and invert y to account for screen rotation
  y = (x_buf[0] << 1) #(rx_buf[0] << 1) | (rx_buf[1] >> 7)
  x = (y_buf[0] << 1) | (y_buf[0] >> 7)

  if x > 0 and y > 0:
    print(f'Touch at {x},{y}')


  GPIO.add_event_detect(t_irq_pin.id, GPIO.FALLING, callback=touch_callback)

# Get touch events
GPIO.setup(t_irq_pin.id, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(t_irq_pin.id, GPIO.FALLING, callback=touch_callback)

# Create the XPT2046 touch controller
#def touchscreen_press(x, y):
#    print(f'Touch at ({x},{y})')
#xpt = Touch(spi, cs=touch_cs, int_pin=touch_irq, int_handler=touchscreen_press)

# Load image and convert to RGB
logo = Image.open('micronova-320x240.png').convert('RGB')
display.image(logo)

# Create a blank image for drawing.
# Swap height/width to rotate it to landscape
height = display.width
width = display.height
image = Image.new('RGB', (width, height)) # Fill entire screen with drawing space
draw = ImageDraw.Draw(image)

while True:
  #draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0)) # Black background
  time.sleep(0.1)
