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
  * Circuitry now comes after AC-coupling and biasing.
  * Changed  pulldowns from 100k Ohms to 499k.
  * Fixed resistor divider on ADC MISO pin to controller board (R106, R107)

## Rev 4.A

* Modified circuitry to support 2 Vrms audio signals, including at the RCA inputs.
  * Moved op-amps, analog muxes, volume control ICs, and resistor dividers from 5V to 9V.
  * Switch from the CD74HCT4066M96 to the CD74HC4066M96 analog muxes to support 9V.
  * Added transistors between the STM32 pins and the analog muxes to level shift to 9V logic.
  * Modify all the pulldown resistors on the analog mux logic signals to pull up to 9V.
* Added a series resistor in the peak detect circuit to divide the new 4.5V baseline voltage
  down to ~2.5V to match the previous version.
* Added an EEPROM to internal I2C bus to identify the board revision.
* Improved ESD handling with TVS diodes connected between the RCA inputs and chassis ground.
* Added 47kOhm pulldowns to RCA inputs to reduce noise when disconnected.
