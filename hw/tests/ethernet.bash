#!/usr/bin/env bash

# The min speed is set a bit higher than 10 Mbps to verify faster
# than 10BASE-T speeds are achieved
dl_speed_min_bps=11000000
test_timeout=10
iface=eth0

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[0;33m'
BLU='\033[0;34m'
NC='\033[0m'

if ! command -v speedtest >/dev/null; then
  echo -e "${YEL}Need speedtest-cli, installing...${NC}"
  sudo apt install speedtest-cli
fi

speed=$(</sys/class/net/$iface/speed)
if [ $speed = 100 ]; then
  speed_pass=true
  echo -e "Link speed......${GRN}OK${NC} - $speed Mbps"
else
  speed_pass=false
  echo -e "Link speed......${RED}FAIL${NC} - $speed Mbps"
fi

duplex=$(</sys/class/net/$iface/duplex)
if [ $duplex = full ]; then
  duplex_pass=true
  echo -e "Duplex..........${GRN}OK${NC} - $duplex"
else
  duplex_pass=false
  echo -e "Duplex..........${RED}FAIL${NC} - $duplex"
fi

printf "Download speed.."
speed_json=$(speedtest --no-upload --json --timeout $test_timeout)
dl_speed=$(echo $speed_json | sed 's/.*"download": \([0-9]*\)\..*/\1/')
if (( $dl_speed > $dl_speed_min_bps )); then
  dl_speed_pass=true
  echo -e "${GRN}OK${NC} - $dl_speed bps"
else
  dl_speed_pass=false
  echo -e "${RED}FAIL${NC} - $dl_speed bps"
fi

if $speed_pass && $duplex_pass && $dl_speed_pass; then
  echo -e "${GRN}TEST PASSED${NC}"
else
  echo -e "${RED}TEST FAILED${NC}"
fi

if [[ $# > 0 ]]; then
  echo "Press any key to exit..."
  read -sn 1
fi
