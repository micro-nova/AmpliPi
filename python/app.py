#!/usr/bin/python3

from flask import Flask, request, render_template
import ethaudio
import json
from collections import OrderedDict

app = Flask(__name__)
app.api = None

def options_html(options):
  html_options = ['<option value="{}">{}</option>'.format(v, k) for k, v in options.items()]
  html = '\n'.join(html_options)
  return html

def src_html(src):
  source = app.api.status['sources'][src]
  source_header = '<tr><td>{}</td><td><select id="s{}_input" onchange="onSrcInputChange(this);">'.format(source['name'], src)
  source_footer = '</select></td></tr>'

  options = OrderedDict()
  inputs = app.api.get_inputs()
  print(inputs)
  # add the connected input first, then the others
  for name, input_ in inputs.items():
    if input_ == source['input']:
      options[name] = input_
  for name, input_ in inputs.items():
    if input_ != source['input']:
      options[name] = input_
  return source_header + options_html(options) + source_footer

def group_html(group):
  # make a volume control bar for a group
  # TODO: make this volume control into its own function once we have to show zones as well
  html_header = '<tr><td>{}</td>'.format(group['name'])
  html = '<td><input id="g{}_vol" type="range" value="{}" onchange="onGroupVolChange(this);" min="-79" max="0"></td>'.format(group['id'], group['vol_delta'])
  html += '<td><span id="g{}_atten">{}</span> dB</td>'.format(group['id'], group['vol_delta'])
  html += '<td><input type="checkbox" id="g{}_mute" onchange="onGroupMuteChange(this);" {} ></td>'.format(group['id'], {False:'', True: 'checked'}[group['mute']])
  html_footer = '</tr>'
  return html_header + html + html_footer

def unused_groups_html(src):
  groups = app.api.status['groups']
  header = '<tr><td></td></tr>'
  html = '<tr><td>Add group</td><td><select id="s{}_add" onchange="onAddGroupToSrc(this);">'.format(src)
  # make a dict that starts eith an empty item, this makes it so any new selection is a change
  unused = { g['name'] : g['id'] for g in groups if g['source_id'] != src }
  items = OrderedDict()
  items['  '] = None
  for k, v in unused.items():
    items[k] = v
  html += options_html(items)
  html += '</select></td></tr>'
  footer = ''
  return header + html + footer

def unused_groups_options_html(src):
  groups = app.api.status['groups']
  return options_html({ g['name'] : g['id'] for g in groups if g['source_id'] != 3 })

def groups_html(src):
  # show all of the groups that are connected to @src
  groups = app.api.status['groups']
  html_header = ''
  html_groups = ''.join([group_html(group) for group in groups if group['source_id'] == src])
  html_footer = ''
  return html_header + html_groups + html_footer

@app.route('/api', methods=['GET'])
def get():
  return json.dumps(app.api.get_state())

@app.route('/api', methods=['POST'])
def parse_cmd():
  req = request.get_json()
  print(req)
  cmd = req.pop('command')
  if cmd == 'set_group':
    out = app.api.set_group(req.pop('id'), **req)
  elif cmd == 'set_source':
    out = app.api.set_source(req.pop('id'), **req)
  elif cmd == 'set_zone':
    out = app.api.set_zone(req.pop('id'), **req)
  else:
    out = {'error': 'Unknown command'}
  print(app.api.visualize_api())
  if out is None: # None is returned on success
    out = app.api.get_state()
  return json.dumps(out)

@app.route('/')
@app.route('/source/<int:src>')
def index(src=0):
  name = app.api.status['sources'][src]['name']
  return render_template('index.html', src=src, name=name)

def unused_groups(src):
  groups = app.api.status['groups']
  return { g['id'] : g['name'] for g in groups if g['source_id'] != src}

def unused_zones(src):
  zones = app.api.status['zones']
  return { z['id'] : z['name'] for z in zones if z['source_id'] != src }

def ungrouped_zones(src):
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
  return [ zones[z] for z in ungrouped_zones_ ]

@app.route('/test')
@app.route('/test/<int:src>')
def amplipi(src=0):
  s = app.api.status
  return render_template('index2.html', cur_src=src, sources=s['sources'],
    zones=s['zones'], groups=s['groups'], inputs=app.api.get_inputs(),
    unused_groups=[unused_groups(src) for src in range(4)],
    unused_zones=[unused_zones(src) for src in range(4)],
    ungrouped_zones=[ungrouped_zones(src) for src in range(4)])

def create_app(mock=False, config_file='../config/jasons_house.json'):
  if mock:
    app.api = ethaudio.Api(ethaudio.api.MockRt(), config_file)
  else:
    app.api = ethaudio.Api(ethaudio.api.RpiRt(), config_file)
  return app

if __name__ == '__main__':
  app = create_app()
  app.run(debug=True, host= '0.0.0.0')
