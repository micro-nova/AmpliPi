#!/bin/bash
#/usr/local/bin

dbus-monitor --system "interface='org.freedesktop.UDisks2.Filesystem'" |
while read -r line; do
    # Execute your bash script when a drive is mounted
    /usr/local/bin/edit_media_directories.sh
done
