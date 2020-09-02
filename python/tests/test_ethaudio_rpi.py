#!/usr/bin/python3

import test_ethaudio_mock
import ethaudio

if __name__ == '__main__':
  test_ethaudio_mock.run_all_tests(ethaudio.Api(ethaudio.api.RpiRt()))
