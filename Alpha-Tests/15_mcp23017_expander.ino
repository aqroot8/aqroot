/*
 * AQROOT ALPHA TEST 15 - MCP23017 I2C GPIO EXPANDER (Waveshare)
 * ------------------------------------------------------------
 * Board : Waveshare MCP23017 IO Expansion Board
 * Lib   : "Adafruit MCP23017 Arduino Library"
 *
 * WIRING (Waveshare MCP23017):
 *   VCC -> 3V3    GND -> GND    SDA -> GPIO 1    SCL -> GPIO 2
 *   INTA / INTB   -> unconnected
 *   RESET handled onboard (no wire needed)
 *   A0/A1/A2 left OPEN = address 0x27 (short to GND for lower addrs)
 *
 * SELF-TEST JUMPER: PA0 <-> PB0 on the board
 *   sketch drives PA0 (lib pin 0) and reads PB0 (lib pin 8)
 *
 * Auto-detects the address from an I2C scan (0x20-0x27 range).
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MCP23X17.h>

#define I2C_SDA 1
#define I2C_SCL 2

#define PIN_DRIVE 0    // PA0
#define PIN_SENSE 8    // PB0

Adafruit_MCP23X17 mcp;
bool ready = false;
uint8_t foundAddr = 0;

void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 3000) delay(10);
  delay(300);

  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F(" AQROOT TEST 15 - MCP23017 (Waveshare)"));
  Serial.println(F("========================================"));
  Serial.printf ("  I2C SDA %d | SCL %d\n", I2C_SDA, I2C_SCL);
  Serial.println(F("  self-test jumper: PA0 <-> PB0"));
  Serial.println(F("----------------------------------------"));

  Wire.begin(I2C_SDA, I2C_SCL);

  Serial.println(F("  scanning I2C bus..."));
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf("    device at 0x%02X\n", a);
      if (a >= 0x20 && a <= 0x27) foundAddr = a;  // MCP23017 range
    }
  }
  Serial.println();

  if (foundAddr == 0) {
    Serial.println(F("  !! no MCP23017 found in 0x20-0x27 range"));
    Serial.println(F("     check VCC->3V3, GND, SDA->1, SCL->2"));
    return;
  }
  Serial.printf ("  using MCP23017 at 0x%02X\n", foundAddr);

  if (!mcp.begin_I2C(foundAddr, &Wire)) {
    Serial.println(F("  !! begin_I2C failed"));
    return;
  }
  Serial.println(F("  MCP23017 initialized OK."));

  mcp.pinMode(PIN_DRIVE, OUTPUT);
  mcp.pinMode(PIN_SENSE, INPUT);
  ready = true;

  Serial.println(F("  running PA0->PB0 loopback self-test..."));
  Serial.println();
}

void loop() {
  if (!ready) { delay(500); return; }

  static int pass = 0, fail = 0;
  static bool level = false;
  static bool announced = false;

  level = !level;
  mcp.digitalWrite(PIN_DRIVE, level ? HIGH : LOW);
  delay(5);
  int readBack = mcp.digitalRead(PIN_SENSE);

  bool ok = (readBack == (level ? HIGH : LOW));
  if (ok) pass++; else fail++;

  Serial.printf("  drove PA0=%d  read PB0=%d  %s   (pass %d / fail %d)\n",
                level ? 1 : 0, readBack,
                ok ? "OK" : "MISMATCH", pass, fail);

  if (!announced && fail == 0 && pass >= 6) {
    announced = true;
    Serial.println();
    Serial.println(F("  ****************************************"));
    Serial.println(F("  ***   MCP23017 EXPANDER VALIDATED    ***"));
    Serial.println(F("  ****************************************"));
    Serial.printf ("  address 0x%02X, PA0->PB0 loopback clean.\n", foundAddr);
    Serial.println();
  }

  if (!ok && pass + fail > 3 && fail > pass) {
    Serial.println(F("  ** mismatches: is the PA0<->PB0 jumper connected?"));
  }

  delay(500);
}
