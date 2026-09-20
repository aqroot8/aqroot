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
  uint16_t vcell = 0xC000;

  bool write(uint8_t, const uint8_t *data, size_t length) override {
    if (!write_ok) return false;
    if (length == 3 && data[0] == aqroot::Max17048Guard::kRegHibrt &&
        !ignore_hibrt_write)
      hibrt = uint16_t(data[1]) << 8 | data[2];
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
    if (reg == aqroot::Max17048Guard::kRegVcell) {
      if (!vcell_read_ok) return false;
      data[0] = uint8_t(vcell >> 8); data[1] = uint8_t(vcell); return true;
    }
    return false;
  }

  bool probe(uint8_t) override { return true; }
};

int main() {
  claim("single floor is D-766's retained 3.50 V",
        kAccessorySingleRailFloorV == 3.50f);
  claim("dual floor is D-787's re-derived 3.85 V",
        kAccessoryDualRailFloorV == 3.85f);
  claim("the dual floor is strictly above the single floor",
        kAccessoryDualRailFloorV > kAccessorySingleRailFloorV);
  claim("first rail uses the single floor", accessoryEnableFloor(false) == 3.50f);
  claim("second rail uses the dual floor", accessoryEnableFloor(true) == 3.85f);

  // ---- enable permission -------------------------------------------------
  claim("unreadable VCELL refuses a first enable",
        !accessoryEnableAllowed(false, 4.2f, false));
  claim("unreadable VCELL refuses a second enable",
        !accessoryEnableAllowed(false, 4.2f, true));
  claim("first rail accepted exactly at 3.50 V",
        accessoryEnableAllowed(true, 3.50f, false));
  claim("first rail refused just below 3.50 V",
        !accessoryEnableAllowed(true, 3.49f, false));
  claim("second rail refused at 3.75 V, below the derived dual floor",
        !accessoryEnableAllowed(true, 3.75f, true));
  claim("second rail refused just below 3.85 V",
        !accessoryEnableAllowed(true, 3.84f, true));
  claim("second rail accepted exactly at 3.85 V",
        accessoryEnableAllowed(true, 3.85f, true));
  claim("a single rail is still allowed at 3.60 V, between the floors",
        accessoryEnableAllowed(true, 3.60f, false));

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
  claim("dual rails at 3.75 V shed the 5 V rail first",
        accessoryRetentionAction(true, 3.75f, true, true)
            == AccessoryBatteryAction::Shed5v);
  claim("dual rails at 3.60 V shed the 5 V rail first",
        accessoryRetentionAction(true, 3.60f, true, true)
            == AccessoryBatteryAction::Shed5v);
  claim("dual rails below the single floor shed everything",
        accessoryRetentionAction(true, 3.49f, true, true)
            == AccessoryBatteryAction::ShedAll);
  claim("dual rails at 3.85 V are retained",
        accessoryRetentionAction(true, 3.85f, true, true)
            == AccessoryBatteryAction::Keep);
  claim("the 3.3 V rail alone is retained at 3.60 V",
        accessoryRetentionAction(true, 3.60f, true, false)
            == AccessoryBatteryAction::Keep);
  claim("the 5 V rail alone is retained at 3.60 V",
        accessoryRetentionAction(true, 3.60f, false, true)
            == AccessoryBatteryAction::Keep);
  claim("a single active rail below 3.50 V sheds",
        accessoryRetentionAction(true, 3.49f, true, false)
            == AccessoryBatteryAction::ShedAll);

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
  claim("a plausible reading at the dual floor is still retained",
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
