#!/bin/bash

echo "Updating AmpliPi's Nginx Unit webserver configuration"

# exit on error
set -e

# make sure the webserver is running
test 'active' != $(systemctl is-active unit.service) && sudo systemctl restart unit.service

# update the flask application configuration, then force a configuration reload
if [ 'active' == $(systemctl is-active unit.service) ]; then
  # set the configuration to nothing
  sudo curl -s -X PUT -d '{}' --unix-socket /var/run/control.unit.sock http://localhost/config
  # update the server configuration
  sudo curl -s -X PUT --data-binary @/home/pi/config/webserver.conf --unix-socket /var/run/control.unit.sock http://localhost/config
else
  echo "Error: Failed to start web server, is it installed?" >&2
fi
