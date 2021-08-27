/*
 * AmpliPi Home Audio
 * Copyright (C) 2021 MicroNova LLC
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
/*
 * Power Board Tester
 *
 * Designed to run on an Arduino Due.
 * This project verifies Power Board functionality independent of the rest of
 * the AmpliPi unit.
 * The 4 power rails are checked:
 *    +5VD, +12VD
 *    +5VA, +9VA
 * All I2C devices are verified:
 *    MAX11601 (0x64): 4-channel ADC measures HV1 and up to 3 thermistors
 *    MCP23008 (0x21): 8-channel GPIO expander. Currently only GP4/5/7 are used
 *    MCP4017  (0x2F): Digital potentiometer controlling +12VD
 * Slave addresses in parenthesis are 7-bit right-aligned, so will be shifted
 * left one bit when sent on the wire.
 *
 * I2C Bus connector for the LED board is tested as a loopback.
 *
 * Hardware required:
 *    Arduino Due
 *    +24V power supply
 *    +24/+12 DC/DC converter
 *    2 1-7k resistors
 *    X RGB LEDs plus any resistors required
 *
 * Connections
 *  +24V -+-> <24/12 DC/DC> -> Arduino Due barrel jack
 *        |
 *        +-> Power Board J1 Pin 1 and 3
 *
 *    Arduino Due | Power Board
 *  +-------------+------------------------+ Power
 *    GND         | GND/AGND*
 *    A0          | J4 pin 1: +5VA
 *    A1          | J4 pin 3: +5VD
 *    A2          | J5 pin 1: +9VA
 *    A3          | J5 pin 3: +5VA
 *    A4          | J8 pin 1: +9VA
 *  +-------------+------------------------+ I2C
 *    +3.3V       | J3 pin 1: +3.3VA
 *    SCL         | J3 pin 2: SCL
 *    SDA         | J3 pin 3: SDA
 *    GND         | J3 pin 4: AGND
 *    A5          | J2 pin 1: +3.3VA
 *    SCL1        | J2 pin 2: SCL     (out)
 *    SDA1        | J2 pin 3: SDA     (out)
 *    GND         | J2 pin 4: AGND
 *  +-------------+------------------------+ IO
 *    2     (out) | J6 pin 1: NTC1
 *    DAC0  (out) | J9 pin 2: DXP1
 *    DAC1  (out) | J9 pin 7: DXP2
 *    A6    (in)  | J9 pin 1: +3.3VA  (out)
 *    A7    (in)  | J9 pin 5: +12VD   (out)
 *    5     (out) | J9 pin 3: TACH1
 *    6     (out) | J9 pin 6: TACH2
 *    A8    (in)  | J9 pin 4: FAN_PWM (out)
 *  +-------------+------------------------+ Status LEDs
 *    23    (out) | LED (+3.3VA_J2)
 *    25    (out) | LED (+3.3VA_J9)
 *    27    (out) | LED (+5VA_J4)
 *    29    (out) | LED (+5VA_J5)
 *    31    (out) | LED (+9VA_J5)
 *    33    (out) | LED (+9VA_J8)
 *    35    (out) | LED (+5VD)
 *    37    (out) | LED (+12VD)
 *    39    (out) | LED (+24V)
 *    41    (out) | LED (Therm1)
 *    43    (out) | LED (Therm2)
 *    45    (out) | LED (Therm3)
 *    47    (out) | LED (FAN_PWM)
 *    49    (out) | LED (I2C Loopback)
 *  +-------------+------------------------+
 *    * This doesn't independently test all GND connections.
 *      Possibly differential measurements would solve that?
 *
 *  WIP Schematic: (TODO: Protection against shorts on power board)
 *
 *  +---------------------------------+
 *  | +-----------------------------+
 *  | |   _______________________                          ___________________
 *  | |  | PWR      USB     PROG |                        |                   |
 *  | |  |                       |                        |                   |
 *  | |  |=======================|                        |===================|
 *  | |  |          DUE          |                        |    Power Board    |
 *  | |  |=======================|                        |===================|
 *  | |  |                  SCL1 +                        | J2 I2C   Therm J6 |
 *  | +--+ 3.3-----+        SDA1 +                        | J3             J7 |
 *  +----+ GND     |        GND  +                        |                   |
 *       |         |             |                        | J9 Fans           |
 *       |         |             |                        |                   |
 *       |         |             |                        | J4 Power          |
 *       |         +-<1.5k>--SDA +--                      | J5                |
 *       |         |             |                        | J8                |
 *       |         +-<1.5k>--SCL +--                      |                   |
 *       |                       |                        |        +24V in J1 |
 *       |_______________________|                        |___________________|
 */

#include <Adafruit_ILI9341.h>
#include <Arduino.h>
#include <Wire.h>

#define TFT_CS       10
#define TFT_DC       11
#define TFT_SPI_FREQ (50 * 1000000)  // Default = 24 MHz
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);

#define TFT_WIDTH       320
#define TFT_HEIGHT      240
#define TFT_FONT_WIDTH  6
#define TFT_FONT_HEIGHT 8
#define TEXT_MARGIN     4

static constexpr uint8_t MAX_DPOT_VAL = 0x7F;
static constexpr uint8_t I2C_TEST_VAL = 0xA4;

enum SlaveAddr : uint8_t
{
  due  = 0x0F,
  gpio = 0x21,
  dpot = 0x2F,
  adc  = 0x64,
};

// I2C1 slave RX callback
bool i2c_loopback_ok_ = false;
void i2cSlaveRx(int rxBufLen) {
  // Assume rxBufLen > 0 and read a received byte
  uint8_t rx = Wire1.read();

  // Verify the received byte is the test byte that was sent
  i2c_loopback_ok_ = rx == I2C_TEST_VAL;

  SerialUSB.print("Got I2C byte 0x");
  SerialUSB.println(rx, HEX);
}

constexpr float adcToVolts(uint32_t adc_val, uint8_t bits, float v_ref,
                           float r_pulldown, float r_series) {
  float scale =
      v_ref * (r_pulldown + r_series) / r_pulldown / ((1 << bits) - 1);
  return scale * adc_val;
}

float adcToTemp(uint8_t ntc_adc) {
  if (ntc_adc == 0) {
    // 0 causes divide-by-zero
    return -INFINITY;
  } else if (ntc_adc == 255) {
    // 255 causes Rt=0 which leads to ln(0)
    return INFINITY;
  } else {
    float rt = 4.7 * (255 / (float)ntc_adc - 1);
    return 1.0 / (log(rt / 10) / 3900 + 1.0 / (25.0 + 273.5)) - 273.15;
  }
}

// Inputs are in the range [0,1]
uint16_t rgb565(float red, float green, float blue) {
  uint16_t r5 = (uint16_t)(abs(red) * ((1 << 5) - 1));
  uint16_t g6 = (uint16_t)(abs(green) * ((1 << 6) - 1));
  uint16_t b5 = (uint16_t)(abs(blue) * ((1 << 5) - 1));

  r5 = r5 >= (1 << 5) ? (1 << 5) - 1 : r5;
  g6 = g6 >= (1 << 6) ? (1 << 6) - 1 : g6;
  b5 = b5 >= (1 << 5) ? (1 << 5) - 1 : b5;

  return (r5 << 11) | (g6 << 5) | b5;
}

bool readI2CADC(uint8_t* ch0, uint8_t* ch1, uint8_t* ch2, uint8_t* ch3) {
  Wire.beginTransmission(SlaveAddr::adc);
  Wire.write((uint8_t)0b00000111);  // Send configuration byte, set CS=0x2
  Wire.endTransmission();

  Wire.requestFrom(SlaveAddr::adc, 4);
  if (Wire.available() >= 4) {
    *ch0 = (uint8_t)Wire.read();
    *ch1 = (uint8_t)Wire.read();
    *ch2 = (uint8_t)Wire.read();
    *ch3 = (uint8_t)Wire.read();
    return true;
  } else {
    *ch0 = 0;
    *ch1 = 0;
    *ch2 = 0;
    *ch3 = 0;
    return false;
  }
}

// N = test number, AKA what line # on the screen
template <uint8_t N>
void drawTest(const char* desc, const char* val1, bool ok1, const char* val2,
              bool ok2) {
  static constexpr uint8_t n1 = 12;  // Number of characters in first column
  static constexpr uint8_t n2 = 6;   // Number of characters in second column
  static constexpr uint8_t n3 = 6;   // Number of characters in third column

  // Font size (doubled)
  static constexpr int16_t fw = 2 * TFT_FONT_WIDTH;
  static constexpr int16_t fh = 2 * TFT_FONT_HEIGHT;

  // Column starts and ends
  static constexpr int16_t c1xl  = TEXT_MARGIN - 1;      // Leftmost pixel
  static constexpr int16_t c1xtl = c1xl + TEXT_MARGIN;   // Text start
  static constexpr int16_t c1xtr = c1xtl + n1 * fw;      // Text end
  static constexpr int16_t c1xr  = c1xtr + TEXT_MARGIN;  // Rightmost pixel
  static constexpr int16_t c2xl  = c1xr;
  static constexpr int16_t c2xtl = c2xl + TEXT_MARGIN;
  static constexpr int16_t c2xtr = c2xtl + n2 * fw;
  static constexpr int16_t c2xr  = c2xtr + TEXT_MARGIN;
  static constexpr int16_t c3xl  = c2xr;
  static constexpr int16_t c3xtl = c3xl + TEXT_MARGIN;
  static constexpr int16_t c3xtr = c3xtl + n3 * fw;
  static constexpr int16_t c3xr  = c3xtr + TEXT_MARGIN;

  // Row starts and ends
  static constexpr int16_t yt  = N * (fh + 2 * TEXT_MARGIN);  // Topmost pixel
  static constexpr int16_t ytt = yt + TEXT_MARGIN;            // Text start
  static constexpr int16_t ytb = ytt + fh;                    // Text end
  static constexpr int16_t yb  = ytb + TEXT_MARGIN;  // Bottommost pixel

  static bool init = true;
  if (init) {
    // Clear entire area
    tft.fillRect(c1xl, yt, c3xr - c1xl, yb - yt, ILI9341_BLACK);

    // Draw static text
    tft.setCursor(c1xtl, ytt);
    tft.setTextColor(ILI9341_WHITE);
    tft.println(desc);

    // Draw horizontal borders
    tft.drawLine(c1xl, yt, c3xr, yt, ILI9341_LIGHTGREY);
    tft.drawLine(c1xl, yb, c3xr, yb, ILI9341_LIGHTGREY);
    // Draw vertical borders
    tft.drawLine(c1xl, yt, c1xl, yb, ILI9341_LIGHTGREY);
    tft.drawLine(c2xl, yt, c2xl, yb, ILI9341_LIGHTGREY);
    tft.drawLine(c3xl, yt, c3xl, yb, ILI9341_LIGHTGREY);
    tft.drawLine(c3xr, yt, c3xr, yb, ILI9341_LIGHTGREY);
    init = false;
  } else {
    // Clear the area that will be re-written with voltage text
    tft.fillRect(c2xtl, ytt, n2 * fw, fh, ILI9341_BLACK);
    tft.fillRect(c3xtl, ytt, n3 * fw, fh, ILI9341_BLACK);
  }

  // Update test result text
  tft.setCursor(c2xtl, ytt);
  tft.setTextColor(ok1 ? ILI9341_GREEN : ILI9341_RED);
  tft.println(val1);
  tft.setCursor(c3xtl, ytt);
  tft.setTextColor(ok2 ? ILI9341_GREEN : ILI9341_RED);
  tft.println(val2);
}

void setup() {
  // Setup onboard LED
  pinMode(LED_BUILTIN, OUTPUT);

  // Setup ADC
  analogReadResolution(12);

  // Setup I2C master
  Wire.begin();

  // Setup I2C slave
  Wire1.begin(SlaveAddr::due);  // Set I2C1 as slave with the given address
  Wire1.onReceive(i2cSlaveRx);  // Register event in I2C1

  // Setup emulated UART output
  SerialUSB.begin(0);
  SerialUSB.println("Welcome to the Power Board Tester");

  // Setup display
  tft.begin();
  tft.setRotation(3);
  tft.fillScreen(ILI9341_BLACK);
  tft.setTextSize(2);
  // tft.setFont(&FreeMono9pt7b);
  // tft.setCursor(0, FreeMono9pt7b.yAdvance);
}

void loop() {
  uint32_t loopStartTime = millis();

  // Blink LED, 100 ms on, 1000 ms off
  static uint32_t led_timer = 0;
  static uint32_t led_state = LOW;
  if (millis() > led_timer) {
    led_state = led_state == HIGH ? LOW : HIGH;
    digitalWrite(LED_BUILTIN, led_state);
    led_timer += led_state == HIGH ? 100 : 900;
  }

  static uint32_t test_timer = 0;
  static bool     fan_on     = false;
  if (millis() > test_timer) {
    char strbuf1[7] = {0};
    char strbuf2[7] = {0};

    // Measure ADCs
    float ctrl5va = adcToVolts(analogRead(A0), 12, 3.3, 33, 100);
    float ctrl5vd = adcToVolts(analogRead(A1), 12, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", ctrl5va);
    sprintf(strbuf2, "%5.2fV", ctrl5vd);
    bool ok1 = ctrl5va < 6.0 && ctrl5va > 4.0;
    bool ok2 = ctrl5vd < 6.0 && ctrl5va > 4.0;
    drawTest<0>("Ctrl 5VA/5VD", strbuf1, ok1, strbuf2, ok2);

    float preamp9v = adcToVolts(analogRead(A2), 12, 3.3, 33, 100);
    float preamp5v = adcToVolts(analogRead(A3), 12, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", preamp9v);
    sprintf(strbuf2, "%5.2fV", preamp5v);
    ok1 = preamp9v < 11.0 && preamp9v > 8.0;
    ok2 = preamp5v < 6.0 && preamp5v > 4.0;
    drawTest<1>("Preamp 9V/5V", strbuf1, ok1, strbuf2, ok2);

    float preout9v = adcToVolts(analogRead(A4), 12, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", preout9v);
    ok1 = preout9v < 11.0 && preout9v > 8.0;
    drawTest<2>("Preout 9V", strbuf1, ok1, "", true);

    // Check I2C loopback
    // Update from previous transmission
    float i2c3v3 = adcToVolts(analogRead(A5), 12, 3.3, 100, 100);
    sprintf(strbuf1, "%5.2fV", i2c3v3);
    drawTest<3>("I2C out (J3)", strbuf1, i2c3v3 < 4.0 && i2c3v3 > 2.7,
                i2c_loopback_ok_ ? " PASS" : " FAIL", i2c_loopback_ok_);

    // Start a new transmission
    i2c_loopback_ok_ = false;
    Wire.beginTransmission(SlaveAddr::due);
    Wire.write((uint8_t)I2C_TEST_VAL);
    Wire.endTransmission();

    // Read I2C ADC
    uint8_t hv1_adc;
    uint8_t hv2_adc;
    uint8_t ntc1_adc;
    uint8_t ntc2_adc;
    readI2CADC(&hv1_adc, &hv2_adc, &ntc1_adc, &ntc2_adc);
    float hv1 = adcToVolts(hv1_adc, 8, 3.3, 4.7, 100);
    float hv2 = adcToVolts(hv2_adc, 8, 3.3, 4.7, 100);
    // float ntc1 = adcToVolts(ntc1_adc, 8, 3.3, 4.7, 0);
    sprintf(strbuf1, "%5.2fV", hv1);
    sprintf(strbuf2, "%5.2fV", hv2);
    drawTest<4>("I2C ADC HV", strbuf1, hv1 < 28 && hv1 > 20, strbuf2,
                hv2 < 28 && hv2 > 20);

    float temp1 = adcToTemp(ntc1_adc);
    if (temp1 == -INFINITY) {
      sprintf(strbuf1, "%s", " D/C");
    } else if (temp1 == INFINITY) {
      sprintf(strbuf1, "%s", "SHORT");
    } else {
      sprintf(strbuf1, "%5.1fC", temp1);
    }
    drawTest<5>("I2C ADC NTC", strbuf1, temp1 > 15 && temp1 < 30, "", true);

    // Toggle FAN_ON

    test_timer += 250;
  }

  static uint32_t fan_timer = 0;
  if (millis() > fan_timer) {
    /*Wire.beginTransmission(SlaveAddr::gpio);
    Wire.write((uint8_t)0x00);  // Instruction byte
    Wire.write(dpot_val);       // Value
    Wire.endTransmission();
    dpot_val++;
    if (dpot_val > MAX_DPOT_VAL) {
      dpot_val = 0;
    }*/
    fan_timer += 1000;
  }

  // Adjust DPOT to control +12V
  /*
  static uint32_t dpot_timer = 0;
  static uint8_t  dpot_val   = 0;
  if (millis() > dpot_timer) {
    Wire.beginTransmission(SlaveAddr::dpot);
    Wire.write((uint8_t)0x00);  // Instruction byte
    Wire.write(dpot_val);       // Value
    Wire.endTransmission();
    dpot_val++;
    if (dpot_val > MAX_DPOT_VAL) {
      dpot_val = 0;
    }
    dpot_timer += 1000;
    update_display = true;
  }
  */

  uint32_t elapsedTime = millis() - loopStartTime;
  SerialUSB.print("Loop took ");
  SerialUSB.print(elapsedTime);
  SerialUSB.println(" ms");
}
