#!/usr/bin/python3

import json
from copy import deepcopy
import deepdiff

# import HTTP server and request handler, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

import http.client


# Helper functions
def encode(pydata):
  """ Encode a dictionary as JSON """
  return json.dumps(pydata)

def decode(j):
  """ Decode JSON into dictionary """
  return json.loads(j)

def parse_int(i, options):
  """ Parse an integer into one of the given options """
  if int(i) in options:
    return int(i)
  else:
    raise ValueError('{} is not in [{}]'.format(i, options))

def error(msg):
  """ wrap the error message specified by msg into an error """
  return {'error': msg}

class EthAudioServer():
  """ A REST based JSON server for the EthAudio system """

  def __init__(self, eth_audio_instance):
    """ Start the server

      eth_audio_instance - system's instance of EthAudio runtime
    """
    print("EthAudio API Server instance created")

    # store reference to eth_audio
    self.eth_audio_instance = eth_audio_instance

    def __request_handler(*args):
      """ RequestHandler only with arguments expected for BaseHTTPRequestHandler """
      # pass reference to the instance of this class (TDS_API),
      # followed by the usual arguments expected for BaseHTTPRequestHandler
      HTTPRequestHandler(self, *args)

    # create instance of HTTPServer
    self.httpd = HTTPServer(('0.0.0.0',8080), __request_handler)

    # launch __server_run() on new thread
    # 'daemon=True' option ensures thread will be killed automatically on app close
    server_thread = threading.Thread(target=self.__server_run, daemon=True)
    server_thread.start()

  def __server_run(self):
    """ run the server (started in a background thread) """
    print("HTTP server started on %s:%s" % self.httpd.server_address)
    self.httpd.serve_forever() # will block here until app close
    print("HTTP server stopped!")

  def parse_command(self, command_json_text):
    """ parse byte array containing API command

      Args:
        command_json_text (str): json command
      Returns:
        'None' on success, otherwise a json encoded error
    """
    cmd = decode(command_json_text)
    return self.eth_audio_instance.test_cmd(cmd)

  def craft_error(self, error):
    """ create byte array containing API error response

    Args:
        error (dict): the wrapped error message.
    Returns:
      utf-8 encoded JSON error
    """
    json = encode(error)
    return json.encode('utf-8')

  def craft_response(self):
    """ create byte array containing API response """
    json = encode(self.eth_audio_instance.get_state())
    return json.encode('utf-8')


class HTTPRequestHandler(BaseHTTPRequestHandler):
  """ Used by HTTPServer in EthAudio to react to HTTP requests """

  def __init__(self, eth_audio_server, *args):

    # store reference to underlying server instance
    self.eth_audio_server = eth_audio_server

    # NOTE: BaseHTTPRequestHandler calls do_GET, do_POST, etc. from INSIDE __init__()
    # So we must set any custom attributes BEFORE CALLING super().__init__
    super().__init__(*args)

  def log_message(self, format, *args):
    """ prevent HTTP server logs from printing to console """
    return

  def do_GET(self):
    """ handle an http GET request """
    # ================ /api ===============
    if(self.path == "/api"):

      # send HTTP code 200 "OK"
      self.send_response(200)
      self.send_header("Content-type", "application/json")
      self.end_headers()
      # send standard response
      self.wfile.write(self.eth_audio_server.craft_response())

    # ======= unimplemented path ===========
    else:
      # send HTTP code 404 "Not Found"
      self.send_response(404)
      self.end_headers()

  def do_POST(self):
    """ handle an http POST request """

    # ================ /api ===============
    if(self.path == "/api"):

      # get content length and read
      content_length = int(self.headers['Content-Length'])
      content = self.rfile.read(content_length)

      # attempt to parse
      parse_error = self.eth_audio_server.parse_command(content)
      # reply with appropriate HTTP code
      if(parse_error == None):
        # send HTTP code 200 "OK"
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # send standard response
        self.wfile.write(self.eth_audio_server.craft_response())

      else:
        # send HTTP code 400 "Bad Request"
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # send error response
        self.wfile.write(self.eth_audio_server.craft_error(parse_error))

    # ======= unimplemented path ===========
    else:
      # send HTTP code 404 "Not Found"
      self.send_response(404)
      self.end_headers()

class EthAudioApi:
  """ EthAudio API

    TODO: make this either a base class, put it in another file, and make both a mock class and a real implementation
    For now this is just a mock implementation
   """

  def __init__(self):
    """ intitialize the mock system to to base configuration """
    self.status = { # This is the system state response that will come back from the ethaudio box
      "power": {
        "audio_power": False, # this needs to be on for any zone to work
        "usb_power": False     # this turns on/off the usb power port
      },
      "sources": [ # this is an array of source objects, each has an id, name, and bool specifying wheater source comes from RCA or digital input
        { "id": 0, "name": "Source 1", "digital": False  },
        { "id": 1, "name": "Source 2", "digital": False  },
        { "id": 2, "name": "Source 3", "digital": False  },
        { "id": 3, "name": "Source 4", "digital": False  }
      ],
      "zones": [ # this is an array of zones, array length depends on # of boxes connected
        { "id": 0, "name": "Zone 1", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 1, "name": "Zone 2", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 2, "name": "Zone 3", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 3, "name": "Zone 4", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 4, "name": "Zone 5", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 },
        { "id": 5, "name": "Zone 6", "source_id": 0, "mute": False , "stby": False , "disabled": False , "vol": 0 }
      ],
      "groups": [ # this is an array of groups that have been created , each group has a friendly name and an array of member zones
        { "id": 0, "name": "Group 1", "zones": [0,1,2] },
        { "id": 1, "name": "Group 2", "zones": [2,3,4] },
        { "id": 2, "name": "Group 3", "zones": [5] }
      ]
    }

  def test_cmd(self, cmd):
    """ process an individual command

      Args:
        cmd(dict): a command decoded from the JSON interface
      Returns:
        'None' if successful, otherwise an error(dict)
    """
    try:
      command = cmd['command']
      if command is None:
        return error('No command specified')
      elif command == 'return_state':
        return None # state is returned at a higher level on success
      elif command == 'set_power':
        return self.set_power(cmd['audio_power'], cmd['usb_power'])
      elif command == 'set_source':
        return self.set_source(cmd['id'], cmd['name'], cmd['digital'])
      elif command == 'set_zone':
        return self.set_zone(cmd['id'], cmd['name'], cmd['source_id'], cmd['mute'], cmd['stby'], cmd['vol'], cmd['disabled'])
      elif command == 'set_group':
        return error('set_group unimplemented')
      elif command == 'create_group':
        return error('create_group unimplemented')
      elif command == 'delete_group':
        return error('delete_group unimplemented')
      else:
        return error('command {} is not supported'.format(command))
    except Exception as e:
      return error(str(e)) # TODO: handle exception more verbosely

  def get_state(self):
    """ get the system state (dict) """
    return self.status

  def set_power(self, audio_on, usb_on):
    """ enable / disable the 9V audio power and 5V usb power """
    self.status['power']['audio_power'] = audio_on
    self.status['power']['usb_power'] = usb_on
    return None

  def set_source(self, id, name, digital):
    """ modify any of the 4 system sources

      Args:
        id (int): source id [0,4]
        name (str): user friendly source name, ie. "cd player" or "stream 1"

      Returns:
        'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['sources']):
      if s['id'] == id:
        idx = i
    if idx is not None:
      try:
        self.status['sources'][idx]['name'] = str(name)
        self.status['sources'][idx]['digital'] = bool(digital)
        return None
      except Exception as e:
        return error('set source ' + str(e))
    else:
      return error('set source: index {} out of bounds'.format(idx))

  def set_zone(self, id, name, source_id, mute, stby, vol, disabled):
    """ modify any zone

          Args:
            id (int): any valid zone [0,p*6-1] (6 zones per preamp)
            name(str): friendly name for the zone, ie "bathroom" or "kitchen 1"
            source_id (int): source to connect to [0,3]
            mute (bool): mute the zone regardless of set volume
            stby (bool): set the zone to standby, very low power consumption state
            vol (int): attenuation [-79,0] 0 is max volume, -79 is min volume
            disabled (bool): disable zone, for when the zone is not connected to any speakers and not in use
          Returns:
            'None' on success, otherwise error (dict)
    """
    idx = None
    for i, s in enumerate(self.status['zones']):
      if s['id'] == id:
        idx = i
    if idx is not None:
      try:
        self.status['zones'][idx]['name'] = str(name)
        self.status['zones'][idx]['source_id'] = parse_int(source_id, [1, 2, 3, 4])
        self.status['zones'][idx]['mute'] = bool(mute)
        self.status['zones'][idx]['stby'] = bool(stby)
        self.status['zones'][idx]['vol'] = parse_int(vol, range(-79, 1))
        self.status['zones'][idx]['disabled'] = bool(disabled)
        return None
      except Exception as e:
        return error('set zone'  + str(e))
    else:
        return error('set zone: index {} out of bounds'.format(idx))

  # TODO: make set group
  # This command can be used to set any EXISTING group
  # Along with the command one or more of the parameters can be passed
  # check the system state for a list of existing group
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  #{
  #    "command":"set_group",
  #    "id":any vaild group,
  #    "name":"new name" # sets the friendly name for the group, ie "upstairs" or "back yard"
  #    "source_id": 0 | 1 | 2 | 3 # change all zones in group to different source
  #    "zones": [0,1,2...] # specify new array of zones that make up the group
  #    "mute": False | True # mutes all zones in group
  #    "stby": False | True # sets all zone in group to standby
  #    "vol_delta": 0 to 79 # CHANGES the volume of each zone in the group by this much. For each zone, will saturate if out of range
  #}

  # TODO: make create new group
  # This command can be used to create a NEW group
  # Along with the command ALL parameters must also be passed
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  # Refer to the returned system state to obtain the id for the newly created group
  #{
  #    "command":"create_group"
  #    "name":"new group name"
  #    "zones": [0,1,2...] # specify new array of zones that make up the group
  #}

  # TODO: make delete group
  # This command can be used to delete an EXISTING group
  # Along with the command ALL parameters must also be passed
  # The system state struct will be returned if the command was successfully processed, error response otherwise
  #{
  #    "command":"delete_group"
  #    "id":"new group name"
  #}

class EthAudioClient():
  """ Simple client for sending JSON commands to an EthAudio server """

  def __init__(self, host = '0.0.0.0', port = 8080):
    self.__host = host
    self.__port = port
    self.__client = http.client.HTTPConnection(host, port)
    pass

  def send_cmd(self, cmd):
    return self.__post(encode(cmd))

  def __post(self, json):
    headers = {'Content-type': 'application/json'}
    try:
      self.__client.request('POST', '/api', json, headers)
      response = self.__client.getresponse()
      if response.getcode() == 200:
        return decode(response.read().decode())
      else:
        return None
    except Exception as ex:
      print(ex)
      # reset connection on fail, a little hacky, there is probably a simpler way
      print('resetting connection')
      try:
        self.__client = http.client.HTTPConnection(self.__host, self.__port)
      except:
        print('Failed to reset connection')
      return None

# Temporary placmemnt until we finish testing
eth_audio = EthAudioApi()
last_status = deepcopy(eth_audio.get_state())

# TODO: encode expected change after each one of these commands to form a tuple similar to (cmd, {field1: value_expected, field2:value_expected})
test_cmds = [
{
  "command" : "set_power",
  "audio_power" : True,
  "usb_power" : True
},
{
  "command" : "set_source",
  "id" : 1,
  "name" : "cd player",
  "digital": False
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "whole house",
  "source_id" : 2,
  "mute" : False,
  "stby" : False,
  "vol" : -9,
  "disabled" : False
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "whole house",
  "source_id" : 2,
  "mute" : False,
  "stby" : False,
  "vol" : -9,
  "disabled" : False
},
#{
#    "command":"set_group",
#    "id":any vaild group,
#    "name":"new name" # sets the friendly name for the group, ie "upstairs" or "back yard"
#    "source_id": 0 | 1 | 2 | 3 # change all zones in group to different source
#    "zones": [0,1,2...] # specify new array of zones that make up the group
#    "mute": False | True # mutes all zones in group
#    "stby": False | True # sets all zone in group to standby
#    "vol_delta": 0 to 79 # CHANGES the volume of each zone in the group by this much. For each zone, will saturate if out of range
#},
#{
#    "command":"create_group"
#    "name":"new group name"
#    "zones": [0,1,2...] # specify new array of zones that make up the group
#},
#{
#    "command":"delete_group"
#    "id":"new group name"
#}

# Rewind state back to initialization
{
  "command" : "set_power",
  "audio_power" : False,
  "usb_power" : True
},
{
  "command" : "set_source",
  "id" : 1,
  "name" : "Pandora",
  "digital": True
},
{
  "command" : "set_zone",
  "id" : 2,
  "name" : "Sleep Zone",
  "source_id" : 3,
  "mute" : False,
  "stby" : False,
  "vol" : -40,
  "disabled" : False
},
]

def pretty_field(field):
  """ pretty print deepdiff's field name """
  return str(field).replace("root['", "").replace("']","").replace("['", ".")

def show_change():
  """ print the difference between status when this was last called

    we use this for debugging
  """
  global last_status
  diff = deepdiff.DeepDiff(last_status, eth_audio.status, ignore_order=True)
  if any(k in diff for k in ('values_changed', 'dictionary_item_added', 'dictionary_item_removed')):
    print('changes:')
    if 'values_changed' in diff:
      for field, change in diff['values_changed'].items():
        print('  {} {} -> {}'.format(pretty_field(field), change['old_value'], change['new_value']))
    if 'dictionary_item_added' in diff:
      for field in diff['dictionary_item_added']:
        print('added {}'.format(pretty_field(field)))
    if 'dictionary_item_removed' in diff:
      for field in diff['dictionary_item_removed']:
        print('added {}'.format(pretty_field(field)))
  else:
    print('no change!')
  last_status = deepcopy(eth_audio.status)

if __name__ == "__main__":

    # Test emulated commands
    # TODO: add verification to these tests
    print('intial state:')
    print(eth_audio.get_state())
    print('testing commands:')
    show_change()
    eth_audio.set_power(audio_on=False, usb_on=True)
    show_change()
    eth_audio.set_source(0, 'Spotify', True)
    show_change()
    eth_audio.set_source(1, 'Pandora', True)
    show_change()
    eth_audio.set_source(2, 'TV', False)
    show_change()
    eth_audio.set_source(3, 'PC', False)
    show_change()
    eth_audio.set_zone(0, 'Party Zone', 1, False, False, 0, False)
    show_change()
    eth_audio.set_zone(1, 'Drone Zone', 2, False, False, -20, False)
    show_change()
    eth_audio.set_zone(2, 'Sleep Zone', 3, True, False, -40, False)
    show_change()
    eth_audio.set_zone(3, "Standby Zone", 4, False, True, -50, False)
    show_change()
    eth_audio.set_zone(4, "Disabled Zone", 1, False, False, 0, True)
    show_change()

    # Test string/json based command handler
    for cmd in test_cmds:
      eth_audio.test_cmd(cmd)
      show_change()

    # Start HTTP server (behind the scenes it runs in new thread)
    srv = EthAudioServer(eth_audio)

    # Send HTTP requests and print output
    client = EthAudioClient()
    for cmd in test_cmds:
      client.send_cmd(cmd)
      show_change()
