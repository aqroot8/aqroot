#pragma once

namespace aqroot {

// ===========================================================================
// D-791 / D790-A03 + D790-A14.  THE ACCESSORY VCELL FLOORS, RE-DERIVED FROM
// THE COMPLETE CELL-TO-LOAD NETWORK AND FROM THE GAUGE'S OWN ERROR.
//
// Hardware current limiting (U20/U22 TPS22950-Q1, sized by D-753/D-765/D-771)
// remains the ABSOLUTE safety boundary and this file never weakens it.  What
// these constants enforce is the NORMAL D-098 load contract: the board
// publishes ACC_3V3_SW = 400 mA TOTAL and ACC_5V_SW = 300 mA TOTAL, and those
// budgets have to be honoured from a 1S pouch through a battery path whose
// series resistance is not small.
//
// WHAT ROUND-10 FOUND, AND IT IS THE REASON EVERY NUMBER BELOW MOVED.
// D-775 through D-790 derived these floors from a model that STARTED at
// `BAT_PROTECTED_P` -- the node the MAX17048 reads -- and said so: it
// deliberately did "not double-count Q2/Q3, R75 or the pack's own internal
// resistance, all of which are UPSTREAM of what the gauge reads".  That is the
// right thing to do for the SAG BELOW the node and the wrong thing to do for
// the question nobody asked: CAN THE NODE BE THERE AT ALL?  It cannot.
// Sustaining 3.85 V at `BAT_PROTECTED_P` while the published load draws needs
// more than 4.3 V upstream through four AO4800 channels and R75 alone, and the
// charger's own regulation maximum on the pack is 4.221 V.  The 3.85 V dual
// floor and the 3.50 V single floor were node voltages THE NODE NEVER REACHES
// UNDER LOAD, so the rails this board publishes would be authorised and then
// shed by the very next settled recheck -- on a FULL pack.
//
// NONE OF THE THREE CONSTANTS BELOW IS A CHOSEN NUMBER.  All are DERIVED by
// `hardware/demo/manufacturing/checks/demo_feature_contract.py` **F12**, which
// solves the whole network as one self-consistent fixed point --
//
//   CELL(OCV) -> pack DC resistance -> 26 AWG harness -> J4 -> F1
//             -> Q2 ch1 -> Q2 ch2 -> Q3 ch1 -> Q3 ch2 -> R75
//             -> BAT_PROTECTED_P -> BQ25185 BATFET -> SYS
//             -> U12 -> +3V3 -> internal load and U20 -> ACC_3V3_SW
//             -> SYS->L4 trunk -> U21 -> U22 -> ACC_5V_SW
//
// -- against every limit at once: a stable operating point existing at all,
// the BQ25185's own VBUVLO, U12's published VIN floor for its 2 A row, the
// IBAT_OCP margin at a DECLARED WIDER accuracy band than TI states at its
// single condition, the AO4800's lowest published conduction row, TI's
// junction maximum referenced to THIS enclosure's internal air, and the fitted
// pouch's published discharge window.
//
//   kAccessoryRetentionFloorV   the HARD node floor.  It is the BQ25185's own
//                               VBUVLO bound -- below it the BATFET
//                               disconnects and the product powers down --
//                               plus the MAX17048's POSITIVE voltage error and
//                               one quantisation step, because the firmware
//                               compares a REPORTED value and ADI publishes
//                               +/-20 mV/cell (D790-A14).  A reported 3.20 V
//                               can be an actual 3.180 V.
//
//   kAccessorySingleRailFloorV  the floor to ENABLE the first accessory rail,
//   kAccessoryDualRailFloorV    and to enable the SECOND one.  Each is the
//                               retention floor PLUS THE NODE STEP THAT RAIL
//                               WILL CAUSE, worst case over every declared
//                               state and every cell voltage.  D-779 named
//                               this exactly -- "the permission was taken
//                               before the load existed" -- and D-790 never
//                               quantified it, so its floors both failed to
//                               anticipate the step and sat above the node's
//                               attainable range at the same time.
//
// F12 FAILS if any constant here is below what it derives, if a floor is not
// ATTAINABLE by the node in the state it governs, or if D-790's own declared
// reference state ever starts passing.  The arithmetic re-runs from the live
// board on every contract run, so a wider +3V3 budget, a different boost
// setpoint, a re-routed BAT_PROTECTED_P, a new limiter setting or a different
// pass pair all move the requirement and this file has to follow it.
//
// SHED ORDER AND WHAT THE USER STILL GETS, UNCHANGED.  Below the retention
// floor with both rails live the 5 V rail sheds FIRST: it is the expensive one
// (a boost, so pack current scales with 5.1654 V / 0.88), and shedding it
// RESTORES the node by the second-rail step -- which is why the 3.3 V rail
// then keeps delivering its full published 400 mA instead of going down with
// it.  Both published budgets are UNCHANGED; what D-791 corrects is which
// internal subsystems may be at maximum AT THE SAME TIME, which F12 derives
// and DEVICE_SPEC publishes as observable modes.
//
// UNREADABLE VCELL IS ALWAYS FAIL-CLOSED: no measurement means no permission,
// and any rail already on is shed.
// ===========================================================================
constexpr float kAccessoryRetentionFloorV = 3.20f;
constexpr float kAccessorySingleRailFloorV = 3.55f;
constexpr float kAccessoryDualRailFloorV = 3.65f;

// ===========================================================================
// D-779.  AN I2C READ THAT SUCCEEDED IS NOT A MEASUREMENT.
//
// `readFuelCellVoltage` returned true for ANY sixteen bits the MAX17048 put on
// the bus, and 0xFFFF decodes to 5.1199 V -- above EVERY floor, so a stuck-high
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

// D-791 / D790-A03.  RETENTION IS JUDGED AT THE RETENTION FLOOR, NOT AT THE
// ENABLE FLOORS.
//
// The enable floors anticipate a load STEP that has not happened yet; once the
// rail is on, that step HAS happened and the node is legitimately lower.
// Judging retention at an enable floor is what would shed a rail 400 ms after
// authorising it, every time.  The graduated response lives in the ACTION --
// 5 V first, then everything -- rather than in a second threshold, so the two
// numbers cannot drift into an order that makes the graduation unreachable.
inline AccessoryBatteryAction accessoryRetentionAction(bool vcell_valid,
                                                       float vcell,
                                                       bool rail3v3_on,
                                                       bool rail5v_on) {
  if (!rail3v3_on && !rail5v_on) return AccessoryBatteryAction::Keep;
  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::ShedAll;
  if (vcell < kAccessoryRetentionFloorV) {
    return (rail3v3_on && rail5v_on) ? AccessoryBatteryAction::Shed5v
                                     : AccessoryBatteryAction::ShedAll;
  }
  return AccessoryBatteryAction::Keep;
}

}  // namespace aqroot
