#!/usr/bin/python3

# AmpliPi Home Audio
# Copyright (C) 2022-2024 MicroNova LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""AmpliPi zeroconf service advertisement"""

import logging
from multiprocessing.synchronize import Event as SyncEvent
from socket import gethostname, inet_aton
import sys
from time import sleep
from typing import Callable, Optional, Tuple, Union

import netifaces as ni
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from amplipi import utils

# TEST: use logging in this module
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)  # TODO: allow changing log level higher up (as AmpliPi config?)
sh = logging.StreamHandler(sys.stderr)
sh.setFormatter(logging.Formatter('%(name)s: %(levelname)s - %(message)s'))
log.addHandler(sh)


def get_ip_info(iface: str = 'eth0') -> Tuple[Optional[str], Optional[str]]:
  """ Get the IP address of interface @iface """
  try:
    info = ni.ifaddresses(iface)
    return info[ni.AF_INET][0].get('addr'), info[ni.AF_LINK][0].get('addr')
  except:
    return None, None


def advertise_service(port, event: SyncEvent):
  """ Advertise the AmpliPi api via zeroconf, can be verified with 'avahi-browse -ar'
      Expected to be run as a separate process, eg:

          event = multiprocessing.Event()
          ad = Process(target=amplipi.app.advertise_service, args=(5000, event))
          ad.start()
          ...
          event.set()
          ad.join()
      NOTE: multiprocessing.Event() is a function that returns a multiprocessing.synchronize.Event type
      Here the type is aliased to SyncEvent
  """
  def ok():
    """ Was a stop requested by the parent process? """
    return not event.is_set()

  while ok():
    try:
      _advertise_service(port, ok)
    except Exception as exc:
      if 'change registration' not in str(exc):
        log.error(f'Failed to advertise AmpliPi service, retrying in 30s: {exc}')
        # delay for a bit after a failure
        delay_ct = 300
        while ok() and delay_ct > 0:
          sleep(0.1)
          delay_ct -= 1


def _find_best_iface(ok: Callable) -> Union[Tuple[str, str, str], Tuple[None, None, None]]:
  """ Try to find the best interface to advertise on
      Retries several times in case DHCP resolution is delayed
  """
  ip_addr, mac_addr = None, None

  # attempt to find the interface used as the default gateway
  retry_count = 5
  while ok() and retry_count > 0:
    try:
      iface = ni.gateways()['default'][ni.AF_INET][1]
      ip_addr, mac_addr = get_ip_info(iface)
      if ip_addr and mac_addr:
        return ip_addr, mac_addr, iface
    except:
      pass
    sleep(2)  # wait a bit in case this was started before DHCP was started
    retry_count -= 1

  # fallback to any normal interface that is available
  # this also covers the case where a link-local connection is established
  def is_normal(iface: str):
    """ Check if an interface is wireless or wired, excluding virtual and local interfaces"""
    return iface.startswith('w') or iface.startswith('e')
  ifaces = filter(is_normal, ni.interfaces())
  for iface in ifaces:
    ip_addr, mac_addr = get_ip_info(iface)
    if ip_addr and mac_addr:
      return ip_addr, mac_addr, iface
  log.warning(f'Unable to register service on one of {ifaces}, \
          they all are either not available or have no IP address.')
  return None, None, None


def _advertise_service(port: int, ok: Callable) -> None:
  """ Underlying advertisement, can throw Exceptions when network is not connected """

  hostname = f'{gethostname()}.local'
  url = f'http://{hostname}'
  log.debug("AmpliPi zeroconf - attempting to find best interface")
  ip_addr, mac_addr, good_iface = _find_best_iface(ok)

  if not ip_addr:
    # Fallback to any hosted ip on this device.
    # This will be resolved to an ip address by the advertisement
    ip_addr = '0.0.0.0'
    log.warning(f'No valid network interface found, advertising on {ip_addr}.')
  else:
    log.debug(f'Found IP address {ip_addr} on interface {good_iface}')
  if port != 80:
    url += f':{port}'

  info = ServiceInfo(
    # use a custom type to easily support multiple amplipi device enumeration
    '_amplipi._tcp.local.',
    # the MAC Address is appended to distinguish multiple AmpliPi units
    f'amplipi-{str(mac_addr).lower()}._amplipi._tcp.local.',
    addresses=[inet_aton(ip_addr)],
    port=port,
    properties={
      # standard info
      'path': '/api/',
      # extra info - for interfacing
      'name': 'AmpliPi',
      'vendor': 'MicroNova',
      'version': utils.detect_version(),
      # extra info - for user
      'web_app': url,
      'documentation': f'{url}/doc'
    },
    server=f'{hostname}.',  # Trailing '.' is required by the SRV_record specification
  )

  if not ok():
    log.info("Advertisement cancelled")
    return

  log.info(f'Registering service: {info}')
  # right now the AmpliPi webserver is ipv4 only
  zeroconf = Zeroconf(ip_version=IPVersion.V4Only, interfaces=[ip_addr])
  zeroconf.register_service(info)
  log.info('Finished registering service')
  try:
    # poll for changes to the IP address
    # this attempts to handle events like router/switch resets
    while ok():
      delay_ct = 100
      while ok() and delay_ct > 0:
        sleep(0.1)
        delay_ct -= 1
      if ok():
        new_ip_addr, _, new_iface = _find_best_iface(ok)
        if new_ip_addr != ip_addr:
          log.info(f'IP address changed from {ip_addr} ({good_iface}) to {new_ip_addr} ({new_iface})')
          log.info('Registration change needed')
          raise Exception("change registration")
  finally:
    log.info('Unregistering service')
    zeroconf.unregister_service(info)
    zeroconf.close()
