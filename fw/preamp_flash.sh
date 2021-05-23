#!/bin/bash

# Flash the attached preamp board
# sudo is required due to the fact that not every user can access the GPIO pins on the Pi
# stm32flash runs the whole operation. Put "stm32flash -h" in the Pi terminal for more information, or visit https://manpages.ubuntu.com/manpages/xenial/en/man1/stm32flash.1.html
# Origin: https://sourceforge.net/projects/stm32flash/
# -b sets the baudrate - here we are using 38400. The UART communication with the chip typically runs at 9600 baud
# -w specifies that you are writing from a file, in this case preamp_bd.bin from its directory. Change this section in order to flash different software
# -v specifies a verify on writes during the flashing process
# -R resets the device when flashing is complete. Allows for seamless use after a flash
# -i calls for a GPIO string. This sequence specifies the process needed for flashing, and makes use of GPIO 4 and 5 which are connected to the NRST and BOOT0 pins respectively.
# The sequence specifically translates to BOOT0 being held high, while NRST sees a low pulse that allows flashing to occur. Typical values for these pins are:
# GPIO4 = NRST = 3.3V and GPIO5 = BOOT0 = 0V
# /dev/ttyAMA0 is the UART network that the script flashes over. Flashing is also possible with I2C

set -e

# get directory that the script exists in
cd "$( dirname "$0" )"

if ! which stm32flash; then
  echo "installing stm32flash"
  sudo apt update && sudo apt install -y stm32flash
else
  echo "stm32flash already installed"
fi

sudo stm32flash -b 38400 -w preamp_bd.bin -v -R -i 5,-4,4 /dev/ttyAMA0
