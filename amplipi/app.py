#!/usr/bin/python3

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

"""AmpliPi Webapp

This serves the amplipi webpp and underlying rest api, that it uses.
The FastAPI/Starlette web framework is used to simplify the web plumbing.
"""

import argparse

DEBUG_API = False

import os

# type handling, fastapi leverages type checking for performance and easy docs
from typing import List, Dict, Tuple, Set, Any, Optional, Callable, Union, TYPE_CHECKING, get_type_hints
from enum import Enum
from types import SimpleNamespace

import urllib.request # For custom album art size
from functools import lru_cache
import asyncio
import json
import yaml
from subprocess import Popen
from time import sleep

from PIL import Image # For custom album art size

# web framework
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Path
from fastapi.openapi.utils import get_openapi # docs
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute, APIRouter
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

# mdns service advertisement
import netifaces as ni
from socket import gethostname, inet_aton
from zeroconf import IPVersion, ServiceInfo, Zeroconf
from multiprocessing import Queue

# amplipi
import amplipi.utils as utils
import amplipi.models as models
from amplipi.ctrl import Api, ApiResponse, ApiCode, RCAs # we don't import ctrl here to avoid naming ambiguity with a ctrl variable

# start in the web directory
TEMPLATE_DIR = os.path.abspath('web/templates')
STATIC_DIR = os.path.abspath('web/static')
GENERATED_DIR = os.path.abspath('web/generated')

app = FastAPI(openapi_url=None, redoc_url=None,) # we host docs using rapidoc instead via a custom endpoint, so the default endpoints need to be disabled
templates = Jinja2Templates(TEMPLATE_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# This will get generated as a tmpfs on AmpliPi,
# but won't exist if testing on another machine.
os.makedirs(GENERATED_DIR, exist_ok=True)
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated") # TODO: make this register as a dynamic folder???


class SimplifyingRouter(APIRouter):
  """
  Overrides the route decorator logic to:
  - to use the annotated return type as the `response_model` if unspecified.
  - always exclude unset fields (this makes so much more sense!)
  """
  if not TYPE_CHECKING:  # pragma: no branch
    def add_api_route(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
      if kwargs.get("response_model") is None:
        kwargs["response_model"] = get_type_hints(endpoint).get("return")
      kwargs["response_model_exclude_none"] = True
      return super().add_api_route(path, endpoint, **kwargs)

# Helper functions
def unused_groups(ctrl: Api, src: int) -> Dict[int, str]:
  """ Get groups that are not connected to src """
  groups = ctrl.status.groups
  return {g.id : g.name for g in groups if g.source_id != src and g.id  is not None}

def unused_zones(ctrl: Api, src: int) -> Dict[int, str]:
  """ Get zones that are not conencted to src """
  zones = ctrl.status.zones
  return {z.id : z.name for z in zones if z.source_id != src and z.id is not None and not z.disabled}

def ungrouped_zones(ctrl: Api, src: int) -> List[models.Zone]:
  """ Get zones that are connected to src, but don't belong to a full group """
  zones = ctrl.status.zones
  groups = ctrl.status.groups
  # get all of the zones that belong to this sources groups
  grouped_zones: Set[int] = set()
  for group in groups:
    if group.source_id == src:
      grouped_zones = grouped_zones.union(group.zones)
  # get all of the zones connected to this soource
  source_zones = {z.id for z in zones if z.source_id == src}
  # return all of the zones connected to this source that aren't in a group
  ungrouped_zones_ = source_zones.difference(grouped_zones)
  return [zones[z] for z in ungrouped_zones_ if z is not None and not zones[z].disabled]

# add a default controller (this is overriden below in create_app)
# TODO: this get_ctrl Singleton needs to be removed and the API converted to be instantiated by a class with ctrl state
@lru_cache(1) # Api controller should only be instantiated once (we clear the cache with get_ctr.cache_clear() after settings object is configured)
def get_ctrl() -> Api:
  """ Get the controller
  Makes a single instance of the controller to avoid duplicates (Singleton pattern)
  """
  return Api(models.AppSettings())

class params(SimpleNamespace):
  """ Describe standard path ID's for each api type """
  # pylint: disable=too-few-public-methods
  # pylint: disable=invalid-name
  SourceID = Path(..., ge=0, le=3, description="Source ID")
  ZoneID = Path(..., ge=0, le=35, description="Zone ID")
  GroupID = Path(..., ge=0, description="Stream ID")
  StreamID = Path(..., ge=0, description="Stream ID")
  StreamCommand = Path(..., description="Stream Command")
  PresetID = Path(..., ge=0, description="Preset ID")
  StationID = Path(..., ge=0, title="Pandora Station ID", description="Number found on the end of a pandora url while playing the station, ie 4610303469018478727 in https://www.pandora.com/station/play/4610303469018478727")
  ImageHeight = Path(..., ge=1, le=500, description="Image Height in pixels")

api = SimplifyingRouter()

@api.get('/api', tags=['status'])
def get_status(ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Get the system status and configuration """
  return ctrl.get_state()

@api.post('/api/load', tags=['status'])
def load_config(config: models.Status, ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Load a new configuration (and return the configuration loaded). This will overwrite the current configuration so it is advised to save the previous config from. """
  ctrl.reinit(settings=ctrl._settings, change_notifier=notify_on_change, config=config)
  return ctrl.get_state()

@api.post('/api/factory_reset', tags=['status'])
def load_factory_config(ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Load the "factory" configuration (and return the configuration loaded).
  This will reset all zone names and streams back to their original configuration.
  We recommend downloading the current configuration beforehand.
  """
  return load_config(models.Status(**ctrl.DEFAULT_CONFIG), ctrl)

@api.post('/api/reset', tags=['status'])
def reset(ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Reload the current configuration, resetting the firmware in the process. """
  ctrl.reinit(settings=ctrl._settings, change_notifier=notify_on_change)
  return ctrl.get_state()

@api.post('/api/reboot', tags=['status'],
  response_class=Response,
  responses = {
      200: {}
  }
)
def reboot():
  """ Restart the OS and all of the AmpliPi services.

  """
  # preemptively save the state (just in case the shutdown procedure doesn't invoke a save)
  get_ctrl().save()
  # start the restart, and return immediately (hopefully before the restart process begins)
  Popen('sleep 1 && sudo systemctl reboot', shell=True)

@api.post('/api/shutdown', tags=['status'],
  response_class=Response,
  responses = {
      200: {}
  }
)
def shutdown():
  """ Shutdown AmpliPi and its OS.

  This allows for a clean shutdown before pulling the power plug.
  """
  # preemptively save the state (just in case the shutdown procedure doesn't invoke a save)
  get_ctrl().save()
  # start the shutdown process and returning immediately (hopeully before the shutdown process begins)
  Popen('sleep 1 && sudo systemctl poweroff', shell=True)


subscribers: Dict[int, 'Queue[models.Status]'] = {}
def notify_on_change(status: models.Status) -> None:
  """ Notify subscribers that something has changed """
  for msg_que in subscribers.values():
    msg_que.put(status)

# @api.get('/api/subscribe') # TODO: uncomment this to add SSE Support and properly document it
async def subscribe(req: Request):
  """ Subscribe to SSE events """
  msg_que: Queue = Queue(3)
  next_sub = max(subscribers.keys(), default=0) + 1
  subscribers[next_sub] = msg_que
  async def stream():
    try:
      while True:
        if await req.is_disconnected():
          print('disconnected')
          break
        if not msg_que.empty():
          msg = msg_que.get()
          yield msg
        await asyncio.sleep(0.2)
      print(f"Disconnected from client {req.client}")
    except asyncio.CancelledError as exc:
      print(f"Disconnected from client (via refresh/close) {req.client}")
      # Do any other cleanup, if any
      raise exc
  return EventSourceResponse(stream())

def code_response(ctrl: Api, resp: Union[ApiResponse, models.BaseModel]):
  """ Convert amplipi.ctrl.Api responses to json/http responses """
  if isinstance(resp, ApiResponse):
    if resp.code == ApiCode.OK:
      # general commands return None to indicate success
      return ctrl.get_state()
    print(f"Error: {resp.msg}")
    # TODO: refine error codes based on error message
    raise HTTPException(404, resp.msg)
  return resp

# sources
@api.get('/api/sources', tags=['source'])
def get_sources(ctrl: Api = Depends(get_ctrl)) -> Dict[str, List[models.Source]]:
  """ Get all sources """
  return {'sources' : ctrl.get_state().sources}

@api.get('/api/sources/{sid}', tags=['source'])
def get_source(ctrl: Api = Depends(get_ctrl), sid: int = params.SourceID) -> models.Source:
  """ Get Source with id=**sid** """
  # TODO: add get_X capabilities to underlying API?
  sources = ctrl.get_state().sources
  return sources[sid]

@api.patch('/api/sources/{sid}', tags=['source'])
def set_source(update: models.SourceUpdate, ctrl: Api = Depends(get_ctrl), sid: int = params.SourceID) -> models.Status:
  """ Update a source's configuration (source=**sid**) """
  if update.input == 'local':
    # correct older api requests to use RCA inputs as a stream
    valid_update = update.copy()
    valid_update.input = f'stream={RCAs[sid]}'
    print(f'correcting deprecated use of RCA inputs from {update} to {valid_update}')
  return code_response(ctrl, ctrl.set_source(sid, update))

@api.get('/api/sources/{sid}/image/{height}', tags=['source'],
  # Manually specify a possible response
  # see https://github.com/tiangolo/fastapi/issues/3258
  response_class=Response,
  responses = {
      200: {
          "content": {"image/jpg": {}}
      }
  },
)
async def get_image(ctrl: Api = Depends(get_ctrl), sid: int = params.SourceID, height: int = params.ImageHeight):
  """ Get a square jpeg image representing the current media playing on source @sid

  This was added to support low power touch panels """
  width = height # square image
  source_info = ctrl.status.sources[sid].info
  if source_info is None or source_info.img_url is None:
    uri = 'static/imgs/disconnected.png'
  else:
    uri = source_info.img_url
  if uri.startswith('static/'):
    # for files we need to convert from webserver url to internal file url
    uri = uri.replace('static/', STATIC_DIR + '/')
    uri = uri.replace('rca_inputs.svg', 'rca_inputs.jpg')  # pillow can't handle svg files for our use case

  # TODO: writing images to /tmp adds file system pressure
  # we should write only a couple to RAM disk instead and manage a small amount of garbage collection
  img_tmp = f'/tmp/{os.path.basename(uri)}'
  img_tmp_jpg = f'{img_tmp}-{height}x{width}.jpg'

  if not os.path.exists(img_tmp_jpg):
    is_file = os.path.exists(uri)
    if is_file:
      img_tmp = uri
    else:
      img_tmp, _ = urllib.request.urlretrieve(uri, img_tmp)
    size = height, width
    img = Image.open(img_tmp)
    img.thumbnail(size)
    img = img.convert(mode="RGB")
    img.save(img_tmp_jpg)
    if not is_file:
      # remove temporary downloads
      os.remove(img_tmp)

  # encode the filename of the image for client side caching/verification
  name = os.path.basename(uri) + '.jpg'
  return FileResponse(img_tmp_jpg, media_type='image/jpg', filename=name)

# zones

@api.get('/api/zones', tags=['zone'])
def get_zones(ctrl: Api = Depends(get_ctrl)) -> Dict[str, List[models.Zone]]:
  """ Get all zones """
  return {'zones': ctrl.get_state().zones}

@api.get('/api/zones/{zid}', tags=['zone'])
def get_zone(ctrl: Api = Depends(get_ctrl), zid: int = params.ZoneID) -> models.Zone:
  """ Get Zone with id=**zid** """
  zones = ctrl.get_state().zones
  if 0 <= zid < len(zones):
    return zones[zid]
  raise HTTPException(404, f'zone {zid} not found')

@api.patch('/api/zones/{zid}', tags=['zone'])
def set_zone(zone: models.ZoneUpdate, ctrl: Api = Depends(get_ctrl), zid: int = params.ZoneID) -> models.Status:
  """ Update a zone's configuration (zone=**zid**) """
  return code_response(ctrl, ctrl.set_zone(zid, zone))

@api.patch('/api/zones', tags=['zone'])
def set_zones(multi_update: models.MultiZoneUpdate, ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Update a bunch of zones (and groups) with the same configuration changes """
  return code_response(ctrl, ctrl.set_zones(multi_update))

# groups

@api.post('/api/group', tags=['group'])
def create_group(group: models.Group, ctrl: Api = Depends(get_ctrl)) -> models.Group:
  """ Create a new grouping of zones """
  # TODO: add named example group
  return code_response(ctrl, ctrl.create_group(group))

@api.get('/api/groups', tags=['group'])
def get_groups(ctrl: Api = Depends(get_ctrl)) -> Dict[str, List[models.Group]]:
  """ Get all groups """
  return {'groups' : ctrl.get_state().groups}

@api.get('/api/groups/{gid}', tags=['group'])
def get_group(ctrl: Api = Depends(get_ctrl), gid: int = params.GroupID) -> models.Group:
  """ Get Group with id=**gid** """
  _, grp = utils.find(ctrl.get_state().groups, gid)
  if grp is not None:
    return grp
  raise HTTPException(404, f'group {gid} not found')

@api.patch('/api/groups/{gid}', tags=['group'])
def set_group(group: models.GroupUpdate, ctrl: Api = Depends(get_ctrl), gid: int = params.GroupID) -> models.Status:
  """ Update a groups's configuration (group=**gid**) """
  return code_response(ctrl, ctrl.set_group(gid, group))

@api.delete('/api/groups/{gid}', tags=['group'])
def delete_group(ctrl: Api = Depends(get_ctrl), gid: int = params.GroupID) -> models.Status:
  """ Delete a group (group=**gid**) """
  return code_response(ctrl, ctrl.delete_group(gid))

# streams

@api.post('/api/stream', tags=['stream'])
def create_stream(stream: models.Stream, ctrl: Api = Depends(get_ctrl)) -> models.Stream:
  """ Create a new audio stream
  - For Pandora the station is the number at the end of the Pandora URL for a 'station', e.g. 4610303469018478727 from https://www.pandora.com/station/play/4610303469018478727. 'user' and 'password' are the account username and password
  """
  return code_response(ctrl, ctrl.create_stream(stream))

@api.get('/api/streams', tags=['stream'])
def get_streams(ctrl: Api = Depends(get_ctrl)) -> Dict[str, List[models.Stream]]:
  """ Get all streams """
  return {'streams' : ctrl.get_state().streams}

@api.get('/api/streams/{sid}', tags=['stream'])
def get_stream(ctrl: Api = Depends(get_ctrl), sid: int = params.StreamID) -> models.Stream:
  """ Get Stream with id=**sid** """
  _, stream = utils.find(ctrl.get_state().streams, sid)
  if stream is not None:
    return stream
  raise HTTPException(404, f'stream {sid} not found')

@api.patch('/api/streams/{sid}', tags=['stream'])
def set_stream(update: models.StreamUpdate, ctrl: Api = Depends(get_ctrl), sid: int = params.StreamID) -> models.Status:
  """ Update a stream's configuration (stream=**sid**) """
  return code_response(ctrl, ctrl.set_stream(sid, update))

@api.delete('/api/streams/{sid}', tags=['stream'])
def delete_stream(ctrl: Api = Depends(get_ctrl), sid: int = params.StreamID) -> models.Status:
  """ Delete a stream """
  return code_response(ctrl, ctrl.delete_stream(sid))

@api.post('/api/streams/{sid}/station={station}', tags=['stream'])
def change_station(ctrl: Api = Depends(get_ctrl), sid: int = params.StreamID, station: int = params.StationID) -> models.Status:
  """ Change station on a pandora stream (stream=**sid**) """
  # This is a specific version of exec command, it needs to be placed before the genertic version so the path is resolved properly
  return code_response(ctrl, ctrl.exec_stream_command(sid, cmd=f'station={station}'))

@api.post('/api/streams/{sid}/{cmd}', tags=['stream'])
def exec_command(cmd: models.StreamCommand, ctrl: Api = Depends(get_ctrl), sid: int = params.StreamID) -> models.Status:
  """ Executes a comamnd on a stream (stream=**sid**).

    Command options:
    * Play Stream: **play**
    * Pause Stream: **pause**
    * Skip to next song: **next**
    * Stop Stream: **stop**
    * Like/Love Current Song: **love**
    * Ban Current Song (pandora only): **ban**
    * Shelve Current Song (pandora only): **shelve**

  Currently only available with Pandora streams"""
  return code_response(ctrl, ctrl.exec_stream_command(sid, cmd=cmd))

# presets

@api.post('/api/preset', tags=['preset'])
def create_preset(preset: models.Preset, ctrl: Api = Depends(get_ctrl)) -> models.Preset:
  """ Create a new preset configuration """
  return code_response(ctrl, ctrl.create_preset(preset))

@api.get('/api/presets', tags=['preset'])
def get_presets(ctrl: Api = Depends(get_ctrl)) -> Dict[str, List[models.Preset]]:
  """ Get all presets """
  return {'presets' : ctrl.get_state().presets}

@api.get('/api/presets/{pid}', tags=['preset'])
def get_preset(ctrl: Api = Depends(get_ctrl), pid: int = params.PresetID) -> models.Preset:
  """ Get Preset with id=**pid** """
  _, preset = utils.find(ctrl.get_state().presets, pid)
  if preset is not None:
    return preset
  raise HTTPException(404, f'preset {pid} not found')

@api.patch('/api/presets/{pid}', tags=['preset'])
def set_preset(update: models.PresetUpdate, ctrl: Api = Depends(get_ctrl), pid: int = params.PresetID) -> models.Status:
  """ Update a preset's configuration (preset=**pid**) """
  return code_response(ctrl, ctrl.set_preset(pid, update))

@api.delete('/api/presets/{pid}', tags=['preset'])
def delete_preset(ctrl: Api = Depends(get_ctrl), pid: int = params.PresetID) -> models.Status:
  """ Delete a preset """
  return code_response(ctrl, ctrl.delete_preset(pid))

@api.post('/api/presets/{pid}/load', tags=['preset'])
def load_preset(ctrl: Api = Depends(get_ctrl), pid: int = params.PresetID) -> models.Status:
  """ Load a preset configuration """
  return code_response(ctrl, ctrl.load_preset(pid))

# PA

@api.post('/api/announce', tags=['announce'])
def announce(announcement: models.Announcement, ctrl: Api = Depends(get_ctrl)) -> models.Status:
  """ Make an announcement """
  return code_response(ctrl, ctrl.announce(announcement))

# Info

@api.get('/api/info', tags=['status'])
def get_info(ctrl: Api = Depends(get_ctrl)) -> models.Info:
  """ Get additional information """
  return code_response(ctrl, ctrl.get_info())

# include all routes above

app.include_router(api)

# API Documentation

def get_body_model(route: APIRoute) -> Optional[Dict[str, Any]]:
  """ Get json model for the body of an api request """
  try:
    if route.body_field:
      json_model = route.body_field.type_.schema_json()
      return json.loads(json_model)
    return None
  except:
    return None

def get_response_model(route: APIRoute) -> Optional[Dict[str, Any]]:
  """ Get json model for the response of an api request """
  try:
    if route.response_field:
      json_model = route.response_field.type_.schema_json()
      return json.loads(json_model)
    return None
  except:
    return None

def add_creation_examples(openapi_schema, route: APIRoute) -> None:
  """ Add creation examples for a given route (for modifying request types) """
  req_model = get_body_model(route)
  if req_model and ('examples' in req_model or 'creation_examples' in req_model):
    if 'creation_examples' in req_model: # prefer creation examples for POST request, this allows us to have different examples for get response and creation requests
      examples = req_model['creation_examples']
    else:
      examples = req_model['examples']
    for method in route.methods:
      # Only POST, PATCH, and PUT methods have a request body
      if method in {"POST", "PATCH", "PUT"}:
        openapi_schema['paths'][route.path][method.lower()]['requestBody'][
        'content']['application/json']['examples'] = examples

def add_response_examples(openapi_schema, route: APIRoute) -> None:
  """ Add response examples for a given route """
  resp_model = get_response_model(route)
  if resp_model and 'examples' in resp_model:
    examples = resp_model['examples']
    for method in route.methods:
      openapi_schema['paths'][route.path][method.lower()]['responses']['200'][
        'content']['application/json']['examples'] = examples
  if route.path in ['/api/zones', '/api/groups', '/api/sources', '/api/streams', '/api/presets']:
    if 'get' in  openapi_schema['paths'][route.path]:
      piece = route.path.replace('/api/', '')
      example_status = list(models.Status.Config.schema_extra['examples'].values())[0]['value']
      openapi_schema['paths'][route.path]['get']['responses']['200'][
          'content']['application/json']['example'] = {piece: example_status[piece]}

def get_live_examples(tags: List[Union[str, Enum]]) -> Dict[str, Dict[str, Any]]:
  """ Create a list of examples using the live configuration """
  live_examples = {}
  for tag in tags:
    for i in get_ctrl().get_items(str(tag)) or []:
      if isinstance(i.name, str):
        if isinstance(i, models.Stream):
          live_examples[i.name] = {'value': i.id, 'summary': f'{i.name} - {i.type}'}
        else:
          live_examples[i.name] = {'value': i.id, 'summary': i.name}
  return live_examples

def get_xid_param(route):
  """ Check if path has an Xid parameter """
  id_param = None
  for param_name in route.param_convertors.keys():
    if 'id' in param_name and len(param_name) == 3:
      id_param = param_name
      break
  return id_param

def add_example_params(openapi_schema, route: APIRoute) -> None:
  """ Manually add relevant example parameters based on the current configuration (for paths that require parameters) """
  for method in route.methods:
    xid_param = get_xid_param(route)
    if xid_param:
      # generate examples for that id parameter
      live_examples = get_live_examples(route.tags)
      # find the matching parameter and add the examples to it
      path_method = openapi_schema['paths'][route.path][method.lower()]
      if 'parameters' in path_method:
        for param in path_method['parameters']:
          if param['name'] == xid_param:
            param['examples'] = live_examples

def generate_openapi_spec(add_test_docs=True):
  """ Generate the openapi spec using documentation embedded in the models and routes """
  if app.openapi_schema:
    return app.openapi_schema
  openapi_schema = get_openapi(
    title='AmpliPi',
    version='1.0',
    description="This is the AmpliPi home audio system's control server.",
    routes=app.routes,
    tags=[
      {
        'name': 'status',
        'description': 'The status and configuration of the entire system, including sources, zones, groups, and streams.',
      },
      {
        'name': 'source',
        'description': 'Audio source. Can accept audio input from a local (RCA) connection or any stream. Sources can be connected to one or multiple zones, or connected to nothing at all.',
      },
      {
        'name': 'zone',
        'description': 'Stereo output to a set of speakers, typically a room. Individually controllable with its own volume control. Can be connected to one of the 4 audio sources.',
      },
      {
        'name': 'group',
        'description': '''Group of zones. Grouping allows a set of zones to be controlled together. A zone can belong to multiple groups, allowing for different levels of abstraction, e.g. Guest Bedroom can belong to both the 'Upstairs' and 'Whole House' groups.'''
      },
      {
        'name': 'stream',
        'description': 'Digital stream that can be connected to a source, e.g. Pandora, AirPlay, Spotify, Internet Radio, DLNA.',
      },
      {
        'name': 'preset',
        'description': '''A partial system configuration. Used to load specific configurations, such as "Home Theater" mode where the living room speakers are connected to the TV's audio output.''',
      }
    ],
    servers=[{
      'url': '',
      'description': 'AmpliPi Controller'
    }],
  )

  openapi_schema['info']['contact'] = {
    'email': 'info@micro-nova.com',
    'name':  'Micronova',
    'url':   'http://micro-nova.com',
  }
  openapi_schema['info']['license'] = {
    'name': 'GPL',
    'url':  'https://github.com/micro-nova/AmpliPi/blob/master/COPYING',
  }

  # Manually add examples present in pydancticModel.schema_extra into openAPI schema
  for route in app.routes:
    if isinstance(route, APIRoute):
      add_creation_examples(openapi_schema, route)
      add_response_examples(openapi_schema, route)

  if not add_test_docs:
    return openapi_schema

  for route in app.routes:
    if isinstance(route, APIRoute):
      add_example_params(openapi_schema, route)

  return openapi_schema

YAML_DESCRIPTION = """| # The links in the description below are tested to work with redoc and may not be portable
    This is the AmpliPi home audio system's control server.

    # Configuration

    This web interface allows you to control and configure your AmpliPi device.
    At the moment the API is the only way to configure the AmpliPi.

    ## Try it out!

    __Using this web interface to test API commands:__

      1. Go to an API request
      1. Pick one of the examples
      1. Edit it
      1. Press the try button, it will send an API command/request to the AmpliPi

    __Try getting the status:__

      1. Go to [Status -> Get Status](#get-/api)
      1. Click the Try button, you will see a response below with the full status/config of the AmpliPi controller

    __Try changing a zone's name:__

      1. Go to [Zone -> Update Zone](#patch-/api/zones/-zid-)
      1. Next to **PATH PARAMETERS** click Zone 2 to fill in Zone 2's id
      1. Under **REQUEST BODY** click Example and select "Change Name"
      1. Edit the name to what you want to call the zone
      1. Click the Try button, you will see a response below with the full status/config of the AmpliPi controller

    __Try changing a group's name and zones:__

      1. Go to [Group -> Update Group](#patch-/api/groups/-gid-)
      1. Next to **PATH PARAMETERS** click Group 1 to fill in Group 1's id
      1. Under **REQUEST BODY** click Example and select "Rezone Group"
      1. Edit the name to what you want to call the group
      1. Edit the zones that belong to the group
      1. Click the Try button, you will see a response below with the full status/config of the AmpliPi controller

    __Try creating a new group:__

      1. Go to [Group -> Create Group](#post-/api/group)
      1. Under **REQUEST BODY** click Example and select "Upstairs Group"
      1. Edit the group name or zones array
      1. Click the Try button, you will see a response below with the new group

    __Here are some other things that you might want to change:__

      - [Stream -> Create new stream](#post-/api/stream)
      - [Preset -> Create preset](#post-/api/preset) (Have a look at the model to see what can be added here)
      - [Source -> Set source](#patch-/api/sources/-sid-) (Try updating Source 1's name to "TV")

    # More Info

    Check out all of the different things you can do with this API:

      - [Status](#tag--status)
      - [Source](#tag--source)
      - [Zone](#tag--zone)
      - [Group](#tag--group)
      - [Stream](#tag--stream)
      - [Preset](#tag--preset)

    # OpenAPI

    This API is documented using the OpenAPI specification
"""

@lru_cache(2)
def create_yaml_doc(add_test_docs=True) -> str:
  """ Create the openapi yaml schema intended for display by rapidaoc

  We use yaml here for its human readability.
  """
  openapi = app.openapi()
  # use a placeholder for the description, multiline strings weren't using block formatting
  openapi['info']['description'] = '$REPLACE_ME$'
  yaml_s = yaml.safe_dump(openapi, sort_keys=False, allow_unicode=True)
  # fix the long description
  return yaml_s.replace('$REPLACE_ME$', YAML_DESCRIPTION)

# additional yaml version of openapi.json
# this is much more human readable
@app.get('/openapi.yaml', include_in_schema=False)
def read_openapi_yaml() -> Response:
  """ Read the openapi yaml file

  This much more human readable than the json version """
  return Response(create_yaml_doc(), media_type='text/yaml')

@app.get('/openapi.json', include_in_schema=False)
def read_openapi_json():
  """ Read the openapi json file

  This is slightly easier to process by our test framework """
  return app.openapi()

app.openapi = generate_openapi_spec # type: ignore

# Documentation

@app.get('/doc', include_in_schema=False)
def doc():
  """ Get the API documentation """
  # TODO: add hosted python docs as well
  return FileResponse(f'{TEMPLATE_DIR}/rest-api-doc.html')

# Website

@app.get('/', include_in_schema=False)
@app.get('/{src}', include_in_schema=False)
def view(request: Request, ctrl: Api = Depends(get_ctrl), src: int = 0):
  """ Webapp main view """
  state = ctrl.get_state()
  context = {
    # needed for template to make response
    'request': request,
    # simplified amplipi state
    'cur_src': src,
    'sources': state.sources,
    'zones': state.zones,
    'groups': state.groups,
    'presets': state.presets,
    'inputs': [ctrl.get_inputs(src) for src in state.sources],
    'unused_groups': [unused_groups(ctrl, src.id) for src in state.sources if src.id is not None],
    'unused_zones': [unused_zones(ctrl, src.id) for src in state.sources if src.id is not None],
    'ungrouped_zones': [ungrouped_zones(ctrl, src.id) for src in state.sources if src.id is not None],
    'song_info': [src.info for src in state.sources if src.info is not None], # src.info should never be None
    'version': state.info.version if state.info else 'unknown',
    'min_vol': models.MIN_VOL_F,
    'max_vol': models.MAX_VOL_F,
  }
  return templates.TemplateResponse('index.html.j2', context, media_type='text/html')

def create_app(mock_ctrl=None, mock_streams=None, config_file=None, delay_saves=None, settings: models.AppSettings = models.AppSettings()) -> FastAPI:
  """ Create the AmpliPi web app with a specific configuration """
  # specify old parameters
  if mock_ctrl is not None:
    settings.mock_ctrl = mock_ctrl
  if mock_streams is not None:
    settings.mock_streams = mock_streams
  if config_file is not None:
    settings.config_file = config_file
  if delay_saves is not None:
    settings.delay_saves = delay_saves
  get_ctrl().reinit(settings, change_notifier=notify_on_change)
  return app

# Shutdown

@app.on_event('shutdown')
def on_shutdown():
  print('Shutting down AmpliPi')
  # gracefully shutdown the underlying controller
  _ctrl = get_ctrl()
  get_ctrl.cache_clear()
  del _ctrl
  print('webserver shutdown complete')

# MDNS

def get_ip_info(iface: str = 'eth0') -> Tuple[Optional[str], Optional[str]]:
  """ Get the IP address of interface @iface """
  try:
    info = ni.ifaddresses(iface)
    return info[ni.AF_INET][0].get('addr'), info[ni.AF_LINK][0].get('addr')
  except:
    return None, None

def advertise_service(port, que: Queue):
  """ Advertise the AmpliPi api via zeroconf, can be verified with 'avahi-browse -ar'
      Expected to be run as a seperate process, eg:

          q = Queue()
          ad = Process(target=amplipi.app.advertise_service, args=(5000, q))
          ad.start()
          ...
          q.put('done')
          ad.join()
  """
  hostname = f'{gethostname()}.local'
  url = f'http://{hostname}'

  # search for the best interface to advertise on
  ifaces = ['eth0', 'wlan0'] # default pi interfaces
  try:
    for iface in ni.interfaces():
      if iface.startswith('w') or iface.startswith('e'):
        ifaces.append(iface)
  except:
    pass
  ip_addr, mac_addr = None, None
  for iface in ifaces:
    ip_addr, mac_addr = get_ip_info(iface)
    if ip_addr and mac_addr:
      break # take the first good interface found

  if not ip_addr:
    print(f'AmpliPi zeroconf - unable to register service on one of {ifaces}, \
            they all are either not available or have no IP address.')
    print(f'AmpliPi zeroconf - is this running on AmpliPi?')
    ip_addr = '0.0.0.0' # Any hosted ip on this device
  if port != 80:
    url += f':{port}'
  info_deprecated = ServiceInfo(
    '_http._tcp.local.',
    # this is named AmpliPi-api to distinguish from the common Spotify/Airport name of AmpliPi
    'amplipi-api._http._tcp.local.',
    addresses=[inet_aton(ip_addr)],
    port=port,
    properties={
      # standard info
      'path': '/api/',
      # extra info - for interfacing
      'name': 'AmpliPi',
      'vendor': 'MicroNova',
      'version': utils.detect_version(),
      # extra info - for user
      'web_app': url,
      'documentation': f'{url}/doc'
    },
    server=f'{hostname}.', # Trailing '.' is required by the SRV_record specification
  )

  info = ServiceInfo(
    # use a custom type to easily support multiple amplipi device enumeration
    '_amplipi._tcp.local.',
    # this is named AmpliPi-api to distinguish from the common Spotify/Airport name of AmpliPi
    f'amplipi-{str(mac_addr).lower()}._amplipi._tcp.local.',
    addresses=[inet_aton(ip_addr)],
    port=port,
    properties={
      # standard info
      'path': '/api/',
      # extra info - for interfacing
      'name': 'AmpliPi',
      'vendor': 'MicroNova',
      'version': utils.detect_version(),
      # extra info - for user
      'web_app': url,
      'documentation': f'{url}/doc'
    },
    server=f'{hostname}.', # Trailing '.' is required by the SRV_record specification
  )

  print(f'AmpliPi zeroconf - registering service: {info}')
  # right now the AmpliPi webserver is ipv4 only
  zeroconf = Zeroconf(ip_version=IPVersion.V4Only, interfaces=[ip_addr])
  zeroconf.register_service(info_deprecated, cooperating_responders=True)
  zeroconf.register_service(info)
  print('AmpliPi zeroconf - finished registering service')
  try:
    while que.empty():
      sleep(0.1)
  except:
    pass
  finally:
    print('AmpliPi zeroconf - unregistering service')
    zeroconf.unregister_service(info)
    zeroconf.close()

if __name__ == '__main__':
  """ Create the openapi yaml file describing the AmpliPi API """
  parser = argparse.ArgumentParser(description="Create AmpliPi's openapi spec in YAML")
  parser.add_argument('file', type=argparse.FileType('w'))
  args = parser.parse_args()
  with args.file as file:
    file.write(create_yaml_doc(add_test_docs=False))
