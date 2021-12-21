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
    <tr><td align=center colspan=100%><b>Audio Control</b></td></tr>
    <tr>
      <td>0x00</td>
      <td>SRC_AD</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>SRC4AD</td>
      <td align=center>SRC3AD</td>
      <td align=center>SRC2AD</td>
      <td align=center>SRC1AD</td>
      <td>0x0F</td>
    </tr>
    <tr>
      <td>0x01</td>
      <td>ZONE123_SRC</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center colspan=2>Z3SRC</td>
      <td align=center colspan=2>Z2SRC</td>
      <td align=center colspan=2>Z1SRC</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x02</td>
      <td>ZONE456_SRC</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center colspan=2>Z6SRC</td>
      <td align=center colspan=2>Z5SRC</td>
      <td align=center colspan=2>Z4SRC</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x03</td>
      <td>MUTE</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>Z6M</td>
      <td align=center>Z5M</td>
      <td align=center>Z4M</td>
      <td align=center>Z3M</td>
      <td align=center>Z2M</td>
      <td align=center>Z1M</td>
      <td>0x3F</td>
    </tr>
    <tr>
      <td>0x04</td>
      <td>AMP ENABLE</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>Z6EN</td>
      <td align=center>Z5EN</td>
      <td align=center>Z4EN</td>
      <td align=center>Z3EN</td>
      <td align=center>Z2EN</td>
      <td align=center>Z1EN</td>
      <td>0x3F</td>
    </tr>
    <tr>
      <td>0x05</td>
      <td>ZONE1_VOL</td>
      <td align='center' colspan=8>Zone 1 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr>
      <td>0x06</td>
      <td>ZONE2_VOL</td>
      <td align='center' colspan=8>Zone 2 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr>
      <td>0x07</td>
      <td>ZONE3_VOL</td>
      <td align='center' colspan=8>Zone 3 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr>
      <td>0x08</td>
      <td>ZONE4_VOL</td>
      <td align='center' colspan=8>Zone 4 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr>
      <td>0x09</td>
      <td>ZONE5_VOL</td>
      <td align='center' colspan=8>Zone 5 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr>
      <td>0x0A</td>
      <td>ZONE6_VOL</td>
      <td align='center' colspan=8>Zone 6 Attenuation</td>
      <td>0x4F</td>
    </tr>
    <tr><td align=center colspan=100%><b>Power/Fan Control</b></td></tr>
    <tr>
      <td>0x0B</td>
      <td>POWER</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>EN_12V</td>
      <td align=center>PG_12V</td>
      <td align=center>EN_9V</td>
      <td align=center>PG_9V</td>
      <td>0x0A</td>
    </tr>
    <tr>
      <td>0x0C</td>
      <td>FANS</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>FAILED</td>
      <td align=center>OVR_TMP</td>
      <td align='center' colspan=2>CTRL_METHOD</td>
      <td align=center>ON</td>
      <td align=center>OVERRIDE</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x0D</td>
      <td>LED_CTRL</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>OVERRIDE</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x0E</td>
      <td>LED_VAL</td>
      <td align=center>ZONE6</td>
      <td align=center>ZONE5</td>
      <td align=center>ZONE4</td>
      <td align=center>ZONE3</td>
      <td align=center>ZONE2</td>
      <td align=center>ZONE1</td>
      <td align=center>STAT_RED</td>
      <td align=center>STAT_GRN</td>
      <td>0x02</td>
    </tr>
    <tr>
      <td>0x0F</td>
      <td>EXPANSION</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>UART_PASS</td>
      <td align=center>BOOT0</td>
      <td align=center>NRST</td>
      <td>0x01</td>
    </tr>
    <tr>
      <td>0x10</td>
      <td>HV1_VOLTAGE</td>
      <td align='center' colspan=8>Power supply voltage, unsigned with 2 fractional bits</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0x11</td>
      <td>AMP_TEMP1</td>
      <td align='center' colspan=8>Temperature of heatsink over amps 1-3 in degrees C, unsigned with 1 fractional bit</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0x12</td>
      <td>HV1_TEMP</td>
      <td align='center' colspan=8>Temperature of power supply in degrees C, unsigned with 1 fractional bit</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0x13</td>
      <td>AMP_TEMP2</td>
      <td align='center' colspan=8>Temperature of heatsink over amps 4-6 in degrees C, unsigned with 1 fractional bit</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0x14</td>
      <td>PI_TEMP</td>
      <td align='center' colspan=8>Temperature sent from the Raspberry Pi in degrees C, unsigned with 1 fractional bit</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x15</td>
      <td>FAN_DUTY</td>
      <td align='center' colspan=8>Fan duty cycle if PWM control is used</td>
      <td>0x00</td>
    </tr>
    <tr>
      <td>0x16</td>
      <td>FAN_VOLTS</td>
      <td align='center' colspan=8>Fan power supply in Volts, unsigned with 4 fractional bits</td>
      <td>0xC0</td>
    </tr>
    <tr><td align=center colspan=100%><b>Version Info</b></td></tr>
    <tr>
      <td>0xFA</td>
      <td>VER_MAJOR</td>
      <td align=center colspan=8>Major Version Number</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0xFB</td>
      <td>VER_MINOR</td>
      <td align=center colspan=8>Minor Version Number</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0xFC</td>
      <td>HASH1</td>
      <td align=center colspan=8>GIT_HASH[27:20]</td>
      <td>N/A</td>
    </tr>
      <td>0xFD</td>
      <td>HASH2</td>
      <td align=center colspan=8>GIT_HASH[19:12]</td>
      <td>N/A</td>
    </tr>
      <td>0xFE</td>
      <td>HASH3</td>
      <td align=center colspan=8>GIT_HASH[11:4]</td>
      <td>N/A</td>
    </tr>
    <tr>
      <td>0xFF</td>
      <td>HASH4</td>
      <td align=center colspan=4>GIT_HASH[3:0]</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>-</td>
      <td align=center>DIRTY</td>
      <td>N/A</td>
    </tr>
  </tbody>
</table>

## Audio Control Registers

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

### AMP ENABLE

Read/write.
Bits 0 to 5 enable/disable the amplifier for a zone. A disabled amplifier will
always remain muted, and won't be considered on for determining if all the
amplifiers can be placed into standby. By default all amplifiers are enabled,
but disabling an amplifier can be useful if only the preout is used for a zone.

| Value | Description       |
| ----- | ----------------- |
| 0     | Zone amp disabled |
| 1     | Zone amp enabled  |

Replaces STANDBY register. Old software will simply enable all zone amplifiers
instead of disabling standby.

### ZONE[1:6]_VOL

Read/write.
Control the attenuation (volume) in dB of each zone independently.
Valid range is between 0 and 79 inclusive, where 0 corresponds to 0 dB
attenuation and 79 corresponds to -79 dB of attenuation.
Values outside this will be saturated to the range [0, 79].

## Power and Fan Control Registers

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

Check fan status and optionally override the fan operation.
CTRL_METHOD is read/write, the rest of the bits are read only.

| CTRL_METHOD | Description |
| ----------- | ----------- |
| 0           | MAX6644     |
| 1           | PWM         |
| 2           | Linear      |
| 3           | Forced      |

* A read of these bits indicates the current fan control method.
  Writing a value of 3 to these bits forces the fans on.
  If any other value is written or this register is never written to,
  automatic detection of the proper fan control method is done:
  - MAX6644: Power Board 2.A used a MAX6644 fan controller. This board version
    is auto-detected and fan control handled by that IC.
  - PWM: Power Board 3.B moves the fan control into this firmware.
    With PWM the fans are either off or varied from 30% to 100%,
    based on the current system temperatures.
  - Linear: Power Board 4.A further improves fan control by allowing the fan
    power supply to be adjusted from about 6V to 12V. Similar to the PWM
    control method, the fans are either off or varied from 50% to 100%.
    Linear voltage control produces less audible noise from the fans.

| ON | Description |
| -- | ----------- |
| 0  | Fans off    |
| 1  | Fans on     |

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

If the power supply exceeds 40 &deg;C the fans will turn
on at their minimum value.
The fan speed will increase with temperature until above 55 &deg;C
when the fans will turn on 100%.

### AMP_TEMP[1:2]

Measures the thermistors under the amplifier heatsinks.
AMP_TEMP1 measures the heatsink for amplifiers 1-3 and
AMP_TEMP2 measures the heatsink for amplifiers 4-6.
The value is reported the same as for the HV1_TEMP register:
an unsigned fixed-point number with 1 fractional bit with units of &deg;C.

If either amplipier heatsink exceeds 45 &deg;C the fans will turn
on at their minimum value.
The fan speed will increase with temperature until above 60 &deg;C
when the fans will turn on 100%.

### PI_TEMP

The Raspberry Pi sends its temperature to this register.
If the Pi exceeds 60 &deg;C the fans will turn on at their minimum value.
At 80 &deg;C the fans will be at 100%.
The value is sent the same as for the HV1_TEMP register:
an unsigned fixed-point number with 1 fractional bit with units of &deg;C.

The highest fan speed demanded by each of the four temperatures measured (HV1_TEMP, AMP_TEMP1, AMP_TEMP2,
and PI_TEMP) is chosen to be the final fan speed that is set.

### FAN_DUTY

Reports the fan duty cycle as an unsigned percentage with 7 fractional bits.
If a MAX6644 fan control IC is present, this register will read 0x00.
If the fans are forced on the value will read 0x80 (100%).
If linear control is used the value will be 0x00 for fans off
or 0x80 for fans on.
If PWM control is used the value will be between 0x26 (30%) and 0x80.

### FAN_VOLTS

Reports the fan power supply voltage as unsigned Volts with 4 fractional bits.
If linear voltage control is not in use, this register will read 0xC0 (12 V).
Otherwise this register will read between 0x63 (6.1875 V) and
0xBF (11.9375 V).

## VERSION REGISTERS

### VER_MAJOR / VER_MINOR

These registers hold the human-readable firmware version.
Both are unsigned, 8-bit numbers.

### HASH[1:4]

Holds the 28-bit short Git hash of the commit used to generate the binary.
Use `git rev-parse --short HEAD` to get the short Git hash for the current commit.

If the DIRTY bit is set, the firmware is not aligned to any particular Git commit
and the hash should be ignored.
