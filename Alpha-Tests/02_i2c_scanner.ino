// AQROOT Alpha - Test 2: I2C scanner with touch reset (PASSED)
// Found touch controller at 0x38 (FT6236/FT6336 family).
// NOTE: the touch chip must be pulsed on CTP_RST or it stays asleep and won't appear.
#include <Wire.h>
#define I2C_SDA 1
#define I2C_SCL 2
#define CTP_RST 21
#define CTP_INT 42
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT I2C Scanner (with touch reset)");
  pinMode(CTP_RST, OUTPUT);
  pinMode(CTP_INT, OUTPUT);
  digitalWrite(CTP_INT, LOW);
  digitalWrite(CTP_RST, LOW);
  delay(20);
  digitalWrite(CTP_RST, HIGH);
  delay(300);
  pinMode(CTP_INT, INPUT);
  Wire.begin(I2C_SDA, I2C_SCL);
}
void loop() {
  byte count = 0;
  Serial.println("Scanning I2C bus...");
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("  Found device at 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
      count++;
    }
  }
  if (count == 0) Serial.println("  No I2C devices found");
  else { Serial.print("Done. "); Serial.print(count); Serial.println(" found."); }
  Serial.println();
  delay(3000);
}
