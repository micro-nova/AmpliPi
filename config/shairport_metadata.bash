#!/bin/bash
# Clear out any previous album cover images, then navigate to the proper directory #
src="$1"
if ((src < 0 || src >= 4));
then
    exit 1;
fi
rm -r -f /home/pi/web/static/imgs/srcs/$1/
mkdir -p /home/pi/web/static/imgs/srcs/$1/
cd /home/pi/web/static/imgs/srcs/$1/

# Start the metadata service with argument $1 being the source number #
cat /home/pi/config/srcs/$1/shairport-sync-metadata | shairport-sync-metadata-reader | /home/pi/scripts/sp_meta.py $1
