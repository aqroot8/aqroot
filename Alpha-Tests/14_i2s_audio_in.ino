/*
 * AQROOT ALPHA TEST 14 - I2S AUDIO IN (ICS-43434)
 * -----------------------------------------------
 * Board : ESP32S3 Dev Module | USB CDC On Boot = ENABLED
 * Lib   : none - ESP_I2S ships with Arduino core 3.x
 *
 * WIRING (ICS-43434):
 *   3V   -> 3V3    GND  -> GND
 *   BCLK -> GPIO 38    LRCL -> GPIO 47    DOUT -> GPIO 9
 *   SEL  -> GND   (left channel; matches I2S_STD_SLOT_LEFT below)
 *
 * The ICS-43434 is a 24-bit mic in 32-bit slots, left-justified,
 * so we read 32-bit and shift right 8.
 *
 * RESULT (2026-07-26): INCONCLUSIVE - suspected DEAD single mic unit.
 * Output was flat 0x00000000 (peak 0) on both GPIO 9 and GPIO 3, on
 * both LEFT and RIGHT slots. Everything around the mic verified good:
 *   - power 3V = 2.98V, SEL = 0V
 *   - continuity confirmed: DOUT->GPIO, BCLK->38, LRCL->47
 *   - BCLK measured 1.5V at the mic = ESP32 IS clocking it correctly
 *   - DOUT idled at flat 0V (a live mic receiving clocks should not)
 * Since the MAX98357A on the SAME I2S bus works, the bus/clocks/pins
 * are all proven good. Conclusion: dead individual mic. Only had one.
 * ACTION: retest with a FRESH ICS-43434. Part choice remains LOCKED;
 * this is a bad unit, not a design/part issue. Does NOT block Beta.
 *
 * Key: c = recalibrate noise floor
 */

#include <Arduino.h>
#include <ESP_I2S.h>

#define I2S_BCLK 38
#define I2S_LRCK 47
#define I2S_DIN   9
#define SAMPLE_RATE 16000
#define FULL_SCALE  8388607L

I2SClass i2s;
const int kSamples = 512;
int32_t   sampleBuf[kSamples];
bool      ready = false;

bool readBlock(int32_t &peak, int32_t &rms) {
  size_t got = i2s.readBytes((char *)sampleBuf, sizeof(sampleBuf));
  int n = got / sizeof(int32_t);
  if (n <= 0) { peak = rms = 0; return false; }
  int64_t sumsq = 0; int32_t pk = 0;
  for (int i = 0; i < n; i++) {
    int32_t s = sampleBuf[i] >> 8;
    int32_t a = s < 0 ? -s : s;
    if (a > pk) pk = a;
    sumsq += (int64_t)s * (int64_t)s;
  }
  peak = pk; rms = (int32_t)sqrt((double)(sumsq / n));
  return true;
}
void calibrate() {
  Serial.println(F("  noise floor - stay quiet 2s..."));
  int32_t worst = 0; uint32_t start = millis();
  while (millis() - start < 2000) { int32_t pk, rms; if (readBlock(pk, rms) && rms > worst) worst = rms; }
  Serial.printf ("  noise floor RMS: %ld\n\n", (long)worst);
}
void drawBar(int32_t rms, int32_t peak) {
  const int kWidth = 40;
  double norm = (double)rms / (double)(FULL_SCALE / 40);
  if (norm > 1.0) norm = 1.0;
  int filled = (int)(norm * kWidth);
  char bar[kWidth + 1];
  for (int i = 0; i < kWidth; i++) bar[i] = (i < filled) ? '#' : '.';
  bar[kWidth] = '\0';
  Serial.printf("  [%s] rms %7ld  peak %7ld\n", bar, (long)rms, (long)peak);
}

void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 3000) delay(10);
  delay(300);

  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F(" AQROOT TEST 14 - I2S AUDIO IN"));
  Serial.println(F("========================================"));
  Serial.printf ("  BCLK %d | LRCK %d | DIN %d\n", I2S_BCLK, I2S_LRCK, I2S_DIN);

  i2s.setPins(I2S_BCLK, I2S_LRCK, -1, I2S_DIN, -1);
  if (!i2s.begin(I2S_MODE_STD, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT)) {
    Serial.println(F("  !! I2S begin FAILED"));
    return;
  }
  ready = true;
  Serial.println(F("  I2S initialized OK."));
  Serial.println();
  delay(500);
  calibrate();
  Serial.println(F("  >>> TAP THE MIC or TALK AT IT <<<"));
  Serial.println(F("  'c' recalibrates"));
  Serial.println();
}

void loop() {
  if (!ready) { delay(500); return; }
  static uint32_t lastPrint = 0;
  static int32_t holdPeak = 0, holdRms = 0;
  int32_t pk, rms;
  if (readBlock(pk, rms)) { if (pk > holdPeak) holdPeak = pk; if (rms > holdRms) holdRms = rms; }
  if (millis() - lastPrint > 150) {
    lastPrint = millis();
    drawBar(holdRms, holdPeak);
    if (holdPeak == 0) Serial.println(F("  !! all zeros - check DOUT->9, SEL->GND, 3V power"));
    holdPeak = holdRms = 0;
  }
  if (Serial.available()) { int c = Serial.read(); if (c=='c'||c=='C') calibrate(); }
}
