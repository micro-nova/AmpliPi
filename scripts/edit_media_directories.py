#!/usr/bin/python
#/usr/local/bin
"""A program for automatically adding and removing removable drives to the LMS media drives list"""
import psutil
import requests

def get_usb_drives():
  """Reads the mount point for removable drives, returns them in a list"""
  usb_drives = []
  for partition in psutil.disk_partitions():
    # Exclude rootfs, the backup drive that happens to mount to /media/pi
    if '/media/pi' in partition.mountpoint and not 'rootfs' in partition.mountpoint:
      usb_drives.append(str(partition.mountpoint))
  return usb_drives


def edit_directories():
  """Update LMS server with list of drives"""
  usb_drives = get_usb_drives() # Get list of available drives
  usb_drives.append("") # Add blank drive to reflect empty string that is always at the end of the mediadirs section of request body
  url = 'http://localhost:9000/settings/server/basic.html'
  data={
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

  requests.post(url, data=data, verify=False, timeout=5)



if __name__ == "__main__":
  edit_directories()
