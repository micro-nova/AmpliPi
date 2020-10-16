#!/usr/bin/python3
# this file is expected to be run using pytest, ie. pytest python/tests/test_ethaudio_rpi.py
if __name__ == '__main__':
  from test_ethaudio_mock import check_all_tsts
else:
  from .test_ethaudio_mock import check_all_tsts
import ethaudio

def test_rpi():
  check_all_tsts(ethaudio.Api(ethaudio.api.RpiRt()))

if __name__ == '__main__':
  test_rpi()
