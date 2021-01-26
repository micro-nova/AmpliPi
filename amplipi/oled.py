
# To retrieve system info
import netifaces as ni    # network interfaces
import psutil             # CPU, RAM, etc.

# For uptime info
import uptime
from datetime import timedelta

# For display thread
import threading
import time
import queue
from enum import Enum

# Stuff for OLED screen control
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.oled.device import ssd1309

# Python Image Library
from PIL import ImageFont

# +--------------------------------------------------+
# �               AmpliPI OLED class                 �
# �    Provides OLED display for AmpliPi system      �
# +--------------------------------------------------+
class AmpliPi_OLED():

  # ================
  #  initialization
  # ================
  def __init__(self):
    print("Initializing AmpliPi_OLED display")

    # Connection for AmpliPi controller board -> OLED board
    #
    # Pi GPIO #   AmpliPi sch net   OLED board
    # -------------------------------------
    #   43        SPI2_CE0_N        CS
    #   39        GPIO39            DC
    #   40        SPI2_MISO         RST
    #   41        SPI2_MOSI         SDA
    #   42        SPI2_SCLK         SCL

    # For SPI2 CS0, we would want port=2, device=0
    self.device = ssd1309(spi(port=2, device=0, gpio_DC=39, gpio_RST=40))

    # thread to periodically update display with stats
    gather_stats_thread = threading.Thread(target=self.__gather_stats, daemon=True)
    gather_stats_thread.start()

    # thread to draw to screen, updated via queue
    display_update_thread = threading.Thread(target=self.__display_update, daemon=True)
    display_update_thread.start()

  # =======================
  #  set volume bar graphs
  # =======================

  # set volumes based on list
  # list should contain exactly 6 integers of volumes (0-100)
  def set_volumes(self, volume_list):
    # validate that list contains 6 items
    if(len(volume_list) == 6):
      # append display update type and put in
      volume_list.insert(0, self.DisplayUpdateType.VolumeBars)
      self.q.put(volume_list)

  # ================
  #  display update
  # ================

  # types of display updates
  class DisplayUpdateType(Enum):
    SystemStats = 1  # four strings to be drawn on top part of screen
    VolumeBars  = 2  # six integers

  # queue of display update items
  q = queue.Queue()

  # update the display (runs on thread)
  def __display_update(self):

    # get fonts
    item_font  = ImageFont.truetype("AndaleMono.ttf", 10)
    tiny_font  = ImageFont.truetype("AndaleMono.ttf", 8)

    # variables to store screen status
    system_stats_strings = ["", "", "", ""]
    volume_bars_level    = [0, 50, 100, 20, 40, 60]

    # volume bars position
    #
    #     col A         col B
    #
    # 1 ######---- 4 ###------- <- row 1
    # 2 ####------ 5 #--------- <- row 2
    # 3 ########-- 6 #--------- <- row 3

    # volume bar X start
    vbar_x_start_col_a = 8 # X start position of volume bar for column A (bars 1, 2, 3)
    vbar_x_start_col_b = 77 # X start position of volume bar for column B (bars 4, 5, 6)

    # volume bar Y start
    vbar_y_start_row_1 = 45 # Y start position of volume bar for row 1 (bars 1, 4)
    vbar_y_start_row_2 = 53 # Y start position of volume bar for row 2 (bars 2, 5)
    vbar_y_start_row_3 = 61 # Y start position of volume bar for row 3 (bars 3, 6)

    # volume bar start coordinates (X, Y)
    vbar_start_coords = [(vbar_x_start_col_a, vbar_y_start_row_1),
                         (vbar_x_start_col_a, vbar_y_start_row_2),
                         (vbar_x_start_col_a, vbar_y_start_row_3),
                         (vbar_x_start_col_b, vbar_y_start_row_1),
                         (vbar_x_start_col_b, vbar_y_start_row_2),
                         (vbar_x_start_col_b, vbar_y_start_row_3)]

    # run forever
    while True:

      # get item from queue (BLOCKS HERE until an item is available)
      item  = self.q.get()

      # ----------- system stats update -----------
      if(item[0] == self.DisplayUpdateType.SystemStats):
        # queue item contains four strings to be written to display
        system_stats_strings = [item[1], item[2], item[3], item[4]]

      # ----------- volume bars update -----------
      if(item[0] == self.DisplayUpdateType.VolumeBars):
        # queue item contains six integers 0-100 representing volume bar status
        volume_bars_level = [item[1], item[2], item[3], item[4], item[5], item[6]]

      # ----------- perform display update -----------
      # (this is the single place where the screen is actually drawn to)

      with canvas(self.device) as draw:
        # system status strings
        draw.text((0, 0),  system_stats_strings[0], fill="white", font=item_font)
        draw.text((0, 10), system_stats_strings[1], fill="white", font=item_font)
        draw.text((0, 20), system_stats_strings[2], fill="white", font=item_font)
        draw.text((0, 30), system_stats_strings[3], fill="white", font=item_font)
        # numbers for volume indicators
        draw.text((0, 42),  "1", fill="white", font=tiny_font)
        draw.text((0, 50),  "2", fill="white", font=tiny_font)
        draw.text((0, 58),  "3", fill="white", font=tiny_font)
        draw.text((69, 42), "4", fill="white", font=tiny_font)
        draw.text((69, 50), "5", fill="white", font=tiny_font)
        draw.text((69, 58), "6", fill="white", font=tiny_font)

        # volume bars: center line
        for i in range(6):
          # start of bar
          vbar_start = vbar_start_coords[i]
          # end of bar is start + 50
          vbar_end   = (vbar_start_coords[i][0]+50, vbar_start_coords[i][1])
          # draw center line
          draw.line((vbar_start, vbar_end), fill="white") # volume indicator 1

        # volume bars: rectangle for volume % indication
        for i in range(6):
          # bar length is 0-50 pixels
          if(volume_bars_level[i] >= 100):
            # saturate high
            bar_len = int(50)
          elif(volume_bars_level[i] <= 0):
            # saturate low
            bar_len = int(0)
          else:
            # scale to 50 pixels
            bar_len = int(volume_bars_level[i]) // 2
          # start (upper left) coordinate
          bar_rectangle_start = (vbar_start_coords[i][0], vbar_start_coords[i][1]-2)
          # stop (lower right) coordinate
          bar_rectangle_stop  = (vbar_start_coords[i][0]+bar_len, vbar_start_coords[i][1]+2)
          # draw box
          draw.rectangle((bar_rectangle_start, bar_rectangle_stop), fill="white")

      # done with this item
      self.q.task_done();

  # =====================
  #  gather system stats
  # =====================
  def __gather_stats(self):

    # run forever
    while(True):

      # get IP address
      # ni.ifaddresses('eth0')
      try:
        # try to get IP address
        ip_address = "IP:   %s" % ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
      except:
        # if this failed, then eth0 must be disconnected!
        ip_address = "IP:   Disconnected"

      # get CPU utilization % and temperature
      cpu_temp_float = psutil.sensors_temperatures(fahrenheit=False)['cpu-thermal'][0].current
      cpu_utilization = "CPU:  %.1f%%  %.1f\xb0C" % (psutil.cpu_percent(), cpu_temp_float)

      # get RAM
      ram_total_mbytes = int(psutil.virtual_memory().total / (1024*1024))
      ram_used_mbytes  = int(psutil.virtual_memory().used / (1024*1024))
      ram_usage = "RAM:  %i / %i MB" % (ram_used_mbytes, ram_total_mbytes)

      # uptime
      uptime_seconds = uptime.uptime()
      # days
      uptime_days = uptime_seconds // (24 * 60 * 60)
      uptime_seconds = uptime_seconds % (24 * 60 * 60)
      # hours
      uptime_hours = uptime_seconds // (60 * 60)
      uptime_seconds = uptime_seconds % (60 * 60)
      # minutes
      uptime_minutes = uptime_seconds // (60)
      uptime_seconds = uptime_seconds % (60)
      # uptime string
      uptime_string = "UP:   %id %ih %im" % (uptime_days, uptime_hours, uptime_minutes)

      # disk (NOT USED)
      disk_total = psutil.disk_usage('/').total // (1024*1024)
      disk_used  = psutil.disk_usage('/').used // (1024*1024)
      disk_free  = psutil.disk_usage('/').free // (1024*1024)
      disk_string = "DISK: %i / %i MB" % (disk_used, disk_total)

      # send strings to display update queue
      self.q.put([self.DisplayUpdateType.SystemStats, ip_address, cpu_utilization, ram_usage, uptime_string])
      # wait 1 second before gathering stats again
      time.sleep(1)

