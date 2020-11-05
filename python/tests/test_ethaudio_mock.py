#!/usr/bin/python3
# this file is expected to be run using pytest, ie. pytest python/tests/test_ethaudio_mock.py

import argparse
from copy import deepcopy
import deepdiff

# use the internal ethaudio library
import ethaudio

# TODO: port this to a standard python test framework such as unittest
# TODO: encode expected change after each one of these commands to form a tuple similar to (cmd, {field1: value_expected, field2:value_expected})
test_sequence = [
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
    "vol" : -9,
    "disabled" : False
  },
  None,
  {
  }
),
(
  "Create a new group",
  {
      "command" : "create_group",
      "name" : "super_group",
      "zones": [0, 1, 2, 3, 4, 5],
  },
  None,
  {
    'added' :
    {
      'groups[3].id'    : 3,
      'groups[3].name'  : 'super_group',
      'groups[3].zones' : [0, 1, 2, 3, 4, 5],
      'groups[3].mute': False,
      'groups[3].source_id': None,
      'groups[3].vol_delta': -40,
    }
  }
),
(
  "Update super group to use source 1",
  {
    "command" : "set_group",
    "id" : 3,
    "source_id" : 1,
  },
  None,
  {
    'zones[1].source_id' : 1,
    'zones[2].source_id' : 1,
    'zones[3].source_id' : 1,
    'zones[5].source_id' : 1,
    'groups[0].source_id': 1,
    'groups[1].source_id': 1,
    'groups[2].source_id': 1,
    'groups[3].source_id': 1,
  }
),
(
  "Fix zone",
  {
    "command" : "set_zone",
    "id" : 1,
    "source_id" : 2,
  },
  None,
  {
    'zones[1].source_id' : 2
  }
),
(
  "Fix zone",
  {
    "command" : "set_zone",
    "id" : 2,
    "source_id" : 2,
  },
  None,
  {
    'zones[2].source_id' : 2
  }
),
(
  "Fix zone",
  {
    "command" : "set_zone",
    "id" : 3,
    "source_id" : 3,
  },
  None,
  {
    'zones[3].source_id' : 3
  }
),
(
  "Fix zone",
  {
    "command" : "set_zone",
    "id" : 5,
    "source_id" : 0,
  },
  None,
  {
    'zones[5].source_id' : 0
  }
),
# TODO: add more group commands here
(
  "Delete the newly created group",
  {
      "command" : "delete_group",
      "id" : 3,
  },
  None,
  {
    'removed' :
    {
      'groups[3].id'    : 3,
      'groups[3].name'  : 'super_group',
      'groups[3].zones' : [0, 1, 2, 3, 4, 5],
      'groups[3].vol_delta': -40,
      'groups[3].mute': False,
      'groups[3].source_id': None,
    }
  }
),
# TODO: test zone following group changes
# Rewind state back to initialization
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
  "Change zone 2 back",
  {
    "command" : "set_zone",
    "id" : 2,
    "vol" : -78
  },
  None,
  {
    'zones[2].vol' : -78
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
    "disabled" : False
  },
  None,
  {
    'zones[2].name' : 'Sleep Zone',
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

def add_field_entries(diff, changes, name, status_ref):
  """ Get the full field name and values that were either added or removed from the status (@status_ref)

      Args:
        diff : dict of items added or removed
        changes : field changes to update
        name: field name (deepdiff names) (ie. dictionary_item_added, dictionary_item_removed, iterable_item_added, iterable_item_removed)
        status_ref: status to get values from
  """
  if name in diff:
    for field in diff[name]:
      # get a simplified name of the field
      pretty = format(pretty_field(field))
      # get the value of this particular field
      actual = 'status_ref' + field.replace('root', '')
      result = eval(actual)
      # add field and its old/new value
      if type(result) == dict:
        for key, val in result.items():
          changes[pretty + '.' + key] = val
      else:
        changes[pretty] = result

def get_state_changes(ignore_group_changes=False):
  """ get difference between status when this was last called
    Args:
      ignore_group_changes: flag to ignore group changes since they can be
        generated aggregate properties, This is needed when changing a zone's volume,
        since a group's volume is calculated from its zones. Not all tests should need
        to care about these aggregate properties.

    Returns:
      changees: dict of modified fields
      added: list of added fields
      removed: list of removed fields
  """
  global last_status, eth_audio_api
  # cutoff_distance_for_pairs needs to be set so that changes don't get grouped together, this became a problem with groups when more fields were added
  # intersection distance is its pair, unsure what it does...
  diff = deepdiff.DeepDiff(last_status, eth_audio_api.status, ignore_order=True, cutoff_distance_for_pairs=0.9, cutoff_intersection_for_pairs=0.9)
  changes = ({}, {}, {})
  # merge type_changes and values_changed (weird that these names are different tenses)
  values_changed = {}
  for k in ['values_changed', 'type_changes']:
    if k in diff:
      values_changed.update(diff[k])
  for field, change in values_changed.items():
    ignore_change = ignore_group_changes and 'groups' in field
    if not ignore_change:
      changes[0][pretty_field(field)] = change['new_value']
  # get added fields
  add_field_entries(diff, changes[1], 'dictionary_item_added', eth_audio_api.status)
  add_field_entries(diff, changes[1], 'iterable_item_added', eth_audio_api.status)
  # get removed fields
  add_field_entries(diff, changes[2], 'dictionary_item_removed', last_status)
  add_field_entries(diff, changes[2], 'iterable_item_removed', last_status)
  last_status = deepcopy(eth_audio_api.status)
  return changes

def check_json_tst(name, result, expected_result, expected_changes, ignore_group_changes=True):
  # check state changes, we conditionally ignore group changes now that they have some aggregate properties that get modified by individual zones
  changes, added, removed = get_state_changes(ignore_group_changes)
  # handle additions and removals in expected changes as optional, making sure to remove them from the actual changes comparison
  expected_changes2 = dict(expected_changes)
  if 'added' in expected_changes:
    assert added == expected_changes['added']
    del expected_changes2['added']
  else:
    assert len(added) == 0
  if 'removed' in expected_changes:
    assert removed == expected_changes['removed']
    del expected_changes2['removed']
  else:
    assert len(removed) == 0
  assert changes == expected_changes2
  assert result == expected_result

def check_http_tst(name, result, expected_result, expected_changes, ignore_group_changes=True):
  assert result != None
  if 'error' in result:
    check_json_tst(name, result, expected_result, expected_changes, ignore_group_changes)
  else:
    check_json_tst(name, None, expected_result, expected_changes, ignore_group_changes)

# TODO: now that we are actually using pytest, we will need to break up these tests into modular pieces, we will need a test fixture that we can use to start from a known configuration
def check_all_tsts(api):
  global last_status, eth_audio_api, test_num
  test_num = 0

  eth_audio_api = api

  last_status = deepcopy(eth_audio_api.get_state())

  # Test emulated commands
  print('intial state:')
  print(eth_audio_api.get_state())
  print('\ntesting commands:')
  # Tests
  check_json_tst('Configure source 0 (digital)', eth_audio_api.set_source(0, 'Spotify', True), None, {'sources[0].name' : 'Spotify'})
  check_json_tst('Configure source 1 (digital)', eth_audio_api.set_source(1, 'Pandora', True), None, {'sources[1].name' : 'Pandora'})
  check_json_tst('Configure source 2 (Analog)', eth_audio_api.set_source(2, 'TV', False), None, {'sources[2].name' : 'TV', 'sources[2].digital' : False})
  check_json_tst('Configure source 3 (Analog)', eth_audio_api.set_source(3, 'PC', False), None, {'sources[3].name' : 'PC', 'sources[3].digital' : False})
  check_json_tst('Configure zone 0, Party Zone', eth_audio_api.set_zone(0, 'Party Zone', 1, False, 0, False), None, {'zones[0].name' : 'Party Zone', 'zones[0].source_id' : 1, 'zones[0].vol': 0, 'zones[0].mute' : False})
  check_json_tst('Configure zone 1, Drone Zone', eth_audio_api.set_zone(1, 'Drone Zone', 2, False, -20, False), None, {'zones[1].name' : 'Drone Zone', 'zones[1].source_id' : 2, 'zones[1].vol': -20, 'zones[1].mute' : False})
  check_json_tst('Configure zone 2, Sleep Zone', eth_audio_api.set_zone(2, None, None, None, None, False), None, {})
  check_json_tst('Configure zone 2, Sleep Zone', eth_audio_api.set_zone(2, 'Sleep Zone', 3, True, None, False), None, {'zones[2].name' : 'Sleep Zone', 'zones[2].source_id' : 3})
  check_json_tst('Configure zone 3, Standby Zone', eth_audio_api.set_zone(3, 'Standby Zone', 3, True, None, False), None, {'zones[3].name' : 'Standby Zone', 'zones[3].source_id' : 3})
  check_json_tst('Configure zone 4, Weird Zone', eth_audio_api.set_zone(4, 'Weird Zone', 1, None, None, None), None, {'zones[4].name' : 'Weird Zone', 'zones[4].source_id' : 1})

  # Test string/json based command handler
  print('\ntesting json:')
  for name, cmd, expected_result, expected_changes  in test_sequence:
    is_group_cmd = '_group' in cmd['command']
    check_json_tst(name, eth_audio_api.parse_cmd(cmd), expected_result, expected_changes, ignore_group_changes=not is_group_cmd)

  print('\ntesting json over http:')

  # Start HTTP server (behind the scenes it runs in new thread)
  srv = ethaudio.Server(eth_audio_api)

  # Send HTTP requests and print output
  client = ethaudio.Client()
  for name, cmd, expected_result, expected_changes in test_sequence:
    is_group_cmd = '_group' in cmd['command']
    check_http_tst(name, client.send_cmd(cmd), expected_result, expected_changes, ignore_group_changes=not is_group_cmd)

def test_mock():
  config_file = 'test_config.json'
  with open(config_file, 'w'): # overwrite the file with nothing, so test has to start from scratch
    pass
  config_file = 'test_config.json.bak'
  with open(config_file, 'w'): # overwrite the file with nothing, so test has to start from scratch
    pass
  check_all_tsts(ethaudio.Api(ethaudio.api.MockRt(), config_file=config_file))

if __name__ == '__main__':
  test_mock()
