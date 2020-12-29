#!/usr/bin/python3
import sys
import time

args = sys.argv[1:]
print('Input Arguments: {}'.format(args[0]))
try:
    if args[0] == '0':
        loc = '/home/pi/config/srcs/0/currentSong'
    elif args[0] == '1':
        loc = '/home/pi/config/srcs/1/currentSong'
    elif args[0] == '2':
        loc = '/home/pi/config/srcs/2/currentSong'
    elif args[0] == '3':
        loc = '/home/pi/config/srcs/3/currentSong'
    else:
        print('Error: Invalid source choice. Sources range from 0 to 3. Please try again.')
        sys.exit('Failure.')
except:
    print('Error: Invalid source choice. Sources range from 0 to 3. Please try again.')
    sys.exit('Failure.')
print('Targeting {}'.format(loc))

def read_field():
    line = sys.stdin.readline()
    line = line.strip(' \n')
    if line[-6:] == 'bytes.':
        line = '"Picture: ' + line + '".'
    if line:
        while line[-2:] != '".':
            line2 = sys.stdin.readline()
            line2 = line2.strip(' \n')
            line = line + '\n' + line2
        data = line.split(': ')
        return data[0], data[1]
    else:
        return None, None

def info():
    u = {}
    v = {}
    field = ''
    while field != '"ssnc" "mden"':
        field, data = read_field()
        print(field, ':', data)
        if field:    
            u[field] = data
    # v['artist'] = u['Artist']
    # v['track'] = u['Title']
    # v['album'] = u['Album Name']
    v = u['Artist'] + ',,,' + u['Title'] + ',,,' + u['Album Name']
    return v

d = {}
f = open(loc, 'w')
f.write("")
f.close()
while True:
    field, data = read_field()
    print(field, ':', data)
    if field == '"ssnc" "mdst"':
        q = info()
        print(q)
        f = open(loc, 'w')
        f.write(str(q))
        f.close()
