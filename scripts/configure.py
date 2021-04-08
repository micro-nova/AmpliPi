#!/usr/bin/python3

""" Update Amplipi's configuration on the raspberry pi or your test setup

This script is initially designed to support local git installs, pi installs, and amplipi installs
"""
import platform
import subprocess
import os
import pwd # username
import glob
import requests
import traceback
import tempfile

_os_deps = {
  'base' : {
    'apt' : ['python3-pip', 'python3-venv', 'curl', 'authbind']
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
  script_dir = os.path.dirname(os.path.realpath(__file__))
  env = {
    'user': pwd.getpwuid(os.getuid()).pw_name,
    'has_apt': False,
    'is_git_repo': False,
    'platform_supported': False,
    'script_dir': script_dir,
    'base_dir': script_dir.rsplit('/', 1)[0],
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


def _install_os_deps(env, progress, deps=_os_deps.keys()):
  def p2(tasks):
    progress(tasks)
    return tasks
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages
  tasks += p2([Task('get latest debian packages', 'sudo apt update'.split()).run()])

  # install debian packages
  packages = set()
  for d in deps:
    if 'apt' in _os_deps[d]:
      packages.update(_os_deps[d]['apt'])
  tasks += p2([Task('install debian packages', 'sudo apt install -y'.split() + list(packages)).run()])

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
    tasks += p2([Task('install local debian packages', 'sudo apt install -y'.split() + list(packages)).run()])
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

def _web_service(user, dir):
  return f"""
  [Unit]
  Description=Amplipi Home Audio System
  After=syslog.target network.target

  [Service]
  Type=simple
  User={user}
  Group={user}
  WorkingDirectory={dir}
  ExecStart=authbind --deep {dir}/venv/bin/python -m uvicorn --host 0.0.0.0 --port 80 --interface wsgi amplipi.wsgi:application
  Restart=on-abort

  [Install]
  WantedBy=multi-user.target(venv)
  """

def _update_service(user, dir):
  return f"""
  [Unit]
  Description=Amplipi Software Updater
  After=syslog.target network.target

  [Service]
  Type=simple
  User={user}
  Group={user}
  WorkingDirectory={dir}
  ExecStart={dir}/venv/bin/python -m uvicorn amplipi.updater.asgi:app --host 0.0.0.0 --port 5001
  Restart=on-abort

  [Install]
  WantedBy=multi-user.target
  """

def _create_and_start_service(name, config):
  service = f'{name}.service'
  c = Task('Create {service}')
  # create the service file
  try:
    with tempfile.NamedTemporaryFile('w', delete=False) as f:
      f.write(config)
      file = f.name
  except IOError as e:
    c.output = ''.join(traceback.format_exception())
    c.success = False
  # copy the service file to the systemd service directory
  c.margs = [f'sudo mv {file} /lib/systemd/system/{service}'.split()]
  c.run()
  if not c.success:
    return [c]
  # start the service
  s = Task(f'Start {service}', multiargs=[
    'sudo systemctl daemon-reload'.split(),
    'sleep 1'.split(),
    f'sudo systemctl restart {name}'.split(),
  ])
  s.run()
  if s.success:
    # we need to check if the service is running
    try:
      # TODO: do we need to sleep for a sec?
      out = subprocess.check_output('sudo systemctl is-active amplipi'.split(), text=True)
      s.success = 'active' in out
    except subprocess.CalledProcessError:
      s.output += 'ERROR: '
      s.output += ''.join(traceback.format_exception())
      s.success = False
  return [c, s]

def _configure_authbind():
  """ Configure access to port 80 so we can run amplipi as a non-root user """
  """ Execute the following commands
  sudo touch /etc/authbind/byport/80
  sudo chmod 777 /etc/authbind/byport/80
  """
  t = Task('Setup autobind', multiargs=[
    'sudo touch /etc/authbind/byport/80'.split(),
    'sudo chmod 777 /etc/authbind/byport/80'.split()
  ])
  t.run()
  return [t]

def check_url(url):
  t = Task('Check url')
  t.output = f'\ntesting: {url}'
  r = requests.get(url)
  if r.ok:
    t.output += "\n  Ok!"
  else:
    t.output += f"\n  Error: {r.reason}"
    t.success = False
  return [t]

def _update_web(env, progress):
  def p2(tasks):
    progress(tasks)
    return tasks
  tasks = []
  # bringup amplipi and updater separately
  tasks += p2(_configure_authbind())
  tasks += p2(_create_and_start_service('amplipi', _web_service(env['user'], env['base_dir'])))
  # NOTE: if debugging updater comment out the following lines and run the with scripts/run_debug_updater
  if tasks[-1].success:
    tasks += p2(_create_and_start_service('amplipi-updater', _update_service(env['user'], env['base_dir'])))
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
  else:
    t.output = str(env)
    t.success = True
  progress([t])
  if not t.success:
    return False
  if os_deps:
    _install_os_deps(env, progress, _os_deps)
  if python_deps:
    with open(os.path.join(env['script_dir'], '..', 'requirements.txt')) as f:
      deps = f.read().splitlines()
      # TODO: embed python progress reporting
      progress(_install_python_deps(env, deps))
  if web:
    _update_web(env, progress)
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
  args = parser.parse_args()
  install(os_deps=args.os_deps, python_deps=args.python_deps, web=args.web)
