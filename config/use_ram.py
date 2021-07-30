#!/usr/bin/python3
# /etc/init.d/use_ram.py
### BEGIN INIT INFO
# Provides:          use_ram.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

import os

web_directory = '/home/pi/web/generated'
src_directory = '/home/pi/config/srcs'

os.system('mkdir -p {}'.format(web_directory))
os.system('sudo mount -osize=100m tmpfs -t tmpfs {}'.format(web_directory))

os.system('mkdir -p {}'.format(src_directory))
os.system('sudo mount -osize=100m tmpfs -t tmpfs {}'.format(src_directory))

print('RAM disk created.')