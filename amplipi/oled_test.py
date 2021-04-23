#!/usr/bin/env python3

# Dependencies:
# apt: python3-pip python3-venv python3-pil
# pip: netifaces psutil uptime Pillow luma.oled
#
# raspi-config: Enable SPI interface
#
# Not sure if necessary...
# sudo usermod -aG spi,gpio pi
#
# For fonts:
# Place AndaleMono.ttf in ~/.fonts? Python can't find there but system can...
# apt: fontconfig
# * fc-list lists available fonts

from oled import AmpliPi_OLED
import time

oled = AmpliPi_OLED(mock=True)

i = 0

# demo
while(oled.running):
  # increment
  i = i + 2
  # rollover
  if(i >= 100):
    i = 0
  # set volume bars
  oled.set_volumes([i,i,i,i,i,i])
  # sleep
  time.sleep(1)
