/*
 * AQROOT ALPHA TEST 13 - I2S AUDIO OUT (MAX98357A) [PASSED 2026-07-26]
 * -------------------------------------------------------------------
 * Board : ESP32S3 Dev Module | USB CDC On Boot = ENABLED
 *         Native USB | 16MB flash | OPI PSRAM
 * Lib   : none - ESP_I2S ships with Arduino core 3.x
 *
 * WIRING (MAX98357A):
 *   LRC  -> GPIO 47    BCLK -> GPIO 38    DIN -> GPIO 48
 *   Vin  -> 3V3        GND  -> GND
 *   GAIN -> unconnected (default 9dB)
 *   SD   -> unconnected (this board has a pull-up; measured 2.98V = enabled)
 *   Speaker across the + and - pads (measured 8.3 ohm, good).
 *
 * Bench pins 38/47/48. Beta map uses 39/40/41 (those collide with
 * microSD/NFC/touch on this bench). Pin choice does not affect the
 * Beta design - this validates the parts + I2S pipeline.
 *
 * RESULT: PASSED. Beeps + 440Hz/1kHz tones audible on a real speaker.
 * Validates the ESP32 I2S peripheral, clocking, pin map, audio-OUT path.
 *
 * Keys: t=tone  s=sweep  b=beeps  x=silence
 */

#include <Arduino.h>
#include <ESP_I2S.h>

#define I2S_BCLK 38
#define I2S_LRCK 47
#define I2S_DOUT 48
#define SAMPLE_RATE 16000
#define AMPLITUDE   6000

I2SClass i2s;
const int kFrames = 256;
int16_t   frameBuf[kFrames * 2];
float     phase = 0.0f;
bool      ready = false;

void fillTone(float freq) {
  float inc = 2.0f * PI * freq / (float)SAMPLE_RATE;
  for (int i = 0; i < kFrames; i++) {
    int16_t s = (int16_t)(sinf(phase) * AMPLITUDE);
    frameBuf[i * 2] = s; frameBuf[i * 2 + 1] = s;
    phase += inc;
    if (phase > 2.0f * PI) phase -= 2.0f * PI;
  }
}
void playTone(float freq, uint32_t ms) {
  uint32_t start = millis();
  while (millis() - start < ms) { fillTone(freq); i2s.write((uint8_t *)frameBuf, sizeof(frameBuf)); }
}
void silence(uint32_t ms) {
  memset(frameBuf, 0, sizeof(frameBuf));
  uint32_t start = millis();
  while (millis() - start < ms) i2s.write((uint8_t *)frameBuf, sizeof(frameBuf));
}
void doTone()  { Serial.println(F("  440 Hz, 2s...")); playTone(440.0f, 2000); silence(50); Serial.println(F("  done.")); }
void doSweep() { Serial.println(F("  sweep 200->2000 Hz...")); for (float f=200; f<=2000; f+=40) playTone(f,40); silence(50); Serial.println(F("  done.")); }
void doBeeps() { Serial.println(F("  three beeps...")); for (int i=0;i<3;i++){ playTone(880.0f,150); silence(120);} Serial.println(F("  done.")); }

void setup() {
  Serial.begin(115200);
  uint32_t t0 = millis();
  while (!Serial && (millis() - t0) < 3000) delay(10);
  delay(300);

  Serial.println();
  Serial.println(F("========================================"));
  Serial.println(F(" AQROOT TEST 13 - I2S AUDIO OUT"));
  Serial.println(F("========================================"));
  Serial.printf ("  BCLK %d | LRCK %d | DOUT %d\n", I2S_BCLK, I2S_LRCK, I2S_DOUT);

  i2s.setPins(I2S_BCLK, I2S_LRCK, I2S_DOUT, -1, -1);
  if (!i2s.begin(I2S_MODE_STD, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO)) {
    Serial.println(F("  !! I2S begin FAILED"));
    return;
  }
  ready = true;
  Serial.println(F("  I2S initialized OK."));
  Serial.println(F("  Keys: t=tone  s=sweep  b=beeps  x=silence"));
  Serial.println();

  delay(1000);
  Serial.println(F("### AUTO TEST ###"));
  doBeeps(); delay(400); doTone();
  Serial.println();
  Serial.println(F("  Heard it? -> amp + speaker PASS"));
  Serial.println();
}

void loop() {
  if (!ready) { delay(500); return; }
  if (Serial.available()) {
    int c = Serial.read();
    if      (c=='t'||c=='T') doTone();
    else if (c=='s'||c=='S') doSweep();
    else if (c=='b'||c=='B') doBeeps();
    else if (c=='x'||c=='X') { Serial.println(F("  silence 1s")); silence(1000); }
  }
}
