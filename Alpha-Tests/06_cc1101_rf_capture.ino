// AQROOT Alpha - Test 6: CC1101 RF reception test (PASSED)
// Measures noise floor, then detects real 433MHz transmissions via RSSI jump.
// Result: noise floor ~-87 dBm; a 433MHz car key fob press spiked RSSI to
// -38..-50 dBm (~40 dB above noise) = confirmed real RF reception.
// NOTE: this proves RECEPTION only. Full capture-and-replay of a specific
// waveform is later firmware work, not Alpha hardware validation.
#include <RadioLib.h>
#define CC1101_SCK   4
#define CC1101_MISO  6
#define CC1101_MOSI  5
#define CC1101_CS    7
#define CC1101_GDO0  15
#define CC1101_GDO2  16
SPIClass radioSPI(HSPI);
CC1101 radio = new Module(CC1101_CS, CC1101_GDO0, RADIOLIB_NC, CC1101_GDO2, radioSPI);
float noiseFloor = -100.0;
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nAQROOT CC1101 RSSI Capture Test");
  radioSPI.begin(CC1101_SCK, CC1101_MISO, CC1101_MOSI, CC1101_CS);
  Serial.print("Init CC1101... ");
  int state = radio.begin(433.92);
  if (state != RADIOLIB_ERR_NONE) {
    Serial.print("FAILED code "); Serial.println(state);
    while (true) delay(1000);
  }
  Serial.println("OK");
  radio.setOOK(true);
  radio.setRxBandwidth(135.0);
  radio.receiveDirect();
  Serial.println("Measuring noise floor (stay quiet, don't press remote)...");
  float sum = 0; int n = 0;
  unsigned long t = millis();
  while (millis() - t < 2000) { sum += radio.getRSSI(); n++; delay(10); }
  noiseFloor = sum / n;
  Serial.print("Noise floor: "); Serial.print(noiseFloor); Serial.println(" dBm");
  Serial.println("Now press your 433MHz remote near the antenna.\n");
}
void loop() {
  float rssi = radio.getRSSI();
  if (rssi > noiseFloor + 15.0) {
    Serial.print(">>> SIGNAL! RSSI = "); Serial.print(rssi);
    Serial.println(" dBm (transmission detected)");
    delay(200);
  }
  delay(20);
}
