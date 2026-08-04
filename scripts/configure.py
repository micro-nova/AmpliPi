#!/usr/bin/python3

""" Update Amplipi's configuration on the raspberry pi or your test setup

This script is initially designed to support local git installs, pi installs, and amplipi installs
"""
import platform
import subprocess
import os
import pathlib
import pwd  # username
import glob
import shutil
import tempfile
from typing import List, Union, Tuple, Dict, Any, Optional
import time
import re
import sys
import requests
import json

# pylint: disable=broad-except
# pylint: disable=bare-except


RSYSLOG_CFG = """# /etc/rsyslog.conf configuration file for rsyslog
# Created by AmpliPi installer
#  Drastically limits logging to any local files while maintaining
# remote logging capabilities.
#
# For more information install rsyslog-doc and see
# /usr/share/doc/rsyslog-doc/html/configuration/index.html


#################
#### MODULES ####
#################

module(load="imuxsock") # provides support for local system logging
module(load="imklog")   # provides kernel logging support

###########################
#### GLOBAL DIRECTIVES ####
###########################

#
# Use traditional timestamp format.
# To enable high precision timestamps, comment out the following line.
#
$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat

#
# Set the default permissions for all log files.
#
$FileOwner root
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755
$Umask 0022

#
# Where to place spool and state files
#
$WorkDirectory /var/spool/rsyslog

#
# Include all config files in /etc/rsyslog.d/
#
$IncludeConfig /etc/rsyslog.d/*.conf


###############
#### RULES ####
###############

# Emergencies are sent to everybody logged in.
#
*.emerg                         :omusrmsg:*

"""

_os_deps: Dict[str, Dict[str, Any]] = {
    'base': {
        'apt': ['curl', 'authbind',
                'python3-pil', 'libopenjp2-7',  # Pillow dependencies
                'libopenblas-dev',             # numpy dependencies. was libatlas-base-dev, is no longer thanks to https://github.com/numpy/numpy/issues/29108#issuecomment-3371130468
                'stm32flash',                  # Programming Preamp Board
                'xkcdpass',                    # Random passphrase generation
                'systemd-journal-remote',      # Remote/web based log access
                'jq',                          # JSON parser used in check-release script
                'redis',                       # background job queue
                # pygobject dependencies (Spotifyd)
                'libgirepository1.0-dev', 'libcairo2-dev',
                ],
    },
    'updates': {
      'copy': [
        {
          'from': 'scripts/amplipi-tryboot-verify.sh',
          'to': '/usr/local/bin/amplipi-tryboot-verify.sh',
          'sudo': 'true',
        },
        {
          'from': 'scripts/update_autoboot.py',
          'to': '/usr/local/bin/update_autoboot.py',
          'sudo': 'true',
        },
        {
          'from': 'scripts/amplipi-tryboot-verify.service',
          'to': '/etc/systemd/system/amplipi-tryboot-verify.service',
          'sudo': 'true',
        },
        {
          'from': 'scripts/amplipi-postflash.sh',
          'to': '/usr/local/bin/amplipi-postflash.sh',
          'sudo': 'true',
        },
        {
          'from': 'scripts/amplipi-postflash.service',
          'to': '/etc/systemd/system/amplipi-postflash.service',
          'sudo': 'true',
        },
      ],
      'script': [
        'sudo chmod +x /usr/local/bin/amplipi-tryboot-verify.sh',
        'sudo chmod +x /usr/local/bin/update_autoboot.py',
        'sudo chmod +x /usr/local/bin/amplipi-postflash.sh',

        'sudo chmod 444 /etc/systemd/system/amplipi-tryboot-verify.service',
        'sudo systemctl enable amplipi-tryboot-verify.service',

        # amplipi-tryboot-verify.service used to be named amplipi-update-commit.service. A unit
        # renamed without ever being explicitly disabled under its old name leaves a dangling
        # enablement symlink behind (found live on an older slot:
        # multi-user.target.wants/amplipi-update-commit.service, pointing at a unit file that no
        # longer exists - harmless to systemd but untracked cruft). Clean it up unconditionally;
        # both commands are no-ops once it's already gone.
        'sudo systemctl disable amplipi-update-commit.service 2>/dev/null || true',
        'sudo rm -f /etc/systemd/system/amplipi-update-commit.service',

        'sudo chmod 444 /etc/systemd/system/amplipi-postflash.service',
        'sudo systemctl enable amplipi-postflash.service',
      ],
    },
    'usb': {
        'apt': [
                'udisks2', 'udiskie',           # Required to mount filesystem without desktop installed
        ],
        'copy': [
          {
            'from': 'config/10-udisks.pkla',
            'to': '/etc/polkit-1/localauthority/50-local.d/10-udisks.pkla',
            'sudo': 'true',
          },
          {
            'from': 'config/99-udisks2.rules',
            'to': '/etc/udev/rules.d/99-udisks2.rules',
            'sudo': 'true',
          }
        ],
        'script': [
            'sudo cp scripts/udiskie.service /etc/systemd/system',
            'sudo chmod 444 /etc/systemd/system/udiskie.service',
            'sudo systemctl enable udiskie.service',
        ]
    },
    'logging': {
        "copy": [
          {
            'from': 'config/deactivate_persist_logs_crontab',
            'to': '/etc/cron.d/deactivate_persist_logs',
            'sudo': 'true',
          },
          {
            'from': 'scripts/increment_auto_off.py',
            'to': '/usr/local/bin/increment_auto_off.py',
            'sudo': 'true',
          },
        ],
        'script': [
            'echo "reconfiguring secondary logging utility rsyslog to only allow remote logging"',
            f"echo '{RSYSLOG_CFG}' | sudo tee /etc/rsyslog.conf",
            # just in case it was disabled...
            'sudo systemctl enable rsyslog.service',
            'sudo systemctl restart rsyslog.service',

            'echo "If first deploy, reconfiguring journald defaults"',
            # Previously guarded on `[ ! -d /var/log/journal ]`, which is always false on stock
            # Trixie (that bare directory ships pre-created), so this line never actually fired.
            # Guard on whether we've already written our own setting instead.
            r'grep -q "^SyncIntervalSec=" /etc/systemd/journald.conf || echo -e "[Journal]\nSyncIntervalSec=30s\nSystemMaxUse=64M\nRuntimeMaxUse=64M\nForwardToConsole=no\nForwardToWall=no\n" | sudo tee /etc/systemd/journald.conf',

            # Raspberry Pi OS (Trixie onward) ships /usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf,
            # which forces Storage=volatile and takes precedence over the main journald.conf file
            # regardless of directory - setting Storage there (as this used to) was silently
            # ineffective. The fix is a same-or-later-sorting drop-in in /etc instead; this reuses
            # the exact file raspi-config's own "Advanced Options > Logging" toggle manages, and the
            # one amplipi/updater/asgi.py's persist-logs feature writes to at runtime, so there's one
            # shared source of truth instead of competing mechanisms. Guarded on the drop-in's own
            # existence so a redeploy doesn't clobber whatever's since been set via the updater UI or
            # raspi-config.
            'echo "If first deploy, seeding the journald storage drop-in (default: volatile)"',
            r'[ -f /etc/systemd/journald.conf.d/80-raspi-config-journal-storage.conf ] || (sudo mkdir -p /etc/systemd/journald.conf.d && echo -e "# Created/managed by AmpliPi (also used by raspi-config)\n\n[Journal]\nStorage=volatile\n" | sudo tee /etc/systemd/journald.conf.d/80-raspi-config-journal-storage.conf)',

            'sudo systemctl enable systemd-journald.service',
            'sudo systemctl restart systemd-journald.service',
            # Restarting the daemon alone is NOT enough for a Storage change to take effect -
            # confirmed empirically that only systemd-journal-flush.service (normally boot-only)
            # actually triggers the runtime-to-persistent migration; without this, the daemon
            # accepts the new config but silently keeps using /run/log/journal until next reboot.
            'sudo systemctl restart systemd-journal-flush.service',

            'echo Handle dependencies for log persistence options',
            'sudo mkdir -p /var/log/journal',
            'sudo systemd-tmpfiles --create --prefix /var/log/journal',

            'echo "enable socket to the journald server to allow easy access to system logs"',
            'sudo systemctl enable systemd-journal-gatewayd.socket',
            'sudo systemctl restart systemd-journal-gatewayd.socket',

            'echo "deleting some old logs"',
            'sudo journalctl --rotate',
            'sudo journalctl --vacuum-time=10m',
            'sudo rm /var/log/daemon*   && echo "removed daemon logs" || echo ok',
            'sudo rm /var/log/syslog*   && echo "removed syslogs"     || echo ok',
            'sudo rm /var/log/messages* && echo "removed messages"    || echo ok',
            'sudo rm /var/log/user*     && echo "removed user logs"   || echo ok',
        ]
    },
    'ssh': {
        'script': [
            # Loosen OpenSSH's default PerSourcePenalties (9.8+, on by default with no config
            # needed). authfail:5/max:600 is tuned for internet-facing servers getting mass-
            # scanned; on a LAN-only device it mostly ends up punishing legitimate dev/support SSH
            # bursts (many connections in a short window) rather than a real attacker, since this
            # unit is never reachable from the public internet in the first place. Lowered, not
            # disabled outright - still slows a sustained brute-force attempt from another device
            # on the same network, just caps the worst case at 30s instead of 10 minutes.
            'echo "PerSourcePenalties authfail:1 max:30 min:5" | sudo tee /etc/ssh/sshd_config.d/ssh_penalties.conf',
            'sudo sshd -t',
            'sudo systemctl reload ssh',
        ]
    },
    'support_tunnel': {
        'apt': [
            'libsystemd-dev',  # permits logging directly to journald
            'wireguard', 'wireguard-tools',  # -tools for wg-quick usage
            'python3-pip', 'python3-venv',  # support_tunnel builds its own venv via system python
        ],
        'copy': [
            {
                'from': 'config/support_tunnel_crontab',
                'to': '/etc/cron.d/support_tunnel',
                'sudo': 'true'
            },
            {
                'from': 'config/support_group_sudoers',
                'to': '/etc/sudoers.d/099_support-nopasswd',
                'sudo': 'true'
            },
            {   # support tunnel scripts must be only be writable by root
                'from': 'scripts/support_tunnel_post_up.sh',
                'to': '/usr/local/bin/support_tunnel_post_up.sh',
                'sudo': 'true'
            },
            {
                'from': 'scripts/support_tunnel_post_down.sh',
                'to': '/usr/local/bin/support_tunnel_post_down.sh',
                'sudo': 'true'
            },
            {
                'from': 'config/support_tunnel_config.ini',
                'to': '/etc/support_tunnel/config.ini',
                'sudo': 'true'
            }
        ],
        'script': [
            'sudo addgroup support',
            'sudo adduser pi support',
            'sudo mkdir -p /var/lib/support_tunnel',
            'sudo chmod 0777 /var/lib/support_tunnel',  # TODO: lock this down
            'if [ ! -e /opt/support_tunnel ] ; then'
            '  pushd $(mktemp --directory)',
            '  git clone https://github.com/micro-nova/support_tunnel.git',
            '  sudo mv support_tunnel /opt',
            '  popd',
            'fi',
            'pushd /opt/support_tunnel',
            'git fetch && git reset --hard origin/main',
            'if [ ! -e /opt/support_tunnel/venv ]; then',
            '  /usr/bin/python3 -m venv venv',
            'fi',
            '/opt/support_tunnel/venv/bin/pip install -r requirements.txt',
            'popd',
        ]
    },
    'poetry': {
      'script': ['curl -sSL https://install.python-poetry.org | python3 -']
    },
    # streams
    # TODO: can stream dependencies be aggregated from the streams themselves?
    'airplay': {
        'apt': ['shairport-sync'],
        'copy': [{'from': 'bin/ARCH/shairport-sync-ap2', 'to': 'streams/shairport-sync-ap2'},
                 {'from': 'bin/ARCH/shairport-sync', 'to': 'streams/shairport-sync'}],
        'script': [
            'if which nqptp  > /dev/null; then exit 0; fi',
            'pushd $(mktemp --directory)',
            'git clone https://github.com/mikebrady/nqptp.git',
            'pushd nqptp',
            'autoreconf -fi',
            './configure --with-systemd-startup',
            'make',
            'sudo make install',
            'sudo systemctl enable nqptp && sudo systemctl restart nqptp',
            'popd',
            'popd',
        ]
    },
    'internet_radio': {
        'apt': ['vlc']
    },
    'fmradio': {
        'apt': ['rtl-sdr', 'git', 'build-essential', 'libsndfile1-dev', 'libliquid-dev', 'meson'],
        'script': [
            'if ! which redsea  > /dev/null; then',  # TODO: check version
            '  echo "Installing redsea"',
            '  cd /tmp',
            '  git clone --depth 1 https://github.com/windytan/redsea.git',
            '  cd redsea',
            '  meson setup build',
            '  cd build',
            '  meson compile',
            '  sudo cp redsea /usr/local/bin/',
            '  sudo wget https://raw.githubusercontent.com/osmocom/rtl-sdr/master/rtl-sdr.rules -P /etc/udev/rules.d/',
            '  sudo udevadm control --reload-rules',
            '  sudo udevadm trigger',
            'fi',
        ]
    },
    'lms': {
        'apt': ['libcrypt-openssl-rsa-perl', 'libio-socket-ssl-perl', 'libopusfile0', 'squeezelite'],
        'copy': [{'from': 'bin/ARCH/find_lms_server', 'to': 'streams/find_lms_server'}],
        'script': [
            # squeezeboxserver's UID is pinned before any apt packages are installed (see the
            # pre-creation step ahead of the apt-get install call below) rather than here, so it
            # always wins the UID race regardless of what other packages' postinst scripts do.
            # Lyrion ships a single architecture-independent package (suffixed "_all"), not
            # separate arm/arm64 builds - confirmed against the actual downloads server; a prior
            # arm64-suffixed URL here never resolved to anything real.
            'if [ ! $(dpkg-query --show --showformat=\'${Status}\' lyrionmusicserver | grep -q installed) ]; then '
            '  wget -nv https://downloads.lms-community.org/LyrionMusicServer_v9.1.1/lyrionmusicserver_9.1.1_all.deb -O /tmp/lyrionmusicserver_9.1.1.deb',
            '  sudo dpkg -i /tmp/lyrionmusicserver_9.1.1.deb',
            '  if [ ! -e /data/.config/amplipi/lms_mode ] ; then sudo systemctl disable lyrionmusicserver; fi',
            '  if [ ! -e /data/.config/amplipi/lms_mode ] ; then sudo systemctl stop lyrionmusicserver; fi',
            'fi',
            # LMS's prefs (settings, playlists, persist db) and cache (installed 3rd-party plugin
            # code, scan/artwork cache) both live under /var/lib/squeezeboxserver by default -
            # that's on the OS root partition, so none of it would survive an OTA slot swap. Move
            # the whole directory onto /data (shared across both slots) and symlink it back in
            # place, the same pattern already used for SSH host keys. Guarded on -L so this only
            # runs once, whether that's on a fresh install or an existing (possibly lms_mode-active,
            # already-running) unit's next deploy - stop the service first so rm -rf isn't pulling
            # the directory out from under open file handles, then restore whatever state it was in.
            'if [ ! -L /var/lib/squeezeboxserver ]; then '
            '  LMS_WAS_ACTIVE=$(systemctl is-active lyrionmusicserver 2>/dev/null || true)',
            '  sudo systemctl stop lyrionmusicserver 2>/dev/null',
            '  sudo mkdir -p /data/lms',
            '  sudo cp -a /var/lib/squeezeboxserver/. /data/lms/',
            '  sudo rm -rf /var/lib/squeezeboxserver',
            '  sudo ln -s /data/lms /var/lib/squeezeboxserver',
            '  [ "$LMS_WAS_ACTIVE" = "active" ] && sudo systemctl start lyrionmusicserver',
            'fi',
            # squeezeboxserver is a system user created by this .deb's postinst (adduser --system)
            # on every install, and gets whatever UID happens to be free at the time - not a fixed
            # number the way the pi user's UID is. /data/lms's ownership is stamped with whatever
            # UID that was on the slot that migrated it, so a *different* slot (or a future
            # reinstall) can easily get a different UID for the same username, silently leaving
            # /data/lms owned by an unrelated user and making lyrionmusicserver fail to write its
            # own logs/cache - it exits quickly with no error output, which looks like nothing
            # happened rather than a permissions failure. Re-asserting ownership by name (not
            # relying on the stored numeric UID staying correct) every deploy self-heals this.
            'sudo chown -R squeezeboxserver:nogroup /data/lms',
            'sudo systemctl stop squeezelite',
            'sudo systemctl disable squeezelite',

            'sudo chmod 755 /media/pi',
            'sudo chmod 755 /media/pi/*',
            'sudo cp scripts/udisks2-listener.sh /usr/local/bin',
            'sudo cp scripts/edit_media_directories.py /usr/local/bin',
            'sudo cp scripts/udisks2-listener.service /etc/systemd/system',
            'sudo chmod 444 /etc/systemd/system/udisks2-listener.service',
            'sudo systemctl enable udisks2-listener.service',
        ]
    },
    'dlna': {
        'apt': ['uuid-runtime', 'build-essential', 'autoconf', 'automake', 'libtool', 'pkg-config',
                'libupnp-dev', 'libgstreamer1.0-dev', 'gstreamer1.0-plugins-base',
                'gstreamer1.0-plugins-good', 'gstreamer1.0-plugins-bad', 'gstreamer1.0-plugins-ugly',
                'gstreamer1.0-libav', 'gstreamer1.0-alsa', 'git'],
        'script': [
            # Same unguarded-rebuild issue as bluealsa above: this used to re-run autogen/configure/
            # make on every single deploy regardless of whether anything had changed, even when the
            # repo already existed - skip the whole thing once gmediarender is actually installed.
            'if [ ! -e /usr/local/bin/gmediarender ]; then',
            'if [ ! -d "gmrender-resurrect" ] ; then',
            '  git clone https://github.com/hzeller/gmrender-resurrect.git gmrender-resurrect',
            '  cd gmrender-resurrect',
            'else',
            '  cd gmrender-resurrect',
            '  git pull https://github.com/hzeller/gmrender-resurrect.git',
            'fi',
            './autogen.sh',
            './configure',
            'make',
            'sudo make install',
            'else',
            'echo gmediarender already installed, skipping build.',
            'fi',
        ],
    },
    'plexamp': {
        # TODO: do a full install of plexamp, the partial install below is not useful
        # 'script' : [ './streams/plexamp_nodeinstall.bash' ]
    },
    'spotify': {
        # from https://github.com/devgianlu/go-librespot's release page
        'copy': [{'from': 'bin/ARCH/go-librespot', 'to': 'streams/go-librespot'}],
    },
    'pandora': {
        'apt': [
          'libavfilter-dev', 'libcurl4-openssl-dev', 'libjson-c-dev', 'libao-dev'
        ],
        'copy': [{'from': 'bin/ARCH/pianobar', 'to': 'streams/pianobar'}],
    },
    'bluetooth': {
        'amplipi_only': True,
        'apt': ['libsndfile1', 'libsndfile1-dev', 'libbluetooth-dev', 'python3-dbus',
                'libasound2-dev', 'git', 'autotools-dev', 'automake', 'libtool', 'm4',
                'build-essential', 'pkg-config', 'python3-docutils', 'libdbus-1-dev',
                'libglib2.0-dev', 'libsbc-dev'],
        'script': [

            # Install bluealsa from git - unlike the SBC/nqptp builds below, this had no guard at
            # all, so every deploy that touched 'bluetooth' re-cloned and rebuilt the whole
            # project from scratch (autoreconf + full C build) even when nothing had changed.
            'if [ ! -e /usr/bin/bluealsad ]; then',
            'echo installing bluealsa from source',
            'git clone https://github.com/arkq/bluez-alsa',
            'cd bluez-alsa',
            'autoreconf --install --force',
            './configure --disable-aac --disable-ldac --disable-aptx --disable-opus',
            'sudo make -j$(nproc)',
            'sudo make install',
            'cd ..',
            'else',
            'echo bluealsa already installed, skipping build.',
            'fi',

            # referencing arm here is okay because bluetooth is marked as 'amplipi_only'
            'sudo cp bin/arm/rtl8761b_fw /lib/firmware/rtl_bt/rtl8761b_fw.bin',
            'sudo cp bin/arm/rtl8761b_config /lib/firmware/rtl_bt/rtl8761b_config.bin',
            'sudo cp config/bluetooth/main.conf /etc/bluetooth/main.conf',
            'sudo cp config/bluetooth/bluealsa.service /etc/systemd/system/',
            'sudo rm -f /usr/lib/systemd/system/bluealsa.service',
            'sudo cp streams/bluetooth_agent /usr/local/bin/',
            'sudo cp config/bluetooth/bluetooth_agent.service /etc/systemd/system/',

            # Install SBC
            'if ! [ -e /usr/local/lib/libsbc.so.1.3.1 ]',
            'then',
            'echo Installing SBC...',
            'pushd $(mktemp --directory)',
            'git clone https://git.kernel.org/pub/scm/bluetooth/sbc.git',
            'cd sbc',
            'git checkout 8dc5d5ba381512ad5b1afa45c63ec6b0a3833244',  # sbc release 2.0
            'sudo ./bootstrap-configure',
            'sudo ./configure',
            'sudo make',
            'sudo make install',
            'popd',
            'else',
            'echo SBC already installed, skipping installation.',
            'fi',

            # Add pi user to bluetooth group so we don't need to run sudo
            'sudo usermod -G bluetooth -a pi',

            'sudo chmod +x /usr/local/bin/bluetooth_agent',

            'sudo systemctl enable bluetooth',
            'sudo systemctl enable bluealsa',
            'sudo systemctl enable bluetooth_agent',

            # BlueZ stores paired-device link keys under /var/lib/bluetooth/<adapter-mac>/<device-mac>/info
            # on the OS root partition, so - like LMS's prefs/cache and the SSH host keys above - none
            # of it would survive an OTA slot swap. bluetooth_agent auto-pairs any device that connects
            # (NoInputNoOutput, no user confirmation), so losing this on every update means every
            # previously-connected phone/speaker silently fails to reconnect and has to be forgotten and
            # re-paired by the user.
            #
            # Unlike LMS/SSH, a plain symlink doesn't work here: bluetooth.service ships with
            # ProtectSystem=strict + StateDirectory=bluetooth, systemd's own sandboxed-state mechanism -
            # it expects /var/lib/bluetooth to be a real directory it manages itself, and fails outright
            # ("Failed to set up special execution directory... No such file or directory") if it finds a
            # symlink there instead (confirmed live - this used to be a plain symlink here and broke
            # bluetooth.service on every boot). BindPaths= is systemd's own mechanism for punching a hole
            # through ProtectSystem=strict for exactly this case, so a drop-in that clears StateDirectory
            # and bind-mounts /data/bluetooth over /var/lib/bluetooth is used instead.
            'BT_WAS_ACTIVE=$(systemctl is-active bluetooth 2>/dev/null || true)',
            'sudo systemctl stop bluetooth 2>/dev/null',
            # migrate any real pairing data (e.g. the very first install) before it's covered by the
            # bind mount below
            'if [ -d /var/lib/bluetooth ] && [ ! -L /var/lib/bluetooth ]; then '
            '  sudo mkdir -p /data/bluetooth',
            '  sudo cp -a /var/lib/bluetooth/. /data/bluetooth/ 2>/dev/null || true',
            'fi',
            # undo an earlier (broken) version of this fix that symlinked this path directly
            'if [ -L /var/lib/bluetooth ]; then sudo rm -f /var/lib/bluetooth; fi',
            'sudo mkdir -p /var/lib/bluetooth /data/bluetooth',
            'sudo mkdir -p /etc/systemd/system/bluetooth.service.d',
            "printf '[Service]\\nStateDirectory=\\nBindPaths=/data/bluetooth:/var/lib/bluetooth\\n' | sudo tee /etc/systemd/system/bluetooth.service.d/override.conf >/dev/null",
            'sudo systemctl daemon-reload',
            # plain `cond && cmd` here would make a false cond fail the whole script's exit code,
            # since this is the last line - use an if so a fresh install (nothing was active
            # before) doesn't get reported as a failed os_dep install
            'if [ "$BT_WAS_ACTIVE" = "active" ]; then sudo systemctl start bluetooth; fi',
        ]
    }
}


def filter_deps(dep: str, dep_filter: List[str]) -> bool:
  ret = len(dep_filter) > 0 and dep not in dep_filter
  if ret:
    print(f"\n{dep} not in {dep_filter}, skipping...\n")
    time.sleep(1)

  return ret


def _check_and_update_streamer(env):
  """Check if this is a streamer (no preamp firmware)"""
  is_streamer_path = os.path.join(env['config_dir'], 'is_streamer')
  env['is_streamer'] = os.path.exists(is_streamer_path)


def _check_and_setup_platform(development, ci_mode):
  script_dir = os.path.dirname(os.path.realpath(__file__))
  env = {
      'user': pwd.getpwuid(os.getuid()).pw_name,
      'has_apt': False,
      'is_git_repo': False,
      'platform_supported': False,
      'script_dir': script_dir,
      'base_dir': script_dir.rsplit('/', 1)[0],
      'config_dir': os.path.join('/data', '.config', 'amplipi'),
      'is_amplipi': False,
      'is_streamer': False,
      'arch': 'unknown',
      'is_ci': ci_mode,
  }

  # Get the platform name
  # - example pi output: Linux-5.4.51-v7+-armv7l-with-debian-10.4
  # - example ubuntu output: Linux-5.4.0-66-generic-x86_64-with-Ubuntu-18.04-bionic
  lplatform = platform.platform().lower()

  # Figure out what platform we are on since we expect to be on a raspberry pi or a debian based development system
  if 'linux' in lplatform:
    apt = subprocess.run('which apt-get'.split(), check=True)
    if apt:
      env['has_apt'] = True

    if 'x86_64' in lplatform:
      env['arch'] = 'x64'
    elif 'armv7l' in lplatform:
      env['arch'] = 'arm'
    elif 'aarch64' in lplatform:
      env['arch'] = 'arm64'

    env['is_amplipi'] = 'amplipi' in platform.node()  # checks hostname
    if env['is_amplipi']:
      env['config_dir'] = '/data/.config/amplipi'

    if env['arch'] == 'x64' and env['has_apt']:
      # possibly a development machine running a debian-based distro
      env['platform_supported'] = True

    if env['arch'] == 'arm' and 'debian' in lplatform:
      # possibly a Rasperry Pi running Raspbian
      env['platform_supported'] = True

    if env['arch'] == 'arm64':
      # 64 bit raspbian OS
      env['platform_supported'] = True

  if development:
    # We're explicitly overriding any checks here; assume we're supported.
    env['platform_supported'] = True

  _check_and_update_streamer(env)

  return env


class Task:
  """ Task runner for scripted installation tasks """

  def __init__(self, name: str, args: Optional[List[str]] = None, multiargs=None, output='', success=False, wd=None, shell=False, stream=False):
    # pylint: disable=too-many-arguments
    self.name = name
    if multiargs:
      assert args is None
      self.margs = multiargs
    elif args is not None:
      self.margs = [args]
    else:
      self.margs = [[]]
    self.output = output
    self.success = success
    self.wd = wd
    self.shell = shell
    # Long-running commands (e.g. dist-upgrade) normally have their output fully buffered and
    # only shown once they finish, which makes a slow-but-working step look identical to a
    # genuinely hung one for the whole duration. stream=True instead inherits the real
    # stdout/stderr so output shows up live, at the cost of not being captured into self.output.
    self.stream = stream

  def __str__(self):
    desc = f"{self.name} : {self.margs}" if len(
        self.margs) > 0 else f"{self.name} :"
    for line in self.output.splitlines():
      if line:
        desc += f'\n  {line}'
    if not self.success:
      desc += '\n  Error: Task Failed'
    return desc

  def run(self):
    """ Run the command line task or tasks sequentially and keep track of failures, stops at the first failure"""
    for args in self.margs:
      if self.stream:
        out = subprocess.run(args, cwd=self.wd, shell=self.shell, check=False)
        self.output += '(output streamed directly to the console above, not captured)'
      else:
        out = subprocess.run(args, cwd=self.wd, shell=self.shell, check=False,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.output += out.stdout.decode()
      self.success = out.returncode == 0
      if not self.success:
        break
    return self


def _setup_loopbacks(base_dir) -> List[Task]:
  """ Configure ALSA loopbacks using snd_aloop kernel module """
  return [Task('copy loopback module configuration', multiargs=[
      f'sudo cp {base_dir}/config/modules.conf /etc/modules'.split(),
      f'sudo cp {base_dir}/config/sound.conf /etc/modprobe.d/sound.conf'.split(),
  ]).run()]


def _install_os_deps(env, progress, with_alsa, deps=_os_deps.keys(), dep_filter: List[str] = []) -> List[Task]:
  def print_progress(tasks):
    progress(tasks)
    return tasks
  tasks = []

  # The commit service leaves the boot partition ro for safety between boots, but apt
  # operations below (dist-upgrade, package installs) can trigger kernel postinst scripts
  # (e.g. update-initramfs) that write here, so remount rw for the duration of dependency
  # install and restore ro at the end.
  _boot_firmware = "/boot/firmware"
  tasks += print_progress([Task(f"remount {_boot_firmware} rw",
                          ['sudo', 'mount', '-o', 'remount,rw', _boot_firmware]).run()])

  # initramfs-tools determines the root device by resolving /proc/mounts's source entry, which
  # the kernel reports as the symbolic "/dev/root" (not a real node in /dev) whenever root= is
  # set via PARTUUID on the kernel cmdline - required for the A/B scheme. That resolution fails
  # outright ("mkinitramfs: failed to determine device for /"), which aborts any kernel package's
  # postinst hook below (e.g. during dist-upgrade) that regenerates the initramfs. MODULES=most
  # is the workaround mkinitramfs's own error message points at - it bundles a broad module set
  # instead of introspecting the (unresolvable) root device to decide what's needed.
  tasks += print_progress([Task("work around initramfs-tools root-device detection failure",
                          ['sudo', 'sed', '-i', 's/^MODULES=.*/MODULES=most/', '/etc/initramfs-tools/initramfs.conf']).run()])

  if env['is_amplipi']:
    # SSH host keys live on /data (survive OS updates, give each unit a stable identity across
    # A/B slot swaps) with /etc/ssh/ssh_host_* symlinked to them - same real-content-on-/data
    # pattern as the LMS data migration below. This used to only live in build_golden_slot's own
    # bash logic, which meant a plain deploy (like this one) never set it up on its own - doing it
    # here too closes that gap. Guarded on -L so repeat runs are a no-op once already symlinked.
    # If real keys already exist locally (e.g. this box's first time running this step) they're
    # moved to /data rather than discarded, so existing known_hosts entries for it stay valid.
    tasks += print_progress([Task("set up SSH host key symlinks to /data",
                            args='sudo mkdir -p /data/ssh; '
                            'if [ ! -L /etc/ssh/ssh_host_ecdsa_key ]; then '
                            '  for key in ssh_host_ecdsa_key ssh_host_ecdsa_key.pub ssh_host_ed25519_key ssh_host_ed25519_key.pub ssh_host_rsa_key ssh_host_rsa_key.pub; do '
                            '    if [ -e "/etc/ssh/$key" ] && [ ! -e "/data/ssh/$key" ]; then sudo mv "/etc/ssh/$key" "/data/ssh/$key"; else sudo rm -f "/etc/ssh/$key"; fi; '
                            '    sudo ln -s "/data/ssh/$key" "/etc/ssh/$key"; '
                            '  done; '
                            'fi',
                            shell=True).run()])

    # Raspberry Pi OS's first-boot key regen (regenerate_ssh_host_keys.service) deletes whatever's
    # at /etc/ssh/ssh_host_* and calls ssh-keygen -A directly on the root the moment a genuinely
    # fresh slot boots for the first time - unlinking the symlinks above before they ever take
    # effect and bypassing /data entirely. build_golden_slot masks this before a fresh root ever
    # boots (the real fix, since by the time this deploy step runs that first boot has already
    # happened); masking it again here is just defensive for any box provisioned some other way.
    # We already give each real shipped unit a unique identity deliberately via scripts/cleanup,
    # so this service is redundant with, and fights, that.
    tasks += print_progress([Task("mask regenerate_ssh_host_keys.service",
                            ['sudo', 'systemctl', 'mask', 'regenerate_ssh_host_keys']).run()])

  # Comment out deb http://raspbian.raspberrypi.org/raspbian/ buster main contrib non-free rpi from /etc/apt/sources.list to avoid hitting up a now empty apt source
  tasks += print_progress([Task('Deactivate apt updates for outdated OS',
                                args='file=/etc/apt/sources.list; '
                                'if grep -q "buster" "$file" && [ "$(head -c 1 "$file")" != "#" ]; then '  # If file is for rasbian buster and the first line isn't already commented out, comment out the first line
                                '  sudo sed -i "s@^deb http://raspbian.raspberrypi.org/raspbian/ buster@#deb http://raspbian.raspberrypi.org/raspbian/ buster@g" "$file"; '
                                'fi',
                                shell=True
                                ).run()])

  # TODO: add extra apt repos
  # find latest apt packages. --allow-releaseinfo-change automatically allows the following change:
  # Repository 'http://raspbian.raspberrypi.org/raspbian buster InRelease' changed its 'Suite' value from 'stable' to 'oldstable'
  tasks += print_progress([Task('get latest debian packages',
                                'sudo apt-get update --allow-releaseinfo-change'.split()).run()])

  # Upgrade current packages
  print_progress(
      [Task("upgrading debian packages, this will take 10+ minutes", success=True)])
  # DEBIAN_FRONTEND=noninteractive used to only be set in development mode - meaning a normal
  # (non-dev) run could hit a package's debconf prompt (e.g. from postinst/preinst scripts;
  # --assume-yes only answers apt's own confirmations, not those) and hang indefinitely waiting
  # on a TTY nobody's watching, with zero output to suggest it was even still doing anything.
  # stream=True on top of that so this step's output shows up live instead of being fully
  # buffered until it finishes - a slow-but-working run should be distinguishable from a hung one.
  tasks += print_progress([Task('upgrade debian packages',
                          'sudo DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade --assume-yes'.split(),
                          stream=True).run()])

  # organize stuff to install
  packages = set()
  files = []
  scripts: Dict[str, List[str]] = {}
  for dep in deps:
    if filter_deps(dep, dep_filter):
      continue

    install_steps = _os_deps[dep]
    if install_steps.get('amplipi_only', False) and not env['is_amplipi']:
      continue
    if 'copy' in install_steps:
      files += install_steps['copy']
    if 'apt' in install_steps:
      packages.update(install_steps['apt'])
    if 'script' in install_steps:
      scripts[dep] = install_steps['script']

  # copy files
  for file in files:
    _from = file['from'].replace('ARCH', env['arch'])
    _to = file['to']
    # prepend home to relative paths
    if _from[0] != '/':
      _from = f"{env['base_dir']}/{_from}"
    if _to[0] != '/':
      _to = f"{env['base_dir']}/{_to}"
    _sudo = "sudo " if 'sudo' in file else ""
    _parent_dir = pathlib.Path(_to).parent
    if _sudo or not _parent_dir.exists():
      tasks += print_progress([Task(f"creating parent dir(s) for {_from}", f"{_sudo}mkdir -p {_parent_dir}".split()).run()])
    tasks += print_progress([Task(f"copy -f {_from} to {_to}", f"{_sudo}cp -f {_from} {_to}".split()).run()])  # shairport needs the -f if it is running
  if with_alsa or env['is_amplipi'] or env['is_ci']:
    # copy alsa configuration file
    _from = f"{env['base_dir']}/config/asound.conf"
    _to = "/etc/asound.conf"
    tasks += print_progress(
        [Task(f"copy {_from} to {_to}", f"sudo cp {_from} {_to}".split()).run()])
    # copy boot_config.txt RPi firmware configuration file
    _boot_config_from = f"{env['base_dir']}/config/boot_config.txt"
    _boot_config_to = f"{_boot_firmware}/config.txt"
    tasks += print_progress([Task(f"copy {_boot_config_from} to {_boot_config_to}",
                            f"sudo cp {_boot_config_from} {_boot_config_to}".split()).run()])
    # fix usb soundcard name
    usb_audio_rule_path = '/etc/udev/rules.d/85-amplipi-usb-audio.rules'
    if not os.path.exists(usb_audio_rule_path):
      _from = f"{env['base_dir']}/config/85-amplipi-usb-audio.rules"
      _to = usb_audio_rule_path
      tasks += print_progress([Task('fix usb soundcard id', multiargs=[
          # add new rule (udev watches this directory for changes)
          f"sudo cp {_from} {_to}".split(),
          # trigger an 'add' action on the 'sound' subsystem
          'sudo udevadm trigger -s sound -c add'.split(),
          # wait for udev rules to fire and settle
          'udevadm settle'.split(),
      ]).run()])
    # disable pulseaudio (it was muting some inputs and is not needed)
    tasks += print_progress([Task('disable pulseaudio', multiargs=[
        'systemctl --user mask pulseaudio.socket'.split(),
        'systemctl --user mask pulseaudio.service'.split(),
    ]).run()])
    # serial port permission granting
    tasks.append(Task('Check serial permissions', 'groups'.split()).run())
    tasks[-1].success = 'pi' in tasks[-1].output
    if not tasks[-1].success:
      tasks += print_progress([Task("Giving pi serial permission. !!!AmpliPi will need to be restarted after this!!!",
                              "sudo gpasswd -a pi dialout".split()).run()])
      return tasks
    # setup tmpfs (ram disk)
    tasks += print_progress(_setup_tmpfs(env['config_dir'], env))
    # setup crontab - Replace the entire Pi user's crontab with AmpliPi's config/crontab
    # and point it to the AmpliPi install location's script directory.
    tasks += print_progress([Task("Setting up crontab", [
                            f"cat {env['base_dir']}/config/crontab | sed 's@SCRIPTS_DIR@{env['base_dir']}/scripts@' | crontab -"], shell=True).run()])
    # setup loopbacks
    tasks += print_progress(_setup_loopbacks(env['base_dir']))
  # squeezeboxserver (the system user the lyrionmusicserver package runs as) is normally created
  # by that package's own postinst via adduser --system, which assigns whatever UID happens to be
  # next free at the time - not a fixed number the way the pi user's UID is. Since /data/lms
  # (shared across both A/B slots) can only have one numeric owner, a different UID on a
  # different slot/reinstall silently breaks LMS there (it fails to write its own logs/cache and
  # exits quickly with no error output) - this has already happened twice on the same hardware,
  # caused by an unrelated package (shairport-sync) grabbing the UID first depending on dpkg's
  # internal install order. Pre-creating squeezeboxserver here, before the single batched
  # apt-get install below runs any package's postinst at all, makes it win that race
  # deterministically every time instead of depending on install order - adduser-based postinst
  # scripts (this is standard Debian packaging convention, not specific to any one package) check
  # for an existing user first and no-op if one's already there. Only applied if the user doesn't
  # already exist, so this only affects fresh installs (re-numbering an existing user's UID would
  # risk breaking whatever it already owns).
  tasks += print_progress([Task("pre-create squeezeboxserver with a pinned UID",
                          args='if ! id squeezeboxserver >/dev/null 2>&1; then '
                          '  sudo useradd --system --uid 105 --gid nogroup --no-create-home --shell /usr/sbin/nologin squeezeboxserver; '
                          'fi',
                          shell=True).run()])

  # install debian packages
  tasks += print_progress([Task('install debian packages',
                          'sudo apt-get install -y'.split() + list(packages)).run()])

  # Run scripts
  for dep, script in scripts.items():
    print(f"\ndep: {dep} \nscript: {script}\n")
    if filter_deps(dep, dep_filter):
      continue
    sh_loc = f'{env["base_dir"]}/install_{dep}.sh'
    with open(sh_loc, 'a') as sh:
      for scrap in script:
        sh.write(scrap + '\n')
    shargs = f'bash {sh_loc}'.split()
    clean = f'rm {sh_loc}'.split()
    tasks += print_progress(
        [Task(f'run {dep} install script', args=shargs, wd=env['base_dir']).run()])
    tasks += print_progress(
        [Task(f'remove {dep} temporary script', args=clean, wd=env['base_dir']).run()])

  # cleanup
  sp_check_tasks, sp_active = _service_status('shairport-sync', system=True)
  tasks += sp_check_tasks
  if sp_active:
    # shairport-sync install sets up a daemon we need to stop, remove it
    tasks += print_progress(_stop_service('shairport-sync', system=True))
    tasks += print_progress(_disable_service('shairport-sync', system=True))

  tasks += print_progress([Task(f"remount {_boot_firmware} ro",
                          ['sudo', 'mount', '-o', 'remount,ro', _boot_firmware]).run()])

  return tasks


def _install_python_deps(env: dict, deps: List[str]):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(env['script_dir'])
    tasks += [Task('install python packages',
                   'bash install_python_deps.bash'.split()).run()]
    os.chdir(last_dir)
  return tasks


def _install_custom_deps(dep):
  tasks = []
  _, extension = os.path.splitext(dep)
  if os.path.isfile(f"/data/update_scripts/{dep}") and extension.lower() == ".sh":
    tasks += [Task(f'install custom settings from {dep}',
                   f'bash /data/update_scripts/{dep}'.split()).run()]
  return tasks


def _add_desktop_icon(env, directory: pathlib.Path, name, command) -> Task:
  """ Add a desktop icon to the pi """
  entry = f"""[Desktop Entry]
Name={name}
Icon=lxterminal
Exec=lxterminal -t "{name}" --working-directory={env["base_dir"]} -e {command}
Type=Application
Terminal=false
Categories=Utility;
"""
  success = True
  try:
    filepath = directory.joinpath(f'{name}.desktop')
    with open(f'{filepath}', 'w') as icon:
      icon.write(entry)
  except Exception:
    success = False
  return Task(f'Add desktop icon for {name}', success=success)


def _setup_tmpfs(config_dir, env):
  """ Adds tmpfs entries used by AmpliPi to /etc/fstab """
  # Warning: these hide the existing filesystem,
  # if anything is already present at the path created.
  tmpfs_opts = 'defaults,noatime,uid=pi,gid=pi,size=100M'
  conf_entry = f'amplipi/config {config_dir}/srcs tmpfs {tmpfs_opts} 0 0'
  web_entry = f'amplipi/web {config_dir}/web/generated tmpfs {tmpfs_opts} 0 0'
  args = [
      'sudo sed -i "/^amplipi/d" /etc/fstab',
      f'echo {conf_entry} | sudo tee -a /etc/fstab',
      f'echo {web_entry} | sudo tee -a /etc/fstab',
      f'mkdir -p {config_dir}/srcs {config_dir}/web/generated',
  ]
  if not env['is_ci']:
    args.append(f'sudo mount -a')

  tasks = [Task('Add tmpfs entries to fstab.', multiargs=args, shell=True).run()]
  return tasks


def _web_service(directory: str, user: str = 'pi'):
  return f"""\
[Unit]
Description=Amplipi Home Audio System
After=network.target

[Service]
User={user}
Group={user}
Type=simple
WorkingDirectory={directory}
ExecStart=/usr/bin/authbind --deep {directory}/venv/bin/python -m uvicorn --host 0.0.0.0 --port 80 amplipi.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
"""


def _tasks_service(directory: str, user: str = 'pi'):
  return f"""\
[Unit]
Description=AmpliPi Background Tasks
After=redis-server.service

[Service]
User={user}
Group={user}
Type=simple
WorkingDirectory={directory}
ExecStart={directory}/venv/bin/python -m celery -A amplipi.tasks worker
Restart=always

[Install]
WantedBy=multi-user.target
"""


def _update_service(directory: str, port: int = 5001, user: str = 'pi'):
  return f"""\
[Unit]
Description=Amplipi Software Updater
After=network.target

[Service]
User={user}
Group={user}
Type=simple
WorkingDirectory={directory}
ExecStart={directory}/venv/bin/python -m uvicorn amplipi.updater.asgi:app --host 0.0.0.0 --port {port}
Restart=on-abort

[Install]
WantedBy=multi-user.target
"""


def _display_service(directory: str, user: str = 'pi'):
  return f"""\
[Unit]
Description=Amplipi Front Panel Display

[Service]
User={user}
Group={user}
Type=simple
WorkingDirectory={directory}
ExecStart={directory}/venv/bin/python -m amplipi.display.display
Restart=on-abort

[Install]
WantedBy=multi-user.target
"""


def _audiodetector_service(base_dir: str, config_dir: str, user: str = 'pi'):
  return f"""\
[Unit]
Description=Amplipi RCA Input Audio Detector
ConditionPathExists=!/data/.config/amplipi/is_streamer

[Service]
User={user}
Group={user}
Type=simple
WorkingDirectory={config_dir}/srcs
ExecStart={base_dir}/amplipi/audiodetector/audiodetector
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""


def systemctl_cmd(system: bool) -> str:
  """ Get the relevant systemctl command based on @system {True: system, False: user} """
  if system:
    return 'sudo systemctl'
  # user
  return 'systemctl --user'


def _service_status(service: str, system: bool = True) -> Tuple[List[Task], bool]:
  # Status can be: active, reloading, inactive, failed, activating, or deactivating
  cmd = f'{systemctl_cmd(system)} is-active {service}'
  tasks = [Task(f'Check {service} status', cmd.split()).run()]
  # The exit code reflects the status of the service, not the command itself.
  # Just assume the command was run successfully.
  tasks[0].success = True
  active = 'active' in tasks[0].output and 'inactive' not in tasks[0].output
  return (tasks, active)


def _stop_service(name: str, system: bool = True) -> List[Task]:
  service = f'{name}.service'
  tasks, running = _service_status(service, system)
  if running:
    cmd = f'{systemctl_cmd(system)} stop {service}'
    tasks.append(Task(f'Stop {service}', cmd.split()).run())
  return tasks


def _remove_service(name: str, system: bool = True) -> List[Task]:
  filename = f'{name}.service'
  tasks = [Task(f'Remove {filename}')]
  if system:
    path = pathlib.Path('/etc/systemd/system') / filename
    result = subprocess.run(['sudo', 'rm', '-f', str(path)], capture_output=True)
    tasks[0].success = result.returncode == 0
    tasks[0].output = f'Removed {path}' if tasks[0].success else result.stderr.decode()
  else:
    path = pathlib.Path.home().joinpath('.config/systemd/user') / filename
    try:
      path.unlink()
      tasks[0].output = f'Removed {path}'
      tasks[0].success = True
    except Exception as exc:
      tasks[0].output = str(exc)
      tasks[0].success = False
  return tasks


def _enable_service(name: str, system: bool = True) -> List[Task]:
  service = f'{name}.service'
  cmd = f'{systemctl_cmd(system)} enable {service}'
  tasks = [Task(f'Enable {service}', cmd.split()).run()]
  return tasks


def _disable_service(name: str, system: bool = True) -> List[Task]:
  service = f'{name}.service'
  cmd = f'{systemctl_cmd(system)} disable {service}'
  tasks = [Task(f'Disable {service}', cmd.split()).run()]
  return tasks


def _start_restart_service(name: str, restart: bool, test_url: Union[None, str] = None, system: bool = True) -> List[Task]:
  service = f'{name}.service'
  if restart:
    tasks = [Task(f'Restart {service}', f'{systemctl_cmd(system)} restart {service}'.split()).run()]
  else:
    tasks = [Task(f'Start {service}', f'{systemctl_cmd(system)} start {service}'.split()).run()]

  # wait a bit, so initial failures are detected before is-active is called
  if tasks[-1].success:
    # we need to check if the service is running
    for _ in range(50):  # retry for 10 seconds, giving the service time to start
      task_check, running = _service_status(service, system)
      if running:
        break
      time.sleep(0.2)
    tasks += task_check
    if test_url and running:
      task = None
      for _ in range(60):  # retry for 30 seconds, giving the server time to start
        task = _check_url(test_url)
        if task.success:
          break
        time.sleep(0.5)
      tasks.append(task)
    elif name == 'amplipi':
      tasks[-1].output += "\ntry checking this service failure using 'scripts/run_debug_webserver' on the system"
      tasks.append(Task(
          f'Check {service} Status', f'{systemctl_cmd(system)} status {service}'.split()).run())
    elif 'amplipi-updater' in name:
      tasks[-1].output += "\ntry debugging this service failure using 'scripts/run_debug_updater' on the system"
      tasks.append(Task(
          f'Check {service} Status', f'{systemctl_cmd(system)} status {service}'.split()).run())
  return tasks


def _start_service(name: str, test_url: Union[None, str] = None, system: bool = True) -> List[Task]:
  return _start_restart_service(name, restart=False, test_url=test_url, system=system)


def _restart_service(name: str, test_url: Union[None, str] = None, system: bool = True) -> List[Task]:
  return _start_restart_service(name, restart=True, test_url=test_url, system=system)


def _create_dir(directory: str) -> List[Task]:
  tasks = [Task(f'Create directory {directory}')]
  path = pathlib.Path(directory)
  if path.exists():
    tasks[-1].success = True
    tasks[-1].output = f'Directory {directory} already exists'
  else:
    try:
      path.mkdir(parents=True)
      tasks[-1].success = True
      tasks[-1].output = f'Created {directory}'
    except:
      tasks[-1].output = f'Failed to create {directory}'
  return tasks


def _create_service(name: str, config: str, env: dict) -> List[Task]:
  filename = f'{name}.service'
  tasks = []

  if env.get('is_ci', False):
    # CI: write to user-level directory without sudo
    directory = pathlib.Path.home().joinpath('.config/systemd/user')
    tasks += _create_dir(str(directory))
    tasks.append(Task(f'Create {filename}'))
    try:
      with directory.joinpath(filename).open('w+') as svc_file:
        svc_file.write(config)
      tasks[-1].success = True
      tasks[-1].output = f'Created {filename}'
    except Exception as exc:
      tasks[-1].output = f'Failed to create {filename}: {exc}'
    tasks.append(Task('Reload systemd config', 'systemctl --user daemon-reload'.split()).run())
  else:
    # Hardware: write to system-level directory using a temp file + sudo cp
    dest = f'/etc/systemd/system/{filename}'
    tasks.append(Task(f'Create {filename}'))
    tmp_path = None
    try:
      with tempfile.NamedTemporaryFile(mode='w', suffix='.service', delete=False) as tmp:
        tmp.write(config)
        tmp_path = tmp.name
      result = subprocess.run(['sudo', 'cp', tmp_path, dest], capture_output=True)
      tasks[-1].success = result.returncode == 0
      tasks[-1].output = f'Created {dest}' if tasks[-1].success else result.stderr.decode()
    except Exception as exc:
      tasks[-1].output = f'Failed to create {filename}: {exc}'
    finally:
      if tmp_path:
        try:
          os.unlink(tmp_path)
        except Exception:
          pass
    tasks.append(Task('Reload systemd config', 'sudo systemctl daemon-reload'.split()).run())
  return tasks


PORT_FILE = '/etc/authbind/byport/80'


def _configure_authbind() -> List[Task]:
  """ Configure access to port 80 so we can run amplipi as a non-root user

  Executes the following commands
  sudo touch /etc/authbind/byport/80
  sudo chmod 777 /etc/authbind/byport/80
  """
  tasks = []
  if not os.path.exists(PORT_FILE):
    tasks.append(Task('Setup autobind', multiargs=[
        f'sudo touch {PORT_FILE}'.split(),
        f'sudo chmod 777 {PORT_FILE}'.split()
    ]).run())
  elif os.stat(PORT_FILE).st_mode != 0o1000777:
    tasks.append(
        Task('Setup autobind', f'sudo chmod 777 {PORT_FILE}'.split()).run())
  return tasks



def _api_key() -> Optional[str]:
  """ Get a singular API key for use with the updater """
  user_file_path = os.path.join('/data', '.config', 'amplipi', 'users.json')
  try:
    with open(user_file_path, encoding='utf-8') as user_file:
      users = json.load(user_file)
      for user, config in users.items():
        if "access_key" in config:
          return config["access_key"]
  except Exception as e:
    # This is a little wholesale, but there is the case where a users file doesn't exist.
    # Additionally, we do not want to print any sensitive information to the console; we
    # simply bail.
    return None
  return None


def _copy_old_config(dest_dir: str) -> Task:
  # try to copy the config of the current running amplipi service into dest_dir/house.json
  # success is desirable, but not strictly required since the config will be generated from defaults if missing.
  # This helps us tolerate a changing `dest_dir`, but there's a good chance the service will write-back
  # its config to this location too.
  task = Task("Write running config to disk")
  url = "http://localhost/api"
  key = _api_key()
  if key:
    url += f'?api-key={key}'
  try:
    req = requests.get(url)
    if req.ok:
      with open(f'{dest_dir}/house.json', 'wb') as f:
        f.write(req.content)
      task.output += "\nOk!"
      task.success = True
  except Exception as e:
    task.output += f"\nError: {e}"
    task.output += f"\nContinuing anyways, in case this current install is broken and needs an upgrade."
    task.success = True
  return task


def _create_backup(env, suffix: str = "") -> List[Task]:
  task = Task('Take a configuration backup', f"{env['base_dir']}/scripts/backup_config.sh {suffix}".split())
  task.run()
  # Everything that consumes this wants a List, so let's give 'em a list.
  return [task]


def _check_url(url) -> Task:
  task = Task(f'Check url {url}')
  key = _api_key()
  if key:
    task.name += " (with api key)"
    url += f'?api-key={key}'
  try:
    req = requests.get(url)
    if req.ok:
      task.output += "\nOk!"
      task.success = True
    else:
      task.output += f"\nError: {req.reason}"
  except:
    task.output = 'Failed to check url, this happens when the server is offline'
  return task


def _check_version(url) -> Task:
  task = Task('Checking version reported by API')
  task.output = f'\nusing: {url}'
  key = _api_key()
  if key:
    url += f"?api-key={key}"
    task.output += " (with api key)"
  try:
    req = requests.get(url)
    if req.ok:
      reported_version = req.json()['info']['version']
      task.success = True
      task.output += f'\nversion={reported_version}'
  except Exception:
    task.output = 'Failed checking version'
  return task


def _update_web(env: dict, restart_updater: bool, progress) -> List[Task]:
  def print_progress(tasks):
    progress(tasks)
    return tasks

  user = env.get('user', 'pi')
  tasks = []

  if not env['is_ci']:
    # try to copy the old config into the potentially new directory
    # This fixes some potential update issues caused by migrating install to a different directory
    # (using the web updated the install dir used to be amplipi-dev2 and is now amplipi-dev)
    tasks += print_progress([_copy_old_config(env['config_dir'])])

    # stop amplipi before reconfiguring authbind
    tasks += print_progress(_stop_service('amplipi'))

  # bringup amplipi and updater separately
  tasks += print_progress(_configure_authbind())
  tasks += print_progress(_create_service('amplipi', _web_service(env['base_dir'], user), env))
  tasks += print_progress(_enable_service('amplipi'))
  if not env['is_ci']:
    tasks += print_progress(_start_service('amplipi', test_url='http://0.0.0.0'))
    if not tasks[-1].success:
      return tasks
    tasks += print_progress([_check_version('http://0.0.0.0/api')])

  tasks += print_progress(_create_service('amplipi-updater', _update_service(env['base_dir'], user=user), env))
  tasks += print_progress(_enable_service('amplipi-updater'))
  if not env['is_ci']:
    if restart_updater:
      tasks += print_progress(_stop_service('amplipi-updater'))
      tasks += print_progress(_start_service('amplipi-updater', test_url='http://0.0.0.0:5001/update'))
    else:
      # start a second updater service and check if it serves a url
      # this allow us to verify the update the updater probably works
      tasks += print_progress(_create_service('amplipi-updater-test', _update_service(env['base_dir'], port=5002, user=user), env))
      tasks += print_progress(_start_service('amplipi-updater-test', test_url='http://0.0.0.0:5002/update'))
      # stop and disable the service so it doesn't start up on a reboot
      tasks += print_progress(_stop_service('amplipi-updater-test'))
      tasks += print_progress(_remove_service('amplipi-updater-test'))

  # bring up amplipi-tasks
  tasks += print_progress(_create_service('amplipi-tasks', _tasks_service(env['base_dir'], user), env))
  tasks += print_progress(_enable_service('amplipi-tasks'))
  if not env['is_ci']:
    tasks += print_progress(_restart_service('amplipi-tasks'))

  return tasks


def _update_display(env: dict, progress) -> List[Task]:
  def print_progress(tasks):
    progress(tasks)
    return tasks
  user = env.get('user', 'pi')
  tasks = []
  tasks += print_progress(_create_service('amplipi-display', _display_service(env['base_dir'], user), env))
  tasks += print_progress(_enable_service('amplipi-display'))
  if not env['is_ci']:
    tasks += print_progress(_restart_service('amplipi-display'))
  return tasks


def _update_audiodetector(env: dict, progress) -> List[Task]:
  """ Create and run the RCA input audio detector service if on AmpliPi hardware """
  def print_progress(tasks):
    progress(tasks)
    return tasks
  if not env['is_amplipi'] and not env['is_ci']:
    return [Task(name='Update Audio Detector', output='Not on AmpliPi', success=False)]
  user = env.get('user', 'pi')
  tasks = []
  tasks += print_progress([Task('Build audiodetector', f'make -C {env["base_dir"]}/amplipi/audiodetector'.split()).run()])
  tasks += print_progress(_create_service('amplipi-audiodetector', _audiodetector_service(env['base_dir'], env['config_dir'], user), env))
  tasks += print_progress(_enable_service('amplipi-audiodetector'))
  if not env['is_ci']:
    tasks += print_progress(_restart_service('amplipi-audiodetector'))
  return tasks


def _check_password(env: dict, progress) -> List[Task]:
  """ If a random default password hasn't been generated, generate, set, and
      store one. This is just for older AmpliPi versions that didn't get a
      random password set at checkout.
  """
  task = Task('Set a default password')
  task.success = True
  pass_file = os.path.join(env['config_dir'], 'default_password.txt')
  if env['user'] != 'pi':
    task.output = 'Not setting a default password: not running as pi user'
  elif not env['is_amplipi']:
    task.output = 'Not setting a default password: not running on AmpliPi'
  elif os.path.exists(pass_file):
    task.output = 'Default password already generated'
  elif not os.path.exists('/run/sshwarn'):
    # no default pass file, but password is not 'raspberry' so already user-set
    task.margs = [f'mkdir -p {env["config_dir"]}'.split(),
                  f'touch {pass_file}'.split()]
    task.run()
  else:
    # at this point the pi default password of 'raspberry' is still set
    task.margs = [f"{env['base_dir']}/scripts/set_pass"]
    task.run()
  progress([task])
  return [task]


def _fw_ver_from_filename(name: str) -> int:
  """ Input: .bin filename, with the pattern 'preamp_X.Y.bin'.
      X = major version, Y = minor version.
      The result is a single integer 256*X + Y
  """
  fw_match = re.search(r'preamp_(\d+)\.(\d+)', name)
  if fw_match is not None and len(fw_match.groups()) >= 2:
    major = int(fw_match[1])
    minor = int(fw_match[2])
    return (major << 8) + minor
  # by default return 0 so non-standard file names won't be considered
  return 0


def _update_firmware(env: dict, progress) -> List[Task]:
  """ If on AmpliPi with preamp hardware, update to the latest firmware """
  task = Task('Flash latest preamp firmware')
  if env['is_amplipi'] and not env['is_streamer']:
    latest_ver = 0
    latest_file = ''
    for f in glob.glob(f"{env['base_dir']}/fw/bin/*.bin"):
      ver = _fw_ver_from_filename(f)
      if ver > latest_ver:
        latest_ver = ver
        latest_file = f
    if latest_ver > 0:
      os.chdir(env['base_dir'])
      task.margs = [
          f'bash scripts/program_firmware {latest_file}'.split()]
      task.run()
    else:
      task.output = f"Couldn't find any firmware in {env['base_dir']}/fw/bin"
      task.success = False
  else:
    task.output = 'Not on AmpliPi with Preamp - No firmware update necessary'
    task.success = True
  progress([task])
  return [task]


def print_task_results(tasks: List[Task]) -> None:
  """ Print out all of the task results """
  for task in tasks:
    print(task)


def fix_file_props(env, progress) -> List[Task]:
  """ Fix file properties that get smashed by Windows """
  tasks = []
  lplatform = platform.platform().lower()
  if 'linux' in lplatform:
    needs_exec = ['scripts/*', '*/*.bash', '*/*.sh']
    make_exec = set()
    for exec_name in needs_exec:
      make_exec.update(glob.glob(f"{env['base_dir']}/{exec_name}"))
    cmd = f"chmod +x {' '.join(make_exec)}"
    tasks += [Task('Make scripts executable', cmd.split()).run()]
  progress(tasks)
  return tasks


def add_tests(env, progress) -> List[Task]:
  """ Add test icons """
  tests = [
      ('Ethernet', './hw/tests/ethernet.bash --wait'),
      ('USB Ports', './hw/tests/usb.py'),
      ('Inputs', './hw/tests/built_in.bash inputs'),
      ('Program Main', './hw/tests/program_preamps.bash'),
      ('Program Main + Exp Preamp', './hw/tests/program_preamps.bash 2'),
      ('Program Main + 2 Exp Preamps', './hw/tests/program_preamps.bash 3'),
      ('Amplifier', './hw/tests/built_in.bash amp'),
      ('LEDs', './hw/tests/built_in.bash led'),
      ('Preamp', './hw/tests/built_in.bash preamp'),
      ('Expander Preamp', './hw/tests/built_in.bash preamp --expansion'),
      ('Preouts', './hw/tests/built_in.bash preout'),
      ('Display', './hw/tests/display.bash --wait'),
      ('Peak Detect', 'venv/bin/python ./hw/tests/peak_detect.py'),
      ('Fans and Power', './hw/tests/fans.bash'),
      # just for info, not a specific test
      ('Preamp Status', 'venv/bin/python ./hw/tests/preamp.py -w'),
      ('Streamer', './hw/tests/built_in.bash streamer'),
      ('Config Streamer', './hw/tests/config_streamer.bash'),
      ('Aux Input', './hw/tests/built_in.bash aux'),
  ]
  tasks = []

  # create the ~/tests directory if it doesn't already exist
  directory = pathlib.Path.home().joinpath('Desktop', 'tests')
  tasks += _create_dir(str(directory))

  tasks += [Task('Remove old tests',
                 [f'rm -f {str(directory)}/*'], shell=True).run()]
  for test in tests:
    tasks += [_add_desktop_icon(env, directory, test[0], test[1])]
  progress(tasks)
  return tasks


def install(os_deps=True, python_deps=True, custom_deps=True, web=True, restart_updater=False,
            display=True, audiodetector=True, firmware=True, password=True,
            progress=print_task_results, development=False, ci_mode=False, with_alsa=False,
            dep_filter: List[str] = []) -> bool:
  """ Install and configure AmpliPi's dependencies """
  # pylint: disable=too-many-return-statements
  tasks = [Task('setup')]

  def failed():
    for task in tasks:
      if not task.success:
        # __str__() on Task renders with an "Error"ed suffix
        print(str(task))
        return True
    return False

  if not development:
    # Find the version number line, break off the version= portion, then split on the decimals to separate major, middle, and minor revisions
    # Example output:
    # using: http://0.0.0.0/api
    # version=0.3.1
    # No match at all (rather than a version below 0.4.0) means there's nothing already running
    # on /api to check - a fresh install with no prior AmpliPi deployment, which isn't what this
    # gate is for, so just proceed instead of crashing on a None match.
    version_match = re.search(r'version=(\d+\.\d+\.\d+)', str(_check_version('http://0.0.0.0/api').output))
    if version_match:
      version = version_match.group(1).split(".")
      if int(version[0]) == 0 and int(version[1]) < 4:  # Is the version less than version 0.4.0?
        print("Your version is too old to update automatically, please update manually using this guide: https://github.com/micro-nova/AmpliPi/blob/main/docs/imaging_etcher.md")
        return False

  env = _check_and_setup_platform(development, ci_mode)
  if not env['platform_supported'] and not development:
    tasks[0].output = f'untested platform: {platform.platform()}. Please fix this script and make a PR to github.com/micro-nova/AmpliPi'
  else:
    tasks[0].output = str(env)
    tasks[0].success = True
  progress(tasks)
  if failed():
    return False
  tasks += fix_file_props(env, progress)
  if failed():
    return False
  if not env['is_ci']:
    pre_backup = _create_backup(env, "_pre-fw-upgrade")
    progress(pre_backup)
    tasks += pre_backup
  if failed():
    return False
  if os_deps:
    tasks += _install_os_deps(env, progress, with_alsa, _os_deps, dep_filter)
    if failed():
      print('OS dependency install step failed, exiting...')
      return False
  if python_deps:
    with open(os.path.join(env['base_dir'], 'requirements.txt'), encoding='utf-8') as req:
      deps = req.read().splitlines()
      # TODO: embed python progress reporting
      py_tasks = _install_python_deps(env, deps)
      progress(py_tasks)
      tasks += py_tasks
    if failed():
      print('Python dependency install step failed, exiting...')
      return False
  if custom_deps:
    custom_deps_dir = "/data/update_scripts"
    os.makedirs(custom_deps_dir, exist_ok=True)
    custom_deps = os.listdir(custom_deps_dir)
    for dep in custom_deps:
      if dep != "README.md":
        custom_tasks = _install_custom_deps(dep)
        progress(custom_tasks)
        tasks += custom_tasks
        if failed():
          print(f'Custom dependency {dep} failed to install')
  # A deploy overwrites .py source files but never touches leftover __pycache__/*.pyc from a
  # previous run - Python only recompiles a stale .pyc when the source's mtime is strictly newer
  # than what's embedded in it, which isn't guaranteed across a tar/cp-based deploy (this has
  # already caused a real, hard-to-diagnose bug: a service kept running old cached bytecode with
  # an old hardcoded path years after the source was fixed to use /data). Clearing it every time,
  # right before anything below might start a service that imports this code, removes the
  # ambiguity entirely rather than relying on timestamp comparisons lining up correctly.
  pycache_task = [Task('clear stale Python bytecode cache',
                       f'find {env["base_dir"]}/amplipi -name __pycache__ -type d -exec rm -rf {{}} +',
                       shell=True).run()]
  progress(pycache_task)
  tasks += pycache_task
  if web:
    tasks += _update_web(env, restart_updater, progress)
    if failed():
      return False
    # The is_streamer detection will happen in the update_web task
    # we need to refresh this detection, just in case the flag changed
    # the update_firmware task depends on this flag
    _check_and_update_streamer(env)
  if display:
    tasks += _update_display(env, progress)
    if failed():
      return False
  if audiodetector:
    tasks += _update_audiodetector(env, progress)
    if failed():
      return False
  # These are lxterminal-launcher shortcuts for hardware QC tests, meant to be clicked by a
  # technician on an actual desktop GUI - useless (and previously created regardless) on a
  # headless Lite install, which has no desktop and no lxterminal to run them with.
  if env['is_amplipi'] and shutil.which('lxterminal'):
    tasks += add_tests(env, progress)
  if firmware:
    tasks += _update_firmware(env, progress)
    if failed():
      return False
  if password:
    tasks += _check_password(env, progress)
    if failed():
      return False
  if not env['is_ci']:
    post_backup = _create_backup(env, "_post-fw-upgrade")
    progress(post_backup)
    tasks += post_backup
  if failed():
    return False
  if restart_updater:
    # Reboot OS to finish potential kernel upgrade, also restarting the updater
    progress([Task('Reboot os', success=True)])
    subprocess.run('sudo reboot now', shell=True, check=False)
    # updater will not return from here
  if web and not restart_updater:
    # let the user know how to handle a specific failure condition of the old updater
    UPDATER_MSG = """!!! OLDER UPDATERS CAN MISTAKENLY FAIL AFTER THIS !!!

                     Just go back to AmpliPi http://amplipi.local to check out the new features."""
    progress([Task(UPDATER_MSG, success=True)])
  return True


if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Configure AmpliPi installation')
  parser.add_argument('--python-deps', action='store_true', default=False,
                      help='Install python dependencies (using venv)')
  parser.add_argument('--os-deps', action='store_true', default=False,
                      help='Install os dependencies using apt')
  parser.add_argument('--dep-filter', action='append', default=[],
                      help='Define what OS deps to install (useful for testing new install flows efficiently)')
  parser.add_argument('--custom-deps', action='store_true', default=False,
                      help='Install custom dependencies from /data/update_scripts')
  parser.add_argument('--web', '--webserver', action='store_true', default=False,
                      help="Install and configure webserver")
  parser.add_argument('--restart-updater', '--reboot', action='store_true', default=False,
                      help="""Restart AmpliPis OS, rebooting all of Ampli's services \
      Only do this if you are running this from the command line. \
      When this is set False system will need to be restarted to complete an update""")
  # --restart-updater is needed by the web updater and hasn't been changed to --reboot to simplify upgrade/downgrade logic
  parser.add_argument('--display', action='store_true', default=False,
                      help="Install and run the front-panel display service")
  parser.add_argument('--audiodetector', action='store_true', default=False,
                      help="Install and run the RCA input audio detector service")
  parser.add_argument('--firmware', action='store_true', default=False,
                      help="Flash the latest firmware")
  parser.add_argument('--password', action='store_true', default=False,
                      help="Generate and set a new default password for the pi user.")
  parser.add_argument('--development', action='store_true', default=False,
                      help="Enable development mode.")
  parser.add_argument('--ci-mode', action='store_true', default=False,
                      help="Enable CI mode, for automated builds. This mode doesn't attempt to start or check services.")
  parser.add_argument('--with-alsa', action='store_true', default=False,
                      help="Configure alsa config. Automatically set to True if the device being configured has hostname 'amplipi'")
  flags = parser.parse_args()
  print('Configuring AmpliPi installation')
  has_args = flags.python_deps or flags.os_deps or flags.web or flags.restart_updater or flags.display or flags.firmware
  if not has_args:
    print('  WARNING: expected some arguments, check --help for more information')
  if sys.version_info.major < 3 or sys.version_info.minor < 7:
    print('  WARNING: minimum python version is 3.7')
  result = install(os_deps=flags.os_deps, python_deps=flags.python_deps, custom_deps=flags.custom_deps,
                   web=flags.web, display=flags.display, audiodetector=flags.audiodetector,
                   firmware=flags.firmware, password=flags.password,
                   restart_updater=flags.restart_updater, development=flags.development,
                   ci_mode=flags.ci_mode, with_alsa=flags.with_alsa, dep_filter=flags.dep_filter)
  if not result:
    sys.exit(1)
