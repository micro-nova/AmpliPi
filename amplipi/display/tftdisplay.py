import cProfile
import socket
import sys
import time
from typing import List, Tuple, Optional

# pylint: disable=wrong-import-position
import busio
import digitalio
# To retrieve system info
import netifaces as ni  # network interfaces
import psutil  # CPU, RAM, etc.
import requests
from PIL import Image, ImageDraw, ImageFont
# Display
from adafruit_rgb_display import ili9341
from loguru import logger as log

from amplipi import models
from amplipi.display.common import Color, Display, DefaultPass

# If this is run on anything other than a Raspberry Pi,
# it won't work. Just quit if not on a Pi.
try:
  import board
  import pwmio
  import RPi.GPIO as gpio
except (NotImplementedError, RuntimeError) as err:
  log.critical(err)
  log.critical('Only Raspberry Pi is currently supported')
  sys.exit(1)


class TFTDisplay(Display):
  # Number of screens to scroll through
  NUM_SCREENS = 1
  spi_baud = 16 * 10 ** 6

  # Start bit=1, A[2:0], 12-bit=0, differential=0, power down when done=00
  XPT2046_CMD_X = 0b11010000  # X=101
  XPT2046_CMD_Y = 0b10010000  # Y=001
  XPT2046_CMD_T0 = 0b10000100  # TEMP0=000, measured at 1x current
  XPT2046_CMD_T1 = 0b11110100  # TEMP1=111, measured at 91x current
  _cal = (300, 400, 3600, 3850)  # Top-left and bottom-right coordinates as raw ADC output
  _max_dist = 0.05 * ((_cal[3] - _cal[1]) ** 2 + (_cal[2] - _cal[0]) ** 2) ** 0.5

  def __init__(self, args):
    self.disp_cs = None
    self.disp_dc = None
    self.touch_cs = None
    self.spi = None
    self.pr = None
    self.image = None
    self.display = None
    self.ap_logo = None
    self.default_pass = None
    self.small_font = None
    self.font = None
    self.args = args
    self.profile = False
    self._touch_test_passed = False

    # Configuration for extra TFT pins:
    self.clk_pin = board.SCLK if args.test_board else board.SCLK_2
    self.mosi_pin = board.MOSI if args.test_board else board.MOSI_2
    self.miso_pin = board.MISO if args.test_board else board.MISO_2

    self.cs_pin = board.CE0 if args.test_board else board.D44
    self.dc_pin = board.D25 if args.test_board else board.D39
    self.led_pin = board.D18 if args.test_board else board.D12
    self.rst_pin = None
    self.t_cs_pin = board.D5 if args.test_board else board.D45
    self.t_irq_pin = board.D6 if args.test_board else board.D38

    self.led = None

    self._active_screen = 0
    self._sleep_timer = 0
    self.disp_start_time = 0

    self.width = 0
    self.height = 0

    self.API_URL = None
    self.API_URL_DEBUG = None

    self.draw = None

  def init(self) -> bool:
    # Determine the full URL to contact, and if no specific port was specified
    # then use port 5000 as a fallback in case the debug webserver is running.
    self.API_URL = 'http://' + self.args.url + '/api'
    self.API_URL_DEBUG = None
    if ':' not in self.args.url:
      self.API_URL_DEBUG = 'http://' + self.args.url + ':5000/api'

    self.default_pass = DefaultPass()

    # Pins
    self.disp_cs = digitalio.DigitalInOut(self.cs_pin)
    self.disp_dc = digitalio.DigitalInOut(self.dc_pin)
    self.touch_cs = digitalio.DigitalInOut(self.t_cs_pin)
    self.touch_cs.direction = digitalio.Direction.OUTPUT
    self.touch_cs.value = True

    # Setup SPI bus using hardware SPI:
    self.spi = busio.SPI(clock=self.clk_pin, MOSI=self.mosi_pin, MISO=self.miso_pin)

    # Create the ILI9341 display:
    self.display = ili9341.ILI9341(self.spi, cs=self.disp_cs, dc=self.disp_dc, rst=self.rst_pin, baudrate=self.spi_baud, rotation=270)

    # Set backlight brightness out of 65535
    # Turn off until first image is written to work around not having RST
    self.led = pwmio.PWMOut(self.led_pin, frequency=5000, duty_cycle=0)
    self.backlight(False)

    self.read_temp_raw()
    temp0, temp1 = self.read_temp_raw()
    if temp0 == 0 or temp1 == 0:
      # A touch screen doesn't seem to be present, so assume e-ink is present
      # release control over spi/pins
      try:
        self.spi.unlock()
      except ValueError:
        pass
      self.spi.deinit()
      self.led.deinit()
      self.disp_cs.deinit()
      self.disp_dc.deinit()
      self.touch_cs.deinit()
      return False

    # Get touch events
    gpio.setup(self.t_irq_pin.id, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.add_event_detect(self.t_irq_pin.id, gpio.FALLING, callback=lambda _: self.touch_callback())

    # Load image and convert to RGB
    mn_logo = Image.open('amplipi/display/imgs/micronova_320x240.png').convert('RGB')
    self.ap_logo = Image.open('amplipi/display/imgs/amplipi_320x126.png').convert('RGB')
    self.display.image(mn_logo)

    # Turn on display backlight now that an image is loaded
    # Anything duty cycle less than 100% causes flickering
    self.backlight(True)

    # Get fonts
    fontname = 'DejaVuSansMono'
    try:
      self.font = ImageFont.truetype(fontname, 14)
      self.small_font = ImageFont.truetype(fontname, 10)
    except:
      log.critical(f'Failed to load font {fontname}')
      sys.exit(3)

    # Create a blank image for drawing.
    # Swap height/width to rotate it to landscape
    self.height = self.display.width
    self.width = self.display.height
    self.image = Image.new('RGB', (self.width, self.height))  # Fill entire screen with drawing space
    self.draw = ImageDraw.Draw(self.image)

    # Keep the splash screen displayed a bit
    time.sleep(1.0)

    if self.profile:
      self.pr = cProfile.Profile()
      self.pr.enable()

    self.disp_start_time = time.time()
    self._sleep_timer = time.time()

    return True

  def run(self):
    # AmpliPi connection
    connected = False
    connected_once = False
    max_connection_retries = 10
    connection_retries = 0
    sources: List[models.Source] = []
    zones: List[models.Zone] = []

    frame_num = 0
    frame_times = []
    use_debug_port = False
    disp_start_time = time.time()
    _sleep_timer = time.time()
    run = True
    while frame_num < 10 and run:
      frame_start_time = time.time()

      log.debug(f'Active screen = {self._active_screen}')
      if self._active_screen == 0:
        # Get AmpliPi status
        if use_debug_port:
          primary_url, secondary_url = self.API_URL_DEBUG, self.API_URL
        else:
          primary_url, secondary_url = self.API_URL, self.API_URL_DEBUG
        primary_success, _sources, _zones = get_amplipi_data(primary_url)
        if primary_success:
          sources = _sources
          zones = _zones
        elif self.API_URL_DEBUG is not None:
          secondary_success, _sources, _zones = get_amplipi_data(secondary_url)
          if secondary_success:
            sources = _sources
            zones = _zones
            use_debug_port = not use_debug_port
            log.warning(f"Couldn't connect at {primary_url} but got a connection at {secondary_url}, switching over")

        if not primary_success and not secondary_success:
          connection_retries += 1
          if not connected_once:
            if connection_retries == 1:
              log.info(f"Waiting for REST API to start at {primary_url}")
            elif connection_retries == max_connection_retries:
              log.error(f"Couldn't connect to REST API at {primary_url}")
          elif connection_retries < max_connection_retries:
            log.error(f'Failure communicating with REST API at {primary_url}')
          elif connection_retries == max_connection_retries:
            log.error(f'Lost connection to REST API at {primary_url}')

          if connection_retries >= max_connection_retries:
            connected = False
        else:
          if not connected:
            url = primary_url if primary_success else secondary_url
            log.info(f'Connected to REST API at {url}')
          connected = True
          connected_once = True
          connection_retries = 0

        # Get stats
        try:
          ip_str = ni.ifaddresses(self.args.iface)[ni.AF_INET][0]['addr'] + ', ' + socket.gethostname() + '.local'
        except:
          ip_str = 'Disconnected'

        cpu_pcnt = psutil.cpu_percent()
        cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
        cpu_str1 = f'{cpu_pcnt:4.1f}%'
        cpu_str2 = f'{cpu_temp:4.1f}\xb0C'

        ram_total = int(psutil.virtual_memory().total / (1024 * 1024))
        ram_used = int(psutil.virtual_memory().used / (1024 * 1024))
        ram_pcnt = 100 * ram_used / ram_total
        ram_str = f'{ram_used}/{ram_total} MB'

        disk_usage = psutil.disk_usage('/')
        disk_pcnt = disk_usage.percent
        disk_used = disk_usage.used / (1024 ** 3)
        disk_total = disk_usage.total / (1024 ** 3)
        disk_str1 = f'{disk_pcnt:4.1f}%'
        disk_str2 = f'{disk_used:.2f}/{disk_total:.2f} GB'

        # Render text
        cw = 8  # Character width
        ch = 16  # Character height
        self.draw.rectangle((0, 0, self.width - 1, self.height - 1), fill=0)  # Clear image

        # BCM2837B0 is rated for [-40, 85] C
        # For now show green for anything below room temp
        self.draw.text((1 * cw, 0 * ch + 2), 'CPU:', font=self.font, fill=Color.WHITE.value)
        self.draw.text((7 * cw, 0 * ch + 2), cpu_str1, font=self.font, fill=gradient(cpu_pcnt))
        self.draw.text((14 * cw, 0 * ch + 2), cpu_str2, font=self.font, fill=gradient(cpu_temp, min_val=20, max_val=85))
        self.draw.text((22 * cw, 0 * ch + 2), 'Mem:', font=self.font, fill=Color.WHITE.value)
        self.draw.text((28 * cw, 0 * ch + 2), ram_str, font=self.font, fill=gradient(ram_pcnt))

        disk_color = gradient(disk_pcnt)
        self.draw.text((1 * cw, 1 * ch + 2), 'Disk:', font=self.font, fill=Color.WHITE.value)
        self.draw.text((7 * cw, 1 * ch + 2), disk_str1, font=self.font, fill=disk_color)
        self.draw.text((14 * cw, 1 * ch + 2), disk_str2, font=self.font, fill=disk_color)

        self.draw.text((1 * cw, 2 * ch + 2), f'IP:   {ip_str}', font=self.font, fill=Color.WHITE.value)

        password, pass_color = self.default_pass.update()
        self.draw.text((1 * cw, 3 * ch + 2), f'Password: ', font=self.font, fill=Color.WHITE.value)
        self.draw.text((11 * cw, 3 * ch + 2), password, font=self.font, fill=pass_color.value)

        if connected:
          # Show source input names
          self.draw.text((1 * cw, int(4.5 * ch)), 'Source 1:', font=self.font, fill=Color.WHITE.value)
          self.draw.text((1 * cw, int(5.5 * ch)), 'Source 2:', font=self.font, fill=Color.WHITE.value)
          self.draw.text((1 * cw, int(6.5 * ch)), 'Source 3:', font=self.font, fill=Color.WHITE.value)
          self.draw.text((1 * cw, int(7.5 * ch)), 'Source 4:', font=self.font, fill=Color.WHITE.value)
          xs = 11 * cw
          xp = xs - round(0.5 * cw)  # Shift playing arrow back a bit
          ys = 4 * ch + round(0.5 * ch)
          self.draw.line(((cw, ys - 3), (self.width - 2 * cw, ys - 3)), width=2, fill=Color.LIGHTGRAY.value)
          for i, src in enumerate(sources):
            sinfo = sources[i].info
            if sinfo is not None:
              if sinfo.state == 'playing':
                self.draw.polygon(
                  [(xp, ys + i * ch + 3), (xp + cw - 3, ys + round((i + 0.5) * ch)), (xp, ys + (i + 1) * ch - 3)],
                  fill=Color.GREEN.value)
              self.draw.text((xs + 1 * cw, ys + i * ch), sinfo.name, font=self.font, fill=Color.YELLOW.value)
          self.draw.line(((cw, ys + 4 * ch + 2), (self.width - 2 * cw, ys + 4 * ch + 2)), width=2,
                         fill=Color.LIGHTGRAY.value)

          # Show volumes
          # TODO: only update volume bars if a volume changed
          draw_volume_bars(self.draw, self.font, self.small_font, zones, x=cw, y=9 * ch - 2,
                           height=self.height - 9 * ch,
                           width=self.width - 2 * cw)
        else:
          # Show an error message on the display, and the AmpliPi logo below
          if not connected_once and connection_retries <= max_connection_retries:
            msg = 'Connecting to the REST API' + '.' * connection_retries
            text_c = Color.WHITE.value
          else:
            msg = 'Cannot connect to the REST API at\n' + self.API_URL
            text_c = Color.RED.value
          text_y = (self.height - self.ap_logo.size[1] - 4 * ch) // 2 + 4 * ch
          self.draw.text((self.width / 2 - 1, text_y), msg, anchor='mm', align='center', font=self.font, fill=text_c)
          self.image.paste(self.ap_logo, box=(0, self.height - self.ap_logo.size[1]))

        # if self.args.sleep_time > 0 and time.time() - _sleep_timer > self.args.sleep_time:
        if 0 < self.args.sleep_time < time.time() - _sleep_timer:
          # Transition to sleep mode, clear screen
          log.debug('Clearing screen then sleeping')
          self.backlight(False)
          self.draw.rectangle((0, 0, self.width - 1, self.height - 1), fill=Color.BLACK.value)
          self.display.image(self.image)
          self._active_screen = 1
        else:
          # Send the updated image to the display
          self.display.image(self.image)
          self.backlight(True)
      elif self._active_screen == 1:
        # Sleeping, wait for touch to wake up
        log.debug('Sleeping...')

      end = time.time()
      frame_times.append(end - frame_start_time)
      log.debug(f'frame time: {sum(frame_times) / len(frame_times):.3f}s')
      sleep_time = 1 / self.args.update_rate - (end - frame_start_time)
      if sleep_time > 0:
        time.sleep(sleep_time)
      else:
        log.warning('Frame took too long')

      if self.profile:
        frame_num = frame_num + 1

      # If the test timeout is 0, ignore testing
      if self.args.test_timeout > 0.0:
        if self._touch_test_passed or (time.time() - disp_start_time) > self.args.test_timeout:
          run = False

    if self.profile:
      self.pr.disable()
      self.pr.print_stats(sort='time')

    # Stop handling touch events
    gpio.remove_event_detect(self.t_irq_pin.id)

    # Clear display on exit
    self.display.image(Image.new('RGB', (self.width, self.height)))
    self.backlight(False)

    if self.args.test_timeout > 0.0 and not self._touch_test_passed:
      sys.exit(2)  # Exit with an error code >0 to indicate test failure

  def read_xpt2046(self, tx_buf: bytearray, rx_buf: bytearray):
    # Try to access SPI, wait if someone else (i.e. screen) is busy
    while not self.spi.try_lock():
      pass
    self.spi.configure(baudrate=int(2.5 * 10 ** 6))
    self.touch_cs.value = False
    self.spi.write_readinto(tx_buf, rx_buf)
    self.touch_cs.value = True
    self.spi.configure(baudrate=self.spi_baud)
    self.spi.unlock()
    return rx_buf

  def read_xy(self):
    tx_buf = bytearray(5)
    rx_buf = bytearray(5)
    tx_buf[0] = self.XPT2046_CMD_X
    tx_buf[2] = self.XPT2046_CMD_Y
    rx_buf = self.read_xpt2046(tx_buf, rx_buf)

    x = (rx_buf[1] << 5) | (rx_buf[2] >> 3)
    y = (rx_buf[3] << 5) | (rx_buf[4] >> 3)
    return x, y

  def read_temp_raw(self):
    tx_buf = bytearray(5)
    rx_buf = bytearray(5)
    tx_buf[0] = self.XPT2046_CMD_T0
    tx_buf[2] = self.XPT2046_CMD_T1
    rx_buf = self.read_xpt2046(tx_buf, rx_buf)

    v0 = (rx_buf[1] << 5) | (rx_buf[2] >> 3)
    v1 = (rx_buf[3] << 5) | (rx_buf[4] >> 3)
    return v0, v1

  def read_temp(self):
    # From XPT2046 datasheet:
    # degK = dV*q/[k*ln(N)]
    #   dV = V_t1 - V_t0
    #   q = 1.602189*10^-19 C (electron charge)
    #   k = 1.38054*10^-23 eV/degK (Boltzmann's constant)
    #   N = 91 (the current ratio)
    # Vref = 3.3V (Vdd) with 12-bit ADC
    factor = 2.0728  # q/[k*ln(N)] * 3.3/2^12
    v0, v1 = self.read_temp_raw()
    t = (v1 - v0) * factor - 273.15
    return t

  def touch_callback(self):
    # TODO: Debounce touches
    # Mask the interrupt since reading the position generates a false interrupt
    gpio.remove_event_detect(self.t_irq_pin.id)

    # Average 16 values
    x_raw_list = []
    y_raw_list = []
    for i in range(16):
      x, y = self.read_xy()
      # x_sum += x
      # y_sum += y
      if x >= self._cal[0] and y <= self._cal[3]:  # Valid touch
        x_raw_list.append(x)
        y_raw_list.append(y)
    valid_count = len(x_raw_list)
    if valid_count > 0:
      x_raw_mean = round(sum(x_raw_list) / valid_count)
      y_raw_mean = round(sum(y_raw_list) / valid_count)
      x_raw_keep = []
      y_raw_keep = []
      for i in range(valid_count):
        dist = ((x_raw_list[i] - x_raw_mean) ** 2 + (y_raw_list[i] - y_raw_mean) ** 2) ** 0.5
        if dist < self._max_dist:
          x_raw_keep.append(x_raw_list[i])
          y_raw_keep.append(y_raw_list[i])
      inlier_count = len(x_raw_keep)
      if inlier_count >= 4:  # At least a quarter of the points were valid and inliers
        x_raw = sorted(x_raw_keep)[inlier_count // 2]
        y_raw = sorted(y_raw_keep)[inlier_count // 2]

        # Use calibration to scale to the range [0,1]
        x_cal = min(max((float(x_raw) - self._cal[0]) / (self._cal[2] - self._cal[0]), 0), 1)
        y_cal = min(max((float(y_raw) - self._cal[1]) / (self._cal[3] - self._cal[1]), 0), 1)

        # Swap x and y and reverse to account for screen rotation
        y = round(self.height * (1 - x_cal))
        x = round(self.width * (1 - y_cal))
        log.debug(f'Touch at {x},{y}')
        _touch_test_passed = True
        # if x > (3*width/4):
        #  self._active_screen = (self._active_screen + 1) % NUM_SCREENS
        # if x < (width/4):
        #  self._active_screen = (self._active_screen - 1) % NUM_SCREENS
        self._active_screen = 0  # 'Wake up' the screen
        _sleep_timer = time.time()
        # TODO: Redraw screen instantly, don't wait for next display period
      else:
        log.debug(f'Not enough inliers: {inlier_count} of 16')
    else:
      log.debug('No valid points')

    gpio.add_event_detect(self.t_irq_pin.id, gpio.FALLING, callback=lambda _: self.touch_callback())

  def backlight(self, on: bool):
    if on:
      self.led.duty_cycle = int(self.args.brightness * (2 ** 16 - 1))
    else:
      self.led.duty_cycle = 0

def draw_volume_bars(draw, font, small_font, zones: List[models.Zone], x=0, y=0, width=320, height=240):
  n = len(zones)
  if n == 0:  # No zone info from AmpliPi server
    pass
  elif n <= 6:  # Draw horizonal bars and full zone names
    wb = int(width / 2)  # Each bar's full width
    hb = 12  # Each bar's height
    sp = int((height - n * hb) / (2 * (n - 1)))  # Spacing between bars
    xb = width - wb  # Bar starting (left) x coordinate
    for i in range(n):
      yb = y + i * hb + 2 * i * sp  # Bar starting y-position

      # Draw zone name as text
      draw.text((x, yb), zones[i].name, font=font, fill=Color.WHITE.value)

      # Draw background of volume bar
      draw.rectangle((xb, int(yb + 2), xb + wb, int(yb + hb)), fill=Color.LIGHTGRAY.value)

      # Draw volume bar
      if zones[i].vol_f > models.MIN_VOL_F:
        color = Color.DARKGRAY.value if zones[i].mute else Color.BLUE.value
        xv = xb + round(zones[i].vol_f * wb)
        draw.rectangle((xb, int(yb + 2), xv, int(yb + hb)), fill=color)
  else:  # Draw vertical bars and zone number
    # Get the pixel height of a character, and add vertical margins
    ch = small_font.getbbox('0', anchor='lt')[3] + 4
    wb = 12  # Each bar's width
    hb = height - ch  # Each bar's full height
    sp = int((width - n * wb) / (2 * (n - 1)))  # Spacing between bars
    yb = y + hb  # Bar starting (bottom) y coordinate
    for i in range(n):
      xb = x + i * wb + 2 * i * sp  # Bar starting x-position

      # Draw zone number as centered text
      draw.text((xb + round(wb / 2), y + height - round(ch / 2)), str(i + 1),
                anchor='mm', font=small_font, fill=Color.WHITE.value)

      # Draw background of volume bar
      draw.rectangle((xb, yb, xb + wb, y), fill=Color.LIGHTGRAY.value)

      # Draw volume bar
      if zones[i].vol_f > models.MIN_VOL_F:
        color = Color.DARKGRAY.value if zones[i].mute else Color.BLUE.value
        yv = yb - round(zones[i].vol_f * hb)
        draw.rectangle((xb, yb, xb + wb, yv), fill=color)
  # TODO: For more than 18 zones, show on multiple screens.

def gradient(num, min_val=0, max_val=100):
  # red = round(255*(val - min_val) / (max_val - min_val))
  # grn = round(255-red)#255*(max_val - val) / (max_val - min_val)
  mid = (min_val + max_val) / 2
  scale = 255 / (mid - min_val)
  if num <= min_val:
    red = 0
    grn = 255
  elif num >= max_val:
    red = 255
    grn = 0
  elif num < mid:
    red = round(scale * (num - min_val))
    grn = 255
  else:
    red = 255
    grn = 255 - round(scale * (num - mid))
  return f'#{red:02X}{grn:02X}00'

def get_amplipi_data(base_url: Optional[str]) -> Tuple[bool, List[models.Source], List[models.Zone]]:
  """ Get the AmpliPi's status via the REST API
      Returns true/false on success/failure, as well as the sources and zones
  """
  _zones: List[models.Zone] = []
  _sources: List[models.Source] = []
  success = False
  if base_url is None:
    return False, _sources, _zones
  try:
    """ TODO: If the AmpliPi server isn't available at this url, there is a
    5-second delay introduced by socket.getaddrinfo """
    req = requests.get(base_url, timeout=0.2)
    if req.status_code == 200:
      status = models.Status(**req.json())
      _zones = status.zones
      _sources = status.sources
      success = True
    else:
      log.error('Bad status code returned from AmpliPi')
  except requests.ConnectionError as err:
    log.debug(err.args[0])
  except requests.Timeout:
    log.error('Timeout requesting AmpliPi status')
  except ValueError:
    log.error('Invalid json in AmpliPi status response')

  return success, _sources, _zones
