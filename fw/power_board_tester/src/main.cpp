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
 *  +-------------+---------------------+ Power
 *    GND         | GND/AGND*
 *    A0          | J4 pin 1: +5VA
 *    A1          | J4 pin 3: +5VD
 *    A2          | J5 pin 1: +9VA
 *    A3          | J5 pin 3: +5VA
 *    A4          | J8 pin 1: +9VA
 *  +-------------+---------------------+ I2C
 *    +3.3V       | J3 pin 1: +3.3VA
 *    SCL         | J3 pin 2: SCL
 *    SDA         | J3 pin 3: SDA
 *    GND         | J3 pin 4: AGND
 *    +3.3V       | J2 pin 1: +3.3VA
 *    SCL1        | J2 pin 2: SCL
 *    SDA1        | J2 pin 3: SDA
 *    GND         | J2 pin 4: AGND
 *  +-------------+---------------------+ IO
 *    2     (out) | J6 pin 1: NTC1
 *    DAC0  (out) | J9 pin 2: DXP1
 *    DAC1  (out) | J9 pin 7: DXP2
 *    A5    (in)  | J9 pin 1: +3.3VA (out)
 *    A6    (in)  | J9 pin 5: +12VD  (out)
 *    5     (out) | J9 pin 3: TACH1
 *    6     (out) | J9 pin 6: TACH2
 *    A5          | J9 pin 4: FAN_PWM
 *  +---------------------+---------------------+
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

#include <Arduino.h>

void setup() {
  // Initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);
  SerialUSB.begin(0);
  SerialUSB.println("Welcome to the Power Board Tester");
}

void loop() {
  // Blink LED
  static uint32_t led_timer = 0;
  static uint32_t led_state = LOW;
  if (millis() > led_timer) {
    led_state = led_state == HIGH ? LOW : HIGH;
    digitalWrite(LED_BUILTIN, led_state);
    led_timer += 1000;
  }

  // Measure ADCs

  // Read I2C ADC

  // Toggle FAN_ON

  // Adjust DPOT to control +12V

  // Check I2C loopback
}
