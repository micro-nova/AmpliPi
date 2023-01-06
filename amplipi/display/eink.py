#!/usr/bin/env python3

import sys
import epd2in13_V3
from PIL import Image,ImageDraw,ImageFont

# Get fonts
#fontname = 'DejaVuSansMono'
fontname = 'DejaVuSansMono-Bold'
fontsize=20
try:
  font = ImageFont.truetype(fontname, fontsize)
except:
  print(f'Failed to load font {fontname}')
  sys.exit(3)

ascent, descent = font.getmetrics()
cw = font.getlength(" ")
ch = ascent + descent
print(f'Font height = {ch}, width = {cw}')

try:
  epd = epd2in13_V3.EPD()
  height = epd.width # rotated
  width = epd.height # rotated
  print(f'Screen height = {height}, width = {width}')
  epd.init()
  epd.Clear(0xFF)

  image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
  draw = ImageDraw.Draw(image)

  if fontsize == 14:
    # draw.text((0, 0*ch), 'Password\u21b4', font=font, fill=0)
    draw.text((0, 0*ch), 'hello world\u21b4', font=font, fill=0)
    draw.text((0, 1*ch), '0123456789 0123456789 012345678', font=font, fill=0)
    draw.text((0, 5*ch), 'IP\u21b4', font=font, fill=0)
    draw.text((width-18*cw, 5*ch), 'Internet access: \u2713', font=font, fill=0)
    draw.text((0, 6*ch), '192.168.128.200 amplipi.local', font=font, fill=0)
  else:
    # draw.text((0, 0*ch), '01234567890123456789', font=font, fill=0)
    draw.text((0, 0*ch), 'hello world', font=font, fill=0)
    draw.text((0, 1*ch), 'password_chars_>20', font=font, fill=0)
    draw.text((0, 2*ch), 'Password\u2197', font=font, fill=0)
    draw.text((width-8*cw, 2*ch), '\u2199IP/host', font=font, fill=0)
    draw.text((0, 3*ch), '192.168.128.200', font=font, fill=0)
    draw.text((0, 4*ch), 'amplipi.local', font=font, fill=0)

  image = image.rotate(180) # flip
  epd.display(epd.getbuffer(image))

  epd.sleep()
except IOError as e:
  print(f'Error: {e}')
except KeyboardInterrupt:
  print('CTRL+C')
  epd2in13_V3.epdconfig.module_exit()
