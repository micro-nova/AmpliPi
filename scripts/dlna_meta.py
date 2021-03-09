#!/usr/bin/python3
import sys
import time
import re

# Check out https://github.com/hzeller/upnp-display/blob/master/controller-state.cc
# This controller state allows subscribing to song info from a UPnP source

args = sys.argv[1:]
print('Input Arguments: {}'.format(args[0]))
try:
    src = int(args[0])
    loc = '/home/pi/config/dlna/{}/'.format(src)
except:
    print('Error: Invalid source choice. Sources range from 0 to 3. Please try again.')
    sys.exit('Failure.')
print('Targeting {}'.format(loc))
cs_loc = loc + 'currentSong'
TS_prev = ''
TS_curr = 'TransportState: PLAYING'
cs_conf = {}

def read_field():
    line = sys.stdin.readline()
    line = line.strip('\n')
    if line[0:4] == "INFO":
        s1 = line.split('] ')
        return s1[1]
    else:
        return None

def meta_parser(CTMD):
    s = CTMD.split('>')
    ind = 0
    val = {}
    u = {}
    r1 = '</upnp:'
    r2 = '</dc:'

    for i in range(len(s)):
        p = s[i]
        if p[0:4] == '<dc:' or p[0:6] == '<upnp:':
            val[ind] = s[i+1]
            ind += 1
    for l in range(len(val)):
        if re.search(r1, val[l]):
            t, y = val[l].split(r1)
            u[y] = t
        elif re.search(r2, val[l]):
            t, y = val[l].split(r2)
            u[y] = t
    print(u)
    return u

f = open(cs_loc, 'w')
f.write("")
f.close()

while True:
    field = read_field()
    # print(field +'\n')
    if re.search('TransportState', str(field)):
        TS_prev = TS_curr
        TS_curr = field
        form = TS_curr.split(': ')
        cs_conf[form[0]] = form[1]
        f = open(cs_loc, 'w')
        f.write(str(cs_conf)) # Do we need str() here for writing cs_conf?
        f.close()
    elif re.search('CurrentTrackMetaData', str(field)):
        cs_conf = meta_parser(field)
        form = TS_curr.split(': ')
        cs_conf[form[0]] = form[1]
        f = open(cs_loc, 'w')
        f.write(str(cs_conf))
        f.close()
