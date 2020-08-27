#!/usr/bin/python3

import json
from copy import deepcopy
import deepdiff

# import HTTP server and request handler, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


# Helper functions
def encode(pydata):
    return json.dumps(pydata)

def decode(j):
    return json.loads(j)

def parse_int(i, options):
    if int(i) in options:
        return int(i)
    else:
        raise ValueError('{} is not in [{}]'.format(i, options))

def error(msg):
    return encode({'error': msg})

# ╔══════════════════════════════════════════════════╗
# ║               Eth Audio API class                ║
# ║ Provides a REST-based JSON API to the TDS system ║
# ╚══════════════════════════════════════════════════╝
class EthAudioServer():

  # ================
  #  initialization
  # ================
  def __init__(self, eth_audio_instance, rx_callback):
    # eth_audio_instance = system's instance of eth_audio runtime
    # rx_callback        = function to handle recieved commands

    print("EthAudio API Server instance created")

    # store reference to TDS_RT, TDS_HEATER_CONTROL, RX callback
    self.eth_audio_instance = eth_audio_instance
    self.rx_callback     = rx_callback

    # definition of RequestHandler only with arguments expected for BaseHTTPRequestHandler
    def __request_handler(*args):
      # pass reference to the instance of this class (TDS_API),
      # followed by the usual arguments expected for BaseHTTPRequestHandler
      HTTPRequestHandler(self, *args)

    # create instance of HTTPServer
    self.httpd = HTTPServer(('0.0.0.0',8080), __request_handler)

    # launch __server_run() on new thread
    # 'daemon=True' option ensures thread will be killed automatically on app close
    server_thread = threading.Thread(target=self.__server_run, daemon=True)
    server_thread.start()

  # ====================================================
  #  server run command (started in background thread)
  # ====================================================
  def __server_run(self):

    print("HTTP server started on %s:%s" % self.httpd.server_address)
    self.httpd.serve_forever() # will block here until app close
    print("HTTP server stopped!")

  # =========================================
  #  parse byte array containing API command
  # =========================================
  def parse_command(self, command_json_text):
      cmd = decode(command_json_text)
      self.eth_audio_instance.test_cmd(cmd)

# ╔══════════════════════════════════════════════════════════╗
# ║                HTTP REQUEST HANDLER class                ║
# ║ Used by HTTPServer in TDS_API to react to HTTP requests  ║
# ╚══════════════════════════════════════════════════════════╝

class HTTPRequestHandler(BaseHTTPRequestHandler):

  # ================
  #  initialization
  # ================
  def __init__(self, eth_audio_instance, *args):

    # store reference to TDS_API instance
    self.eth_audio_instance = eth_audio_instance

    # NOTE: BaseHTTPRequestHandler calls do_GET, do_POST, etc. from INSIDE __init__()
    # So we must set any custom attributes BEFORE CALLING super().__init__
    super().__init__(*args)
        #TODO: connect if necessary then send

  # =============
  #  server logs
  # =============
  def log_message(self, format, *args):
    # prevent HTTP server logs from printing to console
    return

  # =======================================
  #  called upon a GET request from client
  # =======================================
  def do_GET(self):

    # ================ /api ===============
    if(self.path == "/api"):

      # send HTTP code 200 "OK"
      self.send_response(200)
      self.send_header("Content-type", "application/json")
      self.end_headers()
      # send standard response
      self.wfile.write(self.eth_audio_instance.craft_response())

    # ======= unimplemented path ===========
    else:
        # send HTTP code 404 "Not Found"
        self.send_response(404)
        self.end_headers()

  # ================================
  #  called upon a POST from client
  # ================================
  def do_POST(self):

    # ================ /api ===============
    if(self.path == "/api"):

      # get content length and read
      content_length = int(self.headers['Content-Length'])
      content = self.rfile.read(content_length)

      # attempt to parse
      parse_error = self.eth_audio_instance.parse_command(content)
      # reply with appropriate HTTP code
      if(parse_error == None):
        # send HTTP code 200 "OK"
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # send standard response
        self.wfile.write(self.eth_audio_instance.craft_response())

      else:
        # send HTTP code 400 "Bad Request"
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # send error response
        self.wfile.write(self.eth_audio_instance.craft_error(parse_error))

    # ======= unimplemented path ===========
    else:
        # send HTTP code 404 "Not Found"
        self.send_response(404)
        self.end_headers()

# Eth Audio Api, TODO: make this either a base class, put it in another file, and make both a mock class and a real implementation
# For now this is just a mock implementation
class EthAudioApi:

    def __init__(self):
        # This script emulates the JSON command/response server hosted on an EthAudio box
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
        try:
            command = cmd['command']
            if command is None:
                return error('No command specified')
            elif command is 'return_state':
                return self.state()
            elif command is 'set_power':
                return self.set_power(cmd['audio_power'], cmd['usb_power'])
            elif command is 'set_source':
                return self.set_source(cmd['id'], cmd['name'], cmd['digital'])
            elif command is 'set_zone':
                return self.set_zone(cmd['id'], cmd['name'], cmd['source_id'], cmd['mute'], cmd['stby'], cmd['vol'], cmd['disabled'])
            elif command is 'set_group':
                return error('set_group unimplemented')
            elif command is 'create_group':
                return error('create_group unimplemented')
            elif command is 'delete_group':
                return error('delete_group unimplemented')
            else:
                return error('command {} is not supported'.format(command))
        except Exception as e:
            return error(str(e)) # TODO: handle exception more verbosely

    # This command can be used to return the system state
    #{
    #    "command":"return_state"
    #}
    def state(self):
        return encode(self.status)


    # This command can be used to enable / disable the 9V audio power and 5V usb power
    # Along with the command one or more of the parameters can be passed
    # The system state struct will be returned if the command was successfully processed, error response otherwise
    #{
    #    "command":"set_power",
    #    "audio_power": False | True,
    #    "usb_power": False | True
    #}
    def set_power(self, audio_on, usb_on):
        self.status['power']['audio_power'] = audio_on
        self.status['power']['usb_power'] = usb_on

    # This command can be used to modify any of the 4 system sources
    # Along with the command one or more of the parameters can be passed
    # The system state struct will be returned if the command was successfully processed, error response otherwise
    #{
    #    "command":"set_source",
    #    "id":0 | 1 | 2 | 3,
    #    "name":"new name", # sets the friendly name for the source, ie "cd player" or "stream 1"
    #    "digital": False | True # sets the connection for the source, either analog (RCA) or digital (sharpoint)
    #}
    def set_source(self, id, name, digital):
        idx = None
        for i, s in enumerate(self.status['sources']):
            if s['id'] == id:
                idx = i
        if idx is not None:
            try:
                self.status['sources'][idx]['name'] = str(name)
                self.status['sources'][idx]['digital'] = bool(digital)
            except Exception as e:
                return error('set source ' + str(e))
        else:
            return error('set source: index {} out of bounds'.format(idx))

    # This command can be used to modify any zone
    # Along with the command one or more of the parameters can be passed
    # The number of the zones depends on how many boxes are chained together, check system state for # of zones
    # The system state struct will be returned if the command was successfully processed, error response otherwise
    #{
    #    "command":"set_zone",
    #    "id":any valid zone,
    #    "name":"new name" # sets the friendly name for the zone, ie "bathroom" or "kitchen 1"
    #    "source_id": 0 | 1 | 2 | 3
    #    "mute": False | True # this mutes the zone regardless of set volume
    #    "stby": False | True # this sets the zone to standby, very low power consumption
    #    "vol": 0 to -79 # this sets the zone attenuation, 0 is max volume, -79 is min volume
    #    "disabled": False | True # set this to True if the zone is not connected to any speakers and not in use
    #}
    def set_zone(self, id, name, source_id, mute, stby, vol, disabled):
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

# Temporary placmemnt until we finish testing
eth_audio = EthAudioApi()
last_status = deepcopy(eth_audio.state())

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

# pretty print deepdiff's @field name
def pretty_field(field):
    return str(field).replace("root['", "").replace("']","").replace("['", ".")

# show the difference between status when this was last called
#   we use this for debugging
def show_change():
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
    print('intial state:')
    print(eth_audio.state())
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
        eth_audio.test_cmd(cmd) # TODO: add expected result checker here
        show_change()


    # TODO: Start HTTP server (in new thread)

    # TODO: Send HTTP requests and print output

