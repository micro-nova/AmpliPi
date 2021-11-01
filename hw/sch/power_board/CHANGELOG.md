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
* Changed pin 1 of J9 from GND to 3.3VA
* Removed MAX6644 fan controller. DXP1/DXP2 are now connected to thermistors on Amp board. MAX11601 ADC now samples thermistor voltages from amp heatkinks on AN1 and AN3
