#!/usr/bin/python3

import json
from copy import deepcopy
import deepdiff

import serial
import time
from smbus2 import SMBus
import smbus2 as smb

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

  def update_sources(self, digital):
    """ modify all of the 4 system sources

      Args:
        digital [bool*4]: array of configuration for sources where
          Analog is False and Digital True

      Returns:
        True on success, False on hw failure
    """
    assert len(digital) == 4
    for d in digital:
      assert type(d) == bool
    return True

  def update_zone_mutes(self, zone, mutes):
    """ Update the mute level to all of the zones

      Args:
        zone int: zone to muted/unmute
        mutes [bool*zones]: array of configuration for zones where
          Unmuted is False and Muted True

      Returns:
        True on success, False on hw failure
    """
    assert len(mutes) >= 6
    num_preamps = int(len(mutes) / 6)
    assert len(mutes) == num_preamps * 6
    for preamp in range(num_preamps):
      for zone in range(6):
        assert type(mutes[preamp * 6 + zone]) == bool
    return True

  def update_zone_stbys(self, zone, stbys):
    """ Update the standby to all of the zones

      Args:
        zone int: zone to standby/unstandby
        stbys [bool*zones]: array of configuration for zones where
          On is False and Standby True

      Returns:
        True on success, False on hw failure
    """
    assert len(stbys) >= 6
    num_preamps = int(len(stbys) / 6)
    assert len(stbys) == num_preamps * 6
    for preamp in range(num_preamps):
      for zone in range(6):
        assert type(stbys[preamp * 6 + zone]) == bool
    return True

  def update_zone_sources(self, zone, sources):
    """ Update the sources to all of the zones

      Args:
        zone int: zone to change source
        sources [int*zones]: array of source ids for zones (None in place of source id indicates disconnect)

      Returns:
        True on success, False on hw failure
    """
    assert len(sources) >= 6
    num_preamps = int(len(sources) / 6)
    assert len(sources) == num_preamps * 6
    for preamp in range(num_preamps):
      for zone in range(6):
        src = sources[preamp * 6 + zone]
        assert type(src) == int or src == None
    return True

  def update_zone_vol(self, zone, vol):
    """ Update the sources to all of the zones

      Args:
        zone: zone to adjust vol
        vol: int in range[-79, 0]

      Returns:
        True on success, False on hw failure
    """
    preamp = int(zone / 6)
    assert zone > 0
    assert preamp <= 15
    assert vol <= 0 and vol >= -79
    return True

class RpiRt:
  """ Actual EthAudio Runtime

      This acts as an EthAudio Runtime, expected to be executed on a raspberrypi
  """

  # Dictionary with all of the regs
  # NOT WORKING!!!!!! Is this not global within class??
  REG_ADDRS = {
    'SRC_AD_REG' : 0x00,
    'CH123_SRC_REG' : 0x01,
    'CH456_SRC_REG' : 0x02,
    'MUTE_REG' : 0x03,
    'STANDBY_REG' : 0x04,
    'CH1_ATTEN_REG' : 0x05,
    'CH2_ATTEN_REG' : 0x06,
    'CH3_ATTEN_REG' : 0x07,
    'CH4_ATTEN_REG' : 0x08,
    'CH5_ATTEN_REG' : 0x09,
    'CH6_ATTEN_REG' : 0x0A
  }

  def __init__(self):
    # Setup serial connection via UART pins - set I2C addresses for preamps
    ser = serial.Serial ("/dev/ttyS0")
    ser.baudrate = 9600
    addr = 0x41, 0x10, 0x0D, 0x0A
    ser.write(addr)
    ser.close()

    # Delay to account for addresses being set
    # Possibly unnecessary due to human delay
    time.sleep(3)

    # Setup self._bus as I2C1 from the RPi
    bus = smb.SMBus(1)
    self._bus = bus

  def update_zone_mutes(self, zone, mutes):
    """ Update the mute level to all of the zones

      Args:
        zone int: zone to muted/unmute
        mutes [bool*zones]: array of configuration for zones where
          Unmuted is False and Muted True

      Returns:
        True on success, False on hw failure
    """
    return False

  def update_zone_stbys(self, zone, stbys):
    """ Update the standby to all of the zones

      Args:
        zone int: zone to standby/unstandby
        stbys [bool*zones]: array of configuration for zones where
          On is False and Standby True

      Returns:
        True on success, False on hw failure
    """
    # TODO: actually configure the stbys
    return False

  def update_zone_sources(self, zone, sources):
    """ Update the sources to all of the zones

      Args:
        zone int: zone to change source
        sources [int*zones]: array of source ids for zones (None in place of source id indicates disconnect)

      Returns:
        True on success, False on hw failure
    """
    # TODO: actually configure the sources
    return False

  def update_zone_vol(self, zone, vol):
    """ Update the sources to all of the zones

      Args:
        zone: zone to adjust vol
        vol: int in range[-79, 0]

      Returns:
        True on success, False on hw failure
    """
    # TODO: configure zone's volume on preamp
    return False

  def update_sources(self, digital):
    """ modify all of the 4 system sources

      Args:
        digital [bool*4]: array of configuration for sources where
          Analog is False and Digital True

      Returns:
        True on success, False on hw failure
    """

    # Start with a fresh byte - only update on Digital (True)
    output = 0x00

    # When digital is true, set the appropriate bit to 1
    for i in range(4):    
      if digital[i]:
        output = output | (0x01 << i)

    # Send out the updated source information to the appropriate preamp
    self._bus.write_byte_data(0x08, 0x00, output)

    # TODO: update this to allow for different preamps on the bus
    # also, figure out how to use 'SRC_AD_REG' instead of 0x00 (see init)
    return True # TODO: Add error checking on successful write

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
        # get the current digital state of all of the sources
        digital_cfg = [ self.status['sources'][s]['digital'] for s in range(4) ]
        # update this source
        digital_cfg[idx] = bool(digital)
        # update the name
        src['name'] = str(name)
        if self._rt.update_sources(digital_cfg):
          # update the status
          src['digital'] = bool(digital)
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
        source_id, update_source_id = updated_val(source_id, z['source_id'])
        mute, update_mutes = updated_val(mute, z['mute'])
        stby, update_stbys = updated_val(stby, z['stby'])
        vol, update_vol = updated_val(vol, z['vol'])
        disabled, _ = updated_val(disabled, z['disabled'])
      except Exception as e:
        return error('failed to set zone, error getting current state: {}'.format(e))
      try:
        sid = parse_int(source_id, [0, 1, 2, 3, 4])
        vol = parse_int(vol, range(-79, 1))
        zones = self.status['zones']
        # update non hw state
        z['name'] = name
        z['disabled'] = disabled
        # TODO: figure out an order of operations here, like does mute need to be done before changing sources?
        if True or update_source_id:
          zone_sources = [ zone['source_id'] for zone in zones ]
          zone_sources[idx] = sid
          if self._rt.update_zone_sources(idx, zone_sources):
            z['source_id'] = sid
          else:
            return error('set zone failed: unable to update zone source')
        if update_mutes:
          mutes = [ zone['mute'] for zone in zones ]
          mutes[idx] = mute
          if self._rt.update_zone_mutes(idx, mutes):
            z['mute'] = mute
          else:
            return error('set zone failed: unable to update zone mute')
        if update_stbys:
          stbys = [ zone['stby'] for zone in zones ]
          stbys[idx] = stby
          if self._rt.update_zone_stbys(idx, stbys):
            z['stby'] = stby
          else:
            return error('set zone failed: unable to update zone stby')
        if update_vol:
          if self._rt.update_zone_vol(idx, vol):
            z['vol'] = vol
          else:
            return error('set zone failed: unable to update zone volume')
        return None
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
