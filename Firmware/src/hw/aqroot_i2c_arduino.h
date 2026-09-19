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
#include <Arduino.h>
#include <Wire.h>

#include "aqroot_demo_board.h"

namespace aqroot {

class ArduinoI2cBus : public I2cBus {
 public:
  // D-766 / round-2 review: an MCU reset can occur while a slave is halfway
  // through a read.  The slave may then hold SDA low while the new firmware
  // instance is trying to write the safety latches.  Recover the bus BEFORE
  // Wire owns the pins: release SDA/SCL, clock up to nine bits, then emit a
  // STOP.  If either line is still stuck, begin() fails closed.
  bool recoverStuckBus() {
    pinMode(AQROOT_I2C_SDA_GPIO, INPUT_PULLUP);
    pinMode(AQROOT_I2C_SCL_GPIO, INPUT_PULLUP);
    delayMicroseconds(5);

    if (digitalRead(AQROOT_I2C_SCL_GPIO) == LOW) return false;
    if (digitalRead(AQROOT_I2C_SDA_GPIO) == LOW) {
      for (int i = 0; i < 9 && digitalRead(AQROOT_I2C_SDA_GPIO) == LOW; ++i) {
        pinMode(AQROOT_I2C_SCL_GPIO, OUTPUT_OPEN_DRAIN);
        digitalWrite(AQROOT_I2C_SCL_GPIO, LOW);
        delayMicroseconds(5);
        pinMode(AQROOT_I2C_SCL_GPIO, INPUT_PULLUP);
        delayMicroseconds(5);
        if (digitalRead(AQROOT_I2C_SCL_GPIO) == LOW) return false;
      }

      // STOP: SDA low while SCL is released high, then release SDA.
      pinMode(AQROOT_I2C_SDA_GPIO, OUTPUT_OPEN_DRAIN);
      digitalWrite(AQROOT_I2C_SDA_GPIO, LOW);
      delayMicroseconds(5);
      pinMode(AQROOT_I2C_SCL_GPIO, INPUT_PULLUP);
      delayMicroseconds(5);
      pinMode(AQROOT_I2C_SDA_GPIO, INPUT_PULLUP);
      delayMicroseconds(5);
    }
    return digitalRead(AQROOT_I2C_SDA_GPIO) == HIGH &&
           digitalRead(AQROOT_I2C_SCL_GPIO) == HIGH;
  }

  bool begin(uint32_t hz = AQROOT_I2C_BRINGUP_HZ) {
    if (!recoverStuckBus()) return false;
    return Wire.begin(AQROOT_I2C_SDA_GPIO, AQROOT_I2C_SCL_GPIO, hz);
  }

  bool reopen(uint32_t hz = AQROOT_I2C_BRINGUP_HZ) {
    Wire.end();
    return begin(hz);
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
