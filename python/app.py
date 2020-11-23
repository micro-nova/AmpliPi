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

def groups_html(src):
  # show all of the groups that are connected to @src
  groups = app.api.status['groups']
  html_header = ''
  html_groups = ''.join([group_html(group) for group in groups if group['source_id'] == src])
  html_footer = ''
  return html_header + html_groups + html_footer

@app.route('/api', methods=['POST'])
def parse_cmd():
  req = request.get_json()
  cmd = req.pop('command')
  if cmd == 'set_group':
    out = app.api.set_group(req.pop('id'), **req)
  elif cmd == 'set_source':
    out = app.api.set_source(req.pop('id'), **req)
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

def create_app(mock=False, config_file='../config/jasons_house.json'):
  if mock:
    app.api = ethaudio.Api(ethaudio.api.MockRt(), config_file)
  else:
    app.api = ethaudio.Api(ethaudio.api.RpiRt(), config_file)
  return app

if __name__ == '__main__':
  app = create_app()
  app.run(debug=True, host= '0.0.0.0')
