# AmpliPi Setup
Implementation of the AmpliPi Controller on the Raspberry Pi
## Configuration (Compute Module)
### From Ubuntu Linux

    git clone --depth=1 https://github.com/raspberrypi/usbboot
    pushd usbboot
    sudo apt install libusb-1.0-0-dev
    make
    
    echo "Plug in a usb cable from the service port to your computer. Don't turn on the AmpliPi yet." 
    read -p "Plug in the AmpliPi after pressing any key" -n 1
    sudo ./rpiboot
    popd

    echo "Downloading and extracting Raspberry Pi OS"
    wget https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2020-08-24/2020-08-20-raspios-buster-armhf-lite.zip
    mkdir 2020-08-20-raspios-buster-armhf-lite
    cd 2020-08-20-raspios-buster-armhf-lite
    unzip ../2020-08-20-raspios-buster-armhf-lite.zip
    
    echo "Copying the image to the AmpliPi"
    sudo dd if=2020-08-20-raspios-buster-arm64-lite.img of=/dev/sda bs=1024MiB
    
    echo "Setup SSH so we can configure the Pi"
    sudo mkdir -p /mnt/pi
    sudo mount /dev/sda1 /mnt/pi
    cd /mnt/pi
    sudo touch ssh
    sudo emacs etc/dhcpcd.conf # add a static ip address using your favorite editor
    cd -
    sudo umount /mnt/pi

Download Raspberry Pi OS from [here](https://www.raspberrypi.org/downloads/raspberry-pi-os/) we are currently using the "Raspberry Pi OS (32-bit) with desktop and recommended software"
Follow steps on [rpi](https://www.raspberrypi.org/documentation/hardware/computemodule/cm-emmc-flashing.md) to flash the eMMC on the device
## Configuration (RPi 4)
Download and install Raspberry Pi Imager from [here.](https://www.raspberrypi.org/downloads/) We are currently using v1.4
Using this program with an SD card reader, install "Raspberry Pi OS (32-bit) onto the SD card.

## Development setup
1. Use vscode with its python plugin, this should highlight errors
2. In a bash terminal you should setup an ssh key for interacting with the pi checkout this [guide](https://www.raspberrypi.org/documentation/remote-access/ssh/passwordless.md)

### Deploying code for testing
1. Find the rpi's ip address and set the variable expected by the deploy script
2. Copy the python files over
From the base of the git repo in bash
```./scripts/deploy```
3. ssh into the pi and run the files
```
ssh $RPI_IP_ADDRESS
```
4. Run the webserver
```
cd python && ./run_webserver.sh
```
### Running tests
```bash
pip3 install pytest # add pytest
cd python
pip3 install -e # local install of ethaudio so we can test against it
pytest tests/test_ethaudio.py
```
### Flashing Preamp Code
1. Go to the firmware directory on the Pi with "cd ~/fw". It should be created in the home directory with "./util/copy_python_to_board.sh" that was run previously
2. Once you are ready to flash the ST chip on the preamp board, run the flashing script from the Pi terminal with "./preamp_flash.sh"
3. If you want to change the software on the preamp, change the content of 'preamp_bd.bin' or change 'preamp_flash.sh' to flash a binary file of your choosing

