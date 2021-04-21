# AmpliPi Setup
Implementation of the AmpliPi Controller on the Raspberry Pi
## Configuration (Compute Module)
### From Ubuntu Linux
We have a script to configure the compute module as an AmpliPi
    ./scripts/bootstrap_pi
Then use the deploy script to put the AmpliPi software on the compute module
    ./scripts/deploy pi@amplipi.local
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

