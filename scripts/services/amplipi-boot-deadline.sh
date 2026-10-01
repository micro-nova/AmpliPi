#!/usr/bin/env bash
set -euo pipefail

# Arms a hard deadline for a trial (tryboot) boot to converge on commit or revert, independent of
# amplipi-tryboot-verify.service's own dependency chain (network-online.target, amplipi.service,
# etc.) - a stuck mount or network-online.target never converging leaves PID1 alive and still
# petting the hardware watchdog, so the watchdog alone can't catch a stuck *unit*, only a dead
# PID1. A systemd-run timer fires on schedule regardless of what else in the dependency graph is
# stuck.
#
# Ordered After=boot-firmware.mount (not the default target chain) so this arms before the
# network/cloud-init chain that's the actual hang risk even gets a chance to.

BOOT_MOUNT="/boot/firmware"
PENDING_FILE="${BOOT_MOUNT}/update-pending"
DEADLINE_MIN=15  # generous vs. amplipi-tryboot-verify.sh's own ~9-10min worst-case retry budget

[ -f "${PENDING_FILE}" ] || exit 0  # not a trial boot, nothing to arm

echo "[$(date -Iseconds)] amplipi-boot-deadline: trial boot detected, arming ${DEADLINE_MIN}min deadline" >> /data/update-log.txt 2>/dev/null || true

systemd-run --unit=amplipi-boot-deadline-fire --on-active="${DEADLINE_MIN}min" \
  /usr/local/bin/amplipi-boot-deadline-fire.sh
