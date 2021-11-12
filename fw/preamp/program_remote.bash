#!/usr/bin/env bash
# This script assumes a directory 'amplipi-test' exists on the remote AmpliPi
# that has the prerequisites to flashing the preamp already setup.
fw_bin=${1:-preamp_bd.bin}
remote_host=${2:-amplipi.local}
remote_dir=${3:-amplipi-dev}

echo "Programming $fw_bin on $remote_host using ~/$remote_dir"
#echo "Building firmware locally then programming on $remote_host using ~/$remote_dir"
#cd "$(dirname "${BASH_SOURCE[0]}")"
#mkdir -p build
#cd build
#cmake ..
#make -j
scp $fw_bin pi@$remote_host:$remote_dir/
ssh pi@$remote_host -- "cd $remote_dir; venv/bin/python -m amplipi.hw --flash preamp_bd.bin"
