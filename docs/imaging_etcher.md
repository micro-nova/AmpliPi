# Imaging with Etcher

## What You'll Need
  * A computer running MacOS, Linux, or Windows
  * A micro USB cable
  * Your Amplipi

## 1. Get the Latest Amplipi Image
  Download the latest image of Amplipi from [here](https://drive.google.com/file/d/1VHQhHivWCNVwmHukqtjjWu322Nxu_iDp/view) and save it to your computer.

## 2. Get Etcher
Download and install (if necessary) the latest version of Etcher from [etcher.io](https://etcher.io/).

## 3. Connect your Amplipi to your computer
  Unplug your Amplipi from power and then connect your Amplipi to your computer via the service port using the micro USB cable. Once connected, plug your Amplipi back into power.

  ![connected to service port](imgs/flashing/plugged_sp.jpg)

  IMPORTANT - You must connect your Amplipi to your computer before plugging it into power or the Compute Module will not be recognized.

## 4. Open Etcher and Select the Amplipi Image
  Open Etcher and select "Flash from file", then select the Amplipi image you downloaded in step 1.

 ![selecting image](imgs/flashing/image.png)

## 5. Select the Compute Module
  Click the "Select target" button and select the Compute Module from the list of available drives.

  ![selecting device](imgs/flashing/device.png)

  WARNING -  Make sure to select the compute module! If you select the wrong drive, you may overwrite your computer's hard drive!

## 6. Flash the Image
  Click the "Flash!" button to begin flashing the image to your Amplipi.

  ![ready to flash](imgs/flashing/ready.png)

  This process may take several minutes so feel free to grab a cup of coffee or your preferred beverage.

![flashing](imgs/flashing/flashing.png)

## 7. Disconnect your Amplipi from your computer
  Once Etcher has finished flashing the image, unplug your Amplipi from power and disconnect the micro USB cable. Now you're ready to boot up your Amplipi! The username and password will be reset to the defaults of pi and raspberry, respectively.

  ![unplugged from service port](imgs/flashing/unplugged_sp.jpg)

  IMPORTANT - You must unplug your micro USB cable before plugging your Amplipi back into power or the Compute Module will not boot properly.
