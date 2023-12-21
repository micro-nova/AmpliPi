#!/usr/bin/env bash
# Program an expander to verify the expansion port's control signals work

# First argument is the manual heat test timeout. Default to 60s
timeout=${1:-60}

RED='\033[0;31m'
GRN='\033[0;32m'
NC='\033[0m'

print_result () {
  if $1; then
    echo -e "${GRN}$2${NC}"
  else
    echo -e "${RED}$2${NC}"
  fi
}

# First argument is true/false success.
exit_test () {
  if $1; then
    print_result true "ALL TESTS PASSED"
  else
    print_result false "TEST(S) FAILED"
  fi

  echo "Press any key to exit..."
  read -sn 1
  exit
}

cmd="venv/bin/python hw/tests/preamp.py"
success=true

# First argument is forwarded to preamp.py as arguments
send_cmd () {
  if ! $cmd "$1"; then
    print_result false "Failed to communicate to preamp."
    exit_test false
  fi
}

echo "Starting fans, temps, and volts tests."
echo

echo "Enter the unit to test"
select yn in Main Expander; do
  case $yn in
    Main ) unit=1; break;;
    Expander ) unit=2; break;;
  esac
done
echo

cd "$(dirname ${BASH_SOURCE[0]})/../.." # cd to amplipi root dir
send_cmd -qu$unit

echo "Are the fans off?"
select yn in Yes No; do
  case $yn in
    Yes ) print_result true "Succeeded"; break;;
    No ) print_result false "Failed"; success=false; break;;
  esac
done
echo

send_cmd -qfu$unit

echo "Are the fans on?"
select yn in Yes No; do
  case $yn in
    Yes ) print_result true "Succeeded"; break;;
    No ) print_result false "Failed"; success=false; break;;
  esac
done
echo

echo "Testing voltage and temperature readings"
if $cmd -qftu$unit; then
  print_result true "Succeeded"
else
  print_result false "Failed"
  success=false
fi
echo

echo "Heat up an amp heatsink, this test will wait until temp has risen 5C."
if $cmd -qu$unit --heat $timeout; then
  print_result true "Succeeded"
else
  print_result false "Failed"
  success=false
fi
echo

exit_test $success
