#!/usr/bin/env bash

img_file=$HOME/mn/images/amplipi_0.2.1.img
disk_base_path=/dev/disk/by-id/usb-RPi-MSD

function check_for_pi() {
  # Check for Raspberry Pi device path
  local path=$(ls $disk_base_path* 2>/dev/null | head -n1)
  if [ ! -z $path ]; then
    # Check for boot and root partition
    if [[ -e $path-part1 ]] && [[ -e $path-part2 ]]; then
      echo "$path"
      return 0
    fi
  fi
  return 1
}

# Connect to amplipi eMMC.
# The Pi must have been powered on with the service USB plugged in.
if ! pi_path=$(check_for_pi); then
  sudo rpiboot
  printf "\nWaiting for the Pi's eMMC to show up"
  for i in {1..10}; do
    printf "."
    sleep 0.5
    if pi_path=$(check_for_pi); then
      break
    fi
  done
  printf "\n"
fi

# Error out if no Pi found
if [ -z $pi_path ]; then
  echo -e "\n${RED}ERROR:${NC} No Raspberry Pi device found at $disk_base_path*"
  read -p "Press any key to continue..." -sn 1
  echo "" # newline
  exit 2
else
  echo -e "Raspberry Pi device found at $pi_path"
fi

# Pi found! Mount root directory.
root_dir=$(mktemp -d)
sudo mount $pi_path-part2 $root_dir

echo -e "\nSetting up resize2fs_once"
sudo wget -qO $root_dir/etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
sudo chmod +x $root_dir/etc/init.d/resize2fs_once
sudo ln -s ../init.d/resize2fs_once $root_dir/etc/rc3.d/S01resize2fs_once

echo -e "\nRemoving all log files"
sudo find $root_dir/var/log -type f -exec rm {} \;

echo "Resetting password to default"
# TODO set password to 'raspberry'

echo "Setting a unique /etc/machine-id"
old_id=$(cat $root_dir/etc/machine-id)
echo "Old id=$old_id"
sudo rm $root_dir/etc/machine-id
sudo dbus-uuidgen --ensure=$root_dir/etc/machine-id

echo "Cleaning up /home/pi"
rm -f $root_dir/home/pi/.config/amplipi/default_password.txt
cat /dev/null > ~/.bash_history
sudo umount $root_dir

# Mount boot partition and ensure init_resize.sh is configured to run at boot
boot_dir=$(mktemp -d)
sudo mount $pi_path-part1 $boot_dir
# Remove any existing init= args, and add init_resize.sh as the init binary
echo "Configuring resize2fs to run at boot."
sudo sed -i 's/init=.* //;s/ init=.*$//' $boot_dir/cmdline.txt
sudo sed -i 's@$@ init=/usr/lib/raspi-config/init_resize.sh@' $boot_dir/cmdline.txt
sudo umount $boot_dir

echo -e "\nRunning fsck on boot filesystem just in case."
sudo fsck -f $pi_path-part1
if [[ $? -gt 1 ]]; then
  echo "\n${RED}ERROR:${NC} Couldn't auto-fix AmpliPi's boot filesystem, exiting."
  exit 3
fi

echo -e "\nRunning fsck on root filesystem - required by resize2fs."
sudo fsck -f $pi_path-part2
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

# Resize the root partition
fs_blk_cnt=$(sudo tune2fs -l $pi_path-part2 | grep "Block count" | sed "s/^Block count: *//g")
fs_blk_size=$(sudo tune2fs -l $pi_path-part2 | grep "Block size" | sed "s/^Block size: *//g")
if [[ -z $fs_blk_cnt ]] || [[ -z $fs_blk_size ]]; then
  echo -e "\n${RED}ERROR:${NC} Couldn't read block count or size."
  exit 5
fi
sector_size=512
new_sectors=$(($fs_blk_cnt*$fs_blk_size/$sector_size))

# Wait for filesystem changes to be complete (timeout after 10s)
reread=false
for i in {1..100}; do
  sleep 0.1
  if sudo blockdev --rereadpt $pi_path 2>/dev/null; then
    reread=true
    break
  fi
done
if ! $reread; then
  echo -e "\n${RED}ERROR:${NC} Timeout waiting for filesystem shrink."
  exit 6
fi

echo -e "\nShrinking root partition to $new_sectors $sector_size-byte sectors."
echo ",$new_sectors" | sudo sfdisk -N2 $pi_path

# Print disk info, get last line, trim whitespace, return 3rd field
echo -e "\nRoot partition shrunk, finding end of used space on disk."
end_sector=$(sudo fdisk -l $pi_path | tail -1 | tr -s ' ' | cut -d ' ' -f 3)
mb_chunks=$(($end_sector*$sector_size/1024**2 + 1)) # +1 because this math truncates

echo -e "\nCopying $mb_chunks MiB from $pi_path"
echo " to $img_file"
sudo dd if=$pi_path of=$img_file bs=1048576 count=$mb_chunks status=progress
sudo chown $USER:$USER $img_file
