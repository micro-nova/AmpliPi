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

"""AmpliPi Updater

Simple web based software updates
"""

from flask import Flask, request, render_template, jsonify, Response, stream_with_context

# file and process handling
import os
import subprocess
import glob
import sys
from tempfile import mkdtemp
import re
import json
import threading
import amplipi.updater.sse as sse
import typing

app = Flask(__name__, static_folder='static')

@app.route('/update')
def update():
  return app.send_static_file('index.html')

@app.route('/update/upload', methods=['POST'])
def start_update():
  try:
    print('got update file')
    # TODO: use a temp directory and pass it the installation
    os.makedirs('web/uploads', exist_ok=True)
    for f in request.files.values():
      f.save('web/uploads/update.tar.gz')
    return jsonify({'status': 'ok', 'path': 'web/uploads/'}), 200
  except Exception as e:
    print(e)
    app.last_error = str(e)
    return jsonify({'status': 'error', 'message': str(e)}), 500

def sse_message(t, msg):
  msg = msg.replace('\n', '<br>')
  with app.app_context():
    sse_msg = sse.format({'message': msg, 'type' : t})
    app.install_progress_announcer.announce(sse_msg)

def sse_info(msg):
  return sse_message('info', msg)
def sse_warning(msg):
  return sse_message('warning', msg)
def sse_error(msg):
  return sse_message('error', msg)
def sse_done(msg):
  return sse_message('success', msg)

app.install_progress_announcer = sse.MessageAnnouncer()
@app.route('/update/install/progress')
def progress():
  @stream_with_context
  def stream():
    try:
      messages = app.install_progress_announcer.listen() # returns a queue.Queue
      while True:
        # TODO: break out and send a non-text/event-stream message when we get a done message
        msg = messages.get()  # blocks until a new message arrives
        yield msg
    finally:
      print('progress reporting done')
  # return response with a function
  return Response(stream(), mimetype='text/event-stream')

def extract_to_home(home):
  """ The simple, pip-less install. Extract tarball and copy into users home directory """
  temp_dir = mkdtemp()
  sse_info(f'Extracting software to temp directory {temp_dir}')
  file_list = subprocess.getoutput('tar -tvf web/uploads/update.tar.gz')
  release = re.search(r'(amplipi-.*?)/', file_list).group(1) # get the full name of the release
  sse_info(f'Got amplipi release: {release}')
  out = subprocess.run('tar -xf web/uploads/update.tar.gz --directory={}'.format(temp_dir).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  sse_info('copying software')
  files_to_copy = ' '.join(glob.glob(f'{temp_dir}/amplipi-*/*'))
  subprocess.check_call(f'mkdir -p {home}'.split())
  subprocess.check_call(f'cp -a {files_to_copy}  {home}/'.split())

def indent(p: str):
  """ indent paragraph p """
  return '  ' + '  '.join(p.splitlines(keepends=True))

def install_thread():
  sse_info('starting installation')
  # TODO: add pip install

  home = os.environ.get('HOME') + '/amplipi-dev2' # placeholder

  sse_info(f'home={home}')
  extract_to_home(home)

  sys.path.insert(0, f'{home}/scripts')
  import configure # we want the new configure!
  def progress_sse(tl):
    for task in tl:
      sse_info(task.name)
      output = indent(task.output)
      if task.success:
        sse_info(output)
      else:
        sse_error(output)
  configure.install(progress=progress_sse)

  sse_done('installation done')

@app.route('/update/install')
def install():
  t = threading.Thread(target=install_thread)
  t.start()
  return {}

if __name__ == '__main__':
  app.run(debug=True, host= 'localhost', threaded=True)

application = app # wsgi expects application var for app
