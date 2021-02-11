#!/usr/bin/python3
import sys
import time

args = sys.argv[1:]
print('Input Arguments: {}'.format(args[0]))
try:
    src = int(args[0])
    loc = '/home/pi/config/srcs/{}/'.format(src)
except:
    print('Error: Invalid source choice. Sources range from 0 to 3. Please try again.')
    sys.exit('Failure.')
print('Targeting {}'.format(loc))
cs_loc = loc + 'currentSong'
si_loc = loc + 'sourceInfo'
p_status = ''

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
    elif field == 'Image length':
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
