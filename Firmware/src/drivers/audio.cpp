// AQROOT — audio driver (ESP32 I2S).
//
// Uses the ESP-IDF I2S driver (driver/i2s.h) from the Arduino framework:
//   * I2S_NUM_0 = TX to the speaker/amp  -> audio_play_tone()
//   * I2S_NUM_1 = RX from the digital mic -> audio_record()
// I2S pins in config.h are PLACEHOLDER wiring pending the final PCB.
//
// SIMULATION_MODE: Wokwi does not model I2S audio hardware, so the I2S calls are compiled
// out — audio_play_tone() just blocks for the requested duration and audio_record()
// returns a buffer of silence, so app logic that uses audio still runs.

#include "audio.h"
#include "../config.h"
#include <Arduino.h>
#include <math.h>

#ifndef SIMULATION_MODE
#include <driver/i2s.h>

static bool s_tx_ready = false;
static bool s_rx_ready = false;

void audio_init(void) {
    // --- TX (speaker) on I2S_NUM_0 ---
    i2s_config_t tx_cfg = {
        .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
        .sample_rate          = AUDIO_SAMPLE_RATE,
        .bits_per_sample      = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags     = 0,
        .dma_buf_count        = 8,
        .dma_buf_len          = 256,
        .use_apll             = false,
        .tx_desc_auto_clear   = true,
        .fixed_mclk           = 0,
    };
    i2s_pin_config_t tx_pins = {
        .mck_io_num   = I2S_PIN_NO_CHANGE,
        .bck_io_num   = I2S_BCLK,
        .ws_io_num    = I2S_LRCLK,
        .data_out_num = I2S_DOUT,
        .data_in_num  = I2S_PIN_NO_CHANGE,
    };
    if (i2s_driver_install(I2S_NUM_0, &tx_cfg, 0, NULL) == ESP_OK &&
        i2s_set_pin(I2S_NUM_0, &tx_pins) == ESP_OK) {
        s_tx_ready = true;
    }

    // --- RX (mic) on I2S_NUM_1 ---
    i2s_config_t rx_cfg = {
        .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate          = AUDIO_SAMPLE_RATE,
        .bits_per_sample      = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags     = 0,
        .dma_buf_count        = 8,
        .dma_buf_len          = 256,
        .use_apll             = false,
        .tx_desc_auto_clear   = false,
        .fixed_mclk           = 0,
    };
    i2s_pin_config_t rx_pins = {
        .mck_io_num   = I2S_PIN_NO_CHANGE,
        .bck_io_num   = I2S_BCLK,
        .ws_io_num    = I2S_LRCLK,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num  = I2S_DIN,
    };
    if (i2s_driver_install(I2S_NUM_1, &rx_cfg, 0, NULL) == ESP_OK &&
        i2s_set_pin(I2S_NUM_1, &rx_pins) == ESP_OK) {
        s_rx_ready = true;
    }
}

// Generate and play a sine tone of the given frequency for the given duration.
void audio_play_tone(int frequency_hz, int duration_ms) {
    if (!s_tx_ready || frequency_hz <= 0) return;

    const int total_samples = (AUDIO_SAMPLE_RATE * duration_ms) / 1000;
    const int chunk = 256;
    int16_t samples[chunk];
    int produced = 0;

    while (produced < total_samples) {
        int n = ((total_samples - produced) < chunk) ? (total_samples - produced) : chunk;
        for (int i = 0; i < n; i++) {
            float t = (float)(produced + i) / (float)AUDIO_SAMPLE_RATE;
            samples[i] = (int16_t)(sinf(2.0f * (float)M_PI * frequency_hz * t) * 12000.0f);
        }
        size_t written = 0;
        i2s_write(I2S_NUM_0, samples, n * sizeof(int16_t), &written, portMAX_DELAY);
        produced += n;
    }
}

// Capture raw 16-bit PCM from the mic into the buffer. Returns bytes captured.
int audio_record(unsigned char *buffer, int max_length) {
    if (!s_rx_ready) return 0;
    size_t bytes_read = 0;
    i2s_read(I2S_NUM_1, buffer, max_length, &bytes_read, portMAX_DELAY);
    return (int)bytes_read;
}

#else
// ============================ SIMULATION (no I2S hardware) ============================
void audio_init(void) {}

void audio_play_tone(int frequency_hz, int duration_ms) {
    (void)frequency_hz;
    if (duration_ms > 0) delay(duration_ms);   // keep timing behaviour for app logic
}

int audio_record(unsigned char *buffer, int max_length) {
    memset(buffer, 0, max_length);             // silence
    return max_length;
}
#endif  // SIMULATION_MODE
