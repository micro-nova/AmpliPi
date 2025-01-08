#!/bin/bash
# flashes an amplipi disk image to an amplipi; attempts to launch rpiboot,
# autodetect the amplipi disk, prompt the user, flash it, and finally
# send a terminal bell.

# check user
if [ $(whoami) != "root" ] ; then
  echo "Please become root."
  exit
fi

# check dependencies
for i in whiptail rpiboot partprobe; do
  if [ ! $(which ${i} ]; then
    echo "Dependency ${i} not found; please install it or place it in your \$PATH"
    exit
  fi
done

set -u

if [ -z "$(ls /dev/disk/by-id/usb-RPi*)" ]; then
  rpiboot
  sleep .2
  partprobe
fi

set -e

dev=$(ls /dev/disk/by-id/usb-RPi* | grep -v part)
parts=$(ls /dev/disk/by-id/usb-RPi* | grep part)

set +e
for part in ${parts}; do
	umount ${part}
done
set -e

sync

whiptail --yesno "is this the correct device? \n ${dev}" 10 50

dd if=${1} of=${dev} bs=2M oflag=dsync status=progress

echo "syncing to disk..."
sync
sleep 5

echo "done!"

# I would use `notify-send` here, but it doesn't function for me
# in `sudo -i` 🥴
# https://youtu.be/Dp11DjaUc5A
tput bel
