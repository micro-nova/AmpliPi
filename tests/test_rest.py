import pytest

# json utils
import json

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

@pytest.fixture
def client(cfg=base_config_copy()):
  config_dir = tempfile.mkdtemp()
  config_file = os.path.join(config_dir, 'house.json')
  with open(config_file, 'w') as cfg_file:
    cfg_file.write(json.dumps(cfg))
  app = amplipi.app.create_app(mock=True, config_file=config_file)
  app.testing = True
  return app.test_client()

def test_base(client):
    """Start with a basic controller and just check if it gives a real response"""
    rv = client.get('/api/')
    jrv = rv.get_json()
    assert jrv != None
    for t in ['sources', 'streams', 'zones', 'groups']:
      assert len(jrv[t]) == len(base_config()[t])

# TODO: test sources
# TODO: test zones
# TODO: test groups

# TODO: test streams
# /stream post-stream
def test_create_pandora(client):
  m_and_k = { 'name': 'Matt and Kim Radio', 'user': 'lincoln@micro-nova.com', 'password': ''}
  rv = client.post('/stream', json=m_and_k)
  # check that the stream has an id added to it and that all of the fields are still there
  jrv = rv.get_json()
  assert 'id' in jrv
  assert type(jrv['id']) == int
  for k, v in m_and_k.items():
    assert jrv[k] == v

# /streams/{streamId} get-stream
# /streams/{streamId} patch-stream
# /streams/{streamId} delete-stream
# /streams/{streamId}/{streamCmd} post-stream-command
