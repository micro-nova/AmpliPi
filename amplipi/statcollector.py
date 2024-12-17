#!/usr/bin/env python3
"""Stat Collector for AmpliPi; collects data, saves it to a json file, then phones home with user consent every X days/weeks"""
import os
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from shutil import disk_usage
import requests
# pylint: disable=no-name-in-module
from pydantic import BaseModel
from psutil import virtual_memory

path = "/var/lib/UsageSurvey.json"

def find_matches(list1: list, list2: list):
  """Takes in two lists, returns a list that only contains data shared by both lists"""
  set1 = {json.dumps(item, sort_keys=True) for item in list1}
  set2 = {json.dumps(item, sort_keys=True) for item in list2}

  matches = [json.loads(item) for item in set1 & set2]
  return matches


def average(running_average, weight, new_entry):
  """
    Calculates an average using three variables:
    running_average, the average so far
    weight, the count of numbers that went into that average
    new_entry, the newest addition to the dataset
    Returns the new average
  """
  # Round to nearest whole number, then int() to shave of trailing .0
  return int(round(((running_average * weight) + new_entry) / (weight + 1), 0))


class StreamUsageSchema(BaseModel):
  """Schema for individual stream type usage statistics"""
  # For the purpose of the below comments, a "survey cycle" is defined as how often the device phones home
  active_streams: list = []

  # The highest number of concurrent streams running within the survey cycle
  average_concurrent_streams: int = 0
  peak_concurrent_streams: int = 0

  # The length in seconds that a stream of this type has been connected within the survey cycle
  # Counts as long as at least one playing stream of the given type persists between polling calls
  current_runtime: int = 0
  average_runtime: int = 0
  runtime_weight: int = 0
  peak_runtime: int = 0

  def consume(self, source_info: list, poll_count: int, timediff: timedelta):
    """Consumes a list of source["info"] json blobs and updates stream statistics tracker with information found within"""
    stream_names = [item["name"] for item in source_info]
    stream_count = len(stream_names)

    if stream_count == 0 and len(self.active_streams) != 0:  # If a stream has just been shut off, record average based on current runtime
      new_average = average(self.average_runtime, self.runtime_weight, self.current_runtime)
      self.average_runtime = new_average
      self.runtime_weight += 1

    matches = find_matches(self.active_streams, stream_names)
    if len(matches) != 0:  # If there is at least one playing match, calculate runtime
      self.current_runtime = self.current_runtime + timediff.seconds

      self.peak_runtime = max(self.peak_runtime, self.current_runtime) if self.current_runtime < 86400 else 86400
    else:
      self.current_runtime = 0

    self.peak_concurrent_streams = max(self.peak_concurrent_streams, stream_count)
    self.average_concurrent_streams = average(self.average_concurrent_streams, poll_count, stream_count)

    # set current data to be next poll's previous data
    self.active_streams = stream_names


class UsageSurveySchema(BaseModel):
  """A verification layer for JSON objects to be sent to the Usage Survey server"""
  # Auth code that legitimizes the data as coming from a MicroNova AmpliPro and not some random other source
  authentication_code: str = os.environ.get('AUTH_CODE', "")
  amplipi_version: str = ""
  is_streamer: bool = False

  poll_count: int = 0  # Used to calculate averaged values
  time_of_first_poll: datetime = datetime.min
  time_of_previous_poll: datetime = datetime.min

  # Memory measured in Kb
  peak_memory_usage: int = 0
  average_memory_usage: int = 0

  # Disk space measured in Gb
  # Disk average not collected as it's less variable over time
  disk_total: int = 0
  disk_used: int = 0
  disk_free: int = 0

  # Used to store notable events, such as anything that occurs above a logging level of warning. See record_logs() function for details.
  notable_logs: list = []

  # These were once in a dict called "streams" that contained the data in the same format, having there not be dicts 3 layers deep seemed prefferable
  airplay: StreamUsageSchema = StreamUsageSchema()
  aux: StreamUsageSchema = StreamUsageSchema()
  bluetooth: StreamUsageSchema = StreamUsageSchema()
  dlna: StreamUsageSchema = StreamUsageSchema()
  fileplayer: StreamUsageSchema = StreamUsageSchema()
  internetradio: StreamUsageSchema = StreamUsageSchema()
  lms: StreamUsageSchema = StreamUsageSchema()
  media_device: StreamUsageSchema = StreamUsageSchema()
  pandora: StreamUsageSchema = StreamUsageSchema()
  plexamp: StreamUsageSchema = StreamUsageSchema()
  rca: StreamUsageSchema = StreamUsageSchema()
  spotify: StreamUsageSchema = StreamUsageSchema()

  def save_to_disk(self):
    """Saves contents of UsageSurvey to file"""
    tmp = "/tmp/UsageSurvey.json"
    with open(tmp, "w", encoding="UTF-8") as file:
      file.write(self.json())
    subprocess.run(['sudo', 'mv', tmp, path], check=True)

  @classmethod
  def load_from_disk(cls):
    """Loads contents of UsageSurvey from saved file"""
    if os.path.exists(path):
      with open(path, "r", encoding="UTF-8") as file:
        file_data = json.load(file)
        return cls(**file_data)
    else:
      return cls()

  def phone_home(self):
    """Send contents back to amplipi devs, and delete current state to refresh the data cycle"""
    url = "Currently unknown"  # TODO: Update this url after finishing the hosted home base side of the stat collector
    response = requests.post(url, json={**self}, timeout=10)
    if os.path.exists(path) and response.status_code == 200:
      subprocess.run(['sudo', 'rm', path], check=True)

  def get_disk_usage(self):
    """Collects and populates disk usage statistics via shutil"""
    self.disk_total, self.disk_used, self.disk_free = disk_usage("/")

  def get_mem_usage(self):
    """Collects and populates memory usage statistics via psutil"""
    memory_info = virtual_memory()
    used_memory = memory_info.used

    self.peak_memory_usage = max(self.peak_memory_usage, used_memory)
    self.average_memory_usage = average(self.average_memory_usage, self.poll_count, used_memory)

  def record_logs(self):
    """Reads journalctl and searches for a list of keywords, then saves new logs to self.notable_logs"""
    keywords = ["WARNING", "ERROR"]

    result = subprocess.run(
        ["journalctl", "--no-pager", f"--grep={'|'.join(keywords)}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    # Split logs into individual line items in a list, then add new entries to the notable_logs list
    logs = result.stdout.splitlines()
    # Removes the timestamp and hostname of logs, helps sort out logs that are the same but would be seen as different due to a different timestamp
    pattern = r"^[A-Za-z]{3} \d{1,2} \d{2}:\d{2}:\d{2} \S+ "
    logs = [re.sub(pattern, "", log) for log in logs]

    # Was once a single line: self.notable_logs.extend([log for log in logs if log not in self.notable_logs])
    # That didn't work as some duplicates were within logs but not self.notable_logs
    # so they weren't filtered against and would get flushed to self.notable_logs at the end of the loop
    for log in logs:
      if log not in self.notable_logs:
        self.notable_logs.extend([log])

  def get_state(self):
    """Gets system state, saves to relevant places"""
    state = requests.get("http://localhost/api", timeout=1)
    if state.status_code == 200:
      state_json = state.json()
      now = datetime.now(timezone.utc)  # in UTC to avoid any issues if we do implement a user-set timezone option
      if self.time_of_first_poll == datetime.min:
        self.time_of_first_poll = now

      timediff = (now - self.time_of_previous_poll) if self.time_of_previous_poll != datetime.min else timedelta(0)
      stream_handlers = {
        "airplay": {"object": self.airplay, "list": []},
        "aux": {"object": self.aux, "list": []},
        "bluetooth": {"object": self.bluetooth, "list": []},
        "dlna": {"object": self.dlna, "list": []},
        "fileplayer": {"object": self.fileplayer, "list": []},
        "internetradio": {"object": self.internetradio, "list": []},
        "lms": {"object": self.lms, "list": []},
        "media_device": {"object": self.media_device, "list": []},
        "pandora": {"object": self.pandora, "list": []},
        "plexamp": {"object": self.plexamp, "list": []},
        "rca": {"object": self.rca, "list": []},
        "spotify": {"object": self.spotify, "list": []},
      }

      for source in state_json["sources"]:
        if source["input"] and source.get("info", {}).get("state") in ["playing", "connected"]:
          stream_type = source["info"]["type"]
          if stream_type in stream_handlers:
            stream_handlers[stream_type]["list"].append(source["info"])

      for _, handler in stream_handlers.items():
        handler["object"].consume(handler["list"], self.poll_count, timediff)

      self.poll_count += 1
      self.time_of_previous_poll = now
      self.amplipi_version = state_json["info"]["version"]
      self.is_streamer = state_json["info"]["is_streamer"]
      self.get_disk_usage()
      self.get_mem_usage()
      self.record_logs()


if __name__ == "__main__":
  UsageSurvey = UsageSurveySchema.load_from_disk()
  UsageSurvey.get_state()
  UsageSurvey.save_to_disk()
