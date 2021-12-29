#!/usr/bin/env bash

# By default just reset and verify I2C communication
# If any argument is passed, also read special I2C debugging registers.
read_special_i2c=false
if (( $# > 0 )); then
  read_special_i2c=true
fi

cnt=0
failed=false

exit_func () {
  echo "Number of resets: $cnt"
  exit 1
}

trap exit_func INT TERM

# cd to amplipi root dir
cd "$(dirname ${BASH_SOURCE[0]})/../.."

max_time="0"
while ! $failed; do
  ((cnt=cnt+1))

  # Reset preamp
  sleep 0.1
  if ! venv/bin/python hw/tests/preamp.py -raq 2>/dev/null; then
    echo "Error communicating to preamp"
    break
  fi
  sleep 0.1

  if $read_special_i2c; then
    # Check if exp_nrst or exp_boot0 were set (used as error flags)
    reg_tries=$(i2cget -y 1 0x08 0x17)
    reg_itime=$(i2cget -y 1 0x08 0x18)
    reg_err=$(i2cget -y 1 0x08 0x19)
    printf "Reset $cnt, %u I2C init tries totalling %u us" "$reg_tries" "$reg_itime"
    if (( $reg_err > 0 )); then
      echo ", SDA ERROR";
      failed=true
    else
      echo ""
    fi

    # Print stats every 100th time
    if (( $reg_itime > $max_time )); then
      max_time=$reg_itime
    fi
    if (( $cnt % 10 == 0 )); then
      printf "Max init time so far: %u us\n" "$max_time"
    fi
  else
    printf "Reset $cnt: version=%u.%u\n" $(i2cget -y 1 0x08 0xFA) $(i2cget -y 1 0x08 0xFB)
  fi
done
echo "Number of reset attempts: $cnt"
