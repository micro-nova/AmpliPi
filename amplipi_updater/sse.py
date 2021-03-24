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
