# I2C Registers

## Register interface

<table>
  <thead>
    <tr>
      <th style="text-align:left">Reg Address</th>
      <th style="text-align:left">Reg Name</th>
      <th style="text-align:center">bit 7</th>
      <th style="text-align:center">bit 6</th>
      <th style="text-align:center">bit 5</th>
      <th style="text-align:center">bit 4</th>
      <th style="text-align:center">bit 3</th>
      <th style="text-align:center">bit 2</th>
      <th style="text-align:center">bit 1</th>
      <th style="text-align:center">bit 0</th>
      <th style="text-align:center">Default value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>0x00</td>
      <td style="text-align:left">SRC_AD</td>
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
      <td style="text-align:left">ZONE123_SRC</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td colspan=2, td align='center'>Z3SRC</td>
      <td colspan=2, td align='center'>Z2SRC</td>
      <td colspan=2, td align='center'>Z1SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x02</td>
      <td style="text-align:left">ZONE456_SRC</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td colspan=2, td align='center'>Z6SRC</td>
      <td colspan=2, td align='center'>Z5SRC</td>
      <td colspan=2, td align='center'>Z4SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x03</td>
      <td style="text-align:left">MUTE</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">Z6M</td>
      <td style="text-align:center">0x3F</td>
    </tr>
    <tr>
      <td>0x04</td>
      <td style="text-align:left">STANDBY</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">Z6STBY</td>
      <td style="text-align:center">Z5STBY</td>
      <td style="text-align:center">Z4STBY</td>
      <td style="text-align:center">Z3STBY</td>
      <td style="text-align:center">Z2STBY</td>
      <td style="text-align:center">Z1STBY</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x05</td>
      <td style="text-align:left">ZONE1_VOL</td>
      <td colspan=8, td align='center'>Zone 1 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x06</td>
      <td style="text-align:left">ZONE2_VOL</td>
      <td colspan=8, td align='center'>Zone 2 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x07</td>
      <td style="text-align:left">ZONE3_VOL</td>
      <td colspan=8, td align='center'>Zone 3 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x08</td>
      <td style="text-align:left">ZONE4_VOL</td>
      <td colspan=8, td align='center'>Zone 4 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x09</td>
      <td style="text-align:left">ZONE5_VOL</td>
      <td colspan=8, td align='center'>Zone 5 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0A</td>
      <td style="text-align:left">ZONE6_VOL</td>
      <td colspan=8, td align='center'>Zone 6 Attenuation</td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0B</td>
      <td style="text-align:left">POWER_STATUS</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">FAN_FAIL</td>
      <td colspan=2, td align='center'>FAN_CTRL</td>
      <td style="text-align:center">FAN_ON</td>
      <td style="text-align:center">OVR_TMP</td>
      <td style="text-align:center">EN_12V</td>
      <td style="text-align:center">PG_12V</td>
      <td style="text-align:center">0x02</td>
    </tr>
    <tr>
      <td>0x0C</td>
      <td style="text-align:left">FAN_CTRL</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">FAN_OVERRIDE</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0D</td>
      <td style="text-align:left">LED_CTRL</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">LED_OVERRIDE</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0E</td>
      <td style="text-align:left">LED_VAL</td>
      <td style="text-align:center">ZONE_6</td>
      <td style="text-align:center">ZONE_5</td>
      <td style="text-align:center">ZONE_4</td>
      <td style="text-align:center">ZONE_3</td>
      <td style="text-align:center">ZONE_2</td>
      <td style="text-align:center">ZONE_1</td>
      <td style="text-align:center">STAT_RED</td>
      <td style="text-align:center">STAT_GRN</td>
      <td style="text-align:center">0x02</td>
    </tr>
    <tr>
      <td>0x0F</td>
      <td style="text-align:left">EXPANSION</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">UART_PASSTHROUGH</td>
      <td style="text-align:center">BOOT0</td>
      <td style="text-align:center">NRST</td>
      <td style="text-align:center">0x01</td>
    </tr>
    <tr>
      <td>0x10</td>
      <td style="text-align:left">HV1_VOLTAGE</td>
      <td colspan=8, td align='center'>Power supply voltage, unsigned with 2 fractional bits</td>
      <td style="text-align:center">N/A</td>
    </tr>
    <tr>
      <td>0x11</td>
      <td style="text-align:left">AMP_TEMP1</td>
      <td colspan=8, td align='center'>Temperature of heatsink over amps 1-3 in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x12</td>
      <td style="text-align:left">HV1_TEMP</td>
      <td colspan=8, td align='center'>Temperature of power supply in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x13</td>
      <td style="text-align:left">AMP_TEMP2</td>
      <td colspan=8, td align='center'>Temperature of heatsink over amps 4-6 in degrees C, unsigned with 1 fractional bit</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td></td>
      <td style="text-align:left"></td>
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
      <td style="text-align:left">VER_MAJOR</td>
      <td colspan=8, td align='center'>Major Version Number</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFB</td>
      <td style="text-align:left">VER_MINOR</td>
      <td colspan=8, td align='center'>Minor Version Number</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFC</td>
      <td style="text-align:left">HASH1</td>
      <td colspan=8, td align='center'>GIT_HASH[27:20]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFD</td>
      <td style="text-align:left">HASH2</td>
      <td colspan=8, td align='center'>GIT_HASH[19:12]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFE</td>
      <td style="text-align:left">HASH3</td>
      <td colspan=8, td align='center'>GIT_HASH[11:4]</td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFF</td>
      <td style="text-align:left">HASH4</td>
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

### SRC_AD_REG

Switch each source between analog and digital sources. Each bit SRCxAD can have the following values.

| Value | Description |
| ----- | ----------- |
| 0 | Analog |
| 1 | Digital |

### CHxxx_SRC_REG

For each channel (zone) specify the source it is connected to. Each 2-bit CHxSRC can have the following values.

| Value | Description |
| ----- | ----------- |
| 0 | Use Source 0 |
| 1 | Use Source 1 |
| 2 | Use Source 2 |
| 3 | Use Source 3 |

### MUTE_REG

Mute each channel (zone) independently. Each bit CHxM can have the following values.

| Value | Description |
| ----- | ----------- |
| 0 | Not Muted |
| 1 | Muted |

### STANDBY_REG

Standby each channel (zone) independently. Each bit CHxSTBY can have the following values.

| Value | Description |
| ----- | ----------- |
| 0 | Enabled |
| 1 | In Standby |

### CHx_ATTEN_REG

Control the attenuation (volume) in dB of each channel (zone) independently. Valid range is between 0 and 79 inclusive, where 0 corresponds to 0dB attenuation and 79 corresponds to -79dB of attenuation. Values outside this range will be saturated to 79 (-79dB).

### POWER_GOOD

Read-only. Check the power status of the two power supplies. 12V power runs the fans, while 9V is the audio power.

| Value | Description |
| ----- | ----------- |
| 0 | Not Good |
| 1 | Good |

### FAN_STATUS

Check fan status and override the fan operation. Write 0x01 to this register to turn the fans fully on, or write 0x00 to release them.

FAN_OVERRIDE:
| Value | Description |
| ----- | ----------- |
| 0 | Normal |
| 1 | Fully on |

OVR_TEMP:
| Value | Description |
| ----- | ----------- |
| 0 | Normal |
| 1 | Over temp |

FAN_FAIL:
| Value | Description |
| ----- | ----------- |
| 0 | Normal |
| 1 | Failure |

### EXTERNAL_GPIO

An external GPIO for whatever you want. Set it by writing 0x00 or 0x01; reading will also return either 0x00 or 0x01.

| Value | Description |
| ----- | ----------- |
| 0 | Low |
| 1 | High |

### LED_OVERRIDE

Direct control of front panel LEDs.

| Value | Description |
| ----- | ----------- |
| 0 | Off |
| 1 | On |

## ADC REGISTERS ##

### HVx_VOLTAGE

This register reports a hex value based on the connected voltage. Looking at the decimal value from 0-255, each bit change roughly equates to 0.2883V. Following this, a decimal value of 84, or 54 in hex, will be pretty close to 24V.

### HVx_TEMP

This register has an operating range from around 4-237 in decimal, corresponding to a range of -40 to 125 degrees Celsius. The direct translation is a resistance, since the temperature sensor is a thermistor. Using a temp vs. resistance look-up-table on the NCP21XV103J03RA datasheet, the temperature can be determined.

Resistance in kilo-ohms is calculated by taking the decimal value read from the register, dividing 255 by that value, and multiplying the resultant by 4.7. A typical reading, say 25 degrees C, would be 0x51.

## VERSION REGISTERS ##

### version_major/minor

These registers hold the human-readable firmware version. For version 1.1, each register reports 0x01.

### git_hash[x:y]

These registers hold two digits each of the seven digit git_hash associated with each Git commit. Reading from each of these returns the hex digits that can be seen on GitHub.

### git_hash & git_status

This register is different in that the upper hex digit is part of the git hash, while the lower digit is the clean/dirty flag. For git hash f46612d:

| Value | Description |
| ----- | ----------- |
| 0xd0 | clean |
| 0xd1 | dirty |
