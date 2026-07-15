// AQROOT Alpha - Test 4: FT6236 capacitive touch read (PASSED)
// Touch controller at I2C 0x38. Must pulse CTP_RST to wake it.
#include <Wire.h>
#define I2C_SDA 1
#define I2C_SCL 2
#define CTP_RST 21
#define CTP_INT 42
#define FT6236_ADDR 0x38
void wakeTouch() {
  pinMode(CTP_RST, OUTPUT);
  digitalWrite(CTP_RST, LOW);
  delay(20);
  digitalWrite(CTP_RST, HIGH);
  delay(300);
}
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT Touch Test (FT6236 @ 0x38)");
  wakeTouch();
  Wire.begin(I2C_SDA, I2C_SCL);
  pinMode(CTP_INT, INPUT);
  Serial.println("Touch the screen...");
}
void loop() {
  Wire.beginTransmission(FT6236_ADDR);
  Wire.write(0x02);
  Wire.endTransmission();
  Wire.requestFrom(FT6236_ADDR, 1);
  byte touches = Wire.available() ? Wire.read() : 0;
  if (touches > 0 && touches < 3) {
    Wire.beginTransmission(FT6236_ADDR);
    Wire.write(0x03);
    Wire.endTransmission();
    Wire.requestFrom(FT6236_ADDR, 4);
    if (Wire.available() >= 4) {
      byte xh = Wire.read();
      byte xl = Wire.read();
      byte yh = Wire.read();
      byte yl = Wire.read();
      int x = ((xh & 0x0F) << 8) | xl;
      int y = ((yh & 0x0F) << 8) | yl;
      Serial.print("Touch at X="); Serial.print(x);
      Serial.print("  Y="); Serial.println(y);
    }
  }
  delay(50);
}
