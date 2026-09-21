#pragma once
#include <stdint.h>
#include <stddef.h>
#include "Arduino.h"

struct SPISettings {
  SPISettings() {}
  SPISettings(uint32_t, uint8_t, uint8_t) {}
};

class HostSPI {
 public:
  void begin(int8_t = -1, int8_t = -1, int8_t = -1, int8_t = -1) {
    ++aqroot_hal::recorder().spi_begin_calls;
  }
  void end() {}
  void beginTransaction(SPISettings) {}
  void endTransaction() {}
  // The host image has no silicon on the bus: every read returns 0xFF, which
  // the identity probes correctly report as "no answer".
  uint8_t transfer(uint8_t) { return 0xFF; }
  void writeBytes(const uint8_t *, size_t) {}
};
extern HostSPI SPI;
