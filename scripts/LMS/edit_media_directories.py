#!/usr/bin/python
#/usr/local/bin
"""A program for automatically adding and removing removable drives to the LMS media drives list"""
import psutil

def add_directories(usb_drives: list):
  """Check list of connected drives, compare to list of recognized drives and add drives that are not recognized but are connected"""
  with open('/var/lib/squeezeboxserver/prefs/server.prefs', 'r+', encoding='utf-8') as file:
    lines = file.readlines()

    media_drives = [] # Check for already recognized drives to avoid duplication
    index = None # Find the location of the mediadirs line to insert newlines after it later
    for i, line in enumerate(lines):
      if 'mediadirs' in line:
        index = i
      if '/media/pi' in line:
        media_drives.append(line)

    insert = True # if true, insert new drive into list
    for d, drive in enumerate(usb_drives):
      for m, media_drive in enumerate(media_drives):
        if drive in media_drive: # Is the current drive anywhere on the media drives list already?
          insert = False # do not insert drive into list if already on list
      if insert:
        lines.insert(index+1, f"- {drive}\n")

    # Go to the start of the file, delete everything, save with modified lines
    file.seek(0)
    file.truncate()
    file.writelines(lines)


def remove_directories(usb_drives: list):
  """Check list of connected drives, compare to list of recognized drives and remove drives that are recognized but not connected"""
  with open('/var/lib/squeezeboxserver/prefs/server.prefs', 'r+', encoding='utf-8') as file:
    lines = file.readlines()
    for i, line in enumerate(lines):
      if "/media/pi" in line:
        # In case of multiple usb storage devices, remove only absent drives from device list
        remove_line = True
        for d, drive in enumerate(usb_drives):
          if drive in line:
            remove_line = False
        if remove_line:
          lines.pop(i)

    # Go to the start of the file, delete everything, save with modified lines
    file.seek(0)
    file.truncate()
    file.writelines(lines)


def check_default():
  """Set mediadirs line to default state, either 'mediadirs:' or 'mediadirs: []'"""
  with open('/var/lib/squeezeboxserver/prefs/server.prefs', 'r+', encoding='utf-8') as file:
    lines = file.readlines()
    index = None
    for i, line in enumerate(lines):
      if 'mediadirs' in line:
        index = i
    if index is not None:
      if '-' in lines[index + 1]:
        lines[index] = "mediadirs:\n" # Remove the empty array that signifies no media drives
      else:
        lines[index] = "mediadirs: []\n" # If no media drives, replace default empty array

    # Go to the start of the file, delete everything, save with modified lines
    file.seek(0)
    file.truncate()
    file.writelines(lines)


def get_usb_drives():
  """Reads the mount point for removable drives, returns them in a list"""
  usb_drives = []
  for partition in psutil.disk_partitions():
    # Exclude rootfs, the backup drive that happens to mount to /media/pi
    if '/media/pi' in partition.mountpoint and not 'rootfs' in partition.mountpoint:
      usb_drives.append(str(partition.mountpoint))
  return usb_drives


if __name__ == "__main__":
  usb_drives = get_usb_drives() # Get list of available drives
  add_directories(usb_drives) # Pass list of drives, see if any should be added
  remove_directories(usb_drives) # Pass list of drives, see if any should be removes
  check_default() # After all adding and removing, check if there are any drives left and set mediadirs to proper default state
