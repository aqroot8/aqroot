// D-775 host test for the accessory VCELL policy.  The two floors are DERIVED
// by demo_feature_contract.py F6 from the MAX17048 measurement node, the live
// BAT_PROTECTED_P copper, the BQ25185 BATFET maximum and D-098's published
// 400 mA / 300 mA budgets; this test pins the BEHAVIOUR those numbers drive.
#include <cstdio>
#include "aqroot_accessory_power_policy.h"
#include "max17048_guard.h"

using aqroot::AccessoryBatteryAction;
using aqroot::accessoryEnableAllowed;
using aqroot::accessoryEnableFloor;
using aqroot::accessoryRetentionAction;
using aqroot::kAccessoryDualRailFloorV;
using aqroot::kAccessoryRetentionFloorV;
using aqroot::kAccessorySingleRailFloorV;
using aqroot::kVcellAllOnesV;
using aqroot::kVcellPlausibleMaxV;
using aqroot::kVcellPlausibleMinV;
using aqroot::vcellIsPlausible;

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

class GaugeBus : public aqroot::I2cBus {
 public:
  bool write_ok = true;
  bool hibrt_read_ok = true;
  bool mode_read_ok = true;
  bool vcell_read_ok = true;
  bool ignore_hibrt_write = false;
  uint16_t hibrt = 0x8030;
  uint16_t mode = 0x0000;
  // D-790 / D789-A10.
  uint16_t config = 0x971C;
  bool config_read_ok = true;
  uint16_t vcell = 0xC000;

  bool write(uint8_t, const uint8_t *data, size_t length) override {
    if (!write_ok) return false;
    if (length == 3 && data[0] == aqroot::Max17048Guard::kRegHibrt &&
        !ignore_hibrt_write)
      hibrt = uint16_t(data[1]) << 8 | data[2];
    if (length == 3 && data[0] == aqroot::Max17048Guard::kRegConfig)
      config = uint16_t(data[1]) << 8 | data[2];
    if (length == 3 && data[0] == aqroot::Max17048Guard::kRegMode) {
      const uint16_t v = uint16_t(data[1]) << 8 | data[2];
      mode = uint16_t((v & ~aqroot::Max17048Guard::kModeHibStatMask)
                      | (mode & aqroot::Max17048Guard::kModeHibStatMask));
    }
    return true;
  }

  bool readRegister(uint8_t, uint8_t reg, uint8_t *data, size_t length) override {
    if (length != 2) return false;
    if (reg == aqroot::Max17048Guard::kRegHibrt) {
      if (!hibrt_read_ok) return false;
      data[0] = uint8_t(hibrt >> 8); data[1] = uint8_t(hibrt); return true;
    }
    if (reg == aqroot::Max17048Guard::kRegMode) {
      if (!mode_read_ok) return false;
      data[0] = uint8_t(mode >> 8); data[1] = uint8_t(mode); return true;
    }
    if (reg == aqroot::Max17048Guard::kRegConfig) {
      if (!config_read_ok) return false;
      data[0] = uint8_t(config >> 8); data[1] = uint8_t(config); return true;
    }
    if (reg == aqroot::Max17048Guard::kRegVcell) {
      if (!vcell_read_ok) return false;
      data[0] = uint8_t(vcell >> 8); data[1] = uint8_t(vcell); return true;
    }
    return false;
  }

  bool probe(uint8_t) override { return true; }
};

int main() {
  // D-791 / D790-A03 + D790-A14.  THE THREE DERIVED FLOORS.
  //
  // D-790 had two constants that were BOTH enable floors AND retention floors
  // and were derived from a model that started at BAT_PROTECTED_P without ever
  // asking whether the node could be there.  F12 now derives three, and the
  // boundary claims below are the values it publishes.
  claim("the retention floor is the derived 3.20 V",
        kAccessoryRetentionFloorV == 3.20f);
  claim("the first-rail ENABLE floor is the derived 3.55 V",
        kAccessorySingleRailFloorV == 3.55f);
  claim("the second-rail ENABLE floor is the derived 3.65 V",
        kAccessoryDualRailFloorV == 3.65f);
  claim("the dual enable floor is strictly above the single one",
        kAccessoryDualRailFloorV > kAccessorySingleRailFloorV);
  claim("every enable floor is strictly ABOVE the retention floor, because an "
        "enable has to anticipate a load step a retention does not",
        kAccessorySingleRailFloorV > kAccessoryRetentionFloorV
        && kAccessoryDualRailFloorV > kAccessoryRetentionFloorV);
  claim("first rail uses the single floor", accessoryEnableFloor(false) == 3.55f);
  claim("second rail uses the dual floor", accessoryEnableFloor(true) == 3.65f);

  // ---- enable permission -------------------------------------------------
  claim("unreadable VCELL refuses a first enable",
        !accessoryEnableAllowed(false, 4.2f, false));
  claim("unreadable VCELL refuses a second enable",
        !accessoryEnableAllowed(false, 4.2f, true));
  claim("first rail accepted exactly at 3.55 V",
        accessoryEnableAllowed(true, 3.55f, false));
  claim("first rail refused just below 3.55 V",
        !accessoryEnableAllowed(true, 3.54f, false));
  claim("second rail refused at 3.60 V, below the derived dual enable floor",
        !accessoryEnableAllowed(true, 3.60f, true));
  claim("second rail refused just below 3.65 V",
        !accessoryEnableAllowed(true, 3.64f, true));
  claim("second rail accepted exactly at 3.65 V",
        accessoryEnableAllowed(true, 3.65f, true));
  claim("a single rail is still allowed at 3.60 V, between the enable floors",
        accessoryEnableAllowed(true, 3.60f, false));
  claim("NO rail may be ENABLED at the retention floor itself -- the step the "
        "enable has to anticipate has not happened yet",
        !accessoryEnableAllowed(true, kAccessoryRetentionFloorV, false)
        && !accessoryEnableAllowed(true, kAccessoryRetentionFloorV, true));

  // ---- retention ---------------------------------------------------------
  claim("no rail on and no reading is not an action",
        accessoryRetentionAction(false, 0.0f, false, false)
            == AccessoryBatteryAction::Keep);
  claim("unreadable VCELL sheds a single active rail",
        accessoryRetentionAction(false, 4.2f, true, false)
            == AccessoryBatteryAction::ShedAll);
  claim("unreadable VCELL sheds both active rails",
        accessoryRetentionAction(false, 4.2f, true, true)
            == AccessoryBatteryAction::ShedAll);
  // THE REGRESSION D-791 EXISTS TO STOP.  With D-790's constants a rail
  // authorised at the dual ENABLE floor was shed by the very next settled
  // recheck, because the load step it had just caused took the node below the
  // number that authorised it.  Retention is judged at the RETENTION floor.
  claim("a pair authorised at the dual enable floor survives the load step it "
        "causes",
        accessoryRetentionAction(true, kAccessoryDualRailFloorV - 0.40f,
                                 true, true)
            == AccessoryBatteryAction::Keep);
  claim("dual rails just above the retention floor are retained",
        accessoryRetentionAction(true, 3.21f, true, true)
            == AccessoryBatteryAction::Keep);
  claim("dual rails just below the retention floor shed the 5 V rail first",
        accessoryRetentionAction(true, 3.19f, true, true)
            == AccessoryBatteryAction::Shed5v);
  claim("dual rails far below the retention floor STILL shed the 5 V rail "
        "first, because shedding it is what restores the node",
        accessoryRetentionAction(true, 2.90f, true, true)
            == AccessoryBatteryAction::Shed5v);
  claim("the 3.3 V rail alone below the retention floor sheds everything",
        accessoryRetentionAction(true, 3.19f, true, false)
            == AccessoryBatteryAction::ShedAll);
  claim("the 5 V rail alone below the retention floor sheds everything",
        accessoryRetentionAction(true, 3.19f, false, true)
            == AccessoryBatteryAction::ShedAll);
  claim("the 3.3 V rail alone is retained at 3.60 V",
        accessoryRetentionAction(true, 3.60f, true, false)
            == AccessoryBatteryAction::Keep);
  claim("the 5 V rail alone is retained at 3.60 V",
        accessoryRetentionAction(true, 3.60f, false, true)
            == AccessoryBatteryAction::Keep);
  claim("dual rails at 3.85 V are retained",
        accessoryRetentionAction(true, 3.85f, true, true)
            == AccessoryBatteryAction::Keep);

  // ---- D-779: an I2C read that succeeded is not a measurement ------------
  claim("the all-ones VCELL code is OUTSIDE the plausible band",
        !vcellIsPlausible(kVcellAllOnesV));
  claim("the plausible maximum is above the BQ25185 regulation point",
        kVcellPlausibleMaxV > 4.25f);
  claim("the plausible maximum is below the all-ones code",
        kVcellPlausibleMaxV < kVcellAllOnesV);
  claim("the plausible minimum is below the pack's 2.75 V cut-off",
        kVcellPlausibleMinV < 2.75f);
  claim("a zero reading is not plausible", !vcellIsPlausible(0.0f));
  claim("a normal cell IS plausible", vcellIsPlausible(3.85f));
  claim("the all-ones code cannot enable a first rail",
        !accessoryEnableAllowed(true, kVcellAllOnesV, false));
  claim("the all-ones code cannot enable a second rail",
        !accessoryEnableAllowed(true, kVcellAllOnesV, true));
  claim("the all-ones code SHEDS a rail that is already on",
        accessoryRetentionAction(true, kVcellAllOnesV, true, false)
            == AccessoryBatteryAction::ShedAll);
  claim("the all-ones code sheds BOTH rails",
        accessoryRetentionAction(true, kVcellAllOnesV, true, true)
            == AccessoryBatteryAction::ShedAll);
  claim("a zero reading sheds rather than being read as a flat pack",
        accessoryRetentionAction(true, 0.0f, true, true)
            == AccessoryBatteryAction::ShedAll);
  claim("a plausible reading above the retention floor is still retained",
        accessoryRetentionAction(true, 3.85f, true, true)
            == AccessoryBatteryAction::Keep);

  // ---- Round 4: active-mode configuration is part of measurement validity -
  {
    GaugeBus bus;
    aqroot::Max17048Guard gauge(0x36);
    float v = 0.0f;
    claim("VCELL is refused before active-mode configuration is verified",
          !gauge.readVcell(bus, &v));

    bus.write_ok = false;
    claim("failed HIBRT write makes gauge configuration fail",
          !gauge.configureActiveMode(bus));
    claim("plausible stale VCELL remains unusable after failed HIBRT write",
          !gauge.readVcell(bus, &v));

    bus.write_ok = true;
    bus.hibrt_read_ok = false;
    claim("HIBRT write without a successful readback is not configuration proof",
          !gauge.configureActiveMode(bus) && !gauge.activeReady());

    bus.hibrt_read_ok = true;
    bus.ignore_hibrt_write = true;
    bus.hibrt = 0x8030;
    claim("a successful HIBRT transaction with nonzero readback is rejected",
          !gauge.configureActiveMode(bus) && !gauge.activeReady());

    bus.ignore_hibrt_write = false;
    bus.hibrt = 0x8030;
    bus.vcell = 0xC300;
    claim("HIBRT=0 write plus exact readback establishes active mode",
          gauge.configureActiveMode(bus) && gauge.activeReady());
    claim("verified active-mode gauge permits a VCELL read",
          gauge.readVcell(bus, &v) && vcellIsPlausible(v));

    bus.hibrt = 0x8030;  // emulate gauge reset / configuration loss
    claim("later HIBRT configuration loss invalidates VCELL permission",
          !gauge.readVcell(bus, &v) && !gauge.activeReady());

    bus.hibrt = 0;
    claim("active mode can be re-established only by the explicit configure path",
          gauge.configureActiveMode(bus));
    bus.hibrt_read_ok = false;
    claim("failed HIBRT supervision read fails closed before VCELL",
          !gauge.readVcell(bus, &v) && !gauge.activeReady());
  }

  return failures ? 1 : 0;
}
