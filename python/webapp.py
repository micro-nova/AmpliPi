#!/usr/bin/python3

from flask import Flask
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
    onRequest(group + ' vol= ' + obj.value);
  }
  function onGroupMuteChange(obj) {
    var group = obj.id.substring(0,2);
    var mute = obj.checked;
    var gid = group.substring(1,2);
    onRequest(group + ' mute= ' + obj.checked);
  }
  function onAddGroupToSrc(obj) {
    var src = obj.id.substring(1,2);
    var gid = obj.value
    onRequest('Adding g' + gid  + ' to src ' + src);
  }
  function onSrcInputChange(obj) {
    var input = obj.value
    var src = obj.id.substring(1,2);
    onRequest('Changing source ' + src  + ' to use ' + input);
  }
  function onRequest(resp) {
    document.getElementById("request").innerHTML = resp;
  }
  function onResponse(resp) {
    document.getElementById("response").innerHTML = resp;
  }
"""

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
  html_footer += '<div>Request:</div>'
  html_footer += '<div id="request">request goes here</div>'
  html_footer += '<div>Response:</div>'
  html_footer += '<div id="response">response goes here</div>'
  html_footer += '<script>{}</script>'.format(SCRIPTS)
  html_footer += '</body></html>'
  return html_header + html + html_footer

if __name__ == '__main__':
  app.run(debug=True)
