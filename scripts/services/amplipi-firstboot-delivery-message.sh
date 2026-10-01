#!/usr/bin/env bash
# Write the QR code message to the e-ink screen on first boot
set -euo pipefail

REVERT_MINUTES=2 # units migrated in the field shouldn't need to reboot to remove this message

# mask the amplipi-display service so we can overrule it before sending it back to normal operation after the reversion timer
systemctl mask --runtime amplipi-display.service
systemctl stop amplipi-display.service 2>/dev/null || true

if ! /home/pi/amplipi-dev/venv/bin/python -m amplipi.display.display --delivery-message; then
  echo "Delivery message failed unexpectedly - restarting normal display instead." >&2
  systemctl unmask amplipi-display.service
  systemctl start amplipi-display.service
  exit 0
fi

systemd-run --unit=amplipi-delivery-message-revert --on-active="${REVERT_MINUTES}min" \
  /usr/local/bin/amplipi-delivery-message-revert.sh
