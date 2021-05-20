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
from typing import List, Set, Dict, Optional, Union
from pydantic import BaseModel, BaseSettings, Field

class Base(BaseModel):
  """ Base class for AmpliPi Models
  id: Per type unique id generated on instance creation
    id is always returned by all API calls.
    It is optional so this calls can be abstract enough to use for creation and returned state
  name: Associated name, not intended to be unique
  """
  id: Optional[int] = Field(description='Unique identifier')
  name: str = Field(description="Friendly name")

class BaseUpdate(BaseModel):
  """ Base class for updates to AmpliPi models
  name: Associated name, updated if necessary
  """
  name: Optional[str] = Field(description="Friendly name")

class Source(Base):
  """ An audio source """
  input: str = Field('', description="""Connected audio source

    * Digital Stream ('stream=SID') where SID is the ID of the connected stream
    * Analog RCA Input ('local') connects to the RCA inputs associated
    * Nothing ('') behind the scenes this is muxed to a digital output
    """)

  def get_stream(self) -> Optional[int]:
    try:
      if 'stream=' in self.input:
        return int(self.input.split('=')[1])
      else:
        return None
    except:
      return None

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return SourceUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'examples': [
        {
          'name': '1',
          'input': 'stream=1009',
        },
        {
          'name': '2',
          'input': '',
        },
        {
          'name': '3',
          'input': 'local',
        },
      ]
    }

class SourceUpdate(BaseUpdate):
  """ Partial reconfiguration of an audio Source """
  input: Optional[str] # 'None', 'local', 'stream=ID' # TODO: add helpers to get stream_id

class SourceUpdate2(SourceUpdate):
  """ Partial reconfiguration of a specific audio Source """
  id : int = Field(ge=0,le=4)

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return SourceUpdate.parse_obj(update)

class Zone(Base):
  """ Audio output to a stereo pair of speakers, typically belonging to a room """
  source_id: int = Field(default=0, ge=0, le=3, description='id of the connected source')
  mute: bool = Field(default=True, description='Set to true if output is muted')
  vol: int = Field(default=-79, ge=-79, le=0, description="Output volume in dB")
  disabled: bool = Field(default=False, description="Set to true if not connected to a speaker")

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return ZoneUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'examples': {
        'Living Room' : {
          "summary": "11",
          "description": "111",
          'value': {
            'name': 'Living Room',
            'source_id': 1,
            'mute' : False,
            'vol':-25,
            'disabled': False,
          }
        },
        'Dining Room' : {
          "summary": "22",
          "description": "222",
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
  source_id: Optional[int]
  mute: Optional[bool]
  vol: Optional[int]
  disabled: Optional[bool]

class ZoneUpdate2(ZoneUpdate):
  """ Reconfiguration of a specific Zone """
  id: int = Field(ge=0,le=35)

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return ZoneUpdate.parse_obj(update)

class Group(Base):
  """ A group of zones that can share the same audio input and be controlled as a group ie. Updstairs.

  Volume, mute, and source_id fields are aggregates of the member zones."""
  source_id: int =  Field(default=0, ge=0, le=3, description='id of the connected source')
  zones: Set[int] = Field(default=[], description='Set of zones that belong to group, a zone can belong to multiple groups.')
  mute: bool = Field(default=True, description='Set to true if all zones are muted')
  vol_delta: int = Field(default=0, ge=-79, le=0, description="Average output volume in dB")

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return GroupUpdate.parse_obj(update)

  class Config:
    schema_extra = {
      'examples': {
        'Add Upstairs Group': {
          'value': {
            'name': 'Upstairs',
            'zones': [1, 2, 3, 4, 5]
          }
        },
        'Add Downstairs Group': {
          'value': {
            'name': 'Downstairs',
            'zones': [6,7,8,9]
          }
        }
      },
    }

class GroupUpdate(BaseUpdate):
  """ Reconfiguration of a Group """
  source_id: Optional[int]
  zones: Optional[List[int]]
  mute: Optional[bool]
  vol_delta: Optional[int]

class GroupUpdate2(GroupUpdate):
  """ Reconfiguration of a specific Group """
  id: int

  def as_update(self):
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
  """)
  # TODO: how to support different stream types
  user: Optional[str] = Field(description="User login")
  password: Optional[str] = Field(description="Password")
  station: Optional[str] = Field(description="Radio station identifier")
  url: Optional[str] = Field(description="Stream url, used for internetradio")
  logo: Optional[str] = Field(description="Icon/Logo url, used for internetradio")
  # generated fields
  # TODO: formalize stream info
  info: Optional[Dict] = Field(description='Additional info about the current audio playing from the stream (generated during playback')
  status: Optional[str] = Field(description="State of the stream")

class StreamUpdate(BaseUpdate):
  """ Reconfiguration of a Stream """
  # TODO: how to support different stream types
  user: Optional[str]
  password: Optional[str]
  station: Optional[str]
  url: Optional[str]
  logo: Optional[str]

class PresetState(BaseModel):
  """ A set of partial configuration changes to make to sources, zones, and groups """
  sources: Optional[List[SourceUpdate2]]
  zones: Optional[List[ZoneUpdate2]]
  groups: Optional[List[GroupUpdate2]]

class Command(BaseModel):
  """ A command to execute on a stream """
  stream_id: int = Field(description="Stream to execute the command on")
  cmd: str = Field(description="Command to execute")

class Preset(Base):
  """ A partial controller configuration the can be loaded on demand.
  In addition to most of the configuration found in Status, this can contain commands as well that configure the state of different streaming services.
  """
  state: PresetState # TODO: should state be optional for a preset?
  commands: Optional[List[Command]] = []
  last_used: Union[int, None] = None

class PresetUpdate(BaseUpdate):
  """ Changes to a current preset

  The contents of state and commands will be completely replaced if populated.
  Merging old and new updates seems too complicated and error prone.
  """
  state: Optional[PresetState]
  commands: Optional[List[Command]]

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

class AppSettings(BaseSettings):
  """ Controller settings """
  mock_ctrl: bool = False
  mock_streams: bool = False
  config_file: str = 'house.json'
  delay_saves: bool = True
