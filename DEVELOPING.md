# Developing for the AmpliPi Project
Thanks for considering developing for AmpliPi. We appreciate your support!
Many of you will not have the luxury of having an AmpliPi system to test with, after all they are not currently available.
## Different development setups
Below are a couple of different ways you can start developing for the AmpliPi without an actual system:
* Mocked out audio and mocked out controller (needs: debian based system such as Pi or Ubuntu)

  Supports:
  * Web interface development
  * API testing

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

## Testing mocked out audio and mocked out controller on a debian based os
1. Checkout this repo
1. Install python dependencies
1. Use ```scripts/run_debug_webserver --mock-ctrl --mock-streams``` to start the mock server

## Testing mocked out controller (with 4 stereo channel audio) on something running Raspberry Pi OS
1. Start with a 32-bit version of Rasberry Pi OS. This needs to be older than december 2020 since our system only supports the ALSA audio backend currently.
1. Connect a cmedia based, usb, 7.1 channel audio device to the pi. We have tested using this one: https://www.amazon.com/Vantec-NBA-200U-External-Channel-Adapter/dp/B004HXGJ3S
1. Checkout this repo on a linux based system (a git bash shell on windows works fine as well)
1. Edit config/asound.conf. Uncomment the "Old Prototype" section at the bottom, and comment out the similar configuration above. This should be the configuration needed for the 7.1 channel USB audio card. Depending on the setup the card will either show up as #2 or #3. That needs to be changed on lines 27 and 32. Find the card # using ```aplay -l | grep "USB Sound Device"``` and edit those lines to include the correct #.
1. Execute ```scripts/deploy USER@HOSTNAME --mock-ctrl``` or ```scripts/deploy USER@IP_ADDRESS``` replacing USER and HOSTNAME/IP_ADDRESS with the appropriate values for the pi device
1. Over ssh connection, run ```scripts/run_debug_webserver --mock-ctrl``` from the ```~/amplipi-dev``` directory.

## Testing on a pi 3+ compute module connected to an AmpliPi Controller
1. Checkout this repo on a linux based system (a git bash shell on windows works fine as well).
1. All AmpliPi's have already been configured using `scripts/bootstrap-pi`.
   For a fresh installation run that script from the host system, but this should not be necessary.
   After this SSH is enabled from a fresh Raspberry Pi OS.
1. Use `scripts/deploy` to deploy the latest software.
1. Use the scripts/deploy to configure the pi (TODO: make this configure the pi's boot file).
1. [amplipi.local] should now be hosted on your network.
1. For development. To run the amplipi server in debug mode Over an ssh connection, run `scripts/run_debug_webserver` it will run a debug webserver on [amplipi.local:5000]

## Testing on windows
This should be possible but has not been documented
TODO: investigation and testing needed
