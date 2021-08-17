#include <Arduino.h>

void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(PIN_LED, OUTPUT);
  //SerialUSB.begin(0);
}

void loop() {
  digitalWrite(PIN_LED, HIGH);  // turn the LED on (HIGH is the voltage level)
  delay(100);                       // wait for a second
  digitalWrite(PIN_LED, LOW);   // turn the LED off by making the voltage LOW
  delay(100);                       // wait for a second
  //SerialUSB.println("hi");
}
