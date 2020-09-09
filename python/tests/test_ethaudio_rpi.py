#!/usr/bin/python3

from .test_ethaudio_mock import check_all_tsts
import ethaudio

def test_rpi():
  check_all_tsts(ethaudio.Api(ethaudio.api.RpiRt()))

if __name__ == '__main__':
  test_rpi()
