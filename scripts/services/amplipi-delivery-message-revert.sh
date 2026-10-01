#!/usr/bin/env bash
set -euo pipefail

# Runs only if amplipi-firstboot-delivery-message.sh's timer actually fires - invoked directly by
# the systemd-run transient timer it arms, not a persistent unit of its own (same pattern as
# amplipi-boot-deadline-fire.sh). Unmask before start: a masked unit refuses to start at all.
systemctl unmask amplipi-display.service
systemctl start amplipi-display.service
