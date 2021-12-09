#!/usr/bin/env bash
# Program an expander to verify the expansion port's control signals work

# First argument is the manual heat test timeout. Default to 60s
timeout=${1:-60}

print_result () {
  RED='\033[0;31m'
  GRN='\033[0;32m'
  NC='\033[0m'
  if $1; then
    echo -e "${GRN}$2${NC}"
  else
    echo -e "${RED}$2${NC}"
  fi
}

cmd="venv/bin/python hw/tests/preamp.py"
success=true

cd "$(dirname ${BASH_SOURCE[0]})/../.." # cd to amplipi root dir
$cmd -q

echo "Are the fans off?"
select yn in Yes No; do
  case $yn in
    Yes ) print_result true "Succeeded"; break;;
    No ) print_result false "Failed"; success=false; break;;
  esac
done
echo

$cmd -qf

echo "Are the fans on?"
select yn in Yes No; do
  case $yn in
    Yes ) print_result true "Succeeded"; break;;
    No ) print_result false "Failed"; success=false; break;;
  esac
done
echo

echo "Testing voltage and temperature readings"
if $cmd -qft; then
  print_result true "Succeeded"
else
  print_result false "Failed"
  success=false
fi
echo

echo "Heat up an amp heatsink, this test will wait until temp has risen 5C."
if $cmd -q --heat $timeout; then
  print_result true "Succeeded"
else
  print_result false "Failed"
  success=false
fi
echo

if $success; then
  print_result true "ALL TEST PASSED"
else
  print_result false "TEST(S) FAILED"
fi

echo "Press any key to exit..."
read -sn 1
