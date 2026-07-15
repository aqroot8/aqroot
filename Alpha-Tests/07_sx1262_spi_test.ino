// AQROOT Alpha - Test 7: SX1262 SPI init on shared bus (PASSED)
// Waveshare Core1262 (SX1262 LoRa Node HF, 850-930MHz, 22dBm).
// GOTCHA: MOSI/MISO were swapped at first (classic SPI error) -> code -2.
// Fixed by swapping. Also BUSY=0 confirmed chip was alive before SPI worked.
#include <RadioLib.h>
#define SX_SCK    4
#define SX_MISO   6
#define SX_MOSI   5
#define SX_CS     17
#define SX_DIO1   18
#define SX_BUSY   8
#define SX_RESET  3
SPIClass radioSPI(HSPI);
SX1262 radio = new Module(SX_CS, SX_DIO1, SX_RESET, SX_BUSY, radioSPI);
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT SX1262 Test");
  radioSPI.begin(SX_SCK, SX_MISO, SX_MOSI, SX_CS);
  Serial.print("Initializing SX1262... ");
  int state = radio.begin(915.0);
  if (state == RADIOLIB_ERR_NONE) {
    Serial.println("SUCCESS!");
    Serial.println("SX1262 alive on shared SPI bus.");
  } else {
    Serial.print("FAILED, code "); Serial.println(state);
  }
}
void loop() { delay(1000); }
