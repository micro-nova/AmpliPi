#!/usr/bin/env bash

cleanup () {
  echo ""
  echo "Unmounting drive and exiting."
  sudo umount /tmp/drive
  exit 0
}
trap cleanup SIGINT SIGTERM

# Expects a flash drive on /dev/sda
echo "Waiting for a flash drive to be plugged in..."
while [ ! -b /dev/sda ]; do
  sleep 0.5
done
sleep 1

# Mount drive
echo "Mounting drive..."
mkdir -p /tmp/drive
sudo mount /dev/sda1 /tmp/drive

# Loop and do minimal writing
echo "Writing to drive in loop..."
while true; do
  sudo touch /tmp/drive/data
  sleep 0.5
done

# Unmount drive and exit
cleanup
