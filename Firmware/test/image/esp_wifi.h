#pragma once
// AQROOT Demo -- D-801 / D801-01.  Host stand-in for the two ESP-IDF 4.4 Wi-Fi
// calls the FAP-01 image makes.  See `WiFi.h` beside it.
#include "WiFi.h"

#ifndef ESP_OK
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#endif
typedef enum { WIFI_IF_STA = 0, WIFI_IF_AP = 1 } wifi_interface_t;
typedef enum { WIFI_PS_NONE = 0 } wifi_ps_type_t;

inline esp_err_t esp_wifi_set_ps(wifi_ps_type_t) { return ESP_OK; }
inline esp_err_t esp_wifi_80211_tx(wifi_interface_t, const void *buffer,
                                   int len, bool) {
  auto &w = aqroot_hal::wifi();
  if (buffer == nullptr || len < 24) return ESP_FAIL;
  if (w.current_mode == WIFI_MODE_NULL) {
    ++w.frames_while_off;
    return ESP_FAIL;
  }
  ++w.frames;
  return ESP_OK;
}
