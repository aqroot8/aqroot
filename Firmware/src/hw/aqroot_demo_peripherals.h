#pragma once
// AQROOT Demo -- the rest of the bring-up exercises.
//
// `aqroot_demo_radios.h` proves SPI bus B.  These prove the four subsystems
// whose pin map is otherwise only provable by using the product:
//
//   microSD    a raw CMD0/CMD8 sequence.  This is the ONLY test on the board
//              that proves SPI-A MISO, because R112 is DNP and the display SDO
//              never reaches the MCU -- the card is the sole reader on that net.
//   backlight  an LEDC ramp on GPIO46.  Visible, and it also demonstrates that
//              the strap pin came out of reset low and is now firmware's.
//   IR         a 38 kHz carrier on the emitter while the TSOP38238 is sampled.
//              Emitter and receiver share the top window, so a hand or the
//              enclosure's own inner surface closes the loop.
//   audio      a tone through the MAX98357A.  Exercises AMP_SD_MODE leaving
//              shutdown, all three I2S pins, and the speaker on its flying leads.
//
// NONE of these runs at boot.  Each is a console command, because each one
// energises something -- an LED string, an IR emitter, a speaker -- and a
// bring-up image must not surprise the person holding the first board.

#include <stdint.h>

#ifdef ARDUINO
#include <Arduino.h>
#include <SPI.h>
#include <driver/i2s.h>

#include "aqroot_demo_board.h"

namespace aqroot {

// ---------------------------------------------------------------------------
// microSD (J2) over SPI-A.
//
// The card is spoken to at 400 kHz in idle mode -- the SD specification's own
// requirement, and also the speed at which a marginal connector still answers,
// which is what a first-article test wants to know.
struct SdProbeResult {
  bool responded_to_cmd0;
  uint8_t r1_cmd0;
  bool voltage_accepted;   // CMD8 echoed the 0x1AA check pattern
  uint32_t cmd8_echo;
};

inline uint8_t sdCommand(uint8_t index, uint32_t argument, uint8_t crc) {
  SPI.transfer(uint8_t(0x40 | index));
  SPI.transfer(uint8_t(argument >> 24));
  SPI.transfer(uint8_t(argument >> 16));
  SPI.transfer(uint8_t(argument >> 8));
  SPI.transfer(uint8_t(argument));
  SPI.transfer(crc);
  for (int i = 0; i < 10; ++i) {
    const uint8_t response = SPI.transfer(0xFF);
    if ((response & 0x80) == 0) return response;
  }
  return 0xFF;
}

inline SdProbeResult probeSdCard() {
  SdProbeResult result = {false, 0xFF, false, 0};

  // The display shares SCK/MOSI; hold its select high for the whole sequence.
  digitalWrite(AQROOT_PIN_DISP_CS_N, HIGH);

  SPI.begin(AQROOT_PIN_SPI_A_SCK, AQROOT_PIN_SPI_A_MISO, AQROOT_PIN_SPI_A_MOSI,
            -1);
  SPI.beginTransaction(SPISettings(400000, MSBFIRST, SPI_MODE0));

  // 74+ clocks with CS high is how a card is told to enter native SPI mode.
  digitalWrite(AQROOT_PIN_SD_CS_N, HIGH);
  for (int i = 0; i < 10; ++i) SPI.transfer(0xFF);

  digitalWrite(AQROOT_PIN_SD_CS_N, LOW);
  result.r1_cmd0 = sdCommand(0, 0x00000000, 0x95);   // GO_IDLE_STATE
  result.responded_to_cmd0 = (result.r1_cmd0 == 0x01);

  if (result.responded_to_cmd0) {
    // SEND_IF_COND: 2.7-3.6 V, check pattern 0xAA.  A v2 card echoes both back.
    const uint8_t r1 = sdCommand(8, 0x000001AA, 0x87);
    if (r1 == 0x01) {
      uint32_t echo = 0;
      for (int i = 0; i < 4; ++i) echo = (echo << 8) | SPI.transfer(0xFF);
      result.cmd8_echo = echo;
      result.voltage_accepted = ((echo & 0xFFF) == 0x1AA);
    }
  }

  digitalWrite(AQROOT_PIN_SD_CS_N, HIGH);
  SPI.transfer(0xFF);
  SPI.endTransaction();
  SPI.end();
  return result;
}

// ---------------------------------------------------------------------------
// Backlight: U17 TPS61169 WLED boost, enabled and dimmed from GPIO46 through
// R109.  GPIO46 is a strapping pin held low by R108 at reset, so this is also
// the moment the strap stops being a strap.
inline void backlightRamp(uint8_t channel = 0) {
  ledcSetup(channel, 5000, 8);
  ledcAttachPin(AQROOT_PIN_DISP_BL_PWM, channel);
  for (int duty = 0; duty <= 255; duty += 5) {
    ledcWrite(channel, duty);
    delay(8);
  }
  for (int duty = 255; duty >= 0; duty -= 5) {
    ledcWrite(channel, duty);
    delay(8);
  }
  ledcWrite(channel, 0);
  ledcDetachPin(AQROOT_PIN_DISP_BL_PWM);
  pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
  digitalWrite(AQROOT_PIN_DISP_BL_PWM, LOW);
}

// ---------------------------------------------------------------------------
// IR: 38 kHz carrier out of D1 through Q1, sampled on the TSOP38238's
// demodulated output.  The receiver is ACTIVE LOW and needs a burst of at least
// ~10 carrier cycles before it asserts, so the carrier runs for 2 ms and the
// output is sampled across it.
struct IrSelfTest {
  uint16_t low_samples;
  uint16_t total_samples;
  bool detected;
};

inline IrSelfTest irSelfTest(uint8_t channel = 1) {
  IrSelfTest result = {0, 0, false};
  ledcSetup(channel, 38000, 8);
  ledcAttachPin(AQROOT_PIN_IR_TX, channel);
  ledcWrite(channel, 128);            // 50 % duty at 38 kHz
  const uint32_t deadline = millis() + 2;
  while (millis() <= deadline) {
    ++result.total_samples;
    if (digitalRead(AQROOT_PIN_IR_RX) == LOW) ++result.low_samples;
  }
  ledcWrite(channel, 0);
  ledcDetachPin(AQROOT_PIN_IR_TX);
  pinMode(AQROOT_PIN_IR_TX, OUTPUT);
  digitalWrite(AQROOT_PIN_IR_TX, LOW);   // R23 holds the gate down anyway
  // The TSOP38238 idles HIGH, so any sustained LOW during the burst is the
  // receiver seeing the emitter.  Reflection-dependent: report the ratio and
  // let the operator decide, rather than asserting a pass.
  result.detected = result.total_samples > 0 &&
                    result.low_samples > (result.total_samples / 4);
  return result;
}

// ---------------------------------------------------------------------------
// Audio: a tone through the MAX98357A.
//
// THE MONO SAMPLE GOES INTO BOTH SLOTS.  SD_MODE is driven straight to +3V3 by
// U2.P03 with R15 100k to GND, which puts the pin in the MAX98357A's top
// channel-select band -- a SINGLE channel, not the (L+R)/2 average.  Writing
// the same sample to left and right makes the board work whichever slot the
// part picks, and removes a first-article failure whose symptom is silence.
inline bool playTone(uint32_t hz, uint32_t ms, uint16_t amplitude = 6000) {
  const uint32_t rate = 44100;
  i2s_config_t config = {};
  config.mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_TX);
  config.sample_rate = rate;
  config.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  config.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  config.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  config.intr_alloc_flags = 0;
  config.dma_buf_count = 6;
  config.dma_buf_len = 256;
  config.use_apll = false;

  i2s_pin_config_t pins = {};
  pins.bck_io_num = AQROOT_PIN_I2S_BCLK;
  pins.ws_io_num = AQROOT_PIN_I2S_LRCLK;
  pins.data_out_num = AQROOT_PIN_I2S_SPK_DOUT;
  pins.data_in_num = I2S_PIN_NO_CHANGE;

  if (i2s_driver_install(I2S_NUM_0, &config, 0, nullptr) != ESP_OK) return false;
  if (i2s_set_pin(I2S_NUM_0, &pins) != ESP_OK) {
    i2s_driver_uninstall(I2S_NUM_0);
    return false;
  }

  const uint32_t frames = (rate * ms) / 1000;
  int16_t block[128 * 2];
  uint32_t written_frames = 0;
  uint32_t phase = 0;
  const uint32_t step = (hz * 0x10000u) / rate;
  while (written_frames < frames) {
    for (size_t i = 0; i < 128; ++i) {
      // A square wave: no sine table, and the amplifier's own filter shapes it.
      const int16_t sample =
          ((phase & 0x8000u) ? int16_t(amplitude) : int16_t(-amplitude));
      block[i * 2] = sample;        // left slot
      block[i * 2 + 1] = sample;    // right slot -- same sample, deliberately
      phase += step;
    }
    size_t bytes = 0;
    i2s_write(I2S_NUM_0, block, sizeof(block), &bytes, portMAX_DELAY);
    written_frames += 128;
  }
  i2s_zero_dma_buffer(I2S_NUM_0);
  i2s_driver_uninstall(I2S_NUM_0);
  return true;
}

}  // namespace aqroot
#endif  // ARDUINO
