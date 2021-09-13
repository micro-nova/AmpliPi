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
import subprocess
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

EXTRA_INPUTS_PLAYBACK = {
  'id': 1002,
  'name': 'Input Playback',
  'type': "fileplayer",
  'url': "alsa://plughw:2,0",
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
    'name': 'amp-0 mute all',
    'state': {'zones': [{'id': zid, 'mute': True} for zid in range(6)]}
  },
  # play music
  {
    'name': 'amp-1 play',
    'state': {
      'sources': [{'id': 0, 'input': f'stream={BEATLES_RADIO["id"]}'}],
      'zones': [{'id': zid, 'mute': False, 'vol': -40} for zid in range(6)]
    }
  },
  # play music
  {
    'name': 'preout-0 play',
    'state': {
      'sources': [{'id': 0, 'input': f'stream={BEATLES_RADIO["id"]}'}],
      'zones': [{'id': zid, 'mute': False, 'vol': -40} for zid in range(6)]
    }
  },
]

PRESETS += [pst_all_zones_to_src(f'preamp-analog-in-{src+1}', src, 'local', -20) for src in range(4)]
PRESETS += [pst_all_zones_to_src('inputs-in', 0, f'stream={EXTRA_INPUTS_PLAYBACK["id"]}', -20)]

def setup(client: Client):
  """ Configure AmpliPi for testing by loading a simple known configuration """
  prev_cfg = client.get_status()
  client.load_config(models.Status(streams=[BEATLES_RADIO, EXTRA_INPUTS_PLAYBACK]))
  for pst in PRESETS:
    client.create_preset(models.Preset(**pst))
  print('waiting for config file to be written')
  sleep(6)
  return prev_cfg

def loop_test(client: Client, test_name: str):
  """ Loop a test over and over """
  status = client.get_status()
  if status is None:
    return
  stages = [pst for pst in status.presets if pst.name.startswith(test_name) and pst.id is not None]
  if len(stages) == 0:
    print(f"test '{test_name}' not found")
    return
  while True:
    for stage in stages:
      if stage.id is not None: # placate the typechecker
        client.load_preset(stage.id)
    sleep(1)
    if test_name == 'led':
      client.reset() # reset amplipi since fw can lock up during unplugging/plugging in led board


def get_analog_tester_client():
  """ Get the second **special** amplipi instance available on MicroNova's network
     We use this to drive an AmpliPi under test's audio inputs (analog1-4, aux, optical) """
  primary = Client('http://aptestanalog.local/api')
  if not primary.available():
    fallback = Client('http://aptestanalog.local:5000/api')
    if fallback.available():
      return fallback
  return primary # when both are not available we return the primary so primary.available() can be checked

def inputs_test(ap1: Client):
  """ Test the controller boards Aux and Optical inputs """
  ap2 = get_analog_tester_client()
  analog_tester_avail = ap2.available()
  if not analog_tester_avail:
    print('No analog tester available, please manually connect audio to the aux and optical inputs')
  status = ap1.get_status()
  if status is None:
    print('failed to get AmpliPi status')
    sys.exit(1)
  preset = [pst for pst in status.presets if pst.name == 'inputs-in'][0]

  if not preset.id:
    print('Preset id not available')
    sys.exit(1)

  print("""
  Alternating between outputting Optical and Aux left and right audio

  - Verify that both Auxillary and Optical In left and right channels are announced out the speaker
  """)

  while True:
    # select the Aux input on this device and play audio through it to all zones
    subprocess.check_call(['amixer', '-c', '2', 'set', "PCM Capture Source", "Line"], stdout=subprocess.DEVNULL)
    # connect all zones to ch3
    ap1.load_preset(preset.id)
    if not analog_tester_avail:
      sleep(5)
    else:
      ap2.announce(models.Announcement(source_id=3, media=f'web/static/audio/aux_in.mp3', vol=-25))

    # select the Optical input on this device and play audio through it to all zones
    subprocess.check_call(['amixer', '-c', '2', 'set', "PCM Capture Source", "IEC958 In"], stdout=subprocess.DEVNULL)
    # connect all zones to ch0
    ap1.load_preset(preset.id)
    if not analog_tester_avail:
      sleep(5)
    else:
      ap2.announce(models.Announcement(source_id=0, media=f'web/static/audio/optical_in.mp3', vol=-25))



def preamp_test(ap1: Client):
  """ Test the preamp board's audio, playing 8 different audio sources then looping """
  ap2 = get_analog_tester_client()
  analog_tester_avail = ap2.available()
  status = ap1.get_status()
  if status is None:
    print('failed to get AmpliPi status')
    sys.exit(1)
  presets = [pst for pst in status.presets if pst.name.startswith('preamp-analog-in-') and pst.id is not None]
  if not analog_tester_avail:
    print('No analog tester available, only able to test digital inputs')
  digital_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/digital{src+1}.mp3', vol=-20) for src in range(4)]
  analog_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/analog{src+1}.mp3', vol=-25) for src in range(4)]
  while True:
    # TODO: add a reset here and attempt to program fw if missing/outdated fw version
    if analog_tester_avail:
      for msg in analog_msgs:
        pst = presets[msg.source_id]
        if pst.id is not None:
          # analog X -> All Zones
          ap1.load_preset(pst.id)
          # play analog announcement on other amplipi (its four source outputs are connected to ap1's analog inputs)
          ap2.announce(msg)
    for msg in digital_msgs:
      ap1.announce(msg)

if __name__ == '__main__':

  tests = ['led', 'amp', 'preout', 'preamp', 'inputs']

  parser = argparse.ArgumentParser('Test audio functionality')
  parser.add_argument('test', help=f'Test to run ({tests})')
  args = parser.parse_args()

  print('configuring amplipi for testing')
  ap = Client('http://localhost/api')
  if not ap.available():
    ap = Client('http://localhost:5000/api')
    if not ap.available():
      print('Unable to connect to local AmpliPi production (port 80) or development (port 5000) servers. Please check if AmpliPi is running and try again.')
      sys.exit(1)
  if args.test not in tests:
    print(f'Test "{args.test}" is not available. Please pick one of {tests}')
    sys.exit(1)

  old_config = setup(ap)
  try:
    print(f"Running test '{args.test}'. Press Ctrl-C to stop.")
    if args.test == 'preamp':
      preamp_test(ap)
    elif args.test == 'inputs':
      inputs_test(ap)
    else:
      loop_test(ap, args.test)
  except KeyboardInterrupt:
    try:
      if ap.available() and ap.load_config(old_config):
        print('\nRestored previous configuration.')
      else:
        print('\nFailed to restore configuration. Left in testing state.')
    except:
      print('\nError restoring configuration. Left in testing state.')
