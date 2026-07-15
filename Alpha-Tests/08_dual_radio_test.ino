// AQROOT Alpha - Test 8: BOTH radios on shared SPI bus 2 (PASSED - MILESTONE)
// Result: CC1101 SUCCESS + SX1262 SUCCESS = two-radio architecture VALIDATED.
// KEY LEARNING: each radio must be explicitly DESELECTED (CS high) while the
// other is initialized/used. A floating CS on the idle radio corrupts the shared
// MISO line and causes -2 on the active radio. This CS-discipline is exactly what
// the Beta firmware "radio manager" must enforce.
#include <RadioLib.h>
#define SHARED_SCK   4
#define SHARED_MOSI  5
#define SHARED_MISO  6
#define CC_CS    7
#define CC_GDO0  15
#define CC_GDO2  16
#define SX_CS    17
#define SX_DIO1  18
#define SX_BUSY  8
#define SX_RESET 3
SPIClass radioSPI(HSPI);
CC1101 cc = new Module(CC_CS, CC_GDO0, RADIOLIB_NC, CC_GDO2, radioSPI);
SX1262 sx = new Module(SX_CS, SX_DIO1, SX_RESET, SX_BUSY, radioSPI);
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT DUAL RADIO TEST v2");
  pinMode(CC_CS, OUTPUT);
  pinMode(SX_CS, OUTPUT);
  digitalWrite(CC_CS, HIGH);
  digitalWrite(SX_CS, HIGH);
  radioSPI.begin(SHARED_SCK, SHARED_MISO, SHARED_MOSI);
  digitalWrite(SX_CS, HIGH);
  Serial.print("CC1101 (Sub-GHz)... ");
  int s1 = cc.begin(433.0);
  Serial.println(s1 == RADIOLIB_ERR_NONE ? "SUCCESS" : ("FAILED " + String(s1)));
  digitalWrite(CC_CS, HIGH);
  Serial.print("SX1262 (LoRa)... ");
  int s2 = sx.begin(915.0);
  Serial.println(s2 == RADIOLIB_ERR_NONE ? "SUCCESS" : ("FAILED " + String(s2)));
  digitalWrite(SX_CS, HIGH);
  Serial.println();
  if (s1 == RADIOLIB_ERR_NONE && s2 == RADIOLIB_ERR_NONE) {
    Serial.println(">>> BOTH RADIOS ALIVE ON SHARED BUS <<<");
    Serial.println(">>> Two-radio architecture VALIDATED <<<");
  }
}
void loop() { delay(1000); }
