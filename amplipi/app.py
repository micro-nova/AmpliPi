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
Flask is used to simplify the web plumbing.
"""

from flask import Flask, request, render_template, jsonify, make_response
import amplipi.ctrl as ctrl
import amplipi.rt as rt
import amplipi.utils as utils
import json
from collections import OrderedDict

DEBUG_API = False

# start in the web directory (where everythins is layed out for flask)
import os
template_dir = os.path.abspath('web/templates')
static_dir = os.path.abspath('web/static')

app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
app.api = None # TODO: assign an unloaded API here to get auto completion / linting

# Helper functions
def unused_groups(src):
  """ Get groups that are not connected to src """
  groups = app.api.status['groups']
  return { g['id'] : g['name'] for g in groups if g['source_id'] != src}

def unused_zones(src):
  """ Get zones that are not conencted to src """
  zones = app.api.status['zones']
  return { z['id'] : z['name'] for z in zones if z['source_id'] != src }

def ungrouped_zones(src):
  """ Get zones that are connected to src, but don't belong to a full group """
  zones = app.api.status['zones']
  groups = app.api.status['groups']
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
  stream = app.api._get_stream(app.api.status['sources'][src]['input'])
  info = stream.info() if stream else {}
  # add empty strings for unpopulated fields
  for field in song_fields:
    if field not in info:
      info[field] = ''
  return info

# API
# TODO: add debug printing to each request, ie.
#   if DEBUG_API:
#     print(app.api.visualize_api())

@app.route('/api', methods=['GET'])
@app.route('/api/', methods=['GET'])
def get_status():
  return make_response(jsonify(app.api.get_state()))

def code_response(resp):
  if resp is None:
    # general commands return None to indicate success
    return get_status(), 200
  elif 'error' in resp:
    # TODO: refine error codes based on error message
    return jsonify(resp), 404
  else:
    return jsonify(resp), 200

# sources

@app.route('/api/sources/<int:src>', methods=['GET'])
def get_source(src):
  # TODO: add get_X capabilities to underlying API?
  sources = app.api.get_state()['sources']
  if src >= 0 and src < len(sources):
    return sources[src]
  else:
    return {}, 404

@app.route('/api/sources/<int:src>', methods=['PATCH'])
def set_source(src):
  return code_response(app.api.set_source(id=src, **request.get_json()))

# zones

@app.route('/api/zones/<int:zone>', methods=['GET'])
def get_zone(zone):
  zones = app.api.get_state()['zones']
  if zone >= 0 and zone < len(zones):
    return zones[zone]
  else:
    return {}, 404

@app.route('/api/zones/<int:zone>', methods=['PATCH'])
def set_zone(zone):
  return code_response(app.api.set_zone(id=zone, **request.get_json()))

# groups

@app.route('/api/group', methods=['POST'])
def create_group():
  return code_response(app.api.create_group(**request.get_json()))

@app.route('/api/groups/<int:group>', methods=['GET'])
def get_group(group):
  groups = app.api.get_state()['groups']
  if group >= 0 and group < len(groups):
    return groups[group]
  else:
    return {}, 404

@app.route('/api/groups/<int:group>', methods=['PATCH'])
def set_group(group):
  return code_response(app.api.set_group(id=group, **request.get_json()))

@app.route('/api/groups/<int:group>', methods=['DELETE'])
def delete_group(group):
  return code_response(app.api.delete_group(id=group))

# streams

@app.route('/api/stream', methods=['POST'])
def create_stream():
  print('creating stream from {}'.format(request.get_json()))
  return code_response(app.api.create_stream(**request.get_json()))

@app.route('/api/streams/<int:sid>', methods=['GET'])
def get_stream(sid):
  _, stream = utils.find(app.api.get_state()['streams'], sid)
  if stream is not None:
    return stream
  else:
    return {}, 404

@app.route('/api/streams/<int:sid>', methods=['PATCH'])
def set_stream(sid):
  return code_response(app.api.set_stream(id=sid, **request.get_json()))

@app.route('/api/streams/<int:sid>', methods=['DELETE'])
def delete_stream(sid):
  return code_response(app.api.delete_stream(id=sid))

@app.route('/api/streams/<int:sid>/<cmd>', methods=['POST'])
def exec_command(sid, cmd):
  return code_response(app.api.exec_stream_command(id=sid, cmd=cmd))

# presets

@app.route('/api/preset', methods=['POST'])
def create_preset():
  print('creating preset from {}'.format(request.get_json()))
  return code_response(app.api.create_preset(request.get_json()))

@app.route('/api/presets/<int:pid>', methods=['GET'])
def get_preset(pid):
  _, preset = utils.find(app.api.get_state()['presets'], pid)
  if preset is not None:
    return preset
  else:
    return {}, 404

@app.route('/api/presets/<int:pid>', methods=['PATCH'])
def set_preset(pid):
  return code_response(app.api.set_preset(pid, request.get_json()))

@app.route('/api/presets/<int:pid>', methods=['DELETE'])
def delete_preset(pid):
  return code_response(app.api.delete_preset(id=pid))

@app.route('/api/presets/<int:pid>/load', methods=['POST'])
def load_preset(pid):
  return code_response(app.api.load_preset(id=pid))

# documentation

@app.route('/api/doc')
def doc():
  # TODO: add hosted python docs as well
  return render_template('rest-api-doc.html')

# Website

@app.route('/')
@app.route('/<int:src>')
def view(src=0):
  s = app.api.status
  return render_template('index.html', cur_src=src, sources=s['sources'],
    zones=s['zones'], groups=s['groups'], inputs=app.api.get_inputs(),
    unused_groups=[unused_groups(src) for src in range(4)],
    unused_zones=[unused_zones(src) for src in range(4)],
    ungrouped_zones=[ungrouped_zones(src) for src in range(4)],
    song_info=[song_info(src) for src in range(4)])

def create_app(mock_ctrl=False, mock_streams=False, config_file='config/house.json'):
  if mock_ctrl:
    app.api = ctrl.Api(rt.Mock(), mock_streams=mock_streams, config_file=config_file)
  else:
    app.api = ctrl.Api(rt.Rpi(), mock_streams=mock_streams, config_file=config_file)
  return app

if __name__ == '__main__':
  app = create_app()
  app.run(debug=True, host= '0.0.0.0')
