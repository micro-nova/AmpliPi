#!/bin/bash

function help() {
  echo "${0}: mounts an AmpliPi disk image into the relative directory 'root'"
  echo "usage: ${0} [disk image]"
}

if [ -z ${1} ]; then
  help
  exit
fi

if [ $(whoami) != "root" ] ; then
  echo "Please become root."
  exit
fi

set -eu

lo=$(losetup --find --show --partscan ${1})

mkdir -p root/boot
mount ${lo}p2 root
mount ${lo}p1 root/boot
