# Shared A/B slot-switching logic, sourced by any script that needs to flip which slot an
# already-running unit boots into over SSH (make_golden_release and make_progenitor both need
# this). Every function here operates against the global $target variable ("user@host") - set it
# before calling into this file, same as make_golden_release always has.
#
# Slot switches here are direct autoboot.txt edits + a plain reboot - deliberately NOT the normal
# tryboot/update-pending path, since that triggers amplipi-tryboot-verify.sh's health check, which
# would fail (and revert) against a freshly-built slot with no AmpliPi installed on it yet. This is
# an attended build step, not a field update - there's no health/rollback concern here that the
# operator running the script isn't already accountable for directly.
#
# Not meant to be executed directly - source it and call its functions.

root_part() { [[ "$1" == "A" ]] && echo 5 || echo 6; }
boot_part() { [[ "$1" == "A" ]] && echo 2 || echo 3; }
other_slot() { [[ "$1" == "A" ]] && echo B || echo A; }
target_host() { echo "${target#*@}"; }  # strip "user@" for ssh-keygen -R, which wants the bare host

# Rebuilding a slot from a stock image legitimately changes its SSH host key - the fresh image's
# key, until configure.py's symlink-to-/data step restores the persisted one, which hasn't run yet
# at any point this key actually changes here. Without this, the *next* connection to $target from
# anywhere hits a hard "REMOTE HOST IDENTIFICATION HAS CHANGED" refusal instead of just
# reconnecting - not something -o StrictHostKeyChecking=accept-new alone fixes, since that only
# covers a host never seen before, not one whose key changed. Safe here specifically because this
# is a LAN-local build tool talking to a physically-controlled reference unit, not a broad
# practice for untrusted hosts.
clear_stale_host_key() {
  ssh-keygen -R "$(target_host)" >/dev/null 2>&1 || true
}

wait_for_reboot() {
  clear_stale_host_key
  echo "Waiting for $target to come back up..."
  local tries=0
  # Deliberately NOT -o UserKnownHostsFile=/dev/null: writing the fresh key into the real
  # known_hosts here (accept-new) pre-warms trust for it, so any subsequent, unmodified ssh calls
  # right after this don't need any special handling themselves - they just see an already-known,
  # already-matching host.
  until ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new "$target" true 2>/dev/null; do
    tries=$((tries + 1))
    if ((tries > 60)); then echo "Error: $target didn't come back up after 5 minutes"; exit 1; fi
    sleep 5
  done

  # sshd accepting connections isn't the same as the target being fully booted: /data (p7, a real
  # multi-GB ext4 partition mounted via fstab at boot, not part of the root filesystem) can still
  # be mid-mount for a few seconds after ssh is already reachable. Anything reading /data starting
  # in that window sees it as its local, empty, root-owned rootfs mountpoint stub instead of the
  # real partition.
  tries=0
  until ssh -o ConnectTimeout=5 "$target" "mountpoint -q /data" 2>/dev/null; do
    tries=$((tries + 1))
    if ((tries > 24)); then echo "Error: /data never finished mounting on $target after 2 minutes"; exit 1; fi
    sleep 5
  done
  echo "$target is back up."
}

switch_active_slot() {
  local new_default_boot=$1 new_tryboot_boot=$2
  local expected_slot; expected_slot="$([[ "$new_default_boot" == "2" ]] && echo A || echo B)"

  local attempt actual_line actual_slot
  for attempt in 1 2 3; do
    # Cleared up front, not just reactively inside wait_for_reboot: an out-of-band reboot (e.g.
    # unattended-upgrades auto-rebooting after a kernel package update, independent of anything
    # this script does) can regenerate the target's host key before this script ever notices. If
    # that's already happened by the time we get here, the ssh command below fails at the
    # connection level and NONE of the remote commands (mount/update_autoboot.py/reboot) run - but
    # that failure looks identical to "the reboot just dropped the connection", the expected/
    # normal case the `|| true` below exists for. Without the verification step further down, that
    # silently looks like a successful switch even though nothing happened.
    clear_stale_host_key
    ssh -o StrictHostKeyChecking=accept-new "$target" "
      sudo mount -o remount,rw /boot/autoboot
      sudo python3 /usr/local/bin/update_autoboot.py /boot/autoboot/autoboot.txt $new_default_boot $new_tryboot_boot
      sudo mount -o remount,ro /boot/autoboot
      sudo reboot
    " || true  # the reboot itself always drops the SSH connection non-zero; that's expected, not a failure
    sleep 5  # give the target a moment to actually go down before polling for it to come back
    wait_for_reboot

    # Verify the switch actually took effect rather than trusting reachability alone as proof -
    # the stale-key case above means the target was never down, so it looks "back up" immediately
    # even though the switch command never reached it.
    actual_line=$(ssh -o StrictHostKeyChecking=accept-new "$target" "cat /proc/cmdline") || actual_line=""
    if [[ "$actual_line" =~ BOOT_SLOT=([AB]) ]]; then
      actual_slot="${BASH_REMATCH[1]}"
      [[ "$actual_slot" == "$expected_slot" ]] && return 0
    else
      actual_slot="unknown"
    fi
    echo "Warning: $target is on slot $actual_slot, not $expected_slot as expected - the switch may not have reached it. Retrying ($attempt/3)..."
  done
  echo "Error: failed to switch $target onto slot $expected_slot after 3 attempts."
  exit 1
}
