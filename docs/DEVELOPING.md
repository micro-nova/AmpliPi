# Developing for the AmpliPi Project
Thanks for considering developing for AmpliPi. We appreciate your support!

## Developing on a separate computer
This allows remote development with the ability to test changes on your AmpliPi
1. Checkout this repo on a linux based system (a git bash shell on windows works fine as well).
1. Make changes with your favorite editor, we suggest vscode
1. Use `scripts/deploy` to deploy the latest software.
   The pi must have access to the internet to successfully run this script.
   #### Congratulations! The Amplipi is now running the software you deployed! You can stop now or continue in order to debug over SSH!
1. ssh into the AmpliPi with `ssh pi@amplipi.local`, the default password is raspberry (you can change it to whatever)
1. Change directory to the development root `~/amplipi-dev` (this is where `deploy` put the software)
1. To run the amplipi server in debug mode over an ssh connection, run `./scripts/run_debug_webserver` it will run a debug webserver on [amplipi.local:5000](http://amplipi.local:5000).
1. Restart amplipi service (it was stopped by `./scripts/run_debug_webserver`) with `systemctl --user restart amplipi`.

## Developing on an AmpliPi Controller over SSH
1. Make a git checkout at `~/amplipi-dev` using `git checkout https://github.com/micro-nova/AmpliPi ~/amplipi-dev` (you may need to delete `amplipi-dev` if it already exists)
1. Change directory to amplipi-dev `cd ~/amplipi-dev`
1. Make changes using your favorite editor
1. To run the amplipi server in debug mode, run `./scripts/run_debug_webserver` it will run a debug webserver on [amplipi.local:5000](http://amplipi.local:5000).
1. Once you are comfortable with your changes, run `./scripts/configure.py --python-deps --os-deps --display --web`. This will install any required dependencies and reconfigure the amplipi web and display services.

## Developing on an AmpliPi Controller remotely using vscode

See our [remote vscode guide](docs/vscode_remote_dev.md) for more information.

## Additional setup and notes for testing on Windows

__You will need to install the following:__
- git (you will need git bash)
- vscode (only recommended)
- python 3 and setup the python path (step 6 in the following guide) https://phoenixnap.com/kb/how-to-install-python-3-windows

__Notes:__
- The latest Windows 10 supports mDNS which we use to easily ssh into amplipi, however we had some problems using WiFi so we suggest a ethernet connection on windows.

## Different development setups
Many of you will not have the luxury of having an AmpliPi system to test with, after all they are not currently available.
Below are a couple of different ways you can start developing for the AmpliPi without an actual system:
* Mocked out audio and mocked out controller (needs: debian based system such as Pi or Ubuntu)

  Supports:
  * Web interface development
  * API testing
  * Basic Streams testing

* Mocked out controller (with 4 stereo audio channels), needs: something running Raspberry Pi OS (previously called raspbian)

  Supports:
  * Web interface development
  * API testing
  * Streams integration and testing

  Requires:
  * Raspberry Pi OS with ALSA support (any 32-bit image before December 2020) (we recommend: https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2020-08-24/)
  * A cmedia based, usb, 7.1 channel audio device (we have tested with this connected: https://www.amazon.com/Vantec-NBA-200U-External-Channel-Adapter/dp/B004HXGJ3S)

* Actual system

  Supports:
  * Web interface development
  * API testing
  * Streams integration and testing
  * Group and zone configuration
  * Analog Audio input

## Developing with a mocked out controller on a debian based os
This is the simplest way to develop new features for AmpliPi without an AmpliPi controller.
Optionally you can install some streaming sources for partial streaming testing.
1. Checkout this repo
1. (Optional) Install streaming os dependencies with `./scripts/configure.py --os-deps`.
The dependencies will be installed globally with apt.
This is optional since it installs many packages needed by the various streaming sources.
It could potentially cause package conflicts on your system.
1. Install python dependencies to AmpliPi's virtual environment with `./scripts/configure.py --python-deps`
1. Use ```./scripts/run_debug_webserver``` to start the mock server, if the streaming deps were not installed add the **--mock-streams** flag like ```./scripts/run_debug_webserver --mock-streams```.

## Developing with a mocked out controller (with 4 stereo channel audio) on something running Raspberry Pi OS
1. Start with a 32-bit version of Rasberry Pi OS. This needs to be older than december 2020 since our system only supports the ALSA audio backend currently.
1. Connect a cmedia based, usb, 7.1 channel audio device to the pi. We have tested using this one: https://www.amazon.com/Vantec-NBA-200U-External-Channel-Adapter/dp/B004HXGJ3S
1. Checkout this repo on a linux based system (a git bash shell on windows works fine as well)
1. Edit config/asound.conf. Uncomment the "Old Prototype" section at the bottom, and comment out the similar configuration above. This should be the configuration needed for the 7.1 channel USB audio card. Depending on the setup the card will either show up as #2 or #3. That needs to be changed on lines 27 and 32. Find the card # using ```aplay -l | grep "USB Sound Device"``` and edit those lines to include the correct #.
1. Execute ```scripts/deploy USER@HOSTNAME --mock-ctrl``` or ```scripts/deploy USER@IP_ADDRESS``` replacing USER and HOSTNAME/IP_ADDRESS with the appropriate values for the pi device
1. Over ssh connection, run ```scripts/run_debug_webserver --mock-ctrl``` from the ```~/amplipi-dev``` directory.

## Installing AmpliPi from scratch on a Pi Compute Module
1. For a fresh pi compute module, run `scripts/bootstrap-pi`.
   All pi compute modules shipped with AmpliPi's have already been configured using this script,
   so this step should not be necessary.
   Running the script without any arguments will print the instructions.
   After this step is done SSH is enabled from a fresh Raspberry Pi OS at [amplipi.local].
1. [amplipi.local] should now be hosted on your network.
