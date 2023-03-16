"""Module for reading and writing to Amplipi EEPROM."""

from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import List, Tuple
import smbus2 as smbus
import RPi.GPIO as GPIO

WP_PIN = 34
WRITE_CHECK_ADDRESS = (int)((2048/8)-1) #last byte of 2kbit EEPROM, 8bit per address
FORMAT_ADDR = 0x00
SERIAL_ADDR = 0x01
UNIT_TYPE_ADDR = 0x05
BOARD_TYPE_ADDR = 0x06
BOARD_REV_ADDR = 0x07

SUPPORTED_FORMATS = [0x00]
FORMAT = 0x00

class UnitType(Enum):
  """Unit type"""
  PI = 0
  PRO = 1
  STREAMER = 2

class BoardType(Enum):
  """Board type"""
  STREAMER_SUPPORT = 0x50

@dataclass
class BoardInfo:
  """Board info"""
  serial: int
  unit_type: UnitType
  board_type: BoardType
  board_rev: Tuple[int, str]


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
  def __init__(self, bus: int, board: BoardType) -> None:
    self._i2c = smbus.SMBus(bus)
    self._address = board.value
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(WP_PIN, GPIO.OUT)

  def _enable_write(self) -> None:
    """Enable write to EEPROM."""
    GPIO.output(WP_PIN, GPIO.LOW)
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
    """Write data to address in EEPROM."""
    try:
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
    """Write number to EEPROM."""
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
    self._write_letter(BOARD_REV_ADDR+1, rev[1])

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

  def get_board_type(self) -> BoardType:
    """Get board type from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return BoardType(self._read(BOARD_TYPE_ADDR, 1)[0])

  def get_board_rev(self) -> Tuple[str, int]:
    """Get board rev from EEPROM."""
    if self.get_format() not in SUPPORTED_FORMATS:
      raise UnsupportedFormatError("Unsupported format")

    return (self._read_number(1, BOARD_REV_ADDR),
            self._read_letter(BOARD_REV_ADDR+1))

  def get_board_info(self) -> BoardInfo:
    """Get board info from EEPROM."""
    return BoardInfo(self.get_serial(),
                      self.get_unit_type(),
                      self.get_board_type(),
                      self.get_board_rev())

  def write_board_info(self, board_info: BoardInfo) -> None:
    """Write board info to EEPROM."""
    self._write_format()
    self.write_serial(board_info.serial)
    self.write_unit_type(board_info.unit_type)
    self.write_board_type(board_info.board_type)
    self.write_board_rev(board_info.board_rev)
