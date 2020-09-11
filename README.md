# ethaudio-rpi-controller
Implementation of the EthAudio Controller on the Raspberry Pi
## Configuration (Compute Module)
Download Raspberry Pi OS from [here](https://www.raspberrypi.org/downloads/raspberry-pi-os/) we are currently using the "Raspberry Pi OS (32-bit) with desktop and recommended software"
Follow steps on [rpi](https://www.raspberrypi.org/documentation/hardware/computemodule/cm-emmc-flashing.md) to flash the eMMC on the device
## Configuration (RPi 4)
Download and install Raspberry Pi Imager from [here.](https://www.raspberrypi.org/downloads/) We are currently using v1.4
Using this program with an SD card reader, install "Raspberry Pi OS (32-bit) onto the SD card.

## Development setup
1. Use vscode with its python plugin, this should highlight errors
2. In a bash terminal you should setup an ssh key for interacting with the pi checkout this [guide](https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md)

### Deploying code for testing
1. Find the rpi's ip address and set the variable expected by the copy_python_to_board.sh script
2. Copy the python files over
From the base of the git repo in bash
```./util/copy_python_to_board.sh```
3. ssh into the pi and run the files
```
ssh $RPI_IP_ADDRESS
export DISPLAY=:0 # use the connected display, this is set weird over ssh by default
```

## TODO add howto configure USB audio for shairport
## TODO follow strategy for handling 7.1 channel audio -> 4 stereo output
