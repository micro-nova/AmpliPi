#!/usr/bin/python3
# this file is expected to be run using pytest, ie. pytest python/tests/test_ethaudio_rpi.py

from .test_ethaudio_mock import check_all_tsts
import ethaudio

def test_rpi():
  check_all_tsts(ethaudio.Api(ethaudio.api.RpiRt()))
