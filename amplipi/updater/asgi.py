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
# web framework
import requests
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from starlette.responses import FileResponse
# web server
import uvicorn
# models
# pylint: disable=no-name-in-module
from pydantic import BaseModel

app = FastAPI()
sse_messages: queue.Queue = queue.Queue()

class ReleaseInfo(BaseModel):
  """ Software Release Information """
  url: str
  version: str

# host all of the static files the client will look for
real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)
app.mount("/static", StaticFiles(directory=f"{dir_path}/static"), name="static")

HOME = f"{os.environ.get('HOME')}/amplipi-dev" # standard install directory

@app.get('/update')
def get_index():
  """ Get the update website """
  # FileResponse knows nothing about the static mount
  return FileResponse(f'{dir_path}/static/index.html')

def save_upload_file(upload_file: UploadFile, destination: pathlib.Path) -> None:
  """ Save the update file """
  try:
    with destination.open("wb") as buffer:
      shutil.copyfileobj(upload_file.file, buffer)
  finally:
    upload_file.file.close()

@app.post("/update/upload")
async def start_upload(file: UploadFile = File(...)):
  """ Start a upload based update """
  print(file.filename)
  try:
    # TODO: use a temp directory and pass it the installation
    os.makedirs('web/uploads', exist_ok=True)
    save_upload_file(file, pathlib.Path('web/uploads/update.tar.gz'))
    # TODO: verify file has amplipi version
    return 200
  except Exception as e:
    print(e)
    return 500

def download(url, file_name):
  """ Download a binary file from @url to @file_name """
  with open(file_name, "wb") as file:
    # get request
    response = requests.get(url)
    # write to file
    file.write(response.content)
    # TODO: verify file has amplipi version

@app.post("/update/download")
async def download_update(info: ReleaseInfo ):
  """ Download the update """
  print(f'downloading update from: {info.url}')
  try:
    os.makedirs('web/uploads', exist_ok=True)
    download(info.url, 'web/uploads/update.tar.gz')
    return 200
  except Exception as e:
    print(e)
    return 500

@app.get('/update/restart')
def restart():
  """ Restart the update service

  This is typically done at the end of an update
  """
  subprocess.Popen(f'python3 {HOME}/scripts/configure.py --restart-updater'.split())
  return {}

TOML_VERSION_STR = re.compile(r'version\s*=\s*"(.*)"')

@app.get('/update/version')
def get_version():
  """ Get the AmpliPi software version from the project TOML file """
  # Assume the application is running in its base directory and check the pyproject.toml file
  # to determine the version. This is needed for a straight github checkout
  # (the common developement paradigm at MicroNova)
  version = 'unknown'
  updater_folder = os.path.dirname(os.path.realpath(__file__))
  try:
    with open(os.path.join(updater_folder, '../..', 'pyproject.toml')) as proj_file:
      for line in proj_file.readlines():
        if 'version' in line:
          match = TOML_VERSION_STR.search(line)
          if match is not None:
            version = match.group(1)
  except:
    pass
  return {'version': version}

def _sse_message(t, msg):
  """ Report an SSE message """
  msg = msg.replace('\n', '<br>')
  sse_msg = {'data' : json.dumps({'message': msg, 'type' : t})}
  sse_messages.put(sse_msg)
  # Give the SSE publisher time to handle the messages, is there a way to just yield?
  time.sleep(0.1)

def _sse_info(msg):
  _sse_message('info', msg)
def _sse_warning(msg):
  _sse_message('warning', msg)
def _sse_error(msg):
  _sse_message('error', msg)
def _sse_done(msg):
  _sse_message('success', msg)
def _sse_failed(msg):
  _sse_message('failed', msg)

@app.route('/update/install/progress')
async def progress(req: Request):
  """ SSE Progress server """
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
  _sse_info(f'Extracting software to temp directory {temp_dir}')
  file_list = subprocess.getoutput('tar -tvf web/uploads/update.tar.gz')
  # get the full name of the release
  release = re.search(r'((micro-nova-)?amplipi-.*?)/', file_list, flags=re.IGNORECASE).group(1)
  _sse_info(f'Got amplipi release: {release}')
  subprocess.run('tar -xf web/uploads/update.tar.gz --directory={}'.format(temp_dir).split(),
                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
  _sse_info('copying software')
  files_to_copy = ' '.join(glob.glob(f'{temp_dir}/{release}/*'))
  subprocess.check_call(f'mkdir -p {home}'.split())
  subprocess.check_call(f'cp -a {files_to_copy}  {home}/'.split())

def indent(p: str):
  """ indent paragraph p """
  return '  ' + '  '.join(p.splitlines(keepends=True))

def install_thread():
  """ Basic tar.gz based installation """

  _sse_info('starting installation')

  try:
    extract_to_home(HOME)
    _sse_info('done copying software')
  except Exception as e:
    _sse_failed(f'installation failed, error extracting release: {e}')
    return

  try:
    # use the configure script provided by the new install to configure the installation
    time.sleep(1) # update was just copied in, add a small delay to make sure we are accessing the new files
    sys.path.insert(0, f'{HOME}/scripts')
    import configure # we want the new configure! # pylint: disable=import-error,import-outside-toplevel
    def progress_sse(tasks):
      for task in tasks:
        _sse_info(task.name)
        output = indent(task.output)
        if task.success:
          print(f'info: {output}')
          _sse_info(output)
        else:
          print(f'error: {output}')
          _sse_error(output)
    # reconfigure and restart everything but the updater
    # (which is restarted later by update/restart)
    success = configure.install(progress=progress_sse)
    if success:
      _sse_done('installation done')
    else:
      _sse_failed('installation failed')
  except Exception as e:
    _sse_failed(f'installation failed, error configuring update: {e}')
    return

@app.get('/update/install')
def install():
  """ Start the install after update is downloaded """
  t = threading.Thread(target=install_thread)
  t.start()
  return {}

if __name__ == '__main__':
  uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)

application = app # asgi assumes application var for app
