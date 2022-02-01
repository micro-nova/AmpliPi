"""
# Built-in tests
"""

from time import sleep
from typing import Optional, Sequence
import sys
import subprocess
import signal
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
    """ Reset firmware """
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
  'url': "alsa://plughw:cmedia8chint,0",
}

def all_zones(exp_unit: bool = False) -> Sequence[int]:
  return range(18) if exp_unit else range(12)

def setup(client: Client, exp_unit: bool):
  def pst_all_zones_to_src(name: str, src: int, _input: str, vol=-50):
    """ Create a preset that connects all zones to @src"""
    return {
      'name': name,
      'state': {
        'sources': [{'id': src, 'input': _input}],
        'zones': [{'id': zid, 'source_id': src, 'vol': vol, 'mute': False} for zid in all_zones(exp_unit)],
      }
    }

  PRESETS = [
    {
      'name': 'led-0 mute all',
      'state': {'zones': [{'id': zid, 'mute': True} for zid in all_zones(exp_unit)]}
    },
    # mute all
    {
      'name': 'amp-0 mute all',
      'state': {'zones': [{'id': zid, 'mute': True} for zid in all_zones(exp_unit)]}
    },
    # play music
    {
      'name': 'amp-1 play',
      'state': {
        'sources': [{'id': 0, 'input': f'stream={BEATLES_RADIO["id"]}'}],
        'zones': [{'id': zid, 'mute': False, 'vol': -40} for zid in all_zones(exp_unit)]
      }
    },
    # play music
    {
      'name': 'preout-0 play',
      'state': {
        'sources': [{'id': 0, 'input': f'stream={BEATLES_RADIO["id"]}'}],
        'zones': [{'id': zid, 'mute': False, 'vol': -40} for zid in all_zones(exp_unit)]
      }
    },
  ]

  # set volume on zoneX
  for zid in all_zones(exp_unit):
    PRESETS += [
      {
        'name': f'led-{zid + 1} enable zone {zid + 1}',
        'state': {'zones': [{'id': zid, 'mute': False, 'vol': -50}]}
      }
    ]
  PRESETS += [pst_all_zones_to_src(f'preamp-analog-in-{src+1}', src, 'local', -40) for src in range(4)]
  PRESETS += [pst_all_zones_to_src('inputs-in', 0, f'stream={EXTRA_INPUTS_PLAYBACK["id"]}', -40)]

  """ Configure AmpliPi for testing by loading a simple known configuration """
  prev_cfg = client.get_status()
  client.load_config(models.Status(zones=[models.Zone(id=z, name=f'Zone {z + 1}') for z in all_zones(exp_unit)], streams=[BEATLES_RADIO, EXTRA_INPUTS_PLAYBACK]))
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
  elif test_name == 'preout':
    print("""Use a pair of headphones to connect to each of the 6 channels.

    - Verify both left and right sides are playing music for each channel
    """)
  elif test_name == 'amp':
    print("""Connect the test speakers to each of the 6 zones

    - Verify audio plays out each side, then pauses, then starts playing again
    """)
  elif test_name == 'led':
    print("""Look at the front LEDs.

    - Verify the sequence is the following:
      1. The first led should blink red then green.
      2. The blue zone leds will light up in a progress bar-like sequence (they should be the same brightness)
      3. Repeat
    """)
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

  def set_pcm(src):
    for card in range(4):
      try:
        subprocess.check_call(['amixer', '-c', str(card), 'set', "'PCM Capture Source',0", src],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        break
      except:
        pass

  while True:
    # select the Aux input on this device and play audio through it to all zones
    set_pcm("Line")
    # connect all zones to ch3
    ap1.load_preset(preset.id)
    if not analog_tester_avail:
      sleep(5)
    else:
      ap2.announce(models.Announcement(source_id=3, media=f'web/static/audio/aux_in.mp3'))

    # select the Optical input on this device and play audio through it to all zones
    set_pcm("IEC958 In")
    # connect all zones to ch0
    ap1.load_preset(preset.id)
    if not analog_tester_avail:
      sleep(5)
    else:
      ap2.announce(models.Announcement(source_id=0, media=f'web/static/audio/optical_in.mp3'))

def preamp_test(ap1: Client, exp_unit: bool = False):
  """ Test the preamp board's audio, playing 8 different audio sources then looping """
  ap2 = get_analog_tester_client()
  status = ap1.get_status()
  if status is None:
    print('failed to get AmpliPi status')
    sys.exit(1)
  presets = [pst for pst in status.presets if pst.name.startswith('preamp-analog-in-') and pst.id is not None]
  try_analog = not exp_unit # the analog tester is not needed for expansion units
  if try_analog and ap2.available():
    print('Test will play Analog 1 Left, Analog 1 Right...Analog 4 Right, Digital 1 Left... Digital 4 Right')
    print('- Verify that each side and all 8 sources are played out of each of the 6 zones')
  else:
    if try_analog:
      print('No analog tester found at aptestanalog.local, only able to test digital inputs\n')
    print('Test will play Digital 1 Left... Digital 4 Right')
    print('- Verify that each side and all 4 sources are played out of each of the 6 zones')
  digital_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/digital{src+1}.mp3', vol=-30) for src in range(4)]
  analog_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/analog{src+1}.mp3') for src in range(4)]
  while True:
    # TODO: verify fw version
    if try_analog and ap2.available():
      for msg in analog_msgs:
        pst = presets[msg.source_id]
        if pst.id is not None:
          # analog X -> All Zones
          ap1.load_preset(pst.id)
          # play analog announcement on other amplipi (its four source outputs are connected to ap1's analog inputs)
          ap2.announce(msg)
    for msg in digital_msgs:
      ap1.announce(msg)

def exit_handler(_, _1):
  """ Attempt to gracefully shutdown """
  print('Closing (attempting to restore config)')
  try:
    subprocess.run(['killall', 'vlc'], check=False) # HACK: kill weird lingering vlc process
    if ap.available() and ap.load_config(old_config):
      print('\nRestored previous configuration.')
    else:
      print('\nFailed to restore configuration. Left in testing state.')
  except:
    print('\nError restoring configuration. Left in testing state.')
  sys.exit(0)

if __name__ == '__main__':

  tests = ['led', 'amp', 'preout', 'preamp', 'inputs']

  parser = argparse.ArgumentParser('Test audio functionality')
  parser.add_argument('test', help=f'Test to run ({tests})')
  parser.add_argument('--expansion', action='store_true',
                      help='Test expansion units: disable analog input tests and set 18 zones')
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

  signal.signal(signal.SIGINT, exit_handler)
  signal.signal(signal.SIGTERM, exit_handler)
  signal.signal(signal.SIGHUP, exit_handler)

  old_config = setup(ap, exp_unit=args.expansion)
  try:
    print(f"Running test '{args.test}'. Press Ctrl-C to stop.")
    if args.test == 'preamp':
      preamp_test(ap, exp_unit=args.expansion)
    elif args.test == 'inputs':
      inputs_test(ap)
    else:
      loop_test(ap, args.test)
  except KeyboardInterrupt: # TODO: handle other signals kill and sighup
    try:
      if ap.available() and ap.load_config(old_config):
        print('\nRestored previous configuration.')
      else:
        print('\nFailed to restore configuration. Left in testing state.')
    except:
      print('\nError restoring configuration. Left in testing state.')
