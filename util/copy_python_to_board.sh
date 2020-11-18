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

# create directories if they don't exists
ssh $RPI_IP_ADDRESS "mkdir -p ${RPI_PYTHON_FOLDER}/ethaudio"
ssh $RPI_IP_ADDRESS "mkdir -p ${RPI_PYTHON_FOLDER}/tests"
ssh $RPI_IP_ADDRESS "mkdir -p ${RPI_PYTHON_FOLDER}/../config"

sed -i 's/DISABLE_HW = True/DISABLE_HW = False/' $SCRIPT_DIR/../python/ethaudio/api.py

# copy stuff to board
scp $SCRIPT_DIR/../python/*.sh                      $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/
scp $SCRIPT_DIR/../python/*.py                      $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/
scp $SCRIPT_DIR/../python/ethaudio/*.py             $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/ethaudio/
scp $SCRIPT_DIR/../python/tests/*.py                $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/tests/
# copy config files that need to be moved with sudo, then call a script to move/configure them
scp $SCRIPT_DIR/../config/*.json                    $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/../config/
scp $SCRIPT_DIR/../config/asound.conf               $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/../config/
scp $SCRIPT_DIR/../config/update_config.bash        $RPI_IP_ADDRESS:${RPI_PYTHON_FOLDER}/../config/
ssh $RPI_IP_ADDRESS "cd ${RPI_PYTHON_FOLDER}/../config && ./update_config.bash"

sed -i 's/DISABLE_HW = False/DISABLE_HW = True/' $SCRIPT_DIR/../python/ethaudio/api.py
