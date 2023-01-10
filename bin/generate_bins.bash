#!/bin/bash
set -e # stop on error

# get directory that the script exists in
cd "$( dirname "$0" )"

function build {
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

  # install a bunch of packages required by shaairport-sync with airplay2 support
  sudo apt install --no-install-recommends xmltoman automake libtool \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev \
    libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev xxd libgcrypt-dev

  pushd $(mktemp --directory)
    # build shairport-sync-metadata-reader
    git clone https://github.com/micronova-jb/shairport-sync-metadata-reader.git
    cd shairport-sync-metadata-reader
    autoreconf -if
    ./configure
    make
    cd ..

    # build shairport-sync with airplay2 support
    git clone https://github.com/mikebrady/shairport-sync.git
    cd shairport-sync
    autoreconf -if
    ./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2 --with-metadata --with-mpris-interface
    make

    # copy the generated bins to a common directory
    mkdir -p ../bins
    cd ../bins
    cp ../shairport-sync-metadata-reader/shairport-sync-metadata-reader .
    cp ../shairport-sync/shairport-sync ./shairport-sync-ap2

    # clean then build shairport-sync without airplay2 support
    cd ../shairport-sync
    make clean
    ./configure --sysconfdir=/etc --with-alsa --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-metadata --with-mpris-interface
    make

    # copy the generated bins to a common directory
    cd ../bins
    cp ../shairport-sync/shairport-sync .

    # report success, with the filepath to the built binary (so the remote version of this script can copy the file)
    echo "success=$(pwd)"

    # export the working directory so we can use it locally
    export bin_dir=$(pwd)
  popd
}

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
  scp generate_bins.bash ${RPI_IP_ADDRESS}:
  echo "building the files on the amplipi"
  x=$(ssh $RPI_IP_ADDRESS "source generate_bins.bash | grep 'success=' | sed 's/success=//'")
  if [[ -z "$x" ]] ; then
    echo "failed to build binaries, try running this script directly on the pi to debug"
    exit -1
  fi
  scp $RPI_IP_ADDRESS:$x/* arm/
  # build files locally
  build
  cp $bin_dir/* x64/
  echo "done building bins!"
  exit
fi

# build binaries on the pi
build
