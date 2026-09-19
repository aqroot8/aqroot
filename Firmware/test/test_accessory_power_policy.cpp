// D-775 host test for the accessory VCELL policy.  The two floors are DERIVED
// by demo_feature_contract.py F6 from the MAX17048 measurement node, the live
// BAT_PROTECTED_P copper, the BQ25185 BATFET maximum and D-098's published
// 400 mA / 300 mA budgets; this test pins the BEHAVIOUR those numbers drive.
#include <cstdio>
#include "aqroot_accessory_power_policy.h"

using aqroot::AccessoryBatteryAction;
using aqroot::accessoryEnableAllowed;
using aqroot::accessoryEnableFloor;
using aqroot::accessoryRetentionAction;
using aqroot::kAccessoryDualRailFloorV;
using aqroot::kAccessorySingleRailFloorV;

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

int main() {
  claim("single floor is D-766's retained 3.50 V",
        kAccessorySingleRailFloorV == 3.50f);
  claim("dual floor is D-775's derived 3.80 V",
        kAccessoryDualRailFloorV == 3.80f);
  claim("the dual floor is strictly above the single floor",
        kAccessoryDualRailFloorV > kAccessorySingleRailFloorV);
  claim("first rail uses the single floor", accessoryEnableFloor(false) == 3.50f);
  claim("second rail uses the dual floor", accessoryEnableFloor(true) == 3.80f);

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
  claim("second rail refused just below 3.80 V",
        !accessoryEnableAllowed(true, 3.79f, true));
  claim("second rail accepted exactly at 3.80 V",
        accessoryEnableAllowed(true, 3.80f, true));
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
  claim("dual rails at 3.80 V are retained",
        accessoryRetentionAction(true, 3.80f, true, true)
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
  return failures ? 1 : 0;
}
