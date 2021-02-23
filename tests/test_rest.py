import pytest

# json utils
import json
from http import HTTPStatus

# temporary directory for each test config
import tempfile
import os

# copy test config
from copy import deepcopy

# testing context
from context import amplipi

def base_config():
  return deepcopy(amplipi.ctrl.Api._DEFAULT_CONFIG)

def base_config_copy():
  return deepcopy(base_config())

def status_copy(client):
  rv = client.get('/api/')
  jrv = rv.get_json()
  assert jrv != None
  return jrv # jrv was already serialized so it should be a copy

def find(list, id):
  for i in list:
    if i['id'] == id:
      return i
  return None

@pytest.fixture
def app(cfg=base_config_copy()):
  config_dir = tempfile.mkdtemp()
  config_file = os.path.join(config_dir, 'house.json')
  with open(config_file, 'w') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock_ctrl=True, mock_streams=True, config_file=config_file)
  app.testing = True
  return app

@pytest.fixture
def client(app):
  return app.test_client()

def test_base(client):
    """Start with a basic controller and just check if it gives a real response"""
    rv = client.get('/api/')
    jrv = rv.get_json()
    assert jrv != None
    for t in ['sources', 'streams', 'zones', 'groups']:
      assert len(jrv[t]) == len(base_config()[t])


# To reduce the amount of boilerplate we use test parameters.
# Examples: https://docs.pytest.org/en/stable/example/parametrize.html#paramexamples

# TODO: test sources
# TODO: /sources/{sourceId} get-source
# TODO: /sources/{sourceId} patch-source

# TODO: test zones
# TODO: /zones/{zoneId} get-zone
# TODO: /zones/{zoneId} patch-zone

# TODO: test groups
# TODO: /group post-group
# TODO: /groups/{groupId} get-group
# TODO: /groups/{groupId} patch-group
# TODO: /groups/{groupId} delete-group

# test streams
def base_stream_ids():
  """ Return all of the stream IDs belonging to each of the streams in the base config """
  return [ s['id'] for s in base_config()['streams']]

# /stream post-stream
def test_create_pandora(client):
  m_and_k = { 'name': 'Matt and Kim Radio', 'type':'pandora', 'user': 'lincoln@micro-nova.com', 'password': ''}
  rv = client.post('/api/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json()
  assert 'id' in jrv
  assert type(jrv['id']) == int
  for k, v in m_and_k.items():
    assert jrv[k] == v

# /streams/{streamId} get-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_get_stream(client, sid):
  rv = client.get('/api/streams/{}'.format(sid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json()
  s = find(base_config()['streams'], sid)
  assert s != None
  assert s['name'] == jrv['name']

# /streams/{streamId} patch-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_patch_stream_rename(client, sid):
  rv = client.patch('/api/streams/{}'.format(sid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['streams'], sid)
  assert s != None
  assert s['name'] == 'patched-name'

# /streams/{streamId} delete-stream
@pytest.mark.parametrize('sid', base_stream_ids())
def test_delete_stream(client, sid):
  rv = client.delete('/api/streams/{}'.format(sid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was deleted
  s = find(jrv['streams'], sid)
  assert s == None
  # make sure the rest of the streams are still there
  for other_sid in base_stream_ids():
    if other_sid != sid:
      assert find(jrv['streams'], other_sid) != None

# TODO: /streams/{streamId}/{streamCmd} post-stream-command
# TODO: mocked streams do not currently handle state changes from commands
#       these tests will require either a real system with passwords and account info or a better mock

# test presets
def base_preset_ids():
  """ Return all of the preset IDs belonging to each of the presets in the base config """
  return [ s['id'] for s in base_config()['presets']]

# /preset post-preset
def test_create_mute_all_preset(client):
  mute_some = { 'name' : 'Mute some', 'zones' : [ { 'id' : 1, 'mute': True}, { 'id' : 4, 'mute': True} ]}
  rv = client.post('/api/preset', json=mute_some)
  # check that the stream has an id added to it and that all of the fields are still there
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json()
  assert 'id' in jrv
  assert type(jrv['id']) == int
  for k, v in mute_some.items():
    assert jrv[k] == v

# /presets/{presetId} get-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_get_preset(client, pid):
  rv = client.get('/api/presets/{}'.format(pid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json()
  s = find(base_config()['presets'], pid)
  assert s != None
  assert s['name'] == jrv['name']

# /presets/{presetId} patch-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_patch_preset_name(client, pid):
  rv = client.patch('/api/presets/{}'.format(pid), json={'name': 'patched-name'})
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the stream was renamed
  s = find(jrv['presets'], pid)
  assert s != None
  assert s['name'] == 'patched-name'

# /presets/{presetId} delete-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_delete_preset(client, pid):
  rv = client.delete('/api/presets/{}'.format(pid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the preset was deleted
  s = find(jrv['presets'], pid)
  assert s == None
  # make sure the rest of the presets are still there
  for other_pid in base_preset_ids():
    if other_pid != pid:
      assert find(jrv['presets'], other_pid) != None

# /presets/{presetId}/load load-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_load_preset(client, pid):
  last_state = status_copy(client)
  rv = client.post('/api/presets/{}/load'.format(pid))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  # TODO: check that the system state is valid
  # make sure the preset was loaded
  p = find(last_state['presets'], pid)
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
  for z in jrv['zones']:
    expected_mute = last_state['zones']
    if preset_zones_changes:
      pz = find(preset_zones_changes, z['id'])
      if pz and 'mute' in pz:
        expected_mute = pz['mute']
    assert z['mute'] == expected_mute
  # load the saved config and verify that the sources, zones, and groups are the same as initial state (before the preset was loaded)
  LAST_CONFIG_PRESET = 9999
  rv = client.post('/api/presets/{}/load'.format(LAST_CONFIG_PRESET))
  assert rv.status_code == HTTPStatus.OK
  jrv = rv.get_json() # get the system state returned
  for name, mod in jrv.items():
    prev_mod = last_state[name]
    for cfg in mod:
      if cfg['id'] != LAST_CONFIG_PRESET:
        prev_cfg = find(prev_mod, cfg['id'])
        assert cfg == prev_cfg
