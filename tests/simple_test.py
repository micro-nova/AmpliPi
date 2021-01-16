#!/usr/bin/python3

import pprint
import ethaudio.api
ea = ethaudio.Api(ethaudio.api.RpiRt(), '../config/jasons_house.json')
pprint.pprint(ea.get_state())
