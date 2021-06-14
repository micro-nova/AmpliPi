#!/usr/bin/env python3
# AmpliPi Tester

##############################################################################
# Assumptions
##############################################################################
# It is assumed that the Raspberry Pi Compute Module 3+ has been bootstrapped
# and that Ethernet communication has successed in order for this script to be
# running on the Pi.
# A valid 5V is present and none of the boards in the AmpliPi short that rail.

##############################################################################
# Manual tests
##############################################################################
# Hardware    | Test
#-------------+---------------------------------------------------------------
# USB SLAVE   | Bootstrap Pi through the slave USB
# INT USB     | Plug in a USB flash drive and verify it enumerates
# TOP USB     | Plug in a USB flash drive and verify it enumerates
# BOTTOM USB  | Plug in a USB flash drive and verify it enumerates
# HDMI        | Plug in monitor and verify 1080p@60fps works
# DEBUG-PRE   | Use the SWD port of the preamp
# FANS-AUTO?  | Use a heat gun on the amp board, see if fans come on


##############################################################################
# Semi-Automated tests
##############################################################################
# Hardware    | Test
#-------------+---------------------------------------------------------------
# DISPLAY     | Visually check the display is showing
# DIM-DISP?   | Visually check the display dims and brightens
# TOUCH       | Touch the screen to continue
# PEAK-DETECT | Test nothing connected, connected but no audio, playing
# FANS-ON     | Force fans to 100%, check if on


##############################################################################
# Automated tests
##############################################################################
# Hardware    | Test
#-------------+---------------------------------------------------------------
# CTRL TEMP   | Verify controller-board's PCB temp sensor value is valid
# THERM TEMP  | Verify power-board's thermocouple temp value is valid
# PGOOD-9V    |
# PGood-12V   |

# Check that we're on a Pi and all required interfaces exist
# Program preamp
# Verify comms to preamp
# Check all ADCs
# Check I2S DAC output
# Check all USB DAC outputs

# Questions:
# Is it work testing the 3 serial expansion headers on the control board?

import board
import busio
import RPi.GPIO as GPIO
from typing import List

_PINS = { # BCM (GPIO) numbering
  'PADC_CS'   : 17,
  'PADC_MISO' : 19,
  'PADC_MOSI' : 20,
  'PADC_CLK'  : 21
}

class PeakAdc:
  def __init__(self, baud: int = 1000000):
    # Setup SPI bus using hardware SPI:
    # Baud is in Hz, MCP3008 max is 3.6 MHz, min 10 kHz
    self.cs_pin = _PINS['PADC_CS']
    GPIO.setup(_PINS['PADC_CS'], GPIO.OUT, initial=1)
    self.spi = busio.SPI(
      MISO=_PINS['PADC_MISO'],
      MOSI=_PINS['PADC_MOSI'],
      clock=_PINS['PADC_CLK'])
    while not self.spi.try_lock():
      pass
    self.spi.configure(baudrate=baud)

    self.rx_buf = bytearray(3)
    self.tx_buf = bytearray(3)
    self.tx_buf[0] = 0x01
    self.tx_buf[2] = 0x00

  #channels: List(int) = (1, 2, 3, 4)
  def sample(self):
    vals = []
    for chan in range(8):
      self.tx_buf[1] = 0x80 | (chan << 4)
      GPIO.output(self.cs_pin, 0)
      self.spi.write_readinto(self.tx_buf, self.rx_buf)
      GPIO.output(self.cs_pin, 1)

      vals.append(((self.rx_buf[1] & 0x3) << 8) | self.rx_buf[2])

class AmpliPiTester:
  def __init__(self, hostname: str = 'amplipi.local'):
    self.hostname = hostname

    GPIO.setmode(GPIO.BCM)
    self.padc_baud = 1000000
    self.padc_sample_rate = 2.0   # Hz

  def run_all(self):
    print('running!')

if __name__ == '__main__':
  t = AmpliPiTester()
  t.run_all()
