# Shared SSH/SCP password-shim setup, sourced by any script that wants every `ssh`/`scp` call in
# its own process - AND any subprocess it spawns (build_golden_slot, deploy, make_images, ...),
# since PATH is inherited - to transparently authenticate with the same password, prompted for at
# most once per run. Without this, each of those separately opens its own unrelated connection,
# prompting again at every single call boundary - e.g. make_progenitor's own direct ssh calls, its
# build_golden_slot --remote subprocess, and its deploy subprocess would otherwise each prompt
# independently, even though they're all talking to the same target in the same run.
#
# Not meant to be executed directly - source it and call setup_ssh_password_shim "$target".
#
# Deliberately does NOT set its own `trap ... EXIT` for cleanup, since bash only honors one EXIT
# trap and a caller with its own cleanup logic (e.g. make_golden_release's on_exit, which also
# handles slot auto-revert) would have it silently overwritten. Instead, this sets a global
# $_ssh_shim_dir - callers must remove it themselves on exit, either via their own trap
# (`trap 'rm -rf "$_ssh_shim_dir"' EXIT`) or by folding it into an existing one.

setup_ssh_password_shim() {
  local target="$1"

  # Key-based auth to $target can't be relied on here - authorized_keys may not have this
  # machine's key, or key trust may only ever have been established interactively (an agent that
  # isn't available in a non-interactive context like this). The account password, unlike SSH key
  # trust, is guaranteed to stay valid across a whole multi-phase run (build_golden_slot carries
  # the password hash forward to any freshly-built slot), so this authenticates with it directly
  # via sshpass instead of depending on key trust having been set up already.
  command -v sshpass >/dev/null || { echo "Error: sshpass is required (sudo apt install sshpass)"; exit 1; }
  if [[ -z "${AMPLIPI_SSH_PASSWORD:-}" ]]; then
    read -rsp "Password for $target (used for every SSH/SCP call this run makes): " AMPLIPI_SSH_PASSWORD
    echo
  fi

  # Shimming ssh/scp on PATH for the duration of the run, rather than threading sshpass/-o flags
  # through every individual call: every script this process spawns that talks to $target over
  # ssh/scp makes its own separate calls, and none of them need to change to pick this up - they
  # just see an ssh/scp earlier on PATH than the real ones. Same reasoning covers
  # -o StrictHostKeyChecking=accept-new, baked into the shim so every call gets it too.
  local real_ssh real_scp
  real_ssh="$(command -v ssh)"
  real_scp="$(command -v scp)"
  _ssh_shim_dir="$(mktemp -d)"
  cat > "$_ssh_shim_dir/ssh" <<EOF
#!/bin/sh
exec sshpass -e "$real_ssh" -o StrictHostKeyChecking=accept-new "\$@"
EOF
  cat > "$_ssh_shim_dir/scp" <<EOF
#!/bin/sh
exec sshpass -e "$real_scp" -o StrictHostKeyChecking=accept-new "\$@"
EOF
  chmod +x "$_ssh_shim_dir/ssh" "$_ssh_shim_dir/scp"
  export PATH="$_ssh_shim_dir:$PATH"
  export SSHPASS="$AMPLIPI_SSH_PASSWORD"
}
