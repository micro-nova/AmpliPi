#!/usr/bin/env bash
set -euo pipefail

BOOT_MOUNT="/boot/firmware"
PENDING_FILE="${BOOT_MOUNT}/update-pending"
AUTOBOOT_FILE="${BOOT_MOUNT}/autoboot.txt"
UPDATE_LOG="/data/update-log.txt"

log() {
  local msg="[$(date -Iseconds)] amplipi-tryboot-verify: $*"
  echo "${msg}"
  echo "${msg}" >> "${UPDATE_LOG}" 2>/dev/null || true
}

# Retry helper: retry N times with DELAY seconds between attempts
retry() {
  local n=$1 delay=$2; shift 2
  for i in $(seq 1 "${n}"); do
    if "$@" &>/dev/null; then return 0; fi
    [ "${i}" -lt "${n}" ] && sleep "${delay}"
  done
  return 1
}

current_part=$( [[ "${BOOT_SLOT}" == "A" ]] && echo 2 || echo 3 )

commit() { # Swap which boot slot is considered primary and secondary p1's autoboot.txt
  local old_part
  if [ "${current_part}" = "2" ]; then old_part=3; else old_part=2; fi

  log "Committing: p${current_part} becomes default, p${old_part} becomes tryboot"

  mount -o remount,rw "${BOOT_MOUNT}"

  # Update boot_partition in [all] and [tryboot] sections
  python3 /usr/local/bin/update_autoboot.py "${AUTOBOOT_FILE}" "${current_part}" "${old_part}"

  rm -f "${PENDING_FILE}"
  mount -o remount,ro "${BOOT_MOUNT}"

  log "Commit complete. Default: p${current_part} | Tryboot: p${old_part}"
}

revert() { # If anything is unsuccessful, revert to the previous boot slot
  local reason="$1"
  log "Health check failed: ${reason} — rebooting to trigger auto-revert"
  mount -o remount,rw "${BOOT_MOUNT}" 2>/dev/null || true
  rm -f "${PENDING_FILE}"
  mount -o remount,ro "${BOOT_MOUNT}" 2>/dev/null || true
  systemctl reboot
}

# ---- Main ----

if [ ! -f "${PENDING_FILE}" ]; then
  log "No update pending — exiting"
  exit 0
fi

expected_part=$(tr -d '[:space:]' < "${PENDING_FILE}")
log "Trial boot detected. Expected p${expected_part}, running on p${current_part}"

if [ "${current_part}" != "${expected_part}" ]; then
  revert "Booted on wrong partition (expected p${expected_part}, got p${current_part})"
  exit 0
fi

log "Running health checks"

failed_checks=()

# TODO: switch to system services once services are moved off p7
retry 12 5 systemctl --user -M pi@ is-active amplipi       || failed_checks+=("amplipi service")
retry 12 5 systemctl --user -M pi@ is-active amplipi-tasks || failed_checks+=("amplipi-tasks service")
retry 6  5 systemctl is-active redis-server                || failed_checks+=("redis-server service")
retry 12 5 curl -sf --max-time 5 http://localhost/api      || failed_checks+=("API health check")

if [ "${#failed_checks[@]}" -gt 0 ]; then
  revert "Failed: ${failed_checks[*]}"
  exit 0
fi

commit
