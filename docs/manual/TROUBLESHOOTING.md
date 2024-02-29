# Troubleshooting

If you are having problems with your AmpliPi device, start here.

## Audio

### Noise
Audio noise can have a lot of causes, below are some common reasons:
* **Mixing grounds**: AmpliPro has two different grounded lines, analog and digital. The most common way to mix them is by plugging in an audio device and attempting to power it with the USB on the rear of the unit, all USB-powered devices must be powered from a wall outlet
* **Speaker setup**: Some speaker configurations can lead to excess noise being inducted into the output. This is unrelated to the system and has everything to do with how the speakers are wired and installed.
* **Hardware issues**: See the support page for more info.

### No Audio
Lack of audio typically has one of a few causes:
* **No Source / Bad Source**: The source itself isn't outputting audio properly, try changing to a different source to confirm
* **Bad Output / Bad Zone**: Either the speaker, the speaker wires, or one of the ports on the back of the AmpliPro might be broken or hooked up incorrectly. Try a different speaker, length of wire, or port on the back of the AmpliPro to test each case

## Updating

There are two methods of updating:

### Webapp
Go to the web app at http://amplipi.local/ (if you've changed the hostname of your unit, replace "amplipi" with that hostname)

### Mobile App
Download the "Amplipi" app from the Google Play Store or Apple App Store. Go to the overview page for QR codes for each version.

### After choosing your update method
Once you've done either of those steps, the remaining steps are the same:
1. Click the gear icon in the bottom right corner to go to the configuration page
2. Select **Updates** and click the **Check for Updates** button

### New Release
To update your AmpliPi to the latest version:

3. Click the **Update** button

### Prereleases and using previous versions
Had an issue with an update? Revert your unit to a previous state:

3. Click the **Older Releases** tab and select the release you would like to use
4. Click the **Start Update** button

## Reimaging AmpliPro
For directions on how to bring AmpliPro's OS back to a previous version, scan the QR code:
![https://github.com/micro-nova/AmpliPi/blob/1e18ac7852a3340caacbe0e4b938336e7ce4d6fc/docs/imaging_etcher.md](imgs/reimaging-your-pi-qr.jpeg)
