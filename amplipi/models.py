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
from pydantic import BaseModel, BaseSettings

class Base(BaseModel):
  """ Base class for AmpliPi Models
  id: Per type unique id generated on instance creation
    id is always returned by all API calls.
    It is optional so this calls can be abstract enough to use for creation and returned state
  name: Associated name, not intended to be unique
  """
  id: Optional[int]
  name: str

class BaseUpdate(BaseModel):
  """ Base class for updates to AmpliPi models
  name: Associated name, updated if necessary
  """
  name: Optional[str]

class Source(Base):
  """ An audio source
  input: connected audio source
  Options:
  - Digital Stream ('stream=SID') where SID is the ID of the connected stream
  - Analog RCA Input ('local') connects to the RCA inputs associated
  - Nothing ('None') behind the scenes this is muxed to a digital output
  """
  input: str
  # TODO: add status

class SourceUpdate(BaseUpdate):
  input: Optional[str] # 'None', 'local', 'stream=ID' # TODO: add helpers to get stream_id

class SourceUpdate2(SourceUpdate):
  id : int

class Zone(Base):
  source_id: int = 0
  mute: bool = True
  vol: int = -79
  disabled: bool = False

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return ZoneUpdate.parse_obj(update)

class ZoneUpdate(BaseUpdate):
  source_id: Optional[int]
  mute: Optional[bool]
  vol: Optional[int]
  disabled: Optional[bool]

class ZoneUpdate2(ZoneUpdate):
  id: int

class Group(Base):
  source_id: int = 0
  zones: List[int]
  mute: bool = True
  vol_delta: int = 0

  def as_update(self):
    update = self.dict()
    update.pop('id')
    return GroupUpdate.parse_obj(update)

class GroupUpdate(BaseUpdate):
  source_id: Optional[int]
  zones: Optional[List[int]]
  mute: Optional[bool]
  vol_delta: Optional[int]

class GroupUpdate2(GroupUpdate):
  id: int

class Stream(Base):
  type: str
  user: Optional[str]
  password: Optional[str]
  station: Optional[str]
  url: Optional[str]
  logo: Optional[str]
  # generated fields
  info: Optional[Dict] # TODO: formalize stream info
  status: Optional[str]

class PresetState(BaseModel):
  sources: Optional[List[SourceUpdate2]]
  zones: Optional[List[ZoneUpdate2]]
  groups: Optional[List[GroupUpdate2]]

class Command(BaseModel):
  """ A command to execute on a stream
  stream_id: Stream to execute the command on
  cmd: Command to execute
  """
  stream_id: int
  cmd: str

class Preset(Base):
  """ A partial controller configuration the can be loaded on demand.
  In addition to most of the configuration found in Status, this can contain commands as well that configure the state of different streaming services.
  """
  state: PresetState # TODO: should state be optional for a preset?
  commands: Optional[List[Command]]
  last_used: Union[int, None] = None

class PresetUpdate(BaseUpdate):
  state: Optional[PresetState]
  commands: Optional[List[Command]]

class Status(BaseModel):
  """ Full Controller Configuration and Status """
  sources: List[Source]
  zones: List[Zone]
  groups: List[Group]
  streams: List[Stream]
  presets: List[Preset]
  info: Dict[str, Union[str, int, bool]]

class AppSettings(BaseSettings):
  mock_ctrl: bool = False
  mock_streams: bool = False
  config_file: str = 'house.json'
  delay_saves: bool = True
