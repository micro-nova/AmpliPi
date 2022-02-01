#!/usr/bin/env bash
# Program an expander to verify the expansion port's control signals work

# If any argument was passed, assume it's the number of units to program.
nprog=''
if [[ $# > 0 ]]; then
  nprog="--num-units $1"
fi

cd "$(dirname ${BASH_SOURCE[0]})/../.." # cd to amplipi root dir

# Program master and 1 expansion unit (forced)
passed=false
if ./scripts/program_firmware $nprog fw/bin/preamp_1.4.bin; then
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
