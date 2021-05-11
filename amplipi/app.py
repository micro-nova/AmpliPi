#!/usr/bin/python3

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

"""AmpliPi Webapp

This serves the amplipi webpp and underlying rest api, that it uses.
The FastAPI/Starlette web framework is used to simplify the web plumbing.
"""

# web framework
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi_utils import cbv
from fastapi_utils.inferring_router import InferringRouter
# type handling, fastapi leverages type checking for performance and easy docs
from typing import List, Optional, Dict, Union
from functools import lru_cache
# web server
import uvicorn
# amplipi
import amplipi
import amplipi.rt as rt
import amplipi.utils as utils
import amplipi.models as models
#helpers
from json import dumps as jsonify
DEBUG_API = False

# start in the web directory (where everything is layed out for flask)
import os
template_dir = os.path.abspath('web/templates')
static_dir = os.path.abspath('web/static')
generated_dir = os.path.abspath('web/generated')

app = FastAPI(title='Amplipi')
templates = Jinja2Templates(template_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/generated", StaticFiles(directory=generated_dir), name="generated") # TODO: make this register as a dynamic folder???

# Helper functions
def unused_groups(src):
  """ Get groups that are not connected to src """
  ctrl = get_ctrl()
  groups = ctrl.status['groups']
  return { g['id'] : g['name'] for g in groups if g['source_id'] != src}

def unused_zones(src):
  """ Get zones that are not conencted to src """
  ctrl = get_ctrl()
  zones = ctrl.status['zones']
  return { z['id'] : z['name'] for z in zones if z['source_id'] != src }

def ungrouped_zones(src):
  """ Get zones that are connected to src, but don't belong to a full group """
  ctrl = get_ctrl()
  zones = ctrl.status['zones']
  groups = ctrl.status['groups']
  # get all of the zones that belong to this sources groups
  grouped_zones = set()
  for g in groups:
    if g['source_id'] == src:
      grouped_zones = grouped_zones.union(g['zones'])
  # get all of the zones connected to this soource
  source_zones = set([ z['id'] for z in zones if z['source_id'] == src ])
  # return all of the zones connected to this source that aren't in a group
  ungrouped_zones_ = source_zones.difference(grouped_zones)
  return [ zones[z] for z in ungrouped_zones_ if not zones[z]['disabled']]

def song_info(src):
  """ Get the song info for a source """
  ctrl =  get_ctrl()
  song_fields = ['artist', 'album', 'track', 'img_url']
  stream = ctrl._get_stream(ctrl.status['sources'][src]['input'])
  info = stream.info() if stream else {}
  # add empty strings for unpopulated fields
  for field in song_fields:
    if field not in info:
      info[field] = ''
  return info

# Add our own router so we can bind/inject our API object
settings = models.AppSettings()

@lru_cache(1)
def get_ctrl() -> amplipi.ctrl.Api:
  return amplipi.ctrl.Api(settings)

@app.get('/api')
@app.get('/api/')
def get_status(ctrl=Depends(get_ctrl)):
  return ctrl.get_state()

def code_response(resp):
  if resp is None:
    # general commands return None to indicate success
    return get_ctrl().get_state()
  elif 'error' in resp:
    # TODO: refine error codes based on error message
    raise HTTPException(404, resp['error'])
  else:
    return resp

# sources

@app.get('/api/sources')
def get_sources(ctrl=Depends(get_ctrl)):
  return {'sources' : ctrl.get_state()['sources']}

@app.get('/api/sources/{sid}')
def get_source(sid: int, ctrl=Depends(get_ctrl)):
  # TODO: add get_X capabilities to underlying API?
  sources = ctrl.get_state()['sources']
  return sources[sid]

@app.patch('/api/sources/{sid}')
async def set_source(sid: int, request:Request, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  params = await request.json()
  return code_response(ctrl.set_source(id=sid, **params))

# zones

@app.get('/api/zones')
def get_zones(ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> Dict[str, List[models.Zone]]:
  return {'zones': ctrl.get_state()['zones']}

@app.get('/api/zones/{zid}')
def get_zone(zid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Zone:
  zones = ctrl.get_state()['zones']
  if zid >= 0 and zid < len(zones):
    return zones[zid]
  else:
    raise HTTPException(404, f'zone {zid} not found')

@app.patch('/api/zones/{zid}')
def set_zone(zid: int, zone: models.ZoneUpdate, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  return code_response(ctrl.set_zone(zid, zone))

# groups

@app.post('/api/group')
def create_group(group: models.Group, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Group:
  return code_response(ctrl.create_group(group))

@app.get('/api/groups')
def get_groups(ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> Dict[str, List[models.Group]]:
  return {'groups' : ctrl.get_state()['groups']}

@app.get('/api/groups/{gid}')
def get_group(gid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Group:
  _, grp = utils.find(ctrl.get_state()['groups'], gid)
  if grp is not None:
    return grp
  else:
    raise HTTPException(404, f'group {gid} not found')

@app.patch('/api/groups/{gid}')
def set_group(gid: int, group: models.GroupUpdate, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  return code_response(ctrl.set_group(gid, group)) # TODO: pass update directly

@app.delete('/api/groups/{gid}')
def delete_group(gid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> None:
  return code_response(ctrl.delete_group(id=gid))

# streams

@app.post('/api/stream')
async def create_stream(request: Request, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  params = await request.json()
  return code_response(ctrl.create_stream(**params))

@app.get('/api/streams')
def get_streams(ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  return {'streams' : ctrl.get_state()['streams']}

@app.get('/api/streams/{sid}')
def get_stream(sid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  _, stream = utils.find(ctrl.get_state()['streams'], sid)
  if stream is not None:
    return stream
  else:
    raise HTTPException(404, f'stream {sid} not found')

@app.patch('/api/streams/{sid}')
async def set_stream(request: Request, sid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  params = await request.json()
  return code_response(ctrl.set_stream(id=sid, **params))

@app.delete('/api/streams/{sid}')
def delete_stream(sid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  return code_response(ctrl.delete_stream(id=sid))

@app.post('/api/streams/{sid}/{cmd}')
def exec_command(sid: int, cmd: str, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)):
  return code_response(ctrl.exec_stream_command(id=sid, cmd=cmd))

# presets

@app.post('/api/preset')
def create_preset(preset:models.Preset, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Preset:
  return code_response(ctrl.create_preset(preset))

@app.get('/api/presets')
def get_presets(ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> Dict[str, List[models.Preset]]:
  return {'presets' : ctrl.get_state()['presets']}

@app.get('/api/presets/{pid}')
def get_preset(pid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Preset:
  _, preset = utils.find(ctrl.get_state()['presets'], pid)
  if preset is not None:
    return preset
  else:
    raise HTTPException(404, f'preset {pid} not found')

@app.patch('/api/presets/{pid}')
def set_preset(pid: int, update: models.PresetUpdate, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Status:
  return code_response(ctrl.set_preset(pid, update))

@app.delete('/api/presets/{pid}')
def delete_preset(pid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Status:
  return code_response(ctrl.delete_preset(pid))

@app.post('/api/presets/{pid}/load')
def load_preset(pid: int, ctrl: amplipi.ctrl.Api = Depends(get_ctrl)) -> models.Status:
  return code_response(ctrl.load_preset(pid))

# Documentation

@app.get('/api/doc')
def doc():
  # TODO: add hosted python docs as well
  return FileResponse(f'{template_dir}/rest-api-doc.html') # TODO: this is not really a template

# Website

@app.get('/')
@app.get('/{src}')
def view(request: Request, src=0):
  ctrl = get_ctrl()
  s = ctrl.get_state()
  context = {
    # needed for template to make response
    'request': request,
    # simplified amplipi state
    'cur_src': src,
    'sources': s['sources'],
    'zones': s['zones'],
    'groups': s['groups'],
    'presets': s['presets'],
    'inputs': ctrl.get_inputs(),
    'unused_groups': [unused_groups(src) for src in range(4)],
    'unused_zones': [unused_zones(src) for src in range(4)],
    'ungrouped_zones': [ungrouped_zones(src) for src in range(4)],
    'song_info': [song_info(src) for src in range(4)],
    'version': s['version'],
  }
  return templates.TemplateResponse("index.html.j2", context)

def create_app(mock_ctrl=None, mock_streams=None, config_file=None, delay_saves=None, s:models.AppSettings=models.AppSettings()) -> FastAPI:
  # specify old parameters
  if mock_ctrl: s.mock_ctrl = mock_ctrl
  if mock_streams: s.mock_streams = mock_streams
  if config_file: s.config_file = config_file
  if delay_saves: s.delay_saves = delay_saves
  # modify settings
  global settings
  settings = s # set the settings class the api_router uses to instantiate the API class
  return app
