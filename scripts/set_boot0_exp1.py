#!/usr/bin/env python3

from RPi import GPIO
import serial
import smbus2
import time


NRST_PIN = 4
BOOT0_PIN = 5

reset=False
if reset:
  # Issue a reset and boot to flash
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(NRST_PIN, GPIO.OUT)
  GPIO.output(NRST_PIN, 0)
  GPIO.setup(BOOT0_PIN, GPIO.OUT)
  GPIO.output(BOOT0_PIN, 0)
  time.sleep(0.01)
  GPIO.output(NRST_PIN, 1)
  time.sleep(0.01)
  GPIO.cleanup()

  # Set the I2C address
  time.sleep(0.1) # Wait for the micro to bootup
  ser = serial.Serial ("/dev/serial0")
  ser.baudrate = 9600
  ser.write((0x41, 0x10, 0x0D, 0x0A))
  ser.close()
  time.sleep(0.1) # Wait for address setting to complete

# Issue a reset and boot to bootloader (for expansion board)
# Bit 0: NRST
# BIT 1: BOOT0
# Bit 2: UART TX passthrough
# Bit 3: UART RX passthrough
bus = smbus2.SMBus(1)
bus.write_byte_data(0x08, 0x0F, 0x02)
time.sleep(0.001)
bus.write_byte_data(0x08, 0x0F, 0x0F)

# Program master: sudo stm32flash -vRb 38400 -i 5,-4,4 -w ~/preamp_exp.bin /dev/serial0
# Program exp1:   sudo stm32flash -b 38400 -w ~/preamp_exp.bin /dev/serial0
