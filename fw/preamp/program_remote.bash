#!/usr/bin/env bash
# This script assumes a directory 'amplipi-test' exists on the remote AmpliPi
# that has the prerequisites to flashing the preamp already setup.
remote_host=${1:-amplipi105.local}
remote_dir=${2:-amplipi-test}

echo "Building firmware locally then programming on $remote_host using ~/$remote_dir"
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p build
cd build
cmake ..
make -j
scp preamp_bd.bin pi@$remote_host:$remote_dir
ssh pi@$remote_host -- "cd amplipi-test; venv/bin/python -m amplipi.hw --flash preamp_bd.bin"
