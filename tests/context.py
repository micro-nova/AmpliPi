# import amplipi as if it were installed
# autopep8: off
# pylint: disable=wrong-import-position
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import amplipi
import amplipi.app
import amplipi.auth
import amplipi.ctrl
import amplipi.defaults
import amplipi.hw
import amplipi.models
import amplipi.rt # TODO: remove
import amplipi.streams
import amplipi.utils
import amplipi.zeroconf
# autopep8: on
