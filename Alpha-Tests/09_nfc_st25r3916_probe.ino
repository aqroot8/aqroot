// AQROOT Alpha - Test 9: ST25R3916 NFC chip-ID probe (PASSED - hardest chip)
// X-NUCLEO-NFC06A1 board. Raw SPI read of IC Identity register (0x3F).
// Result: returned 0x2A -> IC-type field (bits[7:3]) = 0x05 = ST25R3916 confirmed.
// NFC hardware SPI communication VALIDATED.
//
// KEY POWER FINDING: this board needs BOTH 3V3 and 5V rails. The ESP32-S3 devkit's
// "5Vin" pin is INPUT-only (read 0.75V, not 5V), so the 5V pin was fed from 3V3
// instead. The chip communicates fine over SPI at 3.3V on both rails. Full RF
// transmit power (up to 1.7W antenna) needs a real 5V rail -> BETA POWER SYSTEM MUST
// PROVIDE A 5V BOOST FOR NFC RF. The bq25185 only outputs 3.3V, so Beta needs a
// 5V boost converter for the NFC front-end.
//
// Wiring (X-NUCLEO-NFC06A1, verified with multimeter):
//   CN5 GND (3 pins to edge / 6 pins to CN9) -> ESP32 GND
//   CN5 SCK  (1st toward CN9 from GND) -> GPIO39
//   CN5 MISO (2nd) -> GPIO41
//   CN5 MOSI (3rd) -> GPIO40
//   CN5 CS   (4th) -> GPIO42
//   CN6 3V3 (4th from left, lit PWR LED) -> ESP32 3V3
//   CN6 5V  (5th from left) -> ESP32 3V3 (see power finding above)
//   ST25R3916 uses SPI MODE0/1 (0x2A read consistent on both).

#include <SPI.h>
#define NFC_SCK   39
#define NFC_MISO  41
#define NFC_MOSI  40
#define NFC_CS    42
SPIClass nfcSPI(HSPI);
byte readReg(byte reg, byte spiMode) {
  digitalWrite(NFC_CS, LOW);
  delayMicroseconds(10);
  nfcSPI.beginTransaction(SPISettings(1000000, MSBFIRST, spiMode));
  nfcSPI.transfer(0x40 | (reg & 0x3F));
  byte val = nfcSPI.transfer(0x00);
  nfcSPI.endTransaction();
  delayMicroseconds(10);
  digitalWrite(NFC_CS, HIGH);
  return val;
}
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT ST25R3916 NFC probe");
  pinMode(NFC_CS, OUTPUT);
  digitalWrite(NFC_CS, HIGH);
  nfcSPI.begin(NFC_SCK, NFC_MISO, NFC_MOSI, NFC_CS);
  delay(100);
  byte id = readReg(0x3F, SPI_MODE1);
  Serial.print("IC Identity (0x3F) = 0x"); Serial.println(id, HEX);
  byte icType = (id >> 3) & 0x1F;
  Serial.print("IC type = 0x"); Serial.println(icType, HEX);
  if (icType == 0x05) Serial.println(">>> ST25R3916 CONFIRMED - NFC hardware validated!");
  else if (id == 0x00 || id == 0xFF) Serial.println(">>> No response - check power (needs VDD) and MISO.");
  else Serial.println(">>> Got response but unexpected IC type.");
}
void loop() { delay(2000); }
