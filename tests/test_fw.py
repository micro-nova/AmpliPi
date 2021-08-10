#!/usr/bin/env python3

"""
Test the amplipi preamp firmware
This file is expected to be run using pytest, ie. pytest tests/test_fw.py
This file is expected to be run on the controller board Pi, connected to a preamp board.
"""

import pytest
import subprocess
import tempfile

# Use the internal amplipi library
from context import amplipi

NUM_EXPANDERS = 0

# Preamp firmware .bin file path, relative to amplipi's directory.
BIN_FILE = 'fw/preamp/build/preamp_bd.bin'

def build_preamp_fw(amplipi_dir) -> str:
  """ Build the firmware from source """
  # TODO: Support debug build and setting version
  #mkdir = subprocess.run(['mkdir fw/preamp/build'], check=True)
  #if mkdir.returncode != 0:
  #  return False
  #flash = subprocess.run([f'fw/'])

  exists = subprocess.run([f'ls {amplipi_dir}/{BIN_FILE}'], shell=True, check=False)
  if exists.returncode == 0:
    return BIN_FILE
  return None

@pytest.mark.dependency()
def test_flash_master(request):
  amplipi_dir = f'{request.fspath.dirname}/..'
  bin_path = build_preamp_fw(amplipi_dir)
  assert bin_path is not None

  preamps = amplipi.hw.Preamps()
  preamps.flash(bin_path)
  ver = preamps[0].read_version()
  print(ver)
  assert ver[0] == 1


@pytest.mark.dependency(depends=['test_flash_master'])
def test_read_i2c():
  preamps = amplipi.hw.Preamps()
  assert preamps[NUM_EXPANDERS] is not None

#@pytest.mark.dependency(depends=['test_read_i2c'])
#def test_multi_baud():
#  assert False
