#!/usr/bin/python3

from flask import Flask

app = Flask(__name__)


def options_html(options):
  html_options = ['<option value="{}">{}</option>'.format(v, k) for k, v in options.items()]
  return '\n'.join(html_options)

def src_html():
  src = 1
  source_header = '<tr><td>{}</td><td><select id="src1_ad" onchange="onAdChange(this);">'.format(src)
  source_footer = '</select></td></tr>'
  options = {
    "" : "None",
    "Jason's iScone" : "stream=44590",
    "Regina Spektor Radio" : "stream=90890",
    "Local" : "local"
  }
  return source_header + options_html(options) + source_footer

@app.route('/')
def index():
  html_header = '<html><body><table>'
  html_footer = '</table></body></html>'
  return html_header + src_html() + html_footer

if __name__ == '__main__':
  app.run(debug=True)
