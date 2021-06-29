#!/usr/bin/env python3

import smbus2
import time

# Loop through all values
bus = smbus2.SMBus(1)
for i in range(3):
  bus.write_byte_data(0x08, 0x0F, i)
  time.sleep(1)

# Exit with the default state set
bus.write_byte_data(0x08, 0x0F, 0x01)
