# Amplifier Board

## Rev 1.A
Initial release

## Rev 2.B
* Isolated the grounds for the fan control and LCD display circuitry.
* Removed the ground connection from the screw pads.
* Moved from the MAX6644 integrated fan controller to firmware fan control:
  - Temp sensing transistors (Q1, Q2) replaced with NTC thermistors (R19, R20)
  - R4, R5 replaced with 0ohm resistors
  - C34, C35 fitted with 10uF caps
  - Pin 1 of J12 changed from GND to 3.3VA
