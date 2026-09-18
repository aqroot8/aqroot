#pragma once
// AQROOT Demo -- the one I2C seam the hardware layer talks through.
//
// The expander driver is the most safety-relevant code on this board: it owns
// both accessory-power enables, the amplifier shutdown and every reset line.
// It is therefore written against this interface rather than against `Wire`,
// so the ORDER of the transactions it issues can be recorded and asserted on a
// host build with no ESP32 present (see `Firmware/test/test_expander_order.cpp`).
//
// `ArduinoI2cBus` is the only implementation that ships on hardware.

#include <stddef.h>
#include <stdint.h>

namespace aqroot {

class I2cBus {
 public:
  virtual ~I2cBus() {}

  // Write `length` bytes to `address`.  Returns false on NACK or bus error.
  virtual bool write(uint8_t address, const uint8_t *data, size_t length) = 0;

  // Write `reg`, repeated START, then read `length` bytes.
  virtual bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                            size_t length) = 0;

  // Address-only probe.  Returns true if the device ACKs.
  virtual bool probe(uint8_t address) = 0;
};

// Convenience: single-register write, the shape every PCAL9535A write takes.
inline bool writeRegister(I2cBus &bus, uint8_t address, uint8_t reg,
                          uint8_t value) {
  const uint8_t frame[2] = {reg, value};
  return bus.write(address, frame, sizeof(frame));
}

// Convenience: 16-bit port write.  The PCAL9535A auto-increments between the
// two registers of a port pair, so port 0 and port 1 go out in one transaction
// and cannot be observed half-applied.
inline bool writePortPair(I2cBus &bus, uint8_t address, uint8_t reg,
                          uint16_t value) {
  const uint8_t frame[3] = {reg, uint8_t(value & 0xFF), uint8_t(value >> 8)};
  return bus.write(address, frame, sizeof(frame));
}

}  // namespace aqroot
