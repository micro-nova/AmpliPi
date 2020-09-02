#!/usr/bin/python3

import json
import http.client

# Helper functions for encoding and decoding JSON
def encode(pydata):
  """ Encode a dictionary as JSON """
  return json.dumps(pydata)

def decode(j):
  """ Decode JSON into dictionary """
  return json.loads(j)

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
