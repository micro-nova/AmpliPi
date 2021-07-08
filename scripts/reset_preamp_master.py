#!/usr/bin/env python3

from RPi import GPIO
import serial
import time

NRST_PIN = 4
BOOT0_PIN = 5



# Issue a reset and boot to flash
GPIO.setmode(GPIO.BCM)
GPIO.setup(NRST_PIN, GPIO.OUT)
GPIO.output(NRST_PIN, 0)
GPIO.setup(BOOT0_PIN, GPIO.OUT)
GPIO.output(BOOT0_PIN, 0)
time.sleep(0.001)
GPIO.output(NRST_PIN, 1)
time.sleep(0.001)
GPIO.cleanup()

# Set the I2C address
time.sleep(0.1) # Wait for the micro to bootup
ser = serial.Serial ('/dev/serial0')
ser.baudrate = 9600
ser.write((0x41, 0x10, 0x0D, 0x0A))
ser.close()
time.sleep(0.1) # Wait for address setting to complete

