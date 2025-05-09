#!/usr/bin/env python3
# A program for automatically adding and removing removable drives to the LMS media drives list
import psutil
import logging
import sys
import subprocess

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def check_lms_mode():
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
    if '/media' in partition.mountpoint and 'rootfs' not in partition.mountpoint:
      usb_drives.append(str(partition.mountpoint))
      logger.info(f"Found USB device at: {partition.mountpoint}")
  return usb_drives


def edit_directories(logger: logging.Logger, sesh: requests.Session):
  """Update LMS server with list of drives"""
  try:
    usb_drives = get_usb_drives(logger)  # Get list of available drives
    is_lms_mode = check_lms_mode()
    if is_lms_mode:
      usb_drives.append("")  # Add blank drive to reflect empty string that is always at the end of the mediadirs section of request body
      url = 'http://localhost:9000/settings/server/basic.html'
      data = {
        'saveSettings': '1',
        'useAJAX': '0',
        'page': 'BASIC_SERVER_SETTINGS',
        'pref_language': 'EN',
        'pref_libraryname': '',
        'pref_playlistdir': '',
        'pref_rescantype': '1rescan'
      }  # All default headers, mediadirs added in loop
      for d, drive in enumerate(usb_drives):
        data[f"pref_mediadirs{d}"] = drive
        data[f"pref_ignoreInAudioScan{d}"] = 1

      logger.info("Adding drives to LMS settings...")
      sesh.post(url, data=data, verify=False, timeout=5)
      logger.info("Drives added, LMS scanning now.")
    else:
      if len(usb_drives) > 0:
        drives = ""
        for drive in usb_drives:
          drives += f"{drive}, "
        logger.info(f"Detected drives: {drives}")
        logger.info("If you wish to mount these to the internal LMS server, please go to Config and set LMS Mode")
  except Exception as e:
    logger.error(f"LMS Automated Drive Mounting has encountered an error: {e}")


if __name__ == "__main__":
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.DEBUG)
  sh = logging.StreamHandler(sys.stdout)
  logger.addHandler(sh)

  session = requests.Session()
  retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
  session.mount('http://', HTTPAdapter(max_retries=retries))

  edit_directories(logger, session)
