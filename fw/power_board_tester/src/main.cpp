/*
 * AmpliPi Home Audio
 * Copyright (C) 2022 MicroNova LLC
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
 * Designed to run on an Arduino Due. This project verifies Power Board
 * functionality independent of the rest of the AmpliPi unit.
 *
 * Tests:
 *  - Ctrl 5VA/5VD: must be within (4.5, 5.5) V.
 *  - Preamp 9V/5V: must be within (8.5, 9.5) and (4.5, 5.5) V, respectively.
 *  - Preout 9V   : must be within (8.5, 9.5) V.
 *  - I2C loopback: 3.3v must be within (3, 3.6) V and I2C out must work.
 *  - I2C ADC HV1 : HV1 must be within (15, 30) V and temp within (20, 28) C
 *  - I2C ADC HV2 : HV2 must be within (15, 30) V and temp within (20, 28) C
 *  - I2C ADC temp: both amp temps must be within (22.5, 27.5) C
 *  - PG_12V/PG_5V: verifies both power good signals are high
 *  - 12V J9/J10  : both fan outputs must be within +/-10% the desired values.
 *                  The DPOT control is cycled through 3 values.
 *  - FAN_ON J9/10: check that the fan on/off control works.
 * All I2C devices are verified:
 *  - MAX11601 (0x64), MAX11603 (0x6D), or MAX11605 (0x65): 4-channel MAX11601
 *    ADC measures HV1 voltage and temp, and measures both amp temp sensors.
 *    MAX11603/5 also measure HV2 voltage and temp.
 *  - MCP23008 (0x21): 8-channel GPIO expander. Currently only GP2/3/7 are used
 *  - MCP4017 (0x2F) or MCP40D17 (0x2E) : Digital potentiometer controlling +12V
 *  - I2C Bus connector for the LED board is tested as a loopback to the Due.
 * Slave addresses in parenthesis are 7-bit right-aligned, so will be shifted
 * left one bit when sent on the wire.
 *
 * Hardware required:
 *  - Arduino Due
 *  - +24V power supply
 *  - +24/+9 DC/DC converter (using an old power board)
 *  - LCD Display
 *  - 10k, 33k, and 100k resistors
 * See power_board_tester_sch.drawio.pdf for the full schematic.
 *
 *  TODO: A global ground is used for measurements, so individual ground
 *        connectors are not actually tested. Possibly differential analog
 *        measurements would solve that?
 *
 *  TODO: Protection against shorts on power board
 */

#include <Adafruit_ILI9341.h>
#include <Arduino.h>
#include <Wire.h>

// Enables debug printing and test timing
//#define DEBUG

// How often to run the tests
#define TEST_PERIOD_MS 500

// TFT display parameters
#define TFT_CS       10
#define TFT_DC       11
#define TFT_SPI_FREQ (50 * 1000000)  // Default = 24 MHz
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);

#define TFT_WIDTH       320
#define TFT_HEIGHT      240
#define TFT_FONT_WIDTH  6
#define TFT_FONT_HEIGHT 8
#define TEXT_MARGIN     4

// I2C loopback test
static constexpr uint8_t I2C_TEST_VAL = 0xA4;

// I2C GPIO
static constexpr uint8_t MCP23008_REG_IODIR = 0x00;
static constexpr uint8_t MCP23008_REG_OLAT  = 0x0A;

// I2C digital potentiometer values to loop through
// V = 100k / (10k / 127 * DPOT_VAL + 9.1k) + 1
static constexpr uint8_t DPOT_VALS[]  = {0x7F, 0x3F, 0x00};
static constexpr float   DPOT_VOLTS[] = {6.24, 8.11, 11.99};

// 7-bit I2C addresses, in bits 6 downto 0
enum SlaveAddr : uint8_t {
  due   = 0x0F,
  gpio  = 0x21,
  dpots = 0x2E,  // DPot that requires SMBus byte-write command 0x00
  dpot  = 0x2F,
  adc4  = 0x64,  // MAX11601 4-channel ADC
  adc8  = 0x6D,  // MAX11603 8-channel ADC
  adc12 = 0x65,  // MAX11605 12-channel ADC
};

// I2C1 slave RX callback
bool i2c_loopback_ok_ = false;
void i2cSlaveRx(int rxBufLen) {
  // Assume rxBufLen > 0 and read a received byte
  uint8_t rx = Wire1.read();

  // Verify the received byte is the test byte that was sent
  i2c_loopback_ok_ = rx == I2C_TEST_VAL;

#ifdef DEBUG
  SerialUSB.print("Got I2C byte 0x");
  SerialUSB.println(rx, HEX);
#endif
}

constexpr float adcToVolts(uint32_t adc_val, uint8_t bits, float v_ref,
                           float r_pulldown, float r_series) {
  float scale =
      v_ref * (r_pulldown + r_series) / r_pulldown / ((1 << bits) - 1);
  return scale * adc_val;
}

// Returns false if outside of [min, max], disconnected, or shorted
bool adcToTempStr(uint8_t ntc_adc, float min, float max, char* str) {
  if (ntc_adc == 0) {
    // 0 causes divide-by-zero
    sprintf(str, "%s", " D/C");
    return false;
  } else if (ntc_adc == 255) {
    // 255 causes Rt=0 which leads to ln(0)
    sprintf(str, "%s", "SHORT");
    return false;
  } else {
    float rt   = 4.7f * 255 / ntc_adc - 4.7f;
    float c    = 1.0f / (25.0f + 273.5f);
    float temp = 1.0f / (logf(rt / 10) / 3900 + c) - 273.15f;
    sprintf(str, "%5.1fC", temp);
    return min < temp && temp < max;
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

struct AdcData {
  union {
    struct {
      uint8_t hv1_volts;
      uint8_t amp1_temp;
      uint8_t hv1_temp;
      uint8_t amp2_temp;
      uint8_t hv2_volts;
      uint8_t hv2_temp;
    };
    uint8_t vals[6];
  };
  uint8_t num_chans;
};

bool i2cDevPresent(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

bool readI2CADC(AdcData* data) {
  // Figure out which ADC is present
  uint8_t addr = SlaveAddr::adc4;
  if (i2cDevPresent(SlaveAddr::adc4)) {
    addr            = SlaveAddr::adc4;
    data->num_chans = 4;
  } else if (i2cDevPresent(SlaveAddr::adc8)) {
    addr            = SlaveAddr::adc8;
    data->num_chans = 6;
  } else if (i2cDevPresent(SlaveAddr::adc12)) {
    addr            = SlaveAddr::adc12;
    data->num_chans = 6;
  } else {
    // No ADC present
    return false;
  }

  Wire.beginTransmission(addr);
  Wire.write((uint8_t)0b00000111);  // Send configuration byte, set CS=0x2
  Wire.endTransmission();

  Wire.requestFrom(addr, data->num_chans);
  if (Wire.available() < data->num_chans) {
    // Not enough data was read
    return false;
  }

  for (size_t i = 0; i < data->num_chans; i++) {
    data->vals[i] = Wire.read();
  }
  return true;
}

void writeI2CGPIO(bool fan_on) {
  // FAN_ON = GP7
  // EN_12V = GP1 (Removed on Power Board Rev4)
  // EN_9V  = GP0 (Removed on Power Board Rev3)
  Wire.beginTransmission(SlaveAddr::gpio);
  Wire.write(MCP23008_REG_IODIR);
  Wire.write((uint8_t)0x7C);  // Set GP7, GP1, and GP0 as outputs
  Wire.endTransmission();

  // Always enable 9V and 12V for old boards
  Wire.beginTransmission(SlaveAddr::gpio);
  Wire.write(MCP23008_REG_OLAT);
  Wire.write(fan_on ? 0x83 : 0x03);
  Wire.endTransmission();
}

// Gets PG_12V and PG_5VA's status
// Returns true on I2C read success, false on failure
bool readI2CGPIO(bool& pg_12v, bool& pg_5va) {
  // PG_12V   = GP3
  // PG_5VA   = GP2
  Wire.beginTransmission(SlaveAddr::gpio);
  Wire.write(MCP23008_REG_OLAT);
  Wire.requestFrom(SlaveAddr::gpio, 1);
  Wire.endTransmission();
  if (Wire.available()) {
    uint8_t gpio = Wire.read();
    pg_12v       = gpio & 0x08;
    pg_5va       = gpio & 0x04;
    return true;
  }
  return false;
}

// Sum 16 ADC reads, resulting in a 16-bit ADC read
uint32_t readAna16(uint8_t pin) {
  uint32_t ana = 0;
  for (size_t i = 0; i < 16; i++) {
    ana += analogRead(pin);
  }
  return ana;
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
  // Setup GPIO
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(A7, INPUT);
  pinMode(A9, INPUT);

  // Setup ADC
  analogReadResolution(12);

  // Setup I2C master
  Wire.begin();
  Wire.setClock(400000);

  // Setup I2C slave
  Wire1.begin(SlaveAddr::due);  // Set I2C1 as slave with the given address
  Wire1.onReceive(i2cSlaveRx);  // Register event in I2C1

  // Setup emulated UART output
#ifdef DEBUG
  SerialUSB.begin(0);
  SerialUSB.println("Welcome to the Power Board Tester");
#endif

  // Setup display
  tft.begin(TFT_SPI_FREQ);
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

  static uint8_t  dpot_val_idx = 0;
  static uint32_t test_timer   = 0;
  if (millis() > test_timer) {
    char strbuf1[7] = {0};
    char strbuf2[7] = {0};

    // Measure ADCs
    float ctrl5va = adcToVolts(readAna16(A0), 16, 3.3, 33, 100);
    float ctrl5vd = adcToVolts(readAna16(A1), 16, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", ctrl5va);
    sprintf(strbuf2, "%5.2fV", ctrl5vd);
    bool ok1 = ctrl5va < 5.5 && ctrl5va > 4.5;
    bool ok2 = ctrl5vd < 5.5 && ctrl5vd > 4.5;
    drawTest<0>("Ctrl 5VA/5VD", strbuf1, ok1, strbuf2, ok2);

    float preamp9v = adcToVolts(readAna16(A2), 16, 3.3, 33, 100);
    float preamp5v = adcToVolts(readAna16(A3), 16, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", preamp9v);
    sprintf(strbuf2, "%5.2fV", preamp5v);
    ok1 = preamp9v < 9.5 && preamp9v > 8.5;
    ok2 = preamp5v < 5.5 && preamp5v > 4.5;
    drawTest<1>("Preamp 9V/5V", strbuf1, ok1, strbuf2, ok2);

    float preout9v = adcToVolts(readAna16(A4), 16, 3.3, 33, 100);
    sprintf(strbuf1, "%5.2fV", preout9v);
    ok1 = preout9v < 9.5 && preout9v > 8.5;
    drawTest<2>("Preout 9V", strbuf1, ok1, "", true);

    // Check I2C loopback
    // Update from previous transmission
    float i2c3v3 = adcToVolts(readAna16(A5), 16, 3.3, 100, 100);
    sprintf(strbuf1, "%5.2fV", i2c3v3);
    drawTest<3>("I2C out (J3)", strbuf1, i2c3v3 < 3.6 && i2c3v3 > 3.0,
                i2c_loopback_ok_ ? " PASS" : " FAIL", i2c_loopback_ok_);

    // Check the 12V power supply
    bool pg_12v;
    bool pg_5va;
    bool i2c_success = readI2CGPIO(pg_12v, pg_5va);
    drawTest<4>("PG_12V/PG_5V", pg_12v ? " PASS" : " FAIL", pg_12v,
                pg_5va ? " PASS" : " FAIL", pg_5va);

    // Check the 12V fan power supply from both J9 and J10 is ok
    float fan12v     = adcToVolts(readAna16(A6), 16, 3.3, 10, 100);
    float psu_fan12v = adcToVolts(readAna16(A8), 16, 3.3, 10, 100);
    sprintf(strbuf1, "%5.2fV", fan12v);
    sprintf(strbuf2, "%5.2fV", psu_fan12v);
    ok1 = fan12v < DPOT_VOLTS[dpot_val_idx] * 1.1 &&
          fan12v > DPOT_VOLTS[dpot_val_idx] * 0.9;
    ok2 = psu_fan12v < DPOT_VOLTS[dpot_val_idx] * 1.1 &&
          psu_fan12v > DPOT_VOLTS[dpot_val_idx] * 0.9;
    drawTest<5>("12V J9/J10", strbuf1, ok1, strbuf2, ok2);

    // Check that the fan control output works.
    // Leave output high for ADC reading.
    writeI2CGPIO(false);             // Set low FAN_ON signal
    delay(1);                        // Wait a bit to make sure output settles
    ok1 = digitalRead(A7) == LOW;    // J9 - direct connection
    ok2 = digitalRead(A9) == HIGH;   // J10 - pulled up external to power board
    writeI2CGPIO(true);              // Set high FAN_ON signal
    delay(1);                        // Wait a bit to make sure output settles
    ok1 &= digitalRead(A7) == HIGH;  // J9 - direct connection
    ok2 &= digitalRead(A9) == LOW;   // J10 - mosfet active, output grounded
    drawTest<6>("FAN_ON J9/10", ok1 ? " PASS" : " FAIL", ok1,
                ok2 ? " PASS" : " FAIL", ok2);

    // Adjust DPOT to control +12V
    dpot_val_idx += 1;
    if (dpot_val_idx >= sizeof(DPOT_VALS)) {
      dpot_val_idx = 0;
    }
    // Try MCP4017
    Wire.beginTransmission(SlaveAddr::dpot);
    Wire.write(DPOT_VALS[dpot_val_idx]);  // Value
    Wire.endTransmission();

    // Try MCP40D17
    Wire.beginTransmission(SlaveAddr::dpots);
    Wire.write((uint8_t)0x00);            // SMBus command byte
    Wire.write(DPOT_VALS[dpot_val_idx]);  // Value
    Wire.endTransmission();

    // Read I2C ADC
    AdcData adc_data = {};
    readI2CADC(&adc_data);
    bool t1_ok = adcToTempStr(adc_data.amp1_temp, 25 * 0.9, 25 * 1.1, strbuf1);
    bool t2_ok = adcToTempStr(adc_data.amp2_temp, 25 * 0.9, 25 * 1.1, strbuf2);
    drawTest<7>("I2C ADC temp", strbuf1, t1_ok, strbuf2, t2_ok);

    float hv1 = adcToVolts(adc_data.hv1_volts, 8, 3.3, 4.7, 100);
    sprintf(strbuf1, "%5.2fV", hv1);
    bool hv1_ntc_ok = adcToTempStr(adc_data.hv1_temp, 15, 30, strbuf2);
    drawTest<8>("I2C ADC HV1", strbuf1, hv1 < 28 && hv1 > 20, strbuf2,
                hv1_ntc_ok);

    if (adc_data.num_chans > 4) {
      float hv2 = adcToVolts(adc_data.hv2_volts, 8, 3.3, 4.7, 100);
      sprintf(strbuf1, "%5.2fV", hv2);
      bool hv2_ntc_ok = adcToTempStr(adc_data.hv2_temp, 15, 30, strbuf2);
      drawTest<9>("I2C ADC HV2", strbuf1, hv2 < 28 && hv2 > 20, strbuf2,
                  hv2_ntc_ok);
    } else {
      drawTest<9>("I2C ADC HV2", " NONE", false, "", false);
    }

    // Start a new transmission
    i2c_loopback_ok_ = false;
    Wire.beginTransmission(SlaveAddr::due);
    Wire.write((uint8_t)I2C_TEST_VAL);
    Wire.endTransmission();

#ifdef DEBUG
    // TODO: this is off the screen currently
    uint32_t elapsedTime = millis() - loopStartTime;
    SerialUSB.print("Test took ");
    SerialUSB.print(elapsedTime);
    SerialUSB.println(" ms");
    sprintf(strbuf1, "%6d", elapsedTime);
    ok1 = elapsedTime < TEST_PERIOD_MS;
    drawTest<10>("Test time ms", strbuf1, ok1, "", true);
#endif
    test_timer += TEST_PERIOD_MS;
  }
}
