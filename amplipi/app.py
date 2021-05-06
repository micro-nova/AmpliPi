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
from fastapi import FastAPI, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.templating import Jinja2Templates
# type handling, fastapi leverages type checking for performance and easy docs
from typing import List, Optional
# web server
import uvicorn
# amplipi
import amplipi.ctrl as ctrl
import amplipi.rt as rt
import amplipi.utils as utils
#helpers
from json import dumps as jsonify
DEBUG_API = False

# start in the web directory (where everything is layed out for flask)
import os
template_dir = os.path.abspath('web/templates')
static_dir = os.path.abspath('web/static')
generated_dir = os.path.abspath('web/generated')

app = FastAPI(title='Amplipi')
app.ctrl = ctrl.Api(rt.Mock(), mock_streams=True, config_file='/tmp/amplipi.conf') # TODO: assign an unloaded API here to get auto completion / linting
templates = Jinja2Templates(template_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/generated", StaticFiles(directory=generated_dir), name="generated") # TODO: make this register as a dynamic folder???

# TODO: move this to ctrl
from pydantic import BaseModel

class ZoneUpdate(BaseModel):
  name: Optional[str]
  source_id: Optional[int]
  zones: Optional[List[int]]
  mute: Optional[bool]
  vol: Optional[int]

@app.get('/static/{filename:path}')
def generated(filename: str):
  print(f'looking for {filename}')
  filename = filename.replace('../', '') # TODO: Get a fancier regex that checks for bad names
  return FileResponse(f'{static_dir}/{filename}')

@app.get('/generated/{filename:path}')
def generated(filename: str):
  filename = filename.replace('../', '') # TODO: Get a fancier regex that checks for bad names
  return FileResponse(f'{generated_dir}/{filename}')

# Helper functions
def unused_groups(src):
  """ Get groups that are not connected to src """
  groups = app.ctrl.status['groups']
  return { g['id'] : g['name'] for g in groups if g['source_id'] != src}

def unused_zones(src):
  """ Get zones that are not conencted to src """
  zones = app.ctrl.status['zones']
  return { z['id'] : z['name'] for z in zones if z['source_id'] != src }

def ungrouped_zones(src):
  """ Get zones that are connected to src, but don't belong to a full group """
  zones = app.ctrl.status['zones']
  groups = app.ctrl.status['groups']
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
  song_fields = ['artist', 'album', 'track', 'img_url']
  stream = app.ctrl._get_stream(app.ctrl.status['sources'][src]['input'])
  info = stream.info() if stream else {}
  # add empty strings for unpopulated fields
  for field in song_fields:
    if field not in info:
      info[field] = ''
  return info

# API
# TODO: add debug printing to each request, ie.
#   if DEBUG_API:
#     print(app.ctrl.visualize_api())

@app.get('/api')
@app.get('/api/')
async def get_status():
  return app.ctrl.get_state()

def code_response(resp):
  if resp is None:
    # general commands return None to indicate success
    return app.ctrl.get_state()
  elif 'error' in resp:
    # TODO: refine error codes based on error message
    raise HTTPException(404, resp['error'])
  else:
    return resp

# sources

@app.get('/api/sources')
async def get_sources():
  return {'sources' : app.ctrl.get_state()['sources']}

@app.get('/api/sources/{sid}')
async def get_source(sid: int):
  # TODO: add get_X capabilities to underlying API?
  sources = app.ctrl.get_state()['sources']
  return sources[sid]

@app.patch('/api/sources/{sid}')
async def set_source(request: Request, sid: int):
  params = await request.json()
  return code_response(app.ctrl.set_source(id=sid, **params))

# zones

@app.get('/api/zones')
async def get_zones():
  return {'zones': app.ctrl.get_state()['zones']}

@app.get('/api/zones/{zid}')
async def get_zone(zid: int):
  zones = app.ctrl.get_state()['zones']
  if zid >= 0 and zid < len(zones):
    return zones[zid]
  else:
    raise HTTPException(404, f'zone {zid} not found')

@app.patch('/api/zones/{zid}')
async def set_zone(zid: int, zone: ZoneUpdate):
  return code_response(app.ctrl.set_zone(id=zid, name=zone.name, source_id=zone.source_id, mute=zone.mute, vol=zone.vol))

# groups

@app.post('/api/group')
async def create_group(request: Request):
  params = await request.json()
  return code_response(app.ctrl.create_group(**params))

@app.get('/api/groups')
async def get_groups():
  return {'groups' : app.ctrl.get_state()['groups']}

@app.get('/api/groups/{group}')
async def get_group(group: int):
  _, grp = utils.find(app.ctrl.get_state()['groups'], group)
  if grp is not None:
    return grp
  else:
    raise HTTPException(404, f'group {group} not found')

@app.patch('/api/groups/{group}')
async def set_group(request: Request, group: int):
  params = await request.json()
  return code_response(app.ctrl.set_group(id=group, **params))

@app.delete('/api/groups/{group}')
def delete_group(group: int):
  return code_response(app.ctrl.delete_group(id=group))

# streams

@app.post('/api/stream')
async def create_stream(request: Request):
  params = await request.json()
  return code_response(app.ctrl.create_stream(**params))

@app.get('/api/streams')
def get_streams():
  return {'streams' : app.ctrl.get_state()['streams']}

@app.get('/api/streams/{sid}')
def get_stream(sid: int):
  _, stream = utils.find(app.ctrl.get_state()['streams'], sid)
  if stream is not None:
    return stream
  else:
    raise HTTPException(404, f'stream {sid} not found')

@app.patch('/api/streams/{sid}')
async def set_stream(request: Request, sid: int):
  params = await request.json()
  return code_response(app.ctrl.set_stream(id=sid, **params))

@app.delete('/api/streams/{sid}')
def delete_stream(sid: int):
  return code_response(app.ctrl.delete_stream(id=sid))

@app.post('/api/streams/{sid}/{cmd}')
def exec_command(sid: int, cmd: str):
  return code_response(app.ctrl.exec_stream_command(id=sid, cmd=cmd))

# presets

@app.post('/api/preset')
async def create_preset(request: Request):
  params = await request.json()
  return code_response(app.ctrl.create_preset(params))

@app.get('/api/presets')
def get_presets():
  return {'presets' : app.ctrl.get_state()['presets']}

@app.get('/api/presets/{pid}')
def get_preset(pid: int):
  _, preset = utils.find(app.ctrl.get_state()['presets'], pid)
  if preset is not None:
    return preset
  else:
    raise HTTPException(404, f'preset {pid} not found')

@app.patch('/api/presets/{pid}')
async def set_preset(request: Request, pid: int):
  params = await request.json()
  return code_response(app.ctrl.set_preset(pid, params))

@app.delete('/api/presets/{pid}')
async def delete_preset(pid: int):
  return code_response(app.ctrl.delete_preset(id=pid))

@app.post('/api/presets/{pid}/load')
async def load_preset(pid: int):
  return code_response(app.ctrl.load_preset(id=pid))

# documentation

@app.get('/api/doc')
def doc():
  # TODO: add hosted python docs as well
  return FileResponse(f'{template_dir}/rest-api-doc.html') # TODO: this is not really a template

# Website

@app.get('/')
@app.get('/{src}')
async def view(request: Request, src=0):
  s = app.ctrl.status
  context = {
    # needed for template to make response
    'request': request,
    # simplified amplipi state
    'cur_src': src,
    'sources': s['sources'],
    'zones': s['zones'],
    'groups': s['groups'],
    'presets': s['presets'],
    'inputs': app.ctrl.get_inputs(),
    'unused_groups': [unused_groups(src) for src in range(4)],
    'unused_zones': [unused_zones(src) for src in range(4)],
    'ungrouped_zones': [ungrouped_zones(src) for src in range(4)],
    'song_info': [song_info(src) for src in range(4)],
    'version': s['version'],
  }
  return templates.TemplateResponse("index.html.j2", context)

def create_app(mock_ctrl=False, mock_streams=False, config_file='config/house.json', delay_saves=True):
  if mock_ctrl:
    app.ctrl = ctrl.Api(rt.Mock(), mock_streams=mock_streams, config_file=config_file, delay_saves=delay_saves)
  else:
    app.ctrl = ctrl.Api(rt.Rpi(), mock_streams=mock_streams, config_file=config_file, delay_saves=delay_saves)
  return app

if __name__ == '__main__':
  app = create_app()
  uvicorn.run(app, host="0.0.0.0", port=5000, debug=True)
