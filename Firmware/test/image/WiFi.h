#pragma once
// AQROOT Demo -- D-801 / D801-01.  THE HOST Wi-Fi SURFACE THE FAP-01 IMAGE USES.
//
// Only `src/fap01/` includes this, and only the FAP-01 build compiles
// `src/fap01/`.  The release image never includes it: `test_fap01_image.cpp`,
// compiled against the release sources, proves every counter here stays zero
// whatever the operator types.  It records what the image ASKED the radio to
// do -- the mode, the TX power, the raw frames -- and nothing more.
#include <stdint.h>
#include <stddef.h>
#include "Arduino.h"

typedef enum { WIFI_MODE_NULL = 0, WIFI_MODE_STA = 1, WIFI_MODE_AP = 2 } wifi_mode_t;
#define WIFI_OFF WIFI_MODE_NULL
#define WIFI_STA WIFI_MODE_STA
typedef enum { WIFI_POWER_19_5dBm = 78 } wifi_power_t;

namespace aqroot_hal {
struct WifiRecord {
  int mode_calls = 0;
  int sta_starts = 0;
  int off_calls = 0;
  int current_mode = WIFI_MODE_NULL;
  int tx_power = 0;
  uint64_t frames = 0;
  uint64_t frames_while_off = 0;
  uint64_t first_on_us = 0;
  uint64_t last_off_us = 0;
  void reset() { *this = WifiRecord(); }
};
inline WifiRecord &wifi() {
  static WifiRecord w;
  return w;
}
}  // namespace aqroot_hal

class HostWiFi {
 public:
  bool mode(wifi_mode_t m) {
    auto &w = aqroot_hal::wifi();
    ++w.mode_calls;
    if (m == WIFI_MODE_STA && w.current_mode != WIFI_MODE_STA) {
      ++w.sta_starts;
      if (w.first_on_us == 0) w.first_on_us = aqroot_hal::recorder().clock_us;
    }
    if (m == WIFI_MODE_NULL) {
      ++w.off_calls;
      w.last_off_us = aqroot_hal::recorder().clock_us;
    }
    w.current_mode = m;
    return true;
  }
  bool setTxPower(wifi_power_t p) {
    aqroot_hal::wifi().tx_power = int(p);
    return true;
  }
};
inline HostWiFi WiFi;
