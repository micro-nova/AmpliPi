#!/bin/bash

if [ $(whoami) != "root" ] ; then
  echo "Please become root."
  exit
fi

set -eu

sync
umount root/boot
umount root
losetup -D
