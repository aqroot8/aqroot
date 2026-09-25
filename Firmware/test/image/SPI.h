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
  // D-800: the PINNED CORE'S behaviour, not an idealisation of it.
  // framework-arduinoespressif32 `SPIClass::begin` returns at once when the
  // bus is already running -- the new pins are IGNORED.  The model records
  // which SCK the peripheral is really bound to and every ignored begin, so
  // a caller that leaves the bus bound to the other pins is visible.
  void begin(int8_t sck = -1, int8_t miso = -1, int8_t mosi = -1,
             int8_t = -1) {
    auto &r = aqroot_hal::recorder();
    ++r.spi_begin_calls;
    if (r.spi_bound_sck != -1) {
      if (r.spi_bound_sck != sck) ++r.spi_begin_ignored_other_pins;
      return;
    }
    r.spi_bound_sck = sck;
    (void)miso; (void)mosi;
  }
  void end() { aqroot_hal::recorder().spi_bound_sck = -1; }
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
