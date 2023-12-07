"""Module for reading and writing to Amplipi EEPROMs.

These are used to identify features and device types among other things."""

from dataclasses import dataclass
from enum import IntEnum
from time import sleep
from typing import List, Optional, Tuple
from smbus2 import SMBus
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

@dataclass
class EepromField:
  size    : int    # Size in bytes
  datatype: type   # Type of the field
  value   : object # Actual value of the field

class BoardInfo:
  """Board info, to be read/written to EEPROM"""

  EEPROM_PAGE_SIZE: int  = 16 # Number of bytes per EEPROM page.

  fields = {
    'format'       : EepromField(size = 1, datatype = int,       value =    0),
    'serial'       : EepromField(size = 4, datatype = int,       value = None),
    'unit_type'    : EepromField(size = 1, datatype = UnitType,  value = None),
    'board_type'   : EepromField(size = 1, datatype = BoardType, value = None),
    'board_rev_num': EepromField(size = 1, datatype = int,       value = None),
    'board_rev_let': EepromField(size = 1, datatype = str,       value = None),
  }

  def __init__(self, serial: Optional[int] = None, unit_type: Optional[UnitType] = None,
               board_type: Optional[BoardType] = None, board_rev: Optional[Tuple[int, str]] = None) -> None:
    self.fields['serial'].value = serial
    self.fields['unit_type'].value = unit_type
    self.fields['board_type'].value = board_type
    if board_rev:
      self.fields['board_rev_num'].value = board_rev[0]
      self.fields['board_rev_let'].value = board_rev[1]

  def _get_size(self) -> int:
    return sum([f.size for f in self.fields.values()])

  def from_bytes(self, data: bytes) -> None:
    if len(data) < self._get_size():
      raise ValueError("Not enough data to create BoardInfo")
    address = 0
    for f in self.fields.values():
      # val = 0
      # for i in range(f.size):
      #   # Unfortunately big-endian, go backwards here.
      #   val += data[address + i] << (8*(f.size - 1 - i))
      val = sum([data[address + i] << (8*(f.size - 1 - i)) for i in range(f.size)])
      f.value = f.datatype(val)
      address += f.size

  def to_bytes(self) -> bytes:
    page_buf = [0] * self.EEPROM_PAGE_SIZE
    address = 0
    for f in self.fields.values():
      for i in range(f.size):
        # Unfortunately big-endian, go backwards here.
        #page_buf[field.address + i] = (int(f.value) & (0xFF << (8*(f.size - 1 - i)))) >> (8*(f.size - 1 - i))
        page_buf[address + f.size - 1 - i] = (int(f.value) & (0xFF << (8*i))) >> (8*i)
      address += f.size
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
  def __init__(self, board: BoardType) -> None:
    self.board = board.value

  @staticmethod
  def get_available_devices() -> List[BoardType]:
    """Get list of available devices."""
    return [bt for bt in BoardType if EEPROM(bt).get_board_type() is not None]

  def _bus(self) -> int:
    """Returns the I2C bus to communicate on, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return (int(self._board) & 0x80) >> 7 # Bit 7 is bus, either 0 (Pi bus) or 1 (Preamp bus).

  def _address(self) -> int:
    """Returns the I2C address of the EEPROM, based on the BoardType"""
    # TODO: make board a full class to abstract this away.
    return int(self._board) & 0x7F # Lowest 7 bits are the I2C address

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

  def _write_number(self, bytes_len: int, addr: int, value: int) -> None:
    """Write number to EEPROM, big-endian."""
    write_out = [0]*bytes_len
    for i in range(0, bytes_len):
      write_out[i] = value & 0xFF
      value >>= 8

    write_out.reverse()

    self._write(addr, write_out)

  def _read_number(self, bytes_len: int, addr: int) -> int:
    """Read number from EEPROM."""
    value = 0
    read_in = self._read(addr, bytes_len)
    for i in range(0, bytes_len):
      value += read_in[i]
      value <<= 8

    return value >> 8

  def _write_letter(self, addr: int, value: str) -> None:
    """Write letter to EEPROM."""
    self._write(addr, [ord(*value)])

  def _read_letter(self, addr: int) -> str:
    """Read letter from EEPROM."""
    return chr(self._read(addr, 1)[0])

  def _write_format(self) -> None:
    """Write format to EEPROM."""
    self._write(FORMAT_ADDR, [FORMAT])

  def write_serial(self, serial: int) -> None:
    """Write serial to EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")
    self._write_number(4, SERIAL_ADDR, serial)

  def write_unit_type(self, unit_type: UnitType) -> None:
    """Write unit type to EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")
    self._write(UNIT_TYPE_ADDR, [unit_type.value])

  def write_board_type(self, board_type: BoardType) -> None:
    """Write board type to EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")
    self._write(BOARD_TYPE_ADDR, [board_type.value])

  def write_board_rev(self, rev: Tuple[int, str]) -> None:
    """Write board rev to EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")
    self._write_number(1, BOARD_REV_ADDR, rev[0])
    self._write_letter(BOARD_REV_ADDR+1, rev[1].upper())

  def get_format(self) -> int:
    """Check EEPROM format."""
    fmt = self._read(FORMAT_ADDR, 1)[0]

    return fmt

  def get_serial(self) -> int:
    """Get serial from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return self._read_number(4, SERIAL_ADDR)

  def get_unit_type(self) -> UnitType:
    """Get unit type from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return UnitType(self._read(UNIT_TYPE_ADDR, 1)[0])

  def get_board_type(self) -> Optional[BoardType]:
    """Get board type from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return BoardType(self._read(BOARD_TYPE_ADDR, 1)[0])

  def get_board_rev(self) -> Tuple[int, str]:
    """Get board rev from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return (self._read_number(1, BOARD_REV_ADDR),
            self._read_letter(BOARD_REV_ADDR+1))

  def read_board_info(self) -> BoardInfo:
    """Get board info from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return self._read_number(4, SERIAL_ADDR)

    return BoardInfo(self.get_serial(),
                      self.get_unit_type(),
                      self.get_board_type(),
                      self.get_board_rev())

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
