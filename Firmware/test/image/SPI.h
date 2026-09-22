#pragma once
#include <stdint.h>
#include <stddef.h>
#include "Arduino.h"

struct SPISettings {
  SPISettings() {}
  SPISettings(uint32_t, uint8_t, uint8_t) {}
};

// D-793 / R12-03.  A SPI MODEL, SO A RETAINED RADIO STATE CAN BE INDEPENDENT
// OF THE IMAGE.
//
// Round-12 asks for a "real-image/real-driver host test with an independently
// retained CC1101 stub: keyed before MCU reset, retained through setup, then
// verify SRES/SIDLE/quiesce occurs before load authority and TX arbitration
// become permissive."  The stub has to survive the image's construction,
// which means it cannot live inside the image -- so it lives here, behind the
// same seam `Wire.h` already uses for the board model, and the test installs
// it before calling `setup()`.
namespace aqroot_hal {

struct SpiModel {
  virtual ~SpiModel() {}
  // `out` is what the image put on MOSI; the return value is MISO.
  virtual uint8_t transfer(uint8_t out) = 0;
};

inline SpiModel *&spiModel() {
  static SpiModel *m = nullptr;
  return m;
}

}  // namespace aqroot_hal

class HostSPI {
 public:
  void begin(int8_t = -1, int8_t = -1, int8_t = -1, int8_t = -1) {
    ++aqroot_hal::recorder().spi_begin_calls;
  }
  void end() {}
  void beginTransaction(SPISettings) {}
  void endTransaction() {}
  // With no model installed the host image has no silicon on the bus and
  // every read returns 0xFF, which the identity probes correctly report as
  // "no answer" -- the D-790 behaviour, unchanged.
  uint8_t transfer(uint8_t out) {
    auto *m = aqroot_hal::spiModel();
    return m ? m->transfer(out) : 0xFF;
  }
  void writeBytes(const uint8_t *, size_t) {}
};
extern HostSPI SPI;
