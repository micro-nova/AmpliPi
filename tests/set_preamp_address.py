#!/usr/bin/env python3

# Writing Addresses to Preamp Boards
import serial
ser = serial.Serial ("/dev/serial0")
ser.baudrate = 9600

addr = 0x41, 0x10, 0x0D, 0x0A

ser.write(addr)
ser.close()

# Delay for Addresses to Propagate through boards
import time
time.sleep(3)

# I2C test commands - should turn on the first light in the first box
from smbus2 import SMBus
import smbus2 as smb
bus = smb.SMBus(1)
bus.write_byte_data(0x08, 0x05, 0x11)


### The steps above in the form of nice functions
# def init():
#     ser = serial.Serial ("/dev/ttyS0")
#     ser.baudrate = 9600

#     addr = 0x41, 0x10, 0x0D, 0x0A

#     ser.write(addr)
#     ser.close()

# def init2():
#     from smbus2 import SMBus
#     import smbus2 as smb
#     bus = smb.SMBus(1)
#     bus.write_byte_data(0x08, 0x05, 0x11)
