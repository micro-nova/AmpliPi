"""
# Built-in tests

LED Board
- [ ] All on/scroll

Preout or Amplifier Board
- [ ] 6 Zone 50% volume/mute toggle

Preamp
- [ ] Program preamp and connected expansion board
- [ ] 4x2 sources on zone 1 (also zone 7 on expansion)
- [ ] 4 sources on all zones, toggle volume between 45 and 60%
- [ ] Poll/display 24V ADC + thermistors
"""

from enum import Enum
from time import sleep
from typing import Optional
import requests

from amplipi import models

class Client:
  """ Simple AmpliPi client interface

  TODO: create full fledged client for full AmpliPi API
  """

  def __init__(self):
    self.url = 'http://localhost/api'

  def load_config(self, cfg: models.Status) -> Optional[models.Status]:
    """ Load a configuration """
    resp = requests.post(f'{self.url}/load', json=cfg.dict())
    if resp.ok:
      return models.Status(**resp.json())
    return None

  def load_preset(self, pid: int) -> bool:
    """ Load a preset configuration """
    resp = requests.post(f'{self.url}/presets/{pid}/load')
    return resp.ok

  def create_preset(self, pst: models.Preset) -> bool:
    """ Create a new preset configuration """
    resp = requests.post(f'{self.url}/preset', json=pst.dict())
    return resp.ok

  def get_status(self) -> Optional[models.Status]:
    """ Get the system state """
    resp = requests.get(self.url)
    if resp.ok:
      return models.Status(**resp.json())
    return None

# TODO: use these when we have processes
class Instruction(Enum):
  """ Instructions for sending commands to built-in tests that run as background processes"""
  NEXT = 'next'
  STOP = 'stop'

BEATLES_RADIO = {
  'id': 1001,
  'name': 'Beatles Radio',
  "type": "internetradio",
  "url": "http://www.beatlesradio.com:8000/stream/1/",
  "logo": "http://www.beatlesradio.com/content/images/thumbs/0000587.gif"
}
PRESETS = [
  {
    'name': 'led-0 mute all',
    'state': {'zones': [{'id': zid, 'mute': True} for zid in range(6)]}
  },
  # set volume on zoneX
  {
    'name': 'led-1 enable zone 1',
    'state': {'zones': [{'id': 0, 'mute': False, 'vol': -50}]}
  },
  {
    'name': 'led-2 enable zone 2',
    'state': {'zones': [{'id': 1, 'mute': False, 'vol': -50}]}
  },
  {
    'name': 'led-3 enable zone 3',
    'state': {'zones': [{'id': 2, 'mute': False, 'vol': -50}]}
  },
  {
    'name': 'led-4 enable zone 4',
    'state': {'zones': [{'id': 3, 'mute': False, 'vol': -50}]}
  },
  {
    'name': 'led-5 enable zone 5',
    'state': {'zones': [{'id': 4, 'mute': False, 'vol': -50}]}
  },
  {
    'name': 'led-6 enable zone 6',
    'state': {'zones': [{'id': 5, 'mute': False, 'vol': -50}]}
  },
  # mute all
  {
    'name': 'zones-0 mute all',
    'state': {'zones': [{'id': zid, 'mute': True} for zid in range(6)]}
  },
  # play music
  {
    'name': 'zones-1 play',
    'state': {
      'sources': [{'id': 0, 'input': f'stream={BEATLES_RADIO["id"]}'}],
      'zones': [{'id': zid, 'mute': False, 'vol': -50} for zid in range(6)]
    }
  },
]

def setup(client: Client):
  """ Configure AmpliPi for testing by loading a simple known configuration """
  client.load_config(models.Status(streams=[BEATLES_RADIO]))
  for pst in PRESETS:
    client.create_preset(models.Preset(**pst))

def loop_test(client: Client, test_name: str):
  """ Loop a test over and over """
  status = client.get_status()
  if status is None:
    return
  stages = [pst for pst in status.presets if pst.name.startswith(test_name) and pst.id is not None]
  try:
    while True:
      for stage in stages:
        if stage.id is not None: # placate the typechecker
          client.load_preset(stage.id)
          sleep(1)
      sleep(3)
  except:
    pass


if __name__ == '__main__':
  ap = Client()
  setup(ap)
  loop_test(ap, 'led')
