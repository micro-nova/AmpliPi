# I2C Calculations

## Bus Capacitance and Rise/Fall Times
| Device           | Capacitance (pF) |
| ---------------- | ---------------- |
| STM32            | 5                |
| MAX11601 (ADC)   | 15               |
| MCP23008 (Power) | ??               |
| MCP23008 (LEDs)  | ??               |
| MCP4017 (DPot)   | 10               |
| TDA7448 (Vol1)   | ??               |
| TDA7448 (Vol2)   | ??               |

~70 pF for all devices, plus say ~20 pF for all traces and wires = ~90 pF
Rise time t_r:
```
t_r = 0.8473*Rp*Cb ~= 0.8473 * 1 kOhm * 90 pF = 76 ns
```

Measured rise time: **t_r = 72 ns**.
Measured fall time: **t_f = 4 ns**.

## Pullup Resistor Values
Max output current for I2C Standard/Fast mode is 3 mA, so min pullup is:
```
Rp_min > [V_DD - V_OL(max)] / I_OL = (3.3 V - 0.4 V) / 3 mA = 967 Ohms
```

Max bus capacitance (with only resistor for pullup) is 200 pF.
Standard mode rise-time t_r(max) = 1000 ns.
```
Rp_std < t_r(max) / (0.8473 * Cb) = 1000 / (0.8473 * 0.2) = 5901 Ohm
```

Fast mode rise-time t_r(max) = 300 ns.
```
Rp_fast < t_r(max) / (0.8473 * Cb) = 1000 / (0.8473 * 0.2) = 1770 Ohm
```

For Standard mode: **1k <= Rp <= 5.6k**.
For Fast mode: **1k <= Rp <= 1.6k**.

## I2C Timing
### Common parameters
```
t_I2CCLK = 1 / 8 MHz = 125 ns
t_AF(min) = 50 ns   - Analog filter minimum input delay
t_AF(max) = 260 ns  - Analog filter maximum input delay
t_DNF = 0           - Digital filter input delay
t_r = 72 ns         - Rise time
                      For Standard mode (100 kHz), rise time < 1000 ns
                      For Fast mode (400 kHz), rise time < 300 ns
t_f = 4 ns          - Fall time (must be < 300 ns)

t_SYNC1(min) = t_f + t_AF(min) + t_DNF + 2*t_I2CCLK
             = 4 + 50 + 2*125 = 306 ns
t_SYNC2(min) = t_r + t_AF(min) + t_DNF + 2*t_I2CCLK
             = 76 + 50 + 2*125 = 376 ns
```

### Standard mode, max 100 kHz
```
t_LOW > 4.7 us,t_HIGH > 4 us
t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (4700 - 50) / 4 = 1162.5 ns
t_I2CCLK < t_HIGH = 4000 ns
Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
SDADEL >= [4 - 50 - 375] / 125 = -3.368 < 0, so SDASEL >= 0
SDADEL <= [t_VD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
SDADEL <= (3450 - 72 - 260 - 500) / 125 = 20.944
SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
SCLDEL >= (72 + 250) / 125 - 1 = 1.576
So 0 <= SDADEL <= 20, SCLDEL >= 2
I2C_TIMINGR[31:16] = 0x0020

t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
4000 <= 50 + 2*125 + 125*(SCLH + 1)
3575 <= 125*SCLH
SCLH >= 28.6 = 0x1D

t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
4700 <= 50 + 2*125 + 125*(SCLL + 1)
4275 <= 125*SCLL
SCLL >= 34.2 = 0x23

Need to stay under 100 kHz in "worst" case. Keep SCLH at min,
but here we determine final SCLL.
t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 10000 ns (100 kHz max)
t_LOW + t_HIGH >= 10000 - 304 - 372 ns = 9324 ns
t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 9324 ns
125*(SCLL + 1) + 125*30 >= 9324 ns
SCLL >= 43.592 = 0x2C

I2C_TIMINGR[31:0] = 0x00101D2C
```

## Fast mode, max 400 kHz
```
t_LOW > 1.3 us, t_HIGH > 0.6 us
t_I2CCLK < [t_LOW - t_AF(min) - t_DNF] / 4 = (1300 - 50) / 4 = 312.5 ns
t_I2CCLK < t_HIGH = 600 ns
Set PRESC = 0, so t_I2CCLK = 1 / 8 MHz = 125 ns
t_PRESC = t_I2CCLK / (PRESC + 1) = 125 / (0 + 1) = 125 ns
SDADEL >= [t_f + t_HD;DAT(min) - t_AF(min) - t_DNF - 3*t_I2CCLK] / t_PRESC
SDADEL >= [4 - 50 - 375] / 125 = -3.368 < 0, so SDASEL >= 0
SDADEL <= [t_VD;DAT(max) - t_r - t_AF(max) - t_DNF - 4*t_I2CCLK] / t_PRESC
SDADEL <= (900 - 72 - 260 - 500) / 125 = 0.544
SCLDEL >= {[t_r + t_SU;DAT(min)] / t_PRESC} - 1
SCLDEL >= (72 + 100) / 125 - 1 = 0.376
So 0 <= SDADEL <= 0, SCLDEL >= 1
I2C_TIMINGR[31:16] = 0x0010

t_HIGH(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLH + 1)
600 <= 50 + 2*125 + 125*(SCLH + 1)
175 <= 125*SCLH
SCLH >= 1.4 = 0x02

t_LOW(min) <= t_AF(min) + t_DNF + 2*t_I2CCLK + t_PRESC*(SCLL + 1)
1300 <= 50 + 2*125 + 125*(SCLL + 1)
875 <= 125*SCLL
SCLL >= 7 = 0x07

Need to stay under 400 kHz in "worst" case. Keep SCLH at min,
but here we determine final SCLL.
t_SCL = t_SYNC1 + t_SYNC2 + t_LOW + t_HIGH >= 2500 ns (400 kHz max)
t_LOW + t_HIGH >= 2500 - 304 - 372 ns = 1824 ns
t_PRESC*(SCLL + 1) + t_PRESC*(SCLH + 1) >= 1824 ns
125*(SCLL + 1) + 125*3 >= 1824 ns
SCLL >= 10.592 = 0x0B

I2C_TIMINGR[31:0] = 0x0010020B
```
