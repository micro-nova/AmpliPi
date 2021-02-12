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
def test_create_mute_all(client):
  assert False

# /presets/{presetId} get-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_get_preset(client, pid):
  assert False

# /presets/{presetId} patch-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_patch_preset(client, pid):
  assert False

# /presets/{presetId} delete-preset
@pytest.mark.parametrize('pid', base_preset_ids())
def test_delete_preset(client, pid):
  assert False
