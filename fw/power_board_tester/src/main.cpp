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
 *    +3.3V       | J2 pin 1: +3.3VA
 *    SCL1        | J2 pin 2: SCL     (out)
 *    SDA1        | J2 pin 3: SDA     (out)
 *    GND         | J2 pin 4: AGND
 *  +-------------+------------------------+ IO
 *    2     (out) | J6 pin 1: NTC1
 *    DAC0  (out) | J9 pin 2: DXP1
 *    DAC1  (out) | J9 pin 7: DXP2
 *    A5    (in)  | J9 pin 1: +3.3VA  (out)
 *    A6    (in)  | J9 pin 5: +12VD   (out)
 *    5     (out) | J9 pin 3: TACH1
 *    6     (out) | J9 pin 6: TACH2
 *    A7    (in)  | J9 pin 4: FAN_PWM (out)
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

static constexpr uint8_t MAX_DPOT_VAL = 63;
static constexpr uint8_t I2C_TEST_VAL = 0xA4;

enum SlaveAddr : uint8_t
{
  due  = 0x0F,
  gpio = 0x21,
  dpot = 0x2F,
  adc  = 0x64
};

enum StatusLed : uint32_t
{
  v3_3A_J2 = 23,
  v3_3A_J9 = 25,
  v5A_J4   = 27,
  v5A_J5   = 29,
  v9A_J5   = 31,
  v9A_J8   = 33,
  v5D      = 35,
  v12D     = 37,
  v24      = 39,
  therm1   = 41,
  therm2   = 43,
  therm3   = 45,
  fan      = 47,
  i2c      = 49
};

// I2C1 slave RX callback
void i2cSlaveRx(int rxBufLen) {
  // Assume rxBufLen > 0 and read a received byte
  uint8_t rx = Wire1.read();

  // Verify the received byte is the test byte that was sent
  uint32_t led = rx == I2C_TEST_VAL ? HIGH : LOW;
  digitalWrite(StatusLed::i2c, led);
  // Update test status
  // TODO

  SerialUSB.print("Got I2C byte 0x");
  SerialUSB.println(rx, HEX);
}

void setup() {
  // Setup onboard LED
  pinMode(LED_BUILTIN, OUTPUT);

  // Setup I2C master
  Wire.begin();

  // Setup I2C slave
  Wire1.begin(SlaveAddr::due);  // Set I2C1 as slave with the given address
  Wire1.onReceive(i2cSlaveRx);  // Register event in I2C1

  // Setup emulated UART output
  SerialUSB.begin(0);
  SerialUSB.println("Welcome to the Power Board Tester");

  // Setup display
  tft.begin(TFT_SPI_FREQ);
  tft.setRotation(1);
  tft.fillScreen(ILI9341_BLACK);
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

  // Read I2C ADC

  // Toggle FAN_ON

  // Adjust DPOT to control +12V
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
  }

  // Check I2C loopback
  static uint32_t i2c_loopback_timer = 0;
  if (millis() > i2c_loopback_timer) {
    Wire.beginTransmission(SlaveAddr::due);
    Wire.write((uint8_t)I2C_TEST_VAL);
    Wire.endTransmission();
    i2c_loopback_timer += 1000;
  }

  // Update display
  static bool blank = true;
  if (blank) {
    tft.fillScreen(ILI9341_WHITE);
  } else {
    tft.fillScreen(ILI9341_BLACK);
  }
  blank = !blank;
  // takes 500ms with individual pixel writes
  // tft.drawPixel(x, y, (n * 29)<<8 | (n * 67));
  uint32_t elapsedTime = millis() - loopStartTime;
  SerialUSB.print("Loop took ");
  SerialUSB.print(elapsedTime);
  SerialUSB.println(" ms");
}
