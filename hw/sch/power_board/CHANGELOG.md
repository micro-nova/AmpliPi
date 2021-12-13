# Power Board

## Rev 2.A
Initial release

### Modifications from Schematic
* TH2/TL2 pulled high via 4.7k resistor.
* TH1/TL1 pulled low via 4.7k resistor.
* 9VA DC-DC supply removed, replaced with 9VA isolated supply ITR0305S09.

## Rev 3.B
* Power good resistors changed for 5V/12V DC-DC power supplies to make LEDs dimmer
* 9VA DC-DC supply removed, replaced with 5VA and 9VA isolated supplies.
* Switched all 3.3V circuitry over to analog ground as the preamp board no longer has digital ground.
* R4 added to reduce PG_12V from 5V to 3.3V logic.
* Moved from the MAX6644 integrated fan controller to firmware fan control:
  - Removed MAX6644 fan controller.
  - Changed pin 1 of J9 from GND to 3.3VA
  - Connected FAN_ON from GPIO expander directly to FAN_PWM.
  - DXP1/DXP2 are now connected to thermistors on Amp board.
  - MAX11601 ADC now samples thermistor voltages from amp heatkinks on AN1 and AN3
