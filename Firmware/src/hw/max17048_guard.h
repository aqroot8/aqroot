#pragma once
// AQROOT Demo -- safety-facing MAX17048 VCELL gate.
//
// Accessory permission depends on VCELL.  A successful register read is not
// enough: the gauge must first be proven in active (non-hibernate) mode.  The
// guard verifies both HIBRT=0 and MODE.HibStat=0, and rechecks them before every
// VCELL value used by the power policy. ADI 19-6171 Rev.7 is archived as
// vendor/ADI/max17048-max17049-rev7.pdf; its hash and safety-relevant facts are
// pinned by the adjacent source record and firmware hardware-map contract.

#include <stdint.h>

#include "aqroot_accessory_power_policy.h"
#include "aqroot_i2c.h"

namespace aqroot {

class Max17048Guard {
 public:
  explicit Max17048Guard(uint8_t address)
      : address_(address), active_ready_(false) {}

  bool configureActiveMode(I2cBus &bus) {
    const uint8_t frame[3] = {kRegHibrt, 0x00, 0x00};
    uint8_t verify[2] = {0xFF, 0xFF};
    uint8_t mode_raw[2] = {0xFF, 0xFF};
    const bool wrote = bus.write(address_, frame, sizeof(frame));
    const bool readback = wrote &&
        bus.readRegister(address_, kRegHibrt, verify, sizeof(verify));
    const bool mode_read = readback &&
        bus.readRegister(address_, kRegMode, mode_raw, sizeof(mode_raw));
    const uint16_t mode =
        (uint16_t(mode_raw[0]) << 8) | uint16_t(mode_raw[1]);
    active_ready_ = mode_read && verify[0] == 0x00 && verify[1] == 0x00 &&
                    (mode & kModeHibStatMask) == 0;
    return active_ready_;
  }

  void invalidate() { active_ready_ = false; }
  bool activeReady() const { return active_ready_; }

  bool verifyActiveMode(I2cBus &bus) {
    if (!active_ready_) return false;
    uint8_t verify[2] = {0xFF, 0xFF};
    uint8_t mode_raw[2] = {0xFF, 0xFF};
    if (!bus.readRegister(address_, kRegHibrt, verify, sizeof(verify)) ||
        verify[0] != 0x00 || verify[1] != 0x00 ||
        !bus.readRegister(address_, kRegMode, mode_raw, sizeof(mode_raw))) {
      active_ready_ = false;
      return false;
    }
    const uint16_t mode =
        (uint16_t(mode_raw[0]) << 8) | uint16_t(mode_raw[1]);
    if ((mode & kModeHibStatMask) != 0) {
      active_ready_ = false;
      return false;
    }
    return true;
  }

  bool readVcell(I2cBus &bus, float *volts) {
    if (!volts || !verifyActiveMode(bus)) return false;
    uint8_t raw[2] = {0, 0};
    if (!bus.readRegister(address_, kRegVcell, raw, sizeof(raw))) {
      active_ready_ = false;
      return false;
    }
    const uint16_t counts = (uint16_t(raw[0]) << 8) | uint16_t(raw[1]);
    const float v = float(counts) * kVcellLsbV;
    *volts = v;
    if (counts == 0x0000 || counts == 0xFFFF || !vcellIsPlausible(v)) {
      active_ready_ = false;
      return false;
    }
    return true;
  }

  static constexpr uint8_t kRegVcell = 0x02;
  static constexpr uint8_t kRegMode = 0x06;
  static constexpr uint8_t kRegHibrt = 0x0A;
  static constexpr uint16_t kModeHibStatMask = 0x1000;
  static constexpr float kVcellLsbV = 0.000078125f;

 private:
  uint8_t address_;
  bool active_ready_;
};

}  // namespace aqroot
