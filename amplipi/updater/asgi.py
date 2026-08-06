#!/usr/bin/python3

# AmpliPi Home Audio
# Copyright (C) 2022 MicroNova LLC
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
import logging
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

import hashlib
import lzma
import io

import configparser

# web framework
import requests
from fastapi import FastAPI, Request, File, UploadFile, Depends, APIRouter, Response
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from sse_starlette.sse import EventSourceResponse
from starlette.responses import FileResponse
# web server
import uvicorn
# models
# pylint: disable=no-name-in-module
from pydantic import BaseModel
from typing import Optional, Callable
from enum import Enum

from ..auth import CookieOrParamAPIKey, router as auth_router, set_password_hash, unset_password_hash, \
  NotAuthenticatedException, not_authenticated_exception_handler, create_access_key

app = FastAPI()
router = APIRouter(dependencies=[Depends(CookieOrParamAPIKey)])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

app.add_exception_handler(NotAuthenticatedException, not_authenticated_exception_handler)

sse_messages: queue.Queue = queue.Queue()


class SSEChannel:
  """ Bundles the queue/in-progress-flag/latest-status trio a long-running background job reports
  its progress through, plus the polling generator that serves it as SSE to a native EventSource.
  /update/flash and /update/download/images each run their own long job in a background thread
  (flash_partition_thread/download_images_thread), separate from sse_messages/install, so a
  dropped/reconnecting browser can't interrupt or duplicate the actual work - watched via a paired
  GET .../progress endpoint rather than tying the work to any one HTTP connection's lifetime. This
  used to be two separate copies of identical plumbing (globals, message-formatting helpers, and
  the SSE generator itself) differing only in which globals they closed over; this class replaces
  both, instantiated once per job below. """

  def __init__(self, idle_message: str):
    self.messages: queue.Queue = queue.Queue()
    self.in_progress = threading.Event()
    """A guard against multiple runs of the same process (ie, no double flashing the inactive slot)"""

    self.latest_status: dict = {}
    """
      The most recent message from self.messages,
      stored here so that late subscribers can see where the process is
      without waiting for the next printed event message
    """

    self.idle_message = idle_message
    """Message shown when there is nothing in progress"""

  def _message(self, t: str, msg: str):
    msg = msg.replace('\n', '<br>')
    sse_msg = {'data': json.dumps({'message': msg, 'type': t})}
    self.latest_status['data'] = sse_msg['data']
    self.messages.put(sse_msg)

  def info(self, msg: str):
    self._message('info', msg)

  def error(self, msg: str):
    self._message('error', msg)

  def done(self, msg: str):
    self._message('success', msg)

  def start(self, target: Callable, args: tuple = ()) -> bool:
    if self.in_progress.is_set():
      return False
    self.in_progress.set()
    while not self.messages.empty():
      self.messages.get()
    self.latest_status.clear()
    threading.Thread(target=target, args=args).start()
    return True

  async def stream(self, req: Request):
    """ Async generator for an EventSourceResponse - catches a late subscriber up on current
    status immediately, then polls for new messages every 0.2s until the client disconnects. """
    if 'data' in self.latest_status:
      yield {'data': self.latest_status['data']}
      if not self.in_progress.is_set():
        # That cached message was the terminal result of a run that's already done - nothing else
        # is ever coming, so close now instead of polling forever for a late subscriber.
        return
    elif not self.in_progress.is_set():
      yield {'data': json.dumps({'message': self.idle_message, 'type': 'info'})}
      return
    try:
      while True:
        if await req.is_disconnected():
          logger.info('disconnected')
          break
        if not self.messages.empty():
          yield self.messages.get()
        await asyncio.sleep(0.2)
      logger.info(f"Disconnected from client {req.client}")
    except asyncio.CancelledError as e:
      logger.exception(f"Disconnected from client (via refresh/close) {req.client}")
      raise e


flash_channel = SSEChannel(idle_message='No flash in progress')
download_channel = SSEChannel(idle_message='No download in progress')


def validate_logging_ini():
  """Fallback in case the ini file or any individual header  doesn't exist, set to default settings. Only really comes up during tests."""
  tmp = '/tmp/logging.ini.tmp'
  ini = '/var/log/logging.ini'
  conf = configparser.ConfigParser(strict=False, allow_no_value=True)

  with open(tmp, "+w", encoding="utf-8") as file:
    if os.path.exists(ini):
      conf.read(ini)
    else:
      conf.read(file)

    if not conf.has_section("logging"):
      conf.add_section("logging")

    if not conf.has_option("logging", "auto_off_delay"):
      conf.set("logging", "auto_off_delay", "14")
    auto_off_delay = conf.get("logging", "auto_off_delay", fallback="14")
    if not auto_off_delay.isdigit() and bool(re.fullmatch(r'\d*\.\d+', auto_off_delay)):
      # regex to check decimal state, this would lead to "123.45" and ".45" being true but not "123."
      # Exclude anything that isdigit() as to not overwrite valid user settings
      rounded = round(float(auto_off_delay)) if round(float(auto_off_delay)) > 0 else 1  # Avoid instances where it could be zero as to not set the "do not deactivate" setting
      conf.set("logging", "auto_off_delay", str(rounded))
    elif not auto_off_delay.isdigit():  # Cannot be merged with the first check in an OR case as valid regex catches would be intercepted by that
      conf.set("logging", "auto_off_delay", "14")
    conf.write(file)

  subprocess.run(['sudo', 'mv', tmp, ini], check=True)


def journald_configparser() -> configparser.ConfigParser:
  """ ConfigParser for journald.conf. systemd's keys are case-sensitive (Storage=, not
  storage=), unlike ConfigParser's default of lowercasing every option name, so this preserves
  case - otherwise every key we write gets silently ignored by journald as unrecognized. """
  conf = configparser.ConfigParser(strict=False, allow_no_value=True)
  conf.optionxform = str
  return conf


# Raspberry Pi OS ships with /usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf,
# which unconditionally sets Storage=volatile. Files in journald.conf.d/ take precedence over the
# main /etc/systemd/journald.conf file regardless of directory, so setting Storage there (as this
# code used to) doesn't matter. The only way to set this to what we want is by editing that file instead.
JOURNALD_RASPI_CONF = '/etc/systemd/journald.conf.d/80-raspi-config-journal-storage.conf'


def _read_journald_storage_persistence() -> Optional[str]:
  """ Returns the Storage= value from our storage drop-in, or None if it doesn't exist/can't be read """
  if not os.path.exists(JOURNALD_RASPI_CONF):
    return None
  conf = journald_configparser()
  conf.read(JOURNALD_RASPI_CONF)
  return conf.get('Journal', 'Storage', fallback=None)


def _write_journald_storage_persistence(storage: str):
  """ Write our journald settings file with the expected log persistence state, then restart journald """
  os.makedirs(os.path.dirname(JOURNALD_RASPI_CONF), exist_ok=True)
  tmp = '/tmp/journald-settings.tmp'
  with open(tmp, 'w', encoding='utf-8') as f:
    f.write(f'# Created/managed by AmpliPi (also used by raspi-config)\n\n[Journal]\nStorage={storage}\n')
  subprocess.run(['sudo', 'mv', tmp, JOURNALD_RASPI_CONF], check=True)
  subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-journald'], check=True)
  subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-journal-flush.service'], check=True)


def validate_journald_conf():
  """Fallback in case the config file or any individual header doesn't exist, set to default settings"""
  tmp = '/tmp/journald.conf.tmp'
  conf = '/etc/systemd/journald.conf'
  confparse = journald_configparser()

  with open(tmp, "+w", encoding="utf-8") as file:
    if os.path.exists(conf):
      confparse.read(conf)
    else:
      confparse.read(file)

    if not confparse.has_section("Journal"):
      confparse.add_section("Journal")

    # Set everything else to default while preserving user settings
    if not confparse.has_option("Journal", "SyncIntervalSec"):
      confparse.set('Journal', 'SyncIntervalSec', '30s')
    if not confparse.has_option("Journal", "SystemMaxUse"):
      confparse.set('Journal', 'SystemMaxUse', '64M')
    if not confparse.has_option("Journal", "RuntimeMaxUse"):
      confparse.set('Journal', 'RuntimeMaxUse', '64M')
    if not confparse.has_option("Journal", "ForwardToConsole"):
      confparse.set('Journal', 'ForwardToConsole', 'no')
    if not confparse.has_option("Journal", "ForwardToWall"):
      confparse.set('Journal', 'ForwardToWall', 'no')

    confparse.write(file)
  subprocess.run(['sudo', 'mv', tmp, conf], check=True)

  if _read_journald_storage_persistence() not in ('volatile', 'persistent'):
    _write_journald_storage_persistence('persistent')


# host all of the static files the client will look for
real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)
app.mount("/static", StaticFiles(directory=f"{dir_path}/static"), name="static")

INSTALL_DIR = os.getenv('INSTALL_DIR', os.getcwd())
USER_CONFIG_DIR = os.path.join('/data', '.config', 'amplipi')

# if we have a broken configuration, the updater should still function
# as a failsafe. This structure & some code was copied from
# https://github.com/micro-nova/AmpliPi/blob/8368a4a79f536757d7f301612494b6788355aafc/amplipi/app.py#L753
# except that we don't handle typing or HTML here - this is MVP updater code.
identity = {
  'name': 'AmpliPi',
  'website': 'http://www.amplipi.com',
  'html_logo': '<span class="text-white">Ampli</span><span class="text-danger">Pi</span>',
}
try:
  with open(os.path.join(USER_CONFIG_DIR, 'identity'), encoding='utf-8') as f:
    proposed_identity = json.load(f)
    identity.update(proposed_identity)
except FileNotFoundError:
  pass
except Exception as e:
  logger.exception(f'Error loading identity file: {e}')


class Persist_Logs(BaseModel):
  """Basemodel that consists of a bool and int, used to change different config files around the system via POST /settings/persist_logs"""
  persist_logs: bool
  auto_off_delay: int


@router.get("/settings/persist_logs")
def get_log_persist_state():
  """
  Checks our journald.conf.d settings file to find if the current storage setting is persistent
  and returns a bool. Note that returning false doesn't necessarily mean that logs are set to
  volatile, and could just mean that the config file is missing the line being read
  """
  validate_journald_conf()

  validate_logging_ini()
  logconf = configparser.ConfigParser(strict=False, allow_no_value=True)
  logconf.read('/var/log/logging.ini')

  # Fallback set is the default value of the Storage variable under the Journal header of the conf file
  # Used when the variable cannot be read but the file itself can (implying that the variable is missing, and should be set to a default)
  ret = Persist_Logs(persist_logs=_read_journald_storage_persistence() == "persistent", auto_off_delay=logconf.get("logging", "auto_off_delay", fallback="14"),)
  return ret


@router.post("/settings/persist_logs")
def toggle_persist_logs(data: Persist_Logs):
  """Toggles the option within journald to save logs to memory or storage, and sets the length of time before that setting is reset to volatile"""
  try:
    # Just in case
    validate_logging_ini()
    validate_journald_conf()

    state = get_log_persist_state()

    if state.persist_logs != data.persist_logs:
      # goal_value is true if you wish to turn persistent logging on and false if you wish to turn it off
      _write_journald_storage_persistence('persistent' if data.persist_logs else 'volatile')
      logger.info(f"persist_logs set to {data.persist_logs}")
    else:
      logger.info("persist_logs unchanged")

    if state.auto_off_delay != data.auto_off_delay:
      logconf = '/var/log/logging.ini'
      logtmp = '/tmp/logging.ini.tmp'
      log = configparser.ConfigParser(strict=False, allow_no_value=True)
      log.read(logconf)
      log.set('logging', 'auto_off_delay', f"{data.auto_off_delay}")  # Accept auto_off_delay as an int for type checking, parse to str for configParser validity
      with open(logtmp, 'w', encoding='utf-8') as file:
        log.write(file)
      subprocess.run(['sudo', 'mv', logtmp, logconf], check=True)
      logger.info(f"auto_off_delay set to {data.auto_off_delay}")

    else:
      logger.info("auto_off_delay unchanged")

    # Add the persist state to /data so we set proper persistence on slot swap
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)
    with open(os.path.join(USER_CONFIG_DIR, 'persist_logs.json'), 'w', encoding='utf-8') as f:
      json.dump({'persist_logs': data.persist_logs, 'auto_off_delay': data.auto_off_delay}, f)
  except Exception as exc:
    logger.exception(str(exc))
    return 500


@router.get('/update')
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


def persist_logs_during_update():
  """Used during system updates to ensure persist logs is activated and has a minimum delay"""
  persist_data = get_log_persist_state()
  existing_persist = persist_data.persist_logs
  existing_delay = persist_data.auto_off_delay
  # If persist logs is already on and has a larger delay, keep that delay; otherwise ensure it has our sane minimum for support
  if existing_persist and (existing_delay > 3 or existing_delay == 0):
    data = Persist_Logs(persist_logs=True, auto_off_delay=existing_delay)
    toggle_persist_logs(data=data)
  else:
    # Three days is an arbitrary number, picked to ensure the next few days of usage post-update are captured for support cases
    data = Persist_Logs(persist_logs=True, auto_off_delay=3)
    toggle_persist_logs(data=data)


@router.post("/update/upload")
async def start_upload(file: UploadFile = File(...)):
  """ Start a upload based update """
  logger.info(file.filename)
  try:
    persist_logs_during_update()
    # TODO: use a temp directory and pass it the installation
    os.makedirs('web/uploads', exist_ok=True)
    save_upload_file(file, pathlib.Path('web/uploads/update.tar.gz'))
    # TODO: verify file has amplipi version
    return 200
  except Exception as e:
    logger.exception(e)
    return 500


@router.get('/update/restart')  # an old version accidentally used get instead of post
@router.post('/update/restart')
def restart():
  """ Restart the OS and all of the AmpliPi services including the updater.

  This is typically done at the end of an update
  """
  # start the restart, and return immediately (hopefully before the restart process begins)
  subprocess.Popen(f'python3 {INSTALL_DIR}/scripts/configure.py --restart-updater'.split())
  return 200


TOML_VERSION_STR = re.compile(r'version\s*=\s*"(.*)"')


@router.get('/update/version')
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
  sse_msg = {'data': json.dumps({'message': msg, 'type': t})}
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


@router.route('/update/install/progress')
async def progress(req: Request):
  """ SSE Progress server """
  async def stream():
    try:
      while True:
        if await req.is_disconnected():
          logger.info('disconnected')
          break
        if not sse_messages.empty():
          msg = sse_messages.get()
          yield msg
        await asyncio.sleep(0.2)
      logger.info(f"Disconnected from client {req.client}")
    except asyncio.CancelledError as e:
      logger.exception(f"Disconnected from client (via refresh/close) {req.client}")
      # Do any other cleanup, if any
      raise e
  return EventSourceResponse(stream())


@router.route('/update/flash/progress')
async def flash_progress(req: Request):
  """ SSE Progress server for /update/flash - same shape as /update/install/progress. Being a
  plain GET consumed via EventSource (rather than the POST-with-inline-SSE-response the actual
  flash used to be) means the browser can freely reconnect here on any dropped connection without
  affecting flash_partition_thread(), which keeps running regardless in its own thread. """
  return EventSourceResponse(flash_channel.stream(req))


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
    extract_to_home(INSTALL_DIR)
    _sse_info('done copying software')
  except Exception as e:
    _sse_failed(f'installation failed, error extracting release: {e}')
    return

  try:
    # use the configure script provided by the new install to configure the installation
    time.sleep(1)  # update was just copied in, add a small delay to make sure we are accessing the new files
    sys.path.insert(0, f'{INSTALL_DIR}/scripts')
    import configure  # we want the new configure! # pylint: disable=import-error,import-outside-toplevel

    def progress_sse(tasks):
      for task in tasks:
        _sse_info(task.name)
        output = indent(task.output)
        if task.success:
          logger.info(f'info: {output}')
          _sse_info(output)
        else:
          logger.warning(f'error: {output}')
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


@router.get('/update/install')
def install():
  """ Start the install after update is downloaded """
  t = threading.Thread(target=install_thread)
  t.start()
  return {}


class PasswordInput(BaseModel):
  password: str


@router.post('/password')
def set_admin_password(input: PasswordInput):
  """ Sets the admin password and (re)sets its access key."""
  # At present, we don't support multiple human users, just an "admin".
  # This field is potentially still used with API keys though, so it's worthwhile to distinguish
  # (and also permits us forward-looking flexibility.)
  username = "admin"
  if len(input.password) == 0:
    unset_password_hash(username)
  else:
    set_password_hash(username, input.password)
    create_access_key(username)


@router.post('/support')
def request_support():
  """ Creates a support tunnel request. """
  try:
    out = subprocess.run(
      '/opt/support_tunnel/venv/bin/python3 -m invoke request'.split(),
      capture_output=True,
      cwd='/opt/support_tunnel',
      timeout=120,
      check=True
    )
    return Response(content=f"{out.stdout.decode('utf')}", media_type="text/html")
  except Exception as e:
    return Response(content=f"failed to request tunnel: {e}", media_type="text/html")


class ImageMetadata(BaseModel):
  """ Expected checksum/size of a single image file (root or boot) from the update manifest """
  filename: str
  sha256: str
  size: int


class UpdateManifest(BaseModel):
  """ Schema for manifest.json, contains size and checksum info for the image(s). Root is required, boot is optional """
  version: str
  boot: Optional[ImageMetadata] = None
  root: ImageMetadata


def _load_manifest(path: str) -> Optional[UpdateManifest]:
  """ Loads an update's manifest.json as an UpdateManifest object for easy reading """
  if not os.path.exists(path):
    return None
  try:
    with open(path, encoding="UTF-8") as f:
      return UpdateManifest(**json.load(f))
  except Exception:
    return None


class BootPair(BaseModel):
  """
    Partition mappings for the boot and root partitions of OS A and B
    Given that there's only two slots, this is just a schema for hardcoding the mappings for the BootSlot Enum
  """
  boot: int
  root: int


class BootSlot(Enum):
  """
    RPi A:B tryboot has two boot slots: A and B
    This enum contains the partition mappings for both slots
  """
  A = BootPair(boot=2, root=5)
  B = BootPair(boot=3, root=6)


class PartitionSize(Enum):
  """
    The size of boot and root partitions, used to provide a progress bar for the reflashing step
    Hardcoded using the byte size of the uncompressed images
  """
  BOOT = 268435456
  ROOT = 11470372864


def get_checksum(path: str, total_size: int, progress_cb: Optional[Callable] = None) -> str:
  """ sha256 checksum of a file (path) in 4MB chunks, reporting progress via progress_cb(done, total) callback as it goes """
  h = hashlib.sha256()
  hashed_size = 0
  with open(path, "rb") as f:
    while chunk := f.read(4 * 1024 * 1024):
      h.update(chunk)
      hashed_size += len(chunk)
      if progress_cb:
        progress_cb(hashed_size, total_size)
    return h.hexdigest()


class ImageDownloadInfo(BaseModel):
  """ Release asset URLs to populate /data/update/ from, matching what /update/flash later
  expects to find there. `boot_url` is optional, mirroring UpdateManifest.boot - a root-only
  update doesn't need a new boot image. Getting these URLs (e.g. by polling the GitHub releases
  API) is not this endpoint's job - see the "Backend GitHub polling" gap in
  docs/ab_update_design.md. `expected_version`, if given, is checked against the downloaded
  manifest's own `version` field before the (large) root/boot images are downloaded - protects
  against a caller's idea of "the release I'm downloading" silently drifting from what's actually
  behind these URLs (stale cache, wrong asset, etc.) without wasting bandwidth on gigabytes that
  would just get rejected anyway. Optional since callers without a specific release in mind (e.g.
  pointing at an arbitrary test URL) have nothing meaningful to compare against. """
  manifest_url: str
  root_url: str
  boot_url: Optional[str] = None
  expected_version: Optional[str] = None


def download_images_thread(info: ImageDownloadInfo):
  try:
    _download_images_body(info)
  finally:
    download_channel.in_progress.clear()


def _download_images_body(info: ImageDownloadInfo):
  """
    Download manifest.json, root.img.xz, and (optionally) boot.img.xz from the given URLs into
    /data/update/
  """
  dest_dir = "/data/update"

  # Set up the SSE event loop with a throttle of 0.5 messages per second (1 message every two seconds)
  progress_state: dict = {}
  progress_lock = threading.Lock()
  stop_heartbeat = threading.Event()

  def progress(done, total, label):
    with progress_lock:
      progress_state[label] = (done, total)

  def progress_done(label):
    # Explicitly report 100% here rather than relying on the heartbeat to have caught it - a small
    # asset (e.g. manifest.json vs. root's several GB) can finish faster than the heartbeat's 2s
    # sampling interval, meaning the heartbeat would never once have observed it.
    download_channel.info(f'{label}: {1.0:.1%}')
    with progress_lock:
      progress_state.pop(label, None)

  def heartbeat():
    while not stop_heartbeat.wait(2.0):
      with progress_lock:
        items = list(progress_state.items())
      for label, (done, total) in items:
        download_channel.info(f'{label}: {done / total:.1%}')

  def download_asset(url: str, dest: str, label: str):
    response = requests.get(url, stream=True, timeout=(10, 30))
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    written = 0
    with open(dest, "wb") as f:
      for chunk in response.iter_content(chunk_size=4 * 1024 * 1024):
        if chunk:
          f.write(chunk)
          written += len(chunk)
          # content-length isn't guaranteed to be present (e.g. a chunked transfer-encoding
          # response omits it) - only report a percentage when we actually know the total
          if total:
            progress(written, total, label)
    if total:
      progress_done(label)

  def clear_if_stale(manifest_path: str):
    """
      Compare /data/update/manifest.json's version with info.expected_version.
      If those versions aren't the same, delete the contents of /data/update,
      if they are the same then keep the current update package and skip the download
    """
    existing = _load_manifest(manifest_path)  # None (unreadable/corrupt/missing) is treated as stale regardless
    if existing is None:
      if not os.path.exists(manifest_path):
        return  # nothing staged at all - nothing to clear
    elif info.expected_version is not None and existing.version == info.expected_version:
      return
    for filename in ("manifest.json", "root.img.xz", "boot.img.xz"):
      path = os.path.join(dest_dir, filename)
      if os.path.exists(path):
        os.remove(path)

  heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
  heartbeat_thread.start()
  try:
    os.makedirs(dest_dir, exist_ok=True)
    manifest_path = os.path.join(dest_dir, "manifest.json")
    clear_if_stale(manifest_path)
    download_asset(info.manifest_url, manifest_path, "Downloading manifest")

    manifest = _load_manifest(manifest_path)
    if manifest is None:
      raise RuntimeError("Downloaded manifest could not be parsed")

    if info.expected_version is not None and manifest.version != info.expected_version:
      raise RuntimeError(
        f"Downloaded manifest is for version {manifest.version}, expected {info.expected_version} - refusing to download root/boot images for the wrong release")

    # Check for available space before downloading
    # Due to the update commit service deleting staged updates, this is only able to be tripped by a user overfilling their /data directory
    needed = manifest.root.size + (manifest.boot.size if manifest.boot is not None else 0)
    available = shutil.disk_usage(dest_dir).free
    if available < needed:
      raise RuntimeError(
        f"Not enough free space on /data to download this update "
        f"(need {needed / 1024**3:.2f} GB, have {available / 1024**3:.2f} GB free) - "
        f"free up space on /data and try again")

    download_asset(info.root_url, os.path.join(dest_dir, "root.img.xz"), "Downloading root image")
    if info.boot_url is not None:
      download_asset(info.boot_url, os.path.join(dest_dir, "boot.img.xz"), "Downloading boot image")

    download_channel.done('Download complete!')
  except Exception as e:
    download_channel.error(str(e))
  finally:
    stop_heartbeat.set()
    heartbeat_thread.join(timeout=3)


@router.post('/update/download/images')
def start_download_images(info: ImageDownloadInfo):
  """
    Start downloading manifest.json, root.img.xz, and (optionally) boot.img.xz into /data/update/ in
    the background and return immediately; watch progress via
    GET /update/download/images/progress

    Refuses to start a second download while one's already running - concurrent writes to the same
    /data/update/ files would corrupt each other.
  """
  # This endpoint uses the same pattern as /update/flash
  if not download_channel.start(target=download_images_thread, args=(info,)):
    return {'started': False, 'reason': 'a download is already in progress'}
  return {'started': True}


@router.route('/update/download/images/progress')
async def download_images_progress(req: Request):
  """ SSE Progress server for /update/download/images """
  return EventSourceResponse(download_channel.stream(req))


@router.get('/update/staged')
def staged_update():
  """
    Reports whether /data/update/manifest.json already exists and, if so, what version it
    declares
  """
  manifest = _load_manifest("/data/update/manifest.json")
  if manifest is None:
    return {'staged': False, 'version': None}
  return {'staged': True, 'version': manifest.version}


def flash_partition_thread(tryboot: bool):
  """
    Validate the update package downloaded to /data/update and then flash the inactive boot slot.
    Runs in its own background thread (like install_thread()), started by POST /update/flash and
    watched via GET /update/flash/progress so that a dropped connection doesn't lead to a failed or duplicated update.
    tryboot arg is used to toggle whether or not "sudo reboot '0 tryboot'" is run at the end of flashing to actually change slots
    tryboot is false by default to simplify manual invocation during development
    see the BootSlot enum for slot mapping details
  """
  try:
    _flash_partition_body(tryboot)
  finally:
    flash_channel.in_progress.clear()


def _flash_partition_body(tryboot: bool):
  try:
    persist_logs_during_update()
  except Exception as e:
    logger.exception(f'Failed to enable persist_logs before flashing: {e}')

  def flash(image: str, partition: int, total: int, progress_cb: Optional[Callable] = None):
    """ Decompress an image and stream it straight into /dev/mmcblk0p{partition} via dd, reporting
    progress via the progress_cb(written, total) callback as it goes """
    written = 0
    dd = subprocess.Popen(
      # conv=fsync forces dd to flush all writes to disk before it exits, so a successful return
      # here means the image is actually durable on the card, not just sitting in a write cache
      ['sudo', 'dd', f'of=/dev/mmcblk0p{partition}', 'bs=4M', 'conv=fsync'],
      stdin=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # This is chunked both to prevent loading a massive (potentially too large) file into memory all at once and to provide chunk-by-chunk feedback to the user for how the update is going
    with lzma.open(image, 'rb') as src:
      while chunk := src.read(4 * 1024 * 1024):
        dd.stdin.write(chunk)
        written += len(chunk)
        if progress_cb:
          progress_cb(written, total)
    dd.stdin.close()
    dd.wait()
    if dd.returncode != 0:
      raise RuntimeError(f'dd failed: {dd.stderr.read().decode()}')

  def set_persist_logs():
    """ persist logs after an update, set auto_off_delay to 14 unless the user's own delay is larger or 0 (no auto_off) """
    persist_logs = False
    auto_off_delay = 14
    state_file = os.path.join(USER_CONFIG_DIR, 'persist_logs.json')
    if os.path.exists(state_file):
      with open(state_file, encoding='utf-8') as f:
        state = json.load(f)
      persist_logs = state.get('persist_logs', False)
      auto_off_delay = state.get('auto_off_delay', 14)

    dropin_path = '/data/tmpmnt' + JOURNALD_RASPI_CONF
    subprocess.run(['sudo', 'mkdir', '-p', os.path.dirname(dropin_path)], check=True)
    journald_config_content = (
      '# Created/managed by AmpliPi (also used by raspi-config)\n\n'
      f"[Journal]\nStorage={'persistent' if persist_logs else 'volatile'}\n"
    )
    subprocess.run(['sudo', 'tee', dropin_path], input=journald_config_content, text=True, check=True)

    log_path = '/data/tmpmnt/var/log/logging.ini'
    existing_log = subprocess.run(['sudo', 'cat', log_path], capture_output=True, text=True).stdout
    logconf = configparser.ConfigParser(strict=False, allow_no_value=True)
    logconf.read_string(existing_log)
    if not logconf.has_section('logging'):
      logconf.add_section('logging')
    logconf.set('logging', 'auto_off_delay', str(auto_off_delay))

    log_buf = io.StringIO()
    logconf.write(log_buf)
    subprocess.run(['sudo', 'tee', log_path], input=log_buf.getvalue(), text=True, check=True)

  manifest_dir = "/data/update/manifest.json"
  root_img = "/data/update/root.img.xz"
  boot_img = "/data/update/boot.img.xz"
  # BOOT_SLOT is an env_var set by the active boot partition's commandline.txt
  if os.environ.get("BOOT_SLOT") != "A" and os.environ.get("BOOT_SLOT") != "B":
    flash_channel.error("Boot slot could not be read")
    return

  active_slot = BootSlot.A if os.environ.get("BOOT_SLOT") == "A" else BootSlot.B
  target_slot = BootSlot.B if os.environ.get("BOOT_SLOT") == "A" else BootSlot.A

  # Some chunks of decompression move faster than others, make sure that the frontend gets a message every
  # 2 seconds as long as the process is ongoing to avoid the illusion of a hang or failed update
  progress_state: dict = {}
  progress_lock = threading.Lock()
  stop_heartbeat = threading.Event()

  def progress(done, total, label):
    with progress_lock:
      progress_state[label] = (done, total)

  def progress_done(label):
    # Explicitly report 100% here rather than relying on the heartbeat to have caught it
    # Boot is VERY small relative to root and thus easy to miss in the event loop
    flash_channel.info(f'{label}: {1.0:.1%}')
    # Forcibly send the 100% complete message for a given job and then end the job
    # Without this, every future process will also print "{process} 100%" during every heartbeat
    with progress_lock:
      progress_state.pop(label, None)

  def heartbeat():
    while not stop_heartbeat.wait(2.0):
      with progress_lock:
        items = list(progress_state.items())
      for label, (done, total) in items:
        flash_channel.info(f'{label}: {done / total:.1%}')

  def do_checks():
    """
      Load manifest.json and verify the downloaded root (and boot, if present) images actually
      match the size/checksum it declares, before anything is allowed to touch a partition
    """
    manifest = None
    if os.path.exists(manifest_dir):
      with open(manifest_dir, "r", encoding="UTF-8") as f:
        manifest = UpdateManifest(**json.load(f))

    if manifest is None:
      raise RuntimeError("Manifest unable to load due to error")
    if not os.path.exists(root_img):
      raise RuntimeError("Root image not found")

    root_size = os.path.getsize(root_img)
    if manifest.root.size != root_size:
      raise RuntimeError("Root image size does not match expected value")
    if manifest.root.sha256 != get_checksum(root_img, root_size, lambda done, total: progress(done, total, "Verifying root image")):
      raise RuntimeError("Root image checksum does not match expected value")
    progress_done("Verifying root image")

    if manifest.boot is not None:
      if not os.path.exists(boot_img):
        raise RuntimeError("Boot image expected but not found")
      boot_size = os.path.getsize(boot_img)
      if manifest.boot.size != boot_size:
        raise RuntimeError("Boot image size does not match expected value")
      if manifest.boot.sha256 != get_checksum(boot_img, boot_size, lambda done, total: progress(done, total, "Verifying boot image")):
        raise RuntimeError("Boot image checksum does not match expected value")
      progress_done("Verifying boot image")

    return manifest

  heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
  heartbeat_thread.start()
  try:
    try:
      manifest = do_checks()
      flash_channel.info('All checks successful!')
    except Exception as e:
      flash_channel.error(str(e))
      return

    # Congrats, everything is in place, you've survived this far, time to actually do anything at all
    try:
      flash_channel.info(f'Currently on slot {active_slot.name}, will flash slot {target_slot.name} (root p{target_slot.value.root}, boot p{target_slot.value.boot})')

      flash_channel.info('Flashing root image...')
      flash(root_img, target_slot.value.root, PartitionSize.ROOT.value, lambda done, total: progress(done, total, 'Flashing root'))
      progress_done('Flashing root')
      flash_channel.info('Root image flashed')

      if manifest.boot is not None:
        flash_channel.info('Flashing boot image...')
        flash(boot_img, target_slot.value.boot, PartitionSize.BOOT.value, lambda done, total: progress(done, total, 'Flashing boot'))
        progress_done('Flashing boot')
        flash_channel.info('Boot image flashed')
    except Exception as e:
      flash_channel.error(f'Update failed mid-flash: {e}')
      return
  finally:
    # No more percentage-based progress after this point (patching is discrete step messages,
    # not a byte counter), so the heartbeat's job is done regardless of which path got here.
    stop_heartbeat.set()
    heartbeat_thread.join(timeout=3)

  try:
    # /data/tmpmnt is the mountpoint used for whichever partition is being operated on at the time, either the inactive boot or root
    # Necessary for making sure individual files have the proper details such as making sure the boot points to the correct root partition
    flash_channel.info('Patching boot partition...')
    if not os.path.exists("/data/tmpmnt"):
      os.mkdir("/data/tmpmnt")
    subprocess.run(["sudo", "umount", "/data/tmpmnt"])  # In case the user put something there
    subprocess.run(["sudo", "mount", f"/dev/mmcblk0p{target_slot.value.boot}", "/data/tmpmnt"], check=True)

    # The captured boot image carries whatever label its source partition had when it was built,
    # which isn't necessarily this slot's - relabel to match the slot actually being written here,
    # so blkid/lsblk aren't misleading about which slot is which. Safe to run against a mounted
    # vfat filesystem.
    subprocess.run(["sudo", "fatlabel", f"/dev/mmcblk0p{target_slot.value.boot}", f"BOOT-{target_slot.name}"], check=True)

    # The section below used to be more pythonic by using with open(...) as f:, reading, and writing to the file
    # That is no longer the case as all of these operations require higher privs to touch a boot partition that doesn't belong to the user doing the changes
    if manifest.boot is not None:
      flash_channel.info('Patching cmdline.txt')
      content = subprocess.run(['sudo', 'cat', '/data/tmpmnt/cmdline.txt'], capture_output=True, text=True, check=True).stdout
      content = re.sub(rf'(root=PARTUUID=[0-9a-f]+-0){active_slot.value.root}\b', rf'\g<1>{target_slot.value.root}', content)
      content = content.replace(f"BOOT_SLOT={active_slot.name}", f"BOOT_SLOT={target_slot.name}")
      subprocess.run(['sudo', 'tee', '/data/tmpmnt/cmdline.txt'], input=content, text=True, check=True)

    flash_channel.info('Patching root partition...')
    # All systems originate from the same ancestor image. The following tools cleanse the root partition of identifiable info
    # so that A and B don't have a case of mistaken identity by sharing these identifiers
    fsck = subprocess.run(["sudo", "e2fsck", "-p", f"/dev/mmcblk0p{target_slot.value.root}"])
    if fsck.returncode not in (0, 1):
      raise RuntimeError(f"e2fsck exited with code {fsck.returncode} on /dev/mmcblk0p{target_slot.value.root}")
    subprocess.run(["sudo", "tune2fs", "-U", "random", f"/dev/mmcblk0p{target_slot.value.root}"], check=True)
    # Same identification concern as is handled by the fatlabel subprocess above
    subprocess.run(["sudo", "e2label", f"/dev/mmcblk0p{target_slot.value.root}", f"ROOT-{target_slot.name}"], check=True)

    # Create the update-pending file that the update validation service will use to detect an update happened post-reboot
    subprocess.run(['sudo', 'tee', '/data/tmpmnt/update-pending'], input=str(target_slot.value.boot), text=True, check=True)
    subprocess.run(["sudo", "umount", "/data/tmpmnt"], check=True)

    flash_channel.info('Patching root fstab...')
    subprocess.run(["sudo", "mount", f"/dev/mmcblk0p{target_slot.value.root}", "/data/tmpmnt"], check=True)

    # Mark the root with the slot letter so you know which partition you're in by simply running `ls`
    subprocess.run(["sudo", "touch", f"/data/tmpmnt/home/pi/SLOT_{target_slot.name}"], check=True)
    subprocess.run(["sudo", "chown", "pi:pi", f"/data/tmpmnt/home/pi/SLOT_{target_slot.name}"], check=True)
    fstab = subprocess.run(['sudo', 'cat', '/data/tmpmnt/etc/fstab'], capture_output=True, text=True, check=True).stdout
    # The root image was captured from whichever slot was active on the machine that built it,
    # so its baked-in fstab still has that slot's boot/root partition numbers. Since this image
    # always lands on the slot opposite whatever's active on *this* device, remap both digits so
    # /boot/firmware and / mount from the partitions this slot actually occupies here.
    fstab = re.sub(rf'(PARTUUID=[0-9a-f]+-0){active_slot.value.boot}\b', rf'\g<1>{target_slot.value.boot}', fstab)
    fstab = re.sub(rf'(PARTUUID=[0-9a-f]+-0){active_slot.value.root}\b', rf'\g<1>{target_slot.value.root}', fstab)
    subprocess.run(['sudo', 'tee', '/data/tmpmnt/etc/fstab'], input=fstab, text=True, check=True)

    flash_channel.info('Applying persist-logs preference...')
    set_persist_logs()

    subprocess.run(["sudo", "umount", "/data/tmpmnt"], check=True)

  except Exception as e:
    flash_channel.error(f'Update failed post-flash: {e}')
    return

  if tryboot:
    flash_channel.info('Triggering tryboot...')
  flash_channel.done('Imaging successful!')
  if tryboot:
    time.sleep(2)
    subprocess.Popen(['sudo', 'reboot', '0 tryboot'])


@router.post('/update/flash')
def start_flash(tryboot: bool = False):
  """
    Validate the image(s) against manifest.json, determine the inactive slot, and flash to the inactive slot.
    The tryboot flag causes the system to reboot to the freshly flashed slot on completion, which is then healthchecked
    and set to be the new default boot slot if it's successful
  """
  # Read synchronously here (not just inside the thread's do_checks()) so the caller finds out
  # upfront whether this update includes a boot image - e.g. to show the right progress bars
  # immediately, rather than waiting for a boot-labeled message to show up mid-flash (or never,
  # if it's a root-only update).
  staged_manifest = _load_manifest("/data/update/manifest.json")
  has_boot = staged_manifest is not None and staged_manifest.boot is not None

  if not flash_channel.start(target=flash_partition_thread, args=(tryboot,)):
    return {'started': False, 'reason': 'a flash is already in progress', 'has_boot': has_boot}
  return {'started': True, 'has_boot': has_boot}


app.include_router(auth_router)
app.include_router(router)

if __name__ == '__main__':
  uvicorn.run(app, host="0.0.0.0", port=8000)

application = app  # asgi assumes application var for app
