#pragma once

namespace aqroot {

// ===========================================================================
// D-775.  THE ACCESSORY VCELL FLOORS, AND WHERE THE NUMBERS COME FROM.
//
// Hardware current limiting (U20/U22 TPS22950-Q1, sized by D-753/D-765/D-771)
// remains the ABSOLUTE safety boundary and this file never weakens it.  What
// these two constants enforce is the NORMAL D-098 load contract: the board
// publishes ACC_3V3_SW = 400 mA TOTAL and ACC_5V_SW = 300 mA TOTAL, and at the
// bottom of the pack's discharge those two budgets DELIVERED AT THE SAME TIME,
// on top of every internal subsystem running at once, pull the BQ25185 past its
// own IBAT_OCP minimum and hiccup the charger.  That is not a fault the user
// caused; it is the published budget being honoured on a low battery.
//
// NEITHER FLOOR IS A CHOSEN NUMBER.  Both are DERIVED, by
// `hardware/demo/manufacturing/checks/demo_feature_contract.py` F6, from
//
//   * the MAX17048 measurement point -- VCELL is BAT_PROTECTED_P (U14.2/U14.3,
//     the same node as BQ25185 U11.2), so the sag model starts THERE and does
//     not double-count Q2/Q3, R75 or the pack's own internal resistance, all of
//     which are UPSTREAM of what the gauge reads;
//   * the LIVE BAT_PROTECTED_P copper resistance, measured off the board on
//     every contract run (R75.2 -> U11.2), at its hot resistivity;
//   * the BQ25185 BATFET maximum -- SLUSF65B RON_BAT = 140 mOhm max over
//     -40..+125 C, with a declared allowance for the 3.5 V / 2.3 A corner TI
//     does not publish;
//   * D-098's published 400 mA / 300 mA budgets, the live SYS->U21 trunk and
//     accessory-rail copper, and each load switch's own RON maximum.
//
// The derived requirements, at F6's 10 % margin to the IBAT_OCP minimum:
//
//     single rail   3.1232 V   ->  3.15 V on a 0.05 V grid
//     both rails    3.7622 V   ->  3.80 V on a 0.05 V grid
//
// so kAccessoryDualRailFloorV IS the derived requirement and
// kAccessorySingleRailFloorV is D-766's existing 3.50 V policy floor, which
// sits well above its own requirement and is retained.  F6 FAILS if either
// constant here drops below what it derives, and the arithmetic is re-derived
// from the live board on every run -- so a wider +3V3 budget, a different boost
// setpoint, a re-routed BAT_PROTECTED_P or a new limiter setting moves the
// requirement and this file has to follow it.
//
// SHED ORDER AND WHAT THE USER STILL GETS.  Below the dual-rail floor the 5 V
// rail sheds FIRST: it is the expensive one (boost, so pack current scales with
// 5.1654 V / 0.88), and shedding it leaves the 3.3 V rail delivering its full
// published 400 mA.  Each rail on its own remains available down to 3.50 V.
// Only the SIMULTANEOUS full-budget case is restricted, and it is restricted
// rather than allowed to hiccup the charger.
//
// UNREADABLE VCELL IS ALWAYS FAIL-CLOSED: no measurement means no permission,
// and any rail already on is shed.
// ===========================================================================
constexpr float kAccessorySingleRailFloorV = 3.50f;
constexpr float kAccessoryDualRailFloorV = 3.80f;

enum class AccessoryBatteryAction { Keep, Shed5v, ShedAll };

inline float accessoryEnableFloor(bool other_rail_on) {
  return other_rail_on ? kAccessoryDualRailFloorV : kAccessorySingleRailFloorV;
}

inline bool accessoryEnableAllowed(bool vcell_valid, float vcell,
                                   bool other_rail_on) {
  return vcell_valid && vcell >= accessoryEnableFloor(other_rail_on);
}

inline AccessoryBatteryAction accessoryRetentionAction(bool vcell_valid,
                                                       float vcell,
                                                       bool rail3v3_on,
                                                       bool rail5v_on) {
  if (!rail3v3_on && !rail5v_on) return AccessoryBatteryAction::Keep;
  if (!vcell_valid) return AccessoryBatteryAction::ShedAll;
  if (rail3v3_on && rail5v_on && vcell < kAccessoryDualRailFloorV) {
    return vcell >= kAccessorySingleRailFloorV
               ? AccessoryBatteryAction::Shed5v
               : AccessoryBatteryAction::ShedAll;
  }
  if (vcell < kAccessorySingleRailFloorV) return AccessoryBatteryAction::ShedAll;
  return AccessoryBatteryAction::Keep;
}

}  // namespace aqroot
