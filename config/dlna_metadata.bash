#!/bin/bash
# Set up directory and pipe
mkdir -p /home/pi/config/dlna/$1
mkfifo /home/pi/config/dlna/$1/logfile
chmod +x /home/pi/config/dlna/$1/logfile

# Send relevant logfile data to the translation script
cat logfile | grep -w 'CurrentTrackMetaData\|TransportState' | /home/pi/scripts/dlna_meta.py $1