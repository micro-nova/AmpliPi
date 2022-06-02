#!/usr/bin/env python3
import spidev
import time

spi = spidev.SpiDev()
spi.open(1, 1)
spi.max_speed_hz = 3600000
#spi.mode = 0b00
#spi.bits_per_word = 8
#spi.cshigh=False
#spi.lsbfirst=False

# Only first read working, need to check hardware
to_send = [0x01, 0x80, 0x00]
data = []
start_time = time.time()
for c in range(8):
  #to_send[1] = 0x80 | (c << 4)
  meas = spi.xfer2(to_send)
  print(meas)
  data.append((meas[1] << 8) + meas[2])
print(f'Elapsed = {time.time() - start_time}')
print(data)
