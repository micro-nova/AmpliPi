"""Module for reading and writing to Amplipi EEPROMs.

These are used to identify features and device types among other things."""

from dataclasses import dataclass
from enum import IntEnum
from struct import pack, unpack, calcsize
from time import sleep
from typing import List, Optional, Union

from smbus2 import SMBus
try:
  from RPi import GPIO
except Exception:
  pass

WP_PIN = 34
WRITE_CHECK_ADDRESS = (int)((2048 / 8) - 1)  # last byte of 2kbit EEPROM, 8bit per address
SUPPORTED_FORMATS = [0x00]  # Supported EEPROM data formats
FORMAT_ADDR = 0x00
SERIAL_ADDR = 0x01
UNIT_TYPE_ADDR = 0x05
BOARD_TYPE_ADDR = 0x06
BOARD_REV_ADDR = 0x07


class UnitType(IntEnum):
  """Unit type"""
  AP1_Z6 = 0    # AmpliPro expansion unit
  AP1_S4Z6 = 1  # AmpliPro main unit
  STREAMER = 2    # Streamer
  NONE = 0xFF   # Unprogrammed EEPROM


class BoardType(IntEnum):
  """Matches the I2C address. The address is stored in the lowest 7 bits of the byte.
  * For EEPROMs connected directly to the Pi's I2C bus, the MSB is 0 (uses I2C bus 0).
  * For EEPROMs connected to the Preamp's I2C bus, the MSB is 1 (uses I2C bus 1).

  The MC24C02's base I2C address is 0x50, with the 3 LSBs controlled by pins E[2:0].
  """
  STREAMER_SUPPORT = 0x50
  PREAMP = 0xD0


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
    format: str    # Format char, see https://docs.python.org/3/library/struct.html
    value: Union[int, UnitType, BoardType, BoardRev]  # Actual value of the field

  _fields = {
    'format': EepromField(format='B', value=0),
    'serial': EepromField(format='I', value=0),
    'unit_type': EepromField(format='B', value=UnitType.NONE),
    'board_type': EepromField(format='B', value=BoardType.STREAMER_SUPPORT),
    'board_rev': EepromField(format='H', value=BoardRev()),
  }

  def __init__(self, serial: Union[int, bytes],
               unit_type: Optional[UnitType] = None, board_type: Optional[BoardType] = None,
               board_rev: Optional[BoardRev] = None) -> None:
    """`serial` can either be an integer number to assign, or the list of bytes from a EEPROM."""
    if isinstance(serial, bytes):
      data = serial
      size = calcsize(f'>{"".join([f.format for f in self._fields.values()])}')
      if len(data) < size:
        raise ValueError("Not enough data to create BoardInfo")
      unpacked = unpack(self._get_format_str(), data)
      for i, v in enumerate(self._fields.values()):
        v.value = type(v.value)(unpacked[i])
      # self._fields = {k:type(v)(unpacked[i]) for i,(k,v) in enumerate(self._fields.items())}
    else:
      self._fields['serial'].value = serial
      assert (unit_type is not None and board_type is not None and board_rev is not None)
      self._fields['unit_type'].value = unit_type
      self._fields['board_type'].value = board_type
      self._fields['board_rev'].value = board_rev

  def _get_format_str(self) -> str:
    return f'>{"".join([f.format for f in self._fields.values()])}'

  def to_bytes(self) -> bytes:
    page_buf = pack(self._get_format_str(), *[int(f.value) for f in self._fields.values()])
    return page_buf

  @property
  def format(self):
    return self._fields['format'].value

  @property
  def serial(self):
    return self._fields['serial'].value

  @property
  def board_type(self):
    return self._fields['board_type'].value


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

  EEPROM_PAGE_SIZE: int = 16  # Number of bytes per EEPROM page.

  def __init__(self, board: BoardType) -> None:
    self._board = board.value

  def _bus(self) -> int:
    """Returns the I2C bus to communicate on, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return (int(self._board) & 0x80) >> 7  # Bit 7 is bus, either 0 (Pi bus) or 1 (Preamp bus).

  def _address(self) -> int:
    """Returns the I2C address of the EEPROM, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return int(self._board) & 0x7F  # Lowest 7 bits are the I2C address

  def _enable_write(self) -> None:
    """Enable write to EEPROM. Only required for streamers."""
    if self._board == BoardType.STREAMER_SUPPORT:
      try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(WP_PIN, GPIO.OUT)
        GPIO.output(WP_PIN, GPIO.LOW)
      except NameError:
        pass
      except OSError as exception:
        raise EEPROMWriteProtectError("Write enable failed") from exception

  def present(self, unit_addr=0x08) -> bool:
    if self._bus() == 1:
      try:
        with SMBus(self._bus()) as bus:
          bus.write_byte_data(unit_addr, 0x1F, 0x01)  # Initiate read of page 0
          return True
      except OSError:
        return False
    else:
      # TODO: Check if Streamer Support Board's EEPROM acks it's address.
      try:
        with SMBus(self._bus()) as bus:
          bus.read_byte(self._board)
          return True
      except OSError:
        return False

  def _write(self, address: int, data: Union[bytes, List[int]]) -> None:
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
          bus.write_byte_data(self._address(), 0x1F, ctrl_byte)  # Initiate write
      else:
        # Direct Pi I2C bus, open and write as normal.
        with SMBus(self._bus()) as bus:
          bus.write_i2c_block_data(self._address(), address, data)

    except OSError as exception:
      raise EEPROMWriteError("Write failed") from exception
    sleep(0.1)

  def _read(self, address: int, length: int, unit_addr=0x08) -> bytes:
    """Read data from address in EEPROM."""
    try:
      if self._bus() == 1:
        # Preamp bus, have to write to the micro which will forward the page of data to the EEPROM.
        assert address % 16 == 0, "Currently only page-aligned reads are implemented for the Preamp EEPROM interface."
        assert length <= 16, "Currently only a single page read is implemented for the Preamp EEPROM interface."
        with SMBus(self._bus()) as bus:
          bus.write_byte_data(unit_addr, 0x1F, 0x01)  # Initiate read of page 0
          # TODO: Wait for reads to finish
          return bytes([bus.read_byte_data(unit_addr, 0x20 + i) for i in range(length)])
      else:
        # Direct Pi I2C bus, open and read as normal.
        with SMBus(self._bus()) as bus:
          return bytes(bus.read_i2c_block_data(self._address(), address, length))
    except OSError as exception:
      raise EEPROMReadError("Read failed") from exception

  def read_board_info(self, unit_addr=0x08) -> Optional[BoardInfo]:
    """Get board info from EEPROM."""

    # Read page from EEPROM
    # TODO: Handle exceptions?
    try:
      eeprom_data = self._read(0, 9, unit_addr)
      # Convert to BoardInfo if successful
      board_info = BoardInfo(eeprom_data)
    except:
      return None   # If there is no EEPROM, such as on an old AmpliPi, read should return nothing
    if board_info.format not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")
    return board_info

  def get_format(self) -> int:
    """Check EEPROM format."""
    fmt = self._read(FORMAT_ADDR, 1)[0]

    return fmt

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
    self._enable_write()
    self._write(0, board_info.to_bytes())

  def erase(self) -> None:
    self._enable_write()
    self._write(0, [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255])


def find_boards() -> List[BoardType]:
  """Get list of available boards by checking their EEPROMs."""
  return [bt for bt in BoardType if EEPROM(bt).present()]
