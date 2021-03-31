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

def _run_task(name, args):
  task = dict() # TODO: migrate this task report to an actual class
  task['name'] = name
  task['args'] = args
  out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
  task['output'] = out.stdout.decode()
  task['status'] = 'success' if out.returncode == 0 else 'failed' # TODO: apt update returns 100 on my machine :/
  return task

def _install_os_deps(env, deps=_os_deps.keys()):
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages
  tasks += [_run_task('get latest debian packages', 'sudo apt update'.split())]

  # install debian packages
  packages = set()
  for d in deps:
    if 'apt' in _os_deps[d]:
      packages.update(_os_deps[d]['apt'])
  tasks += [_run_task('install debian packages', 'sudo apt install -y'.split() + list(packages))]

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
    tasks += [_run_task('install local debian packages', 'sudo apt install -y'.split() + list(packages))]
  os.chdir(last_dir)
  return tasks

def _install_python_deps(env, deps):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(env['script_dir'])
    tasks += [_run_task('install python packages', 'sh install_python_deps.bash'.split())]
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
        "working_directory": base_dir
      },
      "amplipi_updater": {
        # TODO: use amplipi_updater user?
        "user": "pi",
        "group": "pi",
          "type": "python 3.7",
          "path": base_dir,
          "home": f'{base_dir}/venv/', # TODO: should the updater have a seperate venv?
          "module": "amplipi.updater.wsgi",
        "working_directory": base_dir
      }
    }
  }
  if not amplipi_up:
    del config['listeners']['*:80']
    del config['applications']['amplipi']
  if not updater_up:
    del config['listeners']['*:5001']
    del config['applications']['updater']
  return config

CONFIG_URL = 'http://localhost/config'

def _get_web_config():
  """ Grab the current Nginx Unit server configuration
    NOTE: this theoretically can be done in python but this and only this needs to run as sudo
    import requests_unixsocket
    session = requests_unixsocket.Session()
    session.get('http+unix://%2Fvar%2Frun%2Fcontrol.unit.sock/config')
  """
  t = _run_task('Get web config', 'sudo curl -s --unix-socket /var/run/control.unit.sock http://localhost/config'.split())
  return t

def _put_web_config(cfg):
  """ Configure Nginx Unit Server """
  cmds = 'sudo curl -s -X PUT -d DATA --unix-socket /var/run/control.unit.sock http://localhost/config'.split()
  assert cmds[6] == 'DATA'
  cmds[6] = '{}'.format(json.dumps(cfg))
  t = _run_task('Put web config', cmds)
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
  js = json.loads(t['output'])
  if 'success' in js:
    t['status'] = "success"
    t['output'] = js['success']
  elif 'error' in js:
    t['status'] = "error"
    t['output'] = js['error']
  else:
    t['status'] = "error"
  if 'detail' in js:
    t['output'] += '\n{}'.format(js['detail'])
  return t

def _is_web_running():
  return _get_web_config()['status'] == 'success'

def _restart_web():
  print('restarting webserver')
  subprocess.check_call('sudo systemctl restart unit.service'.split())

def update_web(env):
  if not _is_web_running():
    _restart_web()
  base_dir = env['script_dir'].rstrip('/scripts')
  # TODO: bringup amplipi and updater separately (checking if they are working before starting the next)
  t = _put_web_config(_create_web_config(base_dir))
  if t['status'] != 'success':
    print('Error updating web configuration: {}'.format(t['status']))
  return [t]

def print_task_results(tasks):
  for task in tasks:
    print(f"{task['name']} : {task['args']}")
    for line in task['output'].splitlines():
      print(f'  {line}')
    if 'success' != task['status']:
      status = task['status']
      print(f'  ERROR: {status}')

def install(os_deps=True, python_deps=True, web=True, progress=print_task_results):
  """ Install and configure AmpliPi's dependencies """
  t = {'name': 'setup', 'args': [], 'output': '', 'status' : 'success'}
  env = _check_and_setup_platorm()
  if not env['platform_supported']:
    t['output'] = f'untested platform: {platform.platform()}. Please fix this this script and make us a PR'
    t['status'] = 'error'
    exit(1)
  if web and not env['nginx_supported']:
    t['output'] = 'nginx unit webserver is not supported on this platform yet'
    t['status'] = 'error'
    exit(1)
  t['output'] = str(env)
  progress([t])
  if os_deps:
    if web and env['nginx_supported']:
      # add unit web server
      _os_deps['web']['debs'] = ['unit', 'unit-python3.7']
    progress(_install_os_deps(env, _os_deps))
  if python_deps:
    with open(os.path.join(env['script_dir'], '../requirements.txt')) as f:
      deps = f.read().splitlines()
      progress(_install_python_deps(env, deps))
  if web:
    progress(update_web(env))

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
