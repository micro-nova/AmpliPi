#!/usr/bin/python3

import argparse
from copy import deepcopy
import deepdiff

# use the internal ethaudio library
from context import ethaudio

# TODO: port this to a standard python test framework such as unittest
# TODO: encode expected change after each one of these commands to form a tuple similar to (cmd, {field1: value_expected, field2:value_expected})
test_cmds = [
{
  "command" : "set_power",
  "audio_power" : True,
  "usb_power" : True
},
{
  "command" : "set_source",
  "id" : 1,
  "name" : "cd player",
  "digital": False
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "whole house",
  "source_id" : 2,
  "mute" : False,
  "stby" : False,
  "vol" : -9,
  "disabled" : False
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "whole house",
  "source_id" : 2,
  "mute" : False,
  "stby" : False,
  "vol" : -9,
  "disabled" : False
},
#{
#    "command":"set_group",
#    "id":any vaild group,
#    "name":"new name" # sets the friendly name for the group, ie "upstairs" or "back yard"
#    "source_id": 0 | 1 | 2 | 3 # change all zones in group to different source
#    "zones": [0,1,2...] # specify new array of zones that make up the group
#    "mute": False | True # mutes all zones in group
#    "stby": False | True # sets all zone in group to standby
#    "vol_delta": 0 to 79 # CHANGES the volume of each zone in the group by this much. For each zone, will saturate if out of range
#},
#{
#    "command":"create_group"
#    "name":"new group name"
#    "zones": [0,1,2...] # specify new array of zones that make up the group
#},
#{
#    "command":"delete_group"
#    "id":"new group name"
#}

# Rewind state back to initialization
{
  "command" : "set_power",
  "audio_power" : False,
  "usb_power" : True
},
{
  "command" : "set_source",
  "id" : 1,
  "name" : "Pandora",
  "digital": True
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "Sleep Zone",
  "source_id" : 3,
  "mute" : False,
  "stby" : False,
  "vol" : -40,
  "disabled" : False
},
]

def pretty_field(field):
  """ pretty print deepdiff's field name """
  return str(field).replace("root['", "").replace("']","").replace("['", ".")

def show_change():
  """ print the difference between status when this was last called

    we use this for debugging
  """
  global last_status, eth_audio_api
  diff = deepdiff.DeepDiff(last_status, eth_audio_api.status, ignore_order=True)
  if any(k in diff for k in ('values_changed', 'dictionary_item_added', 'dictionary_item_removed')):
    print('changes:')
    if 'values_changed' in diff:
      for field, change in diff['values_changed'].items():
        print('  {} {} -> {}'.format(pretty_field(field), change['old_value'], change['new_value']))
    if 'dictionary_item_added' in diff:
      for field in diff['dictionary_item_added']:
        print('added {}'.format(pretty_field(field)))
    if 'dictionary_item_removed' in diff:
      for field in diff['dictionary_item_removed']:
        print('added {}'.format(pretty_field(field)))
  else:
    print('no change!')
  last_status = deepcopy(eth_audio_api.status)

def test(result):
  if result == None:
    show_change()
  else:
    print(result)

def test_http(result):
  if result == None:
    print("None?")
  elif 'error' in result:
    print(result['error'])
  else:
    show_change()

def run_all_tests(api):
  global last_status, eth_audio_api

  eth_audio_api = api

  last_status = deepcopy(eth_audio_api.get_state())

  # Test emulated commands
  # TODO: add verification to these tests
  print('intial state:')
  print(eth_audio_api.get_state())
  print('\ntesting commands:')
  test(eth_audio_api.set_power(audio_on=False, usb_on=True))
  test(eth_audio_api.set_source(0, 'Spotify', True))
  test(eth_audio_api.set_source(1, 'Pandora', True))
  test(eth_audio_api.set_source(2, 'TV', False))
  test(eth_audio_api.set_source(3, 'PC', False))
  test(eth_audio_api.set_zone(0, 'Party Zone', 1, False, False, 0, False))
  test(eth_audio_api.set_zone(1, 'Drone Zone', 2, False, False, -20, False))
  test(eth_audio_api.set_zone(2, 'Sleep Zone', 3, True, False, -40, False))
  test(eth_audio_api.set_zone(3, "Standby Zone", 4, False, True, -50, False))
  test(eth_audio_api.set_zone(4, "Disabled Zone", 1, False, False, 0, True))

  # Test string/json based command handler
  print('\ntesting json:')
  for cmd in test_cmds:
    test(eth_audio_api.parse_cmd(cmd))

  print('\ntesting json over http:')

  # Start HTTP server (behind the scenes it runs in new thread)
  srv = ethaudio.Server(eth_audio_api)

  # Send HTTP requests and print output
  client = ethaudio.Client()
  for cmd in test_cmds:
    test_http(client.send_cmd(cmd))

if __name__ == "__main__":
  run_all_tests(ethaudio.Api(ethaudio.api.MockRt()))
