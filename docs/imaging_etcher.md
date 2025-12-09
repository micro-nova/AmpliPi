# Imaging with Etcher

## What You'll Need
  * A computer running Windows, MacOS or Linux
  * A micro USB cable
  * Your AmpliPi

## Optional Step: Preserve your config
  Assuming you're not reflashing due to a corrupted config, you can make sure to save your configuration file for later upload to save yourself the manual setup post-flash. You can get your configuration file by going to Settings -> Configuration -> Download Config. If you can't reach the app, you can also access it by SSHing in using the credentials on the screen on the front of your unit (username: pi@{IP} ; password: {4 word string on front display}) or through the USB connection that will be achieved in steps 1 , 2, and 4 and then mounting the connected drive.
  Once you're in, the config file is at **/home/pi/.config/amplipi/house.json**

## 1. Get the Latest AmpliPi Image
  Download the latest AmpliPi image from [here](https://storage.googleapis.com/amplipi-img/amplipi_0.4.8.img.xz) ([md5sum](https://storage.googleapis.com/amplipi-img/CHECKSUMS), [.sig](https://storage.googleapis.com/amplipi-img/CHECKSUMS.sig)) and save it to your computer.

## 2. Get RPIBoot
Download and install the latest version of RPIBoot from [here](https://github.com/raspberrypi/usbboot/raw/master/win32/rpiboot_setup.exe) on windows, otherwise refer to the instructions for [building RPIBoot](https://github.com/raspberrypi/usbboot#building).

## 3. Get Etcher
Download and install (if necessary) the latest version of Etcher from [etcher.io](https://etcher.io/), on windows use the portable version.

## 4. Connect your AmpliPi to your computer

  **VERY IMPORTANT:** Please connect the USB cable to your computer FIRST before connecting the other side of the cable to the service port of the AmpliPro. Certain older units with TFT displays (not EINK) were susceptible to ESD damage on the USB service port. Connecting the cable to the computer first will mitigate this risk.

  Unplug your AmpliPi from power and then connect your AmpliPi to your computer via the service port using the micro USB cable. Once connected, plug your AmpliPi back into power.

  ![connected to service port](imgs/flashing/plugged_sp.jpg)

  IMPORTANT - You must connect your AmpliPi to your computer before plugging it into power or the Compute Module will not be recognized.

## 5. Open Etcher and Select the AmpliPi Image
  Open Etcher and select "Flash from file", then select the AmpliPi image you downloaded in step 1.

 ![selecting image](imgs/flashing/image.png)

## 6. Select the Compute Module
  Click the "Select target" button and select the Compute Module from the list of available drives.

  ![selecting device](imgs/flashing/device.png)

  WARNING -  Make sure to select the compute module! If you select the wrong drive, you may overwrite your computer's hard drive!

## 7. Flash the Image
  Click the "Flash!" button to begin flashing the image to your AmpliPi.

  ![ready to flash](imgs/flashing/ready.png)

  This process may take several minutes so feel free to grab a cup of coffee or your preferred beverage.

![flashing](imgs/flashing/flashing.png)

## 8. Disconnect your AmpliPi from your computer
  Once Etcher has finished flashing the image, unplug your AmpliPi from power and disconnect the micro USB cable. Now you're ready to boot up your AmpliPi! The username and password will be reset to the defaults of pi and raspberry, respectively.

  ![unplugged from service port](imgs/flashing/unplugged_sp.jpg)

  IMPORTANT - You must unplug your micro USB cable before plugging your AmpliPi back into power or the Compute Module will not boot properly.
