// D-775 host test for the accessory VCELL policy.  The two floors are DERIVED
// by demo_feature_contract.py F6 from the MAX17048 measurement node, the live
// BAT_PROTECTED_P copper, the BQ25185 BATFET maximum and D-098's published
// 400 mA / 300 mA budgets; this test pins the BEHAVIOUR those numbers drive.
#include <cstdio>
#include "aqroot_accessory_power_policy.h"
#include "max17048_guard.h"

using aqroot::AccessoryBatteryAction;
using aqroot::AccessoryLoadState;
using aqroot::accessoryCombinationPermitted;
using aqroot::accessoryEnableAllowed;
using aqroot::accessoryEnableFloor;
using aqroot::accessoryLoadBits;
using aqroot::accessoryModeEntryAllowed;
using aqroot::accessoryModeEntryFloor;
using aqroot::accessoryModeEntryPermitted;
using aqroot::kAccessoryNotPermittedV;
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
  claim("the published single-rail envelope is the derived 3.85 V",
        kAccessorySingleRailFloorV == 3.85f);
  claim("the published dual-rail envelope is the derived 3.85 V",
        kAccessoryDualRailFloorV == 3.85f);
  claim("the dual envelope is never below the single one",
        kAccessoryDualRailFloorV >= kAccessorySingleRailFloorV);
  claim("every enable envelope is strictly ABOVE the retention floor, because "
        "an enable has to anticipate a load step a retention does not",
        kAccessorySingleRailFloorV > kAccessoryRetentionFloorV
        && kAccessoryDualRailFloorV > kAccessoryRetentionFloorV);

  // =======================================================================
  // D-792 / R11-04.  THE PERMISSION TABLE, AND THE COUNTEREXAMPLE IT KILLS.
  //
  // Round-11 drove the production image from a reported 3.55 V -- D-791's own
  // `kAccessorySingleRailFloorV` -- enabled the 5 V rail and watched the
  // retention rule shed it.  The floors below are derived from the LIGHTEST
  // pre-state, which is the adverse one, and they are indexed by the
  // observable mode set.  The first claim IS Astra's case.
  // =======================================================================
  const AccessoryLoadState kQuiet;                       // no optional mode
  AccessoryLoadState amp;      amp.amplifier_on = true;
  AccessoryLoadState subghz;   subghz.subghz_tx = true;
  AccessoryLoadState wifi;     wifi.wifi_tx = true;
  AccessoryLoadState amp_subghz;  amp_subghz.amplifier_on = true;
                                  amp_subghz.subghz_tx = true;
  AccessoryLoadState wifi_amp;    wifi_amp.wifi_tx = true;
                                  wifi_amp.amplifier_on = true;
  AccessoryLoadState wifi_subghz; wifi_subghz.wifi_tx = true;
                                  wifi_subghz.subghz_tx = true;
  AccessoryLoadState all_three;   all_three.wifi_tx = true;
                                  all_three.amplifier_on = true;
                                  all_three.subghz_tx = true;

  claim("R11-04 REGRESSION: D-791's own 3.55 V no longer enables a rail",
        !accessoryEnableAllowed(true, 3.55f, false, kQuiet));
  claim("...and D-792's own 3.65 V does not either",
        !accessoryEnableAllowed(true, 3.65f, false, kQuiet));
  claim("...and the reason is the floor, which is now 3.80 V",
        accessoryEnableFloor(kQuiet, 1) == 3.80f);

  claim("the bit order is Wi-Fi, amplifier, sub-GHz",
        accessoryLoadBits(kQuiet) == 0u && accessoryLoadBits(wifi) == 1u
        && accessoryLoadBits(amp) == 2u && accessoryLoadBits(subghz) == 4u
        && accessoryLoadBits(all_three) == 7u);

  // ---- THE RAIL EDGE: the mode set does not change across the transition.
  //
  // D-793 / R12-01 + R12-05 + R12-08 NARROWED THIS TABLE, AND THE NARROWING IS
  // THE FINDING.  The completed source path (the Molex specification's own
  // 40 mOhm aged contact and 5 mOhm crimp, the measured J4 -> R75 board copper
  // and the ground return), the corrected ESP32-S3 transmitting total, and a
  // permission edge judged with a burst PRESENT together take the permitted
  // set from ten rows to four.  Nothing about the board changed.
  claim("rail edge, quiet: one rail at 3.80 V",
        accessoryEnableFloor(kQuiet, 1) == 3.80f);
  claim("rail edge, quiet: two rails at 3.80 V",
        accessoryEnableFloor(kQuiet, 2) == 3.80f);
  claim("rail edge, amplifier on: 3.85 V",
        accessoryEnableFloor(amp, 1) == 3.85f);
  claim("rail edge, sub-GHz keyed: NOT PERMITTED",
        accessoryEnableFloor(subghz, 1) >= kAccessoryNotPermittedV);
  claim("rail edge, amplifier + sub-GHz: NOT PERMITTED",
        accessoryEnableFloor(amp_subghz, 1) >= kAccessoryNotPermittedV);
  claim("rail edge, Wi-Fi TX: NOT PERMITTED",
        accessoryEnableFloor(wifi, 1) >= kAccessoryNotPermittedV);
  // ---- THE MODE EDGE: entered from a LIGHTER pre-state, so it reads higher
  // and the floor is higher.  This is the half D-791 had no word for.
  claim("mode edge, quiet: 3.80 V",
        accessoryModeEntryFloor(kQuiet, 1) == 3.80f);
  claim("mode edge, entering the amplifier: NOT PERMITTED",
        accessoryModeEntryFloor(amp, 1) >= kAccessoryNotPermittedV);
  claim("mode edge, keying sub-GHz: NOT PERMITTED",
        accessoryModeEntryFloor(subghz, 1) >= kAccessoryNotPermittedV);
  claim("mode edge, bringing Wi-Fi up: NOT PERMITTED",
        accessoryModeEntryFloor(wifi, 1) >= kAccessoryNotPermittedV);
  claim("THE TWO EDGES DIFFER, and the mode edge is never the lower of them "
        "-- a single collapsed table would either be unsound or unreachable",
        accessoryModeEntryFloor(amp, 1) > accessoryEnableFloor(amp, 1)
        && accessoryModeEntryFloor(subghz, 1) >= accessoryEnableFloor(subghz, 1)
        && accessoryModeEntryFloor(wifi, 1) >= accessoryEnableFloor(wifi, 1));
  claim("a heavier mode set never has a LOWER rail-edge floor",
        accessoryEnableFloor(kQuiet, 1) <= accessoryEnableFloor(amp, 1)
        && accessoryEnableFloor(amp, 1) <= accessoryEnableFloor(amp_subghz, 1));
  claim("no permitted floor exceeds the published single-rail envelope",
        accessoryEnableFloor(amp, 1) <= kAccessorySingleRailFloorV
        && accessoryModeEntryFloor(kQuiet, 1) <= kAccessorySingleRailFloorV);

  // THE SIX REFUSALS.  These are NOT high floors: no attainable VCELL makes
  // the settled state survive its own retention criterion, so they are
  // refused explicitly at EVERY cell voltage including a full pack.
  claim("sub-GHz TX alone is NOT PERMITTED with any accessory rail -- new at "
        "D-793, and it is the cost of the corrected source path",
        !accessoryCombinationPermitted(subghz, 1)
        && !accessoryCombinationPermitted(subghz, 2));
  claim("Wi-Fi TX alone is NOT PERMITTED with any accessory rail",
        !accessoryCombinationPermitted(wifi, 1)
        && !accessoryCombinationPermitted(wifi, 2));
  claim("Wi-Fi + amplifier is NOT PERMITTED with any accessory rail",
        !accessoryCombinationPermitted(wifi_amp, 1)
        && !accessoryCombinationPermitted(wifi_amp, 2));
  claim("Wi-Fi + sub-GHz is NOT PERMITTED with any accessory rail",
        !accessoryCombinationPermitted(wifi_subghz, 1)
        && !accessoryCombinationPermitted(wifi_subghz, 2));
  claim("all three modes is NOT PERMITTED with any accessory rail",
        !accessoryCombinationPermitted(all_three, 1)
        && !accessoryCombinationPermitted(all_three, 2));
  claim("a refusal is refused ON A FULL PACK, not merely at a low one",
        !accessoryEnableAllowed(true, 4.20f, false, wifi_subghz)
        && !accessoryEnableAllowed(true, 4.20f, true, all_three));
  claim("a refused combination reports the sentinel rather than a number a "
        "caller could compare its way past, on BOTH edges",
        accessoryEnableFloor(wifi_subghz, 1) >= kAccessoryNotPermittedV
        && accessoryModeEntryFloor(wifi_subghz, 1) >= kAccessoryNotPermittedV);
  claim("...and both edges agree about which combinations are refused",
        !accessoryModeEntryPermitted(wifi_amp, 1)
        && !accessoryModeEntryPermitted(wifi_subghz, 2)
        && !accessoryModeEntryPermitted(all_three, 1));
  claim("the sentinel is above the all-ones code, so a stuck bus cannot "
        "clear it either",
        kAccessoryNotPermittedV > kVcellAllOnesV);
  claim("an out-of-range rail count is refused",
        !accessoryCombinationPermitted(kQuiet, 0)
        && !accessoryCombinationPermitted(kQuiet, 3));

  // ---- enable permission -------------------------------------------------
  claim("unreadable VCELL refuses a first enable",
        !accessoryEnableAllowed(false, 4.2f, false, kQuiet));
  claim("unreadable VCELL refuses a second enable",
        !accessoryEnableAllowed(false, 4.2f, true, kQuiet));
  claim("first rail accepted exactly at 3.80 V",
        accessoryEnableAllowed(true, 3.80f, false, kQuiet));
  claim("first rail refused just below 3.80 V",
        !accessoryEnableAllowed(true, 3.79f, false, kQuiet));
  claim("second rail refused just below 3.80 V",
        !accessoryEnableAllowed(true, 3.79f, true, kQuiet));
  claim("second rail accepted exactly at 3.80 V",
        accessoryEnableAllowed(true, 3.80f, true, kQuiet));
  claim("with the amplifier on, 3.84 V is no longer enough",
        !accessoryEnableAllowed(true, 3.84f, false, amp));
  claim("...and 3.85 V is",
        accessoryEnableAllowed(true, 3.85f, false, amp));
  claim("NO rail may be ENABLED at the retention floor itself -- the step the "
        "enable has to anticipate has not happened yet",
        !accessoryEnableAllowed(true, kAccessoryRetentionFloorV, false, kQuiet)
        && !accessoryEnableAllowed(true, kAccessoryRetentionFloorV, true,
                                   kQuiet));

  // ---- THE MODE EDGE.  The same transition, walked in the other order. ----
  claim("with NO rail on, every mode combination is allowed -- the guard is "
        "about the accessory tree and nothing else",
        accessoryModeEntryAllowed(true, 3.30f, 0, all_three)
        && accessoryModeEntryAllowed(false, 0.0f, 0, wifi_subghz));
  claim("entering the amplifier with one rail live is REFUSED at D-793, while "
        "enabling a rail with the amplifier already on is permitted -- the two "
        "edges have not been collapsed",
        !accessoryModeEntryAllowed(true, 4.20f, 1, amp)
        && accessoryEnableAllowed(true, 3.85f, false, amp));
  claim("keying sub-GHz with one rail live is refused on a full pack",
        !accessoryModeEntryAllowed(true, 4.20f, 1, subghz));
  claim("a mode entry that reaches a REFUSED combination is refused on a full "
        "pack",
        !accessoryModeEntryAllowed(true, 4.20f, 1, wifi_subghz));
  // D-793: asked at the ONE mode-edge row that is still permitted, so the
  // claim is about the GAUGE and not about the row's own refusal.  Asking it
  // at a refused row would pass whatever the gauge did, which is vacuity.
  claim("an unreadable gauge refuses a mode entry while a rail is live",
        !accessoryModeEntryAllowed(false, 4.20f, 1, kQuiet)
        && accessoryModeEntryAllowed(true, 4.20f, 1, kQuiet));
  claim("the all-ones code refuses a mode entry",
        !accessoryModeEntryAllowed(true, kVcellAllOnesV, 1, kQuiet));
  claim("...and an implausible low reading does too",
        !accessoryModeEntryAllowed(true, 0.0f, 1, kQuiet));

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
  // D-793: the worst SECOND-rail node step F12 derives is 0.5553 V, so a pair
  // authorised at the dual envelope settles no lower than that below it.  The
  // number here is the derived step, not a round one.
  claim("a pair authorised at the dual enable envelope survives the load step "
        "it causes",
        accessoryRetentionAction(true, kAccessoryDualRailFloorV - 0.5553f,
                                 true, true)
            == AccessoryBatteryAction::Keep);
  claim("...and the envelope really is above the retention floor by more than "
        "that step, which is what makes the previous claim non-vacuous",
        kAccessoryDualRailFloorV - 0.5553f > kAccessoryRetentionFloorV);
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
        !accessoryEnableAllowed(true, kVcellAllOnesV, false, kQuiet));
  claim("the all-ones code cannot enable a second rail",
        !accessoryEnableAllowed(true, kVcellAllOnesV, true, kQuiet));
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
