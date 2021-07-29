#!/usr/bin/env python3
import smbus2


REG_ADDRS = {
  'VERSION_MAJOR'   : 0xFA,
  'VERSION_MINOR'   : 0xFB,
  'GIT_HASH_27_20'  : 0xFC,
  'GIT_HASH_19_12'  : 0xFD,
  'GIT_HASH_11_04'  : 0xFE,
  'GIT_HASH_STATUS' : 0xFF,
}

# Version
with smbus2.SMBus(1) as bus:
  major = bus.read_byte_data(0x08, REG_ADDRS['VERSION_MAJOR'])
  minor = bus.read_byte_data(0x08, REG_ADDRS['VERSION_MINOR'])
  git_hash = bus.read_byte_data(0x08, REG_ADDRS['GIT_HASH_27_20']) << 20
  git_hash |= (bus.read_byte_data(0x08, REG_ADDRS['GIT_HASH_19_12']) << 12)
  git_hash |= (bus.read_byte_data(0x08, REG_ADDRS['GIT_HASH_11_04']) << 4)
  git_hash4_stat = bus.read_byte_data(0x08, REG_ADDRS['GIT_HASH_STATUS'])
  git_hash |= (git_hash4_stat >> 4)
  dirty = (git_hash4_stat & 0x01) != 0

print(f'Version {major}.{minor}-{git_hash:07X}, {"dirty" if dirty else "clean"}')
