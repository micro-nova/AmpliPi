"""Module for reading and writing to Amplipi EEPROMs.

These are used to identify features and device types among other things."""

from dataclasses import dataclass
from enum import IntEnum
from time import sleep
from typing import List, Optional, Tuple, Union
from smbus2 import SMBus
from struct import pack, unpack, calcsize
try:
  from RPi import GPIO
except Exception:
  pass

WP_PIN = 34
WRITE_CHECK_ADDRESS = (int)((2048/8)-1) #last byte of 2kbit EEPROM, 8bit per address

class UnitType(IntEnum):
  """Unit type"""
  NONE     = 0 # No branding, currently only used in AP1-Z6
  AP1_S4Z6 = 1 # AmpliPro main unit branding/functionality
  AP1_S4   = 2 # Streamer branding/functionality

class BoardType(IntEnum):
  """Matches the I2C address. The address is stored in the lowest 7 bits of the byte.
  * For EEPROMs connected directly to the Pi's I2C bus, the MSB is 0 (uses I2C bus 0).
  * For EEPROMs connected to the Preamp's I2C bus, the MSB is 1 (uses I2C bus 1).

  The MC24C02's base I2C address is 0x50, with the 3 LSBs controlled by pins E[2:0].
  """
  STREAMER_SUPPORT = 0x50
  PREAMP           = 0xD0

class BoardRev:
  """Board revision"""
  number: int
  letter: str
  def __init__(self, number: int = 0, letter: str = 'A') -> None:
    # If the 'number' passed is larger than a byte, assume it's a packed number/letter combo
    if number > 255:
      self.number = number >> 8
      self.letter = chr(number & 0xFF)
    else:
      self.number = number
      self.letter = letter
  def __str__(self) -> str:
    return f'Rev{self.number}.{self.letter}'
  def __int__(self) -> int:
    return (self.number << 8) + ord(self.letter)

class BoardInfo:
  """Board info, to be read/written to EEPROM"""

  @dataclass
  class EepromField:
    """Helper struct for the BoardInfo class"""
    format  : str    # Format char, see https://docs.python.org/3/library/struct.html
    value   : object # Actual value of the field

  _fields = {
    'format'    : EepromField(format = 'B', value = 0),
    'serial'    : EepromField(format = 'I', value = 0),
    'unit_type' : EepromField(format = 'B', value = UnitType.NONE),
    'board_type': EepromField(format = 'B', value = BoardType.STREAMER_SUPPORT),
    'board_rev' : EepromField(format = 'H', value = BoardRev()),
  }

  def __init__(self, serial: Optional[Union[int, bytes]] = None,
               unit_type: Optional[UnitType] = None, board_type: Optional[BoardType] = None,
               board_rev: Optional[BoardRev] = None ) -> None:
    """`serial` can either be an integer number to assign, or the list of bytes from a EEPROM."""
    if type(serial) is bytes:
      data = serial
      size = calcsize(f'>{"".join([f.format for f in self._fields.values()])}')
      if len(data) < size:
        raise ValueError("Not enough data to create BoardInfo")
      unpacked = unpack(self._get_format_str(), data)
      for i, v in enumerate(self._fields.values()):
        v.value = type(v.value)(unpacked[i])
      #self._fields = {k:type(v)(unpacked[i]) for i,(k,v) in enumerate(self._fields.items())}
    else:
      self._fields['serial'].value = serial
      self._fields['unit_type'].value = unit_type
      self._fields['board_type'].value = board_type
      self._fields['board_rev'].value = board_rev

  def _get_format_str(self) -> str:
    return f'>{"".join([f.format for f in self._fields.values()])}'

  def to_bytes(self) -> bytes:
    page_buf = pack(self._get_format_str(), *[int(f.value) for f in self._fields.values()])
    return page_buf


class EEPROMWriteError(Exception):
  """Error writing to EEPROM."""

class EEPROMReadError(Exception):
  """Error reading from EEPROM."""

class EEPROMWriteProtectError(Exception):
  """Error setting EEPROM to write mode."""

class UnsupportedFormatError(Exception):
  """Unknown EEPROM format."""

class EEPROM:
  """Class for reading from and writing to EEPROM."""

  EEPROM_PAGE_SIZE: int  = 16 # Number of bytes per EEPROM page.

  def __init__(self, board: BoardType) -> None:
    self._board = board.value

  def _bus(self) -> int:
    """Returns the I2C bus to communicate on, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return (int(self._board) & 0x80) >> 7 # Bit 7 is bus, either 0 (Pi bus) or 1 (Preamp bus).

  def _address(self) -> int:
    """Returns the I2C address of the EEPROM, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return int(self._board) & 0x7F # Lowest 7 bits are the I2C address

  # TODO: Is this necessary?
  def _enable_write(self) -> None:
    """Enable write to EEPROM. Only required for streamers."""
    try:
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(WP_PIN, GPIO.OUT)
      GPIO.output(WP_PIN, GPIO.LOW)
    except NameError:
      pass

    try:
      val = self._i2c.read_i2c_block_data(self._address, WRITE_CHECK_ADDRESS, 1)[0]
      self._i2c.write_i2c_block_data(self._address, WRITE_CHECK_ADDRESS, [val+1])
      sleep(0.1)
      check = self._i2c.read_i2c_block_data(self._address, WRITE_CHECK_ADDRESS, 1)[0]
      self._i2c.write_i2c_block_data(self._address, WRITE_CHECK_ADDRESS, [val])
      sleep(0.1)
      if check != val+1:
        raise EEPROMWriteProtectError("Write enable failed")

    except OSError as exception:
      raise EEPROMWriteProtectError("Write enable failed") from exception

  def present(self) -> bool:
    if self._bus() == 1:
      # Preamp bus, have to write to the micro which will forward the page of data to the EEPROM.
      with SMBus(self._bus()) as bus:
        bus.read_byte_data(self._address(), 0x1F, ctrl_byte) # Initiate write
        bus.write_byte_data(self._address(), 0x20, d)
        page = address // 16
        eeprom_address = self._address() & 0x7
        ctrl_byte = (page << 4) + (eeprom_address << 1)       # LSB = 0 for write
    else:
      # Direct Pi I2C bus, open and write as normal.
      with SMBus(self._bus()) as bus:
        self._i2c.write_i2c_block_data(self._address, address, data)
    return False

  def _write(self, address: int, data: List[int]) -> None:
    """Write data to the EEPROM, starting at address `address`."""
    try:
      if self._bus() == 1:
        # Preamp bus, have to write to the micro which will forward the page of data to the EEPROM.
        if len(data) > 16:
          raise NotImplementedError("Writing more than 1 page at a time through the "
                                    "Preamp's microcontroller is not yet supported.")
        if address != 0:
          raise NotImplementedError("Writing to an address other than the start of a page "
                                    "is not yet supported for the Preamp.")
        with SMBus(self._bus()) as bus:
          # For now only single-byte writes are supported to the Preamp's micro.
          for i, d in enumerate(data):
            bus.write_byte_data(self._address(), 0x20 + i, d)
          page = address // 16
          eeprom_address = self._address() & 0x7
          ctrl_byte = (page << 4) + (eeprom_address << 1)       # LSB = 0 for write
          bus.write_byte_data(self._address(), 0x1F, ctrl_byte) # Initiate write
      else:
        # Direct Pi I2C bus, open and write as normal.
        with SMBus(self._bus()) as bus:
          self._i2c.write_i2c_block_data(self._address, address, data)

    except OSError as exception:
      raise EEPROMWriteError("Write failed") from exception
    sleep(0.1)

  def _read(self, address: int, length: int) -> List[int]:
    """Read data from address in EEPROM."""
    try:
      return self._i2c.read_i2c_block_data(self._address, address, length)
    except OSError as exception:
      raise EEPROMReadError("Read failed") from exception

  def read_board_info(self) -> Optional[BoardInfo]:
    """Get board info from EEPROM."""

    # Read page from EEPROM
    eeprom_data = bytes([0,0,0,0,254,1,0xD0,4,0x41])

    # Convert to BoardInfo if successful
    board_info = BoardInfo(eeprom_data)
    if board_info. not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return BoardInfo(eeprom_data)

  def write_board_info(self, board_info: BoardInfo) -> None:
    """Write board info to EEPROM.
    | Addr | Datatype | Data                      |
    | ---- | -------- | :------------------------ |
    | 0x00 | uint8    | EEPROM Data Format (0x00) |
    | 0x01 | uint32   | Serial Number             |
    | 0x05 | uint8    | Unit Type                 |
    | 0x06 | uint8    | Board Type                |
    | 0x07 | uint8    | Board Revision Number     |
    | 0x08 | char     | Board Revision Letter     |
    """

    self._write_number(4, SERIAL_ADDR, serial)
    """Write number to EEPROM, big-endian."""
    write_out = [0]*bytes_len
    for i in range(0, bytes_len):
      write_out[i] = value & 0xFF
      value >>= 8
    write_out.reverse()
    self._write(addr, write_out)


    self.write_serial(board_info.serial)
    self.write_unit_type(board_info.unit_type)
    self.write_board_type(board_info.board_type)
    self.write_board_rev(board_info.board_rev)


def find_boards() -> List[BoardType]:
  """Get list of available boards be checking their EEPROMs."""
  #return [bt for bt in BoardType if EEPROM(bt).get_board_type() is not None]
  boards = []
  for board in BoardType:
    ep = EEPROM(board)

  return boards
