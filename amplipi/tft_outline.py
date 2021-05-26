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


# Configuration for extra TFT pins:
cs_pin = digitalio.DigitalInOut(board.D44) #(board.CE0) #board.D43
dc_pin = digitalio.DigitalInOut(board.D39) #(board.D25) #board.D39
led_pin = board.D12
rst_pin = None
t_cs_pin = board.D5
t_irq_pin = board.D38

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
# spi_baud = 50 * 10**6

spi_baud = 16 * 10**6

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.D42, MOSI=board.D41, MISO=board.D40)

# Create the ILI9341 display:
display = ili9341.ILI9341(spi, cs=cs_pin, dc=dc_pin, rst=rst_pin, baudrate=spi_baud, rotation=270)

# Set backlight brightness out of 65535
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
led.duty_cycle = 65535

# Create a blank image for drawing.
# Swap height/width to rotate it to landscape
height = display.width
width = display.height
image = Image.new('RGB', (width, height)) # Fill entire screen with drawing space
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width-1, height-1), outline='#FF0000')
draw.rectangle((2, 2, width-3, height-3), outline='#00FF00')
draw.rectangle((4, 4, width-5, height-5), outline='#0000FF')
display.image(image)

while True:
  time.sleep(0.1)
