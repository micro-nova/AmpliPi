#!/usr/bin/env python3

"""
Peak-detect test script.
This file is not meant to be used with pytest, since it currently requires
human interaction to play/pause inputs before checking the output of this script.
"""

from pathlib import Path
import time

import board
import busio

# Config
CS_PIN = 17           # GPIO pin number
SPI_BAUD = 1000000    # MHz, MCP3008 max is 3.6 MHz, min 10 kHz
SAMPLE_RATE = 20.0    # Hz, rate at which to sample all channels

def cs_setup() -> None:
  """ CS pin setup. Leaves CS inactive. """
  if not Path('/sys/class/gpio/gpio17').exists():
    with open('/sys/class/gpio/export', 'w') as file:
      file.write(f'{CS_PIN}')
    time.sleep(0.1)
    with open('/sys/class/gpio/gpio17/direction', 'w') as file:
      file.write('out')

  with open(f'/sys/class/gpio/gpio{CS_PIN}/value', 'w') as cs_file:
    cs_file.write('1')

def read_adc(spi: busio.SPI, channel: int) -> int:
  """ Read a single ADC channel of the MCP3008  """
  # TODO: This is still kinda slow, investigate Python's 'spidev'
  # library or https://iosoft.blog/2020/06/11/fast-data-capture-raspberry-pi/
  rx_buf = bytearray(3)
  tx_buf = bytearray((0x01, 0x80 | (channel << 4), 0x00))
  with open(f'/sys/class/gpio/gpio{CS_PIN}/value', 'w') as cs_file:
    cs_file.write('0')
  spi.write_readinto(tx_buf, rx_buf)
  with open(f'/sys/class/gpio/gpio{CS_PIN}/value', 'w') as cs_file:
    cs_file.write('1')
  raw_val = ((rx_buf[1] & 0x3) << 8) | rx_buf[2]
  return raw_val

def read_vals():
  """ Read all 8 peak-detect channels forever. Every second, prints the max
      value read for each channel over the preceding second.
  """
  # Setup SPI bus using hardware SPI:
  peak_spi = busio.SPI(clock=board.SCLK_1, MOSI=board.MOSI_1, MISO=board.MISO_1)
  while not peak_spi.try_lock():
    pass
  peak_spi.configure(baudrate=SPI_BAUD)

  cs_setup()

  sample_period = 1/SAMPLE_RATE
  i = 0
  max_val = [0]*8
  next_time = time.time()
  while True:
    for chan in range(8):
      raw_val = read_adc(peak_spi, chan)
      adc_val = raw_val * 100.0 / 1023.0
      if adc_val > max_val[7-chan]:
        max_val[7-chan] = adc_val
        #filt_val = alpha*adc_val + (1-alpha)*filt_val

    # Print header once every 30 seconds
    if i % (30*int(SAMPLE_RATE)) == 0:
      print('  CH1R   CH1L   CH2R   CH2L   CH3R   CH3L   CH4R   CH4L')

    # Print vals once a second
    if i % int(SAMPLE_RATE) == 0:
      print(*(f'{val:5.1f}%' for val in max_val))
      max_val = [0]*8
    i += 1

    next_time = next_time + sample_period
    sleep_time = next_time - time.time()
    if sleep_time > 0:
      time.sleep(sleep_time)
    else:
      print(f'Warning: ADC sampling took {-sleep_time}s too long!')
      # Reset sampling period in case of NTP time jumps
      next_time = time.time() + sample_period

if __name__ == "__main__":
  read_vals()
