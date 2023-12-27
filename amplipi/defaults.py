import os

from time import time
from shutil import copy

from enum import Enum
from typing import List, Dict, Set, Union, Optional, Callable

from amplipi import models

MUTE_ALL_ID = 10000
LAST_PRESET_ID = 9999
RCAs = [996, 997, 998, 999]
LMS_DEFAULTS = [1000, 1001, 1002, 1003]

USER_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')

DEFAULT_CONFIG = {  # This is the system state response that will come back from the amplipi box
  "sources": [  # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
    {"id": 0, "name": "Input 1", "input": ""},
    {"id": 1, "name": "Input 2", "input": ""},
    {"id": 2, "name": "Input 3", "input": ""},
    {"id": 3, "name": "Input 4", "input": ""},
  ],
  # NOTE: streams and groups seem like they should be stored as dictionaries with integer keys
  #       this does not make sense because JSON only allows string based keys
  "streams": [
    {"id": RCAs[0], "name": "Input 1", "type": "rca", "index": 0, "disabled": False},
    {"id": RCAs[1], "name": "Input 2", "type": "rca", "index": 1, "disabled": False},
    {"id": RCAs[2], "name": "Input 3", "type": "rca", "index": 2, "disabled": False},
    {"id": RCAs[3], "name": "Input 4", "type": "rca", "index": 3, "disabled": False},
    {"id": 1000, "name": "Groove Salad", "type": "internetradio", "url": "http://ice6.somafm.com/groovesalad-32-aac",
     "logo": "https://somafm.com/img3/groovesalad-400.jpg", "disabled": False},
  ],
  "zones": [  # this is an array of zones, array length depends on # of boxes connected
    {"id": 0, "name": "Zone 1", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 1, "name": "Zone 2", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 2, "name": "Zone 3", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 3, "name": "Zone 4", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 4, "name": "Zone 5", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 5, "name": "Zone 6", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
  ],
  "groups": [
  ],
  "presets": [{
    # NOTE: additional zones are added automatically to this preset
    "id": MUTE_ALL_ID,
    "name": "Mute All",
    "state": {
      "zones": [
        {"id": 0, "mute": True},
        {"id": 1, "mute": True},
        {"id": 2, "mute": True},
        {"id": 3, "mute": True},
        {"id": 4, "mute": True},
        {"id": 5, "mute": True},
      ]
    }
  }]
}

STREAMER_CONFIG = {  # This is the system state response that will come back from the amplipi box
  "sources": [  # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
    {"id": 0, "name": "Output 1", "input": ""},
    {"id": 1, "name": "Output 2", "input": ""},
    {"id": 2, "name": "Output 3", "input": ""},
    {"id": 3, "name": "Output 4", "input": ""},
  ],
  "streams": [
    {"id": 1000, "name": "Groove Salad", "type": "internetradio", "url": "http://ice6.somafm.com/groovesalad-32-aac",
     "logo": "https://somafm.com/img3/groovesalad-400.jpg", "disabled": False},
  ],
  "zones": [  # this is an array of zones, array length depends on # of boxes connected
  ],
  "groups": [
  ],
  "presets": [
  ]
}

DEFAULT_LMS_CONFIG = {  # This is the system state response that will come back from the amplipi box
  "sources": [  # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
    {"id": 1, "name": "Input 1", "input": f"stream={LMS_DEFAULTS[0]}"},
    {"id": 2, "name": "Input 2", "input": f"stream={LMS_DEFAULTS[1]}"},
    {"id": 3, "name": "Input 3", "input": f"stream={LMS_DEFAULTS[2]}"},
    {"id": 4, "name": "Input 4", "input": f"stream={LMS_DEFAULTS[3]}"},
  ],
  # NOTE: streams and groups seem like they should be stored as dictionaries with integer keys
  #       this does not make sense because JSON only allows string based keys
  "streams": [
    {"id": RCAs[0], "name": "Input 1", "type": "rca", "index": 0, "disabled": False},
    {"id": RCAs[1], "name": "Input 2", "type": "rca", "index": 1, "disabled": False},
    {"id": RCAs[2], "name": "Input 3", "type": "rca", "index": 2, "disabled": False},
    {"id": RCAs[3], "name": "Input 4", "type": "rca", "index": 3, "disabled": False},
    {"id": LMS_DEFAULTS[0], "name": "Music 1", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[1], "name": "Music 2", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[2], "name": "Music 3", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[3], "name": "Music 4", "type": "lms", "server": "localhost"},
  ],
  "zones": [  # this is an array of zones, array length depends on # of boxes connected
    {"id": 0, "name": "Zone 1", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 1, "name": "Zone 2", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 2, "name": "Zone 3", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 3, "name": "Zone 4", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 4, "name": "Zone 5", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
    {"id": 5, "name": "Zone 6", "source_id": 0, "mute": True, "disabled": False,
     "vol_f": models.MIN_VOL_F, "vol_min": models.MIN_VOL_DB, "vol_max": models.MAX_VOL_DB},
  ],
  "groups": [
  ],
  "presets": [{
    # NOTE: additional zones are added automatically to this preset"id": MUTE_ALL_ID,
    "name": "Mute All",
    "state": {
      "zones": [
        {"id": 0, "mute": True},
        {"id": 1, "mute": True},
        {"id": 2, "mute": True},
        {"id": 3, "mute": True},
        {"id": 4, "mute": True},
        {"id": 5, "mute": True},
      ]
    }
  }]
}

STREAMER_LMS_CONFIG = {  # This is the system state response that will come back from the amplipi box
  "sources": [  # this is an array of source objects, each has an id, name, type specifying whether source comes from a local (like RCA) or streaming input like pandora
    {"id": 1, "name": "Output 1", "input": f"stream={LMS_DEFAULTS[0]}"},
    {"id": 2, "name": "Output 2", "input": f"stream={LMS_DEFAULTS[1]}"},
    {"id": 3, "name": "Output 3", "input": f"stream={LMS_DEFAULTS[2]}"},
    {"id": 4, "name": "Output 4", "input": f"stream={LMS_DEFAULTS[3]}"},
  ],
  "streams": [
    {"id": LMS_DEFAULTS[0], "name": "Music 1", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[1], "name": "Music 2", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[2], "name": "Music 3", "type": "lms", "server": "localhost"},
    {"id": LMS_DEFAULTS[3], "name": "Music 4", "type": "lms", "server": "localhost"},
  ],
  "zones": [  # this is an array of zones, array length depends on # of boxes connected
  ],
  "groups": [
  ],
  "presets": [
  ]
}


def default_config(is_streamer: bool, lms_mode: bool) -> dict:
  """ Given a little bit of system state, return the correct default
      configuration for a given appliance.
  """
  if not lms_mode and is_streamer:
    return STREAMER_CONFIG
  elif lms_mode and is_streamer:
    return STREAMER_LMS_CONFIG
  elif lms_mode and not is_streamer:
    return DEFAULT_LMS_CONFIG
  return DEFAULT_CONFIG
