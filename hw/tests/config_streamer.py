#!/usr/bin/env python3
""" Interactively configure the Streamer's EEPROM"""
import os
import re
import requests
import sys
from typing import Optional, Tuple, Union

# Add the amplipi directory to PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from amplipi.eeprom import BoardInfo, BoardType, EEPROM, UnitType

BOARD_REV_RE = re.compile(r"(\d+)([A-z])") # accept lower or uppser case change designator
                                           # we will uppercase later

def main() -> None:
  """Write board info to eeprom, using user input for serial number and board revision"""
  serial: Optional[int] = None
  board_rev : Union[Tuple[int, str], Tuple[None, None]] = (None, None)
  try:
    serial_input = input("Enter streamer serial number (ie: 1234):")
    serial = int(serial_input)
    board_rev_input = input("Enter streamer board revision (ie: 1a):").strip()
    board_rev_match = BOARD_REV_RE.fullmatch(board_rev_input)
    if board_rev_match and len(board_rev_match.groups()) == 2:
      board_rev = (int(board_rev_match.group(1)), board_rev_match.group(2))
    else:
      print(f'Failed to parse board revision from "{board_rev_input}"')
  except ValueError as e:
    print(f'Failed to read serial number from "{serial_input}": {e}')
  except (KeyboardInterrupt, EOFError):
    print("Failed to read input")

  if serial is None or board_rev[0] is None:
    sys.exit(1)

  try:
    print(f"Writing streamer config to eeprom: serial={serial}, board_rev={board_rev[0]}{board_rev[1]}")
    eeprom = EEPROM(0, BoardType.STREAMER_SUPPORT)
    eeprom.write_board_info(BoardInfo(serial=serial, unit_type=UnitType.STREAMER, board_type=BoardType.STREAMER_SUPPORT, board_rev=board_rev))
  except Exception as e:
    print(f"Failed to write board info to eeprom: {e}")
    sys.exit(1)

  try:
    print("Resetting amplipi to detect streamer capability")
    response = requests.post('http://0.0.0.0/api/factory_reset', timeout=10)
    if not response.ok:
      print(f"Failed to reset amplipi: {response.text}")
  except Exception as e:
    print(f"Failed to reset amplipi: {e}")

if __name__ == "__main__":
  if len(sys.argv) > 1:
    print(main.__doc__)
  else:
    main()
