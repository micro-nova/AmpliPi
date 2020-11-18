#!/usr/bin/python3

from flask import Flask

app = Flask(__name__)

groups = [
    {
      "id": 0,
      "name": "Whole House",
      "zones": [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11
      ],
      "mute": True,
      "source_id": None,
      "vol_delta": -24
    },
    {
      "id": 1,
      "name": "Upstairs",
      "zones": [
        1,
        2,
        3,
        4,
        5,
        6
      ],
      "mute": True,
      "source_id": 1,
      "vol_delta": -24
    },
    {
      "id": 2,
      "name": "Downstairs Apartment",
      "zones": [
        7,
        8,
        9,
        10,
        11
      ],
      "mute": True,
      "source_id": None,
      "vol_delta": -24
    },
    {
      "id": 3,
      "name": "Outside",
      "zones": [
        12,
        13,
        14,
        15,
        16
      ],
      "mute": True,
      "source_id": 1,
      "vol_delta": -40
    }
  ]

def options_html(options):
  html_options = ['<option value="{}">{}</option>'.format(v, k) for k, v in options.items()]
  return '\n'.join(html_options)

def src_html(src):
  source_header = '<tr><td>{}</td><td><select id="src1_ad" onchange="onSrcChange(this);">'.format(src)
  source_footer = '</select></td></tr>'
  options = {
    "" : "None",
    "Jason's iScone" : "stream=44590",
    "Regina Spektor Radio" : "stream=90890",
    "Local" : "local"
  }
  return source_header + options_html(options) + source_footer

def group_html(group):
  # make a volume control bar for a group
  # TODO: make this volume control into its own function once we have to show zones as well
  html_header = '<tr><td>{}</td>'.format(group['name'])
  html = '<td><input id="g{}_vol" type="range" value="{}" onchange="onGroupVolChange(this);" min="-79" max="0"></td>'.format(group['id'], group['vol_delta'])
  html += '<td><span id="g{}_atten">{}</span> dB</td>'.format(group['id'], group['vol_delta'])
  html += '<td><input type="checkbox" id="g{}_mute" checked="{}"></td>'.format(group['id'], str(group['mute']).lower())
  html_footer = '</tr>'
  return html_header + html + html_footer

def unused_groups_html(src):
  header = '<tr><td></td></tr>'
  html = '<tr><td>Add group</td><td><select id="g_add" onchange="onAddGroupToSrc(this);">'
  unused = {g['name'] : g['id'] for g in groups if g['source_id'] != src}
  html += options_html(unused)
  html += '</select></td></tr>'
  footer = ''
  return header + html + footer

def groups_html(src):
  # show all of the groups that are connected to @src
  html_header = ''
  html_groups = ''.join([group_html(group) for group in groups if group['source_id'] == src])
  html_footer = ''
  return html_header + html_groups + html_footer

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
  html_footer += '</table></body></html>'
  return html_header + html + html_footer

if __name__ == '__main__':
  app.run(debug=True)
