import requests
import time
from typing import Optional
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_radio_servers():
  class ServerDataPackage(BaseModel):
    url: str
    latency: Optional[float]

  def test_server_latency(server_url, timeout=15, reps=5) -> Optional[float]:
    """Measure latency of a single server by sending GET requests and averaging the elapsed time."""
    try:
      if not server_url.startswith("http"):
        server_url = "http://" + server_url

      results = []
      for _ in range(reps):
        start = time.perf_counter()
        response = requests.get(server_url, timeout=timeout, stream=True)
        elapsed = time.perf_counter() - start
        response.close()
        results.append(elapsed)

      return sum(results) / len(results)

    except requests.RequestException as e:
      print(f"Error contacting {server_url}: {e}")
      return None

  r = requests.get("https://all.api.radio-browser.info/json/servers")
  json = r.json()

  # Example response used for testing
  # json = [
  #     {'ip': '2a01:4f9:c012:3620::1', 'name': 'fi1.api.radio-browser.info'},
  #     {'ip': '2a01:4f8:c2c:f004::1', 'name': 'de2.api.radio-browser.info'},
  #     {'ip': '2a0a:4cc0:c0:27c1::1', 'name': 'de1.api.radio-browser.info'},
  #     {'ip': '37.27.202.89', 'name': 'fi1.api.radio-browser.info'},
  #     {'ip': '152.53.85.3', 'name': 'de1.api.radio-browser.info'},
  #     {'ip': '162.55.180.156', 'name': 'de2.api.radio-browser.info'},
  # ]

  seen = set()
  servers: list[ServerDataPackage] = []
  for entry in json:
    if entry["name"] not in seen:
      seen.add(entry["name"])
      servers.append({'url': entry["name"]})

  with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_server = {
        executor.submit(test_server_latency, server['url']): server
        for server in servers
    }
    for future in as_completed(future_to_server):
      server = future_to_server[future]
      server['latency'] = future.result()

  servers.sort(key=lambda s: s['latency'])
  return [s['url'] for s in servers if s['latency'] is not None]


get_radio_servers()


# models.py line 1027: internetradio_servers: List[str] = Field(default=[], description='A list of internet radio servers, ordered by ping latency (fastest to slowest)')
