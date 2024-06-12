""" Test the amplipi rest API """

from typing import Dict, List, Optional, Set

# json utils
import json
from http import HTTPStatus

# we need threads with return values for announcement tests
from concurrent.futures import ThreadPoolExecutor

# temporary directory for each test config
import tempfile
import os
from copy import deepcopy # copy test config

import pytest
from fastapi.testclient import TestClient

# testing context
from context import amplipi

# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
# pylint: disable=too-many-locals

TEST_CONFIG = amplipi.defaults.DEFAULT_CONFIG

NO_SOURCE = -1 # Allows a zone to be disconnected from any source

# add several groups and most of the default streams to the config
TEST_CONFIG['groups'] = [
  {"id": 100, "name": "Group 1", "zones": [1, 2], "source_id": 0, "mute": True, "vol_f": amplipi.models.MIN_VOL_F},
  {"id": 101, "name": "Group 2", "zones": [3, 4], "source_id": 0, "mute": True, "vol_f": amplipi.models.MIN_VOL_F},
  {"id": 102, "name": "Group 3", "zones": [5],    "source_id": 0, "mute": True, "vol_f": amplipi.models.MIN_VOL_F},
  {"id": 103, "name": "Empty",   "zones": [],     "source_id": 0, "mute": True, "vol_f": amplipi.models.MIN_VOL_F},
]
RCAs =  amplipi.defaults.RCAs
AUX_STREAM_ID = amplipi.defaults.AUX_STREAM_ID
AP_STREAM_ID = 1000
P_STREAM_ID = 1001
TEST_CONFIG['streams'] = [
  {"id": AUX_STREAM_ID, "name": "Aux", "type": "aux"},
  {"id": RCAs[0], "name": "Input 1", "type": "rca", "index": 0},
  {"id": RCAs[1], "name": "Input 2", "type": "rca", "index": 1},
  {"id": RCAs[2], "name": "Input 3", "type": "rca", "index": 2},
  {"id": RCAs[3], "name": "Input 4", "type": "rca", "index": 3},
  {"id": AP_STREAM_ID, "name": "AmpliPi", "type": "shairport", "ap2": False},
  {"id": P_STREAM_ID, "name": "Radio Station, needs user/pass/station-id", "type": "pandora", "user": "change@me.com", "password": "CHANGEME", "station": "CHANGEME"},
  {"id": 1002, "name": "AmpliPi", "type": "spotify"},
  {"id": 1003, "name": "Groove Salad", "type": "internetradio", "url": "http://ice6.somafm.com/groovesalad-32-aac", "logo": "https://somafm.com/img3/groovesalad-400.jpg"},
  {"id": 1004, "name": "AmpliPi", "type": "dlna"},
  {"id": 1005, "name": "AmpliPi", "type": "lms"},
]
TEST_CONFIG['presets'] = [
  {"id": 10000,
    "name": "Mute All",
    "state" : {
      "zones" : [
        {"id": 0, "mute": True},
        {"id": 1, "mute": True},
        {"id": 2, "mute": True},
        {"id": 3, "mute": True},
        {"id": 4, "mute": True},
        {"id": 5, "mute": True},
      ]
    }
  },
  {"id": 10001,
    "name": "Play Pandora",
    "state" : {
      "sources" : [
        {"id": 1, "input": "stream=1001"},
      ],
      "groups" : [
        {"id": 100, "source_id": 1},
        {"id": 101, "source_id": 1},
      ]
    }
  }
]

def base_config():
  """ Default Amplipi configuration """
  return TEST_CONFIG

def base_config_copy():
  """ Modify-able Amplipi configuration """
  return deepcopy(TEST_CONFIG)

def base_config_no_presets():
  """ AmpliPi configuration with presets field unpopulated """
  cfg = base_config_copy()
  del cfg['presets']
  return cfg

def base_config_no_groups():
  """ AmpliPi configuration with groups field unpopulated """
  cfg = base_config_copy()
  del cfg['groups']
  return cfg

def base_config_no_streams():
  """ AmpliPi configuration with streams field unpopulated """
  cfg = base_config_copy()
  del cfg['streams']
  return cfg

def base_config_vol_db():
  """ Old AmpliPi configuration with dB volumes only """
  cfg = base_config_copy()
  for z in cfg['zones']:
    del z['vol_f']
    del z['vol_min']
    del z['vol_max']
    z['vol'] = amplipi.models.MIN_VOL_DB
  for g in cfg['groups']:
    del g['vol_f']
    g['vol_delta'] = amplipi.models.MIN_VOL_DB
  return cfg

def status_copy(client):
  """ Modify-able copy of AmpliPi's status """
  rv = client.get('/api/')
  jrv = rv.json()
  assert jrv is not None
  return jrv # jrv was already serialized so it should be a copy

def find(elements:List, eid:int):
  """ Find an element with id==eid """
  for i in elements:
    if i['id'] == eid:
      return i
  return None

@pytest.fixture(params=[base_config_copy(), base_config_no_presets(), base_config_no_groups(), base_config_no_streams(), base_config_vol_db()])
def client(request):
  """ AmpliPi instance with mocked ctrl and streams """
  cfg = request.param
  config_dir = tempfile.mkdtemp()
  # write a valid version to the cache directory, needed by test_get_info
  status_dir = amplipi.defaults.USER_CONFIG_DIR
  os.makedirs(status_dir, exist_ok=True)
  with open(os.path.join(status_dir, 'latest_release'), 'w', encoding='utf-8') as version_file:
    version_file.write('0.1.8\n')
  config_file = os.path.join(config_dir, 'house.json')
  with open(config_file, 'w', encoding='utf') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock_ctrl=True, mock_streams=True, config_file=config_file, delay_saves=False)
  c = TestClient(app)
  c.original_config = deepcopy(cfg) # add the loaded config so we can remember what was loaded
  return c

@pytest.fixture(params=[base_config_copy(), base_config_no_presets(), base_config_no_groups(), base_config_no_streams(), base_config_vol_db()])
def clientnm(request):# Non-mock systems should use this client - mock_ctrl and mock_streams are False here
  """ AmpliPi instance connected to a real AmpliPi controller """
  cfg = request.param
  config_dir = tempfile.mkdtemp()
  config_file = os.path.join(config_dir, 'house.json')
  # write a valid version to the cache directory, needed by test_get_info
  status_dir = amplipi.defaults.USER_CONFIG_DIR
  os.makedirs(status_dir, exist_ok=True)
  with open(os.path.join(status_dir, 'latest_release'), 'w', encoding='utf-8') as version_file:
    version_file.write('0.1.8\n')
  with open(config_file, 'w') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock_ctrl=False, mock_streams=False, config_file=config_file, delay_saves=False)
  c = TestClient(app)
  c.original_config = deepcopy(cfg) # add the loaded config so we can remember what was loaded
  return c

# TODO: the web view test should be added to its own testfile once we add more functionality to the site
@pytest.mark.parametrize('path', ['' , '/'])
def test_view(client: TestClient, path):
  """ Test the web app's main view """
  rv = client.get(path)
  assert rv.status_code == HTTPStatus.OK

@pytest.mark.parametrize('path', ['/api', '/api/'])
def test_base(client, path):
  """ Start with a basic controller and just check if it gives a real response """
  rv = client.get(path)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    jrv = rv.json()
    assert jrv is not None
    og_config = client.original_config
    for t in ['sources', 'streams', 'zones', 'groups', 'presets']:
      if t in og_config:
        assert len(jrv[t]) == len(og_config[t])
    # make sure a real version is reported
    assert 'info' in jrv and 'version' in jrv['info']
    assert len(jrv['info']['version'].split('.')) in [3,4] # alpha/beta builds have an extra version string
  else:
    assert path == '/api'
    assert '/api/' in rv.location

def test_reset(client):
  """ Reset the firmware """
  rv = client.post('/api/reset')
  assert rv.status_code == HTTPStatus.OK

def check_config(expected, actual):
  """Check configuration changes match expected"""
  assert actual is not None
  for t in ['sources', 'streams', 'zones', 'groups', 'presets']:
    if t in expected:
      assert t in actual, f'missing field {t}'
      assert len(actual[t]) == len(expected[t]), f'failed to load {t} portion of configuration expected: {expected[t]}, actual: {actual[t]}'
      # check ids and names match for each field, avoiding generated data
      exp_ids = { exp["id"]: exp for exp in expected[t] }
      for iact in actual[t]:
        assert iact["id"] in exp_ids, f'{iact["name"]}(id={iact["id"]}) missing from expected config'
        assert iact["name"] == exp_ids[iact["id"]]["name"], f'{iact["name"]} does not match expected={exp_ids[iact["id"]]["name"]}'
    else:
      assert t in actual, f'missing field {t}, it is still expected to be generated empty even though it not specified in the expected configuration'
      if t == 'streams':
        assert len(actual[t]) == 5, f'{t} should be populated by the 4 default RCA streams and the aux stream'
      else:
        assert len(actual[t]) == 0, f'{t} should be empty since it is not preset in expected config'

def test_load_og_config(client):
  """ Reload the initial configuration """
  rv = client.post('/api/load', json=client.original_config)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(client.original_config, rv.json())

def test_load_null_config(client):
  """ Load with the basic default configuration """
  rv = client.post('/api/load', json=amplipi.models.Status().dict())
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(amplipi.models.Status().dict(), rv.json())

def test_load_stream_missing_config(client):
  """ A config loaded with a missing stream will be a common problem when changing versions.
    This will happend when a version does not support a specific stream type
  """
  # create a config with an unloadable stream
  unsupported_stream_cfg = amplipi.models.Status().dict()
  unsupported_stream_cfg['sources'][0]['input'] = 'stream=2000'
  unsupported_stream_cfg['streams'] = [
    {"id": 2000, 'name': 'Unsupported stream', "type": "unsupported-type" }
  ]
  rv = client.post('/api/load', json=unsupported_stream_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    # config should be loaded without unsupported stream and source input should be set to ''
    status = rv.json()
    check_config(amplipi.models.Status().dict(), rv.json())
    assert status['sources'][0]['input'] == ''

def test_load_old_config(client):
  """ Test that an old config has its RCA input names updated and the aux stream and version number are added"""
  # convert the config into something that looks like an old config
  source_names = ['tv', 'record player', 'cd player', 'jukebox']
  old_config = base_config_copy()
  old_config.pop('version')
  old_config['streams'].pop(0) # remove the aux stream
  for i in range(4):
    rca_stream = old_config['streams'].pop(0)
    assert rca_stream['type'] == 'rca'
  for src in old_config['sources']:
    src['name'] = source_names[src['id']]
  # load the old config, the value returned should be a config that has been converted
  rv = client.post('/api/load', json=old_config)
  assert rv.status_code == HTTPStatus.OK
  status = rv.json()
  assert status['version'] == 1, 'version number was not added to old config'
  for s in status['streams']:
    if s['type'] == 'rca':
      assert s['name'] == source_names[s['index']], print('old source name was not converted to rca stream name')
  assert status['streams'][0]['type'] == 'aux', 'aux stream was not added to old config'

def test_load_multi_config(client):
  """ Load multiple configurations """
  # create a test config with a multiple connected stream
  sinputs = [f'stream={AP_STREAM_ID}', f'stream={P_STREAM_ID}']
  multi_stream_cfg = client.original_config
  if 'streams' in multi_stream_cfg:
    multi_stream_cfg['sources'][0]['input'] = sinputs[0]
    multi_stream_cfg['sources'][1]['input'] = sinputs[1]
    assert multi_stream_cfg['streams'][5]['id'] == AP_STREAM_ID, f"Test config expects a stream with id={AP_STREAM_ID}"
    assert multi_stream_cfg['streams'][6]['id'] == P_STREAM_ID, f"Test config expects a stream with id={P_STREAM_ID}"
  # create a simple config with a single stream connected, with metadata representing raw config load
  single_stream_cfg = amplipi.models.Status().dict()
  single_stream_cfg['sources'][0] = {
    "id": 0,
    "name": "Input 1",
    "input": "stream=2000",
    "info": {
      "name": "Groove Salad - internet radio",
      "state": "playing",
      "artist": "Liam Thomas",
      "track": "With your touch",
      "station": "Groove Salad [SomaFM]",
      "img_url": "https://somafm.com/img3/groovesalad-400.jpg",
      "supported_cmds": [
        "play",
        "stop"
      ]
    }
  }
  single_stream_cfg['streams'] = [
    {"id": AUX_STREAM_ID, "name": "Aux", "type": "aux"},
    {"id": RCAs[0], "name": "Input 1", "type": "rca", "index": 0},
    {"id": RCAs[1], "name": "Input 2", "type": "rca", "index": 1},
    {"id": RCAs[2], "name": "Input 3", "type": "rca", "index": 2},
    {"id": RCAs[3], "name": "Input 4", "type": "rca", "index": 3},
    {"id": 2000, 'name': 'Groove Salad', "type": "internetradio",
     "url": "http://ice6.somafm.com/groovesalad-32-aac", "logo": "https://somafm.com/img3/groovesalad-400.jpg"}
  ]
  # create a barebones config with no streams
  bare_cfg = deepcopy(amplipi.models.Status().dict())
  # load a barebones config
  rv = client.post('/api/load', json=bare_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(bare_cfg, rv.json())
  # load a single stream config
  rv = client.post('/api/load', json=single_stream_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(single_stream_cfg, rv.json())
  # load the multi stream config with a stream (testing the transition from simple -> more complicated)
  rv = client.post('/api/load', json=multi_stream_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(multi_stream_cfg, rv.json())
  # load a single stream config (testing the transition from more complicated -> simple)
  rv = client.post('/api/load', json=single_stream_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(single_stream_cfg, rv.json())
  # load a bare config (testing the transition from more simple -> bare bones)
  rv = client.post('/api/load', json=bare_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(bare_cfg, rv.json())
  # load the multi stream config with a stream (testing the transition from bare -> more complicated)
  rv = client.post('/api/load', json=multi_stream_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(multi_stream_cfg, rv.json())
  # load a bare config (testing the transition from complex -> bare bones)
  rv = client.post('/api/load', json=bare_cfg)
  assert rv.status_code == HTTPStatus.OK
  if rv.status_code == HTTPStatus.OK:
    check_config(bare_cfg, rv.json())

def test_open_api_yamlfile(client):
  """ Check if the openapi yaml doc is available """
  rv = client.get('/openapi.yaml')
  assert rv.status_code == HTTPStatus.OK

# To reduce the amount of boilerplate we use test parameters.
# Examples: https://docs.pytest.org/en/stable/example/parametrize.html#paramexamples

# Test Status
def test_get_info(client):
  """ Check the system information """
  rv = client.get(f'/api/info')
  print('getting info')
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  for key, val in jrv.items():
    assert val is not None, f"Unpopulated info field {key}, expected value got 'None'"
    if isinstance(val, str):
      assert val.lower() != 'unknown', f"Unpopulated info field {key}"

# Test Sources
def base_source_ids():
  """ Default Source ids """
  return [ s['id'] for s in base_config()['sources']]

@pytest.mark.parametrize('sid', base_source_ids())
def test_get_source(client, sid):
  """ Try getting each of the sources """
  rv = client.get(f'/api/sources/{sid}')
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(base_config()['sources'], sid)
  assert s is not None
  assert s['name'] == jrv['name']
  assert jrv['info']['supported_cmds'] is not None

@pytest.mark.parametrize('sid', base_source_ids())
def test_patch_source_name(client, sid):
  """ Try changing a source's name """
  rv = client.patch('/api/sources/{}'.format(sid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['sources'], sid)
  assert s is not None
  assert s['name'] == 'patched-name'

@pytest.mark.parametrize('src_id', base_source_ids())
@pytest.mark.parametrize('_input', ['stream=1001', 'stream=-1', 'stream=RCA', 'stream=WRONG_RCA', '']) # add a non-existent stream
def test_patch_source_input(client, src_id, _input):
  """ Try changing a source's input """
  last_state = status_copy(client)
  wrong_rca = False
  if 'WRONG_RCA' in _input:
    wrong_rca = True
    _input = _input.replace('WRONG_RCA', str(RCAs[src_id-1]))
  elif 'RCA' in _input:
    _input = _input.replace('RCA', str(RCAs[src_id]))
  stream_id = int(_input.split('stream=')[1]) if _input and 'stream=' in _input else -1
  rv = client.patch('/api/sources/{}'.format(src_id), json={'input': _input})
  if _input == '' or (find(last_state['streams'], stream_id) and not wrong_rca):
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    s = find(jrv['sources'], src_id)
    assert s is not None
    assert s['input'] == _input
  else:
    assert rv.status_code != HTTPStatus.OK
    # now lets verify nothing changed
    last_src = find(last_state['sources'], src_id)
    rv = client.get('/api/')
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    s = find(jrv['sources'], src_id)
    assert s is not None
    assert s['input'] == last_src['input'], 'input modified on failed patch'

@pytest.mark.parametrize('sid', base_source_ids())
def test_get_source_image(client, sid):
  """ Try getting an image for a source """
  rv = client.get('/api')
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['sources'], sid)
  expected_file = os.path.basename(s['info']['img_url']).replace('.svg', '.jpg')
  rv = client.get(f'/api/sources/{sid}/image/100')
  assert rv.status_code == HTTPStatus.OK
  assert rv.headers['content-type'] == 'image/jpg'
  assert int(rv.headers['content-length']) > 100
  assert rv.headers['content-disposition'] == f'attachment; filename="{expected_file}.jpg"'

# Test Zones
def base_zone_ids():
  """ Default zones """
  return [ s['id'] for s in base_config()['zones']]

@pytest.mark.parametrize('zid', base_zone_ids())
def test_get_zone(client, zid):
  """ Try getting a zone """
  rv = client.get('/api/zones/{}'.format(zid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(base_config()['zones'], zid)
  assert s is not None
  assert s['name'] == jrv['name']

@pytest.mark.parametrize('zid', base_zone_ids())
def test_patch_zone_rename(client, zid):
  """ Try changing a zones name """
  rv = client.patch('/api/zones/{}'.format(zid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['name'] == 'patched-name'

@pytest.mark.parametrize('zid', base_zone_ids())
def test_patch_zone_mute_disable(client, zid):
  """ Unmute then disable a zone """
  rv = client.patch('/api/zones/{}'.format(zid), json={'mute': False, 'vol_f': 0.5})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['mute'] == False
  assert s['vol_f'] == 0.5
  rv = client.patch('/api/zones/{}'.format(zid), json={'disabled': True})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['disabled'] == True
  assert s['mute'] == True
  rv = client.patch('/api/zones/{}'.format(zid), json={'mute': False})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['mute'] == True # a disabled zone overrides/forces mute

@pytest.mark.parametrize('zid', base_zone_ids())
def test_patch_zone_mute_disconnect(client, zid):
  """ Unmute then disconnect a zone """
  rv = client.patch('/api/zones/{}'.format(zid), json={'mute': False, 'vol_f': 0.5})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['mute'] == False
  assert s['vol_f'] == 0.5
  rv = client.patch('/api/zones/{}'.format(zid), json={'source_id': NO_SOURCE})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['source_id'] == -1
  assert s['mute'] == True
  rv = client.patch('/api/zones/{}'.format(zid), json={'mute': False})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['mute'] == True # a disconnected zone overrides/forces mute

@pytest.mark.parametrize('sid', base_source_ids())
def test_patch_zones(client, sid):
  """ Try changing multiple zones """
  rv = client.patch('/api/zones', json={'zones': [z for z in range(6)], 'update': {'source_id': sid}})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert len(jrv['zones']) >= 6
  for z in jrv['zones']:
    if z['id'] in range(6):
      assert z['source_id'] == sid

def test_patch_zones_duplicate_name(client):
  """ Try changing multiple zones and setting base name """
  rv = client.patch('/api/zones', json={'zones': [z for z in range(6)], 'update': {'name': 'test'}})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert len(jrv['zones']) >= 6
  for z in jrv['zones']:
    if z['id'] in range(6):
      assert z['name'] == f"test {z['id']+1}"

# Test Groups
def base_group_ids():
  """ Default groups """
  return [ s['id'] for s in base_config()['groups']]

def test_post_group(client):
  """ Try creating a new group """
  # check that the whole house group doesn't already exist
  rv = client.get('/api')
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert 'groups' in jrv
  for g in jrv['groups']:
    assert 'name' in g
    assert g['name'] != 'Whole House'
  # try creating the whole house group
  grp = {'name' : 'Whole House', 'zones' : [0, 1, 2, 3, 4, 5]}
  rv = client.post('/api/group', json=grp)
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert 'id' in jrv
  assert isinstance(jrv['id'], int)
  for k, v in grp.items():
    assert jrv[k] == v

@pytest.mark.parametrize('gid', base_group_ids())
def test_get_group(client, gid):
  """ Try getting a default group """
  last_state = status_copy(client)
  rv = client.get('/api/groups/{}'.format(gid))
  if find(last_state['groups'], gid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json()
  s = find(base_config()['groups'], gid)
  assert s is not None
  assert s['name'] == jrv['name']

@pytest.mark.parametrize('gid', base_group_ids())
def test_patch_group(client, gid):
  """ Try changing a group's name """
  last_state = status_copy(client)
  rv = client.patch('/api/groups/{}'.format(gid), json={'name': 'patched-name'})
  if find(last_state['groups'], gid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json()
  s = find(jrv['groups'], gid)
  assert s is not None
  assert s['name'] == 'patched-name'

@pytest.mark.parametrize('gid', base_group_ids())
def test_delete_group(client, gid):
  """ Try deleting a group """
  rv = client.delete('/api/groups/{}'.format(gid))
  if 'groups' in client.original_config and find(client.original_config['groups'], gid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json()
  s = find(jrv['groups'], gid)
  assert s is None
  for other_gid in base_group_ids():
    if other_gid != gid:
      assert find(jrv['groups'], other_gid) is not None

# test streams
def base_stream_ids():
  """ Return all of the stream IDs belonging to each of the streams in the base config """
  return [s['id'] for s in base_config()['streams']]

def removable_stream_ids():
  """ Only removable streams (RCAs are exempt) """
  return [s for s in base_stream_ids() if s not in (RCAs + [AUX_STREAM_ID])]

def airplay_stream_ids():
  return [s['id'] for s in base_config()['streams'] if s['type'] == 'airplay' or s['type'] == 'shairport']

def airplay_names():
  return {
    "AmpliPi": True,
    "Living Room TV": True,
    "Kitchen Speaker": True,
    "Bedroom HomePod": True,
    "Office Sound System": True,
    "Den Apple TV": True,
    "Bathroom Speaker": True,
    "Patio Sound Bar": True,
    "Garage Music System": True,
    "Family Room Home Theater": True,
    "Guest Room Sound Dock": True,
    "Living Room TV with Surround Sound and Subwoofer System Installed": False,
    "Kitchen Speaker with Alexa Integration and Advanced Sound Control": False,
    "Bedroom HomePod with Personalized Audio Settings and Custom EQ": False,
    "Office Sound System Featuring High Fidelity Audio and Noise Cancellation": False,
    "Den Apple TV Connected to Home Theater System with Dolby Atmos Support": False,
    "Bathroom Speaker with Waterproof Design and Extended Battery Life": False,
    "Patio Sound Bar with Wireless Subwoofer and Multi-Room Audio Capability": False,
    "Garage Music System with Enhanced Bass and Treble Controls for Optimum Sound": False,
    "Family Room Home Theater System with 4K UHD and High Dynamic Range": False,
    "Guest Room Sound Dock with Bluetooth and Wi-Fi Connectivity for Easy Streaming": False
  }.items()

def pandora_stream_ids():
  return [s['id'] for s in base_config()['streams'] if s['type'] == 'pandora']

def pandora_users():
  return {
    "change@me.com": True,
    "user@example.com": True,
    "john.doe@example.co.uk": True,
    "user_name123@example.org": True,
    "user.name+alias@sub.domain.net": True,
    "user.name@example.travel": True,
    "username@domain.co": True,
    "user123@example.io": True,
    "user@domain.commmm": True,
    "user@.com": False,
    "user@domain.c": False,
    "@example.com": False,
    "user@domain..com": False,
    "user@domain_com": False,
    "user@domain,com": False,
    "user@domain": False,
    "userdomain.com": False,
  }.items()

def spotify_stream_ids():
  return [s['id'] for s in base_config()['streams'] if s['type'] == 'spotify']

def spotify_names():
  return {
    "AmpliPi": True,
    "device1": True,
    "device-name": True,
    "my-device": True,
    "device.name": True,
    "device1.device2": True,
    "my-device.name-2": True,
    "-device": False,
    "device-": False,
    "device..name": False,
    "device-.name": False,
    "device.name-": False,
    "device!name": False,
    ".device": False,
    "device..name": False
  }.items()

def internetradio_stream_ids():
  return [s['id'] for s in base_config()['streams'] if s['type'] == 'internetradio']

def internetradio_urls():
  return {
    "http://ice6.somafm.com/groovesalad-32-aac" : True,
    "https://www.example.com": True,
    "http://www.example.com": True,
    "https://example.com": True,
    "http://example.com": True,
    "https://www.example.co.uk": True,
    "https://subdomain.example.com/path/to/page": True,
    "http://sub.domain.example.com": True,
    "ftp://www.example.com": False,
    "http://www.example": False,
    "https://example": False,
}.items()

def internetradio_logos():
  return {
    "https://somafm.com/img3/groovesalad-400.jpg": True,
    "https://www.example.com/logo.jpg" : True,
    "http://example.com/logo.jpg" : True,
    "https://www.example.com/logo123.jpg": True,
    "https://example.com/logo.jpg" : True,
    "http://www.example.com/logo123.jpg" : True,
    "https://www.example.com/logo.png" : True,
    "ftp://www.example.com/logo.jpg" : False,
    "https://www.example.com/logos/logo.jpg" : True,
    "https://www.example.com/logo" : False,
    "https://example.com/logo/jpg" : False,
    "https://www.example.com/logo?size=medium.jpg ": False
  }.items()

# /stream post-stream
@pytest.mark.parametrize('name, valid', airplay_names())
def test_create_airplay(client, name, valid):
  """ Try creating a AirPlay stream """
  m_and_k = { 'name': name, 'type':'airplay'}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  if valid:
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    assert 'id' in jrv
    assert isinstance(jrv['id'], int)
    for k, v in m_and_k.items():
      assert jrv[k] == v
  else:
    assert rv.status_code == HTTPStatus.BAD_REQUEST
 
# /stream post-stream
@pytest.mark.parametrize('user, valid', pandora_users())
def test_create_pandora(client, user, valid):
  """ Try creating a Pandora stream """
  m_and_k = { 'name': 'Matt and Kim Radio', 'type':'pandora', 'user': user, 'password': ''}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  if valid:
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    assert 'id' in jrv
    assert isinstance(jrv['id'], int)
    for k, v in m_and_k.items():
      assert jrv[k] == v
  else:
    assert rv.status_code == HTTPStatus.BAD_REQUEST

 # /stream post-stream
@pytest.mark.parametrize('name, valid', spotify_names())
def test_create_spotify(client, name, valid):
  """ Try creating a Spotify stream """
  m_and_k = { 'name': name, 'type':'spotify'}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  if valid:
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    assert 'id' in jrv
    assert isinstance(jrv['id'], int)
    for k, v in m_and_k.items():
      assert jrv[k] == v
  else:
    assert rv.status_code == HTTPStatus.BAD_REQUEST
 
@pytest.mark.parametrize('url, valid_url', internetradio_urls())
@pytest.mark.parametrize('logo, valid_logo', internetradio_logos())
def test_create_internetradio(client, url, valid_url, logo, valid_logo):
  """ Try creating an Internet Radio stream """
  m_and_k = { 'name': 'Beatles Radio', 'type': 'internetradio', 'url': url, 'logo': logo}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  if valid_url and valid_logo:
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    assert 'id' in jrv
    assert isinstance(jrv['id'], int)
    for k, v in m_and_k.items():
      assert jrv[k] == v
  else:
    assert rv.status_code == HTTPStatus.BAD_REQUEST

# /streams/{streamId} get-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_get_stream(client, sid):
  """ Try getting a default stream """
  last_state = status_copy(client)
  rv = client.get('/api/streams/{}'.format(sid))
  if find(last_state['streams'], sid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json()
  s = find(base_config()['streams'], sid)
  assert s is not None
  assert s['name'] == jrv['name']

# /streams/{streamId} patch-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_patch_stream_rename(client, sid):
  """ Try renaming a stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'name': 'patched-name'})
  if find(last_state['streams'], sid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['name'] == 'patched-name'

@pytest.mark.parametrize('sid', airplay_stream_ids())
@pytest.mark.parametrize('name, valid', airplay_names())
def test_patch_stream_rename_airplay(client, sid, name, valid):
  """ Try renaming an AirPlay stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'name': name})
  if find(last_state['streams'], sid):
    if valid:
      assert rv.status_code == HTTPStatus.OK
    else:
      assert rv.status_code == HTTPStatus.BAD_REQUEST
      return
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['name'] == name


@pytest.mark.parametrize('sid', spotify_stream_ids())
@pytest.mark.parametrize('name, valid', spotify_names())
def test_patch_stream_rename_spotify(client, sid, name, valid):
  """ Try renaming a Spotify stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'name': name})
  if find(last_state['streams'], sid):
    if valid:
      assert rv.status_code == HTTPStatus.OK
    else:
      assert rv.status_code == HTTPStatus.BAD_REQUEST
      return
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['name'] == name

@pytest.mark.parametrize('sid', pandora_stream_ids())
@pytest.mark.parametrize('user, valid', pandora_users())
def test_patch_stream_rename_pandora(client, sid, user, valid):
  """ Try renaming a Pandora stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'user': user})
  if find(last_state['streams'], sid):
    if valid:
      assert rv.status_code == HTTPStatus.OK
    else:
      assert rv.status_code == HTTPStatus.BAD_REQUEST
      return
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['user'] == user

@pytest.mark.parametrize('sid', internetradio_stream_ids())
@pytest.mark.parametrize('url, valid_url', internetradio_urls())
@pytest.mark.parametrize('logo, valid_logo', internetradio_logos())
def test_patch_stream_rename_internetradio(client, sid, url, valid_url, logo, valid_logo):
  """ Try renaming a Internet Radio stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'url': url, 'logo': logo})
  if find(last_state['streams'], sid):
    if valid_url and valid_logo:
      assert rv.status_code == HTTPStatus.OK
    else:
      assert rv.status_code == HTTPStatus.BAD_REQUEST
      return
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['url'] == url
  assert s['logo'] == logo

@pytest.mark.parametrize('sid', base_stream_ids())
@pytest.mark.parametrize('disable', [True, False])
def test_patch_stream_disable(client, sid, disable):
  """ Try disabling a stream """
  last_state = status_copy(client)
  rv = client.patch('/api/streams/{}'.format(sid), json={'disabled': disable})
  if find(last_state['streams'], sid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was disabled
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['disabled'] == disable

@pytest.mark.parametrize('ap2', [True, False])
def test_patch_stream_ap2(client, ap2):
  """ Try configuring the ap2 field of an airplay stream """
  last_state = status_copy(client)
  sid = AP_STREAM_ID
  rv = client.patch('/api/streams/{}'.format(sid), json={'ap2': ap2})
  if find(last_state['streams'], sid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was configured to ap2
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['ap2'] == ap2

# /streams/{streamId} delete-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_delete_stream(client, sid):
  """ Try deleting a stream  """
  last_state = status_copy(client)
  rv = client.delete('/api/streams/{}'.format(sid))
  if find(last_state['streams'], sid) and sid in removable_stream_ids():
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was deleted
  s = find(jrv['streams'], sid)
  assert s is None
  # make sure the rest of the streams are still there
  for other_sid in base_stream_ids():
    if other_sid != sid:
      assert find(jrv['streams'], other_sid) is not None

@pytest.mark.parametrize('sid', base_stream_ids())
def test_delete_connected_stream(client, sid):
  """ Delete a connected stream and make sure it gets disconnected from the source it is connected to"""
  last_state = status_copy(client)
  rv = client.patch('/api/sources/0', json={'input': f'stream={sid}'})
  if find(last_state['streams'], sid) and sid not in RCAs[1:4]:
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  rv = client.delete(f'/api/streams/{sid}')
  if sid in RCAs+[AUX_STREAM_ID]:
    assert rv.status_code != HTTPStatus.OK
    return
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json() # get the system state returned
  assert jrv['sources'][0]['input'] == ''

# Non-Mock client used - run this test on the Pi
# _live tests will be excluded from GitHub testing
@pytest.mark.parametrize('cmd', ['play', 'pause', 'stop', 'next', 'love', 'ban', 'shelve'])
def test_post_stream_cmd_live(clientnm, cmd):
  """ Try sending commands to a pandora stream on a live system """
  # TODO: this test is failing when executed with all of the other tests in parallel see below
  # Add a stream to send commands to
  m_and_k = { 'name': 'Matt and Kim Radio', 'type':'pandora', 'user': 'lincoln@micro-nova.com', 'password': '2yjT4ZXkcr7FNWb', 'station': '4610303469018478727'}
  rv = clientnm.post('/api/stream', json=m_and_k)
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  sid = jrv['id']
  rv = clientnm.patch('/api/sources/0', json={'input': f'stream={sid}'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  # the check below will fail when run in parallel with other tests, why is the configuration different than expected????
  assert not jrv['info']['mock_streams']
  rv = clientnm.post('/api/streams/{}/{}'.format(sid, cmd))
  jrv = rv.json()
  assert not jrv['info']['mock_streams']
  assert rv.status_code == HTTPStatus.OK

# test presets
def base_preset_ids():
  """ Return all of the preset IDs belonging to each of the presets in the base config """
  return [ s['id'] for s in base_config()['presets']]

# /preset post-preset
def test_create_mute_all_preset(client):
  """ Try creating the simplest preset, something that mutes all the zones """
  mute_some = { 'name' : 'Mute some', 'state': { 'zones' : [ { 'id' : 1, 'mute': True}, { 'id' : 4, 'mute': True} ]}}
  rv = client.post('/api/preset', json=mute_some)
  # check that the stream has an id added to it and that all of the fields are still there
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert 'id' in jrv
  assert isinstance(jrv['id'], int)
  assert jrv['name'] == mute_some['name']
  for i, z in enumerate(mute_some['state']['zones']):
    for k,v in z.items():
      assert jrv['state']['zones'][i][k] == v

# /presets/{presetId} get-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_get_preset(client, pid):
  """ Try to get one of the default presets """
  last_state = status_copy(client)
  rv = client.get('/api/presets/{}'.format(pid))
  if find(last_state['presets'], pid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json()
  s = find(base_config()['presets'], pid)
  assert s is not None
  assert s['name'] == jrv['name']

# /presets/{presetId} patch-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_patch_preset_name(client, pid):
  """ Try changing the presets name """
  last_state = status_copy(client)
  rv = client.patch('/api/presets/{}'.format(pid), json={'name': 'patched-name'})
  if find(last_state['presets'], pid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['presets'], pid)
  assert s is not None
  assert s['name'] == 'patched-name'

# /presets/{presetId} delete-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_delete_preset(client, pid):
  """ Try to delete a preset """
  rv = client.delete('/api/presets/{}'.format(pid))
  if 'presets' in client.original_config and find(client.original_config['presets'], pid):
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the preset was deleted
  s = find(jrv['presets'], pid)
  assert s is None
  # make sure the rest of the presets are still there
  for other_pid in base_preset_ids():
    if other_pid != pid:
      assert find(jrv['presets'], other_pid) is not None

# /presets/{presetId}/load load-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_load_preset(client, pid, unmuted=[1,2,3]):
  """ Load a preset configuration with some zones unmuted """
  # TODO: cleanup test structure
  # pylint: disable=dangerous-default-value,too-many-locals,too-many-branches
  # unmute some of the zones
  for zid in unmuted:
    client.patch('/api/zones/{}'.format(zid), json={'mute': False})
  # save the preloaded state
  last_state = status_copy(client)
  # load the preset (in some configurations it won't exist; make sure it fails in that case)
  rv = client.post('/api/presets/{}/load'.format(pid))
  p = find(last_state['presets'], pid)
  if p:
    # check if all of the needed groups exist (it will fail if one of the needed groups doesn't exist')
    effected_groups = { g['id'] for g in p['state'].get('groups', [])}
    missing = False
    for g in effected_groups:
      if not find(last_state['groups'], g):
        missing = True
    # check for streams that are used but unavailable
    effected_source_inputs = { s.get('input', None) for s in p['state'].get('sources', [])}
    for _input in effected_source_inputs:
      if _input in ['']:
        pass
      elif 'stream=' in _input:
        stream_id = int(_input.split('stream=')[1])
        if not find(last_state['streams'], stream_id):
          missing = True
    if missing:
      assert rv.status_code != HTTPStatus.OK
      return
    assert rv.status_code == HTTPStatus.OK
  else:
    assert rv.status_code != HTTPStatus.OK
    return
  jrv = rv.json() # get the system state returned
  jrv.pop('info')
  # TODO: check that the system state is valid
  # make sure the rest of the config got loaded
  for mod, configs in p['state'].items():
    for cfg in configs:
      # each of the keys in the configuration should match
      updated_cfg = find(jrv[mod], cfg['id'])
      assert updated_cfg is not None
      for k, v in cfg.items():
        assert updated_cfg[k] == v
  # verify all of the zones mute levels remained the same (unless they were changed by the preset configuration)
  preset_zones_changes = p['state'].get('zones', None)
  preset_groups_changes = p['state'].get('groups', None)
  for z in jrv['zones']:
    expected_mute = last_state['zones'][z['id']]['mute']
    if preset_zones_changes:
      pz = find(preset_zones_changes, z['id'])
      if pz and 'mute' in pz:
        expected_mute = pz['mute']
    # check if the zone will be muted by a group (group updates are currently applied after zone updates)
    # assuming here that if a zone belonging to multiple groups has its mute changed
    # by multiple group updates, it is the last group update that takes effect on the zone
    if preset_groups_changes:
      for pg in preset_groups_changes:
        if 'mute' in pg:
          g = find(last_state['groups'], pg['id'])
          assert g is not None
          if z['id'] in g['zones']:
            expected_mute = pg['mute']
    assert z['mute'] == expected_mute
  # load the saved config and verify that the sources, zones, and groups are the same as initial state (before the preset was loaded)
  LAST_CONFIG_PRESET = 9999
  rv = client.post('/api/presets/{}/load'.format(LAST_CONFIG_PRESET))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json() # get the system state returned
  jrv.pop('info')
  ignore = ['last_used', 'info', 'status']
  for name, mod in jrv.items():
    prev_mod = last_state[name]
    if name == 'version': # skip version as it is not iterable
      continue
    for cfg in mod:
      if cfg['id'] != LAST_CONFIG_PRESET:
        prev_cfg = find(prev_mod, cfg['id'])
        for ignored_field in ignore:
          if ignored_field in prev_cfg:
            prev_cfg.pop(ignored_field)
          if ignored_field in cfg:
            cfg.pop(ignored_field)
        assert cfg == prev_cfg

def test_announcement(client):
  """Check if a PA Announcement works """
  nasa_audio = 'https://www.nasa.gov/wp-content/uploads/2015/01/640150main_Go20at20Throttle20Up.mp3'
  # error, needs media
  rv = client.post('/api/announce', json={})
  assert rv.status_code != HTTPStatus.OK, 'Should require media field'
  # default volume/source
  rv = client.post('/api/announce', json={'media': nasa_audio})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)
  # force source
  rv = client.post('/api/announce', json={'media': nasa_audio, 'src': 2})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)
  # force db volume
  rv = client.post('/api/announce', json={'media': nasa_audio, 'vol': -40})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)
  rv = client.post('/api/announce', json={'media': nasa_audio, 'vol': -40, 'src': 1})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)
  # force relative volume
  rv = client.post('/api/announce', json={'media': nasa_audio, 'vol_f': 0.5})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)
  rv = client.post('/api/announce', json={'media': nasa_audio, 'vol_f': 0.5, 'src': 0})
  assert rv.status_code == HTTPStatus.OK, print(rv.text)

  def check_zones(muted_zones: Set[int]) -> bool:
    """Check if zones are muted"""
    print(f'Checking zone mute status')
    # wait for the announcement to start playing, then validate zone mute status

    print(f'Waiting for announcement to start playing')
    playing = False
    retry_count = 0
    while not playing and retry_count < 10:
      rv = client.get('/api')
      assert rv.status_code == HTTPStatus.OK, print(rv.text)
      try:
        state = rv.json()['sources'][0]['info']['state']
        playing = state == 'playing'
      except KeyError:
        pass
      retry_count += 1

    assert retry_count < 10, 'Timed out waiting for announcement to start playing'

    for z in rv.json()['zones']:
      should_be_muted = z['id'] in muted_zones
      assert z['mute'] == should_be_muted, f'Zone {z["id"]} should be {"muted" if should_be_muted else "unmuted"}'
    return True

  all_zones = list(range(6))
  rv = client.patch('/api/zones', json={'zones' : all_zones, 'update': {'source_id': 0, 'mute': False}})
  assert rv.status_code == HTTPStatus.OK, f'Failed to unmute zones: {rv.text}'

  # request an announcement on the same source all zones are connected to,
  # validate the zones that aren't announced on are muted, and the others are unmuted
  pa_zones = [4]
  with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(check_zones, set(all_zones) - set(pa_zones))
    rv = client.post('/api/announce', json={'media': nasa_audio, 'source_id': 0, 'zones': pa_zones})
    assert rv.status_code == HTTPStatus.OK, print(rv.text)
    assert future.result(timeout=1.0) == True, "Zone check failed"

def test_api_doc_has_examples(client):
  """Check if each api endpoint has example responses (and requests)"""
  rv = client.get('/openapi.json') # use json since it is easier to check
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  for path, p in jrv['paths'].items():
    for method, m in p.items():
      path_desc = f'{path} - {method}'
      # check for examples of the request on
      if method in ['post', 'put', 'patch']:
        try:
          req_spec = m['requestBody']['content']['application/json']
          assert 'example' in req_spec or 'examples' in req_spec, f'{path_desc}: At least one exmaple request required'
          if 'exmaples' in req_spec:
            assert len(req_spec['examples']) > 0, f'{path_desc}: At least one exmaple request required'
        except KeyError:
          pass # request could be different type or non-existent
      try:
        resp_spec = m['responses']['200']['content']['application/json']
        assert 'example' in resp_spec or 'examples' in resp_spec, f'{path_desc}: At least one exmaple response required'
        if 'exmaples' in resp_spec:
          assert len(resp_spec['examples']) > 0, f'{path_desc}: At least one exmaple response required'
      except KeyError:
        pass # reposnse could not be json

# TODO: this test will fail until we come up with a good scheme for specifying folder locations in a global config
# The test below fails since the test and the app are run in different directories
# skipping it for now until #117
@pytest.mark.skip
def test_generate(client):
  """ Test valid accesses to the generated folder structure """
  fullpath = os.path.abspath('web/generated')
  fullerpath = '{}/shairport/srcs/t'.format(fullpath)
  if not os.path.exists(fullerpath):
    os.makedirs(fullerpath)
  test_filenames = ['test.txt', 'shairport/srcs/t/IMG_A1', '../shairport/srcs/t/Trying-to-cheat-the-system']
  for fn in test_filenames:
    test_name = fn
    fn = fn.replace('../', '') # Taken from app.py > generated
    with open('{}/{}'.format(fullpath, fn), 'w') as f:
      f.write('Test for {}'.format(fn))
    rv = client.get('/generated/{}'.format(test_name))
    assert rv.status_code == HTTPStatus.OK
  # TODO: Figure out how to delete. The last file is being held hostage in python
  # time.sleep(10)
  # for fn in test_filenames:
  #   fn = fn.replace('..\\', '') # Taken from app.py > generated
  #   if os.path.exists('{}/{}'.format(fullpath, fn)):
  #     os.remove('{}/{}'.format(fullpath, fn))

@pytest.mark.parametrize('zid', base_zone_ids())
def test_set_zone_vol(client, zid):
  """ Try changing a zone's volume """

  # get zone info for max and min volume range
  sb = find(base_config()['zones'], zid)
  assert sb is not None
  min_db = sb['vol_min']
  max_db = sb['vol_max']
  assert min_db <= max_db

  # pick some volumes to test
  def pcnt_2_vol_f(pcnt: float) -> float:
    return pcnt * (amplipi.models.MAX_VOL_F + amplipi.models.MIN_VOL_F) + amplipi.models.MIN_VOL_F
  vol_p = [0.0, 0.25, 0.5, 0.75, 1.0]
  vol_f = [pcnt_2_vol_f(p) for p in vol_p]
  vol_db = [amplipi.utils.vol_float_to_db(f, min_db, max_db) for f in vol_f]

  def patch_zone(json: Dict, expect_failure: bool = False) -> Optional[Dict]:
    rv = client.patch(f'/api/zones/{zid}', json=json)
    if expect_failure:
      assert rv.status_code != HTTPStatus.OK
      return None
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    patched_zone = find(jrv['zones'], zid)
    assert patched_zone is not None
    return patched_zone

  # set zone dB volume, expect it to match the above test volume
  for i, db in enumerate(vol_db):
    z = patch_zone({'vol': db})
    assert z['vol'] == db
    assert z['vol_f'] == vol_f[i]

  # set zone float volume, expect it to match the calculated volume in dB
  for i, fv in enumerate(vol_f):
    z = patch_zone({'vol_f': fv})
    assert z['vol'] == vol_db[i]
    assert z['vol_f'] == fv

  # set zone dB volume and DIFFERENT float volume, expect the dB to override the float
  for i, db in enumerate(vol_db):
    fv = vol_f[-i-1] # grab elements in reverse order
    z = patch_zone({'vol': db, 'vol_f': fv})
    assert z['vol'] == db
    assert z['vol_f'] == vol_f[i]

  # set zone volume to below minimum and above maximum, expect failure
  patch_zone({'vol': amplipi.models.MIN_VOL_DB - 1}, expect_failure=True)
  patch_zone({'vol': amplipi.models.MAX_VOL_DB + 1}, expect_failure=True)
  patch_zone({'vol_f': amplipi.models.MIN_VOL_F - 1}, expect_failure=True)
  patch_zone({'vol_f': amplipi.models.MAX_VOL_F + 1}, expect_failure=True)

  # test that changes to 'vol_min' saturate properly
  z = patch_zone({'vol_f': amplipi.models.MIN_VOL_F, 'vol_min': amplipi.models.MIN_VOL_DB})
  assert z['vol'] == amplipi.models.MIN_VOL_DB
  assert z['vol_f'] == amplipi.models.MIN_VOL_F
  assert z['vol_min'] == amplipi.models.MIN_VOL_DB
  # raise the minimum volume an expect it to saturate
  new_min_vol = 0.25 * (amplipi.models.MAX_VOL_DB - amplipi.models.MIN_VOL_DB) + amplipi.models.MIN_VOL_DB
  z = patch_zone({'vol_min': new_min_vol})
  assert z['vol'] == new_min_vol
  assert z['vol_f'] == amplipi.models.MIN_VOL_F
  assert z['vol_min'] == new_min_vol
  # set volume below min and expect it to saturate
  z = patch_zone({'vol': amplipi.models.MIN_VOL_DB})
  assert z['vol'] == new_min_vol
  assert z['vol_f'] == amplipi.models.MIN_VOL_F
  # set volume to 0% and expect minimum dB
  z = patch_zone({'vol_f': amplipi.models.MIN_VOL_F})
  assert z['vol'] == new_min_vol
  assert z['vol_f'] == amplipi.models.MIN_VOL_F

  # test that changes to 'vol_min' update 'vol' properly
  mid_vol = (amplipi.models.MIN_VOL_DB + amplipi.models.MAX_VOL_DB) / 2
  mid_vol_f = (amplipi.models.MIN_VOL_F + amplipi.models.MAX_VOL_F) / 2
  # reset vol_min to minimum but vol_f to halfway
  z = patch_zone({'vol_f': mid_vol_f, 'vol_min': amplipi.models.MIN_VOL_DB, 'vol_max': amplipi.models.MAX_VOL_DB})
  assert z['vol'] == mid_vol
  assert z['vol_f'] == mid_vol_f
  assert z['vol_min'] == amplipi.models.MIN_VOL_DB
  # set vol_min to halfway, expect vol_f to update to min
  z = patch_zone({'vol_min': mid_vol})
  assert z['vol'] == mid_vol                    # vol is still within valid vol range
  assert z['vol_f'] == amplipi.models.MIN_VOL_F # vol is at the new min so vol_f is 0
  assert z['vol_min'] == mid_vol
  # set vol to the new dB midpoint, expect vol_f to be at half
  new_mid_vol = (mid_vol + amplipi.models.MAX_VOL_DB) / 2
  z = patch_zone({'vol': new_mid_vol})
  assert z['vol'] == new_mid_vol
  assert z['vol_f'] == mid_vol_f
  assert z['vol_min'] == mid_vol

  # test that changes to 'vol_max' saturate properly
  z = patch_zone({'vol_f': amplipi.models.MAX_VOL_F, 'vol_max': amplipi.models.MAX_VOL_DB})
  assert z['vol'] == amplipi.models.MAX_VOL_DB
  assert z['vol_f'] == amplipi.models.MAX_VOL_F
  assert z['vol_max'] == amplipi.models.MAX_VOL_DB
  # raise the maximum volume an expect it to saturate
  new_max_vol = 0.75 * (amplipi.models.MAX_VOL_DB - amplipi.models.MIN_VOL_DB) + amplipi.models.MIN_VOL_DB
  z = patch_zone({'vol_max': new_max_vol})
  assert z['vol'] == new_max_vol
  assert z['vol_f'] == amplipi.models.MAX_VOL_F
  assert z['vol_max'] == new_max_vol
  # set volume above max and expect it to saturate
  z = patch_zone({'vol': amplipi.models.MAX_VOL_DB})
  assert z['vol'] == new_max_vol
  assert z['vol_f'] == amplipi.models.MAX_VOL_F
  # set volume to 100% and expect maximum dB
  z = patch_zone({'vol_f': amplipi.models.MAX_VOL_F})
  assert z['vol'] == new_max_vol
  assert z['vol_f'] == amplipi.models.MAX_VOL_F

  # test that changes to 'vol_max' update 'vol' properly
  # reset vol_max to maximum but vol_f to halfway
  z = patch_zone({'vol_f': mid_vol_f, 'vol_min': amplipi.models.MIN_VOL_DB, 'vol_max': amplipi.models.MAX_VOL_DB})
  assert z['vol'] == mid_vol
  assert z['vol_f'] == mid_vol_f
  assert z['vol_min'] == amplipi.models.MIN_VOL_DB
  assert z['vol_max'] == amplipi.models.MAX_VOL_DB
  # set vol_max to halfway, expect vol_f to update to max
  z = patch_zone({'vol_max': mid_vol})
  assert z['vol'] == mid_vol                    # vol is still within valid vol range
  assert z['vol_f'] == amplipi.models.MAX_VOL_F # vol is at the new max so vol_f is 1
  assert z['vol_max'] == mid_vol
  # set vol to the new dB midpoint, expect vol_f to be at half
  new_mid_vol = (amplipi.models.MIN_VOL_DB + mid_vol) / 2
  z = patch_zone({'vol': new_mid_vol})
  assert z['vol'] == new_mid_vol
  assert z['vol_f'] == mid_vol_f
  assert z['vol_max'] == mid_vol

  # test that 'vol_min' and 'vol_max' can't be set closer than MIN_DB_RANGE
  z = patch_zone({'vol_min': amplipi.models.MIN_VOL_DB, 'vol_max': amplipi.models.MIN_VOL_DB + amplipi.models.MIN_DB_RANGE})
  assert z['vol_min'] == amplipi.models.MIN_VOL_DB
  assert z['vol_max'] == amplipi.models.MIN_VOL_DB + amplipi.models.MIN_DB_RANGE
  patch_zone({'vol_min': amplipi.models.MIN_VOL_DB, 'vol_max': amplipi.models.MIN_VOL_DB}, expect_failure=True)
  patch_zone({'vol_min': amplipi.models.MIN_VOL_DB, 'vol_max': amplipi.models.MIN_VOL_DB + amplipi.models.MIN_DB_RANGE / 2}, expect_failure=True)

@pytest.mark.parametrize('gid', base_group_ids())
def test_set_group_vol(client, gid):
  """ Try changing a groups's volume """

  # pick some volumes to test
  def pcnt_2_vol_f(pcnt: float) -> float:
    return pcnt * (amplipi.models.MAX_VOL_F + amplipi.models.MIN_VOL_F) + amplipi.models.MIN_VOL_F
  vol_p = [0.0, 0.25, 0.5, 0.75, 1.0]
  vol_f = [pcnt_2_vol_f(p) for p in vol_p]
  vol_db = [amplipi.utils.vol_float_to_db(f) for f in vol_f]

  # check if the group gid exists in the config, if not always expect failure
  group = find(client.get('/api').json()['groups'], gid)
  no_groups = group is None
  def patch_group(json: Dict, expect_failure: bool = no_groups) -> Optional[Dict]:
    rv = client.patch(f'/api/groups/{gid}', json=json)
    if expect_failure:
      assert rv.status_code != HTTPStatus.OK
      return None
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    patched_group = find(jrv['groups'], gid)
    assert patched_group is not None
    return patched_group

  # if a group has no zones, volume control won't work as expected
  if no_groups:
    no_zones = False
  else:
    no_zones = len(group['zones']) == 0

  # set group dB volume, expect it to match the above test volume
  for i, db in enumerate(vol_db):
    g = patch_group({'vol_delta': db})
    assert g is None or no_zones or g['vol_delta'] == db
    assert g is None or no_zones or g['vol_f'] == vol_f[i]

  # set group float volume, expect it to match the calculated volume in dB
  for i, fv in enumerate(vol_f):
    g = patch_group({'vol_f': fv})
    assert g is None or no_zones or g['vol_delta'] == vol_db[i]
    assert g is None or no_zones or g['vol_f'] == fv

  # set group dB volume and DIFFERENT float volume, expect the dB to override the float
  for i, db in enumerate(vol_db):
    fv = vol_f[-i-1] # grab elements in reverse order
    g = patch_group({'vol_delta': db, 'vol_f': fv})
    assert g is None or no_zones or g['vol_delta'] == db
    assert g is None or no_zones or g['vol_f'] == vol_f[i]

  # set group volume to below minimum and above maximum, expect failure
  patch_group({'vol_delta': amplipi.models.MIN_VOL_DB - 1}, expect_failure=True)
  patch_group({'vol_delta': amplipi.models.MAX_VOL_DB + 1}, expect_failure=True)
  patch_group({'vol_f': amplipi.models.MIN_VOL_F - 1}, expect_failure=True)
  patch_group({'vol_f': amplipi.models.MAX_VOL_F + 1}, expect_failure=True)

  # set individual zone volumes and check group vol_delta updates properly
  num_zones = 0 if group is None else len(group['zones'])
  zone0_vol = pcnt_2_vol_f(1.0)
  zone1_vol = pcnt_2_vol_f(0.5)
  if num_zones > 0:
    # one zone at full vol, the rest at 0
    patch_group({'vol_f': amplipi.models.MIN_VOL_F})
    zid0 = group['zones'][0]
    rv = client.patch(f'/api/zones/{zid0}', json={'vol_f': zone0_vol})
    assert rv.status_code == HTTPStatus.OK
    jrv = rv.json()
    expected_vol = zone0_vol / len(group['zones'])
    assert find(jrv['groups'], gid)['vol_f'] == expected_vol
    if num_zones > 1:
      # one zone at full vol, one at half, the rest at 0
      zid1 = group['zones'][1]
      rv = client.patch(f'/api/zones/{zid1}', json={'vol_f': pcnt_2_vol_f(0.5)})
      assert rv.status_code == HTTPStatus.OK
      jrv = rv.json()
      # The current group volume method only uses the max and min zone volumes,
      # so if there are more than 2 zones in the group the middle value will be ignored.
      if num_zones == 2:
        expected_vol = (zone0_vol + zone1_vol) / 2
      assert find(jrv['groups'], gid)['vol_f'] == expected_vol
