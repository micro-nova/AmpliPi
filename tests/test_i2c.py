#!/usr/bin/env python3

# I2C test commands - should turn on the first light in the first box
import smbus2
bus = smbus2.SMBus(1)
bus.write_byte_data(0x08, 0x0E, 0x55)
