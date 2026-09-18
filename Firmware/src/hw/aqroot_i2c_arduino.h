#pragma once
// AQROOT Demo -- the shipping I2C bus: Arduino `Wire` on the ESP32-S3.
//
// Bring-up order matters.  `AQROOT_I2C_BRINGUP_HZ` is the speed the bus is
// opened at and `AQROOT_I2C_RUN_HZ` the speed it is raised to only after every
// expected device has ACKed, because a board that half-works at 400 kHz and
// works at 100 kHz is a signal-integrity finding, not a firmware bug, and the
// bring-up target has to be able to tell them apart.

#include "aqroot_i2c.h"

#ifdef ARDUINO
#include <Wire.h>

#include "aqroot_demo_board.h"

namespace aqroot {

class ArduinoI2cBus : public I2cBus {
 public:
  bool begin(uint32_t hz = AQROOT_I2C_BRINGUP_HZ) {
    return Wire.begin(AQROOT_I2C_SDA_GPIO, AQROOT_I2C_SCL_GPIO, hz);
  }

  void setClock(uint32_t hz) { Wire.setClock(hz); }

  bool write(uint8_t address, const uint8_t *data, size_t length) override {
    Wire.beginTransmission(address);
    Wire.write(data, length);
    return Wire.endTransmission() == 0;
  }

  bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                    size_t length) override {
    Wire.beginTransmission(address);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
      return false;
    }
    if (Wire.requestFrom(address, uint8_t(length)) != length) {
      return false;
    }
    for (size_t i = 0; i < length; ++i) {
      data[i] = uint8_t(Wire.read());
    }
    return true;
  }

  bool probe(uint8_t address) override {
    Wire.beginTransmission(address);
    return Wire.endTransmission() == 0;
  }
};

}  // namespace aqroot
#endif  // ARDUINO
