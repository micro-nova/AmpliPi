#!/usr/bin/env python3

import board
import busio
import digitalio
import time

# Config
cs_pin = digitalio.DigitalInOut(board.D17)
baud = 1000000      # MHz, MCP3008 max is 3.6 MHz, min 10 kHz
sample_rate = 1.0   # Hz

################################################################################
# A note on Raspberry Pi (BCM2835) clocks
################################################################################
# The SPI frequency is based on the "core clock" of the BCM2835
# See Section 2.3.1 of BCM2835-ARM-Peripherals.pdf, CLK Register CDIV field:
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

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK_1, MOSI=board.MOSI_1, MISO=board.MISO_1)
while not spi.try_lock():
  pass
spi.configure(baudrate=baud)

sample_period = 1/sample_rate
cs_pin.direction = digitalio.Direction.OUTPUT
cs_pin.value = True
rx_buf = bytearray(3)
tx_buf = bytearray(3)
tx_buf[0] = 0x01
tx_buf[2] = 0x00
while True:
  start = time.time()

  adc_vals = []
  for ch in range(8):
    tx_buf[1] = 0x80 | (ch << 4)
    cs_pin.value = False
    spi.write_readinto(tx_buf, rx_buf)
    cs_pin.value = True

    raw_val = ((rx_buf[1] & 0x3) << 8) | rx_buf[2]
    adc_vals.append(raw_val * 100.0 / 1023.0)
  print(*(f'{val:5.1f}%' for val in adc_vals))

  end = time.time()
  #print('Took ', 1000*(end - start), ' ms')
  sleep_time = sample_period - (end-start)
  if sleep_time > 0:
    time.sleep(sleep_time)
  else:
    print(f'Warning: ADC sampling took {sleep_time}s too long!')
