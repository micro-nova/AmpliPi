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
  dir=$(ssh $RPI_IP_ADDRESS "source $0 | grep 'success=' | sed 's/success=//'")
  if [[ -z "$dir" ]] ; then
    echo "failed to build binaries, try running this script directly on the pi to debug"
    exit -1
  fi
  scp $RPI_IP_ADDRESS:$dir/unit_*.deb .
  scp $RPI_IP_ADDRESS:$dir/unit-python3.7*.deb .
  exit
fi

pushd $(mktemp --directory)
git clone https://github.com/nginx/unit
pushd unit/pkg
git checkout 1.22.0 # latest version
sudo apt update
# these deps were reported by a make failure on the line below, they are definitely dependent on what version of raspbian you are running
sudo apt install -y php-dev libphp-embed python3.7-dev python3.8-dev golang libperl-dev ruby-dev ruby-rack openjdk-8-jdk-headless openjdk-8-jdk-headless openjdk-11-jdk-headless libpcre2-dev
make deb

# report success, with the filepath to the built binary (so the remote version of this script can copy the file)
echo "success=$(pwd)"
popd
popd
