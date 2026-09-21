#pragma once
#include <stdint.h>
#include <stddef.h>
#include "../Arduino.h"

typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1

typedef enum {
  I2S_MODE_MASTER = 1, I2S_MODE_SLAVE = 2, I2S_MODE_TX = 4, I2S_MODE_RX = 8,
} i2s_mode_t;
typedef enum { I2S_BITS_PER_SAMPLE_16BIT = 16, I2S_BITS_PER_SAMPLE_24BIT = 24,
               I2S_BITS_PER_SAMPLE_32BIT = 32 } i2s_bits_per_sample_t;
typedef enum { I2S_CHANNEL_FMT_RIGHT_LEFT = 0, I2S_CHANNEL_FMT_ONLY_LEFT = 1,
               I2S_CHANNEL_FMT_ONLY_RIGHT = 2 } i2s_channel_fmt_t;
typedef enum { I2S_COMM_FORMAT_STAND_I2S = 1, I2S_COMM_FORMAT_I2S = 1,
               I2S_COMM_FORMAT_I2S_MSB = 2 } i2s_comm_format_t;
typedef enum { I2S_NUM_0 = 0, I2S_NUM_1 = 1 } i2s_port_t;
#define ESP_INTR_FLAG_LEVEL1 (1 << 1)
#define I2S_PIN_NO_CHANGE (-1)
#define portMAX_DELAY 0xFFFFFFFFu
#define pdMS_TO_TICKS(x) (x)

typedef struct {
  i2s_mode_t mode;
  int sample_rate;
  i2s_bits_per_sample_t bits_per_sample;
  i2s_channel_fmt_t channel_format;
  int communication_format;
  int intr_alloc_flags;
  int dma_buf_count;
  int dma_buf_len;
  bool use_apll;
  bool tx_desc_auto_clear;
  int fixed_mclk;
} i2s_config_t;

typedef struct {
  int bck_io_num;
  int ws_io_num;
  int data_out_num;
  int data_in_num;
  int mck_io_num;
} i2s_pin_config_t;

inline esp_err_t i2s_driver_install(i2s_port_t, const i2s_config_t *, int,
                                    void *) {
  ++aqroot_hal::recorder().i2s_installs;
  return ESP_OK;
}
inline esp_err_t i2s_driver_uninstall(i2s_port_t) { return ESP_OK; }
inline esp_err_t i2s_set_pin(i2s_port_t, const i2s_pin_config_t *) {
  return ESP_OK;
}
inline esp_err_t i2s_zero_dma_buffer(i2s_port_t) { return ESP_OK; }
inline esp_err_t i2s_write(i2s_port_t, const void *, size_t bytes,
                           size_t *written, uint32_t) {
  if (written) *written = bytes;
  return ESP_OK;
}
inline esp_err_t i2s_read(i2s_port_t, void *dest, size_t bytes, size_t *read,
                          uint32_t) {
  for (size_t i = 0; i < bytes; ++i) ((uint8_t *)dest)[i] = 0;
  if (read) *read = bytes;
  return ESP_OK;
}
