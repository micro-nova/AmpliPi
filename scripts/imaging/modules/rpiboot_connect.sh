# Shared rpiboot mass-storage connect logic for scripts that need a Pi's eMMC exposed as a USB
# block device (not needed by anything talking to an already-booted unit over SSH instead). Sets
# $diskpath on success. Source it and call rpiboot_connect - not meant to be executed directly.

rpiboot_connect() {
  local disk_base_path=/dev/disk/by-id/usb-RPi-MSD

  # Check if a pi is already mounted before demanding a mount
  # Useful since most scripts/imaging scripts use this and many are fired one after another
  #
  # `|| true` is required, not decorative: an unmatched glob here hits `ls` literally, which fails
  # and (under set -e + pipefail) would otherwise kill the whole calling script silently.
  local candidate
  candidate=$(ls ${disk_base_path}* 2>/dev/null | head -n1) || true
  if [[ -n "$candidate" ]] && sudo blockdev --getsize64 "$candidate" >/dev/null 2>&1; then
    diskpath="$candidate"
    echo "Reusing already-connected Raspberry Pi device at $diskpath"
  else
    # Resolved to an absolute path once, up front - a `sudo -i` root shell's PATH isn't guaranteed
    # to match the PATH this was found on, so bare `rpiboot` at each call site isn't reliable.
    local boot_cmd
    boot_cmd=$(command -v rpiboot || true)
    if [[ -z "$boot_cmd" ]]; then
      echo "Downloading and building Raspberry Pi usbboot"
      local tmpdir
      tmpdir=$(mktemp --directory)
      git clone --depth=1 https://github.com/raspberrypi/usbboot "$tmpdir/usbboot"
      pushd "$tmpdir/usbboot" >/dev/null
      local inst=false
      for dep in libusb-1.0-0-dev make gcc; do
        dpkg-query -s "$dep" 1>/dev/null 2>/dev/null || inst=true
      done
      $inst && { sudo apt update; sudo apt install -y libusb-1.0-0-dev make gcc; }
      make
      # rpiboot is fully self-contained (boot firmware is compiled into the binary, not read from
      # the source tree at runtime), so installing just the binary to a stable path is enough -
      # otherwise every run re-clones and rebuilds, since nothing persists in the mktemp dir.
      sudo install -m 755 rpiboot /usr/local/bin/rpiboot
      boot_cmd=/usr/local/bin/rpiboot
      popd >/dev/null
    fi
    echo "Using rpiboot at $boot_cmd"

    echo -e "\nPlug in a USB cable from the AmpliPi's service port to this computer. Keep it powered OFF."
    read -rp "Press any key to continue" -n 1; echo
    read -rp "Press any key and then plug in the AmpliPi" -n 1; echo

    # send rpiboot output directly to show if any errors happen during mounting
    if ! timeout 60 sudo "$boot_cmd"; then
      echo "Error: rpiboot didn't detect/boot the AmpliPi within 60s - check the cable and that it's actually in USB-boot mode (powered off when connected, powered on only after this prompt)."
      exit 1
    fi

    # 40 x 0.5s - rpiboot exiting successfully doesn't guarantee the mass-storage stage has fully
    # come up yet, and this bridge's own enumeration is already known to be slow/flaky.
    local connected=false
    for _ in {1..40}; do
      sleep 0.5
      if lsusb -d 0a5c:0001 >/dev/null; then connected=true; break; fi
    done
    $connected || { echo "Error: Failed to connect to Raspberry Pi"; exit 1; }

    sleep 2  # let the device node settle
    # Same unmatched-glob/pipefail issue as above - `|| true` keeps this from bypassing the error
    # check on the next line.
    diskpath=$(ls ${disk_base_path}* 2>/dev/null | head -n1) || true
    [[ -n "$diskpath" ]] || { echo "Error: No Raspberry Pi device found at ${disk_base_path}*"; exit 1; }
    echo "Raspberry Pi device found at $diskpath"
  fi

  sudo partprobe "$diskpath" 2>/dev/null || true
  sudo udevadm settle --timeout=10 2>/dev/null || true
  for _ in {1..15}; do
    all_present=true
    for part in 1 2 3 5 6 7; do
      [[ -e "${diskpath}-part${part}" ]] || { all_present=false; break; }
    done
    $all_present && break
    sleep 1
  done
}

# Certain actions can cause the connection to briefly drop while the system configures itself
# This function is a guard against our scripts dropping in response to that milliseconds-long window
retry_on_partition() {
  local attempt errfile
  errfile=$(mktemp)
  for attempt in 1 2 3 4 5; do
    if "$@" 2>"$errfile"; then
      cat "$errfile" >&2
      rm -f "$errfile"
      return 0
    fi
    cat "$errfile" >&2
    if ((attempt < 5)); then
      echo "  (attempt $attempt/5 failed - reprobing and retrying...)"
      sudo partprobe "$diskpath" 2>/dev/null || true
      sudo udevadm settle --timeout=10 2>/dev/null || true
      sleep 2
    fi
  done
  rm -f "$errfile"
  echo "Error: command failed after 5 attempts: $*"
  return 1
}

# If you plug in another USB device while a pi is plugged in but not mounted, your computer will
# scan for other USB devices and automount the pi when it shouldn't be mounted. Call unmount_if_mounted
# before every step that requires the pi to not be mounted
unmount_if_mounted() {
  local mp
  mp=$(lsblk -no MOUNTPOINT "$1" 2>/dev/null)
  [[ -n "$mp" ]] && sudo umount "$1"
  return 0
}

# e2fsck exit code 1 ("errors corrected") is a normal success outcome, not something to retry on -
# folds that in before retry_on_partition sees the result, so only a genuine device-access failure
# triggers a retry.
e2fsck_tolerant() {
  local rc
  unmount_if_mounted "$1"
  sudo e2fsck -p -f "$1"
  rc=$?
  [[ $rc -le 1 ]]
}
