# Preamp Board

## Rev 2.A
Initial release

### Modifications from Schematic
* 499k pulldowns added to all ALx_R and ALx_L
* Fixed resistor divider on ADC MISO pin to controller board,
  R106 was moved to the other side of R107.
  
## Rev 3.A
* Peak detect circuitry now comes after ac-coupling and biasing.
* removed 5VD supply.
