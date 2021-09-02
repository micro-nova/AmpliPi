#!/usr/bin/env bash

test_timeout=10

echo "Stopping any running display service."
systemctl --user stop amplipi-display

echo "Starting display in test mode, touch screen after logo clears."
echo "If no touch is detected within $test_timeout seconds, the test will fail."
cd "$(dirname ${BASH_SOURCE[0]})/../.." # cd to amplipi root dir
passed=false
if venv/bin/python -m amplipi.display.display --test-timeout $test_timeout; then
  passed=true
fi

echo "Restarting existing display service before exiting."
systemctl --user start amplipi-display

RED='\033[0;31m'
GRN='\033[0;32m'
NC='\033[0m'
if $passed; then
  echo -e "${GRN}TEST PASSED${NC}"
else
  echo -e "${RED}TEST FAILED${NC}"
fi
