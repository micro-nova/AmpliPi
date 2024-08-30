# Bluetooth

Bluetooth support can be enabled by connecting a USB Bluetooth dongle to your AmpliPi.

## Hardware support
AmpliPi currently supports at most one Bluetooth stream at a time. If a Bluetooth dongle is connected when the AmpliPi is started a Bluetooth stream is created automatically.

### Tested Hardware
-  [ZEXMTE Long Range USB Bluetooth Adapter](https://www.amazon.com/gp/product/B08LVH5BCP/).

### Other USB Bluetooth dongles
Other Bluetooth dongles may need drivers to be installed. We suggest ensuring the maximum range of the adapter encompasses your whole home so that the audio doesn't cut out.

## How to play audio
1. Set one of the sources to the Bluetooth stream input
2. Pair and connect your device to **amplipi** (the hostname of your AmpliPro)
3. Play some audio out your device

## Multiple Bluetooth devices
Currently, multiple devices can connect but cannot simultaneously play audio. The first device to play audio will have control over the Bluetooth stream. When this device stops playing audio, AmpliPi will try to give control to the next connected device that is playing audio.
