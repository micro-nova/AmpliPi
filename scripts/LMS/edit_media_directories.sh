#!/bin/bash
#/usr/local/bin

sudo chmod 766 /var/lib/squeezeboxserver/prefs/server.prefs

source /home/pi/amplipi-dev/venv/bin/activate

python /usr/local/bin/edit_media_directories.py
