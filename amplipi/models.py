# type handling, fastapi leverages type checking for performance and easy docs
from typing import List, Optional, Dict
from pydantic import BaseModel

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

class Stream(Base):
  pass # TODO: figure out streams

class PresetState(BaseModel):
  sources: List[Source]
  zones: List[Zone]
  groups: List[Group]

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
  state: PresetState
  cmd: Optional[Command]

class PresetUpdate(BaseUpdate):
  state: Optional[PresetState]
  cmd: Optional[Command]

class Status(Base):
  """ Full Controller Configuration and Status """
  sources: List[Source]
  zones: List[Zone]
  groups: List[Group]
  streams: List[Stream]
  presets: List[Preset]
  version: str
