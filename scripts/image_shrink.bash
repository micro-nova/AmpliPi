#!/usr/bin/env bash

# Connect to amplipi eMMC.
# The Pi must have been powered on with the service USB plugged in.
# TODO: Check for already-booted Pi
sudo rpiboot
disk_base_path=/dev/disk/by-id/usb-RPi-MSD
for i in {1..10}; do
  sleep 0.5

  # Check for Raspberry Pi device path
  pi_path=$(ls $disk_base_path* 2>/dev/null | head -n1)
  if [ ! -z $pi_path ]; then
    echo -e "\nRaspberry Pi device found at $pi_path"
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

# Pi found! Mount root directory.
root_dir=$(mktemp -d)
sudo mount $pi_path-part2 $root_dir

echo -e "\nDownloading resize2fs_once script"
sudo wget -O $root_dir/etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
sudo chmod +x $root_dir/etc/init.d/resize2fs_once
sudo ln -s $root_dir/etc/init.d/resize2fs_once $root_dir/etc/rc3.d/S01resize2fs_once

echo -e "\nRemoving all log files"
sudo find $root_dir/var/log -type f -exec rm {} \;

echo "Cleaning up /home/pi"
rm -f $root_dir/home/pi/.config/amplipi/default_password.txt
cat /dev/null > ~/.bash_history
sudo umount $root_dir

# Mount boot partition and ensure init_resize.sh is configured to run at boot
boot_dir=$(mktemp -d)
sudo mount $pi_path-part1 $boot_dir
# Remove any existing init= args, and add init_resize.sh as the init binary
echo "Configuring resize2fs to run at boot."
sudo sed -i 's/init=.* //g' $boot_dir/cmdline.txt
sudo sed -i 's/ init=.*$//g' $boot_dir/cmdline.txt
sudo sed -i "s@\(^.*$\)@\1 init=/usr/lib/raspi-config/init_resize.sh@" $boot_dir/cmdline.txt
sudo umount $boot_dir

echo -e "\nRunning fsck on boot filesystem just in case."
sudo fsck -fp $pi_path-part1
if [[ $? -gt 1 ]]; then
  echo "\n${RED}ERROR:${NC} Couldn't auto-fix AmpliPi's boot filesystem, exiting."
  exit 3
fi

echo -e "\nRunning fsck on root filesystem - required by resize2fs."
sudo fsck -fp $pi_path-part2
if [[ $? -gt 1 ]]; then
  echo "\n${RED}ERROR:${NC} Couldn't auto-fix AmpliPi's root filesystem, exiting."
  exit 4
fi

# Resize the root filesystem.
# resize2fs is very cautious when shrinking. Running a second time (or more)
# will let its algorithm hone in on the real minimum size. It takes a while
# though, and after a second time there are very diminishing returns.
echo -e "\nShrinking root filesystem."
sudo resize2fs -pM $pi_path-part2
sudo resize2fs -pM $pi_path-part2

# Wait for filesystem changes to be complete (timeout after 10s)
#while ! sudo blockdev --rereadpt /dev/sda 2>/dev/null; do
reread=false
for i in {1..100}; do
  sleep 0.1;
  if sudo blockdev --rereadpt /dev/sda 2>/dev/null; then
    reread=true
    break
  fi
done

if ! $reread; then
  echo -e "\n${RED}ERROR:${NC} Timeout waiting for filesystem shrink."
  exit 5
fi

# Resize the root partition
fs_blk_cnt=$(sudo tune2fs -l $pi_path-part2 | grep "Block count" | sed "s/^Block count: *//g")
fs_blk_size=$(sudo tune2fs -l $pi_path-part2 | grep "Block size" | sed "s/^Block size: *//g")
fs_kib=$(($fs_blk_cnt*$fs_blk_size/1024))
echo -e "\nShrinking root partition to $fs_kib KiB."
echo ",${fs_kib}KiB" | sudo sfdisk -N2 $pi_path

# Print disk info, get last line, trim whitespace, return 3rd field
end_sector=$(sudo fdisk -l $pi_path | tail -1 | tr -s ' ' | cut -d ' ' -f 3)
sector_size=512
mb_chunks=$(($end_sector*$sector_size/1024**2 + 1)) # +1 because this math truncates
echo $mb_chunks

img_file=$HOME/mn/images/amplipi_1.8.img
sudo dd if=$pi_path of=$img_file bs=1MiB count=$mb_chunks status=progress
sudo chown $USER:$USER $img_file
