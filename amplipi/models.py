# AmpliPi Home Audio
# Copyright (C) 2022 MicroNova LLC
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
from functools import lru_cache
from typing import List, Dict, Optional, Union, Set
from types import SimpleNamespace
from enum import Enum

# pylint: disable=no-name-in-module
from pydantic import BaseSettings, BaseModel, Field

# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring

MIN_VOL_F = 0.0
""" Min volume for slider bar. Will be mapped to dB. """

MAX_VOL_F = 1.0
""" Max volume for slider bar. Will be mapped to dB. """

MIN_VOL_DB = -80
""" Min volume in dB. -80 is special and is actually -90 dB (mute). """

MAX_VOL_DB = 0
""" Max volume in dB. """

MIN_DB_RANGE = 20
""" Smallest allowed difference between a zone's vol_max and vol_min """

def pcnt2Vol(pcnt: float) -> int:
  """ Convert a percent to volume in dB """
  assert MIN_VOL_F <= pcnt <= MAX_VOL_F
  return round(pcnt * (MAX_VOL_DB - MIN_VOL_DB) + MIN_VOL_DB)

class fields(SimpleNamespace):
  """ AmpliPi's field types """
  ID = Field(description='Unique identifier')
  Name = Field(description='Friendly name')
  SourceId = Field(ge=0, le=3, description='id of the connected source')
  ZoneId = Field(ge=0, le=35)
  Mute = Field(description='Set to true if output is muted')
  Volume = Field(ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Output volume in dB')
  VolumeF = Field(ge=MIN_VOL_F, le=MAX_VOL_F, description='Output volume as a floating-point scalar from 0.0 to 1.0 representing MIN_VOL_DB to MAX_VOL_DB')
  VolumeMin = Field(ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Min output volume in dB')
  VolumeMax = Field(ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Max output volume in dB')
  GroupMute = Field(description='Set to true if output is all zones muted')
  GroupVolume = Field(ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Average output volume')
  GroupVolumeF = Field(ge=MIN_VOL_F, le=MAX_VOL_F, description='Average output volume as a floating-point number')
  Disabled = Field(description='Set to true if not connected to a speaker')
  Zones = Field(description='Set of zone ids belonging to a group')
  Groups = Field(description='List of group ids')
  AudioInput = Field('', description="""Connected audio source

  * Digital Stream ('stream=SID') where SID is the ID of the connected stream (rca inputs are now just the RCA stream type)
  * Nothing ('') behind the scenes this is muxed to a digital output
  """)

class fields_w_default(SimpleNamespace):
  """ AmpliPi's field types that need a default value

  These are needed because there is ambiguity where an optional field has a default value
  """
  # TODO: less duplication
  SourceId = Field(default=0, ge=0, le=3, description='id of the connected source')
  Mute = Field(default=True, description='Set to true if output is muted')
  Volume = Field(default=MIN_VOL_DB, ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Output volume in dB')
  VolumeF = Field(default=MIN_VOL_F, ge=MIN_VOL_F, le=MAX_VOL_F, description='Output volume as a floating-point scalar from 0.0 to 1.0 representing MIN_VOL_DB to MAX_VOL_DB')
  VolumeMin = Field(default=MIN_VOL_DB, ge=MIN_VOL_DB, le=MAX_VOL_DB,
                    description='Min output volume in dB')
  VolumeMax = Field(default=MAX_VOL_DB, ge=MIN_VOL_DB, le=MAX_VOL_DB,
                    description='Max output volume in dB')
  GroupMute = Field(default=True, description='Set to true if output is all zones muted')
  GroupVolume = Field(default=MIN_VOL_F, ge=MIN_VOL_F, le=MAX_VOL_F, description='Average output volume')
  GroupVolumeF = Field(default=MIN_VOL_F, ge=MIN_VOL_F, le=MAX_VOL_F, description='Average output volume as a floating-point number')
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
  name: str
  state: str # paused, playing, stopped, unknown, loading ???
  artist: Optional[str]
  track: Optional[str]
  album: Optional[str]
  station: Optional[str] # name of radio station
  img_url: Optional[str]
  supported_cmds: List[str] = []

class Source(Base):
  """ An audio source """
  input: str = fields.AudioInput
  info: Optional[SourceInfo] = Field(description='Additional info about the current audio playing from the stream (generated during playback)')

  def get_stream(self) -> Optional[int]:
    """ Get a source's connected stream if any """
    try:
      sinput = str(self.input)
      if sinput.startswith('stream='):
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
            'input': 'stream=1004',
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
            'input': 'stream=999',
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
  input: Optional[str] # 'None', 'rca=ID', 'stream=ID' # TODO: add helpers to get stream_id

  class Config:
    schema_extra = {
      'examples': {
        'Update Input to RCA Input 2': {
          'value': {'input': 'stream=997'}
        },
        'Update name': {
          'value': {'name': 'J2'}
        },
        'Update Input to Matt and Kim Radio': {
          'value': {'input': 'stream=1004'}
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
  vol_f: float = fields_w_default.VolumeF
  vol_min: int = fields_w_default.VolumeMin
  vol_max: int = fields_w_default.VolumeMax
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
            'vol': pcnt2Vol(0.69),
            'vol_f': 0.69,
            'vol_min': MIN_VOL_DB,
            'vol_max': MAX_VOL_DB,
            'disabled': False,
          }
        },
        'Dining Room' : {
          'value': {
            'name': 'Dining Room',
            'source_id': 2,
            'mute' : True,
            'vol': pcnt2Vol(0.19),
            'vol_f': 0.19,
            'vol_min': int(0.1 * (MAX_VOL_DB + MIN_VOL_DB)),
            'vol_max': int(0.8 * (MAX_VOL_DB + MIN_VOL_DB)),
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
  vol_f: Optional[float] = fields.VolumeF
  vol_min: Optional[int] = fields.VolumeMin
  vol_max: Optional[int] = fields.VolumeMax
  disabled: Optional[bool] = fields.Disabled

  class Config:
    schema_extra = {
      'examples': {
        'Change name': {
          'value': {
            'name':
            'Bedroom'
          }
        },
        'Change audio source': {
          'value': {
            'source_id': 3
          }
        },
        'Change volume relative to min/max volume': {
          'value': {
            'vol': 0.44
          }
        },
        'Change volume in absolute decibels': {
          'value': {
            'vol': pcnt2Vol(0.44)
          }
        },
        'Mute': {
          'value': {
            'mute': True
          }
        },
        'Change max volume': {
          'value': {
            'vol_max': int(0.8 * MAX_VOL_DB)
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

class MultiZoneUpdate(BaseModel):
  """ Reconfiguration of multiple zones specified by zone_ids and group_ids """

  zones: Optional[List[int]] = fields.Zones
  groups: Optional[List[int]] = fields.Groups
  update: ZoneUpdate

  class Config:
    schema_extra = {
      'examples': {
        'Connect all zones to source 1': {
          'value': {
            'zones': [0,1,2,3,4,5],
            'update': { 'source_id': 0 }
          }
        },
        'Change the relative volume on all zones': {
          'value': {
            'zones': [0,1,2,3,4,5],
            'update': { 'vol_f': 0.5, "mute": False }
          }
        },
      },
    }

class Group(Base):
  """ A group of zones that can share the same audio input and be controlled as a group ie. Upstairs.

  Volume, mute, and source_id fields are aggregates of the member zones."""
  source_id: Optional[int] = fields.SourceId
  zones: List[int] = fields.Zones # should be a set, but JSON doesn't have native sets
  mute: Optional[bool] = fields.GroupMute
  vol_delta: Optional[int] = fields.GroupVolume
  vol_f: Optional[float] = fields.GroupVolumeF

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
            'vol_delta': pcnt2Vol(0.19),
            'vol_f': 0.19,
          }
        },
        'Downstairs Group': {
          'value': {
            'id': 102,
            'name': 'Downstairs',
            'zones': [6,7,8,9],
            'vol_delta': pcnt2Vol(0.63),
            'vol_f': 0.63,
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
  vol_f: Optional[float] = fields.GroupVolumeF

  class Config:
    schema_extra = {
      'examples': {
        'Rezone group': {
          'value': {
            'name': 'Upstairs',
            'zones': [3,4,5]
          }
        },
        'Change name': {
          'value': {
            'name': 'Upstairs'
          }
        },
        'Change audio source': {
          'value': {
            'source_id': 3
          }
        },
        "Set volume relative to each zone's min/max volume": {
          'value': {
            'vol_f': 0.44
          }
        },
        'Set volume of each zone in absolute decibels': {
          'value': {
            'vol_delta': pcnt2Vol(0.44)
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
  """ Digital stream such as Pandora, AirPlay or Spotify """
  type: str = Field(description="""stream type

  * pandora
  * airplay
  * dlna
  * internetradio
  * spotify
  * plexamp
  * file
  * fmradio
  * lms
  * rca
  """)
  # TODO: how to support different stream types
  user: Optional[str] = Field(description='User login')
  password: Optional[str] = Field(description='Password')
  station: Optional[str] = Field(description='Radio station identifier')
  url: Optional[str] = Field(description='Stream url, used for internetradio and file')
  logo: Optional[str] = Field(description='Icon/Logo url, used for internetradio')
  freq: Optional[str] = Field(description='FM Frequency (MHz), used for fmradio')
  client_id: Optional[str] = Field(description='Plexamp client_id, becomes "identifier" in server.json')
  token: Optional[str] = Field(description='Plexamp token for server.json')
  server: Optional[str] = Field(description='Server url')
  index: Optional[int] = Field(description='RCA index')
  disabled: Optional[bool] = Field(description="Soft disable use of this stream. It won't be shown as a selectable option")

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
        'Add Spotify Connect': {
          'value': {
            'name': 'AmpliPi',
            'type': 'spotify'
          }
        },
        'Add AirPlay': {
          'value': {
            'name': 'AmpliPi',
            'type': 'airplay'
          }
        },
        "Play single file or announcement" : {
          'value': {
            'name': 'Play NASA Announcement',
            'type': 'fileplayer',
            'url': 'https://www.nasa.gov/mp3/640149main_Computers%20are%20in%20Control.mp3'
          }
        },
        'Add FM Radio Station': {
          'value': {
            'name': 'WXYZ',
            'type': 'fmradio',
            'freq': '100.1',
            'logo': 'static/imgs/fmradio.png'
          }
        },
        'Add LMS Client connected specifically to amplipi': {
          'value': {
            'name': 'Test',
            'server': 'localhost',
            'type': 'lms',
          }
        },
        'Add LMS Client': {
          'value': {
            'name': 'Family',
            'type': 'lms',
          }
        }
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
        'AirPlay (connected)': {
          'value': {
            'id': 44590,
            'info': {'details': 'No info available'},
            'name': "Jason's iPhone",
            'status': 'connected',
            'type': 'airplay'
          }
        },
        'AirPlay (disconnected)': {
          'value': {
            'id': 4894,
            'info': {'details': 'No info available'},
            'name': 'Rnay',
            'status': 'disconnected',
            'type': 'airplay'
          }
        },
      }
    }

@lru_cache(1)
def optional_stream_fields() -> Set:
  """ Extra fields that can be preset in a stream """
  model = Stream(id=0, name='', type='fake').dict()
  return { k for k, v in model.items() if v is None }

class StreamUpdate(BaseUpdate):
  """ Reconfiguration of a Stream """
  # TODO: how to support different stream types
  user: Optional[str]
  password: Optional[str]
  station: Optional[str]
  url: Optional[str]
  logo: Optional[str]
  freq: Optional[str]
  server: Optional[str]

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
  PREV = 'prev'
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

class Announcement(BaseModel):
  """ A PA-like Announcement
  IF no zones or groups are specified, all available zones are used
  """
  media : str = Field(description="URL to media to play as the announcement")
  vol: Optional[int] = Field(default=None, ge=MIN_VOL_DB, le=MAX_VOL_DB, description='Output volume in dB, overrides vol_f')
  vol_f: float = Field(default=0.5, ge=MIN_VOL_F, le=MAX_VOL_F, description="Output Volume (float)")
  source_id: int = Field(default=3, ge=0, le=3, description='Source to announce with')
  zones: Optional[List[int]] = fields.Zones
  groups: Optional[List[int]] = fields.Groups

  class Config:
    schema_extra = {
      'examples': {
        'Make NASA Announcement': {
          'value': {
            'media': 'https://www.nasa.gov/mp3/640149main_Computers%20are%20in%20Control.mp3',
          }
        }
      }
    }

class FirmwareInfo(BaseModel):
  """ Firmware Info for an AmpliPi controller or expansion unit's preamp board """
  version: str = Field(default='unknown', description="preamp firmware version")
  git_hash: str = Field(default='unknown', description="short git hash of firmware")
  git_dirty: bool = Field(default=False, description="True if local changes were made. Used for development.")

class Info(BaseModel):
  """ AmpliPi System information """
  version: str = Field(description="software version")
  config_file: str = Field(default='unknown', description='config file location')
  mock_ctrl: bool = Field(default=False, description='Is the controller being mocked? Indicates AmpliPi hardware is not connected')
  mock_streams: bool = Field(default=False, description='Are streams being faked? Used for testing.')
  online: bool = Field(default=False, description='can the system connect to the internet?')
  latest_release: str = Field(default='unknown', description='Latest software release available from GitHub')
  fw: List[FirmwareInfo] = Field(default=[], description='firmware information for each connected controller or expansion unit')

  class Config:
    schema_extra = {
      'examples': {
        "System info": {
          'value': {
            'config_file': 'house.json',
            'version': '0.1.8',
            'mock_ctrl': False,
            'mock_streams': False,
            'online': True,
            'latest_release': '0.1.8',
            'fw': [
              {
                "version": "1.6",
                "git_hash": "de0f8eb",
                "git_dirty": False,
              }
            ]
          }
        }
      }
    }

class Status(BaseModel):
  """ Full Controller Configuration and Status """
  sources: List[Source] = [Source(id=i, name=str(i)) for i in range(4)]
  zones: List[Zone] = [Zone(id=i, name=f'Zone {i + 1}') for i in range(6)]
  groups: List[Group] = []
  streams: List[Stream] = [Stream(id=996+i, name=f'Input {i + 1}', type='rca', index=i) for i in range(4)]
  presets: List[Preset] = []
  info: Optional[Info]

  class Config:
    schema_extra = {
      'examples': {
        "Status of Jason's AmpliPi": {
          'value': {
            'groups': [ { 'id': 100,
                          'mute': True,
                          'name': 'Upstairs',
                          'vol_delta': -39,
                          'vol_f': 0.51,
                          'zones': [0, 1, 2, 3, 4, 5, 6, 7, 11, 16]},
                        { 'id': 102,
                          'mute': True,
                          'name': 'Outside',
                          'source_id': 1,
                          'vol_delta': -41,
                          'vol_f': 0.4909090909090909,
                          'zones': [9, 10]},
                        { 'id': 103,
                          'mute': True,
                          'name': 'Offices',
                          'vol_delta': -54,
                          'vol_f': 0.33,
                          'zones': [0, 7]},
                        { 'id': 104,
                          'mute': True,
                          'name': 'Downstairs',
                          'source_id': 1,
                          'vol_delta': -57,
                          'vol_f': 0.28500000000000003,
                          'zones': [12, 13, 14, 15, 17]},
                        { 'id': 105,
                          'mute': True,
                          'name': 'Main Unit',
                          'vol_delta': -39,
                          'vol_f': 0.51,
                          'zones': [0, 1, 2, 3, 4, 5]},
                        { 'id': 106,
                          'mute': True,
                          'name': 'Expander 1 (HV)',
                          'vol_delta': -39,
                          'vol_f': 0.515,
                          'zones': [6, 7, 8, 9, 10, 11]},
                        { 'id': 107,
                          'mute': True,
                          'name': 'Expander 2',
                          'vol_delta': -58,
                          'vol_f': 0.275,
                          'zones': [12, 13, 14, 15, 16, 17]}
                      ],
            'info': { 'config_file': 'house.json',
                      'fw': [ { 'git_dirty': False,
                                'git_hash': 'de0f8eb',
                                'version': '1.6'},
                              { 'git_dirty': False,
                                'git_hash': 'de0f8eb',
                                'version': '1.6'},
                              { 'git_dirty': False,
                                'git_hash': 'de0f8eb',
                                'version': '1.6'}],
                      'latest_release': '0.1.9',
                      'mock_ctrl': False,
                      'mock_streams': False,
                      'online': True,
                      'version': '0.1.9'},
            'presets': [ { 'id': 10000,
                          'last_used': 1658242203,
                          'name': 'Mute All',
                          'state': { 'zones': [ {'id': 0, 'mute': True},
                                                {'id': 1, 'mute': True},
                                                {'id': 2, 'mute': True},
                                                {'id': 3, 'mute': True},
                                                {'id': 4, 'mute': True},
                                                {'id': 5, 'mute': True},
                                                {'id': 6, 'mute': True},
                                                {'id': 7, 'mute': True},
                                                {'id': 8, 'mute': True},
                                                {'id': 9, 'mute': True},
                                                {'id': 10, 'mute': True},
                                                {'id': 11, 'mute': True},
                                                {'id': 12, 'mute': True},
                                                {'id': 13, 'mute': True},
                                                {'id': 14, 'mute': True},
                                                {'id': 15, 'mute': True},
                                                {'id': 16, 'mute': True},
                                                {'id': 17, 'mute': True}]}}
                        ],
            'sources': [ { 'id': 0,
                          'info': { 'img_url': 'static/imgs/disconnected.png',
                                    'name': 'None',
                                    'state': 'stopped',
                                    'supported_cmds': []},
                          'input': '',
                          'name': 'TV'},
                        { 'id': 1,
                          'info': { 'img_url': 'static/imgs/disconnected.png',
                                    'name': 'None',
                                    'state': 'stopped',
                                    'supported_cmds': []},
                          'input': '',
                          'name': 'Record Player'},
                        { 'id': 2,
                          'info': { 'album': 'Charleston Butterfly',
                                    'artist': 'Parov Stelar',
                                    'img_url': 'http://mediaserver-cont-sv5-2-v4v6.pandora.com/images/00/4c/b7/12/d64a4ffe82251fcc9c44555c/1080W_1080H.jpg',
                                    'name': 'Blackmill Radio - pandora',
                                    'state': 'playing',
                                    'station': 'Blackmill Radio',
                                    'supported_cmds': [ 'play', 'pause', 'stop', 'next',
                                                        'love', 'ban', 'shelve'],
                                    'track': 'Chambermaid Swing'},
                          'input': 'stream=1006',
                          'name': 'Input 3'},
                        { 'id': 3,
                          'info': { 'album': 'Joshua Bell, Romance of the Violin',
                                    'artist': 'Fryderyk Chopin',
                                    'img_url': 'http://cont.p-cdn.us/images/e9/cc/f2/8e/890e4e5e9940c98ba864aaee/1080W_1080H.jpg',
                                    'name': 'Classical - pandora',
                                    'state': 'playing',
                                    'station': 'Antonio Vivaldi Radio',
                                    'supported_cmds': [ 'play', 'pause', 'stop', 'next',
                                                        'love', 'ban', 'shelve'],
                                    'track': 'Nocturne For Piano In C Sharp Minor, Kk '
                                              'Anh.ia/6'},
                          'input': 'stream=1005',
                          'name': 'Input 4'}],
            'streams': [ { 'id': 1000,
                          'logo': 'https://somafm.com/img3/groovesalad-400.jpg',
                          'name': 'Groove Salad',
                          'type': 'internetradio',
                          'url': 'http://ice6.somafm.com/groovesalad-32-aac'},
                        {'id': 1001, 'name': "Jason's House", 'type': 'airplay'},
                        {'id': 1002, 'name': 'Jasons House', 'type': 'spotify'},
                        {'id': 1003, 'name': "Jason's House", 'type': 'dlna'},
                        { 'id': 1004,
                          'name': 'Matt and Kim Radio',
                          'password': '',
                          'station': '135242131387190035',
                          'type': 'pandora',
                          'user': 'example@micro-nova.com'},
                        { 'id': 1005,
                          'name': 'Classical',
                          'password': '',
                          'station': '134892486689565953',
                          'type': 'pandora',
                          'user': 'example@micro-nova.com'},
                        { 'id': 1006,
                          'name': 'Blackmill Radio',
                          'password': '',
                          'station': '91717963601693449',
                          'type': 'pandora',
                          'user': 'example@micro-nova.com'},
                        { 'id': 1007,
                          'logo': 'http://www.beatlesradio.com/content/images/thumbs/0000587.gif',
                          'name': 'Beatles Radio',
                          'type': 'internetradio',
                          'url': 'http://www.beatlesradio.com:8000/stream/1/'}],
            'zones': [ { 'disabled': False,
                        'id': 0,
                        'mute': True,
                        'name': 'Software Office',
                        'source_id': 2,
                        'vol': -56,
                        'vol_f': 0.28,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 1,
                        'mute': True,
                        'name': 'Upstairs Living Room',
                        'source_id': 3,
                        'vol': -49,
                        'vol_f': 0.42,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 2,
                        'mute': True,
                        'name': 'Upstairs Dining',
                        'source_id': 0,
                        'vol': -66,
                        'vol_f': 0.08,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 3,
                        'mute': True,
                        'name': 'Upstairs Laundry',
                        'source_id': 0,
                        'vol': -66,
                        'vol_f': 0.08,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 4,
                        'mute': True,
                        'name': 'Upstairs Kitchen High',
                        'source_id': 0,
                        'vol': -45,
                        'vol_f': 0.5,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 5,
                        'mute': True,
                        'name': 'Upstairs Master Bath',
                        'source_id': 0,
                        'vol': -23,
                        'vol_f': 0.94,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 6,
                        'mute': True,
                        'name': 'Upstairs Kitchen Low HV',
                        'source_id': 0,
                        'vol': -66,
                        'vol_f': 0.1,
                        'vol_max': -30,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 7,
                        'mute': True,
                        'name': 'Hardware Office HV',
                        'source_id': 0,
                        'vol': -51,
                        'vol_f': 0.38,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 8,
                        'mute': True,
                        'name': 'Basement Workshop HV',
                        'source_id': 0,
                        'vol': -13,
                        'vol_f': 0.95,
                        'vol_max': -10,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 9,
                        'mute': True,
                        'name': 'Screened Room HV',
                        'source_id': 1,
                        'vol': -43,
                        'vol_f': 0.4909090909090909,
                        'vol_max': -15,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 10,
                        'mute': True,
                        'name': 'Upstairs Deck Living HV',
                        'source_id': 1,
                        'vol': -43,
                        'vol_f': 0.4909090909090909,
                        'vol_max': -15,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 11,
                        'mute': True,
                        'name': 'Upstairs Main Bedroom HV',
                        'source_id': 0,
                        'vol': -66,
                        'vol_f': 0.08,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 12,
                        'mute': True,
                        'name': 'Downstairs Living Room',
                        'source_id': 1,
                        'vol': -48,
                        'vol_f': 0.44,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 13,
                        'mute': True,
                        'name': 'Downstairs Dining',
                        'source_id': 1,
                        'vol': -48,
                        'vol_f': 0.44,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 14,
                        'mute': True,
                        'name': 'Downstairs Bath',
                        'source_id': 1,
                        'vol': -64,
                        'vol_f': 0.12,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 15,
                        'mute': True,
                        'name': 'Downstairs Laundry',
                        'source_id': 1,
                        'vol': -48,
                        'vol_f': 0.44,
                        'vol_max': -20,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 16,
                        'mute': True,
                        'name': 'Upstairs Main Bath',
                        'source_id': 0,
                        'vol': -66,
                        'vol_f': 0.1,
                        'vol_max': -30,
                        'vol_min': -70},
                      { 'disabled': False,
                        'id': 17,
                        'mute': True,
                        'name': 'Downstairs Bedroom',
                        'source_id': 1,
                        'vol': -52,
                        'vol_f': 0.45,
                        'vol_max': -30,
                        'vol_min': -70}]}

          }
        }
      }

class AppSettings(BaseSettings):
  """ Controller settings """
  mock_ctrl: bool = True
  mock_streams: bool = True
  config_file: str = 'house.json'
  delay_saves: bool = True
