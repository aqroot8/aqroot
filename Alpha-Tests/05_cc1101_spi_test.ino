// AQROOT Alpha - Test 5: CC1101 SPI init test (PASSED)
// Confirms CC1101 is alive and talking over SPI bus 2.
// Result: "Initializing CC1101... SUCCESS! Radio is ready on 433 MHz."
#include <RadioLib.h>
#define CC1101_SCK   4
#define CC1101_MISO  6
#define CC1101_MOSI  5
#define CC1101_CS    7
#define CC1101_GDO0  15
#define CC1101_GDO2  16
SPIClass radioSPI(HSPI);
CC1101 radio = new Module(CC1101_CS, CC1101_GDO0, RADIOLIB_NC, CC1101_GDO2, radioSPI);
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT CC1101 Test");
  radioSPI.begin(CC1101_SCK, CC1101_MISO, CC1101_MOSI, CC1101_CS);
  Serial.print("Initializing CC1101... ");
  int state = radio.begin(433.0);
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("SUCCESS!");
    Serial.println("CC1101 is alive and talking over SPI.");
    Serial.println("Radio is ready on 433 MHz.");
  } else {
    Serial.print("FAILED, code "); Serial.println(state);
    Serial.println("Check wiring: CS=7, SCK=4, MOSI=5, MISO=6, GDO0=15, VCC=3V3, GND=GND");
  }
}
void loop() { delay(1000); }
