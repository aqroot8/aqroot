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

  // D-790 / D789-A10.  HIBERNATE IS NOT THE ONLY WAY THIS PART STOPS
  // CONVERTING, AND THE OTHER WAY SURVIVES A WARM RESET.
  //
  // ADI 19-6171 Rev.7, Sleep Mode: "To enter sleep mode, write MODE.EnSleep =
  // 1 and either hold SDA and SCL logic-low for a period for tSLEEP ... or
  // write CONFIG.SLEEP = 1.  To wake up the IC, write CONFIG.SLEEP = 0.
  // OTHER COMMUNICATION DOES NOT WAKE UP THE IC."  Sleep is INDEPENDENT of
  // hibernate: `MODE.HibStat` stays 0 through it, `HIBRT` stays 0 through it,
  // and a gauge that was put to sleep before an MCU reset is still asleep
  // afterwards -- so the D-779/D-784 guard, which checked only HIBRT and
  // HibStat, qualified a part that had stopped converting and authorised a
  // safety decision on a VCELL that could be arbitrarily stale.
  //
  // The qualification now CLEARS forced sleep explicitly and VERIFIES it,
  // BEFORE the settle is spent, and it preserves everything else in CONFIG:
  // RCOMP (POR 0x97), ALSC, ALRT and ATHD are read, the SLEEP bit alone is
  // masked out, and the rest is written back unchanged.  `MODE.EnSleep` is
  // cleared with a MODE write of 0x0000, which is also the only safe value --
  // setting bit 14 would command a QUICK-START and throw the SOC estimate
  // away.  An unreadable CONFIG or MODE is FAIL-CLOSED, not assumed awake.
  bool clearForcedSleep(I2cBus &bus) {
    uint8_t cfg[2] = {0xFF, 0xFF};
    if (!bus.readRegister(address_, kRegConfig, cfg, sizeof(cfg))) return false;
    const uint16_t before = (uint16_t(cfg[0]) << 8) | uint16_t(cfg[1]);
    const uint16_t wanted = uint16_t(before & ~kConfigSleepMask);
    if (wanted != before) {
      const uint8_t frame[3] = {kRegConfig, uint8_t(wanted >> 8),
                                uint8_t(wanted & 0xFF)};
      if (!bus.write(address_, frame, sizeof(frame))) return false;
    }
    // MODE.EnSleep: a write of 0x0000 clears it and commands nothing.
    const uint8_t mode_frame[3] = {kRegMode, 0x00, 0x00};
    if (!bus.write(address_, mode_frame, sizeof(mode_frame))) return false;
    // Read both back.  Nothing is assumed to have landed.
    uint8_t cfg2[2] = {0xFF, 0xFF};
    uint8_t mode_raw[2] = {0xFF, 0xFF};
    if (!bus.readRegister(address_, kRegConfig, cfg2, sizeof(cfg2)) ||
        !bus.readRegister(address_, kRegMode, mode_raw, sizeof(mode_raw))) {
      return false;
    }
    const uint16_t after = (uint16_t(cfg2[0]) << 8) | uint16_t(cfg2[1]);
    const uint16_t mode = (uint16_t(mode_raw[0]) << 8) | uint16_t(mode_raw[1]);
    // The SLEEP bit must be clear AND every other CONFIG field must be the
    // one that was there before: a guard that silently rewrote RCOMP would
    // change the gauge's model, which is not this guard's business.
    return (after & kConfigSleepMask) == 0
        && (after & ~kConfigSleepMask) == (before & ~kConfigSleepMask)
        && (mode & kModeEnSleepMask) == 0;
  }

  bool configureActiveMode(I2cBus &bus) {
    active_ready_ = false;
    // D-790 / D789-A10: forced sleep is cleared and proved cleared FIRST.  A
    // part that is asleep cannot be qualified by writing HIBRT.
    if (!clearForcedSleep(bus)) return false;
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
                    (mode & kModeHibStatMask) == 0 &&
                    (mode & kModeEnSleepMask) == 0;
    return active_ready_;
  }

  void invalidate() { active_ready_ = false; }
  bool activeReady() const { return active_ready_; }

  bool verifyActiveMode(I2cBus &bus) {
    if (!active_ready_) return false;
    uint8_t verify[2] = {0xFF, 0xFF};
    uint8_t mode_raw[2] = {0xFF, 0xFF};
    uint8_t cfg[2] = {0xFF, 0xFF};
    if (!bus.readRegister(address_, kRegHibrt, verify, sizeof(verify)) ||
        verify[0] != 0x00 || verify[1] != 0x00 ||
        !bus.readRegister(address_, kRegMode, mode_raw, sizeof(mode_raw)) ||
        // D-790 / D789-A10: sleep can be asserted at RUNTIME, long after a
        // clean qualification, and it is checked on every value the policy
        // is about to act on.  An unreadable CONFIG is fail-closed.
        !bus.readRegister(address_, kRegConfig, cfg, sizeof(cfg))) {
      active_ready_ = false;
      return false;
    }
    const uint16_t mode =
        (uint16_t(mode_raw[0]) << 8) | uint16_t(mode_raw[1]);
    const uint16_t config = (uint16_t(cfg[0]) << 8) | uint16_t(cfg[1]);
    if ((mode & kModeHibStatMask) != 0 || (mode & kModeEnSleepMask) != 0 ||
        (config & kConfigSleepMask) != 0) {
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
  // D-790 / D789-A10.  ADI 19-6171 Rev.7 Figure 8 (MODE register format) puts
  // QuickStart at bit 14, EnSleep at bit 13 and HibStat at bit 12; the CONFIG
  // register (0x0C) is RCOMP[15:8], SLEEP bit 7, ALSC bit 6, ALRT bit 5 and
  // ATHD[4:0].
  static constexpr uint8_t kRegConfig = 0x0C;
  static constexpr uint16_t kModeHibStatMask = 0x1000;
  static constexpr uint16_t kModeEnSleepMask = 0x2000;
  static constexpr uint16_t kModeQuickStartMask = 0x4000;
  static constexpr uint16_t kConfigSleepMask = 0x0080;
  static constexpr float kVcellLsbV = 0.000078125f;

 private:
  uint8_t address_;
  bool active_ready_;
};

}  // namespace aqroot
