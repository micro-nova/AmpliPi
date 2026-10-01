#!/usr/bin/env bash
# Generate a unique default SSH/display password, and show the eink delivery/quickstart message,
# the first time this physical unit ever boots.
#
# scripts/imaging/cleanup already does both (via set_pass and show-delivery-message) for the
# normal build flow, where a human runs it once against each individually-built unit before
# shipping. The progenitor image (one shared, pre-built disk image customers flash themselves via
# Balena Etcher) has no such per-unit step: every unit flashed from the same image would otherwise
# share whatever password was baked in at build time, and none would ever get the delivery
# message written to its own physical display. This service closes both gaps on the device's own
# first boot instead - one guard, one first-boot event, not two separate detectors for the same
# thing.
#
# Guarded on default_password.txt not already existing, so this is a true run-once-per-physical-
# unit action, not a run-once-per-boot one: a unit that already went through scripts/imaging/cleanup skips
# it (the file's already there), and a unit that already ran this once (e.g. before slot B gets
# populated by a later OTA update) never regenerates it just because a new slot booted.
set -euo pipefail

CONFDIR="/data/.config/amplipi"
if [ -f "$CONFDIR/default_password.txt" ]; then
  exit 0
fi

/home/pi/amplipi-dev/scripts/services/set_pass
/usr/local/bin/amplipi-firstboot-delivery-message.sh
