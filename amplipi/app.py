#!/usr/bin/python3
from flask import Flask, request, render_template, jsonify, make_response
import amplipi.ctrl as ctrl
import amplipi.rt as rt
import json
from collections import OrderedDict

DEBUG_API = False

# start in the web directory (where everythins is layed out for flask)
import os
template_dir = os.path.abspath('web/templates')
static_dir = os.path.abspath('web/static')

app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
app.api = None

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

@app.route('/api/sources/<int:src>', methods=['GET'])
def get_source(src):
  # TODO: add get_X capabilities to underlying API?
  sources = app.api.get_state()['sources']
  if src >= 0 and src < len(sources):
    return sources[src]
  else:
    return None, 404

@app.route('/api/sources/<int:src>', methods=['PATCH'])
def set_source(src):
  return code_response(app.api.set_source(id=src, **request.get_json()))

@app.route('/api/zones/<int:zone>', methods=['GET'])
def get_zone(zone):
  zones = app.api.get_state()['zones']
  if zone >= 0 and zone < len(zones):
    return zones[zone]
  else:
    return None, 404

@app.route('/api/zones/<int:zone>', methods=['PATCH'])
def set_zone(zone):
  return code_response(app.api.set_zone(id=zone, **request.get_json()))

@app.route('/api/group', methods=['POST'])
def create_group():
  return code_response(app.api.create_group(**request.get_json()))

@app.route('/api/groups/<int:group>', methods=['GET'])
def get_group(group):
  groups = app.api.get_state()['groups']
  if group >= 0 and group < len(groups):
    return groups[group]
  else:
    return None, 404

@app.route('/api/groups/<int:group>', methods=['PATCH'])
def set_group(group):
  return code_response(app.api.set_group(id=group, **request.get_json()))

@app.route('/api/groups/<int:group>', methods=['DELETE'])
def delete_group(group):
  return code_response(app.api.delete_group(id=group))

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
    ungrouped_zones=[ungrouped_zones(src) for src in range(4)])

def create_app(mock=False, config_file='config/jasons_house.json'):
  if mock:
    app.api = ctrl.Api(rt.Mock(), config_file)
  else:
    app.api = ctrl.Api(rt.Rpi(), config_file)
  return app

if __name__ == '__main__':
  app = create_app()
  app.run(debug=True, host= '0.0.0.0')
