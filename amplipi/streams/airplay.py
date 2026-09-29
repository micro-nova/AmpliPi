from typing import ClassVar, List, Optional
from amplipi import models, utils
from .base_streams import PersistentStream, InvalidStreamField, logger
from amplipi.mpris import MPRIS
from zeroconf import IPVersion, Zeroconf, ServiceBrowser, ServiceListener
import ipaddress
import json
import subprocess
import shutil
import sys
import threading
import time
import os
import io

_DACP_SERVICE_TYPES = ['_dacp._tcp.local.', '_touch-able._tcp.local.']


def write_sp_config_file(filename, config):
  """ Write a shairport config file (@filename) with a hierarchy of grouped key=value pairs given by @config """
  with open(filename, 'wt', encoding='utf-8') as cfg_file:
    for group, gconfig in config.items():
      cfg_file.write(f'{group} =\n{{\n')
      for key, value in gconfig.items():
        if isinstance(value, str):
          cfg_file.write(f'  {key} = "{value}"\n')
        else:
          cfg_file.write(f'  {key} = {value}\n')
      cfg_file.write('};\n')


def _normalize_ip(ip: str) -> str:
  """ Collapses an IPv4-mapped IPv6 address (::ffff:a.b.c.d) to its plain IPv4 form, since a
  dual-stack listener can report an IPv4 peer either way """
  try:
    addr = ipaddress.ip_address(ip)
  except ValueError:
    return ip
  return str(addr.ipv4_mapped) if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped else str(addr)


def _rtsp_peer_ip(port: int) -> Optional[str]:
  """ IP of the client with an established RTSP connection to @port, if any """
  try:
    result = subprocess.run(['ss', '-H', '-tn', 'state', 'established', f'( sport = :{port} )'],
                            stdout=subprocess.PIPE, text=True, check=False, timeout=2)
  except Exception:
    return None
  for line in result.stdout.splitlines():
    fields = line.split()
    # ss drops the State column entirely when filtered with "state established" - fields are
    # RecvQ, SendQ, Local, Peer, so Peer is index 3, not the 4 you'd expect with State present.
    if len(fields) >= 4:
      peer = fields[3]
      # IPv6 peers are bracketed ("[addr%scope]:port") since the address itself contains colons
      ip = peer[1:peer.index(']')].split('%', 1)[0] if peer.startswith('[') else peer.rsplit(':', 1)[0]
      return _normalize_ip(ip)
  return None


def _dacp_reachable(client_ip: str, timeout: float = 2.0) -> bool:
  """ Whether @client_ip advertises a DACP remote-control service reachable over mDNS """
  found = threading.Event()

  class _Listener(ServiceListener):
    def add_service(self, zc, type_, name):
      info = zc.get_service_info(type_, name)
      if info and client_ip in info.parsed_addresses(IPVersion.All):
        found.set()

    def update_service(self, zc, type_, name):
      pass

    def remove_service(self, zc, type_, name):
      pass

  zc = Zeroconf(ip_version=IPVersion.All)
  try:
    ServiceBrowser(zc, _DACP_SERVICE_TYPES, _Listener())
    found.wait(timeout)
  finally:
    zc.close()
  return found.is_set()


class AirPlay(PersistentStream):
  """ An AirPlay Stream """

  stream_type: ClassVar[str] = 'airplay'

  def __init__(self, name: str, ap2: bool, disabled: bool = False, mock: bool = False, validate: bool = True):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock, validate=validate)
    self.mpris: Optional[MPRIS] = None
    self.ap2 = ap2
    self.ap2_exists = False
    # Populated once _detect_remote_control_support confirms the client's capabilities
    # starts empty due to newer iOS versions locking third-party control access for airplay2
    self.supported_cmds: List[str] = []
    self._remote_control_check_started = False
    self.STATE_TIMEOUT = 300  # seconds
    self._connect_time = 0.0
    self._coverart_dir = ''
    self._log_file: Optional[io.TextIOBase] = None
    self.src_config_folder: Optional[str] = None
    self.volume_watcher_process: Optional[threading.Thread] = None
    """Populates the fifo that the vol sync process depends on"""
    self.volume_sync_process: Optional[subprocess.Popen] = None
    self._volume_fifo: Optional[int] = None

  def watch_vol(self):
    """Creates and supplies a FIFO with volume data for volume sync"""
    while True:
      try:
        if self.src is not None:
          if self._volume_fifo is None and self.src_config_folder is not None:
            fifo_path = f"{self.src_config_folder}/vol"
            # os.path.isfile() is always False for a FIFO (it only recognizes regular files),
            # so it never actually detects one left over from a prior connection - use exists()
            if not os.path.exists(fifo_path):
              os.mkfifo(fifo_path)
            self._volume_fifo = os.open(fifo_path, os.O_WRONLY, os.O_NONBLOCK)
          data = json.dumps({
            'zones': self.connected_zones,
            'volume': self.volume,
          })
          os.write(self._volume_fifo, bytearray(f"{data}\r\n", encoding="utf8"))
      except Exception as e:
        logger.error(f"{self.name} volume thread ran into exception: {e}")
      time.sleep(0.1)

  def reconfig(self, **kwargs):
    self.validate_stream(**kwargs)
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    if 'name' in kwargs and kwargs['name'] != self.name:
      self.name = kwargs['name']
      reconnect_needed = True
    if 'ap2' in kwargs and kwargs['ap2'] != self.ap2:
      self.ap2 = kwargs['ap2']
      reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect an AirPlay device to a given audio source
    This creates an AirPlay streaming option based on the configuration
    """

    # if stream is airplay2 check for other airplay2s and error if found
    if self.ap2:
      # anchored to the exact binary path, a bare pattern can match unrelated processes
      ap2_path = f"{utils.get_folder('streams')}/shairport-sync-ap2"
      result = subprocess.run(['pgrep', '-f', f'^{ap2_path} '], stdout=subprocess.PIPE, text=True, check=False)
      if result.stdout.strip():
        self.ap2_exists = True
        # TODO: we need a better way of showing errors to user
        logger.info(f'Another Airplay 2 stream is already in use, unable to start {self.name}, mocking connection')
        return

    self.src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    try:
      os.remove(f'{self.src_config_folder}/currentSong')
    except FileNotFoundError:
      pass
    self._connect_time = time.time()
    self._coverart_dir = f'{utils.get_folder("web")}/generated/v{vsrc}'

    logger.info("setting up config")

    config = {
      'general': {
        'name': self.name,
        'port': 5100 + 100 * vsrc,  # Listen for service requests on this port
        'udp_port_base': 6101 + 100 * vsrc,  # start allocating UDP ports from this port number when needed
        'drift': 2000,  # allow this number of frames of drift away from exact synchronisation before attempting to correct it
        'resync_threshold': 0,  # a synchronisation error greater than this will cause resynchronisation; 0 disables it
        'log_verbosity': 0,  # "0" means no debug verbosity, "3" is most verbose.
        'mpris_service_bus': 'Session',
      },
      'metadata': {
        'enabled': 'yes',
        'include_cover_art': 'yes',
        'cover_art_cache_directory': self._coverart_dir,
      },
      'alsa': {
        'output_device': utils.virtual_output_device(vsrc),  # alsa output device
        # If set too small, buffer underflow occurs on low-powered machines. Too long and the response times with software mixer become annoying.
        'audio_backend_buffer_desired_length': 11025
      },
    }

    # make all of the necessary dir(s) & files
    try:
      shutil.rmtree(self._coverart_dir)
    except FileNotFoundError:
      pass
    os.makedirs(self._coverart_dir, exist_ok=True)
    os.makedirs(self.src_config_folder, exist_ok=True)
    config_file = f'{self.src_config_folder}/shairport.conf'
    write_sp_config_file(config_file, config)
    self._log_file = open(f'{self.src_config_folder}/log', mode='w')
    shairport_args = f"{utils.get_folder('streams')}/shairport-sync{'-ap2' if self.ap2 else ''} -c {config_file}".split(' ')
    logger.info(f'shairport_args: {shairport_args}')

    self.proc = subprocess.Popen(args=shairport_args, stdin=subprocess.PIPE,
                                 stdout=self._log_file, stderr=self._log_file)
    # Reset - a new client may not support remote control even if the last one did. Checked
    # lazily from info() once real playback shows up, since there's no telling in advance how
    # long the client will take to actually connect.
    self.supported_cmds = []
    self._remote_control_check_started = False

    try:
      mpris_name = 'ShairportSync'
      # If there are multiple shairport-sync processes, add the pid to the mpris name
      # shairport sync only adds the pid to the mpris name if it cannot use the default name
      if len(os.popen("pgrep shairport-sync").read().strip().splitlines()) > 1:
        mpris_name += f".i{self.proc.pid}"
      self.mpris = MPRIS(mpris_name, f'{self.src_config_folder}/metadata.txt')

      vol_sync = f"{utils.get_folder('streams')}/shairport_volume_handler.py"
      vol_args = [sys.executable, vol_sync, mpris_name, self.src_config_folder]
      logger.info(f'{self.name}: starting vol synchronizer: {vol_args}')
      self.volume_watcher_process = threading.Thread(target=self.watch_vol, daemon=True)
      self.volume_watcher_process.start()
      self.volume_sync_process = subprocess.Popen(args=vol_args, stdout=self._log_file, stderr=self._log_file)
    except Exception as exc:
      logger.exception(f'Error starting airplay MPRIS reader: {exc}')

  def _detect_remote_control_support(self, rtsp_port: int, proc: subprocess.Popen):
    """ Updates supported_cmds once the client's DACP reachability is known.
    @proc guards against a stale result landing after a fast reconnect. """
    client_ip = None
    for _ in range(10):
      client_ip = _rtsp_peer_ip(rtsp_port)
      if client_ip or proc.poll() is not None:
        break
      time.sleep(0.5)

    supported = client_ip is not None and _dacp_reachable(client_ip)
    if self.proc is proc:
      self.supported_cmds = ['play', 'pause', 'next', 'prev'] if supported else []
      logger.info(f"AirPlay remote control {'available' if supported else 'unavailable'} "
                  f"for {self.name} (client {client_ip})")

  def _deactivate(self):
    if 'mpris' in self.__dir__() and self.mpris:
      # When airplay disconnects, a phone will just output audio from it's own speakers at whatever volume it was set to for the airplay session
      # This can be annoying if you prefer to use the amplipi-side volume slider and so keep your phone volume maxxed out
      try:
        self.mpris.set_volume(0.0)
        time.sleep(0.3)
      except Exception as e:
        logger.info(f'Could not zero AirPlay client volume before disconnect: {e}')
      self.mpris.close()
    self.mpris = None
    if self._is_running():
      self.proc.stdin.close()
      logger.info('stopping shairport-sync')
      self.proc.terminate()
      if self.volume_sync_process is not None:
        self.volume_sync_process.terminate()
      if self.proc.wait(1) != 0:
        logger.info('killing shairport-sync')
        self.proc.kill()
      self.proc.communicate()
      if self.volume_sync_process is not None:
        if self.volume_sync_process.wait(1) != 0:
          logger.info('killing shairport vol sync')
          self.volume_sync_process.kill()
        self.volume_sync_process.communicate()
    if self._volume_fifo is not None:
      try:
        os.close(self._volume_fifo)
      except OSError:
        pass
    if '_log_file' in self.__dir__() and self._log_file:
      self._log_file.close()
    if self.src:
      try:
        subprocess.run(f'rm -r {utils.get_folder("config")}/srcs/{self.src}/*', shell=True, check=True)
      except Exception as e:
        logger.exception(f'Error removing airplay config files: {e}')
    self._disconnect()
    self.proc = None
    self.volume_sync_process = None
    self.volume_watcher_process = None
    self._volume_fifo = None

  def info(self) -> models.SourceInfo:
    source = models.SourceInfo(
      name=f"Connect to {self.name} on Airplay{'2' if self.ap2 else ''}",
      state=self.state,
      img_url='static/imgs/shairport.png',
      type=self.stream_type
    )

    # if stream is airplay2 and other airplay2s exist show error message
    if self.ap2:
      if self.ap2_exists:
        source.name = 'An Airplay2 stream already exists!\n Please disconnect it and try again.'
        return source

    if not self.mpris:
      logger.info(f'Airplay: No MPRIS object for {self.name}!')
      return source

    try:
      md = self.mpris.metadata()

      if self.mpris.is_playing():
        source.state = 'playing'
      else:
        # if we've been paused for a while and the state has changed since connecting, then say
        # we're stopped since shairport-sync doesn't really differentiate between paused and stopped
        if self._connect_time < md.state_changed_time and time.time() - md.state_changed_time < self.STATE_TIMEOUT:
          source.state = 'paused'
        else:
          source.state = 'stopped'

      if source.state != 'stopped':
        vsrc = self.vsrc
        if not self._remote_control_check_started and vsrc is not None:
          self._remote_control_check_started = True
          threading.Thread(target=self._detect_remote_control_support,
                           args=(5100 + 100 * vsrc, self.proc), daemon=True).start()

        source.artist = md.artist
        source.track = md.title
        source.album = md.album
        source.supported_cmds = list(self.supported_cmds)

        if md.title != '':
          # if there is a title, attempt to get coverart
          images = os.listdir(self._coverart_dir)
          if len(images) > 0:
            source.img_url = f'generated/v{self.vsrc}/{images[0]}'
        else:
          source.track = "No metadata available"

    except Exception as e:
      logger.exception(f"error in airplay: {e}")

    return source

  def send_cmd(self, cmd):
    try:
      if cmd in self.supported_cmds:
        if cmd == 'play':
          self.mpris.play_pause()
        elif cmd == 'pause':
          self.mpris.play_pause()
        elif cmd == 'next':
          self.mpris.next()
        elif cmd == 'prev':
          self.mpris.previous()
      else:
        raise NotImplementedError(f'"{cmd}" is either incorrect or not currently supported')
    except Exception as e:
      logger.exception(f"error in shairport: {e}")

  def validate_stream(self, **kwargs):
    if 'name' in kwargs and len(kwargs['name']) > 50:
      raise InvalidStreamField("name", "name cannot exceed 50 characters")
