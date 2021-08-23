#!/usr/bin/env python3

import board
import busio
from pathlib import Path
import time

# Config
cs_pin = 17           # GPIO pin number
baud = 1000000        # MHz, MCP3008 max is 3.6 MHz, min 10 kHz
sample_rate = 100.0   # Hz, rate at which to sample all channels

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK_1, MOSI=board.MOSI_1, MISO=board.MISO_1)
while not spi.try_lock():
  pass
spi.configure(baudrate=baud)

# CS pin setup - TODO: This is still kinda slow, investigate Python's 'spidev'
# library or https://iosoft.blog/2020/06/11/fast-data-capture-raspberry-pi/
if not Path('/sys/class/gpio/gpio17').exists():
  with open('/sys/class/gpio/export', 'w') as f:
    f.write(f'{cs_pin}')
  time.sleep(0.1)
  with open('/sys/class/gpio/gpio17/direction', 'w') as f:
    f.write('out')

with open(f'/sys/class/gpio/gpio{cs_pin}/value', 'w') as cs_file:
  cs_file.write('1')
sample_period = 1/sample_rate
rx_buf = bytearray(3)
tx_buf = bytearray(3)
tx_buf[0] = 0x01
tx_buf[2] = 0x00
i = 0
max_val = [0]*8
next_time = time.time()
while True:
  for ch in range(8):
    tx_buf[1] = 0x80 | (ch << 4)
    with open(f'/sys/class/gpio/gpio{cs_pin}/value', 'w') as cs_file:
      cs_file.write('0')
    spi.write_readinto(tx_buf, rx_buf)
    with open(f'/sys/class/gpio/gpio{cs_pin}/value', 'w') as cs_file:
      cs_file.write('1')

    raw_val = ((rx_buf[1] & 0x3) << 8) | rx_buf[2]
    adc_val = raw_val * 100.0 / 1023.0
    if adc_val > max_val[ch]:
      max_val[ch] = adc_val
      #filt_val = alpha*adc_val + (1-alpha)*filt_val

  if i > int(sample_rate):
    print(*(f'{val:5.1f}%' for val in max_val))
    max_val = [0]*8
    i = 0
  i += 1

  next_time = next_time + sample_period
  sleep_time = next_time - time.time()
  if sleep_time > 0:
    time.sleep(sleep_time)
  else:
    print(f'Warning: ADC sampling took {sleep_time}s too long!')
