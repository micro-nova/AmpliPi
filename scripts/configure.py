#!/usr/bin/python3

""" Update Amplipi's configuration on the raspberry pi or your test setup

This script is initially designed to support local git installs, pi installs, and amplipi installs
"""
import platform
import subprocess
import os
import glob
import sys
import json

_os_deps = {
  'base' : {
    'apt' : ['python3-pip', 'python3-venv', 'curl']
  },
  'web' : {
  },
  # streams
  # TODO: can stream dependencies be aggregated from the streams themselves?
  'pandora' : {
    'apt' : [ 'pianobar']
  },
  'airplay' : {
    'apt' : [ 'shairport-sync' ]
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

def _check_and_setup_platorm():
  env = {
    'has_apt': False,
    'is_git_repo': False,
    'nginx_supported': False,
    'platform_supported': False,
    'script_dir': os.path.dirname(os.path.realpath(__file__)),
    'is_amplipi': False,
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
      if apt:
        env['has_apt'] = True
        env['platform_supported'] = True
    elif 'armv7l' in p and 'debian' in p:
      env['nginx_supported'] = True
      env['platform_supported'] = True
      env['has_apt'] = True
      env['is_amplipi'] = 'amplipi' in platform.node() # checks hostname

  return env

class Task:
  """ Task runner for scripted installation tasks """
  def __init__(self, name: str, args=[], output='', success=False, json_out=False):
    self.name = name
    self.args = args
    self.output = output
    self.success = success
    self.json_out = json_out

  def __str__(self):
    s = f"{self.name} : {self.args}"
    for line in self.output.splitlines():
      s += f'\n  {line}'
    if not self.success:
       s += f'\n  Error: Task Failed'
    return s

  def run(self):
    out = subprocess.run(self.args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    self.output = out.stdout.decode()
    if self.json_out:
      # unit returns status as json, rewrite this in an expected format
      """ example Unit outputs
      Example success: {
        "success": "Reconfiguration done."
      }
      Example failure: {
        "error": "Invalid JSON.",
        "detail": "An empty JSON payload isn't allowed."
      }
      """
      js = json.loads(self.output)
      if 'success' in js:
        self.success = True
        self.output = js['success']
      elif 'error' in js:
        self.success = False
        self.output = js['error']
      else:
        self.success = False
      if 'detail' in js:
        self.output += '\n{}'.format(js['detail'])
    else:
      self.success = out.returncode == 0
    return self

def _install_os_deps(env, deps=_os_deps.keys()):
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages
  tasks += [Task('get latest debian packages', 'sudo apt update'.split()).run()]

  # install debian packages
  packages = set()
  for d in deps:
    if 'apt' in _os_deps[d]:
      packages.update(_os_deps[d]['apt'])
  tasks += [Task('install debian packages', 'sudo apt install -y'.split() + list(packages)).run()]

  # install local debian packages
  packages = set()
  # set the local directory so glob knows where to look
  last_dir = os.path.abspath(os.curdir)
  os.chdir(env['script_dir'] + '/..')
  for d in deps:
    if 'debs' in _os_deps[d]:
      for db in _os_deps[d]['debs']:
        # get the full name of the debian file
        packages.update(glob.glob(f'{db}_*.deb'))
  if len(packages) > 0:
    tasks += [Task('install local debian packages', 'sudo apt install -y'.split() + list(packages)).run()]
  os.chdir(last_dir)
  return tasks

def _install_python_deps(env, deps):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(env['script_dir'])
    tasks += [Task('install python packages', 'sh install_python_deps.bash'.split()).run()]
    os.chdir(last_dir)
  return tasks

def _create_web_config(base_dir, amplipi_up = True, updater_up = True):
  base_dir = base_dir.rstrip('/') # remove trailing slash if any
  config = {
    "listeners": {
      "*:80": {
        "pass": "applications/amplipi"
      },
      "*:5001": {
        "pass": "applications/amplipi_updater"
      }
    },
    "applications": {
      "amplipi": {
        # TODO: use amplpi user?
        "user": "pi",
        "group": "pi",
        "type": "python 3.7",
        "path": base_dir,
        "home": f'{base_dir}/venv/',
        "module": "amplipi.wsgi",
        "working_directory": base_dir,
      },
      "amplipi_updater": {
        # TODO: use amplipi_updater user?
        "user": "pi",
        "group": "pi",
        "type": "python 3.7",
        "path": base_dir,
        "home": f'{base_dir}/venv/', # TODO: should the updater have a seperate venv?
        "module": "amplipi.updater.asgi",
        "working_directory": base_dir,
      }
    }
  }
  if not amplipi_up:
    del config['listeners']['*:80']
    del config['applications']['amplipi']
  if not updater_up:
    del config['listeners']['*:5001']
    del config['applications']['amplipi_updater']
  return config

CONFIG_URL = 'http://localhost/config'

def _get_web_config() -> Task:
  """ Grab the current Nginx Unit server configuration
    NOTE: this theoretically can be done in python but this and only this needs to run as sudo
    import requests_unixsocket
    session = requests_unixsocket.Session()
    session.get('http+unix://%2Fvar%2Frun%2Fcontrol.unit.sock/config')
  """
  t = Task('Get web config', 'sudo curl -s --unix-socket /var/run/control.unit.sock http://localhost/config'.split()).run()
  return t

def _put_web_config(cfg, test_url='') -> Task:
  """ Configure Nginx Unit Server """
  import requests
  cmds = 'sudo curl -s -X PUT -d DATA --unix-socket /var/run/control.unit.sock http://localhost/config'.split()
  assert cmds[6] == 'DATA'
  cmds[6] = '{}'.format(json.dumps(cfg))
  t = Task('Put web config', cmds, json_out=True).run()
  if t.success and test_url:
    t.output += f'\ntesting: {test_url}'
    r = requests.get(test_url)
    if r.ok:
      t.output += "\n  Ok!"
    else:
      t.output += f"\n  Error: {r.reason}"
      t.success = False
  return t

def _is_web_running() -> bool:
  return _get_web_config().success

def _restart_web():
  return Task('restart webserver', 'sudo systemctl restart unit.service'.split()).run()

def _update_web(env):
  tasks = []
  if not _is_web_running():
    tasks.append(_restart_web())
  base_dir = env['script_dir'].rstrip('/scripts')
  # bringup amplipi and updater separately
  only_amplipi = _create_web_config(base_dir, amplipi_up=True, updater_up=False)
  amplipi_and_updater = _create_web_config(base_dir, amplipi_up=True, updater_up=True)
  tasks.append(_put_web_config(only_amplipi, 'http://localhost'))
  # NOTE: if debugging updater comment out the following lines and run the with scripts/run_debug_updater
  if tasks[-1].success:
    tasks.append(_put_web_config(amplipi_and_updater, 'http://localhost:5001/update'))
  return tasks

def print_task_results(tasks):
  for task in tasks:
    print(task)

def install(os_deps=True, python_deps=True, web=True, progress=print_task_results):
  """ Install and configure AmpliPi's dependencies """
  t = Task('setup')
  env = _check_and_setup_platorm()
  if not env['platform_supported']:
    t.output = f'untested platform: {platform.platform()}. Please fix this this script and make us a PR'
  elif web and not env['nginx_supported']:
    t.output = 'nginx unit webserver is not supported on this platform yet'
  else:
    t.output = str(env)
    t.success = True
  progress([t])
  if not t.success:
    return False
  if os_deps:
    if web and env['nginx_supported']:
      # add unit web server
      _os_deps['web']['debs'] = ['unit', 'unit-python3.7']
    progress(_install_os_deps(env, _os_deps))
  if python_deps:
    with open(os.path.join(env['script_dir'], '..', 'requirements.txt')) as f:
      deps = f.read().splitlines()
      progress(_install_python_deps(env, deps))
  if web:
    progress(_update_web(env))
  return True

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Configure AmpliPi installation')
  parser.add_argument('--python-deps', action='store_true', default=False,
    help='Install python dependencies (using venv)')
  parser.add_argument('--os-deps', action='store_true', default=False,
    help='Install os dependencies using apt')
  parser.add_argument('--web','--webserver', action='store_true', default=False,
    help="Install and configure webserver (Nginx Unit)")
  args = parser.parse_args()
  install(os_deps=args.os_deps, python_deps=args.python_deps, web=args.web)
