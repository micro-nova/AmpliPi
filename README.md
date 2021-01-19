# AmpliPi Home Audio System
AmpliPi is a multi room/zone home audio controller and amplifier made for whole house audio systems with many zones. It can play 4 different audio streams or sources to one or many zones, all of which are configurable in real-time using the self-hosted AmpliPi Web App or its underlying REST API. It is expandable to 36 zones using AmpliPi Zone Expanders.

The AmpliPi design is entirely open source, from the software, to the firmware, to the hardware. The REST API and Web App are written in Python and run on a Raspberry Pi 3+ Compute Module. The firmware, which provides the low level volume control and zone configuration, is written in C and configured by the Python API over I2C. All of the internal circuitry and PCBs are open hardware as well and come with full schematics.

## Web interface
Each of the four audio sources are configurable.

### Changing Group and Zone volumes


### Adding a group to or zone to a different source
1. Go to the audio source to configure
2. Select the group or zone from the drop down menu

### REST API
