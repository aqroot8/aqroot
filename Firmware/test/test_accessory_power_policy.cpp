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
using aqroot::dualRailInternalReserve;
using aqroot::internalReserveEngaged;
using aqroot::kAccessoryDualRailFloorV;
using aqroot::kAccessorySingleRailFloorV;
using aqroot::kDualRailInternalCeilingA;
using aqroot::kVcellAllOnesV;
using aqroot::kVcellPlausibleMaxV;
using aqroot::kVcellPlausibleMinV;
using aqroot::vcellIsPlausible;

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

  // ---- D-777: the internal +3V3 reserve that keeps J4 inside its own
  // published 2 A rating.  F6 derives the ceiling from the archived JST PH
  // datasheet and REFUSES a firmware constant above it; this pins the
  // behaviour that constant drives.
  claim("the dual-rail internal ceiling is D-777's derived 0.7732 A",
        kDualRailInternalCeilingA == 0.7732f);
  claim("the ceiling is below the 1.0632 A full internal budget",
        kDualRailInternalCeilingA < 1.0632f);
  claim("the reserve is not engaged with no rail on",
        !internalReserveEngaged(false, false));
  claim("the reserve is not engaged on the 3.3 V rail alone",
        !internalReserveEngaged(true, false));
  claim("the reserve is not engaged on the 5 V rail alone",
        !internalReserveEngaged(false, true));
  claim("the reserve IS engaged with both accessory rails on",
        internalReserveEngaged(true, true));

  {
    const aqroot::InternalReserve off = dualRailInternalReserve(true, false);
    claim("sub-GHz TX is available on a single rail", !off.inhibit_subghz_tx);
    claim("the NFC field is available on a single rail", !off.inhibit_nfc_field);
    claim("the IR transmitter is available on a single rail", !off.inhibit_ir_tx);
    const aqroot::InternalReserve on = dualRailInternalReserve(true, true);
    claim("sub-GHz TX is held off while both rails are on",
          on.inhibit_subghz_tx);
    claim("the NFC field is held off while both rails are on",
          on.inhibit_nfc_field);
    claim("the IR transmitter is held off while both rails are on",
          on.inhibit_ir_tx);
    // ALL THREE, not two: the reserve only reaches the ceiling as a set.
    claim("the whole reserve is engaged together",
          on.inhibit_subghz_tx && on.inhibit_nfc_field && on.inhibit_ir_tx);
  }
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
        accessoryRetentionAction(true, 3.80f, true, true)
            == AccessoryBatteryAction::Keep);
  return failures ? 1 : 0;
}
