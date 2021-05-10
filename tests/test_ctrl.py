#!/usr/bin/python3
# this file is expected to be run using pytest, ie. pytest tests/test_ethaudio_mock.py

import argparse
from copy import deepcopy
import deepdiff

# use the internal amplipi library
from context import amplipi

# modify json config files
import json
import os
import tempfile

# several starting configurations to load for testing including a corrupted configuration
DEFAULT_STATUS = deepcopy(amplipi.ctrl.Api._DEFAULT_CONFIG)
# make a good config string, that has less groups than the default (so we can tell the difference)
GOOD_STATUS = deepcopy(DEFAULT_STATUS)
del GOOD_STATUS['groups'][2]
del GOOD_STATUS['groups'][1]
GOOD_CONFIG = json.dumps(GOOD_STATUS) # make it a json string we can write to a config file
# corrupt the json string by only taking the first half
# ( simulating what would happen if the program was terminated while writing the config file)
CORRUPTED_CONFIG = GOOD_CONFIG[0:len(GOOD_CONFIG)//2]
# an non-existant config file
NO_CONFIG = None
def delete_file(file_path):
  try:
    os.remove(file_path)
  except OSError:
    pass
  assert False == os.path.exists(file_path)

def write_file(file_path, content):
  with open(file_path, 'w') as cfg:
    cfg.write(content)
  assert os.path.exists(file_path)

# config file paths for testing
CONFIG_FILE = 'test_config.json'
CONFIG_FILE_BACKUP = CONFIG_FILE + '.bak'
def setup_test_configs(config=None, backup_config=None):
  """ Setup the api's configuration file and its backup,
        config/backup_config=None removes the config file
      Args:
        config: json string to write to config file or None
        backup_config: json string to write to backup config file or None
      Returns: None
  """
  # remove old config files
  delete_file(CONFIG_FILE)
  delete_file(CONFIG_FILE_BACKUP)
  # copy the config file and back to use (we don't want to modify them so they can be reused)
  # if a config is None the file is just deleted, simulating the first time the api is started
  if config:
    write_file(CONFIG_FILE, config)
  if backup_config:
    write_file(CONFIG_FILE_BACKUP, backup_config)

def api_w_mock_rt(config=None, backup_config=None):
  # copy in specfic config files (paths) to know config locations
  #   this sets the initial configuration
  #   (a None config file means that config file will be deleted before launch)
  setup_test_configs(config, backup_config)
  # start the api (we have a specfic config path we use for all tests)
  return amplipi.ctrl.Api(amplipi.rt.Mock(), config_file=CONFIG_FILE)

def api_w_rpi_rt(config=None, backup_config=None):
  # copy in specfic config files (paths) to know config locations
  #   this sets the initial configuration
  #   (a None config file means that config file will be deleted before launch)
  setup_test_configs(config, backup_config)
  # start the api (we have a specfic config path we use for all tests)
  return amplipi.ctrl.Api(amplipi.rt.Rpi(mock=True), config_file=CONFIG_FILE)

def use_tmpdir():
  # lets run these tests in a temporary directory so they dont mess with other tests config files
  test_dir = tempfile.mkdtemp()
  os.chdir(test_dir)
  assert test_dir == os.getcwd()

def prune_state(state: dict):
  """ Prune generated fields from system state to make comparable """
  for s in state['streams']:
    s.pop('info')
    s.pop('status')
  state.pop('version')
  return state

def test_config_loading():
  use_tmpdir() # run from temp dir so we don't mess with current directory
  # test loading an empty config (should load default config)
  api = api_w_mock_rt(NO_CONFIG, backup_config=NO_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())
  # test loading a known good config file by making a copy of it and loading the api with the copy
  api = api_w_mock_rt(GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())
  # test loading a corrupted config file with a good backup
  api = api_w_mock_rt(CORRUPTED_CONFIG, backup_config=GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())
  # test loading a missing config file with a good backup
  api = api_w_mock_rt(NO_CONFIG, backup_config=GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())
  # test loading a corrupted config file and a corrupted backup
  api = api_w_mock_rt(CORRUPTED_CONFIG, backup_config=CORRUPTED_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())
  # test loading a missing config file and a missing backup
  api = api_w_mock_rt(NO_CONFIG, backup_config=NO_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())

if __name__ == '__main__':
  # run tests without pytest
  test_config_loading()
