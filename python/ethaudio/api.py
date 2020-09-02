#!/usr/bin/python3

import json
from copy import deepcopy
import deepdiff

# Helper functions
def encode(pydata):
  """ Encode a dictionary as JSON """
  return json.dumps(pydata)

def decode(j):
  """ Decode JSON into dictionary """
  return json.loads(j)

def parse_int(i, options):
  """ Parse an integer into one of the given options """
  if int(i) in options:
    return int(i)
  else:
    raise ValueError('{} is not in [{}]'.format(i, options))

def error(msg):
  """ wrap the error message specified by msg into an error """
  return {'error': msg}

class EthAudioApi:
  """ EthAudio API

    TODO: make this either a base class, put it in another file, and make both a mock class and a real implementation
    For now this is just a mock implementation
   """

  def __init__(self):
    """ intitialize the mock system to to base configuration """
    self.status = { # This is the system state response that will come back from the ethaudio box
      "power": {
        "audio_power": False, # this needs to be on for any zone to work
        "usb_power": False     # this turns on/off the usb power port
      },
      "sources": [ # this is an array of source objects, each has an id, name, and bool specifying wheater source comes from RCA or digital input
        { "id": 0, "name": "Source 1", "digital": False  },
        { "id": 1, "name": "Source 2", "digital": False  },
        { "id": 2, "name": "Source 3", "digital": False  },
        { "id": 3, "name": "Source 4", "digital": False  }
      ],
      "zones": [ # this is an array of zones, array length depends on # of boxes connected
        { "id": 0, "name": "Zone 1", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 1, "name": "Zone 2", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 2, "name": "Zone 3", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 3, "name": "Zone 4", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 4, "name": "Zone 5", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 5, "name": "Zone 6", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 }
      ],
      "groups": [ # this is an array of groups that have been created , each group has a friendly name and an array of member zones
        { "id": 0, "name": "Group 1", "zones": [0,1,2] },
        { "id": 1, "name": "Group 2", "zones": [2,3,4] },
        { "id": 2, "name": "Group 3", "zones": [5] }
      ]
    }

  def parse_cmd(self, cmd):
    """ process an individual command

      Args:
        cmd(dict): a command decoded from the JSON interface
      Returns:
        'None' if successful, otherwise an error(dict)
    """
    try:
      command = cmd['command']
      if command is None:
        return error('No command specified')
      elif command == 'return_state':
        return None # state is returned at a higher level on success
      elif command == 'set_power':
        return self.set_power(cmd['audio_power'], cmd['usb_power'])
      elif command == 'set_source':
        return self.set_source(cmd['id'], cmd['name'], cmd['digital'])
      elif command == 'set_zone':
        return self.set_zone(cmd['id'], cmd['name'], cmd['source_id'], cmd['mute'], cmd['stby'], cmd['vol'], cmd['disabled'])
      elif command == 'set_group':
        return error('set_group unimplemented')
      elif command == 'create_group':
        return error('create_group unimplemented')
      elif command == 'delete_group':
        return error('delete_group unimplemented')
      else:
        return error('command {} is not supported'.format(command))
    except Exception as e:
      return error(str(e)) # TODO: handle exception more verbosely

  def get_state(self):
    """ get the system state (dict) """
    return self.status

  def set_power(self, audio_on, usb_on):
    """ enable / disable the 9V audio power and 5V usb power """
    self.status['power']['audio_power'] = audio_on
    self.status['power']['usb_power'] = usb_on
    return None

  def set_source(self, id, name, digital):
    """ modify any of the 4 system sources

      Args:
        id (int): source id [0,4]
        name (str): user friendly source name, ie. "cd player" or "stream 1"

      Returns:
        'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['sources']):
      if s['id'] == id:
        idx = i
    if idx is not None:
      try:
        self.status['sources'][idx]['name'] = str(name)
        self.status['sources'][idx]['digital'] = bool(digital)
        return None
      except Exception as e:
        return error('set source ' + str(e))
    else:
      return error('set source: index {} out of bounds'.format(idx))

  def set_zone(self, id, name, source_id, mute, stby, vol, disabled):
    """ modify any zone

          Args:
            id (int): any valid zone [0,p*6-1] (6 zones per preamp)
            name(str): friendly name for the zone, ie "bathroom" or "kitchen 1"
            source_id (int): source to connect to [0,3]
            mute (bool): mute the zone regardless of set volume
            stby (bool): set the zone to standby, very low power consumption state
            vol (int): attenuation [-79,0] 0 is max volume, -79 is min volume
            disabled (bool): disable zone, for when the zone is not connected to any speakers and not in use
          Returns:
            'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['zones']):
      if s['id'] == id:
        idx = i
    if idx is not None:
      try:
        self.status['zones'][idx]['name'] = str(name)
        self.status['zones'][idx]['source_id'] = parse_int(source_id, [1, 2, 3, 4])
        self.status['zones'][idx]['mute'] = bool(mute)
        self.status['zones'][idx]['stby'] = bool(stby)
        self.status['zones'][idx]['vol'] = parse_int(vol, range(-79, 1))
        self.status['zones'][idx]['disabled'] = bool(disabled)
        return None
      except Exception as e:
        return error('set zone'  + str(e))
    else:
        return error('set zone: index {} out of bounds'.format(idx))

  # TODO: make set group
  # This command can be used to set any EXISTING group
  # Along with the command one or more of the parameters can be passed
  # check the system state for a list of existing group
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  #{
  #    "command":"set_group",
  #    "id":any vaild group,
  #    "name":"new name" # sets the friendly name for the group, ie "upstairs" or "back yard"
  #    "source_id": 0 | 1 | 2 | 3 # change all zones in group to different source
  #    "zones": [0,1,2...] # specify new array of zones that make up the group
  #    "mute": False | True # mutes all zones in group
  #    "stby": False | True # sets all zone in group to standby
  #    "vol_delta": 0 to 79 # CHANGES the volume of each zone in the group by this much. For each zone, will saturate if out of range
  #}

  # TODO: make create new group
  # This command can be used to create a NEW group
  # Along with the command ALL parameters must also be passed
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  # Refer to the returned system state to obtain the id for the newly created group
  #{
  #    "command":"create_group"
  #    "name":"new group name"
  #    "zones": [0,1,2...] # specify new array of zones that make up the group
  #}

  # TODO: make delete group
  # This command can be used to delete an EXISTING group
  # Along with the command ALL parameters must also be passed
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  #{
  #    "command":"delete_group"
  #    "id":"new group name"
  #}
