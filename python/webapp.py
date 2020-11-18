#!/usr/bin/python3

from flask import Flask, request
import ethaudio
from collections import OrderedDict

app = Flask(__name__)

api = ethaudio.Api(ethaudio.api.RpiRt(), config_file='config/jasons_house.json')

def options_html(options):
  html_options = ['<option value="{}">{}</option>'.format(v, k) for k, v in options.items()]
  return '\n'.join(html_options)

def src_html(src):
  source = api.status['sources'][src]
  source_header = '<tr><td>{}</td><td><select id="s{}_input" onchange="onSrcInputChange(this);">'.format(source['name'], src)
  source_footer = '</select></td></tr>'

  options = OrderedDict()
  inputs = api.get_inputs()
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
  html += '<td><input type="checkbox" id="g{}_mute" onchange="onGroupMuteChange(this);" checked="{}"></td>'.format(group['id'], str(group['mute']).lower()) # TODO: add mute/unmute function
  html_footer = '</tr>'
  return html_header + html + html_footer

def unused_groups_html(src):
  groups = api.status['groups']
  header = '<tr><td></td></tr>'
  html = '<tr><td>Add group</td><td><select id="s{}_add" onchange="onAddGroupToSrc(this);">'.format(src)
  unused = {g['name'] : g['id'] for g in groups if g['source_id'] != src}
  html += options_html(unused)
  html += '</select></td></tr>'
  footer = ''
  return header + html + footer

def groups_html(src):
  # show all of the groups that are connected to @src
  groups = api.status['groups']
  html_header = ''
  html_groups = ''.join([group_html(group) for group in groups if group['source_id'] == src])
  html_footer = ''
  return html_header + html_groups + html_footer

SCRIPTS = """
  function onGroupVolChange(obj) {
    var group = obj.id.substring(0,2);
    var group_atten = group + "_atten";
    var gid = group.substring(1,2);
    document.getElementById(group_atten).innerHTML = obj.value;
    showIntent(group + ' vol= ' + obj.value);
    req = {
      "command": "set_group",
      "id" : Number(gid),
      "vol_delta" : Number(obj.value)
    };
    sendRequest(req)
  }
  function onGroupMuteChange(obj) {
    var group = obj.id.substring(0,2);
    var mute = obj.checked;
    var gid = group.substring(1,2);
    showIntent(group + ' mute= ' + obj.checked);
    req = {
      "command": "set_group",
      "id" : Number(gid),
      "mute" : Boolean(obj.checked)
    };
    sendRequest(req);
  }
  function onAddGroupToSrc(obj) {
    var src = obj.id.substring(1,2);
    var gid = obj.value
    showIntent('Adding g' + gid  + ' to src ' + src);
    req = {
      "command": "set_group",
      "id" : Number(gid),
      "source_id" : Number(src)
    };
    sendRequest(req);
  }
  function onSrcInputChange(obj) {
    var input = obj.value
    var src = obj.id.substring(1,2);
    showIntent('Changing source ' + src  + ' to use ' + input);
    req = {
      "command": "set_source",
      "id" : Number(src),
      "input" : input
    };
    sendRequest(req);
  }
  async function sendRequest(obj) {
    onRequest(obj)
    let response = await fetch('/cmd', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json;charset=utf-8'
      },
      body: JSON.stringify(obj)
    });
    let result = await response.json();
    onResponse(result);
  }
  function showIntent(intent) {
    document.getElementById("intent").innerHTML = intent;
  }
  function onRequest(req) {
    document.getElementById("request").innerHTML = JSON.stringify(req);
  }
  function onResponse(resp) {
    document.getElementById("response").innerHTML = JSON.stringify(resp);
  }
"""

@app.route('/cmd', methods=['POST'])
def parse_cmd():
  req = request.get_json()
  cmd = req.pop('command')
  if cmd == 'set_group':
    out = api.set_group(req.pop('id'), **req)
  elif cmd == 'set_source':
    out = api.set_source(req.pop('id'), **req)
  else:
    out = {'error': 'Unknown command'}
  print('result:')
  if out is None:
    return {}
  return out

@app.route('/')
@app.route('/source/<int:src>')
def index(src=0):
  print('loading src = {}'.format(src))
  prv = (src - 1) % 4
  nxt = (src + 1) % 4
  html_header ='<html><body><table>'
  html_header += '<td><button onclick="document.location={}">&lt</button></td>'.format("'/source/{}'".format(prv))
  html_header += '<td><table>'
  html = src_html(src)
  html += groups_html(src)
  html += unused_groups_html(src)
  html_footer = '</table></td>'
  html_footer += '<td><button onclick="document.location={}">&gt</button></td>'.format("'/source/{}'".format(nxt))
  html_footer += '</table>'
  html_footer += '<div>-----Debugging-----</div>'
  html_footer += '<div>Intent:</div>'
  html_footer += '<div id="intent">intent goes here</div>'
  html_footer += '<div>Request:</div>'
  html_footer += '<div id="request">request goes here</div>'
  html_footer += '<div>Response:</div>'
  html_footer += '<div id="response">response goes here</div>'
  html_footer += '<script>{}</script>'.format(SCRIPTS)
  html_footer += '</body></html>'
  return html_header + html + html_footer

if __name__ == '__main__':
  app.run(debug=True)
