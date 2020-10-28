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
### Running tests
```bash
pip3 install pytest # add pytest
cd python
pip install -e # local install of ethaudio so we can test against it
pytest tests/test_ethaudio_rpi.py
```

## TODO add howto configure USB audio for shairport
## TODO follow strategy for handling 7.1 channel audio -> 4 stereo output

## Adding Pandora/Streaming support

### Complicated solutions
So I have been going down the rabbit hole of adding Pandora support to the AmpliPi. Here are some of the significant things that I have found:
* [Mopidy](www.mopidy.com) [Git](https://github.com/mopidy/mopidy) - A python based "everything" audio server that has support for many different audio plugins and many different controls
* [Snapcast](https://mjaggard.github.io/snapcast/) [Git](https://github.com/badaix/snapcast) - A multiroom, mutliaudio source streaming server
    + At the very least we should use their interfaces as a reference design
    + Can we present the same interface and use their existing apps?
* [Mopidy Muse](https://mopidy.com/ext/muse/) [Git](https://github.com/cristianpb/muse) - A really nice web interface that combines the snapcast and mopidy
    + Can we use this to control inputs?
    + Looks like you can test it here: https://cristianpb.github.io/muse/ (assuming snapcast and mopidy are running locally)

### Simpler Pandora Support
* Use [Pianobar](https://github.com/PromyLOPh/pianobar) and use its file interface like [Patiobar](https://github.com/kylejohnson/Patiobar) does here: https://github.com/kylejohnson/Patiobar/blob/master/eventcmd.sh
* Use the bare [Pydora](https://github.com/mcrute/pydora) python implementation that uses a vlc backend for audio output, running in a background process and send commands to it with the api


#### Using Pianobar
##### Config
Need to add fifo file using mkfifo to ~/.config/pianobar/ctrl
##### Control
See https://github.com/jreese/pianobar-python/blob/master/pianobar/control.py for an example of how to control pianobar through the fifo
##### Event handling
See https://github.com/kylejohnson/Patiobar/blob/master/eventcmd.sh and https://github.com/PromyLOPh/pianobar/blob/master/contrib/eventcmd-examples/scrobble.py for some example event handling. We need this to handle new songs, radio station list, and additional state
##### Start and Stopping Pandora
TODO: add start and stop control of Pandora, how does patiobar do this?
##### Using multiple Pianobars
TODO: handle configuration and control of multiple pianobars once everything else works. This will need to be done be setting different configuration paths since using ~/.config/pianobar will cause collisions
Maybe for each source there could be a configuration destination, ~/.config/amplipi/srcs/0/
