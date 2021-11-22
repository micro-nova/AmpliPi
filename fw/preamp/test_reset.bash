#!/usr/bin/env bash

cnt=0
failed=false

exit_func () {
  echo "Number of resets: $cnt"
  exit 1
}

trap exit_func INT TERM

while ! $failed; do
  # Reset preamp
  ../../hw/tests/preamp.py -ra
  ((cnt=cnt+1))

  # Check if exp_nrst or exp_boot0 were set (used as error flags)
  exp_reg=$(i2cget -y 1 0x08 0x0F)
  exp_nrst=$(( ($exp_reg & 0x01) != 0 ))
  exp_boot0=$(( ($exp_reg & 0x02) != 0 ))
  if (( $exp_nrst > 0 )); then
    echo "NRST set!";
    failed=true
  fi
  if (( $exp_boot0 > 0 )); then
    echo "BOOT0 set!";
    failed=true
  fi
  sleep 1
done
echo "Number of resets: $cnt"
