#!/usr/bin/env python3

# profiling
import cProfile
import pstats
import io
from pstats import SortKey

# directories
import tempfile
import os

import amplipi.ctrl
import amplipi.rt
import amplipi.models

def use_tmpdir():
  # lets run these tests in a temporary directory so they dont mess with other tests config files
  test_dir = tempfile.mkdtemp()
  os.chdir(test_dir)
  assert test_dir == os.getcwd()

use_tmpdir()
ap = amplipi.ctrl.Api()
g = ap.create_group(amplipi.models.Group(name='all', zones=[0,1,2,3,4,5]))

def play_with_volumes():
  """ Test a bare volume adjustment to evaluate best case performance """
  for _ in range(100):
    ap.set_group(g['id'], amplipi.models.GroupUpdate(mute=False, vol_delta=20))
    ap.set_group(g['id'], amplipi.models.GroupUpdate(mute=False, vol_delta=30))

pr = cProfile.Profile()
pr.enable()
play_with_volumes()
pr.disable()
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print(s.getvalue())

#   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#        1    0.003    0.003   24.361   24.361 /home/pi/amplipi-dev/amplipi/profile_volumes.py:27(play_with_volumes)
# 1400/200    0.036    0.000   24.357    0.122 /home/pi/amplipi-dev/amplipi/utils.py:131(inner)
#      200    0.020    0.000   22.824    0.114 /home/pi/amplipi-dev/amplipi/ctrl.py:440(set_group)
#     1200    0.088    0.000   13.364    0.011 /home/pi/amplipi-dev/amplipi/ctrl.py:357(set_zone)
#     1207    0.030    0.000   12.735    0.011 /home/pi/amplipi-dev/amplipi/rt.py:105(write_byte_data)
#     1200    0.023    0.000   12.682    0.011 /home/pi/amplipi-dev/amplipi/rt.py:329(update_zone_vol)
#     1208   12.468    0.010   12.468    0.010 {built-in method time.sleep}
#     1400    0.458    0.000   10.898    0.008 /home/pi/amplipi-dev/amplipi/ctrl.py:160(save)
#     1400    1.904    0.001    9.760    0.007 /usr/lib/python3.7/json/__init__.py:120(dump)
#   914200    1.038    0.000    6.731    0.000 /usr/lib/python3.7/json/encoder.py:413(_iterencode)
#2116800/914200    3.207    0.000    5.684    0.000 /usr/lib/python3.7/json/encoder.py:333(_iterencode_dict)
#1087800/889000    1.721    0.000    4.563    0.000 /usr/lib/python3.7/json/encoder.py:277(_iterencode_list)
#   912800    1.026    0.000    1.026    0.000 {method 'write' of '_io.TextIOWrapper' objects}
#     1207    0.031    0.000    0.538    0.000 /home/pi/amplipi-dev/venv/lib/python3.7/site-packages/smbus2/smbus2.py:436(write_byte_data)
#   739200    0.506    0.000    0.506    0.000 {built-in method builtins.isinstance}
#     1207    0.449    0.000    0.449    0.000 {built-in method fcntl.ioctl}
#        6    0.000    0.000    0.378    0.063 /home/pi/amplipi-dev/amplipi/rt.py:262(update_zone_mutes)
#     1400    0.286    0.000    0.326    0.000 {built-in method io.open}
#     1400    0.128    0.000    0.213    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:425(_update_groups)
#     1400    0.188    0.000    0.188    0.000 {built-in method posix.remove}
#   226800    0.188    0.000    0.188    0.000 {built-in method _json.encode_basestring_ascii}
#     1400    0.058    0.000    0.088    0.000 /usr/lib/python3.7/json/encoder.py:204(iterencode)
#     2800    0.013    0.000    0.085    0.000 /usr/lib/python3.7/genericpath.py:16(exists)
#     1400    0.079    0.000    0.079    0.000 {built-in method posix.rename}
#     2800    0.072    0.000    0.072    0.000 {built-in method posix.stat}
#     1207    0.053    0.000    0.053    0.000 /home/pi/amplipi-dev/venv/lib/python3.7/site-packages/smbus2/smbus2.py:142(create)
#    63000    0.043    0.000    0.043    0.000 {built-in method builtins.id}
#     1400    0.014    0.000    0.034    0.000 /usr/lib/python3.7/_bootlocale.py:33(getpreferredencoding)
#    46200    0.032    0.000    0.032    0.000 {method 'items' of 'dict' objects}
#     1400    0.026    0.000    0.030    0.000 /usr/lib/python3.7/json/encoder.py:259(_make_iterencode)
#     5600    0.024    0.000    0.024    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:428(<listcomp>)
#     1400    0.020    0.000    0.020    0.000 {built-in method _locale.nl_langinfo}
#     1200    0.005    0.000    0.015    0.000 /home/pi/amplipi-dev/amplipi/utils.py:60(clamp)
#     5600    0.014    0.000    0.014    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:431(<listcomp>)
#     5600    0.014    0.000    0.014    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:429(<listcomp>)
#     5600    0.013    0.000    0.013    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:430(<listcomp>)
#     5600    0.013    0.000    0.013    0.000 {method 'sort' of 'list' objects}
#     2400    0.011    0.000    0.011    0.000 /home/pi/amplipi-dev/amplipi/utils.py:38(parse_int)
#     1400    0.011    0.000    0.011    0.000 /usr/lib/python3.7/json/encoder.py:104(__init__)
#     6600    0.008    0.000    0.008    0.000 /home/pi/amplipi-dev/amplipi/utils.py:50(updated_val)
#     1200    0.007    0.000    0.007    0.000 {built-in method builtins.min}
#      200    0.003    0.000    0.007    0.000 /home/pi/amplipi-dev/amplipi/utils.py:57(find)
#     1400    0.006    0.000    0.006    0.000 /usr/lib/python3.7/codecs.py:186(__init__)
#     1207    0.005    0.000    0.005    0.000 /home/pi/amplipi-dev/venv/lib/python3.7/site-packages/smbus2/smbus2.py:340(_set_address)
#     5618    0.004    0.000    0.004    0.000 {built-in method builtins.len}
#     5600    0.004    0.000    0.004    0.000 {method 'pop' of 'set' objects}
#      200    0.002    0.000    0.003    0.000 {built-in method builtins.next}
#     1200    0.002    0.000    0.002    0.000 {built-in method builtins.max}
#      200    0.002    0.000    0.002    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:478(<listcomp>)
#     1200    0.001    0.000    0.001    0.000 {built-in method builtins.abs}
#      800    0.001    0.000    0.001    0.000 /home/pi/amplipi-dev/amplipi/utils.py:58(<lambda>)
#        6    0.000    0.000    0.000    0.000 /home/pi/amplipi-dev/amplipi/ctrl.py:403(<listcomp>)
#        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
#        1    0.000    0.000    0.000    0.000 {method 'keys' of 'dict' objects}
