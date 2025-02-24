#!/bin/bash


if [ $(whoami) != "root" ] ; then
  echo "Please run as root."
  exit
fi

# perhaps this is the least commonly used util. perhaps not. 
if [ "$(dpkg --get-selections qemu-user-static)" ] ; then
  apt install binfmt-support qemu-user-static
fi

chroot root /bin/bash
rm -v root/root/.bash_history
