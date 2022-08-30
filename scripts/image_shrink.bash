#!/usr/bin/env bash

# Setup resize2fs on the file system so we don't have to edit the image file later
if false; then
ssh pi@amplipi.local '
  rm /home/pi/.config/amplipi/default_password.txt
  sudo sed -i "/^.*init=/! s@\(^.*$\)@\1 init=/usr/lib/raspi-config/init_resize.sh@" /boot/cmdline.txt
  sudo wget -O /etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
  sudo chmod +x /etc/init.d/resize2fs_once
  sudo systemctl enable resize2fs_once
  cat /dev/null > ~/.bash_history && history -c && sudo systemctl poweroff
'
fi
# Instruct user to unplug power and plug back in

# Connect to amplipi eMMC and shrink root partition
sudo rpiboot
disk_base_path=/dev/disk/by-id/usb-RPi-MSD
for i in {1..10}; do
  sleep 0.5

  # Check for Raspberry Pi device path
  pi_path=$(ls $disk_base_path* 2>/dev/null | head -n1)
  if [ ! -z $pi_path ]; then
    echo -e "\nRaspberry Pi device found at $pi_path\n"
    break
  fi
done

# Error out if no Pi found
if [ -z $pi_path ]; then
  echo -e "\n${RED}ERROR:${NC} No Raspberry Pi device found at $disk_base_path*"
  read -p "Press any key to continue..." -sn 1
  echo "" # newline
  exit 2
fi

# Pi found! Mount boot partition and ensure init_resize.sh is configured to run
boot_dir=$(mktemp -d)
sudo mount $pi_path-part1 $boot_dir
sudo sed -i "/^.*init=/! s@\(^.*$\)@\1 init=/usr/lib/raspi-config/init_resize.sh@" $boot_dir/cmdline.txt
sudo umount $boot_dir

root_dir=$(mktemp -d)
sudo mount $pi_path-part1 $root_dir
#rm /home/pi/.config/amplipi/default_password.txt
#sudo wget -O /etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
#sudo chmod +x /etc/init.d/resize2fs_once
#sudo systemctl enable resize2fs_once
#cat /dev/null > ~/.bash_history
# Any files in /var/log that can be removed? /var/log/apt/*?
sudo umount $root_dir

sudo fsck -f $pi_path-part2 #e2fsck
sudo resize2fs -pM $pi_path-part2
block_count=$(sudo tune2fs -l $pi_path-part2 | grep "Block count" | sed "s/^Block count: *//g")
block_size=$(sudo tune2fs -l $pi_path-part2 | grep "Block size" | sed "s/^Block size: *//g")
new_sectors=$(($block_count*$block_size/512))
echo ",$new_sectors" | sudo sfdisk -N2 $pi_path

# TODO:
#The unit size is 512 bytes from the output of `sudo fdisk -l $pi_path`
#To perform the actual copy use `dd`'s `count` argument to copy `count` number of blocks.
#The following is an example where the End sector of $pi_path-part2 was 12374831.
#end_sector=12374831
#sector_size=512
#sudo fdisk -l /dev/disk/by-id/usb-RPi-MSD-_0001_ef805fe6-0\:0 | sed -n 's/.*part2 *//p'
#$[($end_sector+1)*$sector_size/1024/1024]
#sudo dd if=/dev/sdX of=amplipi.img bs=1MiB count=$[($end_sector+1)*$sector_size/1024/1024] status=progress

#root_dir=$(mktemp -d)
#sudo mount $pi_path-part2 $root_dir

image_file=$HOME/mn/images/amplipi_1.8.img
sudo dd if=$pi_path of=$img_file bs=4MiB status=progress
