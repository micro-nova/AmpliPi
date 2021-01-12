#!/bin/bash

sudo systemctl stop shairport-sync.service

for i in 0 1 2 3
do
  sudo systemctl restart shairport-sync@ch${i}.service
done
