#!/usr/bin/env bash
set -euo pipefail

PENDING_FILE="/boot/firmware/update-pending"
PACKAGES_FILE="/data/packages.apt"
SCRIPTS_DIR="/data/update_scripts"
UPDATE_LOG="/data/update-log.txt"

log() {
  local msg="[$(date -Iseconds)] amplipi-postflash: $*"
  echo "${msg}"
  echo "${msg}" >> "${UPDATE_LOG}" 2>/dev/null || true
}

if [ ! -f "${PENDING_FILE}" ]; then
  exit 0
fi

log "Trial boot detected — running post-flash setup"

# Refresh apt package index (cleared during image prep to reduce image size)
log "Refreshing apt package index..."
apt-get update -qq || log "Warning: apt-get update failed — package installs may not work"

# Install user-customized packages that need to survive OTA updates.
# Add package names (one per line) to /data/packages.apt on p7.
if [ -f "${PACKAGES_FILE}" ]; then
  log "Installing packages from ${PACKAGES_FILE}..."
  DEBIAN_FRONTEND=noninteractive xargs apt-get install -y < "${PACKAGES_FILE}" \
    || log "Warning: some packages from ${PACKAGES_FILE} failed to install"
fi

# Run device-specific customization scripts from p7.
# These survive OTA updates and are re-applied on each new slot's first boot.
if [ -d "${SCRIPTS_DIR}" ]; then
  for script in "${SCRIPTS_DIR}"/*.sh; do
    [ -f "${script}" ] || continue
    log "Running ${script}..."
    bash "${script}" || log "Warning: ${script} exited non-zero"
  done
fi

log "Post-flash setup complete"
