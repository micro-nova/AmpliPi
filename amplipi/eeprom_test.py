#!/usr/bin/env python3
import eeprom

#bi = eeprom.BoardInfo(0, eeprom.UnitType.NONE, eeprom.BoardType.NONE, eeprom.BoardRev())
#bi.from_bytes(bytes([0,0,0,0,254,1,0xD0,4,0x41]))
bi = eeprom.BoardInfo(bytes([0,0,0,0,254,1,0xD0,4,0x41]))
print(bi.to_bytes())
