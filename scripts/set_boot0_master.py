#!/usr/bin/env python3

from RPi import GPIO
import time

NRST_PIN = 4
BOOT0_PIN = 5

# Issue a reset and boot to bootloader
GPIO.setmode(GPIO.BCM)
GPIO.setup(NRST_PIN, GPIO.OUT)
GPIO.output(NRST_PIN, 0)
GPIO.setup(BOOT0_PIN, GPIO.OUT)
GPIO.output(BOOT0_PIN, 1)
time.sleep(0.001)
GPIO.output(NRST_PIN, 1)
time.sleep(0.001)
GPIO.cleanup()
