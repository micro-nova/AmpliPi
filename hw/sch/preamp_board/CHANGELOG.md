# Preamp Board

## Rev 2.A
Initial release

### Modifications from Schematic
* 499k pulldowns added to all ALx_R and ALx_L
* Fixed resistor divider on ADC MISO pin to controller board,
  R106 was moved to the other side of R107.

## Rev 3.A
* Removed 5VD supply and changed all GND to AGND.
* Peak detect:
  - Circuitry now comes after AC-coupling and biasing.
  - Changed  pulldowns from 100k Ohms to 499k.
  - Fixed resistor divider on ADC MISO pin to controller board (R106, R107)
