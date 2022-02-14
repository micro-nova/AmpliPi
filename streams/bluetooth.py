from __future__ import absolute_import, print_function, unicode_literals

import argparse
import os
import xml.etree.ElementTree as ET
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import threading
import subprocess
import signal
from multiprocessing import Process
from dataclasses import dataclass
try:
    from gi.repository import GLib
except ImportError:
    import glib as GLib

BUS_NAME = 'org.bluez'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = "/test/agent"

@dataclass
class BTData:
  def __init__(self):
    self.bus = None
    self.agent_on = False
    self.bluealsa_process = None


def help():
  print("Usage: bluetooth.py [COMMAND] [PARAM]...\nControls bluetooth audio.\n-h\t displays this message and exits.")
  exit()


def ask(prompt):
  try:
      return raw_input(prompt)
  except:
      return input(prompt)


def set_trusted(path):
  props = dbus.Interface(bus.get_object("org.bluez", path),
                          "org.freedesktop.DBus.Properties")
  props.Set("org.bluez.Device1", "Trusted", True)


def dev_connect(path):
  dev = dbus.Interface(bus.get_object("org.bluez", path),
                        "org.bluez.Device1")
  dev.Connect()


class Rejected(dbus.DBusException):
  _dbus_error_name = "org.bluez.Error.Rejected"


class Agent(dbus.service.Object):
  exit_on_release = True

  def set_exit_on_release(self, exit_on_release):
      self.exit_on_release = exit_on_release

  @dbus.service.method(AGENT_INTERFACE,
                        in_signature="", out_signature="")
  def Release(self):
      # print("Release")
      if self.exit_on_release:
          mainloop.quit()

  @dbus.service.method(AGENT_INTERFACE,
                        in_signature="os", out_signature="")
  def AuthorizeService(self, device, uuid):
      # print("Authorizing Service (%s, %s)" % (device, uuid))
      return

  @dbus.service.method(AGENT_INTERFACE,
                        in_signature="o", out_signature="")
  def RequestAuthorization(self, device):
      # print("Authorizing (%s)" % (device))
      return

def start_agent():
  mainloop = GLib.MainLoop()

  bus = dbus.SystemBus()

  agent = Agent(bus, AGENT_PATH)

  obj = bus.get_object(BUS_NAME, "/org/bluez")
  manager = dbus.Interface(obj, "org.bluez.AgentManager1")
  manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")

  manager.RequestDefaultAgent(AGENT_PATH)

  mainloop.run()

DEVICE_INAME = "org.bluez.Device1"
PROPERTIES_INAME = "org.freedesktop.DBus.Properties"
PLAYER_INAME = "org.bluez.MediaPlayer1"

agentthread = threading.Thread(target=start_agent)

def start(params):
  try:
    os.system("bluetoothctl power on")
    if not btData.agent_on:
      print(f'starting bluetooth agent')
      agentthread.start()
      btData.agent_on = True
  except Exception as e:
    print(f'Failed to start bluetooth: {e}')

def stop(params):
  try:
    os.system("bluetoothctl power off")
  except Exception as e:
    print(f"Failed to stop bluetooth: {e}")

def pause(params):
  player = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Pause(dbus_interface=PLAYER_INAME)

def play(params):
  player = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Play(dbus_interface=PLAYER_INAME)


def next_song(params):
  player = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Next(dbus_interface=PLAYER_INAME)


def previous_song(params):
  player = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Previous(dbus_interface=PLAYER_INAME)


def info(params):
  player = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  print(player.Get(PLAYER_INAME, "Track", dbus_interface=PROPERTIES_INAME))


def list_devices(params):
  xmlstr = btData.bus.get_object("org.bluez", "/org/bluez/hci0").Introspect()
  devnodes = ET.fromstring(xmlstr).findall("node")

  deviceMacs = []
  for i in devnodes:
    deviceMacs.append(i.attrib["name"])

  devices = []
  for i in deviceMacs:
    try:
      dev = btData.bus.get_object("org.bluez", "/org/bluez/hci0/" + i)
      devices.append((str(dev.Get(DEVICE_INAME, "Name", dbus_interface=PROPERTIES_INAME)), i, bool(dev.Get(DEVICE_INAME, "Connected", dbus_interface=PROPERTIES_INAME))))
    except Exception as e:
      print(e)

  print(devices)

def pair(params):
  os.system("bluetoothctl discoverable on")
  os.system("bluetoothctl pairable on")

def connect(params):
  btData.bluealsa_process = subprocess.Popen(["bluealsa-aplay", "-D", params[0], "--pcm", f'ch{params[1]}'])
  start([])

def disconnect(params):
  if btData.bluealsa_process is not None:
    os.kill(btData.bluealsa_process.pid, signal.SIGTERM)
    stop([])
    print("disconnected successfully")
  else:
    print("not connected")


dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

btData = BTData()

btData.bus = dbus.SystemBus()

commands = {
  "start": start,
  "stop" : stop,
  "pause": pause,
  "play": play,
  "next": next_song,
  "previous": previous_song,
  "info": info,
  "devices": list_devices,
  "pair": pair,
  "connect": connect,
  "disconnect": disconnect
}

args = sys.argv[1:]

command = None
params = []

if len(args) > 0:

  if(args[0] == "-h"):
    help()

  command = args.pop(0)

if len(args) > 0:
  params = args

if command != None:
  commands[command](params)
else:
    while True:
      text = input("# ")
      try:
        command = None
        params = []

        args = text.split()
        if len(args) > 0:
          command = args.pop(0)
        if len(args) > 0:
          params = args

        if command != None:
          commands[command](params)
      except Exception as e:
        print(f'error: {e}')
        pass
