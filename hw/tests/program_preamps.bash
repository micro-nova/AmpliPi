#!/usr/bin/env bash
# Program an expander to verify the expansion port's control signals work

# If any argument was passed, assume it's the number of units to program.
nprog=''
if [[ $# -gt 0 ]]; then
  nprog="--num-units $1"
fi

# cd to amplipi root dir, exit on failure
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

# Get latest firmware binary
bin_file="$(find fw/bin -type f | sort | tail -1)"

# Program the latest released firmware
passed=false
if ./scripts/program_firmware $nprog "$bin_file"; then
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
read -rsn 1
