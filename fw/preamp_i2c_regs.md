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
      <th style="text-align:center">Default value in hex</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>0x00</td>
      <td style="text-align:left">SRC_AD_REG</td>
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
      <td style="text-align:left">CH123_SRC_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">- <td colspan=2, td align='center'>CH3SRC </td> <td colspan=2, td align='center'>CH2SRC </td><td colspan=2, td align='center'>CH1SRC  </td></td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x02</td>
      <td style="text-align:left">CH456_SRC_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">- <td colspan=2, td align='center'>CH6SRC <td colspan=2, td align='center'>CH5SRC <td colspan=2, td align='center'>CH4SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x03</td>
      <td style="text-align:left">MUTE_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">CH6M</td>
      <td style="text-align:center">0x3F</td>
    </tr>
    <tr>
      <td>0x04</td>
      <td style="text-align:left">STANDBY_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">CH6STBY</td>
      <td style="text-align:center">CH5STBY</td>
      <td style="text-align:center">CH4STBY</td>
      <td style="text-align:center">CH3STBY</td>
      <td style="text-align:center">CH2STBY</td>
      <td style="text-align:center">CH1STBY</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x05</td>
      <td style="text-align:left">CH1_ATTEN_REG <td colspan=8, td align='center'>Ch1 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x06</td>
      <td style="text-align:left">CH2_ATTEN_REG <td colspan=8, td align='center'>Ch2 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x07</td>
      <td style="text-align:center">CH3_ATTEN_REG <td colspan=8, td align='center'>Ch3 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x08</td>
      <td style="text-align:center">CH4_ATTEN_REG <td colspan=8, td align='center'>Ch4 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x09</td>
      <td style="text-align:center">CH5_ATTEN_REG <td colspan=8, td align='center'>Ch5 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0A</td>
      <td style="text-align:center">CH6_ATTEN_REG <td colspan=8, td align='center'>Ch6 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x0B</td>
      <td style="text-align:left">POWER_GOOD</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">PG_12V</td>
      <td style="text-align:center">PG_9V</td>
      <td style="text-align:center">0x03</td>
    </tr>
    <tr>
      <td>0x0C</td>
      <td style="text-align:left">FAN_STATUS</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">FAN_OVERRIDE</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">OVR_TMP</td>
      <td style="text-align:center">FAN_FAIL</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0D</td>
      <td style="text-align:left">EXTERNAL GPIO</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">EXT_GPIO</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x0E</td>
      <td style="text-align:left">LED_OVERRIDE</td>
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
    <tr>
      <td>0x10</td>
      <td style="text-align:left">HV1_VOLTAGE <td colspan=8, td align='center'>byte value from 0-255 corresponding to HV1 voltage</td></td>
      <td style="text-align:center">N/A</td>
    </tr>
    <tr>
      <td>0x11</td>
      <td style="text-align:left">HV2_VOLTAGE <td colspan=8, td align='center'>byte value from 0-255 corresponding to HV2 voltage</td></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x12</td>
      <td style="text-align:left">HV1_TEMP<td colspan=8, td align='center'>byte value from 0-255 corresponding to HV1 temp</td></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0x13</td>
      <td style="text-align:left">HV2_TEMP<td colspan=8, td align='center'>byte value from 0-255 corresponding to HV2 temp</td></td>
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
      <td style="text-align:left">version_major[7:0]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFB</td>
      <td style="text-align:left">version_minor[7:0]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFC</td>
      <td style="text-align:left">git_hash[27:20]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFD</td>
      <td style="text-align:left">git_hash[19:12]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFE</td>
      <td style="text-align:left">git_hash[11:4]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center">N/A</td>
    </tr>
      <td>0xFF</td>
      <td style="text-align:left">git_hash[3:0] & git_status[3:0]</td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
      <td style="text-align:center"></td>
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
