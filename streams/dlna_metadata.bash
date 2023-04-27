#!/bin/bash
# use *nix utils to pass the relevant data from DLNA's metadata pipe to our simple parser

# Set up directory and pipe
mkdir -p $1
mkfifo $1/metafifo
chmod +x $1/metafifo

# Get the stream scripts directory (dlna_meta.py is located there)
scripts_dir="$(realpath $(dirname "$0"))"
echo "script dir=$scripts_dir"
test -d $scripts_dir || exit 1 ;

# Send relevant logfile data to the translation script
# we use tail -f to continue reading the pipe "past" the EOF
# this allows us to keep processing new updates without having to poll the pipe
tail -f $1/metafifo | grep --line-buffered -w 'CurrentTrackMetaData\|TransportState' | python3 ${scripts_dir}/dlna_meta.py $1
