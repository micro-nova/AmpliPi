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

# web framework
from fastapi import FastAPI, Request, File, UploadFile
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
#web server
import uvicorn
# file and process handling
import os
import subprocess
import glob
import sys
from tempfile import mkdtemp
import re
import json
import threading
import time
import queue
import pathlib
import shutil
import asyncio
import pkg_resources
from typing import List

app = FastAPI()
sse_messages: queue.Queue = queue.Queue()

# host all of the static files the client will look for
# TODO: put static files somewhere else?
real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)
app.mount("/static", StaticFiles(directory=f"{dir_path}/static"), name="static")

home = f"{os.environ.get('HOME')}/amplipi-dev" # standard install directory

@app.get('/update')
def get_index():
  print('get index!')
  return FileResponse(f'{dir_path}/static/index.html') # FileResponse knows nothing about the static mount

def save_upload_file(upload_file: UploadFile, destination: pathlib.Path) -> None:
  try:
    with destination.open("wb") as buffer:
      shutil.copyfileobj(upload_file.file, buffer)
  finally:
    upload_file.file.close()

@app.post("/update/upload/")
async def start_update(file: UploadFile = File(...)):
  print(file.filename)
  try:
    # TODO: use a temp directory and pass it the installation
    os.makedirs('web/uploads', exist_ok=True)
    save_upload_file(file, pathlib.Path('web/uploads/update.tar.gz'))
    return 200
  except Exception as e:
    print(e)
    return 500

@app.get('/update/restart')
def restart():
  subprocess.Popen(f'python3 {home}/scripts/configure.py --restart-updater'.split())
  return {}

@app.get('/update/version')
def version():
  version = 'unknown'
  try:
    version = pkg_resources.get_distribution('amplipi').version
  except:
    pass
  return {'version': version}

def sse_message(t, msg):
  msg = msg.replace('\n', '<br>')
  sse_msg = {'data' : json.dumps({'message': msg, 'type' : t})}
  sse_messages.put(sse_msg)
  time.sleep(0.1) # Give the SSE publisher time to handle the messages, is there a way to just yield?

def sse_info(msg):
  sse_message('info', msg)
def sse_warning(msg):
  sse_message('warning', msg)
def sse_error(msg):
  sse_message('error', msg)
def sse_done(msg):
  sse_message('success', msg)
def sse_failed(msg):
  sse_message('failed', msg)

@app.route('/update/install/progress')
async def progress(req: Request):
  async def stream():
    try:
      while True:
        if await req.is_disconnected():
          print('disconnected')
          break
        if not sse_messages.empty():
          msg = sse_messages.get()
          yield msg
        await asyncio.sleep(0.2)
      print(f"Disconnected from client {req.client}")
    except asyncio.CancelledError as e:
      print(f"Disconnected from client (via refresh/close) {req.client}")
      # Do any other cleanup, if any
      raise e
  return EventSourceResponse(stream())

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
  """ Basic tar.gz based installation """

  sse_info('starting installation')

  extract_to_home(home)

  # use the configure script provided by the new install to configure the installation
  sys.path.insert(0, f'{home}/scripts')
  import configure # we want the new configure! # pylint: disable=import-error,import-outside-toplevel
  def progress_sse(tl):
    for task in tl:
      sse_info(task.name)
      output = indent(task.output)
      if task.success:
        print(f'info: {output}')
        sse_info(output)
      else:
        print(f'error: {output}')
        sse_error(output)
  success = configure.install(progress=progress_sse)
  if success:
    sse_done('installation done')
  else:
    sse_failed('installation failed')
  # TODO: now we have to install the updater if needed

@app.get('/update/install')
def install():
  t = threading.Thread(target=install_thread)
  t.start()
  return {}

if __name__ == '__main__':
  uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)

application = app # asgi assumes application var for app
