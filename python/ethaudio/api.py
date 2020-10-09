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

def updated_val(update, val):
  """ get the potentially updated value, @update, defaulting to the current value, @val, if it is None """
  if update is None:
    return val, False
  else:
    return update, update != val

def clamp(x, xmin, xmax):
    return max(xmin, min(x, xmax))

class MockRt:
  """ Mock of an EthAudio Runtime

      This pretends to be the runtime of EthAudio, but actually does nothing
  """

  def __init__(self):
    pass

  def set_power(self, audio_on, usb_on):
    """ enable / disable the 9V audio power and 5V usb power

          Returns:
            True on success, False on hw failure
    """
    return True

  def set_source(self, id, digital):
    """ modify any of the 4 system sources

      Args:
        id (int): source id [0,4]

      Returns:
        True on success, False on hw failure
    """
    return True

  def set_zone(self, id, source_id, mute, stby, vol, disabled):
    """ modify any zone

          Args:
            id (int): any valid zone [0,p*6-1] (6 zones per preamp)
            source_id (int): source to connect to [0,3]
            mute (bool): mute the zone regardless of set volume
            stby (bool): set the zone to standby, very low power consumption state
            vol (int): attenuation [-79,0] 0 is max volume, -79 is min volume
            disabled (bool): disable zone, for when the zone is not connected to any speakers and not in use

          Returns:
            True on success, False on hw failure
    """
    return True

class RpiRt:
  """ Actual EthAudio Runtime

      This acts as an EthAudio Runtime, expected to be executed on a raspberrypi
  """

  def __init__(self):
    pass

  def set_power(self, audio_on, usb_on):
    """ enable / disable the 9V audio power and 5V usb power

      Returns:
        True on success, False on hw failure
    """
    # TODO: actually configure the power and verify the configuration
    return False

  def set_source(self, id, digital):
    """ modify any of the 4 system sources

      Args:
        id (int): source id [0,3]

      Returns:
        True on success, False on hw failure
    """
    # TODO: actually configure the source and verify it
    return False

  def set_zone(self, id, source_id, mute, stby, vol, disabled):
    """ modify any zone

          Args:
            id (int): any valid zone [0,p*6-1] (6 zones per preamp)
            source_id (int): source to connect to [0,3]
            mute (bool): mute the zone regardless of set volume
            stby (bool): set the zone to standby, very low power consumption state
            vol (int): attenuation [-79,0] 0 is max volume, -79 is min volume
            disabled (bool): disable zone, for when the zone is not connected to any speakers and not in use

          Returns:
            True on success, False on hw failure
    """
    # TODO: actually configure the zone and verfy it
    return False

class EthAudioApi:
  """ EthAudio API

    TODO: make this either a base class, put it in another file, and make both a mock class and a real implementation
    For now this is just a mock implementation
   """

  def __init__(self, rt = MockRt()):
    self._rt = rt
    """ intitialize the mock system to to base configuration """
    # TODO: this status will need to be loaded from a file
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
        return self.set_power(cmd.get('audio_power'), cmd.get('usb_power'))
      elif command == 'set_source':
        return self.set_source(cmd.get('id'), cmd.get('name'), cmd.get('digital'))
      elif command == 'set_zone':
        return self.set_zone(cmd.get('id'), cmd.get('name'), cmd.get('source_id'), cmd.get('mute'), cmd.get('stby'), cmd.get('vol'), cmd.get('disabled'))
      elif command == 'set_group':
        return self.set_group(cmd.get('id'), cmd.get('name'), cmd.get('source_id'), cmd.get('zones'), cmd.get('mute'), cmd.get('stby'), cmd.get('vol_delta'))
      elif command == 'create_group':
        return self.create_group(cmd.get('name'), cmd.get('zones'))
      elif command == 'delete_group':
        return self.delete_group(cmd.get('id'))
      else:
        return error('command {} is not supported'.format(command))
    except Exception as e:
      return error(str(e)) # TODO: handle exception more verbosely

  def get_state(self):
    """ get the system state (dict) """
    return self.status

  def set_power(self, audio_power=None, usb_power=None):
    """ enable / disable the 9V audio power and 5V usb power """
    p = self.status['power']
    audio_power, _ = updated_val(audio_power, p['audio_power'])
    usb_power, _ = updated_val(usb_power, p['usb_power'])
    if self._rt.set_power(bool(audio_power), bool(usb_power)):
      self.status['power']['audio_power'] = bool(audio_power)
      self.status['power']['usb_power'] = bool(usb_power)
      return None
    else:
      return error('failed to set power')

  def set_source(self, id, name = None, digital = None):
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
        src = self.status['sources'][idx]
        name, _ = updated_val(name, src['name'])
        digital, _ = updated_val(digital, src['digital'])
      except Exception as e:
        return error('failed to set source, error getting current state: {}'.format(e))
      try:
        if self._rt.set_source(idx, bool(digital)):
          # update the status
          self.status['sources'][idx]['name'] = str(name)
          self.status['sources'][idx]['digital'] = bool(digital)
          return None
        else:
          return error('failed to set source')
      except Exception as e:
        return error('set source ' + str(e))
    else:
      return error('set source: index {} out of bounds'.format(idx))

  def set_zone(self, id, name=None, source_id=None, mute=None, stby=None, vol=None, disabled=None):
    """ modify any zone

          Args:
            id (int): any valid zone [0,p*6-1] (6 zones per preamp)
            name(str): friendly name for the zone, ie "bathroom" or "kitchen 1"
            source_id (int): source to connect to [0,4]
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
        z = self.status['zones'][idx]
        # TODO: use updated? value
        name, _ = updated_val(name, z['name'])
        source_id, _ = updated_val(source_id, z['source_id'])
        mute, _ = updated_val(mute, z['mute'])
        stby, _ = updated_val(stby, z['stby'])
        vol, _ = updated_val(vol, z['vol'])
        disabled, _ = updated_val(disabled, z['disabled'])
      except Exception as e:
        return error('failed to set zone, error getting current state: {}'.format(e))
      try:
        sid = parse_int(source_id, [0, 1, 2, 3, 4])
        vol = parse_int(vol, range(-79, 1))
        if self._rt.set_zone(idx, sid, bool(mute), bool(stby), vol, bool(disabled)):
          self.status['zones'][idx]['name'] = str(name)
          self.status['zones'][idx]['source_id'] = sid
          self.status['zones'][idx]['mute'] = bool(mute)
          self.status['zones'][idx]['stby'] = bool(stby)
          self.status['zones'][idx]['vol'] = vol
          self.status['zones'][idx]['disabled'] = bool(disabled)
          return None
        else:
          return error('failed to set zone')
      except Exception as e:
        return error('set zone'  + str(e))
    else:
        return error('set zone: index {} out of bounds'.format(idx))

  def get_group(self, id):
    for i, g in enumerate(self.status['groups']):
      if g['id'] == id:
        return i,g
    return -1, None

  def set_group(self, id, name=None, source_id=None, zones=None, mute=None, stby=None, vol_delta=None):
    """ Configure an existing group
        parameters will be used to configure each sone in the group's zones
        all parameters besides the group id, @id, are optional
    """
    _, g = self.get_group(id)
    if g is None:
      return error('set group failed, group {} not found'.format(id))
    try:
      name, _ = updated_val(name, g['name'])
      zones, _ = updated_val(zones, g['zones'])
    except Exception as e:
      return error('failed to configure group, error getting current state: {}'.format(e))
    g['name'] = name
    g['zones'] = zones
    for z in [ self.status['zones'][zone] for zone in zones ]:
      if vol_delta is not None:
        vol = clamp(z['vol'] + vol_delta, -79, 0)
      else:
        vol = None
      self.set_zone(z['id'], None, source_id, mute, stby, vol)

  def new_group_id(self):
    """ get next available group id """
    ids = [ g['id'] for g in self.status['groups'] ]
    ids = set(ids) # simpler/faster access
    new_gid = len(ids)
    for i in range(0, len(ids)):
      if i not in ids:
        new_gid = i
        break
    return new_gid

  def create_group(self, name, zones):
    """create a new group with a list of zones
    Refer to the returned system state to obtain the id for the newly created group
    """
    # verify new group's name is unique
    names = [ g['name'] for g in self.status['groups'] ]
    if name in names:
      return error('create group failed: {} already exists'.format(name))

    # get the new groug's id
    id = self.new_group_id()

    # add the new group
    group = { 'id': id, 'name' : name, 'zones' : zones }
    self.status['groups'].append(group)

  def delete_group(self, id):
    """delete an existing group"""
    try:
      i, _ = self.get_group(id)
      del self.status['groups'][i]
    except KeyError:
      return error('delete group failed: {} does not exist'.format(id))
