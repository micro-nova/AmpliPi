"""
# Built-in tests

LED Board
- [x] All on/scroll

Preout or Amplifier Board
- [x] 6 Zone 50% volume/mute toggle

Preamp
- [ ] Program preamp and connected expansion board
- [x] 4x2 sources on zone 1 (also zone 7 on expansion)
- [ ] 4 sources on all zones, toggle volume between 45 and 60%
- [ ] Poll/display 24V ADC + thermistors
"""

from enum import Enum
from time import sleep
from typing import Optional
import sys
import argparse
import requests

from amplipi import models

class Client:
  """ Simple AmpliPi client interface

  TODO: create full fledged client for full AmpliPi API
  """

  def __init__(self, url='http://localhost/api'):
    self.url = url

  def reset(self) -> bool:
    """ Rest HW """
    return requests.post(f'{self.url}/reset').ok

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

  def announce(self, announcement: models.Announcement) -> bool:
    """ Announce something """
    return requests.post(f'{self.url}/announce', json=announcement.dict()).ok

  def available(self) -> bool:
    """ Check connection """
    try:
      return self.get_status() is not None
    except:
      return False

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

def pst_all_zones_to_src(name: str, src: int, input: str, vol=-50):
  return {
    'name': name,
    'state': {
      'sources': [{'id': src, 'input': input}],
      'zones': [{'id': zid, 'source_id': src, 'vol': vol, 'mute': False} for zid in range(6)],
    }
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

PRESETS += [pst_all_zones_to_src(f'preamp-analog-in-{src+1}', src, 'local', -35) for src in range(4)]

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
  if len(stages) == 0:
    print(f"test '{test_name}' not found")
    return
  print(f"Running test '{test_name}'. Press Ctrl-C to stop.")
  try:
    while True:
      for stage in stages:
        if stage.id is not None: # placate the typechecker
          client.load_preset(stage.id)
      sleep(1)
      if test_name == 'led':
        client.reset() # reset amplipi since fw can lock up during unplugging/plugging in led board
  except:
    pass


if __name__ == '__main__':

  parser = argparse.ArgumentParser('Test audio functionality')
  parser.add_argument('test', help='Test to run (led,zones,preamp)')
  args = parser.parse_args()

  print('configuring amplipi for testing (TODO: unconfigure it when done!)')
  ap = Client('http://localhost/api')
  if not ap.available():
    ap = Client('http://localhost:5000/api')
    if not ap.available():
      print('Unable to connect to local AmpliPi production (port 80) or development (port 5000) servers. Please check if AmpliPi is running and try again.')
      sys.exit(1)
  apt = Client('http://aptestanalog.local/api')

  setup(ap)
  if args.test == 'preamp':
    analog_tester_avail = apt.available()
    status = ap.get_status()
    if status is None:
      print('failed to get AmpliPi status')
      sys.exit(1)
    presets = [pst for pst in status.presets if pst.name.startswith('preamp-analog-in-') and pst.id is not None]
    if not analog_tester_avail:
      print('No analog tester available, only able to test digital inputs')
    announcements = [models.Announcement(source_id=src, media=f'web/static/audio/{t}{src+1}.{side}.wav', vol=-25) for t in ['analog', 'digital'] for src in range(4) for side in ['left', 'right']]
    while True:
      for a in announcements:
        if 'analog' in a.media:
          if analog_tester_avail:
            pst = presets[a.src_id]
            if pst.id is not None:
              ap.load_preset(pst.id)
              apt.announce(a)
        else:
          ap.announce(a)
  else:
    loop_test(ap, args.test)
