#!/usr/bin/env python3
#
# Generate look-up tables for the various thermistors in the amplipi system.
#
# There are two types of thermistors: a generic thermistor (B=3950, +/-1%) and two NCP21XV103J03RA (B=3900, 3%) placed
# under the amp heatsinks. Newer hardware has two SDNT2012X103F3950FTF (B=3950, 1%) placed under the amp heatsinks.
#
# From the B value a LUT can be generated, but in addition the NCP21XV103J03RA provides a low-res LUT in its datasheet.
# After reviewing the differences between the different B values and the provided LUT, the max difference in calculated
# temps between tables is low so for the sake of simplicity only 1 table is used for both thermistors.

import math
try:
  import matplotlib.pyplot as plt
  PLOT = True
except:
  PLOT = False

# The PSU thermistor only gives B-value, no table
R0 = 10
T0 = 25
B_PSU = 3950
B_NCP = 3950
B_NCP_OLD = 3900
K2C = 273.15


def temp2r(temp: float, b: int) -> float:
  """ Thermocouple resistance = R0*e^[B*(1/T - 1/T0)] = Rt """
  return R0 * math.exp(b * (1 / (temp + K2C) - 1 / (T0 + K2C)))


def r2temp(rt: float, b: int) -> float:
  """ T = 1/(ln(Rt/R0)/B + 1/T0) """
  return 1 / (math.log(rt / R0, math.e) / b + 1 / (T0 + K2C)) - K2C


def adc2temp(adc_val: int, b: int) -> float:
  """ ADC_VAL = 3.3V * 4.7kOhm / (4.7kOhm + Rt kOhm) / 3.3V * 255
      Rt = 4.7 * (255 / ADC_VAL - 1)
      T = 1/(ln(Rt/R0)/B + 1/T0)
      T = 1/(ln(Rt/10)/3900 + 1/(25+273.15)) - 273.15
  """
  MAXR = temp2r(-20, b)  # Resistance in kOhms @ -20C
  MINR = temp2r(107, b)  # Resistance in kOhms @ 107C
  MIN_VAL = math.ceil(255 * 4.7 / (MAXR + 4.7))   # 11
  MAX_VAL = math.floor(255 * 4.7 / (MINR + 4.7))  # 227
  if adc_val < MIN_VAL:
    temp = 0
  elif adc_val > MAX_VAL:
    temp = 255
  else:
    rt = 4.7 * (255 / adc_val - 1)
    f_temp = r2temp(rt, b)
    temp = 2 * (f_temp + 20)  # [UQ7.1 + 20] degC format
  return temp


THERM_LUT_PSU = [round(adc2temp(x, B_PSU)) for x in range(256)]


R2C_LUT_NCP = {
  95.327: -20,
  71.746: -15,
  54.564: -10,
  41.813: -5,
  32.330: 0,
  25.194: 5,
  19.785: 10,
  15.651: 15,
  12.468: 20,
  10.000: 25,
  8.072: 30,
  6.556: 35,
  5.356: 40,
  4.401: 45,
  3.635: 50,
  3.019: 55,
  2.521: 60,
  2.115: 65,
  1.781: 70,
  1.509: 75,
  1.284: 80,
  1.097: 85,
  0.941: 90,
  0.810: 95,
  0.701: 100,
  0.608: 105,
  0.53: 110,
}


def temp2r_interp(temp: float) -> float:
  for r, t in R2C_LUT_NCP.items():
    if temp < t:
      ti = (temp - tp) / (t - tp)
      ri = ti * (r - rp) + rp
      break
    rp = r
    tp = t
  return ri


def r2temp_interp(rt: float) -> float:
  """ The NCP21XV103J03RA thermistors under the amplifier heatsinks
      give a table to interpolate from.
  """
  # Search for the slot in the table to interpolate between
  for r, t in R2C_LUT_NCP.items():
    if rt > r:
      ri = (rt - rp) / (r - rp)
      temp = ri * (t - tp) + tp
      break
    rp = r
    tp = t

  return temp


def adc2temp_interp(adc_val: int) -> float:
  """ Interpolate from the datasheet's small degC->Ohms LUT """
  # Handle adc_val=0 which causes divide-by-zero
  if adc_val < 1:
    return 0

  MAXR = temp2r_interp(-20)  # Resistance in kOhms @ -20C
  MINR = temp2r_interp(107)  # Resistance in kOhms @ 110C
  rt = 4.7 * (255 / adc_val - 1)
  if rt > MAXR:
    temp = 0
  elif rt < MINR:
    temp = 255
  else:
    f_temp = r2temp_interp(rt)
    temp = 2 * (f_temp + 20)  # [UQ7.1 + 20] degC format
  return temp


THERM_LUT_NCP = [round(adc2temp_interp(x)) for x in range(256)]
THERM_LUT_NCP_B = [round(adc2temp(x, B_NCP)) for x in range(256)]
THERM_LUT_NCP_B_OLD = [round(adc2temp(x, B_NCP_OLD)) for x in range(256)]

# THERM_LUT_NCP_B_OLD errs slightly on the side of warmer, but is no more than 1.5 degC different than any other LUT
# print(max(t2 - t1 for t1, t2 in zip(THERM_LUT_NCP_B[30:-1], THERM_LUT_NCP_B_OLD[30:-1])))

print('const uint8_t THERM_LUT_[] = {')
for row in range(16):
  print('  ', end='')
  for col in range(16):
    print(f'0x{THERM_LUT_NCP_B[row*16 + col]:02X}, ', end='')
  print()
print('};')

if PLOT:
  plt.plot(THERM_LUT_PSU, label='PSU')
  plt.plot(THERM_LUT_NCP, label='NCP_LUT')
  plt.plot(THERM_LUT_NCP_B, label='NCP_B')
  plt.legend()
  plt.ylabel('2*(Temp + 20)')
  plt.xlabel('ADC Value')
  plt.show()
