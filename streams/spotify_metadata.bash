#!/bin/bash
# Pipe Spotify metadata into the relevant python script for translation

# Establish the streams directory as the location of the scripts
scripts_dir="$(realpath $(dirname "$0"))"
test -d $scripts_dir || exit 1 ;

# Listen on the provided port, sending updates to the script
if ! which netcat; then
  echo "installing netcat"
  sudo apt update && sudo apt install -y netcat
fi

nc -u -l $1 | python3 ${scripts_dir}/spot_meta.py $1
