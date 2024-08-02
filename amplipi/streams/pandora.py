from .base_streams import PersistentStream, Browsable, InvalidStreamField, write_config_file, logger
from amplipi import models, utils
from typing import ClassVar, List
from pandora.clientbuilder import SettingsDictBuilder
import subprocess
import os
import time
import re

# TODO: A significant amount of complexity could be removed if we switched some features here to using pydora instead of
# interfacing with pianobar's TUI


class Pandora(PersistentStream, Browsable):
  """ A Pandora Stream """

  stream_type: ClassVar[str] = 'pandora'

  def __init__(self, name: str, user, password: str, station: str, disabled: bool = False, mock: bool = False):
    super().__init__(self.stream_type, name, disabled=disabled, mock=mock)
    self.user = user
    self.password = password
    self.station = station
    self.track = ""
    self.invert_liked_state = False
    self.pianobar_path = f'{utils.get_folder("streams")}/pianobar'

    self.stations: List[models.BrowsableItem] = []

    # pandora api client, the values in here come from the pandora android app
    self.pyd_client = SettingsDictBuilder({
      "DECRYPTION_KEY": "R=U!LH$O2B#",
      "ENCRYPTION_KEY": "6#26FRL$ZWD",
      "PARTNER_USER": "android",
      "PARTNER_PASSWORD": "AC7IBG09A3DTSYM4R41UJWL07VLN8JI7",
      "DEVICE": "android-generic",
    }).build()

    self.validate_stream(user=self.user, password=self.password)

    self.ctrl = ''  # control fifo location
    self.supported_cmds = {
      'play': {'cmd': 'P\n', 'state': 'playing'},
      'pause': {'cmd': 'S\n', 'state': 'paused'},
      'next': {'cmd': 'n\n', 'state': 'playing'},
      'love': {'cmd': '+\n', 'state': None},  # love does not change state
      'ban': {'cmd': '-\n', 'state': 'playing'},
      'shelve': {'cmd': 't\n', 'state': 'playing'},
    }

  def reconfig(self, **kwargs):
    self.validate_stream(**kwargs)
    reconnect_needed = False
    if 'disabled' in kwargs:
      self.disabled = kwargs['disabled']
    pb_fields = ['user', 'password', 'station']
    fields = list(pb_fields) + ['name']
    for k, v in kwargs.items():
      if k in fields and self.__dict__[k] != v:
        self.__dict__[k] = v
        if k in pb_fields:
          reconnect_needed = True
    if reconnect_needed and self.is_activated():
      self.reactivate()

  def _activate(self, vsrc: int):
    """ Connect pandora output to a given audio source
    This will start up pianobar with a configuration specific to @src
    """
    try:
      self.pyd_client.login(self.user, self.password)
    except Exception as e:
      logger.exception(f'Failed to login to Pandora: {e}')
      pass

    # make a special home/config to launch pianobar in (this allows us to have multiple pianobars)
    src_config_folder = f'{utils.get_folder("config")}/srcs/v{vsrc}'
    eventcmd_template = f'{utils.get_folder("streams")}/eventcmd.sh'
    pb_home = src_config_folder
    pb_config_folder = f'{pb_home}/.config/pianobar'
    pb_control_fifo = f'{pb_config_folder}/ctl'
    pb_status_fifo = f'{pb_config_folder}/stat'
    pb_config_file = f'{pb_config_folder}/config'
    self.pb_output_file = f'{pb_config_folder}/output'
    pb_error_file = f'{pb_config_folder}/error'
    pb_eventcmd_file = f'{pb_config_folder}/eventcmd.sh'
    pb_src_config_file = f'{pb_home}/.libao'
    self.pb_stations_file = f'{pb_config_folder}/stationList'
    # make all of the necessary dir(s)
    os.system(f'mkdir -p {pb_config_folder}')
    os.system(f'cp {eventcmd_template} {pb_eventcmd_file}')  # Copy to retain executable status
    # write pianobar and libao config files
    pb_conf = {
      'user': self.user,
      'password': self.password,
      'fifo': pb_control_fifo,
      'event_command': pb_eventcmd_file
    }

    if self.station:
      pb_conf['autostart_station'] = self.station

    write_config_file(pb_config_file, pb_conf)
    write_config_file(pb_src_config_file, {'default_driver': 'alsa', 'dev': utils.virtual_output_device(vsrc)})
    # create fifos if needed
    if not os.path.exists(pb_control_fifo):
      os.system(f'mkfifo {pb_control_fifo}')
    if not os.path.exists(pb_status_fifo):
      os.system(f'mkfifo {pb_status_fifo}')
    # start pandora process in special home
    logger.info(f'Pianobar config at {pb_config_folder}')
    try:
      self.proc = subprocess.Popen(
        args=self.pianobar_path, stdin=subprocess.PIPE, stdout=open(self.pb_output_file, 'w', encoding='utf-8'),
        stderr=open(pb_error_file, 'w', encoding='utf-8'), env={'HOME': pb_home})
      time.sleep(0.1)  # Delay a bit before creating a control pipe to pianobar
      self.ctrl = pb_control_fifo

      if not self.station:  # if no station is specified, we need to start playing in order to get the station list
        with open(self.ctrl, 'w', encoding='utf-8') as f:
          f.write('0\n')
          f.flush()

      self.state = 'playing'  # TODO: we need to pause pandora if it isn't playing anywhere

    except Exception as exc:
      logger.exception(f'error starting pianobar: {exc}')

  def _deactivate(self):
    if self._is_running():
      try:
        self.proc.terminate()
        self.proc.wait(timeout=4)
      except:
        # Likely a subprocess.TimeoutException, but we will handle all exceptions the same.
        self.proc.kill()
        self.proc.wait()

    self.proc = None
    self.ctrl = ''

  def info(self) -> models.SourceInfo:
    src_config_folder = f'{utils.get_folder("config")}/srcs/v{self.vsrc}'
    loc = f'{src_config_folder}/.config/pianobar/currentSong'
    source = models.SourceInfo(
      name=self.full_name(),
      state=self.state,
      supported_cmds=list(self.supported_cmds.keys()),
      img_url='static/imgs/pandora.png',
      type=self.stream_type
    )
    try:
      with open(loc, 'r', encoding='utf-8') as file:
        for line in file.readlines():
          line = line.strip()
          if line:
            data = line.split(',,,')
            if self.track != data[1]:  # When song changes, stop inverting state
              self.invert_liked_state = False
            source.state = self.state
            source.artist = data[0]
            source.track = data[1]
            self.track = data[1]
            source.album = data[2]
            source.img_url = data[3].replace('http:', 'https:')  # HACK: kind of a hack to just replace with https
            initial_rating = models.PandoraRating(int(data[4]))

            source.rating = initial_rating

            # Pianobar doesn't update metadata after a song starts playing
            # so when you like a song you have to change the state manually until next song
            if self.invert_liked_state:
              if int(data[4]) == models.PandoraRating.DEFAULT.value:
                source.rating = models.PandoraRating.LIKED
              elif int(data[4]) == models.PandoraRating.LIKED.value:
                source.rating = models.PandoraRating.DEFAULT

            source.station = data[5]
        return source
    except Exception:
      pass
      # logger.error('Failed to get currentSong - it may not exist: {}'.format(e))
    # TODO: report the status of pianobar with station name, playing/paused, song info
    # ie. Playing: "Cameras by Matt and Kim" on "Matt and Kim Radio"
    return source

  def send_cmd(self, cmd):
    """ Pianobar's commands
      cmd: Command string sent to pianobar's control fifo
      state: Expected state after successful command execution
    """
    try:
      if cmd in self.supported_cmds:
        if cmd == "love":
          self.info()  # Ensure liked state is synced with current song
          self.invert_liked_state = not self.invert_liked_state

        with open(self.ctrl, 'w', encoding='utf-8') as file:
          file.write(self.supported_cmds[cmd]['cmd'])
          file.flush()
        expected_state = self.supported_cmds[cmd]['state']

        if expected_state is not None:
          self.state = expected_state
      elif 'station' in cmd:
        station_id = int(cmd.replace('station=', ''))
        if station_id is not None:
          with open(self.pb_output_file, 'w', encoding='utf-8') as file:  # clear output file to detect new station
            file.write('')
          with open(self.ctrl, 'w', encoding='utf-8') as file:
            file.write('s')
            file.flush()
            file.write(f'{station_id}\n')
            file.flush()
          for _ in range(50):  # try over a max of 5 seconds to get the new station
            time.sleep(0.1)
            # open output file and find ID from end of file
            matches = []
            with open(self.pb_output_file, 'r', encoding='utf-8') as file:
              text = file.read()
              matches = re.findall(r'\" \([0-9]+\)', text)
            if matches:
              self.station = matches[-1].replace('\" (', '').replace(')', '')
              self.pb_output_file
              with open(self.pb_output_file, 'w', encoding='utf-8') as file:  # clear file
                file.write('')
              self.state = 'playing'
              logger.info(f'Changed pandora station to {self.station}')
              time.sleep(1)  # give pianobar awhile to update metadata before we end the api call
              break
            elif "Receiving new playlist... Ok." in text:  # if we see this message, we know the station has been changed but we may have simply switched to the same station
              logger.info(f'Changed pandora station to same station ({self.station})')
              break
          else:  # if we don't find the station in 5 seconds, raise an error
            logger.error("Failed to change pandora station!")
            raise RuntimeError('Failed to change pandora station')
        else:
          raise ValueError(f'station=<int> expected, ie. station=23432423; received "{cmd}"')
      else:
        raise NotImplementedError(f'Command not recognized: {cmd}')
    except Exception as exc:
      raise RuntimeError(f'Command {cmd} failed to send: {exc}') from exc

  def browse(self, parent=None) -> List[models.BrowsableItem]:
    """ Browse the stream for items """

    if len(self.stations) == 0:
      try:
        pd_stations = {s.name.upper(): s.art_url for s in self.pyd_client.get_station_list()}
      except Exception as e:
        logger.exception(f'Error browsing for pandora stations: {e}')
        return []
      with open(self.pb_stations_file) as f:
        # try to match PianoBar's list of stations with those returned by the Pandora API
        # NOTE: duplicate station names will only match the last duplicate station returned by the Pandora API
        for line in f.readlines():
          sinfo = line.rstrip("\n").split(":")
          if len(sinfo) >= 2:
            station_id = sinfo[0]
            name = sinfo[1]
            img = pd_stations.get(name.upper(), "")
            self.stations.append(models.BrowsableItem(name=name, playable=True, id=station_id, parent=False, img=img))
    return self.stations

  def play(self, item_id):
    """ Play a specific item """
    self.send_cmd(f'station={item_id}')

  def validate_stream(self, **kwargs):
    USER_LIKE = r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,})$'
    if 'user' in kwargs and not re.fullmatch(USER_LIKE, kwargs['user']):
      raise InvalidStreamField("user", "invalid username")

    if 'password' in kwargs and len(kwargs['password']) == 0:
      raise InvalidStreamField("password", "password cannot be empty")

    # don't run if testing so we don't cause problems with CI
    if not self.mock:
      try:
        self.pyd_client.login(self.user, self.password)
      except Exception as e:
        raise InvalidStreamField("password", "invalid password or unable to connect to Pandora servers") from e
