# scripts/imaging

Tools for building and shipping AmpliPi disk images: the progenitor/baseline lineage used to
bootstrap fresh units from scratch, and the golden-release/OTA pipeline used to ship updates to
units already in the field. Each script is also a standalone tool with its own `--help` - this is
just a map of what exists and how the pieces fit together.

## Progenitor / baseline pipeline

Builds and maintains `progenitor.img.xz` (a real, deployed reference image) and
`partition_base.img.xz` (`progenitor.img.xz` with slot B wiped and identity scrubbed - a
cruft-free seed for the next `make_progenitor` run, breaking the circular dependency of always
bootstrapping from the previous build's own output). Needs a physical USB/rpiboot connection.

- **`make_progenitor`** - the main entry point. Orchestrates a full 7-stage build: flash a
  known-good baseline, migrate a fresh Trixie install onto the inactive slot over SSH, activate
  it, deploy AmpliPi, run a real tryboot dress-rehearsal, wipe the old slot, and capture the
  result as a new `progenitor.img.xz`. Supports `--start-stage N` to resume after a hiccup
  without redoing completed stages.
- **`flash_bootstrap_image`** - writes a complete `.img.xz` onto a Pi's eMMC via a single atomic
  `dd` over rpiboot. Used by `make_progenitor`'s Stage 1, but also a standalone tool for writing
  any known-good image onto a unit directly.
- **`make_partition_base`** - flashes a progenitor image, wipes slot B, clears `/data` (p7), and
  scrubs the active slot's identity, producing `partition_base.img.xz`. Also supports
  `--start-stage N`.
- **`label_base_partitions`** - one-off fix for p1 (`AUTOBOOT`)/p7 (`DATA`) never getting an
  explicit filesystem label anywhere else in the pipeline. Label-only, no content changes.
- **`capture_disk_image`** - captures a connected Pi's entire eMMC (all 7 partitions) to
  `progenitor.img.xz`, scrubbing per-unit credentials (password, SSH host keys, journal,
  support-tunnel/WireGuard state) first. The final step of `make_progenitor`, but also standalone.
- **`reseed_identity`** - generates fresh SSH host keys and a new login password for a connected
  Pi's active slot, without touching anything else. For recovering SSH access to a unit whose
  identity was scrubbed by `capture_disk_image`, without a full rebuild. Not a substitute for
  `make_progenitor` if a unit's `/data` was wiped more aggressively (e.g. by `make_partition_base`)
  - that needs a real `deploy`/`configure.py` pass to reprovision, not just identity.

## Golden release / OTA pipeline

Builds a field release from an already-running, already-partitioned unit, entirely over SSH (no
USB/rpiboot needed) - either a full-image release or an AmpliPi-code-only delta.

- **`make_golden_release`** - end-to-end full-image release: rebuild the inactive slot from a
  clean stock image, deploy AmpliPi onto it, capture it as OTA images, generate its manifest.
  `build_golden_slot` + `deploy` + `make_images` + `make_image_manifest`, tied together.
- **`build_golden_slot`** - rebuilds one A/B slot on an already-running unit from a stock Trixie
  Lite image, over SSH. Only formats/populates the inactive slot's own partitions - never p1, p7,
  or the partition table. `--format-only` wipes a now-stale slot clean without repopulating it.
  Doesn't install AmpliPi itself (`deploy`/`configure.py` does that) or scrub identity (`cleanup`
  does that).
- **`make_update`** - thin wrapper for producing a full-image OTA package from your laptop,
  pointed at a Pi over SSH: `make_images` + `make_image_manifest`.
- **`make_images`** - captures a remote Pi's inactive slot's root (and optionally boot) partitions
  to local `.img.xz` files, auto-detecting the inactive slot.
- **`make_image_manifest`** - generates the OTA manifest for a full-image release from
  `make_images`' output (checksums, sizes). Doesn't handle hosting - the images and their `url`
  fields still get filled in by hand (see `NEW_RELEASE.md`).
- **`make_delta_manifest`** - generates the manifest for an AmpliPi-code-only delta release. No
  image to capture - just a manifest naming a `min_base_version` compatibility floor.
- **`cleanup`** - cleans up a remote unit's filesystem before it ships to a customer.

## `modules/`

Shared bash logic, sourced (never executed directly) by the scripts above:

- **`rpiboot_connect.sh`** - connects to a Pi via USB/rpiboot mass-storage mode (reusing an
  already-connected device when possible), and provides `retry_on_partition` for retrying a
  command against a single partition device - this USB bridge can transiently drop and re-add
  every partition node after a read or write to any one of them.
- **`slot_switch.sh`** - flips which slot an already-running unit boots into, over SSH (direct
  `autoboot.txt` edit + plain reboot, not the normal tryboot/`update-pending` path - this is an
  attended build step, not a field update). Used by `make_progenitor` and `make_golden_release`.
- **`ssh_password_shim.sh`** - shims `ssh`/`scp` on `PATH` for the rest of a script's run (and
  every subprocess it spawns) so the operator is only prompted for the target's password once,
  not once per SSH/SCP call.
