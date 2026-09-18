#!/bin/bash
# This script runs after a support tunnel comes down. Right now, 
# it only prevents Avahi from advertising using the wireguard interface
# $1 is the wireguard interface to remove

# The avahi-daemon.conf follows an ini-style convention; Python's
# configparser makes it easy to safely add & remove contents in a particular
# section, and "shelling out" gives us an opportunity to use `sudo`.
echo "import configparser
import sys
config = configparser.ConfigParser()
config.read('/etc/avahi/avahi-daemon.conf')
if not config.has_section('server'):
  config.add_section('server')
deny = set(config['server'].get('deny-interfaces').split(','))
try:
  deny.remove('${1}')
except KeyError as e:
  print(f'${1} not in config; exiting early.')
  sys.exit(1)
deny_str = ''
for i, d in enumerate(deny):
  deny_str += f'{d}'
  deny_str += ',' if i != (len(deny) - 1) else ''
config['server']['deny-interfaces'] = deny_str
with open('/etc/avahi/avahi-daemon.conf', 'w') as f:
  config.write(f, space_around_delimiters=False)
" | sudo python3 -

sudo systemctl restart avahi-daemon
