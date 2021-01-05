#!/bin/bash

# get directory that the script exists in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# check if RPI_IP_ADDRESS is set
if [[ -z "${RPI_IP_ADDRESS}" ]]; then
  echo ""
  echo "Please set RPI_IP_ADDRESS, for example:"
  echo -e '\033[1;32mexport RPI_IP_ADDRESS=192.168.0.140\033[0m'
  echo "for ssh key access"
  echo -e '\033[1;32mexport RPI_IP_ADDRESS=pi@192.168.0.140\033[0m'
  echo ""
  exit 1
fi

# Python folder on EthAudio controller
RPI_PYTHON_FOLDER=/home/pi/python

# copy stuff to board
scp $SCRIPT_DIR/../python/static/*                  $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/static/
