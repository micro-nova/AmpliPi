#!/usr/bin/python3

# Update Amplipi's configuration on the raspberry pi (or your test setup)
import platform
import subprocess
import os
import glob
import sys

os_deps = {
  'base' : {
    'apt' : ['python3-pip', 'python3-venv']
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

def check_and_setup_platorm():
  global test_env, script_dir
  p = platform.platform().lower()

  # Figure out what platform we are on since we expect to be on a raspberry pi or a debian based development system
  test_env = False
  supported = False
  if 'linux' in p:
    if 'x86_64' in p:
      apt = subprocess.run('which apt'.split())
      # example ubuntu output: Linux-5.4.0-66-generic-x86_64-with-Ubuntu-18.04-bionic
      if apt:
        supported = True
        test_env = True
    elif 'armv7l' in p and 'debian' in p:
      # example pi output: Linux-5.4.51-v7+-armv7l-with-debian-10.4
      supported = True
      # add unit web server
      os_deps['web']['debs'] = ['unit', 'unit-python3.7']
      # TODO: check if this is an amplipi unit
  if not supported:
    print(f'untested platform: {p}. Please fix this this script and make us a PR')
    exit(1)

  script_dir = os.path.dirname(os.path.realpath(__file__))

def run_task(name, args):
  task = dict()
  task['name'] = name
  task['args'] = args
  out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
  task['output'] = out.stdout.decode()
  task['status'] = 'success' if out.returncode == 0 else 'failed' # TODO: apt update returns 100 on my machine :/
  return task

def install_os_deps(deps=os_deps.keys()):
  tasks = []
  # TODO: add extra apt repos
  # find latest apt packages
  tasks += [run_task('get latest debian packages', 'sudo apt update'.split())]

  # install debian packages
  packages = set()
  for d in deps:
    if 'apt' in os_deps[d]:
      packages.update(os_deps[d]['apt'])
  tasks += [run_task('install debian packages', 'sudo apt install -y'.split() + list(packages))]

  # install local debian packages
  packages = set()
  # set the local directory so glob knows where to look
  last_dir = os.path.abspath(os.curdir)
  os.chdir(script_dir+'/..')
  for d in deps:
    if 'debs' in os_deps[d]:
      for db in os_deps[d]['debs']:
        # get the full name of the debian file
        packages.update(glob.glob(f'{db}_*.deb'))
  tasks += [run_task('install local debian packages', 'sudo apt install -y'.split() + list(packages))]
  os.chdir(last_dir)
  return tasks

def install_python_deps(deps):
  tasks = []
  if len(deps) > 0:
    last_dir = os.path.abspath(os.curdir)
    os.chdir(script_dir)
    tasks += [run_task('install python packages', 'sh install_python_deps.bash'.split())]
    os.chdir(last_dir)
  return tasks

if __name__ == '__main__':
  check_and_setup_platorm()
  print(install_os_deps())
  with open(os.path.join(script_dir, '../requirements.txt')) as f:
    deps = f.read().splitlines()
    print(install_python_deps(deps))
