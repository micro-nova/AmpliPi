#!/usr/bin/python3

""" Update Amplipi's configuration on the raspberry pi or your test setup

This script is initially designed to support local git installs, pi installs, and amplipi installs
"""
from os.path import split
import platform
import subprocess
import os
import pwd # username
import glob
import requests
import traceback
import tempfile
from typing import List, Union, Type
import time

_os_deps = {
  'base' : {
    'apt' : ['python3-pip', 'python3-venv', 'curl', 'authbind'],
    'copy' : [{'from': 'docs/amplipi_api.yaml', 'to': 'web/static/amplipi_api.yaml'}],
  },
  'web' : {
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
  # TODO: test spocon! it looks awesome
  # 'spotify' : {
  #   'script' :  [
  #     '$(curl -sL https://spocon.github.io/spocon/install.sh | sh)',
  #     'sudo systemctl stop spocon.service',
  #     'sudo systemctl disable spocon.service'
  #   ]
  # }
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

  """ Get the platform name
  - example pi output: Linux-5.4.51-v7+-armv7l-with-debian-10.4
  - example ubuntu output: Linux-5.4.0-66-generic-x86_64-with-Ubuntu-18.04-bionic
  """
  p = platform.platform().lower()

  # Figure out what platform we are on since we expect to be on a raspberry pi or a debian based development system
  if 'linux' in p:
    if 'x86_64' in p:
      apt = subprocess.run('which apt'.split())
      env['arch'] = 'x64'
      if apt:
        env['has_apt'] = True
        env['platform_supported'] = True
    elif 'armv7l' in p and 'debian' in p:
      env['arch'] = 'arm'
      env['platform_supported'] = True
      env['has_apt'] = True
      env['is_amplipi'] = 'amplipi' in platform.node() # checks hostname

  return env

class Task:
  """ Task runner for scripted installation tasks """
  def __init__(self, name: str, args=[], multiargs=None, output='', success=False):
    self.name = name
    if multiargs:
      assert len(args) == 0
      self.margs = multiargs
    else:
      self.margs = [args]
    self.output = output
    self.success = success

  def __str__(self):
    s = f"{self.name} : {self.margs}" if len(self.margs) > 0 else f"{self.name} :"
    for line in self.output.splitlines():
      if line and not "WARNING: apt does not have a stable CLI interface." in line: # ignore apt warnings so user doesnt get confused
        s += f'\n  {line}'
    if not self.success:
       s += f'\n  Error: Task Failed'
    return s

  def run(self):
    for args in self.margs:
      out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
      self.output += out.stdout.decode()
      self.success = out.returncode == 0
      if not self.success:
        break
    return self


def _install_os_deps(env, progress, deps=_os_deps.keys()) -> List[Task]:
  def p2(tasks):
    progress(tasks)
    return tasks
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages
  tasks += p2([Task('get latest debian packages', 'sudo apt update'.split()).run()])

  # organize stuff to install
  packages = set()
  files = []
  for d in deps:
    if 'copy' in _os_deps[d]:
      files += _os_deps[d]['copy']
    if 'apt' in _os_deps[d]:
      packages.update(_os_deps[d]['apt'])

  # copy files
  for file in files:
    _from = file['from'].replace('ARCH', env['arch'])
    _to = file['to']
    # prepend home to relative paths
    if _from[0] != '/':
      _from = f"{env['base_dir']}/{_from}"
    if _to[0] != '/':
      _to = f"{env['base_dir']}/{_to}"
    tasks += p2([Task(f"copy {_from} to {_to}", f"cp {_from} {_to}".split()).run()])

  if env['is_amplipi']:
    # copy alsa configuration file
    _from = f"{env['base_dir']}/config/asound.conf"
    _to = f"/etc/asound.conf"
    tasks += p2([Task(f"copy {_from} to {_to}", f"sudo cp {_from} {_to}".split()).run()])
    # serial port permission granting
    tasks.append(Task(f'Check serial permissions', f'groups'.split()).run())
    tasks[-1].success = 'pi' in tasks[-1].output
    if not tasks[-1].success:
      tasks += p2([Task(f"Giving pi serial permission. !!!AmpliPi will need to be restarted after this!!!", "sudo gpasswd -a pi dialout".split()).run()])
      return tasks
  # install debian packages
  tasks += p2([Task('install debian packages', 'sudo apt install -y'.split() + list(packages)).run()])

  # cleanup
  # shairport-sync install sets up a deamon we need to stop, remove it
  tasks += p2(_stop_service('shairport-sync'))
  tasks += p2(_disable_service('shairport-sync'))

  return tasks

def _install_python_deps(env: dict, deps: List[str]):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(env['script_dir'])
    tasks += [Task('install python packages', 'sh install_python_deps.bash'.split()).run()]
    os.chdir(last_dir)
  return tasks

def _web_service(user: str, dir: str):
  return f"""
  [Unit]
  Description=Amplipi Home Audio System
  After=syslog.target network.target

  [Service]
  Type=simple
  User={user}
  Group={user}
  WorkingDirectory={dir}
  ExecStart=/usr/bin/authbind --deep {dir}/venv/bin/python -m uvicorn --host 0.0.0.0 --port 80 --interface wsgi amplipi.wsgi:application
  Restart=on-abort

  [Install]
  WantedBy=multi-user.target
  """

def _update_service(user: str, dir: str, port: int=5001):
  return f"""
  [Unit]
  Description=Amplipi Software Updater
  After=syslog.target network.target

  [Service]
  Type=simple
  User={user}
  Group={user}
  WorkingDirectory={dir}
  ExecStart={dir}/venv/bin/python -m uvicorn amplipi.updater.asgi:app --host 0.0.0.0 --port {port}
  Restart=on-abort

  [Install]
  WantedBy=multi-user.target
  """

def _stop_service(name: str) -> List[Task]:
  service = f'{name}.service'
  tasks = [Task(f'Check {service} status', f'systemctl is-active {service}'.split()).run()]
  tasks[0].success = True # when a task is failed the return code sets success=False
  if 'active' == tasks[0].output:
    tasks.append(Task(f'Stop {service}', f'sudo systemctl stop {service}'.split()).run())
  return tasks

def _remove_service(name: str) -> List[Task]:
  service = f'{name}.service'
  tasks = [Task(f'Remove {service}', f'sudo rm -f /lib/systemd/system/{service}'.split()).run()]
  return tasks

def _disable_service(name: str) -> List[Task]:
  service = f'{name}.service'
  tasks = [Task(f'Disable {service}', f'sudo systemctl disable {service}'.split()).run()]
  return tasks

def _start_service(name: str, test_url: Union[None, str] = None) -> List[Task]:
  service = f'{name}.service'
  tasks = []
  tasks.append(Task(f'Start {service}', multiargs=[
    f'sudo systemctl restart {name}'.split(),
    'sleep 2'.split(), # wait a bit, so initial failures are detected before is-active is called
  ]).run())
  if tasks[0].success:
    # we need to check if the service is running
    tasks.append(Task(f'Check {service} Status', f'systemctl is-active {service}'.split()).run())
    tasks[1].success = 'active' in tasks[1].output
    if test_url and tasks[1].success:
      time.sleep(1) # give the server time to start
      tasks.append(_check_url(test_url))
      # We also need to enable the service so that it starts on startup
      tasks.append(Task(f'Enable {service}', f'sudo systemctl enable {service}'.split()).run())
  return tasks

def _create_service(name: str, config: str) -> List[Task]:
  service = f'{name}.service'
  tasks = [Task(f'Create {service}')]
  # create the service file
  try:
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
      f.write(config)
      file = f.name
  except IOError as e:
    tasks[0].output = ''.join(traceback.format_exception())
    tasks[0].success = False
  # copy the service file to the systemd service directory
  tasks[0].margs = [f'sudo mv {file} /lib/systemd/system/{service}'.split()]
  tasks[0].run()
  if not tasks[0].success:
    return tasks
  tasks.append(Task(f'Load changes to {service}', multiargs=[
    'sudo systemctl daemon-reload'.split(),
    'sleep 0.5'.split(), # wait a bit so if start service is called after this it will be ready
  ]).run())
  return tasks

def _configure_authbind() -> List[Task]:
  """ Configure access to port 80 so we can run amplipi as a non-root user """
  """ Execute the following commands
  sudo touch /etc/authbind/byport/80
  sudo chmod 777 /etc/authbind/byport/80
  """
  PORT_FILE = '/etc/authbind/byport/80'
  tasks = []
  if not os.path.exists(PORT_FILE):
    tasks.append(Task('Setup autobind', multiargs=[
      f'sudo touch {PORT_FILE}'.split(),
      f'sudo chmod 777 {PORT_FILE}'.split()
    ]).run())
  elif os.stat(PORT_FILE).st_mode != 0o1000777:
    tasks.append(Task('Setup autobind', f'sudo chmod 777 {PORT_FILE}'.split()).run())
  return tasks

def _check_url(url) -> Task:
  t = Task('Check url')
  t.output = f'\ntesting: {url}'
  try:
    r = requests.get(url)
    if r.ok:
      t.output += "\nOk!"
      t.success = True
    else:
      t.output += f"\nError: {r.reason}"
  except:
    t.output = 'Failed to check url, this happens when the server is offline'
  return t

def _check_version(url) -> Task:
  t = Task('Checking version reported by API')
  t.output = f'\nusing: {url}'
  try:
    r = requests.get(url)
    if r.ok:
      reported_version = r.json()['version']
      t.success = True
      t.output += f'\nversion={reported_version}'
  except Exception:
    t.output = ''.join(traceback.format_exception())
  return t

def _update_web(env: dict, restart_updater: bool, progress) -> List[Task]:
  def p2(tasks):
    progress(tasks)
    return tasks
  tasks = []
  # stop amplipi before reconfiguring authbind
  tasks += p2(_stop_service('amplipi'))
  # bringup amplipi and updater separately
  tasks += p2(_configure_authbind())
  tasks += p2(_create_service('amplipi', _web_service(env['user'], env['base_dir'])))
  tasks += p2(_start_service('amplipi', test_url='http://0.0.0.0'))
  tasks += p2([_check_version('http://0.0.0.0/api')])
  tasks += p2(_create_service('amplipi-updater', _update_service(env['user'], env['base_dir'])))
  if restart_updater:
    tasks += p2(_start_service('amplipi-updater', test_url='http://0.0.0.0:5001/update'))
  else:
    # start a second updater service and check if it serves a url
    # this allow us to verify the update the updater probably works
    tasks += p2(_create_service('amplipi-updater-test', _update_service(env['user'], env['base_dir'], port=5002)))
    tasks += p2(_start_service('amplipi-updater-test', test_url='http://0.0.0.0:5002/update'))
    # stop and disable the service so it doesn't start up on a reboot
    tasks += p2(_stop_service('amplipi-updater-test'))
    tasks += p2(_remove_service('amplipi-updater-test'))
  return tasks

def print_task_results(tasks : List[Task]) -> None:
  for task in tasks:
    print(task)

def install(os_deps=True, python_deps=True, web=True, restart_updater=False, progress=print_task_results) -> bool:
  """ Install and configure AmpliPi's dependencies """
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
  if os_deps:
    tasks += _install_os_deps(env, progress, _os_deps)
    if failed():
      return False
  if python_deps:
    with open(os.path.join(env['base_dir'], 'requirements.txt')) as f:
      deps = f.read().splitlines()
      # TODO: embed python progress reporting
      py_tasks = _install_python_deps(env, deps)
      progress(py_tasks)
      tasks += py_tasks
    if failed():
      return False
  if web:
    tasks += _update_web(env, restart_updater, progress)
    if failed():
      return False
  if not web and restart_updater: # if web and restart_updater are True this restart happens in the _update_web function
    # The update server needs to restart itself after everything else is successful
    ssts =_start_service('amplipi-updater', test_url='http://0.0.0.0:5001/update')
    progress(ssts)
    tasks += ssts
    if failed():
      return False
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
  parser.add_argument('--restart-updater', action='store_true', default=False,
    help="""Restart the updater. Only do this if you are running this from the command line. When this is set False system will need to be restarted to complete update""")
  args = parser.parse_args()
  install(os_deps=args.os_deps, python_deps=args.python_deps, web=args.web, restart_updater=args.restart_updater)
