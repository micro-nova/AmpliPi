# I2C Registers

## Register interface

<table>
  <thead>
    <tr>
      <th>Reg Address</th>
      <th style="text-align:center">Reg Name</th>
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
      <td style="text-align:center">SRC_AD_REG</td>
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
      <td style="text-align:center">CH123_SRC_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">- <td colspan=2, td align='center'>CH3SRC </td> <td colspan=2, td align='center'>CH2SRC </td><td colspan=2, td align='center'>CH1SRC  </td></td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x02</td>
      <td style="text-align:center">CH456_SRC_REG</td>
      <td style="text-align:center">-</td>
      <td style="text-align:center">- <td colspan=2, td align='center'>CH6SRC <td colspan=2, td align='center'>CH5SRC <td colspan=2, td align='center'>CH4SRC</td>
      <td style="text-align:center">0x00</td>
    </tr>
    <tr>
      <td>0x03</td>
      <td style="text-align:center">MUTE_REG</td>
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
      <td style="text-align:center">STANDBY_REG</td>
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
      <td style="text-align:center">CH1_ATTEN_REG <td colspan=8, td align='center'>Ch1 Attenuation </td></td>
      <td style="text-align:center">0x4F</td>
    </tr>
    <tr>
      <td>0x06</td>
      <td style="text-align:center">CH2_ATTEN_REG <td colspan=8, td align='center'>Ch2 Attenuation </td></td>
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
