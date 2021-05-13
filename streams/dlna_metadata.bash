#!/bin/bash
# Set up directory and pipe
mkdir -p $1
mkfifo $1/metafifo
chmod +x $1/metafifo

# Send relevant logfile data to the translation script
cat $1/metafifo | grep --line-buffered -w 'CurrentTrackMetaData\|TransportState' | python3 /home/pi/amplipi-dev/streams/dlna_meta.py $1
