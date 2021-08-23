# AmpliPi Tests
This directory includes various tests for AmpliPi.

## pytest
Any python file beginning with test_* will be run with pytest

## Metadata
Metadata is tested with `meta_test.bash`

## Hardware
The Preamp firmware interface and controls are tested or read with `preamp.py`.
The peak detect hardware is directly read by the Raspberry Pi,
and can be tested with `peak_detect.py`.
