#!/usr/bin/python3

import json

# import HTTP server and request handler, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# get my ip
import socket

# Helper functions for encoding and decoding JSON
def encode(pydata):
  """ Encode a dictionary as JSON """
  return json.dumps(pydata)

def decode(j):
  """ Decode JSON into dictionary """
  return json.loads(j)

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
    print("HTTP server started on {}:{}".format(*self.httpd.server_address))

    """ Try to figure out the system IP address for convenience, this assumes the HTTP server is started locally"""
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(("8.8.8.8", 80))
      print('This server can probably be connected to with: {}:{}'.format(s.getsockname()[0], self.httpd.server_address[1]))
    except Exception as e:
      print('Failed to figure out local ip address: {}'.format(e))

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
    return self.eth_audio_instance.parse_cmd(cmd)

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
