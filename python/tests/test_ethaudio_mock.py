#!/usr/bin/python3

import argparse
from copy import deepcopy
import deepdiff

# use the internal ethaudio library
from context import ethaudio

# TODO: port this to a standard python test framework such as unittest
# TODO: encode expected change after each one of these commands to form a tuple similar to (cmd, {field1: value_expected, field2:value_expected})
test_sequence = [
(
  "Enable Audio",
  {
    "command" : "set_power",
    "audio_power" : True,
    "usb_power" : True
  },
  None,
  {
    "power.audio_power" : True
  }
),
(
  "Add CD Player (in place of Pandora)",
  {
    "command" : "set_source",
    "id" : 1,
    "name" : "cd player",
    "digital": False
  },
  None,
  {
    "sources[1].digital" : False,
    "sources[1].name" : "cd player"
  }
),
(
  "Add Whole House zone",
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
  None,
  {
    'zones[2].name' : 'whole house',
    'zones[2].vol' : -9,
    'zones[2].mute' : False,
    'zones[2].source_id' : 2
  }
),
(
  "Try adding the whole house zone again",
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
  None,
  {
  }
),
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
# TODO: test zone following group changes
# Rewind state back to initialization
(
  "Disbale Audio",
  {
    "command" : "set_power",
    "audio_power" : False,
    "usb_power" : True
  },
  None,
  {
    "power.audio_power" : False
  },
),
(
  "Change source back to Pandora",
  {
    "command" : "set_source",
    "id" : 1,
    "name" : "Pandora",
    "digital": True
  },
  None,
  {
    "sources[1].digital" : True,
    "sources[1].name" : "Pandora"
  }
),
(
  "Change zone 2 back to Sleep Zone",
  {
    "command" : "set_zone",
    "id" : 2,
    "name" : "Sleep Zone",
    "source_id" : 3,
    "mute" : True,
    "stby" : False,
    "vol" : -40,
    "disabled" : False
  },
  None,
  {
    'zones[2].name' : 'Sleep Zone',
    'zones[2].vol' : -40,
    'zones[2].mute' : True,
    'zones[2].source_id' : 3
  }
)
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

def get_state_changes():
  """ get difference between status when this was last called

    Returns:
      changees: dict of modified fields
      added: list of added fields
      removed: list of removed fields
  """
  global last_status, eth_audio_api
  diff = deepdiff.DeepDiff(last_status, eth_audio_api.status, ignore_order=True)
  changes = ({}, [], [])
  if 'values_changed' in diff:
    for field, change in diff['values_changed'].items():
      changes[0][pretty_field(field)] = change['new_value']
  if 'dictionary_item_added' in diff:
    for field in diff['dictionary_item_added']:
      changes[1].append(format(pretty_field(field)))
  if 'dictionary_item_removed' in diff:
    for field in diff['dictionary_item_removed']:
      changes[2].append(format(pretty_field(field)))
  last_status = deepcopy(eth_audio_api.status)
  return changes

def test(name, result, expected_result, expected_changes):
  global test_num
  print('Test {}: {}'.format(test_num, name))
  test_num += 1
  success = True # optistic, any single failure will set to False
  # check state changes
  changes, added, removed = get_state_changes()
  if changes != expected_changes:
    success = False
    print('  Changes do not match:')
    print('    changes: ' + str(changes))
    print('    expected_changes: ' + str(expected_changes))
  if len(added) != 0: success = False; print('  Unexpected fields addded: {}'.format(added))
  if len(added) != 0: success = False; print('  Unexpected fields removed: {}'.format(removed))
  if result != expected_result: success = False; print('  Expected Result = {}, Actual Result = {}'.format(expected_result, result))
  print('  SUCCESS') if success else print(' FAILURE')

def test_http(name, result, expected_result, expected_changes):
  if result == None:
    global test_num
    print('Test {}: {}'.format(test_num, name))
    test_num += 1
    print("  Error: JSON response expected over http")
    print("  FAILURE")
  else:
    if 'error' in result:
      test(name, result, expected_result, expected_changes)
    else:
      test(name, None, expected_result, expected_changes)

def run_all_tests(api):
  global last_status, eth_audio_api, test_num
  test_num = 0

  eth_audio_api = api

  last_status = deepcopy(eth_audio_api.get_state())

  # Test emulated commands
  print('intial state:')
  print(eth_audio_api.get_state())
  print('\ntesting commands:')
  test('Enable USB', eth_audio_api.set_power(audio_on=False, usb_on=True), None, {'power.usb_power' : True})
  test('Configure source 0 (digital)', eth_audio_api.set_source(0, 'Spotify', True), None, {'sources[0].name' : 'Spotify', 'sources[0].digital' : True})
  test('Configure source 1 (digital)',eth_audio_api.set_source(1, 'Pandora', True), None, {'sources[1].name' : 'Pandora', 'sources[1].digital' : True})
  test('Configure source 2 (Analog)', eth_audio_api.set_source(2, 'TV', False), None, {'sources[2].name' : 'TV'})
  test('Configure source 3 (Analog)', eth_audio_api.set_source(3, 'PC', False), None, {'sources[3].name' : 'PC'})
  test('Configure zone 0, Party Zone', eth_audio_api.set_zone(0, 'Party Zone', 1, False, False, 0, False), None, {'zones[0].name' : 'Party Zone', 'zones[0].source_id' : 1})
  test('Configure zone 1, Drone Zone', eth_audio_api.set_zone(1, 'Drone Zone', 2, False, False, -20, False), None, {'zones[1].name' : 'Drone Zone', 'zones[1].source_id' : 2, 'zones[1].vol': -20})
  test('Configure zone 2, Sleep Zone', eth_audio_api.set_zone(2, 'Sleep Zone', 3, True, False, -40, False), None, {'zones[2].name' : 'Sleep Zone', 'zones[2].source_id' : 3, 'zones[2].vol': -40, 'zones[2].mute' : True})
  test('Configure zone 3, Standby Zone', eth_audio_api.set_zone(3, 'Standby Zone', 4, False, True, -50, False), None, {'zones[3].name' : 'Standby Zone', 'zones[3].source_id' : 4, 'zones[3].stby' : True, 'zones[3].vol' : -50})
  test('Configure zone 4, Disabled Zone', eth_audio_api.set_zone(4, 'Disabled Zone', 1, False, False, 0, True), None, {'zones[4].name' : 'Disabled Zone', 'zones[4].source_id' : 1, 'zones[4].disabled' : True})

  # Test string/json based command handler
  print('\ntesting json:')
  for name, cmd, expected_result, expected_changes  in test_sequence:
    test(name, eth_audio_api.parse_cmd(cmd), expected_result, expected_changes)

  print('\ntesting json over http:')

  # Start HTTP server (behind the scenes it runs in new thread)
  srv = ethaudio.Server(eth_audio_api)

  # Send HTTP requests and print output
  client = ethaudio.Client()
  for name, cmd, expected_result, expected_changes in test_sequence:
    test_http(name, client.send_cmd(cmd), expected_result, expected_changes)

if __name__ == "__main__":
  run_all_tests(ethaudio.Api(ethaudio.api.MockRt()))
