#!/usr/bin/env python3
#
# Requirements:
# pip: adafruit-circuitpython-rgb-display pillow

import time
import busio
import digitalio
import board

from xpt2046 import Touch
import RPi.GPIO as GPIO

from adafruit_rgb_display import color565
import adafruit_rgb_display.ili9341 as ili9341

from PIL import Image

# touch callback
import pwmio

import sys


# Configuration for CS and DC pins:
cs_pin = digitalio.DigitalInOut(board.CE0) #board.D43
dc_pin = digitalio.DigitalInOut(board.D25) #board.D39
rst_pin = None#digitalio.DigitalInOut(board.D22)
led_pin = board.D18

# The ILI9341 specifies a max write rate of 10 MHz,
#   and a max read rate of 6.66 MHz.
# The default with this library is 16 MHz.
# Adafruit's example sets 24 MHz.
# Some random dude on the internet uses 80 MHz.
# 100 MHz fails using breadboard setup
spi_baud = 50 * 10**6
# 16 = 93.9 ms
# 17 = 87.9 ms
# 19 = 81.7 ms
# 20 = 75.6 ms
# 23 = 69.3 ms
# 25 = 63.1 ms
# 29 = 56.9 ms
# 34 = 50.7 ms
# 40 = 44.7 ms
# 50 = 38.6 ms
# 67 = 32.5 ms
# 100 = 26.3 ms DOES NOT WORK

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK, MOSI=board.MOSI, MISO=board.MISO)
#spi = busio.SPI(clock=42, MOSI=41, MISO=40)
#while not spi.try_lock():
#  pass
#try:
#    spi.configure(baudrate=10 * 10**6, phase=0, polarity=0)
#except:
#    print("Error configuring SPI")
#finally:
#    print("SPI configured to 10 MHz")
#    spi.unlock()

# Create the ILI9341 display:
display = ili9341.ILI9341(spi, cs=cs_pin, dc=dc_pin, rst=rst_pin, baudrate=spi_baud)
#print("SPI real freq: ", display.spi_device.spi.frequency)

# Set backlight brightness out of 65535
# Turn off until first image is written
led = pwmio.PWMOut(led_pin, frequency=5000, duty_cycle=0)
led.duty_cycle = 0

start = time.time()
display.fill(0) # Clear the screen
end = time.time()
print("Time to fill(0) = ", (end-start)*1000, "ms")

# Create the touch controller:
touch_cs  = digitalio.DigitalInOut(board.D45)
touch_cs.direction = digitalio.Direction.OUTPUT
touch_cs.value = True

touch_irq = digitalio.DigitalInOut(board.D38)
touch_irq.direction = digitalio.Direction.INPUT


# touch callback
def touch_callback(self):

  GPIO.remove_event_detect(38)

  rx_buf = bytearray(3)  # Receive buffer

  print("Touch event!")
  # try to access SPI, wait if someone else (i.e. screen) is busy
  while not spi.try_lock():
    pass

  spi.configure(baudrate=10000, phase=0, polarity=0)
  touch_cs.value = False

  spi.write(bytes([0b11010000]))

  spi.readinto(rx_buf)
  print("RX = ")
  print(rx_buf)

  touch_cs.value = True
  # free up for other usage
  spi.unlock()

  GPIO.add_event_detect(38,GPIO.RISING,callback=touch_callback)


# Get touch events
#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(38, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.add_event_detect(38,GPIO.RISING,callback=touch_callback)

# Load image and convert to RGB
image = Image.open('micronova-320x240.png').convert('RGB')
display.image(image, 90)

# Turn on display backlight now that an image is loaded
led.duty_cycle = 32000

# Main loop:
while True:
    start = time.time()
    display.image(image, 90)

    # Clear the display
    #display.fill(0)
    # Draw a red pixel in the center.
    #display.pixel(120, 160, color565(255, 0, 0))
    # Pause 2 seconds.
    #time.sleep(.1)
    # Clear the screen blue.
    #display.fill(color565(0, 0, 255))
    display.image(image, 270)
    # Pause 2 seconds.
    #time.sleep(.1)
    #print("display loop")
    end = time.time()
    print("FPS:", 2/(end-start))
