#!/bin/bash
#/usr/local/bin
dbus-monitor --system "interface='org.freedesktop.UDisks2.Filesystem'" |
while read -r line; do
  # Execute when a drive is mounted
  source /home/pi/amplipi-dev/venv/bin/activate
  python /usr/local/bin/edit_media_directories.py
done
