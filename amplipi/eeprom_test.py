#!/usr/bin/env python3
import eeprom

bi = eeprom.BoardInfo()
bi.from_bytes([0,0,0,0,254,1,0xD0,4,0x41])
print(bi.to_bytes())
