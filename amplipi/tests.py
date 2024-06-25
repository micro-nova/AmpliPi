"""
# Built-in tests
"""

from time import sleep
from typing import Optional, Sequence
import argparse
import requests
import shlex
import signal
import subprocess
import sys

from amplipi import models


class Client:
  """ Simple AmpliPi client interface

  TODO: create full fledged client for full AmpliPi API
  """
  DEFAULT_TIMEOUT = 4
  ANNOUCE_TIMEOUT = 10  # requests don't return until announcement is finished

  def __init__(self, url='http://localhost/api'):
    self.url = url

  def reset(self) -> bool:
    """ Reset firmware """
    return requests.post(f'{self.url}/reset', timeout=self.DEFAULT_TIMEOUT).ok

  def load_config(self, cfg: models.Status) -> Optional[models.Status]:
    """ Load a configuration """
    resp = requests.post(f'{self.url}/load', json=cfg.dict(), timeout=self.DEFAULT_TIMEOUT)
    if resp.ok:
      return models.Status(**resp.json())
    return None

  def load_preset(self, pid: int) -> bool:
    """ Load a preset configuration """
    resp = requests.post(f'{self.url}/presets/{pid}/load', timeout=self.DEFAULT_TIMEOUT)
    return resp.ok

  def create_preset(self, pst: models.Preset) -> bool:
    """ Create a new preset configuration """
    resp = requests.post(f'{self.url}/preset', json=pst.dict(), timeout=self.DEFAULT_TIMEOUT)
    return resp.ok

  def get_status(self) -> Optional[models.Status]:
    """ Get the system state """
    resp = requests.get(self.url, timeout=self.DEFAULT_TIMEOUT)
    if resp.ok:
      return models.Status(**resp.json())
    return None

  def announce(self, announcement: models.Announcement) -> bool:
    """ Announce something """
    return requests.post(f'{self.url}/announce', json=announcement.dict(), timeout=self.ANNOUCE_TIMEOUT).ok

  def available(self) -> bool:
    """ Check connection """
    try:
      return self.get_status() is not None
    except:
      return False


# TODO: Use amplipi.defaults.RCAs
RCA_INPUTS = {sid: 996 + sid for sid in range(models.MAX_SOURCES)}

BEATLES_RADIO = {
  'id': 1001,
  'name': 'Beatles Radio',
  "type": "internetradio",
  "url": "http://www.beatlesradio.com:8000/stream/1/",
  "logo": "http://www.beatlesradio.com/content/images/thumbs/0000587.gif"
}

AUX_PLAYBACK = {
  'id': 1002,
  'name': 'Aux Playback',
  'type': "fileplayer",
  'url': "alsa://plughw:cmedia8chint,0",
}


def all_zones(exp_unit: bool = False) -> Sequence[int]:
  """Get a list of all available zones based on if this is an @exp_unit"""
  return range(18) if exp_unit else range(12)


def setup(client: Client, exp_unit: bool) -> Optional[models.Status]:
  """ Configure AmpliPi for testing by loading a simple known configuration """
  def pst_all_zones_to_src(name: str, src: int, _input: str, vol=-50):
    """ Create a preset that connects all zones to @src"""
    return {
      'name': name,
      'state': {
        'sources': [{'id': src, 'input': _input}],
        'zones': [{'id': zid, 'source_id': src, 'vol': vol, 'mute': False} for zid in all_zones(exp_unit)],
      }
    }

  status = client.get_status()
  if not status:
    print("Unable to connect to AmpliPi")
    return None

  is_streamer = len(status.zones) == 0
  if is_streamer:
    presets = [
      {
        'name': 'aux-in',
        'state': {
          'sources': [{'id': 0, 'input': f'stream={AUX_PLAYBACK["id"]}'}],
        }
      }
    ]
  else:
    presets = [
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
      presets += [
        {
          'name': f'led-{zid + 1} enable zone {zid + 1}',
          'state': {'zones': [{'id': zid, 'mute': False, 'vol': -50}]}
        }
      ]
    presets += [pst_all_zones_to_src(f'preamp-analog-in-{src+1}', src, f'stream={RCA_INPUTS[src]}', -40)
                for src in range(4)]
    presets += [pst_all_zones_to_src('aux-in', 0, f'stream={AUX_PLAYBACK["id"]}', -40)]

  prev_cfg = client.get_status()
  if is_streamer:
    client.load_config(models.Status(zones=[], streams=[BEATLES_RADIO, AUX_PLAYBACK]))
  else:
    zones = [models.Zone(id=z, name=f'Zone {z + 1}') for z in all_zones(exp_unit)]
    client.load_config(models.Status(zones=zones, streams=[BEATLES_RADIO, AUX_PLAYBACK]))
  for pst in presets:
    client.create_preset(models.Preset(**pst))
  print('waiting for config file to be written')
  sleep(6)
  return prev_cfg


def loop_test(client: Client, test_name: str):
  """ Loop a test over and over """
  status = client.get_status()
  if status is None:
    return
  if len(status.zones) == 0:
    raise Exception('unable to run preamp test on streamer')
  stages = [pst for pst in status.presets if pst.name.startswith(test_name) and pst.id is not None]
  if len(stages) == 0:
    print(f"test '{test_name}' not found")
    return
  if test_name == 'preout':
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
      if stage.id is not None:  # placate the typechecker
        client.load_preset(stage.id)
    sleep(1)
    if test_name == 'led':
      client.reset()  # reset amplipi since fw can lock up during unplugging/plugging in led board


def get_analog_tester_client():
  """ Get the second **special** amplipi instance available on MicroNova's network
     We use this to drive an AmpliPi under test's audio inputs (analog1-4, aux) """
  primary = Client('http://aptestanalog.local/api')
  if not primary.available():
    fallback = Client('http://aptestanalog.local:5000/api')
    if fallback.available():
      return fallback
  return primary  # when both are not available we return the primary so primary.available() can be checked


def aux_test(ap1: Client):
  """ Test the controller board's Aux input """
  ap2 = get_analog_tester_client()
  analog_tester_avail = ap2.available()
  if not analog_tester_avail:
    print('No analog tester available, please manually connect audio to the aux input.')
  status = ap1.get_status()
  if status is None:
    return None

  preset = [pst for pst in status.presets if pst.name == 'aux-in'][0]
  if not preset.id:
    print('Preset aux-in not available')
    sys.exit(1)

  if len(status.zones) > 0:
    print('Connect speakers to any zone.')
  else:
    print('Connect powered speakers with RCA inputs to source 1.')
  print('Verify that both left and right channels are announced.')

  # Connect all zones to ch3, which is duplicated for RCA input 4 and Aux input.
  ap1.load_preset(preset.id)

  # Ensure the Aux Input (Line on the CMedia chip) is selected for capture.
  subprocess.run(shlex.split('amixer -D hw:cmedia8chint set "PCM Capture Source",0 Line'),
                 check=True, stdout=subprocess.DEVNULL)

  # Loop forever, waiting on the user to kill the test.
  while True:
    if analog_tester_avail:
      ap2.announce(models.Announcement(source_id=3, media='web/static/audio/aux_in.mp3'))
    else:
      sleep(5)


def preamp_test(ap1: Client, exp_unit: bool = False):
  """ Test the preamp board's audio, playing 8 different audio sources then looping """
  ap2 = get_analog_tester_client()
  status = ap1.get_status()
  if status is None:
    raise Exception('Failed to get AmpliPi status.')
  if len(status.zones) == 0:
    raise Exception('unable to run preamp test on streamer')
  presets = [pst for pst in status.presets if pst.name.startswith('preamp-analog-in-') and pst.id is not None]
  try_analog = not exp_unit  # the analog tester is not needed for expansion units
  if try_analog and ap2.available():
    print('Test will play the following in a loop:')
    print('- 1L, 1R, 2L ... 4R in a female voice for analog inputs')
    print('- 1L, 1R, 2L ... 4R in a male voice for digital inputs')
    print('Verify that each side and all 8 sources are played out of each of the 6 zones')
  else:
    if try_analog:
      print('No analog tester found at aptestanalog.local, only able to test digital inputs\n')
    print('Test will play 1L, 1R, 2L ... 4R')
    print('- Verify that each side and all 4 digital sources are played out of each of the 6 zones')
  digital_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/digital{src+1}.mp3', vol=-30)
                  for src in range(4)]
  analog_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/analog{src+1}.mp3') for src in range(4)]
  while True:
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


def streamer_test(ap1: Client):
  """ Test the streamer board's audio, playing 4 different audio sources then looping """
  status = ap1.get_status()
  if status is None:
    print('Failed to get AmpliPi status.')
    sys.exit(1)
  if len(status.zones) != 0:
    raise Exception("""Unit has zones. It may not have detected it was a streamer unit.
      Do a factory reset and try testing again.""")
  print('Test will play Digital 1 Left... Digital 4 Right')
  print('- Verify that each side of all 4 sources are played out the corresponding RCA outputs')
  print('  ex. Digital 1 Left should be played out on the RCA output 1')
  print('  NOTE: Requires a powered speaker with an RCA cable input')
  digital_msgs = [models.Announcement(source_id=src, media=f'web/static/audio/digital{src+1}.mp3', vol=-30)
                  for src in range(4)]
  while True:
    for msg in digital_msgs:
      ap1.announce(msg)


class ExitHandler:
  """Handle program exit from a signal."""
  _handled: bool = False
  _ap: Client

  def __init__(self, amplipi_client: Client):
    self._ap = amplipi_client

  def exit_handler(self, _, _1):
    """ Attempt to gracefully shutdown """
    if not self._handled:
      self._handled = True  # Prevent multiple signals from calling this repeatedly.
      print('\nClosing (attempting to restore config)')
      try:
        # HACK: kill weird lingering vlc process
        subprocess.run(['killall', 'vlc'], check=True, stderr=subprocess.DEVNULL)
      except subprocess.CalledProcessError:
        pass

      try:
        if self._ap.available() and self._ap.load_config(old_config):
          print('Restored previous configuration.')
        else:
          print('Failed to restore configuration. Left in testing state.')
      except:
        print('Error restoring configuration. Left in testing state.')
      sys.exit(0)


if __name__ == '__main__':

  tests = ['led', 'amp', 'preout', 'preamp', 'aux', 'streamer']

  parser = argparse.ArgumentParser('Test audio functionality')
  parser.add_argument('test', help=f'Test to run ({tests})')
  parser.add_argument('--expansion', action='store_true',
                      help='Test expansion units: disable analog input tests and set 18 zones')
  args = parser.parse_args()

  print('Configuring AmpliPi for testing.')
  ap = Client('http://localhost/api')
  if not ap.available():
    ap = Client('http://localhost:5000/api')
    if not ap.available():
      print('Unable to connect to local AmpliPi production (port 80) or development (port 5000) servers.')
      print('Please check if AmpliPi is running and try again.')
      sys.exit(1)
  if args.test not in tests:
    print(f'Test "{args.test}" is not available. Please pick one of {tests}')
    sys.exit(1)

  eh = ExitHandler(ap)
  signal.signal(signal.SIGINT, eh.exit_handler)
  signal.signal(signal.SIGTERM, eh.exit_handler)
  signal.signal(signal.SIGHUP, eh.exit_handler)

  old_config = setup(ap, exp_unit=args.expansion)
  if not old_config:
    print('Failed to configure AmpliPi for testing, exiting.')
    sys.exit(1)
  try:
    print(f"Running test '{args.test}'. Press Ctrl-C to stop.")
    if args.test == 'preamp':
      preamp_test(ap, exp_unit=args.expansion)
    elif args.test == 'aux':
      aux_test(ap)
    elif args.test == 'streamer':
      streamer_test(ap)
    else:
      loop_test(ap, args.test)
  except KeyboardInterrupt:
    pass
  except Exception as e:
    print(f'Failed to test {args.test}: {e}')
  try:
    if ap.available() and ap.load_config(old_config):
      print('\nRestored previous configuration.')
    else:
      print('\nFailed to restore configuration. Left in testing state.')
  except:
    print('\nError restoring configuration. Left in testing state.')
