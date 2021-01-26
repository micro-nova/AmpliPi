#!/bin/bash
# Start the metadata service with argument $1 being the source number #
cat /home/pi/config/srcs/$1/shairport-sync-metadata | shairport-sync-metadata-reader | /home/pi/scripts/sp_meta.py $1
