#!/bin/bash
# Clear out any previous album cover images, then navigate to the proper directory #
rm -r -f /home/pi/web/static/imgs/srcs/$1/
mkdir -p /home/pi/web/static/imgs/srcs/$1/
cd /home/pi/web/static/imgs/srcs/$1/

# Start the metadata service with argument $1 being the source number #
cat /home/pi/config/srcs/$1/shairport-sync-metadata | shairport-sync-metadata-reader | /home/pi/scripts/sp_meta.py $1
