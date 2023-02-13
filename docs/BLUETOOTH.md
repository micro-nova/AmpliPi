# Bluetooth
AmpliPi currently supports at most one bluetooth stream at a time. If a bluetooth dongle is present on boot, AmpliPi will create a bluetooth stream automatically. AmpliPi ships with drivers pre-installed for [this bluetooth dongle](https://www.amazon.com/gp/product/B08LVH5BCP/). Other bluetooth dongles may need drivers to be installed.

The AmpliPi bluetooth name will be the same as the host name (defaults to amplipi). Connect to this with a bluetooth sound source and select the bluetooth stream on any source. You should now be able to play audio from the device and control it through the media controls on the stream interface.

Currently, multiple devices can connect but cannot simultaneously play audio. The first device to play audio will have control over the bluetooth stream. When this device stops playing audio, AmpliPi will try to give control to the next connected device that is playing audio.
