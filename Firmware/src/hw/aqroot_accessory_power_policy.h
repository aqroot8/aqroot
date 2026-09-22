#pragma once

// D-794 / R13-01 introduced the gauge conversion-age rule, which is stated in
// milliseconds and therefore needs a fixed-width type.
#include <stdint.h>

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
//   kAccessorySingleRailFloorV  the MOST DEMANDING floor the D-792 permission
//   kAccessoryDualRailFloorV    table permits for one and for two accessory
//                               rails.  These are the PUBLISHED ENVELOPE of
//                               that table, quoted by DEVICE_SPEC and used to
//                               pick the FIRST_FIVE_ASSEMBLY_PLAN bench
//                               points; the firmware itself consults the
//                               TABLE, because whether a transition survives
//                               its own settled state depends on which
//                               high-load modes are on.  D-779 named the
//                               original defect exactly -- "the permission was
//                               taken before the load existed" -- D-790 never
//                               quantified it, D-791 quantified it from the
//                               WRONG PRE-STATE, and Round-11 reproduced the
//                               consequence at D-791's own 3.55 V constant.
//
// F12 FAILS if any constant or table entry here differs from what it derives,
// if a floor is not ATTAINABLE by the node in the state it governs, or if
// D-790's own declared reference state ever starts passing.  The arithmetic re-runs from the live
// board on every contract run, so a wider +3V3 budget, a different boost
// setpoint, a re-routed BAT_PROTECTED_P, a new limiter setting or a different
// pass pair all move the requirement and this file has to follow it.
//
// SHED ORDER AND WHAT THE USER STILL GETS, UNCHANGED.  Below the retention
// floor with both rails live the 5 V rail sheds FIRST: it is the expensive one
// (a boost, so pack current scales with 5.1654 V / 0.88), and shedding it
// RESTORES the node -- which is why the 3.3 V rail then keeps delivering its
// full published 400 mA instead of going down with it.  The PER-RAIL published
// budgets are UNCHANGED.  What D-791 began and D-792 finishes is stating which
// internal subsystems may be at maximum AT THE SAME TIME, and what the two
// rails may draw TOGETHER; F12 derives both and DEVICE_SPEC publishes them as
// observable modes rather than as an unobservable current ceiling.
//
// UNREADABLE VCELL IS ALWAYS FAIL-CLOSED: no measurement means no permission,
// and any rail already on is shed.
// ===========================================================================
constexpr float kAccessoryRetentionFloorV = 3.20f;
constexpr float kAccessorySingleRailFloorV = 3.85f;
constexpr float kAccessoryDualRailFloorV = 3.85f;

// ===========================================================================
// D-792 / R11-04.  TWO SCALARS CANNOT CARRY THIS ANSWER, SO THERE IS A TABLE.
//
// WHAT ROUND-11 REPRODUCED, AND WHY IT IS A ROOT CAUSE AND NOT A NUMBER.
// Astra drove the production image from a reported VCELL of 3.55 V -- exactly
// D-791's `kAccessorySingleRailFloorV` -- enabled the 5 V accessory rail, and
// watched the node sag and the retention rule shed it.  D-791 derived that
// 3.55 V with the OTHER rail already drawing its full published budget in the
// PRE state.  That is the wrong pre-state, and it is wrong in the direction
// that matters: an accessory which is PLUGGED IN AND IDLE holds the node near
// open circuit, the gauge reports that high value, the permission is granted
// on it, and the accessory then starts drawing.  The adverse pre-state is the
// LIGHTEST one -- no optional mode, no accessory current -- because the
// pre-read is what the permission is granted on.  Every floor below is derived
// from that pre-state, with the gauge error charged HIGH on the pre read and
// LOW on the post read at the same time.
//
// AND THE ANSWER DEPENDS ON WHAT ELSE IS ON.  The amplifier at its capped
// level, a keyed sub-GHz transmitter and the Wi-Fi/BLE radio are each a load
// of the same order as an accessory rail.  D-791 answered with two constants
// and a paragraph asking the reader to observe the modes.  A paragraph cannot
// refuse.  The table below is indexed by the OBSERVABLE MODE SET and the RAIL
// COUNT, every entry is DERIVED by `demo_feature_contract.py` F12 from the
// canonical power model, and F12 FAILS if any entry here differs from what it
// derives -- including the sentinel entries.
//
// `kAccessoryNotPermittedV` IS NOT A LARGE FLOOR, IT IS A REFUSAL.  Six of the
// sixteen combinations have NO attainable cell voltage at which the settled
// state survives its own retention criterion at the top of the declared
// 0..40 C ambient envelope.  Encoding those as a high number would be
// D790-A03's defect again -- a floor the node cannot reach reads as a
// restriction and behaves as a rail that never turns on, with no diagnostic.
// They are refused explicitly and the log says which mode caused it.
//
// THE PUBLISHED PER-RAIL BUDGETS ARE UNCHANGED: `ACC_3V3_SW` = 400 mA TOTAL
// and `ACC_5V_SW` = 300 mA TOTAL, each deliverable ALONE.  The two-rail rows
// are derived at the DECLARED SIMULTANEOUS PAIR -- 220 mA on 3.3 V and 170 mA
// on 5 V together -- which is itself solved, not chosen: it is the largest
// proportional derating of the two budgets that holds at the same critical
// cell voltage the single-rail permission already reaches, rounded DOWN onto a
// 10 mA grid.  DEVICE_SPEC publishes both numbers and the per-state table.
// ===========================================================================
// No attainable VCELL authorises the combination.  Above the all-ones code so
// a stuck bus cannot accidentally clear it, and `accessoryEnableAllowed`
// refuses it explicitly rather than by comparison.
constexpr float kAccessoryNotPermittedV = 99.0f;

// The OBSERVABLE high-load modes, in the bit order the derivation sorts them
// in: bit 0 Wi-Fi / BLE TX, bit 1 audio at the capped level, bit 2 sub-GHz TX.
// The NFC field and a microSD write are NOT here: both are carried as
// bounded-duty allowances inside the always-on set of the canonical ledger,
// so they are already in every floor below.
struct AccessoryLoadState {
  bool wifi_tx = false;
  bool amplifier_on = false;
  bool subghz_tx = false;
};

inline unsigned accessoryLoadBits(const AccessoryLoadState &s) {
  return (s.wifi_tx ? 1u : 0u) | (s.amplifier_on ? 2u : 0u) |
         (s.subghz_tx ? 4u : 0u);
}

// TWO EDGES, TWO TABLES, AND THE REASON IS THE PRE-STATE.
//
// A floor is "the reported value below which the settled post state could
// report under the retention floor".  That depends on what the gauge can
// report BEFORE the change, and the two ways into the same state do not share
// a pre-state:
//
//   RAIL EDGE   a rail is switched on.  The mode set does not change, so the
//               pre-read is taken with THOSE modes running and the accessory
//               idle.
//   MODE EDGE   a mode is entered while rails are already live.  The pre-read
//               is taken with the mode set ONE STEP LIGHTER, so it reads
//               HIGHER, so the floor is HIGHER.
//
// Collapsing them means taking the larger, and D-790 has already shown what
// that costs: the rail-edge floor for a state with the Wi-Fi radio up would
// become 3.95 V, while the highest value the gauge can report in that state
// with the accessory idle is 3.8049 V.  The rail would never turn on, and no
// diagnostic anywhere would say why.  That is D790-A03 exactly, and it is why
// there are two tables and why F12 attainability-checks each row against its
// OWN pre-state ceiling.
//
// GENERATED VALUES -- derived by F12, pinned by F12, row by row and sentinel
// by sentinel.  Index is the mode bits; `one_rail_V` is one accessory rail at
// its full published budget, `two_rails_V` is both rails at the declared
// simultaneous pair.
struct AccessoryPermissionRow {
  float one_rail_V;
  float two_rails_V;
};

// The RAIL edge.  Pre-state: these modes, accessory idle.
inline const AccessoryPermissionRow &accessoryRailEdgeRow(unsigned bits) {
  static const AccessoryPermissionRow kRailRows[8] = {
      {3.80f, 3.80f},  // 0  no optional mode
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 1  Wi-Fi / BLE TX
      {3.85f, 3.85f},  // 2  audio at the capped level
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 3  Wi-Fi + audio
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 4  sub-GHz TX
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 5  Wi-Fi + sub-GHz
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 6  audio + sub-GHz
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 7  all three
  };
  return kRailRows[bits & 7u];
}

// The MODE edge.  Pre-state: the lightest mode set one step below, accessory
// idle -- a higher pre-read, therefore a higher floor.
inline const AccessoryPermissionRow &accessoryModeEdgeRow(unsigned bits) {
  static const AccessoryPermissionRow kModeRows[8] = {
      {3.80f, 3.80f},  // 0  no optional mode
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 1  Wi-Fi / BLE TX
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 2  audio at the capped level
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 3  Wi-Fi + audio
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 4  sub-GHz TX
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 5  Wi-Fi + sub-GHz
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 6  audio + sub-GHz
      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 7  all three
  };
  return kModeRows[bits & 7u];
}

inline float accessoryEdgeFloor(const AccessoryPermissionRow &row, int rails) {
  if (rails == 1) return row.one_rail_V;
  if (rails == 2) return row.two_rails_V;
  return kAccessoryNotPermittedV;
}

// `rails_after` is how many accessory rails will be ON once the request is
// granted: 1 or 2.  Anything else is refused.
inline float accessoryEnableFloor(const AccessoryLoadState &modes,
                                  int rails_after) {
  return accessoryEdgeFloor(accessoryRailEdgeRow(accessoryLoadBits(modes)),
                            rails_after);
}

inline float accessoryModeEntryFloor(const AccessoryLoadState &modes_after,
                                     int rails_on) {
  return accessoryEdgeFloor(
      accessoryModeEdgeRow(accessoryLoadBits(modes_after)), rails_on);
}

inline bool accessoryCombinationPermitted(const AccessoryLoadState &modes,
                                          int rails_after) {
  return accessoryEnableFloor(modes, rails_after) < kAccessoryNotPermittedV;
}

inline bool accessoryModeEntryPermitted(const AccessoryLoadState &modes_after,
                                        int rails_on) {
  return accessoryModeEntryFloor(modes_after, rails_on)
         < kAccessoryNotPermittedV;
}

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

// ===========================================================================
// D-794 / R13-01.  A VALID READING IS NOT NECESSARILY A READING OF THE
// PRESENT STATE.
//
// ROUND-13, IN ITS OWN WORDS: "Production display/backlight initialization can
// materially change load after the last MAX17048 conversion.  Current
// admission logic may read a valid-but-pre-load VCELL and authorize a rail
// that immediately falls below retention after the display load plus
// accessory load.  Astra reproduced the real production p -> 5 sequence with
// physical latch modeling: enable write occurs, settled read falls below
// 3.20 V, then safe shed.  Fix the ROOT timing/validity rule: after any
// material load edge relevant to admission, invalidate the prior safety
// conversion, wait for a genuinely new qualified MAX17048 conversion, and
// re-read before granting accessory power.  Do not treat I2C ACK or
// active-mode status as proof the conversion is post-load."
//
// IT REPRODUCES, AND EVERY GUARD THIS PROGRAMME HAS BUILT SO FAR IS ABOUT A
// DIFFERENT QUESTION.  D-779 refused an implausible value.  D-784 refused a
// hibernating part.  D-790 refused a sleeping one.  D-791 refused a floor
// derived from the wrong pre-state.  Every one of them asks whether the
// NUMBER is trustworthy.  None of them asks WHEN THE NUMBER IS FROM -- and
// that is a separate question with a separate answer, because a MAX17048 in
// perfect health, fully qualified, ACKing every transfer, returns the result
// of a conversion that finished before the caller did anything.
//
// THE AGE IS PUBLISHED AND IT IS NOT SMALL.  ADI 19-6171 Rev.7, VCELL Register
// (0x02), in its own words: "VCELL is the average of four ADC conversions.
// The value updates every 250ms in active mode."  Two separate facts, and the
// second is the one that has been missed: the register is not a sample, it is
// a MOVING AVERAGE OF FOUR.  Immediately after a load edge the register still
// contains four pre-load conversions.  One update later it contains three.
// Only after FOUR updates is every conversion in the average post-load, so the
// interval after which the register is guaranteed to describe the present load
// is 4 x 250 ms = 1000 ms.  ADI publishes no separate ADC conversion period
// and no way to observe which conversions are in the average, so four updates
// is the only bound that can be STATED rather than assumed.
//
// D-779'S 400 ms WAS DERIVED AGAINST THE OTHER FACT.  Its own comment says so:
// "the MAX17048 updates VCELL about every 250 ms ... 400 ms covers one update
// with margin".  One update.  Three quarters of the average is still pre-load
// at that point, and the reading is optimistic by three quarters of the step.
// That is why the post-enable recheck could pass and the next one shed.
//
// WHAT THIS CLASS IS.  A LOAD EPOCH: the instant of the most recent material
// change in what the board draws.  Admission may not use a conversion older
// than that epoch plus the full averaging window, and the rule is stated in
// TIME rather than in bus health, because no transfer-level fact can answer
// it.  An ACK proves the part is alive.  MODE.HibStat proves it is converting.
// Neither proves it has converted SINCE THE LOAD ARRIVED.
// ===========================================================================
constexpr uint32_t kGaugeVcellUpdateMs = 250;
constexpr unsigned kGaugeVcellAveragedConversions = 4;
// The interval after a load edge at which every conversion in the VCELL
// average is guaranteed post-load.
constexpr uint32_t kGaugePostLoadConversionMs =
    kGaugeVcellUpdateMs * kGaugeVcellAveragedConversions;
static_assert(kGaugePostLoadConversionMs == 1000,
              "ADI 19-6171 Rev.7: four averaged conversions at a 250 ms "
              "update rate is a 1000 ms window");

class GaugeLoadEpoch {
 public:
  // A material change in what the board draws.  `now_ms` is the moment the
  // new load is ESTABLISHED, not the moment the operation began.
  void noteMaterialLoadEdge(uint32_t now_ms, const char *what) {
    armed_ = true;
    edge_ms_ = now_ms;
    what_ = (what == nullptr) ? "an unnamed load edge" : what;
  }

  bool armed() const { return armed_; }
  const char *what() const { return what_; }
  uint32_t edgeMs() const { return edge_ms_; }

  // How much longer the VCELL average may still contain pre-load conversions.
  uint32_t remainingMs(uint32_t now_ms) const {
    if (!armed_) return 0;
    const uint32_t elapsed = now_ms - edge_ms_;     // wraps correctly
    if (elapsed >= kGaugePostLoadConversionMs) return 0;
    return kGaugePostLoadConversionMs - elapsed;
  }

  bool conversionIsPostLoad(uint32_t now_ms) const {
    return remainingMs(now_ms) == 0;
  }

  // Called once the window has genuinely been spent.  The epoch is not
  // cleared by anything else -- in particular not by a successful read, a
  // successful qualification or a successful transfer, which is the whole
  // point of R13-01.
  void noteWindowSpent(uint32_t now_ms) {
    if (armed_ && conversionIsPostLoad(now_ms)) armed_ = false;
  }

 private:
  bool armed_ = false;
  uint32_t edge_ms_ = 0;
  const char *what_ = "none";
};

enum class AccessoryBatteryAction { Keep, Shed5v, ShedAll };

// THE RAIL EDGE.  `other_rail_on` says whether the OTHER accessory rail is
// already live, so the request lands on the one-rail or the two-rail column.
//
// There is deliberately NO overload that omits the mode set.  D-791 had one,
// and it is how the production image came to grant a permission the model
// never derived for the state the board was actually in: a caller that does
// not know its own modes must not be able to ask.
inline bool accessoryEnableAllowed(bool vcell_valid, float vcell,
                                   bool other_rail_on,
                                   const AccessoryLoadState &modes) {
  const int rails_after = other_rail_on ? 2 : 1;
  if (!accessoryCombinationPermitted(modes, rails_after)) return false;
  return vcell_valid && vcellIsPlausible(vcell)
         && vcell >= accessoryEnableFloor(modes, rails_after);
}

// THE MODE EDGE, AND IT IS THE HALF D-791 HAD NO WORD FOR.
//
// A permission granted in `display_only` says nothing about the state the user
// reaches by pressing the tone key thirty seconds later.  Entering a high-load
// mode while an accessory rail is live is the SAME transition as enabling the
// rail, walked in the other order, and it has to be judged by the same rule
// against the mode set that will exist AFTERWARDS.  With no rail on, every
// mode combination is permitted -- the accessory tree is what the restriction
// is about -- so the guard is transparent until it has something to protect.
inline bool accessoryModeEntryAllowed(bool vcell_valid, float vcell,
                                      int rails_on,
                                      const AccessoryLoadState &after) {
  if (rails_on <= 0) return true;
  if (!accessoryModeEntryPermitted(after, rails_on)) return false;
  return vcell_valid && vcellIsPlausible(vcell)
         && vcell >= accessoryModeEntryFloor(after, rails_on);
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

// ===========================================================================
// D-793 / R12-08.  A DUTY AVERAGE IS NOT AN INSTANTANEOUS PERMISSION BOUND,
// SO THE BURSTS ARE SERIALISED.
//
// ROUND-12, IN ITS OWN WORDS: "D-792 uses sustained duty allowance for SD/NFC/
// IR bursts while permission/retention transitions occur on much shorter
// electrical timescales.  Astra constructed a credible quiet-pre-read ->
// accessory enable + burst -> post-read below retention case.  Separate
// thermal averaging from instantaneous electrical permission.  Enumerate
// actual peak/burst pre/post transitions and maximum burst durations, OR
// enforce a clear scheduling restriction in firmware."
//
// The canonical ledger carries a microSD write at 100 mA for 50 % of a minute,
// the NFC field at 100 mA for 25 % and an IR burst at 50 mA for 10 %.  Those
// duty averages -- 80 mA in total -- are the right model for HEAT and the
// wrong one for a PERMISSION EDGE: the pre-read is taken in a quiet moment and
// the settled recheck lands about 400 ms later, and a logging write, a card
// tap or a key repeat can begin anywhere in between.  Charged as a coincident
// sum the three peaks add 170 mA at that instant and cost FOUR of the sixteen
// permission rows -- every accessory state with the amplifier driving.
//
// THIS CLASS IS THE ALTERNATIVE R12-08 OFFERS, AND IT IS CHEAPER THAN THE
// ROWS.  At most ONE bursty peripheral may be active at a time, so the ruling
// instantaneous delta is the worst SINGLE burst -- 75 mA -- rather than the
// sum.  The restriction is unconditional rather than conditional on a rail
// being live, deliberately: a rule that engages only while a rail is on
// cannot say anything about the ordering in which a rail is enabled DURING
// two already-running bursts, and an unconditional rule is sound under every
// ordering.  Nothing a user does with the card, the tag reader or the IR
// blaster ALONE is restricted; only overlapping two of them is, and that is
// not a published capability.
//
// `demo_feature_contract` F12 derives the permission table at the SERIALISED
// delta only if it can find this arbiter in the shipped firmware AND find the
// production call sites going through it.  Otherwise it derives at the full
// coincident 170 mA and the table tightens.  The restriction is therefore
// pinned to the code that implements it rather than asserted in a comment.
// ===========================================================================
enum class BurstLoad : unsigned char {
  None = 0,
  MicroSdWrite,
  NfcField,
  IrTransmit,
};

inline const char *burstLoadName(BurstLoad which) {
  switch (which) {
    case BurstLoad::MicroSdWrite: return "microSD write";
    case BurstLoad::NfcField: return "NFC field";
    case BurstLoad::IrTransmit: return "IR transmit";
    default: return "none";
  }
}

class BurstArbiter {
 public:
  BurstArbiter() : active_(BurstLoad::None) {}

  BurstLoad active() const { return active_; }

  // REFUSES while ANY bursty load holds the arbiter -- including the same one,
  // for the same re-entrancy reason `SpiBusB::select` refuses a repeat select:
  // a nested hold would release at the inner scope's exit and leave the outer
  // scope believing it still owned the slot.
  bool begin(BurstLoad which) {
    if (which == BurstLoad::None) return false;
    if (active_ != BurstLoad::None) return false;
    active_ = which;
    return true;
  }

  void end(BurstLoad which) {
    if (active_ != which) return;
    active_ = BurstLoad::None;
  }

  // RAII, so a scope cannot forget to release.
  class Hold {
   public:
    Hold(BurstArbiter &arbiter, BurstLoad which)
        : arbiter_(arbiter), which_(which), ok_(arbiter.begin(which)) {}
    ~Hold() { if (ok_) arbiter_.end(which_); }
    bool ok() const { return ok_; }
   private:
    BurstArbiter &arbiter_;
    BurstLoad which_;
    bool ok_;
  };

 private:
  BurstLoad active_;
};

}  // namespace aqroot
