import argparse
import os
import xml.etree.ElementTree as ET
import dbus

DEVICE_INAME = "org.bluez.Device1"
PROPERTIES_INAME = "org.freedesktop.DBus.Properties"
PLAYER_INAME = "org.bluez.MediaPlayer1"

real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)

def start(params):
  try:
    os.system("bluetoothctl power on")
    print(f'trying to start btagent dir {dir_path}')
    os.system(f'python3 {dir_path}/btagent.py &')
  except Exception as e:
    print(f'Failed to start bluetooth: {e}')

def stop(params):
  try:
    os.system("bluetoothctl power off")
    os.system("pkill -e -f btagent.py")
  except Exception as e:
    print(f"Failed to stop bluetooth: {e}")

def pause(params):
  player = bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Pause(dbus_interface=PLAYER_INAME)

def play(params):
  player = bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Play(dbus_interface=PLAYER_INAME)


def next_song(params):
  player = bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Next(dbus_interface=PLAYER_INAME)


def previous_song(params):
  player = bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  player.Previous(dbus_interface=PLAYER_INAME)

def info(params):
  player = bus.get_object("org.bluez", "/org/bluez/hci0/" + params[0] + "/player0")
  print(player.Get(PLAYER_INAME, "Track", dbus_interface=PROPERTIES_INAME))


def list_devices(params):
  xmlstr = bus.get_object("org.bluez", "/org/bluez/hci0").Introspect()
  devnodes = ET.fromstring(xmlstr).findall("node")

  deviceMacs = []
  for i in devnodes:
    deviceMacs.append(i.attrib["name"])

  devices = []
  for i in deviceMacs:
    try:
      dev = bus.get_object("org.bluez", "/org/bluez/hci0/" + i)
      devices.append((str(dev.Get(DEVICE_INAME, "Name", dbus_interface=PROPERTIES_INAME)), i, bool(dev.Get(DEVICE_INAME, "Connected", dbus_interface=PROPERTIES_INAME))))
    except Exception as e:
      print(e)

  print(devices)

def pair(params):
  os.system("bluetoothctl discoverable on")
  os.system("bluetoothctl pairable on")

def is_running(params):
  raise NotImplementedError

def connect(params):
  os.system(f"bluealsa-aplay -D {params[0]} {params[1]}")

def disconnect(params):
  raise NotImplementedError


bus = dbus.SystemBus()

parser = argparse.ArgumentParser(description='Controls bluetooth audio.')
parser.add_argument('command', metavar='Command', type=str, nargs=1, help=
  'A command to run, supported commands are devices, connect, start, stop, pause, play, next, previous, and info.')
parser.add_argument('params', metavar="Parameters", type=str, nargs=argparse.REMAINDER, help=
  "Arguments following the command for commands that support arguments.")

args = parser.parse_args()
command = args.command
params = args.params

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
  "isRunning": is_running,
  "connect": connect,
  "disconnect": disconnect
}

commands[command[0]](params)
