# Shared logic for capturing/writing an OS root partition (p5/p6) at its minimal used size
# instead of its full fixed partition size, while keeping every byte offset in the resulting disk
# image identical to a real full-size disk - the unused tail of a shrunk partition streams as
# explicit zero bytes instead of real (uncompressible, slow-to-read-over-USB) leftover ext4 data,
# and `conv=sparse` on the write side then skips physically writing those zero runs. That's safe
# regardless of whether the destination bridge supports TRIM: the skipped region becomes the
# filesystem's own free space the moment it's grown back (grow_root_fs), so it's never read by
# anything in between, whatever bytes happen to already be sitting there.
#
# This keeps the image itself a single, real, byte-for-byte whole-disk image (still flashable with
# Etcher/dd by hand, no format change) - only p5/p6 are ever shrunk, since they're the only fixed-
# size-across-the-fleet partitions worth it; p1/p2/p3 are tiny already and p7 has no fixed target
# size to grow back to.
#
# Requires e2fsck_tolerant() (modules/rpiboot_connect.sh) already sourced by the caller.
# Not meant to be executed directly - source it.

# A partition_base.img.xz's inactive slot is deliberately left raw/unformatted (make_partition_base
# wipes it, not mkfs's it) - unlike a progenitor image's unpopulated slot, which is still a real,
# freshly-formatted-but-empty ext4 filesystem. Callers must check this before growing a slot, since
# there's nothing to grow on a raw one. `-c /dev/null` forces a live probe, not a stale cache entry
# from whatever used to be on this partition before the write that just happened.
has_ext4_fs() {
  [[ "$(sudo blkid -c /dev/null -o value -s TYPE "$1" 2>/dev/null)" == "ext4" ]]
}

_disk_kname() { basename "$(readlink -f "$1")"; }
_part_start_bytes() { echo $(( $(cat "/sys/block/$(_disk_kname "$1")/$(_disk_kname "$1")$2/start") * 512 )); }
_part_size_bytes()  { echo $(( $(cat "/sys/block/$(_disk_kname "$1")/$(_disk_kname "$1")$2/size") * 512 )); }

# Shrinks the ext4 filesystem on $1 to its minimum size. Prints the new size in bytes on stdout -
# caller must grow it back later (grow_root_fs), either immediately (to leave a capture source
# disk unchanged) or after writing a shrunk image onto a fresh target.
shrink_root_fs() {
  local part="$1"
  e2fsck_tolerant "$part" >&2 || { echo "Error: e2fsck failed on $part" >&2; return 1; }
  local out
  out=$(sudo resize2fs -M "$part" 2>&1) || { echo "$out" >&2; return 1; }
  echo "$out" >&2
  local blocks
  blocks=$(echo "$out" | grep -oP 'now \K[0-9]+(?= \(4k\) blocks)')
  [[ -n "$blocks" ]] || { echo "Error: couldn't parse resize2fs's new block count from: $out" >&2; return 1; }
  echo $((blocks * 4096))
}

# Grows the ext4 filesystem on $1 back out to fill the entirety of whatever partition it's
# currently sitting in (resize2fs's documented no-size-given behavior) - a no-op if it's already
# full size, so safe to call unconditionally after any write.
grow_root_fs() {
  local part="$1"
  e2fsck_tolerant "$part" >&2 || { echo "Error: e2fsck failed on $part" >&2; return 1; }
  sudo resize2fs "$part" >&2
}

# Streams the entirety of $1 to stdout, byte-identical in length and layout to `dd if=$1` -
# except partition 5 and/or 6, if a shrunk byte count is given (args 2/3; empty string = stream
# that partition normally, full size, real bytes - e.g. an unpopulated slot that was never
# shrunk). For a shrunk partition, only its used bytes are read for real; the rest of its declared
# size is emitted as zero bytes instead of read from the (slow, USB-attached) device at all.
#
# Total emitted length is asserted against the disk's real size before returning - a partition-
# table-reading bug fails loudly here instead of silently shipping a corrupt image.
stream_disk_shrunk() {
  local diskpath="$1" p5_shrunk="${2:-}" p6_shrunk="${3:-}"
  local total_bytes
  total_bytes=$(sudo blockdev --getsize64 "$diskpath")

  local -A start size shrunk
  local i
  for i in 1 2 3 5 6 7; do
    start[$i]=$(_part_start_bytes "$diskpath" "$i")
    size[$i]=$(_part_size_bytes "$diskpath" "$i")
  done
  shrunk[5]="$p5_shrunk"
  shrunk[6]="$p6_shrunk"

  # Partition *numbers* have no guaranteed relationship to physical on-disk order (an MBR logical
  # partition's number reflects creation order inside the extended container, not position - p2 on
  # real hardware has landed at the very end of the disk, physically after p5/p6/p7) - walk them
  # sorted by actual start offset, not by number, or the gap-fill below mistakes a large chunk of
  # already-covered partitions for one giant unknown region and reads them all over again.
  local -a order
  mapfile -t order < <(for i in 1 2 3 5 6 7; do echo "${start[$i]} $i"; done | sort -n | awk '{print $2}')

  local cursor=0 streamed=0
  # `status=progress` on each individual dd (rather than one running total for the whole stream)
  # is deliberate - each call is a separate, meaningfully-sized region, and knowing *which* region
  # is currently moving (label printed at each call site below) matters as much as the byte count.
  _emit_real() { # skip_bytes count_bytes
    (("$2" > 0)) || return 0
    sudo dd if="$diskpath" bs=1M iflag=skip_bytes,count_bytes skip="$1" count="$2" status=progress
    streamed=$((streamed + $2))
  }
  _emit_zero() { # count_bytes
    (("$1" > 0)) || return 0
    dd if=/dev/zero bs=1M iflag=count_bytes count="$1" status=progress
    streamed=$((streamed + $1))
  }
  _mb() { echo $(("$1" / 1024 / 1024)); }

  for i in "${order[@]}"; do
    if ((start[$i] > cursor)); then
      local gap=$((start[$i] - cursor))
      echo "  Reading $(_mb "$gap")MB gap before p$i..." >&2
      _emit_real "$cursor" "$gap"
    fi
    if [[ -n "${shrunk[$i]:-}" ]]; then
      echo "  Reading p$i ($(_mb "${shrunk[$i]}")MB used, shrunk from $(_mb "${size[$i]}")MB)..." >&2
      _emit_real "${start[$i]}" "${shrunk[$i]}"
      local pad=$((size[$i] - shrunk[$i]))
      echo "  Zero-padding p$i's remaining $(_mb "$pad")MB..." >&2
      _emit_zero "$pad"
    else
      echo "  Reading p$i ($(_mb "${size[$i]}")MB)..." >&2
      _emit_real "${start[$i]}" "${size[$i]}"
    fi
    cursor=$((start[$i] + size[$i]))
  done
  if ((total_bytes > cursor)); then
    local tail=$((total_bytes - cursor))
    echo "  Reading trailing $(_mb "$tail")MB after the last partition..." >&2
    _emit_real "$cursor" "$tail"
  fi

  [[ "$streamed" -eq "$total_bytes" ]] || { echo "Error: stream_disk_shrunk emitted $streamed bytes, expected $total_bytes - aborting, NOT a valid image" >&2; return 1; }
}
