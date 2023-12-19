#!/usr/bin/env bash
# This script scrapes, cleans up, and prepares an AmpliPi image off an existing appliance.

function help() {
  echo "Usage: ${0} IMAGE_FILE"
}

if [ -z ${1} ] ; then
  help
  exit 1
fi

RED='\033[0;31m'
GRN='\033[0;32m'
NC='\033[0m'

set -u # bails if there are any unset variables

img_file="${1}"
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
if [ -z ${pi_path} ]; then
  echo -e "\n${RED}ERROR:${NC} No Raspberry Pi device found at $disk_base_path*"
  read -p "Press any key to continue..." -sn 1
  echo "" # newline
  exit 2
else
  echo -e "Raspberry Pi device found at $pi_path"
fi


## PRE-SCRAPE

# Pi found! Mount root directory.
root_dir=$(mktemp -d)
sudo mount ${pi_path}-part2 $root_dir

echo -e "\nRemoving all log files"
sudo find ${root_dir}/var/log -type f -delete

echo -e "\nRemoving apt cache files"
sudo find ${root_dir}/var/cache/apt/archives -type f -delete

echo -e "\nRemoving various old detritus."
sudo rm -vr ${root_dir}/var/swap ${root_dir}/home/pi/amplipi-dev/web/node_modules ${root_dir}/home/pi/amplipi-*.tar.gz

echo "Resetting password to default"
set -e # bail if chpasswd isn't happy, for any number of reasons
echo "pi:raspberry" | sudo chpasswd --crypt-method SHA512 -R ${root_dir}
set +e

echo "Setting a unique /etc/machine-id"
# TODO: do this on first boot, not during image creation
old_id=$(cat ${root_dir}/etc/machine-id)
echo "Old id=$old_id"
sudo rm ${root_dir}/etc/machine-id
sudo dbus-uuidgen --ensure=$root_dir/etc/machine-id

echo "Cleaning up /home/pi"
rm -vf ${root_dir}/home/pi/.config/amplipi/*
rm -vf ${root_dir}/home/pi/amplipi-dev/house.json ${root_dir}/home/pi/amplipi-dev/house.json.bak
cat /dev/null > ${root_dir}/home/pi/.bash_history
sudo umount ${root_dir}
sudo umount ${pi_path}-part2 # in case udev wants to play


# Mount boot partition and ensure first_boot_partitioning is configured to run at boot
boot_dir=$(mktemp -d)
sudo mount $pi_path-part1 $boot_dir
# Remove any existing init= args, and add init_resize.sh as the init binary
echo "Configuring resize2fs to run at boot."
sudo sed -i 's/init=.* //;s/ init=.*$//' $boot_dir/cmdline.txt
sudo sed -i 's@$@ init=/home/pi/amplipi-dev/scripts/first_boot_partitioning@' $boot_dir/cmdline.txt
sudo umount $boot_dir
sudo umount ${pi_path}-part1 # in case udev wants to play too

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
