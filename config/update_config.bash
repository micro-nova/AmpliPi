#!/bin/bash

# configure shairpprt-sync on pi for multi instance support
sp_installed=$(sudo apt list --installed 2> /dev/null | grep shairport-sync -c)
if [ 0 -eq "${sp_installed}" ]; then
  echo "installing shairport-sync"
  sudo apt update && sudo apt install -y shairport-sync
fi
echo "updating system alsa config"
sudo cp asound.conf /etc/asound.conf

# make scripts executable
chmod +x eventcmd.sh shairport_metadata.bash


# TODO: configure other systems on rpi?
