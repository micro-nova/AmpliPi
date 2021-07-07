""" Test the amplipi rest API """

from typing import List

# json utils
import json
from http import HTTPStatus

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

def base_config():
  """ Default Amplipi configuration """
  return amplipi.ctrl.Api.DEFAULT_CONFIG

def base_config_copy():
  """ Modify-able Amplipi configuration """
  return deepcopy(base_config())

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

@pytest.fixture(params=[base_config_copy(), base_config_no_presets(), base_config_no_groups()])
def client(request):
  """ AmpliPi instance with mocked ctrl and streams """
  cfg = request.param
  config_dir = tempfile.mkdtemp()
  config_file = os.path.join(config_dir, 'house.json')
  with open(config_file, 'w') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock_ctrl=True, mock_streams=True, config_file=config_file, delay_saves=False)
  c = TestClient(app)
  c.original_config = deepcopy(cfg) # add the loaded config so we can remember what was loaded
  return c

@pytest.fixture(params=[base_config_copy(), base_config_no_presets(), base_config_no_groups()])
def clientnm(request):# Non-mock systems should use this client - mock_ctrl and mock_streams are False here
  """ AmpliPi instance connected to a real AmpliPi controller """
  cfg = request.param
  config_dir = tempfile.mkdtemp()
  config_file = os.path.join(config_dir, 'house.json')
  with open(config_file, 'w') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock_ctrl=False, mock_streams=False, config_file=config_file, delay_saves=False)
  c = TestClient(app)
  c.original_config = deepcopy(cfg) # add the loaded config so we can remember what was loaded
  return c

# TODO: the web view test should be added to its own testfile once we add more functionality to the site
@pytest.mark.parametrize('path', ['' , '/'] + [ '/{}'.format(i) for i in range(4) ])
def test_view(client: TestClient, path):
  """ Test the web app's main view """
  rv = client.get(path)
  assert rv.status_code == HTTPStatus.OK

def test_view_changes(client: TestClient):
  """ Change a zone's name and check if it gets updated on the webapp """
  # check that the webapp works
  rv = client.get('/')
  assert rv.status_code == HTTPStatus.OK
  assert 'patched-name' not in rv.text

  # change the zones name
  rv = client.patch('/api/zones/0', json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  z = find(jrv['zones'], 0)
  assert z is not None
  assert z['name'] == 'patched-name'
  # check it got changed
  rv = client.get('/')
  assert rv.status_code == HTTPStatus.OK
  assert 'patched-name' in rv.text, 'zone name was not updated on the webapp'

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

def test_open_api_yamlfile(client):
    """ Check if the openapi yaml doc is available """
    rv = client.get('/openapi.yaml')
    assert rv.status_code == HTTPStatus.OK
# To reduce the amount of boilerplate we use test parameters.
# Examples: https://docs.pytest.org/en/stable/example/parametrize.html#paramexamples

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

@pytest.mark.parametrize('sid', base_source_ids())
def test_patch_source(client, sid):
  """ Try changing a source's name """
  rv = client.patch('/api/sources/{}'.format(sid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['sources'], sid)
  assert s is not None
  assert s['name'] == 'patched-name'

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
def test_patch_zone(client, zid):
  """ Try changing a zones name """
  rv = client.patch('/api/zones/{}'.format(zid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(jrv['zones'], zid)
  assert s is not None
  assert s['name'] == 'patched-name'

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
  return [ s['id'] for s in base_config()['streams']]

# /stream post-stream
def test_create_pandora(client):
  """ Try creating a Pandora stream """
  m_and_k = { 'name': 'Matt and Kim Radio', 'type':'pandora', 'user': 'lincoln@micro-nova.com', 'password': ''}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  assert 'id' in jrv
  assert isinstance(jrv['id'], int)
  for k, v in m_and_k.items():
    assert jrv[k] == v

# /streams/{streamId} get-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_get_stream(client, sid):
  """ Try getting a default stream """
  rv = client.get('/api/streams/{}'.format(sid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json()
  s = find(base_config()['streams'], sid)
  assert s is not None
  assert s['name'] == jrv['name']

# /streams/{streamId} patch-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_patch_stream_rename(client, sid):
  """ Try renaming a stream """
  rv = client.patch('/api/streams/{}'.format(sid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s is not None
  assert s['name'] == 'patched-name'

# /streams/{streamId} delete-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_delete_stream(client, sid):
  """ Try deleting a stream  """
  rv = client.delete('/api/streams/{}'.format(sid))
  assert rv.status_code == HTTPStatus.OK
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
  rv = client.patch('/api/sources/0', json={'input': f'stream={sid}'})
  assert rv.status_code == HTTPStatus.OK
  rv = client.delete(f'/api/streams/{sid}')
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
    for cfg in mod:
      if cfg['id'] != LAST_CONFIG_PRESET:
        prev_cfg = find(prev_mod, cfg['id'])
        for ignored_field in ignore:
          if ignored_field in prev_cfg:
            prev_cfg.pop(ignored_field)
          if ignored_field in cfg:
            cfg.pop(ignored_field)
        assert cfg == prev_cfg

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
