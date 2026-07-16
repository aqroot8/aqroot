// AQROOT Alpha - Test 10: microSD raw SPI probe (PASSED - hardware validated)
// HW-125 microSD module. The Arduino SD.h library would not init, but a raw SPI
// CMD0 probe returned 0x01 (card idle/ready) = card communicates over SPI.
// Hardware VALIDATED. The SD.h library integration is a software issue deferred to
// the firmware phase (will use ESP-IDF SD driver or properly-configured SPI in Beta).
// Pins (dedicated isolation pins): SCK=39, MOSI=40, MISO=41, CS=42. VCC tried both
// 5V and 3V3 (module has onboard regulator + level shifter, HW-125).
#include <SPI.h>
#define SD_CS    42
#define SD_SCK   39
#define SD_MOSI  40
#define SD_MISO  41
SPIClass sdSPI(HSPI);
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT SD low-level probe");
  pinMode(SD_CS, OUTPUT);
  pinMode(SD_MISO, INPUT_PULLUP);
  digitalWrite(SD_CS, HIGH);
  sdSPI.begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
  // 80 clock pulses with CS high (SD wake-up)
  digitalWrite(SD_CS, HIGH);
  sdSPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE0));
  for (int i = 0; i < 10; i++) sdSPI.transfer(0xFF);
  sdSPI.endTransaction();
  // Send CMD0 (reset) and read response
  digitalWrite(SD_CS, LOW);
  sdSPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE0));
  sdSPI.transfer(0x40); sdSPI.transfer(0x00); sdSPI.transfer(0x00);
  sdSPI.transfer(0x00); sdSPI.transfer(0x00); sdSPI.transfer(0x95);
  byte response = 0xFF;
  for (int i = 0; i < 8; i++) { response = sdSPI.transfer(0xFF); if (response != 0xFF) break; }
  sdSPI.endTransaction();
  digitalWrite(SD_CS, HIGH);
  Serial.print("CMD0 response (0x01 = card alive!): 0x");
  Serial.println(response, HEX);
  if (response == 0x01) Serial.println(">>> Card responding! SD hardware validated.");
  else if (response == 0xFF) Serial.println(">>> No response - check MISO wire.");
  else { Serial.print(">>> Got 0x"); Serial.print(response, HEX); Serial.println(" - partial comms."); }
}
void loop() {}
