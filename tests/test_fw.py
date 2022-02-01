#!/usr/bin/env python3

"""
Test the amplipi preamp firmware
This file is expected to be run using pytest, ie. pytest tests/test_fw.py
This file is expected to be run on the controller board Pi, connected to a preamp board.
"""

# Standard imports
import subprocess

import pytest
#import tempfile

# Use the internal amplipi library
from context import amplipi

NUM_EXPANDERS = 0

# Preamp firmware .bin file path, relative to amplipi's directory.
BIN_FILE = 'fw/preamp/build/preamp_bd.bin'

# The 'request' fixture contains info of the requesting test function.
@pytest.fixture
def fw_path(request) -> str:
  return f'{request.fspath.dirname}/../fw/preamp'

@pytest.fixture
def fw_bin_path(fw_path) -> str:
  return f'{fw_path}/build/preamp_bd.bin'

@pytest.mark.dependency()
def test_fw_build(fw_path):
  """ Build the firmware from source """
  # TODO: Build in a temp directory

  # Configure with CMake
  config_result = subprocess.run([f'cmake -B {fw_path}/build'], cwd=fw_path,
                                 shell=True, check=False)
  assert config_result.returncode == 0

  # Clean an previous build results
  clean_result = subprocess.run([f'cmake --build {fw_path}/build --target clean'],
                                cwd=fw_path, shell=True, check=False)
  assert clean_result.returncode == 0

  # Build the firmware
  build_result = subprocess.run([f'cmake --build {fw_path}/build -j4'],
                                cwd=fw_path, shell=True, check=False)
  assert build_result.returncode == 0

# Only run the following tests on AmpliPi
if not amplipi.utils.is_amplipi():
  pytest.skip("Not running on AmpliPi hardware, skipping firmware tests", allow_module_level = True)

@pytest.mark.dependency(depends=['test_fw_build'])
def test_flash_master(fw_bin_path):
  preamps = amplipi.hw.Preamps()
  preamps.flash(fw_bin_path, num_units=1)
  ver = preamps[0].read_version()
  print(ver)
  assert ver[0] == 1

@pytest.mark.dependency(depends=['test_flash_master'])
def test_set_address():
  preamps = amplipi.hw.Preamps()
  for i in range(10):
    preamps._reset_master(bootloader = False)
    if not preamps.send_i2c_address():
      pytest.fail(f'Failed resetting then setting address after {i} tries.')
  for i in range(10):
    if not preamps.send_i2c_address():
      pytest.fail(f'Failed setting address after {i} tries.')
    #ver = preamps[0].read_version()

# TODO: Fully exercise firmware interfaces

# @pytest.mark.dependency(depends=['test_flash_master'])
# def test_read_i2c():
#   preamps = amplipi.hw.Preamps()
#   assert preamps[NUM_EXPANDERS] is not None

#@pytest.mark.dependency(depends=['test_read_i2c'])
#def test_multi_baud():
#  assert False
