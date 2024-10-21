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

"""Digital Audio Streams

This module allows you to connect and control configurable network audio sources
such as Pandora, Spotify, and AirPlay. Each digital source is expected to have
a consistent interface.
"""

import os
import sys
from typing import Union, List
import logging

from amplipi import models

from .internet_radio import InternetRadio
from .rca import RCA
from .airplay import AirPlay
from .spotify import Spotify
from .spotify_connect_beta import SpotifyConnect
from .dlna import DLNA
from .pandora import Pandora
from .plexamp import Plexamp
from .aux import Aux
from .file_player import FilePlayer
from .fm_radio import FMRadio
from .lms import LMS
from .bluetooth import Bluetooth
from .media_device import MediaDevice
from .base_streams import *  # pylint: disable=wildcard-import we need to import these so they are accessible

# We use Popen for long running process control this error is not useful:
# pylint: disable=consider-using-with
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

DEBUG = os.environ.get('DEBUG', True)

# TODO: In the future we shpuld replace the rest of this file with a decorator that looks something like the following
# @register_stream('internetradio', [Arg('url', 'url of station', 'string', required: True),...
# you'd apply this decorator to every stream class and in here you could likely just from . import * to register everything
# this decorator could also be used to generate the schema json for the frontends config page (or an equivalent endpoint)

# Simple handling of stream types before we have a type heirarchy
AnyStream = Union[RCA, AirPlay, Spotify, SpotifyConnect, InternetRadio, DLNA, Pandora, Plexamp,
                  Aux, FilePlayer, FMRadio, LMS, Bluetooth, MediaDevice]


def build_stream(stream: models.Stream, mock: bool = False, validate: bool = True) -> AnyStream:
  """ Build a stream from the generic arguments given in stream, discriminated by stream.type

  we are waiting on Pydantic's implemenatation of discriminators to fully integrate streams into our model definitions
  """
  # pylint: disable=too-many-return-statements
  args = stream.dict(exclude_none=True)
  name: str = args.pop('name')
  disabled = args.pop('disabled', False)
  if stream.type == 'rca':
    return RCA(name, args['index'], disabled=disabled, mock=mock)
  if stream.type == 'pandora':
    return Pandora(name, args['user'], args['password'], station=args.get('station', None), disabled=disabled, mock=mock, validate=validate)
  if stream.type in ['shairport', 'airplay']:  # handle older configs
    return AirPlay(name, args.get('ap2', False), disabled=disabled, mock=mock, validate=validate)
  if stream.type == 'spotify':
    return Spotify(name, disabled=disabled, mock=mock, validate=validate)
  if stream.type == 'spotifyconnect':
    return SpotifyConnect(name, disabled=disabled, mock=mock, validate=validate)
  if stream.type == 'dlna':
    return DLNA(name, disabled=disabled, mock=mock)
  if stream.type == 'internetradio':
    return InternetRadio(name, args['url'], args.get('logo'), disabled=disabled, mock=mock, validate=validate)
  if stream.type == 'plexamp':
    return Plexamp(name, args['client_id'], args['token'], disabled=disabled, mock=mock)
  if stream.type == 'aux':
    return Aux(name, disabled=disabled, mock=mock)
  if stream.type == 'fileplayer':
    return FilePlayer(name, args.get('url', None), args.get('temporary', None), args.get('timeout', None), args.get('has_pause', True), disabled=disabled, mock=mock)
  if stream.type == 'fmradio':
    return FMRadio(name, args['freq'], args.get('logo'), disabled=disabled, mock=mock)
  if stream.type == 'lms':
    return LMS(name, args.get('server'), args.get("port"), disabled=disabled, mock=mock)
  elif stream.type == 'bluetooth':
    return Bluetooth(name, disabled=disabled, mock=mock)
  elif stream.type == 'mediadevice':
    return MediaDevice(name, args.get('url'), disabled=disabled, mock=mock)
  raise NotImplementedError(stream.type)


def stream_types_available() -> List[str]:
  """ Returns a list of the available streams on this particular appliance.
  """
  stypes = [RCA, AirPlay, Spotify, SpotifyConnect, InternetRadio, DLNA, Pandora, Plexamp,
            Aux, FilePlayer, LMS, MediaDevice]
  if Bluetooth.is_hw_available():
    stypes.append(Bluetooth)
  if FMRadio.is_hw_available():
    stypes.append(FMRadio)
  # the below line is not type checked because mypy isn't smart enough to see this is a relatively
  # constrained set of types, and instead evaluates this as a `list[type]`
  return [s.stream_type for s in stypes]  # type: ignore
