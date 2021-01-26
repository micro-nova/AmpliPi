from oled import AmpliPi_OLED
import time

oled = AmpliPi_OLED()

i = 0

# demo
while(True):
  # increment
  i = i + 2
  # rollover
  if(i >= 100):
    i = 0
  # set volume bars
  oled.set_volumes([i,i,i,i,i,i])
  # sleep
  time.sleep(1)
