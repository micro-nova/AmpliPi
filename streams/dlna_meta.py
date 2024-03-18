""" DLNA Metadata Reader
    This script uses upnp to translate metadata to a json, download cover art, and control a DLNA renderer.
    It takes in a name for the DLNA renderer,
    a fifo file for commands (play, pause, stop, next, prev),
    and a path to place the metadata file (a json).
    and a directory to place cover art in.
    a fifo will be created at the path provided if it does not exist.
"""

import argparse
import upnpy
from upnpy.ssdp.SSDPDevice import SSDPDevice
import json
import os
import sys
import threading
import time
import logging
import xml.etree.ElementTree as ET

# the interval at which to update the metadata file
METADATA_UPDATE_INTERVAL = 3 # seconds

MIN_STOP_TIME = 10 # seconds

# Reads metadata from the upnp AVTransport and writes it to a json file in a loop.
def metadata_reader(metadata_path: str, album_art_dir: str, service: SSDPDevice, debug: bool = False):
  """ Read metadata from the upnp AVTransport and write it to a file. """
  last_file = ''           # last cover art file downloaded
  stop_counter = 0         # counter to prevent empty metadata on transitions
  metadata = {"state":"stopped",  # metadata dict to write to file
              "title":"",
              "artist":"",
              "album":"",
              "album_art":""}

  with open(metadata_path, 'w') as f:
    while True:

      # sleep for a bit
      time.sleep(METADATA_UPDATE_INTERVAL)

      try:

        # try to get the transport state and convert it to a valid string
        try:
          transport_state = service.GetTransportInfo(InstanceID=0)["CurrentTransportState"]
          if(transport_state == "PLAYING"):
            metadata["state"] = "playing"
          elif(transport_state == "PAUSED_PLAYBACK"):
            metadata["state"] = "paused"
          elif(transport_state == "STOPPED"):
            stop_counter += METADATA_UPDATE_INTERVAL
            if stop_counter >= MIN_STOP_TIME: # only set to stopped if it's been stopped for a few seconds
              metadata["state"] = "stopped"
          else:
            metadata["state"] = "playing" # default to playing for states like TRANSITIONING

          if transport_state == "TRANSITIONING": # metadata is empty while transitioning so just skip this state
            continue

          if transport_state != "STOPPED": # reset the stop counter if the state is not stopped
            stop_counter = 0

        except Exception as e:
          logger.error(f"Error: could not get transport state: {e}")

        # try to get song-info from the service and parse it
        try:
          meta_xml = ET.fromstring(service.GetMediaInfo(InstanceID=0)["CurrentURIMetaData"])
          metadata["title"] = ""
          metadata["artist"] = ""
          metadata["album"] = ""
          for i in meta_xml.iter():
            if i.tag == "{http://purl.org/dc/elements/1.1/}title":
              metadata["title"] = i.text
            elif i.tag == "{urn:schemas-upnp-org:metadata-1-0/upnp/}artist":
              metadata["artist"] = i.text
            elif i.tag == "{urn:schemas-upnp-org:metadata-1-0/upnp/}album":
              metadata["album"] = i.text
            elif i.tag == "{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI":
              # limit the file name to 200 characters to prevent going over the limit of 255 chars (yes this happened once)
              # note: this does mean that if the art for two songs starts with the same 200 characters, the second one will not be downloaded, this is pretty unlikely
              fname = (i.text.split('/')[-1])[0:200]
              logger.debug(f"Downloading album art {i.text} to {album_art_dir}/{fname}")

              # move to the album art directory and download the file (if it changed), if it fails delete the file
              os.system(f"cd {album_art_dir} && wget -q -N {i.text} -O {fname} || rm -f {album_art_dir}/{fname}")

              # if the file exists, set the metadata to the file name
              if os.path.exists(f"{album_art_dir}/{fname}"):
                if fname != last_file: # if it's a new file delete the old one
                  if last_file: # handle the case where this is the first file downloaded
                    os.remove(f"{album_art_dir}/{last_file}")
                  last_file = fname

                metadata["album_art"] = fname
              else:
                metadata["album_art"] = ""
        except Exception as e:
          logger.debug(f"Error: could not get song-info: {e}")

        logger.debug(f"writing metadata {metadata}")

        # empty file and write metadata
        f.truncate(0)
        f.seek(0)
        json.dump(metadata, f)
        f.flush()
      except Exception as e:
        logger.error(f"Error: could not write metadata: {e}")


# Blocks until a line is put in the fifo, then executes the command in that line.
def command_executor(fifo_path: str, service: SSDPDevice, debug: bool = False):
  """ Execute commands from the fifo file. """
  # if fifo does not exist, create it
  if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)
    logger.debug(f"Created fifo file at {fifo_path}")
  else:
    logger.debug(f"Found file at {fifo_path}")
    if os.path.isfile(fifo_path): # pipes return false for isfile
      logger.error(f"Error: file at {fifo_path} is not a fifo")
      sys.exit(1)

  # open the fifo file and read commands
  with open(fifo_path, 'r') as fifo:
    while True:
      cmd = fifo.readline().strip()

      if not cmd:
        logger.error("Error: fifo closed, exiting")
        break

      logger.debug(f"Received command {cmd}")
      if cmd=='play':
        try:
          service.Play(InstanceID=0, Speed=1)
        except Exception as e:
          logger.error(f"Error: could not play: {e}")
      elif cmd=='pause':
        try:
          service.Pause(InstanceID=0)
        except Exception as e:
          logger.error(f"Error: could not pause: {e}")
      elif cmd=='stop':
        try:
          service.Stop(InstanceID=0)
        except Exception as e:
          logger.error(f"Error: could not stop: {e}")
      #TODO: implement next and prev, gmrender-resurrect does not support these commands directly
      # elif cmd=='next':
      #   try:
      #     service.Seek(InstanceID=0, Unit='ABS_COUNT', Target=service.GetPositionInfo(InstanceID=0)["AbsCount"])
      #   except Exception as e:
      #     print(f"Error: could not go to next: {e}")
      # elif cmd=='prev':
      #   try:
      #     service.Previous(InstanceID=0)
      #   except Exception as e:
      #     print(f"Error: could not go to previous: {e}")
      else:
        logger.error(f"Error: invalid command {cmd}")

  sys.exit(0)


# setup command line arguments
parser = argparse.ArgumentParser(description='DLNA Metadata Reader')
parser.add_argument('name', metavar='name', type=str, help='name of the dlna renderer')
parser.add_argument('fifo', metavar='fifo', type=str, help='path to the fifo file for commands, will be created if it does not exist, valid commands are play, pause, stop, next, prev')
parser.add_argument('metadata', metavar='metadata', type=str, help='path to the metadata file')
parser.add_argument('albumart', metavar='albumart', type=str, help='path to the directory to place cover art')
parser.add_argument('-d', '--debug', action='store_true', help='print debug messages')
args = parser.parse_args()

# create logger
logger = logging.getLogger(__name__)
if args.debug:
  logger.setLevel(logging.DEBUG)
else:
  logger.setLevel(logging.INFO)
sh = logging.StreamHandler(sys.stdout)
logger.addHandler(sh)

# first, search for upnp devices and pick the one that matches the name
device = None
while True:
  time.sleep(0.25) # wait a bit before checking
  devices = upnpy.UPnP().discover()
  for d in devices:
    logger.debug(f"Found upnp device with name {d.friendly_name}.")
    if d.friendly_name == args.name:
      device = d
      logger.debug(f"Using upnp device {d.friendly_name}.")
      break

  # if no device was found, exit
  if device is None:
    logger.error(f"Error: no upnp device found with name {args.name}, trying again...")
  else:
    break

# next, get the media transport service
service = None
try:
  service = device.AVTransport
except Exception as e:
  logger.error(f"Error: could not get AVTransport service from upnp device at {args.ip}: {e}")
  sys.exit(1)

logger.debug(f"Using AVTransport service with actions {service.actions}.")

# create two threads, one to read metadata and one to execute commands
threading.Thread(target=metadata_reader, args=(args.metadata, args.albumart, service, args.debug)).start()
threading.Thread(target=command_executor, args=(args.fifo, service, args.debug)).start()
