#!/bin/bash
# Set up directory and pipe
mkdir -p /home/pi/config/srcs/$1
mkfifo /home/pi/config/srcs/$1/metafifo
chmod +x /home/pi/config/srcs/$1/metafifo

# Send relevant logfile data to the translation script
cat /home/pi/config/srcs/$1/metafifo | grep --line-buffered -w 'CurrentTrackMetaData\|TransportState' | /home/pi/scripts/dlna_meta.py $1
