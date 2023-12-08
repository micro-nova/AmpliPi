# Controller Board

## Rev 2.A

Initial release

## Rev 3.A

* 3.5mm input moved to analog ground
* SPDIF input moved to 5VA and analog ground
* 9VA rail switched to 5VA, removed 9VA->5VA LDO
* Added isolators for all digital signals between control board and preamp board
* Isolator added for I2S lines between Pi and DAC

## Rev 4.A

* Switched to 2-channel SOIC-8 packages for all isolators as other packages
  are currently not available.

## Rev 5.A

* Added a chassis ground (EGND).
* Connected all external connector shells to EGND.
* Added ESD protection circuitry to all external connectors (Ethernet, USB, audio).
* Removed HDMI port.
* Added 2 layers to PCB and moved all traces to internal layers to reduce RF emissions.
* Fix USB hub labels for USB 2-5.

## Rev 6.A

* Removed optical audio input.
* Added two M3 holes at the front of the board for mounting to panel.
* Removed pours on new layers under the isolator chips.
