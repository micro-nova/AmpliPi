#!/usr/bin/python3

"""
Test amplipi.ctrl
this file is expected to be run using pytest, ie. pytest tests/test_ctrl.py
"""

import json
import os
import tempfile
from copy import deepcopy

# use the internal amplipi library
from context import amplipi

# several starting configurations to load for testing including a corrupted configuration
DEFAULT_STATUS = deepcopy(amplipi.ctrl.Api.DEFAULT_CONFIG) # pylint: disable=no-member
# make a good config string, that has more groups than the default (so we can tell the difference)
GOOD_STATUS = deepcopy(DEFAULT_STATUS)
# vol_delta need to be equal to the average volume of zones 0-5, here it is hardcoded
vol = 0
for zone in GOOD_STATUS['zones']:
  vol += zone['vol_f']
vol_f = vol / len( GOOD_STATUS['zones'])
GOOD_STATUS['groups'] = [{'id': 100, 'name': 'test group', 'mute': True, 'vol_f': vol_f, 'source_id': 0, 'zones': [0, 1, 2, 3, 4, 5]}]
GOOD_CONFIG = json.dumps(GOOD_STATUS) # make it a json string we can write to a config file
# corrupt the json string by only taking the first half
# ( simulating what would happen if the program was terminated while writing the config file)
CORRUPTED_CONFIG = GOOD_CONFIG[0:len(GOOD_CONFIG)//2]
# an non-existant config file
NO_CONFIG = None
def delete_file(file_path):
  """ Delete a config file """
  try:
    os.remove(file_path)
  except OSError:
    pass
  assert not os.path.exists(file_path)

def write_file(file_path, content):
  """ Write a new config File """
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
  """ Copy in specfic config files (paths) to know config locations
  this sets the initial configuration
  (a None config file means that config file will be deleted before launch)
  """
  setup_test_configs(config, backup_config)
  # start the api (we have a specfic config path we use for all tests)
  settings = amplipi.models.AppSettings()
  settings.config_file = CONFIG_FILE
  settings.mock_ctrl = True
  return amplipi.ctrl.Api(settings)

def api_w_rpi_rt(config=None, backup_config=None):
  """ Copy in specfic config files (paths) to know config locations
  this sets the initial configuration
  (a None config file means that config file will be deleted before launch)
  """
  setup_test_configs(config, backup_config)
  # start the api (we have a specfic config path we use for all tests)
  settings = amplipi.models.AppSettings()
  settings.config_file = CONFIG_FILE
  settings.mock_ctrl = False
  return amplipi.ctrl.Api(settings)

def use_tmpdir():
  """ Use a temporary directory so we don't mess with other tests config files """
  test_dir = tempfile.mkdtemp()
  os.chdir(test_dir)
  assert test_dir == os.getcwd()

def prune_state(state: amplipi.models.Status):
  """ Prune generated fields from system state to make comparable """
  dstate = state.dict(exclude_none=True)
  for field in dstate['sources']:
    field.pop('info')
  dstate.pop('info')
  # default config only adds float volumes, dB volumes are calculated
  for field in dstate['zones']:
    field.pop('vol')
  for field in dstate['groups']:
    field.pop('vol_delta')
  return dstate

def test_no_config():
  """ Test loading an empty config (should load default config) """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(NO_CONFIG, backup_config=NO_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())

def test_good_config():
  """ Test loading a known good config file by making a copy of it and loading the api with the copy """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())

def test_corrupted_config():
  """ Test loading a corrupted config file with a good backup """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(CORRUPTED_CONFIG, backup_config=GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())

def test_doubly_corrupted_config():
  """ Test loading a corrupted config file and a corrupted backup """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(CORRUPTED_CONFIG, backup_config=CORRUPTED_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())

def test_missing_config():
  """ Test loading a missing config file with a good backup """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(NO_CONFIG, backup_config=GOOD_CONFIG)
  assert GOOD_STATUS == prune_state(api.get_state())

def test_doubly_missing_config():
  """ Test loading a missing config file and a missing backup """
  use_tmpdir() # run from temp dir so we don't mess with current directory
  api = api_w_mock_rt(NO_CONFIG, backup_config=NO_CONFIG)
  assert DEFAULT_STATUS == prune_state(api.get_state())

if __name__ == '__main__':
  # run tests without pytest
  test_no_config()
  test_good_config()
  test_corrupted_config()
  test_doubly_corrupted_config()
  test_missing_config()
  test_doubly_missing_config()
