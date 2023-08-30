#!/usr/bin/env bash

cd "$(dirname ${BASH_SOURCE[0]})" # python script is in same folder
passed=false
if ./../../venv/bin/python config_streamer.py; then
  passed=true
fi

RED='\033[0;31m'
GRN='\033[0;32m'
NC='\033[0m'
if $passed; then
  echo -e "${GRN}TEST PASSED${NC}"
else
  echo -e "${RED}TEST FAILED${NC}"
fi

echo "Press any key to exit..."
read -sn 1
