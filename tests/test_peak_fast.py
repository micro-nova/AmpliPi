#!/usr/bin/env python3

import board
import busio
import digitalio
import time

# Config
cs_pin = digitalio.DigitalInOut(board.D17)
baud = 1000000      # MHz, MCP3008 max is 3.6 MHz, min 10 kHz
sample_rate = 100.0   # Hz

# Setup SPI bus using hardware SPI:
spi = busio.SPI(clock=board.SCLK_1, MOSI=board.MOSI_1, MISO=board.MISO_1)
while not spi.try_lock():
  pass
spi.configure(baudrate=baud)

sample_period = 1/sample_rate
cs_pin.direction = digitalio.Direction.OUTPUT
cs_pin.value = True
ch = 7 # 0-indexed
rx_buf = bytearray(3)
tx_buf = bytearray(3)
tx_buf[0] = 0x01
tx_buf[1] = 0x80 | (ch << 4)
tx_buf[2] = 0x00
i = 0
max_val = 0
while True:
  start = time.time()

  cs_pin.value = False
  spi.write_readinto(tx_buf, rx_buf)
  cs_pin.value = True

  raw_val = ((rx_buf[1] & 0x3) << 8) | rx_buf[2]
  adc_val = raw_val * 100.0 / 1023.0
  if adc_val > max_val:
    max_val = adc_val
    #filt_val = alpha*adc_val + (1-alpha)*filt_val

  if i > int(sample_rate):
    print(f'{max_val:5.1f}%')
    max_val = 0
    i = 0
  i += 1

  end = time.time()
  #print('Took ', 1000*(end - start), ' ms')
  sleep_time = sample_period - (end-start)
  if sleep_time > 0:
    time.sleep(sleep_time)
  else:
    print(f'Warning: ADC sampling took {sleep_time}s too long!')
