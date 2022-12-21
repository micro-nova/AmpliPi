#!/usr/bin/python3

""" Update Amplipi's configuration on the raspberry pi or your test setup

This script is initially designed to support local git installs, pi installs, and amplipi installs
"""
import platform
import subprocess
import os
import pathlib
import pwd # username
import glob
from typing import List, Union, Tuple, Dict, Any, Optional
import time
import re
import sys
import requests

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
  'base' : {
    'apt' : ['python3-pip', 'python3-venv', 'curl', 'authbind',
             'python3-pil', 'libopenjp2-7', # Pillow dependencies
             'libatlas-base-dev',           # numpy dependencies
             'stm32flash',                  # Programming Preamp Board
             'xkcdpass',                    # Random passphrase generation
             'systemd-journal-remote',      # Remote/web based log access
             'jq',                          # JSON parser used in check-release script
             # pygobject dependencies (Spotifyd)
             'libgirepository1.0-dev', 'libcairo2-dev'
            ],
  },
  'web' : {
  },
  'logging' : {
    'script' : [
      'echo "reconfiguring secondary logging utility rsyslog to only allow remote logging"',
      f"echo '{RSYSLOG_CFG}' | sudo tee /etc/rsyslog.conf",
      'sudo systemctl enable rsyslog.service', # just in case it was disabled...
      'sudo systemctl restart rsyslog.service',

      'echo "reconfiguring journald to only log to RAM"',
      r'echo -e "[Journal]\nStorage=volatile\nRuntimeMaxUse=64M\nForwardToConsole=no\nForwardToWall=no\n" | sudo tee /etc/systemd/journald.conf',
      'sudo systemctl enable systemd-journald.service',
      'sudo systemctl restart systemd-journald.service',

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
  # streams
  # TODO: can stream dependencies be aggregated from the streams themselves?
  'pandora' : {
    'apt' : [ 'pianobar']
  },
  'airplay' : {
    'apt' : [ 'shairport-sync' ],
    'copy' : [{'from': 'bin/ARCH/shairport-sync-metadata-reader', 'to': 'streams/shairport-sync-metadata-reader'}],
  },
  'internet_radio' : {
    'apt' : [ 'vlc' ]
  },
  'fmradio' : {
    'apt' : [ 'rtl-sdr', 'git', 'build-essential', 'autoconf', 'libsndfile1-dev', 'libliquid-dev' ],
    'script' : [
      'if ! which redsea  > /dev/null; then', # TODO: check version
      '  echo "Installing redsea"',
      '  cd /tmp',
      '  git clone --depth 1 https://github.com/windytan/redsea.git',
      '  cd redsea',
      '  ./autogen.sh && ./configure && make',
      '  sudo make install',
      '  sudo wget https://raw.githubusercontent.com/osmocom/rtl-sdr/master/rtl-sdr.rules -P /etc/udev/rules.d/',
      '  sudo udevadm control --reload-rules',
      '  sudo udevadm trigger',
      'fi',
    ]
  },
  'lms' : {
    'apt': ['libcrypt-openssl-rsa-perl'], # needed for ShairTunes2W support
    'copy' : [{'from': 'bin/ARCH/squeezelite', 'to': 'streams/squeezelite'}],
  },
  'dlna' : {
    'apt' : [ 'uuid-runtime', 'build-essential', 'autoconf', 'automake', 'libtool', 'pkg-config',
              'libupnp-dev', 'libgstreamer1.0-dev', 'gstreamer1.0-plugins-base',
              'gstreamer1.0-plugins-good', 'gstreamer1.0-plugins-bad', 'gstreamer1.0-plugins-ugly',
              'gstreamer1.0-libav', 'gstreamer1.0-alsa', 'git' ],
    'script' : [
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
    ],
  },
  'plexamp' : {
    # TODO: do a full install of plexamp, the partial install below is not useful
    # 'script' : [ './streams/plexamp_nodeinstall.bash' ]
  },
  'spotify' : {
    'copy' : [{'from': 'bin/ARCH/spotifyd', 'to': 'streams/spotifyd'}],
  }
}

def _check_and_setup_platform():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  env = {
    'user': pwd.getpwuid(os.getuid()).pw_name,
    'has_apt': False,
    'is_git_repo': False,
    'platform_supported': False,
    'script_dir': script_dir,
    'base_dir': script_dir.rsplit('/', 1)[0],
    'is_amplipi': False,
    'arch': 'unknown',
  }

  # Get the platform name
  # - example pi output: Linux-5.4.51-v7+-armv7l-with-debian-10.4
  # - example ubuntu output: Linux-5.4.0-66-generic-x86_64-with-Ubuntu-18.04-bionic
  lplatform = platform.platform().lower()

  # Figure out what platform we are on since we expect to be on a raspberry pi or a debian based development system
  if 'linux' in lplatform:
    if 'x86_64' in lplatform:
      apt = subprocess.run('which apt-get'.split(), check=True)
      env['arch'] = 'x64'
      if apt:
        env['has_apt'] = True
        env['platform_supported'] = True
    elif 'armv7l' in lplatform and 'debian' in lplatform:
      env['arch'] = 'arm'
      env['platform_supported'] = True
      env['has_apt'] = True
      env['is_amplipi'] = 'amplipi' in platform.node() # checks hostname

  return env

class Task:
  """ Task runner for scripted installation tasks """
  def __init__(self, name: str, args:Optional[List[str]]=None, multiargs=None, output='', success=False, wd=None, shell=False):
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

  def __str__(self):
    desc = f"{self.name} : {self.margs}" if len(self.margs) > 0 else f"{self.name} :"
    for line in self.output.splitlines():
      if line:
        desc += f'\n  {line}'
    if not self.success:
      desc += '\n  Error: Task Failed'
    return desc

  def run(self):
    """ Run the command line task or tasks sequentially and keep track of failures, stops at the first failure"""
    for args in self.margs:
      out = subprocess.run(args, cwd=self.wd, shell=self.shell, check=False,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      self.output += out.stdout.decode()
      self.success = out.returncode == 0
      if not self.success:
        break
    return self


def _install_os_deps(env, progress, deps=_os_deps.keys()) -> List[Task]:
  def print_progress(tasks):
    progress(tasks)
    return tasks
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages. --allow-releaseinfo-change automatically allows the following change:
  # Repository 'http://raspbian.raspberrypi.org/raspbian buster InRelease' changed its 'Suite' value from 'stable' to 'oldstable'
  tasks += print_progress([Task('get latest debian packages', 'sudo apt-get update --allow-releaseinfo-change'.split()).run()])

  # Upgrade current packages
  print_progress([Task("upgrading debian packages, this will take 10+ minutes", success=True)])
  tasks += print_progress([Task('upgrade debian packages', 'sudo apt-get dist-upgrade --assume-yes'.split()).run()])

  # organize stuff to install
  packages = set()
  files = []
  scripts: Dict[str, List[str]] = {}
  for dep in deps:
    install_steps = _os_deps[dep]
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
    tasks += print_progress([Task(f"copy -f {_from} to {_to}", f"cp -f {_from} {_to}".split()).run()]) # shairport needs the -f if it is running
    if 'shairport-sync-metadata-reader' in _to:
      # windows messes up permissions
      tasks += print_progress([Task(f"make {_to} executable", f"chmod +x {_to}".split()).run()])
  if env['is_amplipi']:
    # copy alsa configuration file
    _from = f"{env['base_dir']}/config/asound.conf"
    _to = "/etc/asound.conf"
    tasks += print_progress([Task(f"copy {_from} to {_to}", f"sudo cp {_from} {_to}".split()).run()])
    # fix usb soundcard name
    usb_audio_rule_path = '/etc/udev/rules.d/85-amplipi-usb-audio.rules'
    if not os.path.exists(usb_audio_rule_path):
      _from = f"{env['base_dir']}/config/85-amplipi-usb-audio.rules"
      _to = usb_audio_rule_path
      tasks += print_progress([Task('fix usb soundcard id', multiargs=[
        f"sudo cp {_from} {_to}".split(),               # add new rule (udev watches this directory for changes)
        'sudo udevadm trigger -s sound -c add'.split(), # trigger an 'add' action on the 'sound' subsystem
        'udevadm settle'.split(),                       # wait for udev rules to fire and settle
      ]).run()])
    # set usb soundcard to 100% volume
    tasks += print_progress([Task('set usb soundcard to 100% volume', 'amixer -Dusb71 cset numid=8 100%'.split()).run()])
    # serial port permission granting
    tasks.append(Task('Check serial permissions', 'groups'.split()).run())
    tasks[-1].success = 'pi' in tasks[-1].output
    if not tasks[-1].success:
      tasks += print_progress([Task("Giving pi serial permission. !!!AmpliPi will need to be restarted after this!!!", "sudo gpasswd -a pi dialout".split()).run()])
      return tasks
    # setup tmpfs (ram disk)
    tasks += print_progress(_setup_tmpfs(env['base_dir']))
    # setup crontab - Replace the entire Pi user's crontab with AmpliPi's config/crontab
    # and point it to the AmpliPi install location's script directory.
    tasks += print_progress([Task("Setting up crontab", [f"cat {env['base_dir']}/config/crontab | sed 's@SCRIPTS_DIR@{env['base_dir']}/scripts@' | crontab -"], shell=True).run()])
  # install debian packages
  tasks += print_progress([Task('install debian packages', 'sudo apt-get install -y'.split() + list(packages)).run()])

  # Run scripts
  for dep, script in scripts.items():
    sh_loc = f'{env["base_dir"]}/install_{dep}.sh'
    with open(sh_loc, 'a') as sh:
      for scrap in script:
        sh.write(scrap + '\n')
    shargs = f'bash {sh_loc}'.split()
    clean = f'rm {sh_loc}'.split()
    tasks += print_progress([Task(f'run {dep} install script', args=shargs, wd=env['base_dir']).run()])
    tasks += print_progress([Task(f'remove {dep} temporary script', args=clean, wd=env['base_dir']).run()])

  # cleanup
  # shairport-sync install sets up a daemon we need to stop, remove it
  tasks += print_progress(_stop_service('shairport-sync', system=True))
  tasks += print_progress(_disable_service('shairport-sync', system=True))

  return tasks

def _install_python_deps(env: dict, deps: List[str]):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(env['script_dir'])
    tasks += [Task('install python packages', 'bash install_python_deps.bash'.split()).run()]
    os.chdir(last_dir)
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

def _setup_tmpfs(base_dir):
  """ Adds tmpfs entries used by AmpliPi to /etc/fstab """
  # Warning: these hide the existing filesystem,
  # if anything is already present at the path created.
  tmpfs_opts = 'defaults,noatime,uid=pi,gid=pi,size=100M'
  conf_entry = f'amplipi/config {base_dir}/config/srcs tmpfs {tmpfs_opts} 0 0'
  web_entry = f'amplipi/web {base_dir}/web/generated tmpfs {tmpfs_opts} 0 0'
  tasks = [Task('Add tmpfs entries to fstab.', multiargs=[
        'sudo sed -i "/^amplipi/d" /etc/fstab',
        f'echo {conf_entry} | sudo tee -a /etc/fstab',
        f'echo {web_entry} | sudo tee -a /etc/fstab',
        f'mkdir -p {base_dir}/config/srcs {base_dir}/web/generated',
        f'sudo mount -a',
      ], shell=True).run()]
  return tasks

def _web_service(directory: str):
  return f"""\
[Unit]
Description=Amplipi Home Audio System
After=network.target

[Service]
Type=simple
WorkingDirectory={directory}
ExecStart=/usr/bin/authbind --deep {directory}/venv/bin/python -m uvicorn --host 0.0.0.0 --port 80 amplipi.asgi:application
Restart=always

[Install]
WantedBy=default.target
"""

def _update_service(directory: str, port: int=5001):
  return f"""\
[Unit]
Description=Amplipi Software Updater
After=network.target

[Service]
Type=simple
WorkingDirectory={directory}
ExecStart={directory}/venv/bin/python -m uvicorn amplipi.updater.asgi:app --host 0.0.0.0 --port {port}
Restart=on-abort

[Install]
WantedBy=default.target
"""

def _display_service(directory: str):
  return f"""\
[Unit]
Description=Amplipi Front Panel Display
After=network.target

[Service]
Type=simple
WorkingDirectory={directory}
ExecStart={directory}/venv/bin/python -m amplipi.display.display
Restart=on-abort

[Install]
WantedBy=default.target
"""

def _audiodetector_service(directory: str):
  return f"""\
[Unit]
Description=Amplipi RCA Input Audio Detector
After=network.target

[Service]
Type=simple
WorkingDirectory={directory}/config/srcs
ExecStart={directory}/amplipi/audiodetector/audiodetector
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""

def systemctl_cmd(system: bool) -> str:
  """ Get the relevant systemctl command based on @system {True: system, False: user} """
  if system:
    return 'sudo systemctl'
  # user
  return  'systemctl --user'

def _service_status(service: str, system: bool = False) -> Tuple[List[Task], bool]:
  # Status can be: active, reloading, inactive, failed, activating, or deactivating
  cmd = f'{systemctl_cmd(system)} is-active {service}'
  tasks = [Task(f'Check {service} status', cmd.split()).run()]
  # The exit code reflects the status of the service, not the command itself.
  # Just assume the command was run successfully.
  tasks[0].success = True
  active = 'active' in tasks[0].output and not 'inactive' in tasks[0].output
  return (tasks, active)

# Stop a systemd service. By default use the Session (user) session
def _stop_service(name: str, system: bool = False) -> List[Task]:
  service = f'{name}.service'
  tasks, running = _service_status(service, system)
  if running:
    cmd = f'{systemctl_cmd(system)} stop {service}'
    tasks.append(Task(f'Stop {service}', cmd.split()).run())
  return tasks

def _remove_service(name: str) -> List[Task]:
  filename = f'{name}.service'
  directory = pathlib.Path.home().joinpath('.config/systemd/user')
  tasks = [Task(f'Remove {filename}')]
  try:
    # Delete the service file
    pathlib.Path(directory).joinpath(filename).unlink()
    tasks[0].output = f'Removed {filename}'
    tasks[0].success = True
  except Exception as exc:
    tasks[0].output = str(exc)
    tasks[0].success = False
  return tasks

def _enable_service(name: str, system: bool = False) -> List[Task]:
  service = f'{name}.service'
  cmd = f'{systemctl_cmd(system)} enable {service}'
  tasks = [Task(f'Enable {service}', cmd.split()).run()]
  return tasks

def _disable_service(name: str, system: bool = False) -> List[Task]:
  service = f'{name}.service'
  cmd = f'{systemctl_cmd(system)} disable {service}'
  tasks = [Task(f'Disable {service}', cmd.split()).run()]
  return tasks

def _start_restart_service(name: str, restart: bool, test_url: Union[None, str] = None) -> List[Task]:
  service = f'{name}.service'
  if restart:
    tasks = [Task(f'Restart {service}', f'systemctl --user restart {service}'.split()).run()]
  else:
    # just start
    tasks = [Task(f'Start {service}', f'systemctl --user start {service}'.split()).run()]

  # wait a bit, so initial failures are detected before is-active is called
  if tasks[-1].success:
    # we need to check if the service is running
    for _ in range(25): # retry for 5 seconds, giving the service time to start
      task_check, running = _service_status(service)
      if running:
        break
      time.sleep(0.2)
    tasks += task_check
    if test_url and running:
      task = None
      for _ in range(40): # retry for 20 seconds, giving the server time to start
        task = _check_url(test_url)
        if task.success:
          break
        time.sleep(0.5)
      tasks.append(task)
      # we also need to enable the service so that it starts on startup
      tasks += _enable_service(name)
    elif name == 'amplipi':
      tasks[-1].output += "\ntry checking this service failure using 'scripts/run_debug_webserver' on the system"
      tasks.append(Task(f'Check {service} Status', f'systemctl --user status {service}'.split()).run())
    elif 'amplipi-updater' in name:
      tasks[-1].output += "\ntry debugging this service failure using 'scripts/run_debug_updater' on the system"
      tasks.append(Task(f'Check {service} Status', f'systemctl --user status {service}'.split()).run())
  return tasks

def _start_service(name: str, test_url: Union[None, str] = None) -> List[Task]:
  return _start_restart_service(name, restart=False, test_url=test_url)

def _restart_service(name: str, test_url: Union[None, str] = None) -> List[Task]:
  return _start_restart_service(name, restart=True, test_url=test_url)

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

def _create_service(name: str, config: str) -> List[Task]:
  filename = f'{name}.service'
  directory = pathlib.Path.home().joinpath('.config/systemd/user')
  tasks = []

  # create the systemd directory if it doesn't already exist
  tasks += _create_dir(str(directory))

  # create the service file, overwriting any existing one
  tasks.append(Task(f'Create {filename}'))
  try:
    with directory.joinpath(filename).open('w+') as svc_file:
      svc_file.write(config)
    tasks[-1].success = True
    tasks[-1].output = f'Created {filename}'
  except:
    tasks[-1].output = f'Failed to create {filename}'

  # recreate systemd's dependency tree
  tasks.append(Task('Reload systemd config', 'systemctl --user daemon-reload'.split()).run())
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
    tasks.append(Task('Setup autobind', f'sudo chmod 777 {PORT_FILE}'.split()).run())
  return tasks

# Enable linger so that user manager is started at boot
def _enable_linger(user: str) -> List[Task]:
  return [Task(f'Enable linger for {user} user', f'sudo loginctl enable-linger {user}'.split()).run()]

def _copy_old_config(dest_dir: str) -> None:
  # try to copy the config of the current running amplipi service into base_dir/house.json
  # success is not required since the config will be generated from defaults if missing
  old_dir = subprocess.getoutput('systemctl --user show amplipi | grep WorkingDirectory= | sed s/WorkingDirectory=//')
  if old_dir:
    try:
      subprocess.run(['cp', f'{old_dir}/house.json', f'{dest_dir}/house.json'], check=False)
    except:
      pass

def _check_url(url) -> Task:
  task = Task(f'Check url {url}')
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
  # try to copy the old config into the potentially new directory
  # This fixes some potential update issues caused by migrating install to a different directory
  # (using the web updated the install dir used to be amplipi-dev2 and is now amplipi-dev)
  _copy_old_config(env['base_dir'])
  tasks = []
  # stop amplipi before reconfiguring authbind
  tasks += print_progress(_stop_service('amplipi'))
  # bringup amplipi and updater separately
  tasks += print_progress(_configure_authbind())
  tasks += print_progress(_create_service('amplipi', _web_service(env['base_dir'])))
  tasks += print_progress(_start_service('amplipi', test_url='http://0.0.0.0'))
  if not tasks[-1].success:
    return tasks
  tasks += print_progress([_check_version('http://0.0.0.0/api')])
  tasks += print_progress(_create_service('amplipi-updater', _update_service(env['base_dir'])))
  if restart_updater:
    tasks += print_progress(_stop_service('amplipi-updater'))
    tasks += print_progress(_start_service('amplipi-updater', test_url='http://0.0.0.0:5001/update'))
  else:
    # start a second updater service and check if it serves a url
    # this allow us to verify the update the updater probably works
    tasks += print_progress(_create_service('amplipi-updater-test', _update_service(env['base_dir'], port=5002)))
    tasks += print_progress(_start_service('amplipi-updater-test', test_url='http://0.0.0.0:5002/update'))
    # stop and disable the service so it doesn't start up on a reboot
    tasks += print_progress(_stop_service('amplipi-updater-test'))
    tasks += print_progress(_remove_service('amplipi-updater-test'))
  if env['is_amplipi']:
    # start the user manager at boot, instead of after first login
    # this is needed so the user systemd services start at boot
    tasks += print_progress(_enable_linger(env['user']))
  return tasks

def _update_display(env: dict, progress) -> List[Task]:
  def print_progress(tasks):
    progress(tasks)
    return tasks
  tasks = []
  tasks += print_progress(_create_service('amplipi-display', _display_service(env['base_dir'])))
  tasks += print_progress(_restart_service('amplipi-display'))
  tasks += print_progress(_enable_service('amplipi-display'))
  if env['is_amplipi']:
    # start the user manager at boot, instead of after first login
    # this is needed so the user systemd services start at boot
    tasks += print_progress(_enable_linger(env['user']))
  return tasks

def _update_audiodetector(env: dict, progress) -> List[Task]:
  """ Create and run the RCA input audio detector service if on AmpliPi hardware """
  def print_progress(tasks):
    progress(tasks)
    return tasks
  if not env['is_amplipi']:
    return [Task(name='Update Audio Detector', output = 'Not on AmpliPi', success=False)]
  tasks = []
  tasks += print_progress([Task('Build audiodetector', f'make -C {env["base_dir"]}/amplipi/audiodetector'.split()).run()])
  tasks += print_progress(_create_service('amplipi-audiodetector', _audiodetector_service(env['base_dir'])))
  tasks += print_progress(_restart_service('amplipi-audiodetector'))
  tasks += print_progress(_enable_service('amplipi-audiodetector'))
  # start the user manager at boot, instead of after first login
  # this is needed so the user systemd services start at boot
  tasks += print_progress(_enable_linger(env['user']))
  return tasks

def _check_password(env: dict, progress) -> List[Task]:
  """ If a random default password hasn't been generated, generate, set, and
      store one. This is just for older AmpliPi versions that didn't get a
      random password set at checkout.
  """
  task = Task('Set a default password')
  task.success = True
  pass_dir = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')
  pass_file = os.path.join(pass_dir, 'default_password.txt')
  if env['user'] != 'pi':
    task.output = 'Not setting a default password: not running as pi user'
  elif not env['is_amplipi']:
    task.output = 'Not setting a default password: not running on AmpliPi'
  elif os.path.exists(pass_file):
    task.output = 'Default password already generated'
  elif not os.path.exists('/run/sshwarn'):
    # no default pass file, but password is not 'raspberry' so already user-set
    task.margs = [f'mkdir -p {pass_dir}'.split(), f'touch {pass_file}'.split()]
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
  """ If on AmpliPi hardware, update to the latest firmware """
  task = Task('Flash latest firmware')
  latest_ver = 0
  latest_file = ''
  for f in glob.glob(f"{env['base_dir']}/fw/bin/*.bin"):
    ver = _fw_ver_from_filename(f)
    if ver > latest_ver:
      latest_ver = ver
      latest_file = f
  if latest_ver > 0:
    if env['is_amplipi']:
      os.chdir(env['base_dir'])
      task.margs = [f'bash scripts/program_firmware {latest_file}'.split()]
      task.run()
    else:
      task.output = 'Not on AmpliPi'
      task.success = False
  else:
    task.output = f"Couldn't find any firmware in {env['base_dir']}/fw/bin"
    task.success = False
  progress([task])
  return [task]


def print_task_results(tasks : List[Task]) -> None:
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
    ('Program Main', './hw/tests/program_preamps.bash'),
    ('Program Main + Exp Preamp', './hw/tests/program_preamps.bash 2'),
    ('Program Main + 2 Exp Preamps', './hw/tests/program_preamps.bash 3'),
    ('Amplifier', './hw/tests/built_in.bash amp'),
    ('LEDs', './hw/tests/built_in.bash led'),
    ('Preamp', './hw/tests/built_in.bash preamp'),
    ('Expander Preamp', './hw/tests/built_in.bash preamp --expansion'),
    ('Inputs', './hw/tests/built_in.bash inputs'),
    ('Preouts', './hw/tests/built_in.bash preout'),
    ('Display', './hw/tests/display.bash --wait'),
    ('Ethernet', './hw/tests/ethernet.bash --wait'),
    ('USB Ports', './hw/tests/usb.py'),
    ('Peak Detect', 'venv/bin/python ./hw/tests/peak_detect.py'),
    ('Fans and Power', './hw/tests/fans.bash'),
    ('Preamp Status', 'venv/bin/python ./hw/tests/preamp.py -w'), # just for info, not a specific test
  ]
  tasks = []

  # create the ~/tests directory if it doesn't already exist
  directory = pathlib.Path.home().joinpath('Desktop', 'tests')
  tasks += _create_dir(str(directory))

  for test in tests:
    tasks += [_add_desktop_icon(env, directory, test[0], test[1])]
  progress(tasks)
  return tasks

def install(os_deps=True, python_deps=True, web=True, restart_updater=False,
            display=True, audiodetector=True, firmware=True, password=True,
            progress=print_task_results) -> bool:
  """ Install and configure AmpliPi's dependencies """
  # pylint: disable=too-many-return-statements
  tasks = [Task('setup')]
  def failed():
    for task in tasks:
      if not task.success:
        return True
    return False

  env = _check_and_setup_platform()
  if not env['platform_supported']:
    tasks[0].output = f'untested platform: {platform.platform()}. Please fix this this script and make a PR to github.com/micro-nova/AmpliPi'
  else:
    tasks[0].output = str(env)
    tasks[0].success = True
  progress(tasks)
  if failed():
    return False
  tasks += fix_file_props(env, progress)
  if env['is_amplipi']:
    tasks += add_tests(env, progress)
  if failed():
    return False
  if os_deps:
    tasks += _install_os_deps(env, progress, _os_deps)
    if failed():
      print('OS dependency install step failed, exiting...')
      return False
  if python_deps:
    with open(os.path.join(env['base_dir'], 'requirements.txt')) as req:
      deps = req.read().splitlines()
      # TODO: embed python progress reporting
      py_tasks = _install_python_deps(env, deps)
      progress(py_tasks)
      tasks += py_tasks
    if failed():
      print('Python dependency install step failed, exiting...')
      return False
  if web:
    tasks += _update_web(env, restart_updater, progress)
    if failed():
      return False
  if display:
    tasks += _update_display(env, progress)
    if failed():
      return False
  if audiodetector:
    tasks += _update_audiodetector(env, progress)
    if failed():
      return False
  if firmware:
    tasks += _update_firmware(env, progress)
    if failed():
      return False
  if password:
    tasks += _check_password(env, progress)
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
  parser.add_argument('--web','--webserver', action='store_true', default=False,
    help="Install and configure webserver")
  parser.add_argument('--restart-updater', '--reboot', action='store_true', default=False,
    help="""Restart AmpliPis OS, rebooting all of Ampli's services \
      Only do this if you are running this from the command line. \
      When this is set False system will need to be restarted to complete an update""")
  # --restart-updater is needed by the web updater and hasn't been changed to --reboot to simplify updgrade/downgrade logic
  parser.add_argument('--display', action='store_true', default=False,
    help="Install and run the front-panel display service")
  parser.add_argument('--audiodetector', action='store_true', default=False,
    help="Install and run the RCA input audio detector service")
  parser.add_argument('--firmware', action='store_true', default=False,
    help="Flash the latest firmware")
  parser.add_argument('--password', action='store_true', default=False,
    help="Generate and set a new default password for the pi user.")
  flags = parser.parse_args()
  print('Configuring AmpliPi installation')
  has_args = flags.python_deps or flags.os_deps or flags.web or flags.restart_updater or flags.display or flags.firmware
  if not has_args:
    print('  WARNING: expected some arguments, check --help for more information')
  if sys.version_info.major < 3 or sys.version_info.minor < 7:
    print('  WARNING: minimum python version is 3.7')
  install(os_deps=flags.os_deps, python_deps=flags.python_deps, web=flags.web,
          display=flags.display, audiodetector=flags.audiodetector,
          firmware=flags.firmware, password=flags.password,
          restart_updater=flags.restart_updater)
