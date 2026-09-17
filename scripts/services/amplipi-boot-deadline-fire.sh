#!/usr/bin/env bash
set -euo pipefail

# Runs only if amplipi-boot-deadline.sh's timer actually reaches its
# deadline without being cancelled. Checking update-pending here (rather
# than relying solely on cancellation happening) means this is a safe
# no-op on the happy path even if amplipi-tryboot-verify.sh's commit()
# ever fails to cancel it - correctness doesn't depend on remembering to
# cancel, only on update-pending being gone once commit/revert has run.

BOOT_MOUNT="/boot/firmware"
PENDING_FILE="${BOOT_MOUNT}/update-pending"
UPDATE_LOG="/data/update-log.txt"

log() {
  local msg="[$(date -Iseconds)] amplipi-boot-deadline: $*"
  echo "${msg}"
  echo "${msg}" >> "${UPDATE_LOG}" 2>/dev/null || true
}

if [ ! -f "${PENDING_FILE}" ]; then
  log "update-pending already cleared - commit/revert already happened, deadline is a no-op"
  exit 0
fi

log "Deadline reached without commit/revert - trial boot never converged. Forcing revert."
mount -o remount,rw "${BOOT_MOUNT}" 2>/dev/null || true
rm -f "${PENDING_FILE}"
mount -o remount,ro "${BOOT_MOUNT}" 2>/dev/null || true
systemctl reboot
