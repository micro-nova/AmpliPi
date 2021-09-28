#!/usr/bin/env bash
# Mount a Pi compute module via the service USB port

printf "Attempting to mount the Raspberry Pi via the USB service port.
usbboot will be placed at $HOME/.amplipi

Make sure the USB connection to the service port was made before
powering on the AmpliPi, e.g.:

  1. Turn off AmpliPi
  2. Plug a USB cable into the Service port and into the host computer.
  3. Turn on AmpliPi
  4. Run this script

"

#current_dir="$(dirname "$(realpath ${BASH_SOURCE[0]})")"

usboot_dir="$HOME/.amplipi/usbboot"
if ! [ -d $usboot_dir ]; then
  echo "Downloading Raspberry Pi boot"
  git clone --depth=1 https://github.com/raspberrypi/usbboot $usboot_dir
  pushd $usboot_dir

  # Install dependencies as necessary
  inst=false
  deps="libusb-1.0-0-dev make gcc"
  for dep in $deps; do
    dpkg-query -s $dep 1>/dev/null 2>/dev/null || inst=true
  done
  if $inst; then
    sudo apt update
    sudo apt install $deps
  fi

  # Build
  make
  popd
fi

# Attempt to boot Pi
connected=false
sudo $usboot_dir/rpiboot

# Wait for the Raspberry Pi to connect
for i in {1..10}; do
  sleep 0.5
  if lsusb -d 0a5c:0001 >/dev/null; then
    printf "Connected to Raspberry Pi!\n\n"
    connected=true
    break
  fi
done
if ! $connected; then
  echo "Error: Failed to connect to Raspberry Pi"
fi

# If any args were passed, then treat this as a hardware test
if [[ $# > 0 ]]; then
  RED='\033[0;31m'
  GRN='\033[0;32m'
  NC='\033[0m'
  if $connected; then
    echo -e "${GRN}TEST PASSED${NC}"
  else
    echo -e "${RED}TEST FAILED${NC}"
  fi

  echo "Press any key to exit..."
  read -sn 1
fi
