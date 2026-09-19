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

// ===========================================================================
// D-777.  THE BATTERY CONNECTION HAS A PUBLISHED RATING AND IT IS THE LOWEST
// NUMBER IN THE BATTERY PATH.
//
// `J4` is a JST `B2B-PH-K-S(LF)(SN)`.  JST publishes the PH series at
// **2 A AC/DC (AWG #24)** -- archived at
// `hardware/demo/kicad/aqroot-demo/vendor/JST/jst-ph-connector-ePH.txt` -- and
// the selected pack's own leads are **UL 26AWG**, which is SMALLER than the
// gauge that rating is specified at.  Nothing else in this battery path is
// anywhere near 2 A: the BQ25185's recoverable `IBAT_OCP` band is
// 2.5625-3.6875 A, D-771's LTC4368 latching breaker is 3.960-6.061 A and `F1`
// is a 5 A one-shot.  **The connector is the least protected element in the
// chain**, and the band between its rating and the first protection that acts
// is exactly where D-775's published dual-rail envelope sat: 2.2715 A.
//
// WHY THE FLOOR IS NOT THE LEVER.  Holding the FULL internal +3V3 budget
// (1.0632 A, D-772) plus 400 mA plus 300 mA under 2 A needs `VCELL >= 4.16 V`
// -- a nearly full pack -- which would delete the simultaneous capability in
// all but name.  The lever that works is the other term.  F6 solves for the
// internal +3V3 current that keeps the connection inside its own published
// rating at the enforced dual-rail floor, and firmware RESERVES it.
//
// THE RESERVE IS THREE NAMED BUDGET LINES, held off while BOTH accessory rails
// are enabled.  Each is a line of F6's `P3V3_INTERNAL_BUDGET` and F6 refuses a
// token here that does not name one:
//
//     inhibit_subghz_tx    140.0 mA   U7 / U8   sub-GHz TX
//     inhibit_nfc_field    100.0 mA   U9        NFC front end, field on
//     inhibit_ir_tx         50.0 mA   D1/Q1/R24 IR transmitter
//
// This is a CONCURRENCY condition of exactly the shape D-775 added, not a
// smaller published number: D-098's 400 mA and 300 mA are both still
// guaranteed, each rail alone still runs down to 3.50 V, and the reserve
// applies only while an accessory holds BOTH switched rails.  It is enforced
// rather than assumed because D-772's budget counts these lines precisely on
// the ground that nothing in hardware prevents them -- the fix for an
// unenforced rule is to enforce it, not to stop counting it.
//
// THE ACCESSORY HOLDS AND THE RADIO WAITS, not the other way round.  Dropping
// an accessory's rail mid-operation to service an internal transmit burst is
// worse for the accessory than a deterministic refusal, which is the same
// judgement D-775 made about shedding.
//
// WHAT IS NOT COVERED, STATED.  This board has no accessory current
// measurement (D-753).  An accessory that draws MORE than its published budget
// can still put the connection above 2 A with nothing acting until
// `IBAT_OCP`'s minimum; beyond that the charger hiccups, so the connector
// sees a low-duty burst rather than a sustained overload -- and after 4 to 7
// consecutive trips in a 2 s window the BATFET stays OFF until USB is
// connected (SLUSF65B 6.3.7.3, D-779), which ends the stress entirely at the
// cost of a battery-only dead stop the user has to clear.  The
// residual is named in CTO_DECISIONS D-777 and carries a first-article
// temperature-rise measurement on J4.
// ===========================================================================
constexpr float kDualRailInternalCeilingA = 0.7732f;

struct InternalReserve {
  bool inhibit_subghz_tx;
  bool inhibit_nfc_field;
  bool inhibit_ir_tx;
};

// The reserve is a pure function of which rails are ENABLED -- the only
// accessory state this board can actually observe.
inline InternalReserve dualRailInternalReserve(bool rail3v3_on,
                                               bool rail5v_on) {
  const bool both = rail3v3_on && rail5v_on;
  return InternalReserve{both, both, both};
}

inline bool internalReserveEngaged(bool rail3v3_on, bool rail5v_on) {
  return rail3v3_on && rail5v_on;
}

// ===========================================================================
// D-779.  AN I2C READ THAT SUCCEEDED IS NOT A MEASUREMENT.
//
// `readFuelCellVoltage` returned true for ANY sixteen bits the MAX17048 put on
// the bus, and 0xFFFF decodes to 5.1199 V -- above BOTH floors, so a stuck-high
// bus, a gauge that never came out of reset, or a bus fault that reads all-ones
// AUTHORISED the second accessory rail.  Fail-closed on a failed read was
// already right; this is the other half of it.
//
// NEITHER BOUND IS ARBITRARY.  The upper is above the charger's own regulation
// maximum -- BQ25185 VBATREG 4.2 V with its published tolerance -- with room
// for gauge error, and BELOW the 5.1199 V that the all-ones code decodes to.
// The lower is beneath the pack's own 2.75 V discharge cut-off, below which its
// PCM has already disconnected, so a reading under it is not a live cell.  F6
// parses both and refuses a band that fails to exclude the all-ones code.
// ===========================================================================
constexpr float kVcellPlausibleMinV = 2.50f;
constexpr float kVcellPlausibleMaxV = 4.50f;
// The value the all-ones VCELL code decodes to: 65535 x 78.125 uV.
constexpr float kVcellAllOnesV = 5.1199f;

inline bool vcellIsPlausible(float vcell) {
  return vcell >= kVcellPlausibleMinV && vcell <= kVcellPlausibleMaxV;
}

enum class AccessoryBatteryAction { Keep, Shed5v, ShedAll };

inline float accessoryEnableFloor(bool other_rail_on) {
  return other_rail_on ? kAccessoryDualRailFloorV : kAccessorySingleRailFloorV;
}

inline bool accessoryEnableAllowed(bool vcell_valid, float vcell,
                                   bool other_rail_on) {
  return vcell_valid && vcellIsPlausible(vcell)
         && vcell >= accessoryEnableFloor(other_rail_on);
}

inline AccessoryBatteryAction accessoryRetentionAction(bool vcell_valid,
                                                       float vcell,
                                                       bool rail3v3_on,
                                                       bool rail5v_on) {
  if (!rail3v3_on && !rail5v_on) return AccessoryBatteryAction::Keep;
  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::ShedAll;
  if (rail3v3_on && rail5v_on && vcell < kAccessoryDualRailFloorV) {
    return vcell >= kAccessorySingleRailFloorV
               ? AccessoryBatteryAction::Shed5v
               : AccessoryBatteryAction::ShedAll;
  }
  if (vcell < kAccessorySingleRailFloorV) return AccessoryBatteryAction::ShedAll;
  return AccessoryBatteryAction::Keep;
}

}  // namespace aqroot
