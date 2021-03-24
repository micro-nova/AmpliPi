
# Simple Server-Sent Events (SSE) implementation
#
# based on https://github.com/MaxHalford/flask-sse-no-deps
#
# The MIT License (MIT)
#
# Copyright (c) 2020 Max Halford, 2021 MicroNova
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import queue
import json
from typing import Union

class MessageAnnouncer:
  """ A message publisher for SSE messages """
  def __init__(self):
    self.listeners = []

  def listen(self):
    self.listeners.append(queue.Queue(maxsize=5))
    return self.listeners[-1]

  def announce(self, msg: str):
    # We go in reverse order because we might have to delete an element, which will shift the
    # indices backward
    for i in reversed(range(len(self.listeners))):
      try:
        self.listeners[i].put_nowait(msg)
      except queue.Full:
        del self.listeners[i]


def format(data: Union[str,dict], event=None) -> str:
    """Formats a string and an event name in order to follow the event stream convention.
    >>> format_sse({'abc': 123}, event='Jackson 5')
    'event: Jackson 5\\ndata: {"abc": 123}\\n\\n'
    """
    if type(data) is dict:
      data = json.dumps(data)
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg
