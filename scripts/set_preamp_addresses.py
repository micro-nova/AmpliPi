#!/usr/bin/env python3

# Assign an I2C address to the master preamp, which will
# the assign an address to the first expansion unit if
# one exists, and so on.
import serial
with serial.Serial('/dev/serial0', baudrate=9600) as ser:
  ser.write((0x41, 0x10, 0x0D, 0x0A))
