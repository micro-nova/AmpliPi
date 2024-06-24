#!/usr/bin/env python3
# A program for automatically adding and removing removable drives to the LMS media drives list
import psutil
import requests
import logging
import sys
import subprocess

def CheckLMSMode():
    try:
        status_output = subprocess.check_output('systemctl is-active logitechmediaserver', shell=True).decode().strip()
        return status_output == 'active'
    except subprocess.CalledProcessError:
        return False


def get_usb_drives(logger: logging.Logger):
  """Reads the mount point for removable drives, returns them in a list"""
  usb_drives = []
  logger.debug("Searching for mounted USB devices")
  for partition in psutil.disk_partitions():
    # Exclude rootfs, the backup drive that happens to mount to /media/pi
    if '/media/pi' in partition.mountpoint and 'rootfs' not in partition.mountpoint:
      usb_drives.append(str(partition.mountpoint))
      logger.info(f"Found USB device at: {partition.mountpoint}")
  return usb_drives


def edit_directories(logger: logging.Logger):
  """Update LMS server with list of drives"""
  usb_drives = get_usb_drives(logger) # Get list of available drives
  LMSMode = CheckLMSMode()
  if LMSMode:
    usb_drives.append("") # Add blank drive to reflect empty string that is always at the end of the mediadirs section of request body
    url = 'http://localhost:9000/settings/server/basic.html'
    data = {
      'saveSettings': '1',
      'useAJAX': '0',
      'page': 'BASIC_SERVER_SETTINGS',
      'pref_language': 'EN',
      'pref_libraryname': '',
      'pref_playlistdir': '',
      'pref_rescantype': '1rescan'
    } # All default headers, mediadirs added in loop
    for d, drive in enumerate(usb_drives):
      data[f"pref_mediadirs{d}"] = drive
      data[f"pref_ignoreInAudioScan{d}"] = 1

  logger.info("Adding drives to LMS settings...")
  requests.post(url, data=data, verify=False, timeout=5)
  logger.info("Drives added, LMS scanning now.")



if __name__ == "__main__":
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)
  sh = logging.StreamHandler(sys.stdout)
  logger.addHandler(sh)

  edit_directories(logger)
