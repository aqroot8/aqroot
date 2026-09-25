#pragma once
// AQROOT Demo -- D-801 / D801-01.  Host stand-in for the ESP32 core's NVS
// `Preferences`, used ONLY by the FAP-01 image to carry an armed chip-select
// hold-off across ONE warm reset.  The store deliberately survives
// `aqroot_hal::recorder().reset()` -- that is what non-volatile means, and it
// is what lets the test reset the MCU and keep the injection -- and a test
// clears it explicitly with `aqroot_hal::nvs().clear()`.
#include <stdint.h>
#include <map>
#include <string>

namespace aqroot_hal {
inline std::map<std::string, uint8_t> &nvs() {
  static std::map<std::string, uint8_t> store;
  return store;
}
inline int &nvsWrites() {
  static int n = 0;
  return n;
}
}  // namespace aqroot_hal

class Preferences {
 public:
  bool begin(const char *name, bool read_only = false, const char * = nullptr) {
    ns_ = name ? name : "";
    ro_ = read_only;
    return true;
  }
  void end() {}
  uint8_t getUChar(const char *key, uint8_t def = 0) {
    auto it = aqroot_hal::nvs().find(ns_ + "/" + key);
    return it == aqroot_hal::nvs().end() ? def : it->second;
  }
  size_t putUChar(const char *key, uint8_t value) {
    if (ro_) return 0;
    aqroot_hal::nvs()[ns_ + "/" + key] = value;
    ++aqroot_hal::nvsWrites();
    return 1;
  }
  bool remove(const char *key) {
    if (ro_) return false;
    ++aqroot_hal::nvsWrites();
    return aqroot_hal::nvs().erase(ns_ + "/" + key) > 0;
  }

 private:
  std::string ns_;
  bool ro_ = false;
};
