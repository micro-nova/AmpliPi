# Shared rpiboot mass-storage connect logic, sourced by any script that needs a Pi's eMMC
# exposed as a USB block device (build_golden_slot's --remote mode doesn't need this - it talks
# over SSH to an already-booted unit instead; this is only for the USB/rpiboot-only tools:
# capture_disk_image and flash_bootstrap_image). Sets $diskpath on success.
#
# Not meant to be executed directly - source it (`source "$(dirname ...)/modules/rpiboot_connect.sh"`)
# and call rpiboot_connect.

rpiboot_connect() {
  local boot_cmd=rpiboot
  if ! command -v $boot_cmd >/dev/null; then
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
    # rpiboot is fully self-contained (the boot firmware files get compiled into the binary
    # itself via generated headers, not read from the source tree at runtime), so installing
    # just the binary to a stable system path is enough - without this, every single run of
    # every script sourcing this one re-clones and rebuilds it from scratch, since command -v
    # never finds anything left behind in a throwaway mktemp dir.
    sudo install -m 755 rpiboot /usr/local/bin/rpiboot
    boot_cmd=rpiboot
    popd >/dev/null
  fi

  echo -e "\nPlug in a USB cable from the AmpliPi's service port to this computer. Keep it powered OFF."
  read -rp "Press any key to continue" -n 1; echo
  read -rp "Press any key and then plug in the AmpliPi" -n 1; echo
  sudo $boot_cmd

  local connected=false
  for _ in {1..10}; do
    sleep 0.5
    if lsusb -d 0a5c:0001 >/dev/null; then connected=true; break; fi
  done
  $connected || { echo "Error: Failed to connect to Raspberry Pi"; exit 1; }

  local disk_base_path=/dev/disk/by-id/usb-RPi-MSD
  sleep 2  # let the device node settle
  diskpath=$(ls ${disk_base_path}* 2>/dev/null | head -n1)
  [[ -n "$diskpath" ]] || { echo "Error: No Raspberry Pi device found at ${disk_base_path}*"; exit 1; }
  echo "Raspberry Pi device found at $diskpath"
}
