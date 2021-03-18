#!/bin/bash
set -e # stop on error

# get directory that the script exists in
cd "$( dirname "$0" )"

if [[ ! -d '/home/pi' ]] ; then
  # copy this script to the amplipi
  # check if RPI_IP_ADDRESS is set
  if [[ -z "${RPI_IP_ADDRESS}" ]]; then
    echo ""
    echo "Please set RPI_IP_ADDRESS, for example:"
    echo -e '\033[1;32mexport RPI_IP_ADDRESS=amplipi.local\033[0m'
    echo "for ssh key access"
    echo -e '\033[1;32mexport RPI_IP_ADDRESS=pi@amplipi.local\033[0m'
    echo ""
    exit 1
  fi
  echo "copying this script to the amplipi"
  scp "$0" ${RPI_IP_ADDRESS}:
  echo "building the files on the amplipi"
  x=$(ssh $RPI_IP_ADDRESS "source generate_bins.bash | grep 'success=' | sed 's/success=//'")
  if [[ -z "$x" ]] ; then
    echo "failed to build binaries, try running this script directly on the pi to debug"
    exit -1
  fi
  scp $RPI_IP_ADDRESS:$x .
  # TODO: copy files out of the temp directory
  exit
fi

git_installed=$(sudo apt list --installed 2> /dev/null | grep git/ -c)
if [ 0 -eq "${git_installed}" ]; then
  echo "installing git"
  sudo apt update && sudo apt install -y git
else
  echo "git already installed"
fi

# build-essential and autoconf are required to make the metadata reader
be_installed=$(sudo apt list --installed 2> /dev/null | grep build-essential -c)
if [ 0 -eq "${be_installed}" ]; then
  echo "installing build-essential"
  sudo apt update && sudo apt install -y build-essential
else
  echo "build-essential already installed"
fi

autoconf_installed=$(sudo apt list --installed 2> /dev/null | grep autoconf -c)
if [ 0 -eq "${autoconf_installed}" ]; then
  echo "installing autoconf"
  sudo apt update && sudo apt install -y autoconf
else
  echo "autoconf already installed"
fi

# build shairport-sync-metadata-reader
pushd $(mktemp --directory)
git clone https://github.com/micronova-jb/shairport-sync-metadata-reader.git
cd shairport-sync-metadata-reader
autoreconf -i -f
./configure
make

# report success, with the filepath to the built binary (so the remote version of this script can copy the file)
echo "success=$(pwd)/shairport-sync-metadata-reader"
popd
