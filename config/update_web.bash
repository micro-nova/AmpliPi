#!/bin/bash

echo "Updating AmpliPi's Nginx Unit webserver configuration"

# exit on error
set -e

# make sure the webserver is running
test 'active' != $(systemctl is-active unit.service) && sudo systemctl restart unit.service

# update the flask application configuration, then force a configuration reload
if [ 'active' == $(systemctl is-active unit.service) ]; then
  sudo curl -s -X PUT --data-binary @/home/pi/config/unit.json --unix-socket /var/run/control.unit.sock http://localhost/config
  sudo curl -s -X PUT -d '"'$(date +"%s")'"' --unix-socket /var/run/control.unit.sock http://localhost/config/applications/flask/environment/APPGEN
else
  echo "Error: Failed to start web server, is it installed?" >&2
fi
