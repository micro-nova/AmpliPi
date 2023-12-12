#!/usr/bin/env bash

img_file="$HOME/mn/images/amplipi_0.2.1.img"

echo "Creating a loop device for mounting the image"
loopdev=$(sudo losetup --find --show "$img_file")
sudo partprobe $loopdev

echo "Checking filesystems for errors"
sudo fsck -f ${loopdev}p1
sudo fsck -f ${loopdev}p2

echo "Mounting boot and root partitions"
boot_dir=$(mktemp -d)
root_dir=$(mktemp -d)
sudo mount ${loopdev}p1 $boot_dir
sudo mount ${loopdev}p2 $root_dir

echo "Setting up resize2fs on the image"
sudo sed -i 's@$@ init=/usr/lib/raspi-config/init_resize.sh@' $boot_dir/cmdline.txt
sudo wget -qO $root_dir/etc/init.d/resize2fs_once https://raw.githubusercontent.com/RPi-Distro/pi-gen/master/stage2/01-sys-tweaks/files/resize2fs_once
sudo chmod +x $root_dir/etc/init.d/resize2fs_once
#sudo systemctl enable resize2fs_once
sudo ln -s ../init.d/resize2fs_once $root_dir/etc/rc3.d/S01resize2fs_once

echo "Defragmenting the root filesystem"
sudo e4defrag ${loopdev}p2s

echo "Un-mounting boot and root partitions"
sudo umount $boot_dir
sudo umount $root_dir

echo "Shrinking the root filesystem (must check for errors first)"
sudo fsck -f ${loopdev}p2
sudo resize2fs -pM ${loopdev}p2

echo "Shrinking the root filesystem again so resize2fs can"
sudo resize2fs -pM ${loopdev}p2

echo "Shrinking the root partition (ignore partition table read error)"
block_count=$(sudo tune2fs -l ${loopdev}p2 | grep "Block count" | sed "s/^Block count: *//g")
block_size=$(sudo tune2fs -l ${loopdev}p2 | grep "Block size" | sed "s/^Block size: *//g")
sector_size=512 # fdisk uses 512-byte sectors
new_sectors=$(($block_count*$block_size/512))
echo ",$new_sectors" | sudo sfdisk -N2 $loopdev

echo "Checking root filesystem for errors after shrinking"
sudo fsck -f ${loopdev}p2

echo "Removing loop device"
sudo losetup -d $loopdev

# Verify new partition setup
fdisk -l "$img_file"
#Device       Boot  Start      End  Sectors  Size Id Type
#amplipi.img1        8192   532479   524288  256M  c W95 FAT32 (LBA)
#amplipi.img2      532480 11404616 10872137  5.2G 83 Linux

echo "Truncating image file to the new smaller partition size"
last_sector=$(fdisk -l "$img_file" -o End | tail -1)
truncate --size=$[($last_sector+1)*$sector_size] "$img_file"

echo "Compressing image file to $img_file.xz"
xz -9T0 "$img_file"
