#!/usr/bin/env bash
# Program an expander to verify the expansion port's control signals work

nprog=''
if [[ $# > 0 ]]; then
  nprog="-n $1"
fi

cd "$(dirname ${BASH_SOURCE[0]})/../.." # cd to amplipi root dir

# Program master and 1 expansion unit (forced)
passed=false
if venv/bin/python -m amplipi.hw $nprog --flash fw/bin/preamp_1.3.bin; then
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

if [[ $# > 1 ]]; then
  echo "Press any key to exit..."
  read -sn 1
fi
