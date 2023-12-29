from time import sleep
from multiprocessing import Process, Event
import netifaces as ni
from zeroconf import Zeroconf, ServiceStateChange, ServiceBrowser, IPVersion
from context import amplipi


def test_zeroconf():
  """ Unit test for zeroconf advertisement """
  FAKE_PORT = 9898

  # get network interface and MAC address that the service is expected to be advertised on
  iface = ni.gateways()['default'][ni.AF_INET][1]
  try:
    mac_addr = ni.ifaddresses(iface)[ni.AF_LINK][0]['addr']
  except:
    mac_addr = 'none'

  AMPLIPI_ZC_NAME = f'amplipi-{mac_addr}._amplipi._tcp.local.'
  print(f'Expecting that "{AMPLIPI_ZC_NAME}" is advertised to interface {iface}')

  services_advertised = {}

  def on_service_state_change(zeroconf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange):
    if state_change is ServiceStateChange.Added:
      info = zeroconf.get_service_info(service_type, name)
      if info and info.port != 80:  # ignore the actual amplipi service on your network
        services_advertised[name] = info

  # advertise amplipi-api service (start this before the listener to verify it can be found after advertisement)
  event = Event()
  zc_reg = Process(target=amplipi.zeroconf.advertise_service, args=(FAKE_PORT, event))
  zc_reg.start()
  sleep(4)  # wait for a bit to make sure the service is started

  # start listener that adds available services
  zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
  services = ["_amplipi._tcp.local."]
  _ = ServiceBrowser(zeroconf, services, handlers=[on_service_state_change])

  # wait enough time for a response from the service
  sleep(2)

  # stop the advertiser
  event.set()
  zc_reg.join()

  # stop the listener
  zeroconf.close()

  # check advertisements
  assert AMPLIPI_ZC_NAME in services_advertised
  assert services_advertised[AMPLIPI_ZC_NAME].port == FAKE_PORT
