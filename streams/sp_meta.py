#!/usr/bin/python3
import sys
import time
# args validation
import argparse
import os

parser = argparse.ArgumentParser(description="shairport metadata interpreter")
parser.add_argument('sp_config_dir', description='directory used for shairport song info generation')
args = parser.parse_args()

# Check if the folder is valid and writeable
if not os.path.exists(args.sp_config_dir) or not os.access(args.sp_config_dir, os.W_OK):
  print('Error: unable to access: {}'.format(args.sp_config_dir))

# trim trailing /
if args.sp_config_dir[-1] == '/':
  args.sp_config_dir = args.sp_config_dir[:-1]

cs_loc = '{}/currentSong'.format(args.sp_config_dir)
si_loc = '{}/sourceInfo'.format(args.sp_config_dir)
p_status = ''

def read_field():
    line = sys.stdin.readline()
    line = line.strip(' \n')
    if line[-6:] == 'bytes.': # Works with Mike Brady version of shairport-sync-metadata-reader
        line = '"Picture: ' + line + '".'
    if line:
        while line[-2:] != '".':
            line2 = sys.stdin.readline()
            line2 = line2.strip(' \n')
            line = line + '\n' + line2
        data = line.split(': ')
        if len(data) > 2:
            for i in range(2, len(data), 1):
                data[1] += ': '
                data[1] += data[i]
        return data[0], data[1]
    else:
        return None, None

def info():
    u = {}
    v = {}
    field = ''
    while field != '"ssnc" "mden"':
        field, data = read_field()
        # print(field, ':', data)
        if field:
            u[field] = data
    v = u['Artist'] + ',,,' + u['Title'] + ',,,' + u['Album Name']
    return v

def s_info(inp):
    u = {}
    v = {}
    field = ''
    u['"ssnc" "snua"'] = inp
    while field != '"ssnc" "pbeg"':
        field, data = read_field()
        # print(field, ':', data)
        if field:
            u[field] = data
    v = u['"ssnc" "snua"'] + ',,,' + u['"ssnc" "acre"'] + ',,,' + u['"ssnc" "daid"'] + ',,,' + u["Client's IP"]
    return v

f = open(cs_loc, 'w')
f.write("")
f.close()
f = open(si_loc, 'w')
f.write("")
f.close()
while True:
    field, data = read_field()
    # print(field, ':', data)
    p_status = ',,,PAUSED=False'
    if field == '"ssnc" "mdst"':
        q = info() + p_status
        print(q)
        f = open(cs_loc, 'w')
        f.write(str(q))
        f.close()
    elif field == '"ssnc" "snua"':
        q = s_info(data)
        print(q)
        f = open(si_loc, 'w')
        f.write(str(q))
        f.close()
    elif field == '"ssnc" "pend"':
        f = open(cs_loc, 'r')
        data = f.read()
        data = data.replace('=False', '=True')
        f.close()
        f = open(cs_loc, 'w')
        f.write(data)
        f.close()
    elif field == 'Image length': # 'Image length' and 'Image name' are new outputs from the MicroNova fork of shairport-sync-metadata-reader: https://github.com/micronova-jb/shairport-sync-metadata-reader
        lin = ',,,' + data
        f = open(cs_loc, 'a')
        f.write(lin)
        f.close()
    elif field == 'Image name':
        pic = ',,,' + data
        f = open(cs_loc, 'a')
        f.write(pic)
        f.close()
    elif field == '"End of file"':
        break
