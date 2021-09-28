# I2C Registers

## Register interface

<table>
  <thead>
    <tr>
      <th>Address</th>
      <th>Name</th>
      <th>bit 7</th>
      <th>bit 6</th>
      <th>bit 5</th>
      <th>bit 4</th>
      <th>bit 3</th>
      <th>bit 2</th>
      <th>bit 1</th>
      <th>bit 0</th>
      <th>Default value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>0x00</td>
      <td>SRC_AD</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">SRC4AD</td>
      <td style="text-align:center">SRC3AD</td>
      <td style="text-align:center">SRC2AD</td>
      <td style="text-align:center">SRC1AD</td>
      <td style="text-align:center">0x0F</td>
    </tr>
    <tr>
      <td>0x01</td>
      <td>ZONE123_SRC</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td colspan=2, td align='center'>Z3SRC</td>
      <td colspan=2, td align='center'>Z2SRC</td>
      <td colspan=2, td align='center'>Z1SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x02</td>
      <td>ZONE456_SRC</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td colspan=2, td align='center'>Z6SRC</td>
      <td colspan=2, td align='center'>Z5SRC</td>
      <td colspan=2, td align='center'>Z4SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x03</td>
      <td>MUTE</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z5M</td>
      <td style="text-align:center">Z4M</td>
      <td style="text-align:center">Z3M</td>
      <td style="text-align:center">Z2M</td>
      <td style="text-align:center">Z1M</td>
      <td style="text-align:center">0x3F</td>
    </tr>
    <tr>
      <td>0x04</td>
      <td>STANDBY</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">STANDBY</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x05</td>
      <td>ZONE1_VOL</td>
      <td colspan=8, td align='center'>Zone 1 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x06</td>
      <td>ZONE2_VOL</td>
      <td colspan=8, td align='center'>Zone 2 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x07</td>
      <td>ZONE3_VOL</td>
      <td colspan=8, td align='center'>Zone 3 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x08</td>
      <td>ZONE4_VOL</td>
      <td colspan=8, td align='center'>Zone 4 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x09</td>
      <td>ZONE5_VOL</td>
      <td colspan=8, td align='center'>Zone 5 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0A</td>
      <td>ZONE6_VOL</td>
      <td colspan=8, td align='center'>Zone 6 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0B</td>
      <td>POWER</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">EN_12V</td>
      <td style="text-align:center">PG_12V</td>
      <td style="text-align:center">EN_9V</td>
      <td style="text-align:center">PG_9V</td>
      <td style="text-align:center">0x0A</td>
    </tr>
    <tr>
      <td>0x0C</td>
      <td>FANS</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">FAILED</td>
      <td style="text-align:center">OVR_TMP</td>
      <td colspan=2, td align='center'>CTRL_METHOD</td>
      <td style="text-align:center">ON</td>
      <td style="text-align:center">OVERRIDE</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0D</td>
      <td>LED_CTRL</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">OVERRIDE</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0E</td>
      <td>LED_VAL</td>
      <td style="text-align:center">ZONE6</td>
      <td style="text-align:center">ZONE5</td>
      <td style="text-align:center">ZONE4</td>
      <td style="text-align:center">ZONE3</td>
      <td style="text-align:center">ZONE2</td>
      <td style="text-align:center">ZONE1</td>
      <td style="text-align:center">STAT_RED</td>
      <td style="text-align:center">STAT_GRN</td>
      <td style="text-align:center">0x02</td>
    </tr>
    <tr>
      <td>0x0F</td>
      <td>EXPANSION</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">UART_PASS</td>
      <td style="text-align:center">BOOT0</td>
      <td style="text-align:center">NRST</td>
      <td style="text-align:center">0x01</td>
    </tr>
    <tr>
      <td>0x10</td>
      <td>HV1_VOLTAGE</td>
      <td colspan=8, td align='center'>Power supply voltage, unsigned with 2 fractional bits</td>
      <td style="text-align:center">N/A</td>
    </tr>
    <tr>
      <td>0x11</td>
      <td>AMP_TEMP1</td>
      <td colspan=8, td align='center'>Temperature of heatsink over amps 1-3 in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x12</td>
      <td>HV1_TEMP</td>
      <td colspan=8, td align='center'>Temperature of power supply in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x13</td>
      <td>AMP_TEMP2</td>
      <td colspan=8, td align='center'>Temperature of heatsink over amps 4-6 in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td></td>
      <td></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
    </tr>
      <td>0xFA</td>
      <td>VER_MAJOR</td>
      <td colspan=8, td align='center'>Major Version Number</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFB</td>
      <td>VER_MINOR</td>
      <td colspan=8, td align='center'>Minor Version Number</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFC</td>
      <td>HASH1</td>
      <td colspan=8, td align='center'>GIT_HASH[27:20]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFD</td>
      <td>HASH2</td>
      <td colspan=8, td align='center'>GIT_HASH[19:12]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFE</td>
      <td>HASH3</td>
      <td colspan=8, td align='center'>GIT_HASH[11:4]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFF</td>
      <td>HASH4</td>
      <td colspan=4, td align='center'>GIT_HASH[3:0]</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">DIRTY</td>
      <td style="text-align:center">N/A</td>
    </tr>
  </tbody>
</table>

## Registers

### SRC_AD

Read/write.
Switch each source between analog and digital sources.
Each bit SRCxAD can have the following values:

| Value | Description |
| ----- | ----------- |
| 0     | Analog      |
| 1     | Digital     |

### ZONExxx_SRC

Read/write.
For each zone specify the source it is to be connected to.
Each 2-bit ZxSRC can have the following values:

| Value | Description  |
| ----- | ------------ |
| 0     | Use Source 0 |
| 1     | Use Source 1 |
| 2     | Use Source 2 |
| 3     | Use Source 3 |

### MUTE

Read/write.
Mute each zone independently. Each bit ZxM can have the following values:

| Value | Description |
| ----- | ----------- |
| 0     | Not Muted   |
| 1     | Muted       |

### STANDBY

Read/write.
Set bit 0 to standby all zones. Read to determine standby status.
All amplifiers will be in standby at once, or all enabled.

| Value | Description |
| ----- | ----------- |
| 0     | Enabled     |
| 1     | In Standby  |

### ZONE[1:6]_VOL

Read/write.
Control the attenuation (volume) in dB of each zone independently.
Valid range is between 0 and 79 inclusive, where 0 corresponds to 0 dB
attenuation and 79 corresponds to -79 dB of attenuation.
Values outside this will be saturated to the range [0, 79].

### POWER

Check the status of the two power supplies.
The 12 V supply runs the fans, while 9 V is used for audio power.

EN_xV are read/write, PG_xV are read-only.
EN_9V/PG_9V is only present on prototype power boards, on all others
the 9 V supply is always on.

| PG_9V | Description |
| ----- | ----------- |
| 0     | 9 V bad     |
| 1     | 9 V good    |

| EN_9V | Description |
| ----- | ----------- |
| 0     | 9 V on      |
| 1     | 9 V off     |

| PG_12V | Description |
| ------ | ----------- |
| 0      | 12 V bad    |
| 1      | 12 V good   |

| EN_12V | Description |
| ------ | ----------- |
| 0      | 12 V on     |
| 1      | 12 V off    |

### FANS

Check fan status and override the fan operation.
OVERRIDE is read/write, the rest of the bits are read only.

| OVERRIDE | Description |
| -------- | ----------- |
| 0        | Auto        |
| 1        | On          |

* The fans can be forced to 100% on with this bit.
  By default an automatic temperature-based control is used,
  see the CTRL_METHOD bit.

| ON | Description |
| -- | ----------- |
| 0  | Fans off    |
| 1  | Fans on     |

| CTRL_METHOD | Description |
| ----------- | ----------- |
| 0           | MAX6644     |
| 1           | ON_OFF      |
| 2           | Reserved    |
| 3           | Reserved    |

* MAX6644: Power Board 2.A used a MAX6644 fan controller. This board version
  is auto-detected and fan control handled by that IC.
* ON_OFF: Newer hardware moves the fan control into the STM32 on the Preamp Board.
  The fans will turn on above a threshold temp based on all measured tempuratures.

| OVR_TEMP | Description |
| -------- | ----------- |
| 0        | Temp OK     |
| 1        | Over temp   |

| FAILED | Description |
| ------ | ----------- |
| 0      | Normal      |
| 1      | Fans failed |

* Fan failed status only present with MAX6644

### LED_CTRL / LED_VAL

If OVERRIDE is cleared the front-panel LEDs will display the AmpliPi's
hardware status.
STAT_RED blinks at 0.5 Hz until the preamp receives an I2C address,
then it remains on if the amplifiers are in standby.
STAT_GREEN lights if the amplifiers are on.
The 6 zone status LEDs light if the respective zone is unmuted.

If OVERRIDE is set the front-panel LEDs will display the value in the LED_VAL
register.

### EXPANSION

Used to control the expansion port.
NRST and BOOT0 directly control those hardware pins going to the expansion unit.
NRST pulses low at boot to reset the next expander if present,
then it remains high.
BOOT0 defaults low, but is set high during programming to put the
expansion unit's preamp into bootloader mode.

If UART_PASS is set any data received on UART1 is forwarded to UART2 and vice-versa.
This enables programming of expansion units by setting all previous units
as pass-through.

## ADC REGISTERS ##

### HV1_VOLTAGE

Measures the 24V high-voltage power supply voltage.
The value is reported as an unsigned fixed-point number with 2 fractional bits,
with units of Volts.
So a value of 0x63 equates to a voltage of 0x63 / 4 = 24.75 V

### HV1_TEMP

Measures the thermistor attached to the 24V high-voltage power supply.
The value is reported as an unsigned fixed-point number with 1 fractional bit,
with units of &deg;C.
There is also a 20 &deg;C offset added to keep the value positive.
So a value of 0x5A equates to a temperature of 0x5A/2 - 20 = 25 &deg;C

The minimum temperature reported is -19.5 &deg;C and the maximum is 107 &deg;C
The values 0x00 and 0xFF are both invalid as temperatures:
a value of 0x00 represents a disconnected thermistor, and
a value of 0xFF represents a short.

### AMP_TEMP[1:2]

Measures the thermistors under the amplifier heatsinks.
AMP_TEMP1 measures the heatsink for amplifiers 1-3 and
AMP_TEMP2 measures the heatsink for amplifiers 4-6.
The value is reported the same as for the HV1_TEMP register:
an unsigned fixed-point number with 1 fractional bit with units of &deg;C.

## VERSION REGISTERS ##

### VER_MAJOR / VER_MINOR

These registers hold the human-readable firmware version.
Both are unsigned, 8-bit numbers.

### HASH[1:4]

Holds the 28-bit short Git hash of the commit used to generate the binary.
Use `git rev-parse --short HEAD` to get the short Git hash for the current commit.

If the DIRTY bit is set, the firmware is not aligned to any particular Git commit
and the hash should be ignored.
