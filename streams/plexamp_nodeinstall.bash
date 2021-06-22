#!/bin/bash
# Download Node 9
curl -sL https://deb.nodesource.com/setup_9.x | sudo -E bash -

# Point Nodejs to 9.11.2
sudo apt install nodejs=9.11.2-1nodesource1

# Pin Nodejs to the old version so it isn't updated with "apt upgrade" or similar commands
sudo apt-mark hold nodejs
