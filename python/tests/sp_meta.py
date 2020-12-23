#!/usr/bin/python3
import sys
import time
# data2 = """"ssnc" "mdst": "3874307750".
# Album Name: "Now That's What I Call Music Vol 72".
# Artist: "Allen Lily".
# Comment: "sUPERSHARE.CO.UK".
# Composer: "".
# Genre: "VA".
# File kind: "MPEG audio file".
# Title: "The Fear".
# Persistent ID: "9ed463b45947fa92".
# Sort as: "Fear".
# "ssnc" "mden": "3874307750".
# """

# def info(data):
#     lines = data.split('.\n')
#     d = {}
#     for line in lines:
#         line = line.strip()
#         if line:
#             data = line.split(': ')
#             d[data[0]] = data[1]
#     u = {}
#     u['artist'] = d['Artist']
#     u['track'] = d['Title']
#     u['album'] = d['Album Name']
#     print(u)

# info(data2)

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

def info():
    data = ['','']
    u = {}
    v = {}
    while data[0] != '"ssnc" "mden"':
        line = sys.stdin.readline()
        line = line.strip()
        if line:
            data = line.split(': ')
            u[data[0]] = data[1]
    v['artist'] = u['Artist']
    v['track'] = u['Title']
    v['album'] = u['Album Name']
    return v

d = {}
data = ['','']
while True:
    line = sys.stdin.readline()
    line = line.strip()
    if line:
        data = line.split(': ')
        # print(data)
        if data[0] == '"ssnc" "mdst"':
            q = info()
            print(q)
            f = open(loc, 'w')
            f.write(str(q))
            f.close()

