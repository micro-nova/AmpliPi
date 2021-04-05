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
import typing
import queue
import pathlib
import shutil
import asyncio
from typing import List

app = FastAPI()
app.sse_messages = queue.Queue()
# TODO: locate the static directory path not depending on cwd
real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)
print(f'{dir_path}/static')
app.mount("/static", StaticFiles(directory=f"{dir_path}/static"), name="static")

@app.get('/update')
def get_index():
  print('get index!')
  return FileResponse('static/index.html')

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
    app.last_error = str(e)
    return 500

def sse_message(t, msg):
  msg = msg.replace('\n', '<br>')
  sse_msg = {'message': msg, 'type' : t}
  app.sse_messages.put(sse_msg)

def sse_info(msg):
  return sse_message('info', msg)
def sse_warning(msg):
  return sse_message('warning', msg)
def sse_error(msg):
  return sse_message('error', msg)
def sse_done(msg):
  return sse_message('success', msg)

@app.route('/update/install/progress')
async def progress(req: Request):
  async def stream():
    try:
      while True:
        if await req.is_disconnected():
          print('disconnected')
          break
        msg = app.sse_messages.get()  # blocks until a new message arrives
        yield msg
        await asyncio.sleep(0.1)
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
  sse_info('starting installation')
  # TODO: add pip install

  home = os.environ.get('HOME') + '/amplipi-dev2' # placeholder

  sse_info(f'home={home}')
  extract_to_home(home)
  sse_done('pretend done')
  return

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

@app.get('/update/install')
def install():
  t = threading.Thread(target=install_thread)
  t.start()
  return {}

if __name__ == '__main__':
  uvicorn.run(app, host="0.0.0.0", port=8000, debug=True, workers=3)

application = app # wsgi expects application var for app
