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

#define ADC_REF_VOLTS     3.3
#define ADC_PULLDOWN_OHMS 33
#define ADC_SERIES_OHMS   100
#define ADC_MAX_VAL       4095

static constexpr uint8_t MAX_DPOT_VAL = 0x7F;
static constexpr uint8_t I2C_TEST_VAL = 0xA4;

// Drawing positions
static constexpr int16_t volts_x0 = 0;
static constexpr int16_t volts_y0 = 0;
static constexpr int16_t loop_x0  = 0;
static constexpr int16_t loop_y0  = 10 * TFT_FONT_HEIGHT;

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

float adcToVolts(uint32_t adc_val, uint32_t pulldown, uint32_t series) {
  return ((float)(adc_val * (pulldown + series))) *
         (ADC_REF_VOLTS / ADC_MAX_VAL) / pulldown;
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

template <int16_t x0, int16_t y0>
void drawVoltages(float ctrl5va, float ctrl5vd, float preamp9v, float preamp5v,
                  float preout9v, float i2c3v3) {
  static constexpr uint8_t n1 = 17;  // Number of characters in first column
  static constexpr uint8_t n2 = 6;   // Number of characters in second column
  static constexpr uint8_t nl = 9;   // Number of lines/rows

  // Column ends and starts
  static constexpr int16_t c1x2 = x0 + (0.5 + n1) * TFT_FONT_WIDTH;
  static constexpr int16_t c2x1 = c1x2 + TFT_FONT_WIDTH / 2;
  static constexpr int16_t c2x2 = c2x1 + (0.5 + n2) * TFT_FONT_WIDTH;

  static bool init = true;

  if (init) {
    tft.fillRect(x0, y0, TFT_WIDTH - x0, nl * TFT_FONT_HEIGHT, ILI9341_BLACK);
    tft.setCursor(x0, y0);

    // Draw all static text
    tft.println("Ctrl Board   +5VA");
    tft.println("Power (J4)   +5VD");
    tft.println();
    tft.println("Preamp Board +9VA");
    tft.println("Power (J5)   +5VA");
    tft.println();
    tft.println("Preout (J8)  +9VA");
    tft.println();
    tft.println("I2C (J3)   +3.3VA");

    // Draw borders
    tft.drawLine(x0, 2.5 * TFT_FONT_HEIGHT, c2x2, 2.5 * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    tft.drawLine(x0, 5.5 * TFT_FONT_HEIGHT, c2x2, 5.5 * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    tft.drawLine(x0, 7.5 * TFT_FONT_HEIGHT, c2x2, 7.5 * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    tft.drawLine(x0, (0.5 + nl) * TFT_FONT_HEIGHT, c2x2,
                 (0.5 + nl) * TFT_FONT_HEIGHT, ILI9341_WHITE);
    tft.drawLine(c1x2, y0, c1x2, (0.5 + nl) * TFT_FONT_HEIGHT, ILI9341_WHITE);
    tft.drawLine(c2x2, y0, c2x2, (0.5 + nl) * TFT_FONT_HEIGHT, ILI9341_WHITE);
    init = false;
  } else {
    // Clear the area that will be re-written with voltage text
    tft.fillRect(c2x1, y0, n2 * TFT_FONT_WIDTH, 2 * TFT_FONT_HEIGHT,
                 ILI9341_BLACK);
    tft.fillRect(c2x1, y0 + 3 * TFT_FONT_HEIGHT, n2 * TFT_FONT_WIDTH,
                 2 * TFT_FONT_HEIGHT, ILI9341_BLACK);
    tft.fillRect(c2x1, y0 + 6 * TFT_FONT_HEIGHT, n2 * TFT_FONT_WIDTH,
                 1 * TFT_FONT_HEIGHT, ILI9341_BLACK);
    tft.fillRect(c2x1, y0 + 8 * TFT_FONT_HEIGHT, n2 * TFT_FONT_WIDTH,
                 1 * TFT_FONT_HEIGHT, ILI9341_BLACK);
  }

  // Update voltage text
  char strbuf[n2 + 1] = {0};
  tft.setCursor(c2x1, 0 * TFT_FONT_HEIGHT);
  float good = ctrl5va < 6.0 && ctrl5va > 4.0 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", ctrl5va);
  tft.println(strbuf);
  tft.setCursor(c2x1, 1 * TFT_FONT_HEIGHT);
  good = ctrl5vd < 6.0 && ctrl5vd > 4.0 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", ctrl5vd);
  tft.println(strbuf);
  tft.setCursor(c2x1, 3 * TFT_FONT_HEIGHT);
  good = preamp9v < 11.0 && preamp9v > 8.0 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", preamp9v);
  tft.println(strbuf);
  tft.setCursor(c2x1, 4 * TFT_FONT_HEIGHT);
  good = preamp5v < 6.0 && preamp5v > 4.0 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", preamp5v);
  tft.println(strbuf);
  tft.setCursor(c2x1, 6 * TFT_FONT_HEIGHT);
  good = preout9v < 11.0 && preout9v > 8.0 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", preout9v);
  tft.println(strbuf);
  tft.setCursor(c2x1, 8 * TFT_FONT_HEIGHT);
  good = i2c3v3 < 4.0 && i2c3v3 > 2.7 ? 1.0 : 0.0;
  tft.setTextColor(rgb565(1.0, good, good));
  sprintf(strbuf, "%5.2fV", i2c3v3);
  tft.println(strbuf);
}

template <int16_t x0, int16_t y0>
void drawI2CLoopback(bool ok) {
  static constexpr uint8_t n1 = 12;  // Number of characters in first column
  static constexpr uint8_t n2 = 4;   // Number of characters in second column
  static constexpr uint8_t nl = 2;   // Number of lines (text + 1 for margin)

  // Column ends and starts
  static constexpr int16_t c1x2 = x0 + (0.5 + n1) * TFT_FONT_WIDTH;
  static constexpr int16_t c2x1 = c1x2 + TFT_FONT_WIDTH / 2;
  static constexpr int16_t c2x2 = c2x1 + (0.5 + n2) * TFT_FONT_WIDTH;

  static bool init = true;

  if (init) {
    // Clear entire area
    tft.fillRect(x0, y0, TFT_WIDTH - x0, nl * TFT_FONT_HEIGHT, ILI9341_BLACK);

    // Draw static text
    tft.setCursor(x0, y0 + TFT_FONT_HEIGHT / 2);
    tft.println("I2C out (J3)");

    // Draw borders
    tft.drawLine(x0, y0, c2x2, y0, ILI9341_WHITE);
    tft.drawLine(x0, y0 + nl * TFT_FONT_HEIGHT, c2x2, y0 + nl * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    tft.drawLine(c1x2, y0, c1x2, y0 + nl * TFT_FONT_HEIGHT, ILI9341_WHITE);
    tft.drawLine(c2x2, y0, c2x2, y0 + nl * TFT_FONT_HEIGHT, ILI9341_WHITE);
    init = false;
  } else {
    // Clear the area that will be re-written with voltage text
    tft.fillRect(c2x1, y0 + TFT_FONT_HEIGHT / 2, n2 * TFT_FONT_WIDTH,
                 TFT_FONT_HEIGHT, ILI9341_BLACK);
  }

  // Update voltage text
  tft.setCursor(c2x1, y0 + TFT_FONT_HEIGHT / 2);
  uint16_t color = ok ? ILI9341_GREEN : ILI9341_RED;
  tft.setTextColor(color);
  tft.println(ok ? "PASS" : "FAIL");
}

/*template <int16_t x0, int16_t y0>
void drawI2CLoopback() {
  static constexpr uint8_t n1 = 13;  // Number of characters in first column
  static constexpr uint8_t n2 = 7;   // Number of characters in second column
  static constexpr uint8_t nl = 6;   // Number of lines/rows

  // Column ends and starts
  static constexpr int16_t c1x2 = x0 + (0.5 + n1) * TFT_FONT_WIDTH;
  static constexpr int16_t c2x1 = c1x2 + TFT_FONT_WIDTH / 2;
  static constexpr int16_t c2x2 = c2x1 + (0.5 + n2) * TFT_FONT_WIDTH;

  static bool init = true;

  if (init) {
    tft.fillRect(x0, y0, TFT_WIDTH - x0, nl * TFT_FONT_HEIGHT, ILI9341_BLACK);
    tft.setCursor(x0, y0);

    // Draw all static text
    tft.println("I2C GPIO (U6)");
    tft.println();
    tft.println("I2C ADC  (U7)");
    tft.println("    CH1   HV1");
    tft.println("    CH2   HV2");
    tft.println("    CH3  NTC1");

    // Draw borders
    tft.drawLine(x0, y0, c2x2, y0, ILI9341_WHITE);
    tft.drawLine(x0, y0 + 1.5 * TFT_FONT_HEIGHT, c2x2,
                 y0 + 1.5 * TFT_FONT_HEIGHT, ILI9341_WHITE);
    tft.drawLine(x0, y0 + (0.5 + nl) * TFT_FONT_HEIGHT, c2x2,
                 y0 + (0.5 + nl) * TFT_FONT_HEIGHT, ILI9341_WHITE);
    tft.drawLine(c1x2, y0, c1x2, y0 + (0.5 + nl) * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    tft.drawLine(c2x2, y0, c2x2, y0 + (0.5 + nl) * TFT_FONT_HEIGHT,
                 ILI9341_WHITE);
    init = false;
  } else {
    // Clear the area that will be re-written with voltage text
    tft.fillRect(c2x1, y0, n2 * TFT_FONT_WIDTH, TFT_FONT_HEIGHT, ILI9341_BLACK);
    tft.fillRect(c2x1, y0 + 2 * TFT_FONT_HEIGHT, n2 * TFT_FONT_WIDTH,
                 4 * TFT_FONT_HEIGHT, ILI9341_BLACK);
  }

  // Update GPIO and voltage text
}*/

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

  // Measure ADCs
  static uint32_t adc_timer = 0;
  if (millis() > adc_timer) {
    float ctrl5va =
        adcToVolts(analogRead(A0), ADC_PULLDOWN_OHMS, ADC_SERIES_OHMS);
    float ctrl5vd =
        adcToVolts(analogRead(A1), ADC_PULLDOWN_OHMS, ADC_SERIES_OHMS);
    float preamp9v =
        adcToVolts(analogRead(A2), ADC_PULLDOWN_OHMS, ADC_SERIES_OHMS);
    float preamp5v =
        adcToVolts(analogRead(A3), ADC_PULLDOWN_OHMS, ADC_SERIES_OHMS);
    float preout9v =
        adcToVolts(analogRead(A4), ADC_PULLDOWN_OHMS, ADC_SERIES_OHMS);
    float i2c3v3 = adcToVolts(analogRead(A5), 100, ADC_SERIES_OHMS);
    drawVoltages<volts_x0, volts_y0>(ctrl5va, ctrl5vd, preamp9v, preamp5v,
                                     preout9v, i2c3v3);
    adc_timer += 250;
  }

  // Read I2C ADC

  // Toggle FAN_ON
  static uint32_t fan_timer = 0;
  static bool     fan_on    = false;
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

  // Check I2C loopback
  static uint32_t i2c_loopback_timer = 0;
  // Start opposite so display will update
  static bool last_loop_ok = !i2c_loopback_ok_;
  if (millis() > i2c_loopback_timer) {
    // Update from previous transmission
    if (i2c_loopback_ok_ != last_loop_ok) {
      drawI2CLoopback<loop_x0, loop_y0>(i2c_loopback_ok_);
    }

    // Start a new transmission
    last_loop_ok     = i2c_loopback_ok_;
    i2c_loopback_ok_ = false;
    Wire.beginTransmission(SlaveAddr::due);
    Wire.write((uint8_t)I2C_TEST_VAL);
    Wire.endTransmission();
    i2c_loopback_timer += 100;
  }

  uint32_t elapsedTime = millis() - loopStartTime;
  SerialUSB.print("Loop took ");
  SerialUSB.print(elapsedTime);
  SerialUSB.println(" ms");
}
