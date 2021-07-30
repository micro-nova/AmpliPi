# Copy from a Pi

## USB Boot
Since there is no SD card to pull out,
the USB Boot project is required to mount the Pi's filesystem.
To download and build the project run the following:
```sh
git clone --depth=1 https://github.com/raspberrypi/usbboot
cd usbboot
sudo apt install libusb-1.0-0-dev make gcc
make
```

Now remove power from the AmpliPi, plug a USB cable into the service port,
and then power up the AmpliPi. Finally, run
```sh
sudo ./rpiboot
```

You should see some messages while `rpiboot` connects to the Pi,
and finally the message "`Second stage boot server done`".
Now the Pi should be accessible as `/dev/sdX` where `X` is whatever
the next available drive letter was.
For a more reliable name, you can also access the Pi via
`/dev/disk/by-id/usb-RPi-MSD...`.
The final part of the disk id is unique to each Pi but will remain the same
every time it is added by `rpiboot`.

## Option 1: Copy Full 32 GiB Image
Unfortunately, this will take upwards of an hour to copy,
but it requires no file system changes.
```sh
sudo dd if=/dev/sdX of=amplipi.img bs=4MiB status=progress
```

Compressing the image on the fly can be done to save disk space,
although it won't save any time.
```sh
sudo dd if=/dev/sdaX bs=4MiB | gzip > amplipi.img.gz
```

## Option 2: Shrink then Copy
To save time copying, shrink the root partition so that unused space isn't copied.
While the Pi is mounted with `rpiboot`, use the partition manager of your choice to shrink the root partition as far as possible.
GParted is a good graphical partitioning tool.
Through testing it only seems possible to shrink the root partition to ~5 GB
when about 4 GB are in use.

Once shrunk, find the "End" of the second partion from `fdisk`:
```sh
fdisk -l /dev/sdX
```

The blocksize for the eMMC on the Compute Module 3+ is 512 bytes,
again from the output of the above `fdisk` command.
To perform the actual copy use `dd`'s `count` argument to copy `count`
number of blocks.
The following is an example where the End sector was 10158079.

```sh
end=10158079
bs=512
sudo dd if=/dev/sdX of=amplipi.img bs=1MiB count=$[($end+1)*$bs/1024/1024] status=progress
```

# Accessing an Image File
If it is necessary to add/remove files from an image, or to change partition
sizes, the stored image file can be mounted directly on another computer.

Assuming image is `amplipi.img` run
```sh
loopdev=$(sudo losetup --find --show amplipi.img)
sudo partprobe $loopdev
```

## Mounting
Now the image will be accessible as `/dev/loopX`; the full path is stored in `$loopdev`.
To mount the boot partition use
```sh
sudo mount ${loopdev}p1 /mnt/pi-boot
```
and to mount the root partition use
```sh
sudo mount ${loopdev}p2 /mnt/pi-root
```
The partitions can be mounted to any directory, but the above commands assume
`/mnt/pi-boot` and `/mnt/pi-root` exist.

## Modifying Partitions
A partition manager can shrink/grow `${loopdev}p2` as required.
If shrinking a partition, the image can be shrunk to fit with `truncate`.
First find the "End" of `amplipi.img` and the block size:
```sh
fdisk -l amplipi.img
```

Assuming the end of the image's second partition was at 10158079,
use the following to shrink the image:
```sh
end=10158079
bs=512
truncate --size=$[($end+1)*$bs] amplipi.img
```

Once done editing the image, remove the loop device
```sh
sudo losetup -d $loopdev
```

# Writing to a Pi
Plug in a USB cable to the service port and power up.
Use `rpiboot` to get `/dev/sdX`
Copy the image, assuming it is named `amplipi.img`:
```sh
sudo dd if=amplipi.img of=/dev/sdX bs=4MiB status=progress
```

## Expanding a Shrunk Filesystem
If the filesystem was previously shrunk to save space,
`raspi-config` can expand the filesystem back.
```sh
ssh pi@amplipi.local
sudo raspi-config --expand-rootfs
cat /dev/null > ~/.bash_history && history -c && exit
```
TODO: Utilize the expand-once feature on the Raspberry Pi OS images.

### Hide your traces
To keep the clean state of the image, remove any SSH keys
and command history.
```
rm ~/.ssh/authorized_keys
cat /dev/null > ~/.bash_history && history -c && exit
```
