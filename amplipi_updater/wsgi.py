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

from flask import Flask, request, render_template, jsonify, make_response

import os
import subprocess
from tempfile import mkdtemp

app = Flask(__name__, static_folder='static')

@app.route('/update')
def update():
  return app.send_static_file('index.html')

@app.route('/update/upload', methods=['POST'])
def start_update():
  try:
    print('got update file')
    os.makedirs('web/uploads', exist_ok=True)
    for f in request.files.values():
      f.save('web/uploads/update.tar.gz')
    temp_dir = mkdtemp()
    print('Attempting to extract firmware to temp directory')
    subprocess.check_call('tar -xf web/uploads/update.tar.gz --directory={}'.format(temp_dir).split())
#    # verification check for special file
#    if 0 != subprocess.call('cat {}/ps_mag1c'.format(temp_dir).split()):
#      raise Exception('update not valid')
#    subprocess.check_call('cp -a {}/python ../'.format(temp_dir).split())
#    subprocess.check_call('sync'.split())
#    subprocess.check_call('chmod +x start_ps.sh'.split())
#    print(request)
#    initiate_software_restart()
    return jsonify({'status': 'ok', 'path': temp_dir}), 200
  except Exception as e:
    print(e)
    app.last_error = str(e)
    return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
  app.run(debug=True, host= 'localhost')

application = app # wsgi expects application var for app
