import subprocess
import sys
import time
from typing import Optional, List
import logging
from amplipi import models
from amplipi import utils

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)


def write_config_file(filename, config):
  """ Write a simple config file (@filename) with key=value pairs given by @config """
  with open(filename, 'wt', encoding='utf-8') as cfg_file:
    for key, value in config.items():
      cfg_file.write(f'{key}={value}\n')


def uuid_gen():
  """ Generates a UUID for use in DLNA and Plexamp streams """
  uuid_proc = subprocess.run(args='uuidgen', capture_output=True, check=False)
  uuid_str = str(uuid_proc).split(',')
  c_check = uuid_str[0]
  val = uuid_str[2]

  if c_check[0:16] == 'CompletedProcess':  # Did uuidgen succeed?
    return val[10:46]
  # Generic UUID in case of failure
  return '39ae35cc-b4c1-444d-b13a-294898d771fa'


class InvalidStreamField(Exception):
  def __init__(self, field, message):
    self.msg = f"invalid stream field '{field}': {message}"
    self.field = field

  def __str__(self):
    return repr(self.msg)


class Browsable:
  """ A stream that can be browsed for items """
  # technically does nothing but is a marker for streams that can be browsed


class BaseStream:
  """ BaseStream class containing methods that all other streams inherit """

  def __init__(self, stype: str, name: str, stream_id: int, only_src=None, disabled: bool = False, mock: bool = False, validate: bool = True, **kwargs):

    self.id = stream_id
    self.name = name
    self.disabled = disabled
    self.proc: Optional[subprocess.Popen] = None
    self.mock = mock
    self.src: Optional[int] = None
    self.only_src: Optional[int] = only_src
    self.state = 'disconnected'
    self.stype = stype
    self.browsable = isinstance(self, Browsable)
    if validate:
      self.validate_stream(name=name, mock=mock, **kwargs)

  def __del__(self):
    self.disconnect()

  def __str__(self):
    connection = f' connected to src={self.src}' if self.src else ''
    mock = ' (mock)' if self.mock else ''
    return f'{self.full_name()}{connection}{mock}'

  def full_name(self):
    """ Combine name and type of a stream to make a stream easy to identify.

    Many streams will simply be named something like AmpliPi or John, so embedding the '- stype'
    into the name makes the name easier to identify.
    """
    return f'{self.name} - {self.stype}'

  def _disconnect(self):
    logger.info(f'{self.name} disconnected')
    self.state = 'disconnected'
    self.src = None

  def disconnect(self):
    """ Disconnect the stream from an output source """
    if self._is_running() and self.proc is not None:
      try:
        self.proc.kill()
      except Exception:
        pass
    self._disconnect()

  def _connect(self, src):
    logger.info(f'{self.name} connected to {src}')
    self.state = 'connected'
    self.src = src

  def restart(self):
    """Reset this stream by disconnecting and reconnecting"""
    try:
      self.send_cmd('stop')
    except:
      logger.info(f'Stream {self.name} does not have a stop response')
    last_src = self.src  # Disconnect sets self.src to none, so temp variable used to keep track
    self.disconnect()
    time.sleep(0.1)
    self.connect(last_src)

  def is_connected(self) -> bool:
    return self.src is not None

  def connect(self, src: int):
    """ Connect the stream to an output source """
    self._connect(src)

  def reconfig(self, **kwargs):
    """ Reconfigure a potentially running stream """

  def is_activated(self):
    """ Check if this stream has been activated """
    # activate/deactivate is not supported by the base stream type
    return False

  def _is_running(self):
    if self.proc:
      return self.proc.poll() is None
    return False

  def info(self) -> models.SourceInfo:
    """ Get stream info and song metadata """
    return models.SourceInfo(
      name=self.full_name(),
      state=self.state)

  def requires_src(self) -> Optional[int]:
    """ Check if this stream needs to be connected to a specific source

    returns that source's id or None for any source
    """
    return self.only_src

  def send_cmd(self, cmd: str) -> None:
    """ Generic send_cmd function. If not implemented in a stream,
    and a command is sent, this error will be raised.
    """
    raise NotImplementedError(f'{self.name} does not support commands')

  def play(self, item: str):
    """ Play a BrowsableItem """
    raise NotImplementedError()

  def browse(self, parent: Optional[int] = None, path: Optional[str] = None) -> List[models.BrowsableItem]:
    """ Browse the stream for items"""
    raise NotImplementedError()

  def validate_stream(self, **kwargs):
    """ Validate fields. If we have not implemented a validator, simply pass validation. """
    return True


class VirtualSources:
  """ Virtual source allocator to mind ALSA limits"""

  def __init__(self, num_sources: int):
    self._sources: List[Optional[int]] = [None] * num_sources

  def available(self) -> bool:
    """ Are any sources available """
    return None in self._sources

  def alloc(self) -> int:
    """ Allocate an available virtual source if any"""
    if self.available():
      for i, s in enumerate(self._sources):
        if s is None:
          self._sources[i] = i
          return i
    raise Exception('no sources available')

  def free(self, vsrc: int):
    """ make a virtual source available """
    if self._sources[vsrc] is None:
      raise Exception(f'unable to free virtual source {vsrc} it was not allocated')
    self._sources[vsrc] = None


vsources = VirtualSources(12)


class PersistentStream(BaseStream):
  """ Base class for streams that are able to persist without a direct connection to an output """

  def __init__(self, stype: str, name: str, stream_id: int, disabled: bool = False, mock: bool = False, validate: bool = True, **kwargs):
    super().__init__(stype, name, stream_id, None, disabled, mock, validate, **kwargs)
    self.vsrc: Optional[int] = None
    self._cproc: Optional[subprocess.Popen] = None
    self.device: Optional[str] = None

  def __del__(self):
    self.deactivate()
    self.disconnect()

  def is_persistent(self):
    """ Does this stream run in the background? """
    # TODO: this should be a runtime configurable field and used to determine streams to start up in the background
    return False

  def activate(self):
    """ Start the stream behind the scenes without connecting to a physical source.
    Stream will @persist after disconnected if is_persistent() returns True
    """
    try:
      vsrc = vsources.alloc()
      self.vsrc = vsrc
      self.state = "connected"  # optimistically make this look like a normal stream for now
      if not self.mock:
        self._activate(vsrc)  # might override self.state
      logger.info(f"Activating {self.name} ({'persistant' if self.is_persistent() else 'temporarily'})")
    except Exception as e:
      logger.exception(f'Failed to activate {self.name}: {e}')
      if vsrc is not None:
        vsources.free(vsrc)
      self.vsrc = None
      self.state = 'disconnected'
      raise e

  def _activate(self, vsrc: int):
    raise NotImplementedError(f'{self.stype} does not support activation')

  def is_activated(self) -> bool:
    """ Is this stream activated? """
    return self.vsrc is not None

  def deactivate(self):
    """ Stop the stream behind the scenes """
    try:
      logger.info(f'deactivating {self.name}')
      self._deactivate()
    except Exception as e:
      raise Exception(f'Failed to deactivate {self.name}: {e}') from e
    finally:
      self.state = "disconnected"  # make this look like a normal stream for now
      if 'vsrc' in self.__dir__() and self.vsrc:
        vsrc = self.vsrc
        self.vsrc = None
        vsources.free(vsrc)

  def _deactivate(self):
    raise NotImplementedError(f'{self.stype} does not support deactivation')

  def reactivate(self):
    """ Stop and restart the stream behind the scenes.
    This should be called after significant paranmeter changes.
    """
    logger.info(f'reactivating {self.name}')
    if self.is_activated():
      self.deactivate()
      time.sleep(0.1)  # wait a bit just in case

  def restart(self):
    """Reset this stream by disconnecting and reconnecting"""
    self.deactivate()
    time.sleep(0.1)
    self.activate()

  def connect(self, src: int):
    """ Connect an output to a given audio source """
    if self.is_connected():
      raise Exception(f"Stream already connected to a source {self.src}, disconnect before trying to connect")
    if self.vsrc is None:
      # activate on the fly
      self.activate()
      if self.vsrc is None:
        raise Exception('No virtual source found/available')
    virt_dev = utils.virtual_connection_device(self.vsrc)
    phy_dev = utils.real_output_device(src)
    self.device = phy_dev
    if virt_dev is None or self.mock:
      logger.info('  pretending to connect to loopback (unavailable)')
    else:
      # args = f'alsaloop -C {virt_dev} -P {phy_dev} -t 100000'.split()
      args = f'{sys.executable} {utils.get_folder("streams")}/process_monitor.py alsaloop -C {virt_dev} -P {phy_dev} -t 100000'.split()
      try:
        logger.info(f'  starting connection via: {" ".join(args)}')
        self._cproc = subprocess.Popen(args=args)
      except Exception as exc:
        logger.exception(f'Failed to start alsaloop connection: {exc}')
        time.sleep(0.1)  # Delay a bit
    self.src = src

  def disconnect(self):
    """ Disconnect from a DAC """
    if '_cproc' in self.__dir__() and self._cproc:
      logger.info(f'  stopping connection {self.vsrc} -> {self.src}')
      try:
        # must use terminate as kill() cannot be intercepted
        self._cproc.terminate()
        self._cproc.communicate(timeout=5)

      except Exception as e:
        logger.exception(f'PersistentStream disconnect error: {e}')
        pass
    self.src = None
