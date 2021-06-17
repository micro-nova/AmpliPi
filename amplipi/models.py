# AmpliPi Home Audio
# Copyright (C) 2021 MicroNova LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""AmpliPi Data Models

Encourages reuse of datastructures across AmpliPi
"""

# type handling, fastapi leverages type checking for performance and easy docs
from typing import List, Dict, Optional, Union
from types import SimpleNamespace
from enum import Enum
from pydantic import BaseSettings, BaseModel, Field

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring

class fields(SimpleNamespace):
  """ AmpliPi's field types """
  ID = Field(description='Unique identifier')
  Name = Field(description='Friendly name')
  SourceId = Field(ge=0, le=3, description='id of the connected source')
  ZoneId = Field(ge=0, le=35)
  Mute = Field(description='Set to true if output is muted')
  Volume = Field(ge=-79, le=0, description='Output volume in dB')
  GroupMute = Field(description='Set to true if output is all zones muted')
  GroupVolume = Field(ge=-79, le=0, description='Average input volume in dB')
  Disabled = Field(description='Set to true if not connected to a speaker')
  Zones = Field(description='Set of zones belonging to a group')
  AudioInput = Field('', description="""Connected audio source

  * Digital Stream ('stream=SID') where SID is the ID of the connected stream
  * Analog RCA Input ('local') connects to the RCA inputs associated
  * Nothing ('') behind the scenes this is muxed to a digital output
  """)

class fields_w_default(SimpleNamespace):
  """ AmpliPi's field types that need a default value

  These are needed because there is ambiguity where and optional field has a default value
  """
  # TODO: less duplication
  SourceId = Field(default=0, ge=0, le=3, description='id of the connected source')
  Mute = Field(default=True, description='Set to true if output is muted')
  Volume = Field(default=-79, ge=-79, le=0, description='Output volume in dB')
  GroupMute = Field(default=True, description='Set to true if output is all zones muted')
  GroupVolume = Field(default=-79, ge=-79, le=0, description='Average utput volume in dB')
  Disabled = Field(default=False, description='Set to true if not connected to a speaker')

class Base(BaseModel):
  """ Base class for AmpliPi Models
  id: Per type unique id generated on instance creation
    id is always returned by all API calls.
    It is optional so this calls can be abstract enough to use for creation and returned state
  name: Associated name, not intended to be unique
  """
  id: Optional[int] = fields.ID
  name: str = fields.Name

class BaseUpdate(BaseModel):
  """ Base class for updates to AmpliPi models
  name: Associated name, updated if necessary
  """
  name: Optional[str] = fields.Name

class SourceInfo(BaseModel):
  artist: Optional[str]
  track: Optional[str]
  album: Optional[str]
  station: Optional[str] # name of radio station
  state: Optional[str] # paused, playing, stopped, unknown, loading ???
  img_url: Optional[str]

class Source(Base):
  """ An audio source """
  input: str = fields.AudioInput
  info: Optional[SourceInfo] = Field(description='Additional info about the current audio playing from the stream (generated during playback')

  def get_stream(self) -> Optional[int]:
    """ Get a sources conneted stream if any """
    try:
      sinput = str(self.input)
      if 'stream=' in sinput:
        return int(sinput.split('=')[1])
      return None
    except ValueError:
      return None

  def as_update(self) -> 'SourceUpdate':
    """ Convert to SourceUpdate """
    update = self.dict()
    update.pop('id')
    return SourceUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'examples': {
        'stream connected': {
          'value': {
            'id' : 1,
            'name': '1',
            'input': 'stream=1009',
            'info': {
              'album': 'Far (Deluxe Version)',
              'artist': 'Regina Spektor',
              'img_url': 'http://mediaserver-cont-dc6-1-v4v6.pandora.com/images/public/int/2/1/5/4/093624974512_500W_500H.jpg',
              'station': 'Regina Spektor Radio',
              'track': 'Eet',
              'state': 'playing',
            }
          }
        },
        'nothing connected': {
          'value': {
            'id' : 2,
            'name': '2',
            'input': '',
            'info': {
              'img_url': 'static/imgs/disconnected.png',
              'state': 'stopped',
            }
          }
        },
        'rca connected': {
          'value': {
            'id' : 3,
            'name': '3',
            'input': 'local',
            'info': {
              'img_url': 'static/imgs/rca_inputs.svg',
              'state': 'unknown',
            }
          }
        },
      }
    }

class SourceUpdate(BaseUpdate):
  """ Partial reconfiguration of an audio Source """
  input: Optional[str] # 'None', 'local', 'stream=ID' # TODO: add helpers to get stream_id

  class Config:
    schema_extra = {
      'examples': {
        'Update Input to RCA input': {
          'value': {'input': 'local'}
        },
        'Update name': {
          'value': {'name': 'J2'}
        },
        'Update Input to Matt and Kim Radio': {
          'value': {'input': 'stream=10001'}
        },
      }
    }

class SourceUpdateWithId(SourceUpdate):
  """ Partial reconfiguration of a specific audio Source """
  id : int = Field(ge=0,le=4)

  def as_update(self) -> SourceUpdate:
    """ Convert to SourceUpdate """
    update = self.dict()
    update.pop('id')
    return SourceUpdate.parse_obj(update)

class Zone(Base):
  """ Audio output to a stereo pair of speakers, typically belonging to a room """
  source_id: int = fields_w_default.SourceId
  mute: bool = fields_w_default.Mute
  vol: int = fields_w_default.Volume
  disabled: bool = fields_w_default.Disabled

  def as_update(self) -> 'ZoneUpdate':
    """ Convert to ZoneUpdate """
    update = self.dict()
    update.pop('id')
    return ZoneUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'examples': {
        'Living Room' : {
          'value': {
            'name': 'Living Room',
            'source_id': 1,
            'mute' : False,
            'vol':-25,
            'disabled': False,
          }
        },
        'Dining Room' : {
          'value': {
            'name': 'Dining Room',
            'source_id': 2,
            'mute' : True,
            'vol':-65,
            'disabled': False,
          }
        },
      }
    }

class ZoneUpdate(BaseUpdate):
  """ Reconfiguration of a Zone """
  source_id: Optional[int] = fields.SourceId
  mute: Optional[bool] = fields.Mute
  vol: Optional[int] = fields.Volume
  disabled: Optional[bool] = fields.Disabled

  class Config:
    schema_extra = {
      'examples': {
        'Change Name': {
          'value': {
            'name':
            'Bedroom'
          }
        },
        'Change audio source': {
          'value': {
            'source-id': 3
          }
        },
        'Increase Volume': {
          'value': {
            'vol': -45
          }
        },
        'Mute': {
          'value': {
            'mute': True
          }
        }
      },
    }

class ZoneUpdateWithId(ZoneUpdate):
  """ Reconfiguration of a specific Zone """
  id: int = fields.ZoneId

  def as_update(self) -> ZoneUpdate:
    """ Convert to ZoneUpdate """
    update = self.dict()
    update.pop('id')
    return ZoneUpdate.parse_obj(update)

class Group(Base):
  """ A group of zones that can share the same audio input and be controlled as a group ie. Updstairs.

  Volume, mute, and source_id fields are aggregates of the member zones."""
  source_id: Optional[int] = fields.SourceId
  zones: List[int] = fields.Zones # should be a set, but JSON doesn't have native sets
  mute: Optional[bool] = fields.GroupMute
  vol_delta: Optional[int] = fields.GroupVolume

  def as_update(self) -> 'GroupUpdate':
    """ Convert to GroupUpdate """
    update = self.dict()
    update.pop('id')
    return GroupUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'creation_examples': {
        'Upstairs Group': {
          'value': {
            'name': 'Upstairs',
            'zones': [1, 2, 3, 4, 5]
          }
        },
        'Downstairs Group': {
          'value': {
            'name': 'Downstairs',
            'zones': [6,7,8,9]
          }
        }
      },
      'examples': {
        'Upstairs Group': {
          'value': {
            'id': 101,
            'name': 'Upstairs',
            'zones': [1, 2, 3, 4, 5],
            'vol_delta': -65
          }
        },
        'Downstairs Group': {
          'value': {
            'id': 102,
            'name': 'Downstairs',
            'zones': [6,7,8,9],
            'vol_delta': -30
          }
        }
      },
    }

class GroupUpdate(BaseUpdate):
  """ Reconfiguration of a Group """
  source_id: Optional[int] = fields.SourceId
  zones: Optional[List[int]] = fields.Zones
  mute: Optional[bool] = fields.GroupMute
  vol_delta: Optional[int] = fields.GroupVolume

  class Config:
    schema_extra = {
      'examples': {
        'Rezone Group': {
          'value': {
            'name': 'Upstairs',
            'zones': [3,4,5]
          }
        },
        'Change Name': {
          'value': {
            'name': 'Upstairs'
          }
        },
        'Change audio source': {
          'value': {
            'source-id': 3
          }
        },
        'Increase Volume': {
          'value': {
            'vol_delta': -45
          }
        },
        'Mute': {
          'value': {
            'mute': True
          }
        }
      },
    }

class GroupUpdateWithId(GroupUpdate):
  """ Reconfiguration of a specific Group """
  id: int

  def as_update(self) -> GroupUpdate:
    """ Convert to GroupUpdate """
    update = self.dict()
    update.pop('id')
    return GroupUpdate.parse_obj(update)

class Stream(Base):
  """ Digital stream such as Pandora, Airplay or Spotify """
  type: str = Field(description="""stream type

  * pandora
  * shairport
  * dlna
  * internetradio
  * spotify
  * plexamp
  """)
  # TODO: how to support different stream types
  user: Optional[str] = Field(description='User login')
  password: Optional[str] = Field(description='Password')
  station: Optional[str] = Field(description='Radio station identifier')
  url: Optional[str] = Field(description='Stream url, used for internetradio')
  logo: Optional[str] = Field(description='Icon/Logo url, used for internetradio')
  client_id: Optional[str] = Field(description='Plexamp client_id, becomes "identifier" in server.json')
  token: Optional[str] = Field(description='Plexamp token for server.json')

  # add examples for each type of stream
  class Config:
    schema_extra = {
      'creation_examples': {
        'Add Beatles Internet Radio Station': {
          'value': {
            'logo': 'http://www.beatlesradio.com/content/images/thumbs/0000587.gif',
            'name': 'Beatles Radio',
            'type': 'internetradio',
            'url': 'http://www.beatlesradio.com:8000/stream/1/'
          }
        },
        'Add Classical KING Internet Radio Station': {
          'value': {
            'logo': 'https://i.iheart.com/v3/re/assets/images/7bcfd87a-de3e-47d0-b896-be0ed38c9d74.png',
            'name': 'Classical KING FM 98.1',
            'type': 'internetradio',
            'url': 'http://classicalking.streamguys1.com/king-fm-aac-iheart'
          }
        },
        'Add Generic DLNA': {
          'value': {
            'name': 'Replace this text with a name you like!',
            'type': 'dlna'
            }
        },
        'Add Groove Salad Internet Radio Station': {
          'value': {
            'logo': 'https://somafm.com/img3/groovesalad-200.jpg',
            'name': 'Groove Salad',
            'type': 'internetradio',
            'url': 'http://ice2.somafm.com/groovesalad-16-aac'
          }
        },
        'Add KEXP Internet Radio Station': {
          'value': {
            'logo': 'https://i.iheart.com/v3/re/new_assets/cc4e0a17-5233-4e4b-9b6b-7799904f78ea',
            'name': 'KEXP '
            '90.3',
            'type': 'internetradio',
            'url': 'http://live-aacplus-64.kexp.org/kexp64.aac'
          }
        },
        'Add Matt and Kim Pandora Station': {
          'value': {
            'name': 'Matt and Kim Radio',
            'password': 's79sDDkjf',
            'station': '4473713754798410236',
            'type': 'pandora',
            'user': 'test@micro-nova.com'
          }
        },
        'Add MicroNova Spotify': {
          'value': {
            'name': 'MicroNova Spotify',
            'type': 'spotify'
          }
        },
        'Add Micronova Airplay': {
          'value': {
            'name': 'Micronova AP',
            'type': 'shairport'
          }
        },
      },
      'examples': {
        'Regina Spektor Radio': {
          'value': {
            'id': 90890,
            'name': 'Regina Spektor Radio',
            'password': '',
            'station': '4473713754798410236',
            'status': 'connected',
            'type': 'pandora',
            'user': 'example1@micro-nova.com'
          }
        },
        'Matt and Kim Radio (disconnected)': {
          'value': {
            'id': 90891,
            'info': {'details': 'No info available'},
            'name': 'Matt and Kim Radio',
            'password': '',
            'station': '4610303469018478727',
            'status': 'disconnected',
            'type': 'pandora',
            'user': 'example2@micro-nova.com'
          }
        },
        'Shairport (connected)': {
          'value': {
            'id': 44590,
            'info': {'details': 'No info available'},
            'name': "Jason's iPhone",
            'status': 'connected',
            'type': 'shairport'
          }
        },
        'Shairport (disconnected)': {
          'value': {
            'id': 4894,
            'info': {'details': 'No info available'},
            'name': 'Rnay',
            'status': 'disconnected',
            'type': 'shairport'
          }
        },
      }
    }

class StreamUpdate(BaseUpdate):
  """ Reconfiguration of a Stream """
  # TODO: how to support different stream types
  user: Optional[str]
  password: Optional[str]
  station: Optional[str]
  url: Optional[str]
  logo: Optional[str]

  class Config:
    schema_extra = {
      'examples': {
        'Change account info': {
          'value': {
            'password': 'sd9sk3k30',
            'user': 'test@micro-nova.com'
          }
        },
        'Change name': {
          'value': {
            'name': 'Matt and Kim Radio'
            }
          },
        'Change pandora radio station': {
          'value': {
            'station': '0982034049300'
          }
        },
        'Upgrade groove salad stream quality': {
          'value': {
            'url': 'http://ice2.somafm.com/groovesalad-64-aac'
          }
        }
      },
    }


class StreamCommand(str, Enum):
  PLAY = 'play'
  PAUSE = 'pause'
  NEXT = 'next'
  STOP = 'stop'
  LOVE = 'love'
  BAN = 'ban'
  SHELVE = 'shelve'

class PresetState(BaseModel):
  """ A set of partial configuration changes to make to sources, zones, and groups """
  sources: Optional[List[SourceUpdateWithId]]
  zones: Optional[List[ZoneUpdateWithId]]
  groups: Optional[List[GroupUpdateWithId]]

class Command(BaseModel):
  """ A command to execute on a stream """
  stream_id: int = Field(description="Stream to execute the command on")
  cmd: str = Field(description="Command to execute")

class Preset(Base):
  """ A partial controller configuration the can be loaded on demand.
  In addition to most of the configuration found in Status, this can contain commands as well that configure the state of different streaming services.
  """
  state: Optional[PresetState]
  commands: Optional[List[Command]]
  last_used: Union[int, None] = None


  class Config:
    schema_extra = {
      'creation_examples': {
        'Add Mute All': {
          'value': {
            'name': 'Mute All',
            'state': {
              'zones': [
                {'id': 0, 'mute': True},
                {'id': 1, 'mute': True},
                {'id': 2, 'mute': True},
                {'id': 3, 'mute': True},
                {'id': 4, 'mute': True},
                {'id': 5, 'mute': True}
              ]
            }
          }
        }
      },
      'examples': {
        'Mute All': {
          'value': {
            'id': 10000,
            'name': 'Mute All',
            'state': {
              'zones': [
                {'id': 0, 'mute': True},
                {'id': 1, 'mute': True},
                {'id': 2, 'mute': True},
                {'id': 3, 'mute': True},
                {'id': 4, 'mute': True},
                {'id': 5, 'mute': True}
              ]
            }
          }
        }
      }
    }

class PresetUpdate(BaseUpdate):
  """ Changes to a current preset

  The contents of state and commands will be completely replaced if populated.
  Merging old and new updates seems too complicated and error prone.
  """
  state: Optional[PresetState]
  commands: Optional[List[Command]]

  class Config:
    schema_extra = {
      'examples': {
        'Only mute some': {
          'value': {
            'name': 'Mute Some',
            'state': {
              'zones': [
                {'id': 0, 'mute': True},
                {'id': 1, 'mute': True},
                {'id': 2, 'mute': True},
                {'id': 5, 'mute': True}
              ]
            }
          }
        }
      }
    }

class Info(BaseModel):
  """ Information about the settings used by the controller """
  config_file: str = 'Uknown'
  version: str = 'Unknown'
  mock_ctrl: bool = False
  mock_streams: bool = False

class Status(BaseModel):
  """ Full Controller Configuration and Status """
  sources: List[Source] = [Source(id=i, name=str(i)) for i in range(4)]
  zones: List[Zone] = [Zone(id=i, name=f'Zone {i}') for i in range(6) ]
  groups: List[Group] = []
  streams: List[Stream] = []
  presets: List[Preset] = []
  info: Optional[Info]

  class Config:
    schema_extra = {
      'examples': {
        "Status of Jason's AmpliPi": {
          'value': {
            'groups': [
              {
                'id': 0,
                'mute': False,
                'name': 'Whole House',
                'source_id': None,
                'vol_delta': -44,
                'zones': [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11]
              },
              {
                'id': 1,
                'mute': True,
                'name': 'KitchLivDining',
                'source_id': 0,
                'vol_delta': -49,
                'zones': [3, 9, 10, 11]
              }
            ],
            'presets': [
              {
                'id': 10000,
                'name': 'Mute All',
                'state': {
                  'zones': [
                    {'id': 0, 'mute': True},
                    {'id': 1, 'mute': True},
                    {'id': 2, 'mute': True},
                    {'id': 3, 'mute': True},
                    {'id': 4, 'mute': True},
                    {'id': 5, 'mute': True}
                  ]
                }
              }
            ],
            'sources': [
              {'id': 0, 'input': 'stream=90890', 'name': 'J1'},
              {'id': 1, 'input': 'stream=44590', 'name': 'J2'},
              {'id': 2, 'input': 'local', 'name': 'Marc'},
              {'id': 3, 'input': 'local', 'name': 'Source 4'}],
            'streams': [
              {
                'id': 90890,
                'info': {'album': 'Far (Deluxe Version)',
                          'artist': 'Regina Spektor',
                          'img_url': 'http://mediaserver-cont-dc6-1-v4v6.pandora.com/images/public/int/2/1/5/4/093624974512_500W_500H.jpg',
                          'station': 'Regina Spektor Radio',
                          'track': 'Eet'},
                'name': 'Regina Spektor Radio',
                'password': '',
                'station': '4473713754798410236',
                'status': 'playing',
                'type': 'pandora',
                'user': 'example1@micro-nova.com'
              },
              {
                'id': 90891,
                'info': {'details': 'No info available'},
                'name': 'Matt and Kim Radio',
                'password': '',
                'station': '4610303469018478727',
                'status': 'disconnected',
                'type': 'pandora',
                'user': 'example2@micro-nova.com'
              },
              {
                'id': 90892,
                'info': {'details': 'No info available'},
                'name': 'Pink Radio',
                'password': '',
                'station': '4326539910057675260',
                'status': 'disconnected',
                'type': 'pandora',
                'user': 'example3@micro-nova.com'
              },
              {
                'id': 44590,
                'info': {'details': 'No info available'},
                'name': "Jason's "
                        'iPhone',
                'status': 'connected',
                'type': 'shairport'
              },
              {
                'id': 4894,
                'info': {'details': 'No info available'},
                'name': 'Rnay',
                'status': 'disconnected',
                'type': 'shairport'
              }
            ],
            'info': { 'version': '0.0.1'},
            'zones': [
              {'disabled': False, 'id': 0,  'mute': False, 'name': 'Local', 'source_id': 1, 'vol': -35},
              {'disabled': False, 'id': 1,  'mute': False, 'name': 'Office', 'source_id': 0, 'vol': -41},
              {'disabled': False, 'id': 2,  'mute': True,  'name': 'Laundry Room', 'source_id': 0, 'vol': -48},
              {'disabled': False, 'id': 3,  'mute': True,  'name': 'Dining Room', 'source_id': 0, 'vol': -44},
              {'disabled': True,  'id': 4,  'mute': True,  'name': 'BROKEN', 'source_id': 0, 'vol': -50},
              {'disabled': False, 'id': 5,  'mute': True,  'name': 'Guest Bedroom', 'source_id': 0, 'vol': -48},
              {'disabled': False, 'id': 6,  'mute': True,  'name': 'Main Bedroom', 'source_id': 0, 'vol': -40},
              {'disabled': False, 'id': 7,  'mute': True,  'name': 'Main Bathroom', 'source_id': 0, 'vol': -44},
              {'disabled': False, 'id': 8,  'mute': True,  'name': 'Master Bathroom', 'source_id': 0, 'vol': -41},
              {'disabled': False, 'id': 9,  'mute': True,  'name': 'Kitchen High', 'source_id': 0, 'vol': -53},
              {'disabled': False, 'id': 10, 'mute': True,  'name': 'kitchen Low', 'source_id': 0, 'vol': -52},
              {'disabled': False, 'id': 11, 'mute': True,  'name': 'Living Room', 'source_id': 0, 'vol': -46}
            ]
          }
        }
      },
    }

class AppSettings(BaseSettings):
  """ Controller settings """
  mock_ctrl: bool = True
  mock_streams: bool = True
  config_file: str = 'house.json'
  delay_saves: bool = True

class ImageSpec(BaseSettings):
  height: int = Field(120, ge=40, le=300, description="Image height (and width)")
  uri: str = Field(description="url for image beginning with 'http://', 'https://', or 'file://'")
