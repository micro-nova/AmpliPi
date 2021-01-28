#!/bin/bash

# get directory that the script exists in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# fix the line endings of the scripts copied over (thanks windows) (NOTE: we need to force LF line endings on this file)
d2u_installed=$(sudo apt list --installed 2> /dev/null | grep dos2unix -c)
if [ 0 -eq "${d2u_installed}" ]; then
  echo "installing dos2unix"
  sudo apt update && sudo apt install -y dos2unix
fi
dos2unix ${SCRIPT_DIR}/*

# make some scripts executable
chmod +x eventcmd.sh shairport_metadata.bash

# configure shairport-sync on pi for multi instance support and disable its daemon
sp_installed=$(sudo apt list --installed 2> /dev/null | grep shairport-sync -c)
if [ 0 -eq "${sp_installed}" ]; then
  echo "installing shairport-sync"
  sudo apt update && sudo apt install -y shairport-sync
  # disable and stop its daemon
  sudo systemctl stop shairport-sync.service
  sudo systemctl disable shairport-sync.service
fi

# configure pianobar on pi
pb_installed=$(sudo apt list --installed 2> /dev/null | grep pianobar -c)
if [ 0 -eq "${pb_installed}" ]; then
  echo "installing pianobar"
  sudo apt update && sudo apt install -y pianobar
else
  echo "pianobar already installed"
fi

# configure raspotify on pi and disable its daemon
rs_installed=$(sudo apt list --installed 2> /dev/null | grep pianobar -c)
if [ 0 -eq "${rs_installed}" ]; then
  echo "installing raspotify"
  sudo apt update && sudo apt install -y raspotify
  # disable and stop its daemon
  sudo systemctl stop raspotify.service
  sudo systemctl disable raspotify.service
else
  echo "raspotify already installed"
fi

# TODO: add other dependencies

# TODO: check if boot config changed, copy over if necessary and ask user to restart

echo "updating system alsa config"
sudo cp ${SCRIPT_DIR}/asound.conf /etc/asound.conf
