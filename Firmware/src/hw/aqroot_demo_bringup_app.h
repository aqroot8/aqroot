#pragma once
// AQROOT Demo -- THE PRODUCTION CALL SITES, IN A HEADER A HOST TEST COMPILES.
//
// ADDED AT D-789 / D788-04 + D788-05 + D788-06.
//
// Round-8 reproduced the SAME false green one level further out than Round-7
// did.  D-788 moved the two *leaf* entry points -- `backlightRamp()` and
// `configureFuelGaugeActiveModeOnHardware()` -- into headers so
// `test_production_timing.cpp` could execute them, and Astra then showed that
// the OUTER CALLERS were still uncompiled by any test and still free:
//
//   D788-04  an early return in `demo/main.cpp`'s own
//            `configureFuelGaugeActiveMode()` leaves the tested helper alive
//            but DEAD, and authorises a safety VCELL with a 0 ms settle.  The
//            whole H1-H8 suite passed.
//   D788-05  a complete duplicate backlight implementation, with a no-op
//            microsecond hold, placed in the serial dispatch beside the tested
//            `backlightRamp()`, passed everything.
//   D788-06  mutants that dropped `g_expanders.begin()` from the warm-reset
//            retry, forced the reset-release diagnostic to report success, or
//            printed the WANTED accessory state instead of the RECONCILED one,
//            all passed.
//
// The lesson is the same one twice: a call site that no host test compiles is
// not covered by any gate, however well covered the function it calls is.  So
// every safety-relevant call site in the bring-up image now lives HERE, in a
// header that needs only the Arduino surface `Firmware/test/harness/Arduino.h`
// provides, and `Firmware/test/test_production_callers.cpp` constructs this
// class over a recording bus and a PHYSICAL-LATCH expander model and drives
// the real methods.  `demo/main.cpp` owns no second copy of any of them.
//
// WHAT MAY NOT MOVE BACK OUT.  Anything a mutation control in
// `checks/firmware_hw_map_contract.py` names.  A future edit that reinstates a
// private copy in `demo/main.cpp` is caught by `H8_production_callers`, which
// requires the shipped `demo/main.cpp` to reach each of these behaviours
// THROUGH this class and to contain no second implementation of them.

#include <stdint.h>
#include <stdio.h>

#include <Arduino.h>

#include "aqroot_accessory_power_policy.h"
#include "aqroot_demo_backlight.h"
#include "aqroot_demo_board.h"
#include "aqroot_demo_expanders.h"
#include "aqroot_demo_gauge_bringup.h"
#include "aqroot_demo_timing_policy.h"
#include "aqroot_spi_bus_b.h"
#include "max17048_guard.h"

namespace aqroot {

// How long the board waits after an accessory step before re-reading VCELL.
//
// D-779 derived this as "the MAX17048 updates VCELL about every 250 ms in
// active mode ... 400 ms covers one update with margin", and D-794 / R13-01
// SUPERSEDES that derivation: ADI 19-6171 Rev.7 says the register is the
// AVERAGE OF FOUR conversions updated every 250 ms, so one update leaves
// three quarters of the average describing the load as it was BEFORE the
// step.  The governing interval is `kGaugePostLoadConversionMs` -- 1000 ms at
// D-794, 1300 ms since D-795 / R14-01 derived it at the slow end of tERR and
// with the straddling conversion counted -- enforced by the load epoch inside
// `readFuelCellVoltage`.
//
// This constant is RETAINED as the ELECTRICAL settling allowance -- the time
// the node itself needs to reach its new operating point before any
// conversion of it means anything -- and the epoch wait then covers the
// remainder of the averaging window on top of whatever this has already
// spent.  The two answer different questions and neither replaces the other.
constexpr uint32_t kAccessorySettledRecheckMs = 400;
// The warm-reset recovery retry period and the background requalification
// period, both of which are LIVENESS requirements: a board that gave up would
// sit with an unknown latch state forever.
constexpr uint32_t kExpanderRecoveryPeriodMs = 250;
constexpr uint32_t kGaugeRequalPeriodMs = 1000;
constexpr uint32_t kBatteryGuardPeriodMs = 500;
// D-793 / R12-03.  How often a board that could not confirm the radio quiesce
// retries it.  Liveness: an unconfirmed radio state refuses accessory power,
// so a board that gave up would refuse it forever.
constexpr uint32_t kRadioQuiescePeriodMs = 250;
// ===========================================================================
// D-796 / D796-05 item 4 + D796-09 C-NFC-QUIESCE-01.  THE NFC REVOCATION
// DEADLINE IS A DERIVED CONSTANT, AND THE SCHEDULE IS BUILT TO MEET IT.
//
// ROUND-15: "current plan says revocation within 1 s, but the production-
// image trace can remain unrevoked for ~2.6 s during blocking gauge/admission
// work."  It reproduced on the host image at 2620 ms: D-795 serviced the
// liveness probe once per `loop()`, with a 1000 ms period, and ONE '5' press
// spends the admission window (1300 ms), the settled recheck (400 ms) and the
// rest of the window from the rail step (900 ms) inside a single iteration.
// A rail could even be GRANTED on a confirmation whose part had already gone.
//
// THE SCHEDULE NOW:
//   * the probe runs at the top of every `loop()` -- before the expander
//     recovery branch, because the probe needs SPI-B, not I2C;
//   * every app-owned wait (the gauge window in `waitForPostLoadConversion`,
//     the settled recheck in `waitServicingNfcLiveness`) is sliced into
//     `kNfcLivenessPollSliceMs` pieces with a liveness opportunity before
//     each slice;
//   * the one non-preemptible wait left on an admission path -- the
//     MAX17048's 300 ms qualified settle, which lives in a seam H7/H8 pin --
//     is preceded by a liveness opportunity;
//   * every GRANT (rail admission, mode entry with a rail live, a non-NFC
//     burst) re-proves liveness at the grant itself, so no permission is ever
//     decided on a proof older than the decision.
//
// THE BOUND.  A part lost just after a successful probe at t is next probed
// at the first opportunity at or after t + P, and opportunities are never
// more than G apart on any path that has something to shed or is deciding a
// grant.  Revocation runs the shed in the same call.  So
//
//     deadline = P + G + W
//              = kNfcLivenessPeriodMs (500)
//              + kNfcLongestUnpolledStepMs (300, = max(slice 100, settle 300))
//              + kNfcRevocationWorkAllowanceMs (20)
//              = 820 ms,
//
// inside the 1 s C-NFC-QUIESCE-01 promises.  W is the execution time of the
// probe (seven two-byte SPI frames at 4 MHz, ~0.1 ms) and the shed (at most
// six PCAL9535A transactions at 400 kHz, ~0.6 ms) on healthy buses; the host
// clock does not charge for it, so it is carried as an explicit allowance
// and measured on the bench by C-NFC-QUIESCE-01.
//
// WHAT IS OUTSIDE IT, AND WHY THAT IS SAFE.  With BOTH accessory rails
// confirmed off, the operator demo tests ('l' backlight ramp ~830 ms, 'p'
// display init, 't' tone, 'm' microphone) are not preemptible and may delay a
// revocation by their own length -- at most 827 ms, the backlight ramp, so
// at most 1347 ms in all (`kNfcRevocationWithRailsOffOperatorTestMs`, derived
// below).  There is nothing to shed in that state --
// `blockingDemoTestAllowed` refuses every one of them while a rail is live --
// and no later grant can use the stale confirmation, because every grant
// re-proves liveness first.  `test_production_image.cpp` sweeps the loss over
// every 20 ms of a first- and second-rail admission from five probe phases.
// ===========================================================================
// How often a confirmed-quiet ST25R3916 is asked to prove it is still alive.
// D-795 had 1000 ms; that period alone consumed the whole 1 s promise.
constexpr uint32_t kNfcLivenessPeriodMs = 500;
// The longest single delay an app-owned wait takes between two liveness
// opportunities.
constexpr uint32_t kNfcLivenessPollSliceMs = 100;
// The longest step with NO liveness opportunity on a path that has a rail to
// shed or a grant to decide: the MAX17048 qualified settle (first-rail
// admission, background requalification, expander recovery), or one slice.
constexpr uint32_t kNfcLongestUnpolledStepMs =
    kFuelGaugeActiveSettleMs > kNfcLivenessPollSliceMs
        ? kFuelGaugeActiveSettleMs : kNfcLivenessPollSliceMs;
// Probe plus shed execution on healthy buses (see above).
constexpr uint32_t kNfcRevocationWorkAllowanceMs = 20;
constexpr uint32_t kNfcRevocationDeadlineMs =
    kNfcLivenessPeriodMs + kNfcLongestUnpolledStepMs +
    kNfcRevocationWorkAllowanceMs;
static_assert(kNfcLongestUnpolledStepMs == 300,
              "the longest unpolled step is the 300 ms MAX17048 settle");
static_assert(kNfcLivenessPollSliceMs <= kNfcLongestUnpolledStepMs,
              "a wait slice may not be the new longest unpolled step");
static_assert(kNfcRevocationDeadlineMs == 820,
              "500 ms period + 300 ms unpolled step + 20 ms allowance");
static_assert(kNfcRevocationDeadlineMs <= 1000,
              "C-NFC-QUIESCE-01 promises revocation and shed within 1 s");
static_assert(kAccessorySettledRecheckMs > kNfcLivenessPollSliceMs,
              "the settled recheck is long enough to need slicing");

// ---------------------------------------------------------------------------
// D-796.  THE ONE EXCEPTION TO THE 820 ms BOUND, STATED AS A NUMBER.
//
// With BOTH accessory rails confirmed OFF, the operator demo tests are not
// preemptible and run with no liveness opportunity inside them.  A U9 lost
// just after a probe, with a test started the instant before the next probe
// fell due, is revoked at most P + (the test's own length) + W after the loss.
// The tests, by the waits they are built from:
//
//   'l' backlight ramp   3 ms prime + 51 up-steps x 8 ms + 52 down-steps x
//                        8 ms = 827 ms of delay (plus PWM set-up, microseconds)
//   'p' display init     40 ms DISP_RST_N pulse + 260 ms ILI9488 SWRESET /
//                        SLPOUT / DISPON waits + ~184 ms of 20 MHz pixel data
//                        (320 x 480 x 3 bytes) = ~485 ms
//   't' tone             5 ms + 400 ms of I2S + ~35 ms of DMA drain = ~440 ms
//   'm' microphone       at most 200 ms + 200 ms capture deadline = 400 ms
//   'd' microSD, 'x' IR  a few ms; both are bursts and re-prove liveness at
//                        their grant anyway
//
// So the longest is the backlight ramp, 827 ms, and the worst revocation in
// that state is 500 + 827 + 20 = 1347 ms.  It is SAFE for two reasons, both
// tested: there is nothing to shed (`blockingDemoTestAllowed` refuses every
// one of these tests while a rail is live), and no later grant can use the
// stale confirmation (every grant re-proves liveness first).  It is a
// published first-five limitation, not a hidden one.
constexpr uint32_t kLongestUnpreemptibleOperatorTestMs =
    kBacklightStartupPrimeUs / 1000u + (51u + 52u) * 8u;
static_assert(kLongestUnpreemptibleOperatorTestMs == 827,
              "the backlight ramp's waits are 3 + 103 x 8 = 827 ms");
constexpr uint32_t kNfcRevocationWithRailsOffOperatorTestMs =
    kNfcLivenessPeriodMs + kLongestUnpreemptibleOperatorTestMs +
    kNfcRevocationWorkAllowanceMs;
static_assert(kNfcRevocationWithRailsOffOperatorTestMs == 1347,
              "500 + 827 + 20 ms, rails off, nothing to shed");

// D-795 / R14-01, re-derived at D-796.  How many slices the gauge reader
// takes before it gives up on a window it cannot confirm spent.  The window
// needs ceil(1300 / 100) = 13 slices on an honest clock; eight more absorb
// delays that return a tick early.  A clock that never advances costs all of
// them and yields NO reading.
constexpr unsigned kGaugeWindowWaitAttempts =
    (kGaugePostLoadConversionMs + kNfcLivenessPollSliceMs - 1) /
        kNfcLivenessPollSliceMs + 8;
static_assert(kGaugeWindowWaitAttempts == 21,
              "13 slices of 100 ms cover the 1300 ms window, plus 8 spare");

// What `releaseExpanderResetLines()` could prove.  D-788 / R7-D787-08 made the
// diagnostic honest; D788-06 makes it EXECUTABLE.
enum class ResetRelease { Confirmed, Failed, Unknown };

struct ResetReleaseReport {
  ResetRelease verdict = ResetRelease::Unknown;
  bool writes_acked = false;
  bool shadow_known = false;
  uint16_t latch = 0xFFFF;
  bool ok() const { return verdict == ResetRelease::Confirmed; }
};

// `Bus` is an `I2cBus` that also offers `reopen(uint32_t)` and
// `setClock(uint32_t)`.  `Log` is anything callable with a `const char *`.
template <typename Bus, typename Log>
class DemoBringupApp : public AccessoryLoadAuthority {
 public:
  DemoBringupApp(Bus &bus, DemoExpanders &expanders, Max17048Guard &gauge,
                 Log log)
      : bus_(bus), expanders_(expanders), gauge_(gauge), log_(log) {}

  bool acc3v3() const { return acc3v3_; }
  bool acc5v() const { return acc5v_; }
  bool accessoryI2c() const { return accessory_i2c_; }

  // =========================================================================
  // D-792 / R11-04.  THE OBSERVABLE HIGH-LOAD MODE SET, AS THE PERMISSION
  // TABLE INDEXES IT.
  //
  // The table in `aqroot_accessory_power_policy.h` is indexed by which of
  // three modes is ON, so this class has to be able to say which.  Two of the
  // three it OWNS -- the amplifier through its own intent, and a keyed sub-GHz
  // transmitter through the `AccessoryLoadAuthority` hook `SpiBusB` calls.  The
  // third, the Wi-Fi/BLE radio, is not brought up by this bring-up image at
  // all; `noteWifiRadioActive` exists so the path that eventually does bring it
  // up cannot do so without telling the permission rule, and
  // `wifiActivationPermitted` is the guard it has to ask first.
  //
  // THE AMPLIFIER READING IS FAIL-CLOSED, AND THE DIRECTION IS THE WHOLE
  // POINT.  It counts as ON unless U2's physical output shadow CONFIRMS it
  // OFF.  `amplifierConfirmed(true)` would have been the natural spelling and
  // it is the wrong one: that predicate is false BOTH when the amplifier is
  // off AND when the shadow is unknown -- which is exactly the state a NACKed
  // write leaves behind, and exactly the state in which the amplifier may
  // already be energised.  Reading an unknown latch as OFF would understate
  // the load and hand the permission table a mode set the board is not in.
  // D-783's whole finding is that the optimistic direction is the wrong one.
  // =========================================================================
  bool amplifierCountsAsOn() const { return !amplifierConfirmed(false); }

  // =========================================================================
  // D-793 / R12-03.  A RETAINED TRANSMIT STATE SURVIVES AN MCU RESET AND THE
  // SOFTWARE MODEL OF IT DOES NOT.
  //
  // ROUND-12, IN ITS OWN WORDS: "Astra reproduced retained physical CC1101
  // transmit state while software resets its arbiter/mode state to NONE.  U7
  // stays powered; CS parking is not a radio reset."
  //
  // It reproduces exactly.  `SpiBusB::transmitting_` and `subghz_tx_` are both
  // zeroed by construction, and construction is what an MCU reset does.  U7
  // (CC1101) and U8 (SX1262) are supplied from +3V3, which an MCU reset does
  // not interrupt, so an `STX` issued by the image that died is still keying
  // the PA while this object reports no transmitter and hands the permission
  // table a mode set the board is not in.  That is the SAME defect class as
  // D-766's powered PCAL9535A latches, one subsystem further out.
  //
  // THE DIRECTION IS PESSIMISTIC AND THAT IS THE WHOLE POINT.  Until the boot
  // path has quiesced both transceivers and CONFIRMED it from their own
  // status registers, `subGhzTransmitting()` reads TRUE.  The permission table
  // refuses every accessory combination with a sub-GHz transmitter keyed, so
  // an unconfirmed radio state refuses accessory power rather than granting it
  // against a load the board may actually be carrying.
  //
  // THE NFC FRONT END IS NOW TREATED THE SAME WAY, AND D-793's REASON FOR NOT
  // DOING SO WAS A FALSE PREMISE.  D-793 wrote here that "this repository holds
  // NO ST25R3916 datasheet", so a register write would have been a decode
  // carried from memory -- D-742's standing lesson.  The datasheet is
  // `hardware/beta/kicad/aqroot-beta/vendor/ST25R3916/ST25R3916_DS12484_Rev3.pdf`
  // and has been in the tree since the Beta board was drawn.  R12-03's actual
  // instruction -- "do not blindly add resets without primary-device
  // semantics" -- was satisfiable from the archive on the day it was written.
  //
  // D-794 / R13-03 therefore quiesces U9 with its OWN documented mechanism and
  // VERIFIES the physical state; see `noteNfcFieldQuiesced` below and
  // `st25r3916Quiesce` in `aqroot_demo_radios.h`.  D-793's fallback argument --
  // that a retained field is bounded because the ledger carries it as a
  // duty allowance inside the ALWAYS-ON set -- is TRUE OF THE HEAT and FALSE
  // OF THE PERMISSION: the allowance is 25 % of 100 mA and a field a dead
  // image left keyed draws 100 mA continuously, four times what every floor in
  // the permission table was derived against.
  // =========================================================================
  bool radiosQuiesced() const { return radios_quiesced_; }
  bool radioPhysicalStateIsKnown() override { return radios_quiesced_; }
  void noteRadiosQuiesced(bool confirmed) {
    radios_quiesced_ = confirmed;
    // D-795 / R14-01: a confirmed quiesce may just have stopped a retained
    // transmitter, which is a load edge the gauge average still contains.
    if (confirmed) noteMaterialLoadEdge("the sub-GHz radio quiesce");
    if (!confirmed) {
      log_("radio quiesce: NOT CONFIRMED -- the physical transmit state of "
           "U7/U8 is UNKNOWN.  Sub-GHz TX is treated as KEYED and accessory "
           "power is refused until a confirmed quiesce.");
    }
  }

  // =========================================================================
  // D-794 / R13-03.  THE NFC FIELD IS A THIRD RETAINED STATE, AND IT OWNS A
  // BURST SLOT WHETHER OR NOT THIS IMAGE ASKED FOR ONE.
  //
  // ROUND-13: "Ensure BurstArbiter ownership matches physical field state
  // after reset and prevents SD/IR/NFC overlap when the retained field is
  // unconfirmed."
  //
  // The arbiter exists because the permission table is derived at the worst
  // SINGLE burst rather than the coincident sum of three (D-793 / R12-08).
  // That derivation is only sound if the arbiter's model of who is bursting
  // matches the board.  An MCU reset zeroes `BurstArbiter::active_` while U9
  // is still driving its antenna -- so the arbiter says "nobody" and hands a
  // microSD write or an IR burst the slot the NFC field is physically already
  // occupying, and the coincident sum the table refused to charge for is
  // exactly what the board then draws.
  //
  // So an UNCONFIRMED field TAKES the slot.  Not as a flag beside it -- as
  // the arbiter's real owner, because every consumer already asks the
  // arbiter and none of them should have to learn a second rule.  A confirmed
  // quiesce releases it.
  // =========================================================================
  void noteNfcFieldQuiesced(bool confirmed, uint8_t operation_control = 0xFF,
                            const char *why = nullptr) {
    // D-796 / D796-10: a field session owns U9; a quiesce verdict taken
    // while it does (the radio layer refuses to touch the part) is not a
    // verdict about the field.
    if (nfc_session_active_) return;
    nfc_field_confirmed_off_ = confirmed;
    nfc_operation_control_ = operation_control;
    if (confirmed) {
      burst_.end(BurstLoad::NfcField);
      // D-795 / R14-01: the quiesce may have dropped a retained carrier.
      noteMaterialLoadEdge("the NFC field quiesce");
      return;
    }
    // Take the slot on behalf of the part.  `begin` refuses if something else
    // holds it, which cannot be true this early on a boot path but is the
    // correct behaviour if it ever is: the arbiter stays honest either way.
    (void)burst_.begin(BurstLoad::NfcField);
    char line[288];
    snprintf(line, sizeof(line),
             "NFC quiesce: NOT CONFIRMED (%s; Operation control reads "
             "0x%02X) -- a live, identified ST25R3916 must prove the field "
             "off (D-795 / R14-02).  The field state is UNKNOWN, the "
             "burst slot is held on U9's behalf, and accessory power is "
             "refused until a confirmed quiesce.",
             why == nullptr ? "no liveness proof" : why,
             unsigned(operation_control));
    log_(line);
  }

  bool nfcFieldConfirmedOff() const { return nfc_field_confirmed_off_; }

  // ===========================================================================
  // D-795 / R14-02.  AN OFF CONFIRMATION IS HELD ONLY WHILE THE PART KEEPS
  // ANSWERING.
  //
  // ROUND-14: "Invalid identity/liveness after a previous OFF confirmation
  // must revoke authority."  A part that answered the quiesce and then stops
  // answering is a part whose field this image can no longer see -- a brown-
  // out and re-power, a lifted pin, a chip select that stopped asserting.
  // Its field is UNKNOWN again, so it takes the burst slot back, every rail
  // that was granted while it was confirmed is shed, and the loop's quiesce
  // retry has to prove it all over again.
  bool nfcLivenessDue() {
    if (!nfc_field_confirmed_off_) return false;
    const uint32_t now = millis();
    if (nfc_liveness_started_ && now - last_nfc_liveness_ms_ < kNfcLivenessPeriodMs) {
      return false;
    }
    nfc_liveness_started_ = true;
    last_nfc_liveness_ms_ = now;
    return true;
  }
  void noteNfcLiveness(bool alive, uint8_t identity) {
    if (alive || !nfc_field_confirmed_off_) return;
    nfc_field_confirmed_off_ = false;
    ++nfc_revocations_;
    (void)burst_.begin(BurstLoad::NfcField);
    // D-796 / C-NFC-QUIESCE-01: the SHED runs before the console line.  The
    // deadline is a physical one, and a console write is the one step here
    // whose duration this image does not control.
    if (acc3v3_ || acc5v_ || accessory_i2c_) {
      forceAccessoriesOff("the ST25R3916 field state became UNKNOWN");
    }
    char line[240];
    snprintf(line, sizeof(line),
             "NFC OFF confirmation REVOKED: the ST25R3916 no longer proves "
             "liveness (identity 0x%02X); the field state is UNKNOWN, the "
             "burst slot is held on U9's behalf and accessory power is "
             "refused until a confirmed quiesce (D-795 / R14-02)",
             unsigned(identity));
    log_(line);
  }
  uint32_t nfcRevocations() const { return nfc_revocations_; }

  // ===========================================================================
  // D-796 / D796-05 item 4.  THE PROBE IS THE APP'S TO SCHEDULE.
  //
  // `demo/main.cpp` attaches the hardware probe once, in `setup()`; the app
  // then asks for it wherever the schedule needs an opportunity -- the top of
  // `loop()`, every slice of every app-owned wait, before the qualified
  // settle, and at every grant.  `force` skips the period (a grant must be
  // decided on a proof taken now).  A `Deferred` probe did not touch the part:
  // it restores the schedule so the probe stays DUE and proves nothing.
  using NfcLivenessProbe = NfcLivenessResult (*)(uint8_t *identity);
  void setNfcLivenessProbe(NfcLivenessProbe probe) { nfc_probe_ = probe; }
  bool nfcLivenessProbeAttached() const { return nfc_probe_ != nullptr; }

  NfcLivenessResult serviceNfcLiveness(bool force = false) {
    if (nfc_probe_ == nullptr) return NfcLivenessResult::Deferred;
    const bool was_started = nfc_liveness_started_;
    const uint32_t was_last = last_nfc_liveness_ms_;
    if (force) {
      // No OFF confirmation, no probe: a field session or an UNKNOWN field
      // is the quiesce's to prove, and a session's 11h is the session's.
      if (!nfc_field_confirmed_off_) return NfcLivenessResult::Deferred;
      nfc_liveness_started_ = true;
      last_nfc_liveness_ms_ = millis();
    } else if (!nfcLivenessDue()) {
      return NfcLivenessResult::Deferred;
    }
    uint8_t identity = 0x00;
    const NfcLivenessResult r = nfc_probe_(&identity);
    if (r == NfcLivenessResult::Deferred) {
      nfc_liveness_started_ = was_started;
      last_nfc_liveness_ms_ = was_last;
      return r;
    }
    ++nfc_liveness_probes_;
    noteNfcLiveness(r == NfcLivenessResult::Alive, identity);
    return r;
  }
  uint32_t nfcLivenessProbes() const { return nfc_liveness_probes_; }

  // A wait that keeps the liveness schedule: sliced, with an opportunity
  // before each slice, and ended on ELAPSED time rather than on the sum of
  // the delays asked for (a delay that returns a tick early is not a clock).
  // Bounded: a clock that does not advance ends it after its attempts.
  void waitServicingNfcLiveness(uint32_t ms) {
    const uint32_t start = millis();
    const unsigned attempts =
        unsigned((ms + kNfcLivenessPollSliceMs - 1) / kNfcLivenessPollSliceMs)
        + 8u;
    for (unsigned attempt = 0; attempt < attempts; ++attempt) {
      (void)serviceNfcLiveness();
      const uint32_t elapsed = millis() - start;
      if (elapsed >= ms) return;
      const uint32_t left = ms - elapsed;
      delay(left < kNfcLivenessPollSliceMs ? left : kNfcLivenessPollSliceMs);
    }
  }

  // ===========================================================================
  // D-796 / D796-10.  A FIELD-OWNING NFC SESSION OWNS U9, AND THE LIVENESS
  // PROBE STANDS DOWN FOR IT.
  //
  // ROUND-15: "NFC liveness probe currently rewrites register 11h while the
  // field is confirmed off.  Document/architect future field-owning firmware
  // so active NFC operation suspends/owns that liveness probe."
  //
  // THE CONTRACT FOR ANY FUTURE FIRMWARE THAT TURNS THE FIELD ON:
  //
  //   1  it calls `beginNfcFieldSession(bus)` FIRST, and only turns the field
  //      on if that returns true.  Begin requires a confirmed-OFF,
  //      liveness-proved part, no accessory rail live, and the burst slot;
  //      it takes the burst slot for `BurstLoad::NfcField` and the SPI-B
  //      ownership token (`SpiBusB::beginTransmit(SpiBDevice::St25r3916)`).
  //   2  while the session holds U9, the OFF confirmation is WITHDRAWN -- the
  //      field is on by design -- so the liveness probe is never scheduled,
  //      and the radio layer refuses to challenge 11h, Set-default or even
  //      select the part for the probe or the quiesce (`nfcFieldSessionOwnsU9`).
  //      Register 11h is the session's No-response timer, not a scratch
  //      register, once the field is its own.
  //   3  it calls `endNfcFieldSession(bus)` when its field is off.  End does
  //      NOT restore the confirmation: the field state is UNKNOWN until the
  //      loop's quiesce retry proves it off again from a live, identified
  //      part.  The slot stays with U9 until then.
  //
  // The shipped bring-up image has no caller: it never turns the field on.
  bool beginNfcFieldSession(SpiBusB &bus) {
    const char *refusal = nullptr;
    if (nfc_session_active_) refusal = "a session already owns U9";
    else if (!nfc_field_confirmed_off_)
      refusal = "the field is not confirmed off by a live part";
    else if (acc3v3_ || acc5v_)
      refusal = "an accessory rail is live and its permission did not "
                "account for a carrier";
    if (refusal == nullptr &&
        serviceNfcLiveness(/*force=*/true) != NfcLivenessResult::Alive) {
      refusal = "U9 did not prove liveness at the session request";
    }
    if (refusal == nullptr && !burstAllowed(BurstLoad::NfcField,
                                            "NFC field session")) {
      refusal = "the burst slot is taken";
    }
    if (refusal == nullptr && !burst_.begin(BurstLoad::NfcField)) {
      refusal = "the burst slot is taken";
    }
    if (refusal == nullptr && !bus.beginTransmit(SpiBDevice::St25r3916)) {
      burst_.end(BurstLoad::NfcField);
      refusal = "the SPI-B transmit slot is taken";
    }
    if (refusal != nullptr) {
      char line[200];
      snprintf(line, sizeof(line), "NFC field session REFUSED: %s (D796-10)",
               refusal);
      log_(line);
      return false;
    }
    nfc_session_active_ = true;
    nfc_field_confirmed_off_ = false;
    noteMaterialLoadEdge("an NFC field session starting");
    log_("NFC field session OWNS U9: the OFF confirmation is withdrawn and "
         "the liveness probe stands down until a quiesce re-proves the "
         "field off (D796-10)");
    return true;
  }
  void endNfcFieldSession(SpiBusB &bus) {
    if (!nfc_session_active_) return;
    bus.endTransmit(SpiBDevice::St25r3916);
    nfc_session_active_ = false;
    noteMaterialLoadEdge("an NFC field session ending");
    log_("NFC field session ENDED: the field state is UNKNOWN until the "
         "quiesce retry proves it off (D796-10)");
  }
  bool nfcFieldSessionActive() const { return nfc_session_active_; }
  uint8_t nfcOperationControl() const { return nfc_operation_control_; }

  AccessoryLoadState accessoryLoadState() const {
    AccessoryLoadState s;
    s.wifi_tx = wifi_tx_;
    s.amplifier_on = amplifierCountsAsOn();
    // PESSIMISTIC WHILE UNKNOWN -- see the block above.  `subghz_tx_` alone
    // would read the reset value of a variable as a fact about a powered
    // radio.
    s.subghz_tx = subghz_tx_ || !radios_quiesced_;
    return s;
  }

  // ---- D-793 / R12-08.  THE BURST ARBITER, AND THE ONE WAY THROUGH IT. ----
  BurstArbiter &burstArbiter() { return burst_; }

  // Every production burst call site goes through this.  It logs the refusal,
  // because a burst that silently does not happen is indistinguishable from a
  // broken peripheral on a bring-up console.
  bool burstAllowed(BurstLoad which, const char *what) {
    if (which == BurstLoad::None) return false;
    // D-796 / C-NFC-QUIESCE-01: a burst beside a possibly retained field is
    // the coincident sum the arbiter exists to refuse, so it too is decided
    // on a liveness proof taken now.
    if (which != BurstLoad::NfcField) (void)serviceNfcLiveness(/*force=*/true);
    // D-795 / R14-02: UNKNOWN owns the slot even if a reset cleared the
    // arbiter or another holder released it -- the rule is the field state,
    // not the arbiter's bookkeeping of it.
    if (!nfc_field_confirmed_off_ && which != BurstLoad::NfcField) {
      char unknown[200];
      snprintf(unknown, sizeof(unknown),
               "%s REFUSED: the ST25R3916 field state is UNKNOWN and U9 owns "
               "the burst slot until a liveness-qualified quiesce "
               "(D-795 / R14-02)", what);
      log_(unknown);
      return false;
    }
    if (burst_.active() == BurstLoad::None) return true;
    char line[224];
    snprintf(line, sizeof(line),
             "%s REFUSED: %s is already drawing its burst and this revision "
             "serialises them (D-793 / R12-08); retry when it finishes",
             what, burstLoadName(burst_.active()));
    log_(line);
    return false;
  }

  int accessoryRailsOn() const {
    return (acc3v3_ ? 1 : 0) + (acc5v_ ? 1 : 0);
  }

  // The mode edge, in ONE place, so the amplifier path, the sub-GHz path and
  // the Wi-Fi path cannot drift apart.  `what` names the mode for the log.
  bool modeEntryAllowed(const AccessoryLoadState &after, const char *what) {
    const int rails = accessoryRailsOn();
    if (rails <= 0) return true;
    float v = 0.0f;
    const bool read = readFuelCellVoltageForAdmission(what);
    v = last_admission_vcell_;
    if (accessoryModeEntryAllowed(read, v, rails, after)) return true;
    const float required = accessoryModeEntryFloor(after, rails);
    char line[224];
    if (required >= kAccessoryNotPermittedV) {
      snprintf(line, sizeof(line),
               "%s REFUSED: with %d accessory rail(s) live this mode "
               "combination has NO attainable VCELL -- disable an accessory "
               "rail first (D-792 permission table)",
               what, rails);
    } else if (!read) {
      snprintf(line, sizeof(line),
               "%s REFUSED: MAX17048 VCELL unreadable and %d accessory "
               "rail(s) are live; mode entry is fail-closed",
               what, rails);
    } else {
      snprintf(line, sizeof(line),
               "%s REFUSED: VCELL %.3f V below the %.2f V floor this mode "
               "needs with %d accessory rail(s) live (D-792 permission table)",
               what, double(v), double(required), rails);
    }
    log_(line);
    return false;
  }

  // ---- `AccessoryLoadAuthority`, called by `SpiBusB::beginTransmit`. -------
  bool subGhzTransmitPermitted() override {
    AccessoryLoadState after = accessoryLoadState();
    after.subghz_tx = true;
    return modeEntryAllowed(after, "sub-GHz TX");
  }
  void noteSubGhzTransmitting(bool on) override {
    // D-795 / R14-01: keying and unkeying a PA are both material load edges.
    if (on != subghz_tx_) {
      noteMaterialLoadEdge(on ? "sub-GHz TX keying" : "sub-GHz TX unkeying");
    }
    subghz_tx_ = on;
  }
  bool subGhzTransmitting() const { return subghz_tx_; }

  // ---- The Wi-Fi/BLE radio.  No production caller in this image yet; the
  // guard exists so the one that arrives cannot skip it.
  bool wifiActivationPermitted() {
    AccessoryLoadState after = accessoryLoadState();
    after.wifi_tx = true;
    return modeEntryAllowed(after, "Wi-Fi / BLE radio");
  }
  void noteWifiRadioActive(bool on) {
    if (on != wifi_tx_) {
      noteMaterialLoadEdge(on ? "the Wi-Fi/BLE radio starting"
                              : "the Wi-Fi/BLE radio stopping");
    }
    wifi_tx_ = on;
  }
  bool wifiRadioActive() const { return wifi_tx_; }

  // -------------------------------------------------------------------------
  // D788-04.  THE OUTER GAUGE CALLER.
  //
  // This is the method Round-8's early-return mutant replaced.  It has no body
  // of its own beyond the call, deliberately: the ordering and the settle both
  // live in `configureFuelGaugeActiveModeOnHardware`, which
  // `test_production_timing.cpp` already runs against a recording clock.  What
  // `test_production_callers.cpp` proves is that the callers below REACH it --
  // that no accessory permission is granted without the qualification and its
  // wait actually having happened.
  bool configureFuelGaugeActiveMode() {
    // D-796 / C-NFC-QUIESCE-01: the qualified settle is the one wait on an
    // admission path this class cannot slice, so it is PRECEDED by a liveness
    // opportunity -- which is what makes it, and not the sum of two settles,
    // the longest unpolled step.
    (void)serviceNfcLiveness();
    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);
  }

  // =========================================================================
  // D-794 / R13-01.  THE ONE GAUGE READER, AND IT OWES THE LOAD EPOCH.
  //
  // R13-01: "after any material load edge relevant to admission, invalidate
  // the prior safety conversion, wait for a genuinely new qualified MAX17048
  // conversion, and re-read before granting accessory power. ... Bind exact
  // production call sites, not helpers only."
  //
  // EVERY production path that acts on VCELL comes through here:
  // `accessoryBatteryAllows` (the enable edge), `modeEntryAllowed` (the mode
  // edge) and `applyAccessoryRetention` (retention and the post-enable
  // settled recheck).  Putting the rule in the reader is what binds all three
  // without a fourth place to forget it, and the reader is in the header the
  // host tests compile and run -- which is the lesson D-788 and D-789 each
  // paid for once.
  //
  // THE WAIT IS SPENT HERE RATHER THAN REFUSED.  A refusal would be safe and
  // useless: the operator presses '5' after looking at the display and gets a
  // rejection for a second, which is indistinguishable from a flat pack.  The
  // board waits out the remainder of the averaging window and then reads, so
  // the answer the permission is granted on describes the load the board is
  // actually carrying.  `noteMaterialLoadEdge` records WHEN; nothing else
  // clears the epoch -- not an ACK, not a qualification, not a successful
  // read.
  bool readFuelCellVoltage(float *volts) {
    // D-795 / R14-01: a window that could not be spent is not a reading.
    if (!waitForPostLoadConversion()) {
      if (volts) *volts = 0.0f;
      return false;
    }
    return gauge_.readVcell(bus_, volts);
  }

  // ===========================================================================
  // D-795 / R14-01.  A NEW ADMISSION OWES A FRESH POST-REQUEST WINDOW.
  //
  // This board cannot see a charger being plugged or unplugged: there is no
  // VBUS-present signal on any MCU or expander pin (D-776).  So an adapter
  // pulled out a moment before the operator presses '5' changes the node the
  // gauge reads with NOTHING in the firmware to stamp it, and the average the
  // permission would be granted on is still the charging-era one -- which
  // over-states the cell by the charge current times the path, exactly the
  // D-794 observation about the gauge node while charging.
  //
  // The only defence that covers an edge the firmware cannot observe is to
  // make the ADMISSION ITSELF an epoch: every rail enable and every mode entry
  // with a rail live stamps its own request and reads only once the whole
  // window since the request has passed.  Whatever happened before the
  // request -- announced or not -- is then out of the average.
  bool readFuelCellVoltageForAdmission(const char *what) {
    char label[96];
    snprintf(label, sizeof(label), "the %s admission request",
             what == nullptr ? "accessory" : what);
    // The epoch keeps a POINTER, so the label must outlive the call: copy it
    // into the member buffer the epoch is allowed to point at.
    snprintf(admission_label_, sizeof(admission_label_), "%s", label);
    load_epoch_.noteAdmissionRequest(millis(), admission_label_);
    last_admission_vcell_ = 0.0f;
    const bool read = readFuelCellVoltage(&last_admission_vcell_);
    // D-796 / C-NFC-QUIESCE-01.  THE GRANT IS DECIDED ON A LIVENESS PROOF
    // TAKEN AT THE GRANT.  Every admission ends here, so a U9 that stopped
    // answering at any point before the decision -- in the window, or in an
    // unpolled operator test before the key press -- is revoked HERE and the
    // admission is refused, rather than granted and shed a period later.
    (void)serviceNfcLiveness(/*force=*/true);
    if (!nfc_field_confirmed_off_) {
      char line[232];
      snprintf(line, sizeof(line),
               "%s REFUSED at the grant: the ST25R3916 field is not confirmed "
               "off by a live part (D-796 / C-NFC-QUIESCE-01)", label);
      log_(line);
      last_admission_vcell_ = 0.0f;
      return false;
    }
    return read;
  }

  // A material change in what the board draws.  Call AFTER the new load is
  // established, because the window is measured from the new load, not from
  // the start of the operation that created it.
  void noteMaterialLoadEdge(const char *what) {
    load_epoch_.noteMaterialLoadEdge(millis(), what);
  }

  // Spend whatever is left of the averaging window.
  //
  // D-795 / R14-01: "Loop on an elapsed deadline; do not merely delay once and
  // assume time advanced enough."  ESP32 Arduino's `delay()` is
  // `vTaskDelay(ms / portTICK_PERIOD_MS)`, which blocks for between n-1 and n
  // tick periods, so one delay of the remainder can return a tick EARLY -- and
  // a delay is not a clock.  The loop re-reads `millis()` and only returns
  // once the elapsed time since the epoch is genuinely past the window.  It is
  // BOUNDED: a clock that does not advance makes this return false, and the
  // caller treats that as no measurement (fail-closed), never as a fresh one.
  //
  // D-796 / C-NFC-QUIESCE-01: the window is spent in slices of at most
  // `kNfcLivenessPollSliceMs`, with a liveness opportunity before each, so a
  // 1300 ms window is no longer 1300 ms in which a lost U9 goes unnoticed.  A
  // revocation inside the window ENDS it with no reading: whatever the
  // reading was for, it is no longer being decided under a confirmed field.
  bool waitForPostLoadConversion() {
    bool logged = false;
    last_wait_ms_ = 0;
    const uint32_t revocations_at_entry = nfc_revocations_;
    for (unsigned attempt = 0; attempt < kGaugeWindowWaitAttempts; ++attempt) {
      (void)serviceNfcLiveness();
      if (nfc_revocations_ != revocations_at_entry) {
        log_("gauge: the ST25R3916 was REVOKED inside the post-load window; "
             "no VCELL reading is taken (fail-closed, D-796)");
        return false;
      }
      const uint32_t remaining = load_epoch_.remainingMs(millis());
      if (remaining == 0) {
        load_epoch_.noteWindowSpent(millis());
        return true;
      }
      if (!logged) {
        logged = true;
        char line[240];
        snprintf(line, sizeof(line),
                 "gauge: VCELL still averages conversions from before %s; "
                 "waiting %lu ms for a post-load conversion before any "
                 "permission (D-795 / R14-01, ADI 19-6171 Rev.7: five "
                 "periods at tERR +3.5 %%)",
                 load_epoch_.what(), (unsigned long)remaining);
        log_(line);
      }
      const uint32_t slice =
          remaining < kNfcLivenessPollSliceMs ? remaining
                                              : kNfcLivenessPollSliceMs;
      delay(slice);
      last_wait_ms_ += slice;
    }
    log_("gauge: the post-load window could NOT be confirmed spent -- the "
         "clock did not advance; no VCELL reading is taken (fail-closed)");
    return false;
  }
  uint32_t lastGaugeWaitMs() const { return last_wait_ms_; }
  uint32_t loadEpochEdgeMs() const { return load_epoch_.edgeMs(); }
  uint32_t loadEpochEdges() const { return load_epoch_.edges(); }
  uint32_t loadEpochAdmissions() const { return load_epoch_.admissions(); }

  bool gaugeConversionIsPostLoad() const {
    return load_epoch_.conversionIsPostLoad(millis());
  }
  const char *pendingLoadEdge() const { return load_epoch_.what(); }
  bool loadEpochArmed() const { return load_epoch_.armed(); }

  // D-784 / Round-5: HIBRT=0 is configuration, not proof of the present mode.
  // A first-rail request may requalify the gauge while the accessory tree is
  // completely off; once any rail is active, loss of gauge readiness is
  // fail-closed and may not be hidden behind a blocking reconfiguration.
  bool accessoryBatteryAllows(bool other_rail_on, float *volts = nullptr,
                              float *floor = nullptr) {
    // D-793 / R12-03.  NO ACCESSORY POWER WHILE THE RADIO STATE IS UNKNOWN.
    //
    // The pessimistic mode set below already makes every sub-GHz row of the
    // permission table refuse, but that makes a SAFETY property depend on the
    // NUMBERS in a generated table.  Round-12 asks for the permission itself
    // to be refused, so it is refused HERE, by name, and the table refusal is
    // the second line of defence rather than the only one.
    if (!radios_quiesced_) {
      log_("ACCESSORY REFUSED: the physical transmit state of U7/U8 is "
           "UNKNOWN after this reset and has not been quiesced; a retained "
           "transmit is a load this permission cannot account for");
      if (volts) *volts = 0.0f;
      if (floor) *floor = kAccessoryNotPermittedV;
      return false;
    }
    // D-794 / R13-03.  THE SAME SENTENCE, FOR THE THIRD RADIO.
    //
    // D-793 argued that a retained NFC field needed no refusal because it is
    // carried in the canonical ledger as a bounded-duty allowance inside the
    // ALWAYS-ON set.  That is true of the HEAT and false of the PERMISSION:
    // the duty allowance is 25 % of 100 mA, and a field a dead image left
    // KEYED is 100 mA continuously, which is four times what every floor in
    // the table was derived against.  R12-08 drew exactly that distinction
    // for the burst loads and D-793 did not apply it here.
    if (!nfc_field_confirmed_off_) {
      log_("ACCESSORY REFUSED: the physical field state of U9 (ST25R3916) is "
           "UNKNOWN after this reset and has not been quiesced; a retained "
           "field draws continuously where the ledger charges a bounded duty, "
           "so this permission cannot account for it");
      if (volts) *volts = 0.0f;
      if (floor) *floor = kAccessoryNotPermittedV;
      return false;
    }
    if (!gauge_.activeReady()) {
      if (acc3v3_ || acc5v_ || expanders_.safeShutdownPending() ||
          !configureFuelGaugeActiveMode()) {
        if (volts) *volts = 0.0f;
        if (floor) {
          *floor = accessoryEnableFloor(accessoryLoadState(),
                                        other_rail_on ? 2 : 1);
        }
        return false;
      }
    }
    // D-795 / R14-01: the enable edge is an ADMISSION, and it reads only
    // after a full window since the request -- see
    // `readFuelCellVoltageForAdmission`.
    const bool read = readFuelCellVoltageForAdmission("accessory rail");
    const float v = last_admission_vcell_;
    // D-792 / R11-04: the floor is a TABLE lookup on the observable mode set
    // and the rail count, not a scalar that cannot see what else is on.
    const AccessoryLoadState modes = accessoryLoadState();
    const float required = accessoryEnableFloor(modes, other_rail_on ? 2 : 1);
    if (volts) *volts = v;
    if (floor) *floor = required;
    return accessoryEnableAllowed(read, v, other_rail_on, modes);
  }

  // -------------------------------------------------------------------------
  // D-782.  ONE PLACE RECONCILES SOFTWARE FLAGS WITH THE EXPANDER LATCH.
  void afterAccessoryChange() {
    (void)reconcileAccessoryFlags(expanders_, &acc3v3_, &acc5v_,
                                  &accessory_i2c_);
  }

  void forceAccessoriesOff(const char *why) {
    const bool off5 = expanders_.setAccessory5v(bus_, false);
    const bool off3 = expanders_.setAccessory3v3(bus_, false);
    const bool offbuf = expanders_.setAccessoryI2cBuffer(bus_, false);
    if (off5) acc5v_ = false;
    if (off3) acc3v3_ = false;
    if (offbuf) accessory_i2c_ = false;
    afterAccessoryChange();
    // D-794 / R13-01: shedding is a load edge too.  Nothing here is admitted
    // on the strength of it, but the NEXT permission must not be granted on
    // an average that still contains the shed load.
    if (off5 || off3 || offbuf) noteMaterialLoadEdge("the accessory shed");
    // D-787 / R6-E06.  This line may NOT say the rails are off while the
    // hardware state is unknown: `off*` is the ACKNOWLEDGEMENT of each write,
    // and a NACKed write leaves the latch where it was.  The reconciled state
    // decides the wording.
    char line[176];
    const bool pending = expanders_.safeShutdownPending() ||
                         !expanders_.u2().outputShadowValid() ||
                         !expanders_.u3().outputShadowValid();
    snprintf(line, sizeof(line),
             "ACCESSORY FAIL-CLOSED: %s; off-writes acked 5V=%d 3V3=%d I2C=%d; "
             "hardware state %s",
             why, int(off5), int(off3), int(offbuf),
             pending ? "PENDING/UNKNOWN -- safe state NOT yet confirmed"
                     : "CONFIRMED off from the expander output latches");
    log_(line);
  }

  // The retention rule, in ONE place, so the periodic guard and D-779's
  // post-enable settled recheck cannot drift apart.
  void applyAccessoryRetention(const char *ctx) {
    if (!acc3v3_ && !acc5v_) return;
    float vcell = 0.0f;
    const bool read = readFuelCellVoltage(&vcell);
    const AccessoryBatteryAction action =
        accessoryRetentionAction(read, vcell, acc3v3_, acc5v_);
    if (action == AccessoryBatteryAction::ShedAll) {
      char why[160];
      if (!read) {
        snprintf(why, sizeof(why),
                 "%s: MAX17048 VCELL unreadable; accessory load not permitted",
                 ctx);
      } else if (!vcellIsPlausible(vcell)) {
        // D-779: an implausible reading is NOT a low battery, and saying so
        // keeps a stuck bus from being diagnosed as a flat pack.
        snprintf(why, sizeof(why),
                 "%s: VCELL %.3f V outside the plausible %.2f-%.2f V band; "
                 "treated as no measurement",
                 ctx, double(vcell), double(kVcellPlausibleMinV),
                 double(kVcellPlausibleMaxV));
      } else {
        // D-791 / D790-A03: RETENTION is judged at the retention floor.  The
        // single/dual constants are ENABLE floors and anticipate a load step
        // that, for a rail already on, has already happened.
        snprintf(why, sizeof(why),
                 "%s: VCELL %.3f V below %.2f V retention floor",
                 ctx, double(vcell), double(kAccessoryRetentionFloorV));
      }
      forceAccessoriesOff(why);
    } else if (action == AccessoryBatteryAction::Shed5v) {
      const bool off5 = expanders_.setAccessory5v(bus_, false);
      if (off5) acc5v_ = false;
      afterAccessoryChange();
      if (off5) noteMaterialLoadEdge("the ACC_5V_SW shed");
      if (off5) {
        char line[160];
        snprintf(line, sizeof(line),
                 "ACC_5V_SW SHED (%s): VCELL %.3f V below %.2f V retention "
                 "floor; the 3.3 V rail keeps its full published budget",
                 ctx, double(vcell),
                 double(kAccessoryRetentionFloorV));
        log_(line);
      } else {
        forceAccessoriesOff("5 V dual-rail battery shed failed");
      }
    }
  }

  // D-779.  THE PERMISSION WAS TAKEN BEFORE THE LOAD EXISTED: re-read once the
  // step has settled and apply the ordinary retention rule to the result.
  //
  // D-796 / C-NFC-QUIESCE-01: the electrical settle keeps the liveness
  // schedule -- a rail was granted a moment ago, so this is exactly the state
  // in which a lost U9 has something to shed.
  void settledAccessoryRecheck(const char *what) {
    waitServicingNfcLiveness(kAccessorySettledRecheckMs);
    applyAccessoryRetention(what);
    last_battery_guard_ms_ = millis();
  }

  bool blockingDemoTestAllowed(const char *what) {
    afterAccessoryChange();
    if (expanders_.safeShutdownPending() || acc3v3_ || acc5v_) {
      char line[160];
      snprintf(line, sizeof(line),
               "%s REFUSED: turn both accessory rails off and wait for a "
               "confirmed safe state first", what);
      log_(line);
      return false;
    }
    return true;
  }

  // D-788 / R7-D787-09.  ONE LINE, THREE DIFFERENT FACTS: the REQUEST, the
  // ACKNOWLEDGEMENT, and the state after reconciliation.  D788-06's mutant
  // printed `want` in the third field; the host test refuses that.
  void reportAccessoryCommand(const char *rail, bool want, bool acked,
                              bool retained) {
    const bool uncertain = expanders_.safeShutdownPending() ||
                           !expanders_.u2().outputShadowValid() ||
                           !expanders_.u3().outputShadowValid();
    const char *state = uncertain ? "UNKNOWN (pending safe reconciliation)"
                                  : (retained ? "ON" : "OFF");
    char line[176];
    snprintf(line, sizeof(line),
             "%s requested %s, acknowledged %s, state after reconciliation %s",
             rail, want ? "on" : "off", acked ? "yes" : "no", state);
    log_(line);
  }

  // -------------------------------------------------------------------------
  // D788-06.  THE RESET-RELEASE DIAGNOSTIC, EXECUTED.
  ResetReleaseReport releaseExpanderResetLines() {
    ResetReleaseReport out;
    if (!expanders_.ready()) {
      log_("reset-line release: expanders were not safely initialised; "
           "resets remain asserted");
      out.verdict = ResetRelease::Failed;
      return out;
    }
    // D-788 / R7-D787-08.  EVERY ONE OF THESE RETURN VALUES USED TO BE
    // DISCARDED AND THE LINE BELOW PRINTED `released` UNCONDITIONALLY.
    bool writes_ok = expanders_.holdNfcBoostOff(bus_);
    writes_ok = expanders_.setDisplayReset(bus_, true) && writes_ok;
    writes_ok = expanders_.setTouchReset(bus_, true) && writes_ok;
    writes_ok = expanders_.setLoraReset(bus_, true) && writes_ok;
    delay(10);
    writes_ok = expanders_.setDisplayReset(bus_, false) && writes_ok;
    writes_ok = expanders_.setTouchReset(bus_, false) && writes_ok;
    delay(5);
    writes_ok = expanders_.setLoraReset(bus_, false) && writes_ok;
    delay(10);

    const bool shadow_known = expanders_.u2().outputShadowValid();
    const uint16_t latch = expanders_.u2().outputShadow();
    const bool released =
        shadow_known &&
        Pcal9535a::bitOf(latch, AQROOT_U2_DISP_RST_N) &&
        Pcal9535a::bitOf(latch, AQROOT_U2_TOUCH_RST_N) &&
        Pcal9535a::bitOf(latch, AQROOT_U2_SX1262_RST_N);
    out.writes_acked = writes_ok;
    out.shadow_known = shadow_known;
    out.latch = latch;
    char line[176];
    if (writes_ok && released) {
      out.verdict = ResetRelease::Confirmed;
      snprintf(line, sizeof(line),
               "reset lines released (U2 P00/P01/P04): CONFIRMED from U2 "
               "output latch 0x%04X", unsigned(latch));
    } else if (!shadow_known) {
      out.verdict = ResetRelease::Unknown;
      snprintf(line, sizeof(line),
               "reset lines released (U2 P00/P01/P04): UNKNOWN -- a reset "
               "write failed and U2's output shadow is invalid; resets may "
               "still be asserted");
    } else {
      out.verdict = ResetRelease::Failed;
      snprintf(line, sizeof(line),
               "reset lines released (U2 P00/P01/P04): FAILED -- U2 output "
               "latch 0x%04X does not show all three released", unsigned(latch));
    }
    log_(line);
    return out;
  }

  // -------------------------------------------------------------------------
  // D-790 / D789-A09.  A NON-ACCESSORY COMMAND THAT NACKED USED TO BE FORGOTTEN.
  //
  // Round-9 found the hole the accessory reconciliation left open.  Two
  // commands in the bring-up console are NOT accessory-power commands and had
  // their return values DISCARDED by `demo/main.cpp`:
  //
  //   * the amplifier is taken OUT of shutdown to play a tone and put BACK in
  //     afterwards.  If that second write NACKs, the amplifier is physically
  //     still enabled, and nothing ever notices;
  //   * the display test asserts and then RELEASES `DISP_RST_N`.  If the
  //     release NACKs, the panel is held in reset while the console prints
  //     that the display is up.
  //
  // The generic expander recovery cannot fix either one.  It restores the
  // BOOT-SAFE latch, which is the right thing for safety and the wrong thing
  // for INTENT: boot-safe leaves the amplifier off (which happens to match the
  // amplifier intent) and the reset lines ASSERTED (which is the opposite of
  // the display intent).  Recovery reconstructs a SAFE STATE, never a WANTED
  // operation, and D789-A09 is right that the two are different questions.
  //
  // So the intent is TRACKED.  Each of these commands records what it wanted,
  // writes it, and CONFIRMS it from the physical output shadow.  A write that
  // did not land leaves a PENDING intent that `serviceDeferredCommands()`
  // retries from the main loop until it is confirmed, and the caller is told
  // -- `displayIsUp()` is false while a reset release is outstanding, so no
  // console line may claim the panel is up.  Nothing unrelated is touched:
  // each retry writes ONE bit, not a blanket latch.
  struct CommandIntent {
    bool pending = false;
    bool want = false;
    uint32_t attempts = 0;
  };

  // Take the amplifier out of shutdown, or put it back.  `on == false` is the
  // safety-relevant direction and is the one that must never be lost.
  bool setAmplifierIntent(bool on) {
    // D-792 / R11-04.  THE MODE EDGE.  Energising the amplifier while an
    // accessory rail is live is the same transition as enabling the rail,
    // walked in the other order, and it is judged by the same rule against the
    // mode set that will exist AFTERWARDS.  Only the ON direction is gated:
    // turning the amplifier OFF can never make a state worse and must never be
    // refusable.
    if (on) {
      AccessoryLoadState after = accessoryLoadState();
      after.amplifier_on = true;
      if (!modeEntryAllowed(after, "AMP_SD_MODE enable")) return false;
    }
    amp_intent_.want = on;
    const bool acked = expanders_.setAmplifier(bus_, on);
    const bool confirmed = acked && amplifierConfirmed(on);
    amp_intent_.pending = !confirmed;
    ++amp_intent_.attempts;
    // D-794 / R13-01: the amplifier at its capped level is one of the three
    // modes the permission table is indexed by, so energising or quieting it
    // is a material load edge.  The epoch is stamped on the ACK rather than
    // on the confirmation, deliberately: a write that landed and could not be
    // read back has still changed the load.
    if (acked) {
      noteMaterialLoadEdge(on ? "the amplifier being energised"
                              : "the amplifier being quieted");
    }
    char line[168];
    snprintf(line, sizeof(line),
             "AMP_SD_MODE requested %s, acknowledged %s, state after "
             "reconciliation %s",
             on ? "on" : "off", acked ? "yes" : "no",
             confirmed ? (on ? "ON" : "OFF")
                       : "UNKNOWN (retry pending; the amplifier may still be "
                         "energised)");
    log_(line);
    // D-791 / D790-A06.  AN ABORTED ENABLE MAY NOT LEAVE AN "ON" INTENT
    // BEHIND.  Round-10 reproduced it: the console tone command aborts when
    // this returns false, but the intent recorded here was still `want = on`,
    // so `serviceDeferredCommands()` would later drive AMP_SD_MODE HIGH from
    // the main loop -- energising the amplifier with no tone playing, no
    // operator action and no matching OFF anywhere.  A deferred retry is only
    // ever legitimate for the SAFE direction.  An unconfirmed ENABLE is
    // therefore CANCELLED here and REPLACED by an OFF intent, which is
    // attempted immediately and left pending if it too does not land.  This
    // covers every error exit of every caller, because no caller can observe
    // a false return without this having already run.
    if (on && !confirmed) {
      cancelAmplifierEnable();
    }
    return confirmed;
  }

  // Replace an unconfirmed ON intent with a CONFIRMED-or-PENDING OFF intent.
  // Writes one bit and never touches anything else.  Returns true when the
  // amplifier is confirmed OFF from U2's physical output shadow.
  bool cancelAmplifierEnable() {
    amp_intent_.want = false;
    const bool acked = expanders_.setAmplifier(bus_, false);
    const bool off = acked && amplifierConfirmed(false);
    amp_intent_.pending = !off;
    ++amp_intent_.attempts;
    log_(off ? "AMP_SD_MODE enable ABORTED: ON intent CANCELLED and the "
               "amplifier is CONFIRMED OFF"
             : "AMP_SD_MODE enable ABORTED: ON intent CANCELLED; the OFF "
               "write did not land, OFF retry pending and the amplifier may "
               "still be energised");
    return off;
  }

  // Pulse DISP_RST_N and RELEASE it.  The release is the intent; an
  // unconfirmed release leaves `displayIsUp()` false.
  bool releaseDisplayResetIntent() {
    disp_reset_intent_.want = true;
    // D-791 / D790-A07.  A NEW RESET INVALIDATES THE PREVIOUS INITIALISATION.
    //
    // Round-10 reproduced it: `display_up_` survived a later DISP_RST_N pulse,
    // so a success -> reset -> NACKed release -> deferred release sequence
    // ended with `displayIsUp()` true again the instant the retry landed --
    // with no SPI init in between and a panel sitting in its power-on state.
    // A CONFIRMED RESET RELEASE IS NOT A CONFIRMED PANEL INITIALISATION.  The
    // moment this method asserts the reset the panel is definitively down, and
    // only `noteDisplayInitialised(true)` -- which the caller may only reach
    // after re-running the SPI init -- may put it back up.
    display_up_ = false;
    bool acked = expanders_.setDisplayReset(bus_, true);
    // D-795 / R14-01: a panel held in reset draws differently from a running
    // one; the assertion is a load edge in its own right.
    if (acked) noteMaterialLoadEdge("the display reset being asserted");
    delay(20);
    acked = expanders_.setDisplayReset(bus_, false) && acked;
    delay(20);
    const bool confirmed = acked && displayResetReleased();
    disp_reset_intent_.pending = !confirmed;
    ++disp_reset_intent_.attempts;
    if (!confirmed) {
      log_("DISP_RST_N release NOT CONFIRMED: the panel may still be held in "
           "reset; retry pending and the display is NOT reported up");
    }
    return confirmed;
  }

  // D-791 / D790-A07.  A CONFIRMED RELEASE WITH NO INITIALISATION BEHIND IT.
  //
  // True when a display reset was asked for, the release is now confirmed, and
  // no SPI/display initialisation has run since that reset.  `demo/main.cpp`'s
  // `loop()` reads this and completes the bring-up the operator asked for --
  // which is the only way a DEFERRED release can ever reach a panel that is
  // actually initialised, and the only way the flag may go back up.
  bool displayInitOwed() const {
    return disp_reset_intent_.want && !disp_reset_intent_.pending
        && !display_up_ && expanders_.ready();
  }

  // Retried from the main loop.  Writes ONE bit per outstanding intent and
  // never touches anything else.  Returns true when an intent was confirmed
  // by this call.
  bool serviceDeferredCommands() {
    if (!expanders_.ready()) return false;
    if (!amp_intent_.pending && !disp_reset_intent_.pending) return false;
    // A NACKed write INVALIDATES the output shadow -- `Pcal9535a::writeOutputs`
    // does that deliberately, and `writeBit` then refuses rather than guessing
    // the other fifteen bits.  So a retry has to re-establish the shadow from
    // the part FIRST, or it can never land.  This reads; it writes nothing.
    if (!expanders_.u2().outputShadowValid()
        && !expanders_.u2().syncOutputShadow(bus_)) {
      return false;
    }
    bool progressed = false;
    if (amp_intent_.pending) {
      ++amp_intent_.attempts;
      if (expanders_.setAmplifier(bus_, amp_intent_.want)
          && amplifierConfirmed(amp_intent_.want)) {
        amp_intent_.pending = false;
        progressed = true;
        log_("AMP_SD_MODE intent CONFIRMED on retry");
      }
    }
    if (disp_reset_intent_.pending) {
      ++disp_reset_intent_.attempts;
      if (expanders_.setDisplayReset(bus_, false) && displayResetReleased()) {
        disp_reset_intent_.pending = false;
        progressed = true;
        log_("DISP_RST_N release CONFIRMED on retry");
      }
    }
    return progressed;
  }

  bool amplifierIntentPending() const { return amp_intent_.pending; }
  bool displayResetIntentPending() const { return disp_reset_intent_.pending; }
  bool amplifierConfirmed(bool on) const {
    return expanders_.u2().outputShadowValid()
        && Pcal9535a::bitOf(expanders_.u2().outputShadow(),
                            AQROOT_U2_AMP_SD_MODE) == on;
  }
  bool displayResetReleased() const {
    return expanders_.u2().outputShadowValid()
        && Pcal9535a::bitOf(expanders_.u2().outputShadow(),
                            AQROOT_U2_DISP_RST_N);
  }
  // The ONE fact `demo/main.cpp` is allowed to print about the panel.
  //
  // D-791 / D790-A07: the `!pending` term is now DEFENCE IN DEPTH rather than
  // the load-bearing guard it was at D-790.  `display_up_` is cleared the
  // moment `releaseDisplayResetIntent()` asserts the reset and again by
  // `serviceExpanderRecovery()`, so no reachable state has `display_up_` true
  // with a release outstanding.  The term is kept because a future edit could
  // reintroduce one; `firmware_hw_map_contract` records that mutating it alone
  // is now an EQUIVALENT mutant rather than leaving a vacuous control passing.
  bool displayIsUp() const { return display_up_ && !disp_reset_intent_.pending; }
  // D-794 / R13-01.  THE EDGE ASTRA'S REPRODUCTION WALKS THROUGH.
  //
  // The `p` key resets the panel and runs the ILI9488 initialisation, and
  // that is the largest load step this image makes: a 3.5 in panel's own
  // analog and logic supply plus whatever the backlight is left at.  The
  // gauge's four-conversion average still describes the board as it was
  // before the panel came up, and `5` pressed next is admitted on it.
  //
  // This is where the panel load becomes REAL to the rest of the image, so
  // this is where the epoch is stamped.  It is stamped for BOTH directions
  // -- a panel going down is as material as one coming up, and the average is
  // equally wrong about it.
  void noteDisplayInitialised(bool up) {
    display_up_ = up;
    noteMaterialLoadEdge(up ? "the ILI9488 display initialisation"
                            : "the display going down");
  }

  // -------------------------------------------------------------------------
  // D788-06.  THE WARM-RESET RECOVERY RETRY, EXECUTED.
  //
  // Round-4 R4-03: an MCU reset must not turn one failed safe-latch write into
  // an indefinite energized rail.  Re-open/recover the bus and retry the
  // COMPLETE boot-safe expander initialisation until it is confirmed.  The
  // D788-06 mutants dropped `expanders_.begin()` from this path and forced the
  // subsequent reset release to report success; both are refused by the host
  // test's physical-latch model, which only clears the unsafe latch when the
  // real initialisation runs.
  //
  // Returns true when this call RECOVERED the expanders.
  bool serviceExpanderRecovery() {
    if (expanders_.ready()) return false;
    const uint32_t now = millis();
    if (recovery_started_ && now - last_recovery_ms_ < kExpanderRecoveryPeriodMs) {
      return false;
    }
    recovery_started_ = true;
    last_recovery_ms_ = now;
    const bool bus_open = bus_.reopen(AQROOT_I2C_BRINGUP_HZ);
    const bool recovered = bus_open && expanders_.begin(bus_);
    if (!recovered) return false;
    afterAccessoryChange();
    (void)releaseExpanderResetLines();
    bus_.setClock(AQROOT_I2C_RUN_HZ);
    (void)configureFuelGaugeActiveMode();
    // D-790 / D789-A09.  Recovery rebuilt a SAFE state, not a WANTED one.  The
    // boot-safe latch re-asserts DISP_RST_N and leaves the amplifier off, so
    // any outstanding intent is now definitively unsatisfied and must be
    // re-applied rather than assumed to have survived.  The display is no
    // longer up, whatever the caller last thought.
    display_up_ = false;
    // D-795 / R14-01: recovery rewrote the boot-safe latch -- every enable
    // off, every reset asserted and released -- which is as material a load
    // edge as this image makes.
    noteMaterialLoadEdge("the expander recovery");
    // D-793 / R12-03.  RECOVERY RE-ASSERTS AND RE-RELEASES U2.P01, WHICH IS
    // THE SX1262's RESET, SO THE RADIO STATE THIS OBJECT BELIEVED IS NO
    // LONGER PROVEN.  Invalidating it here is the liveness half of the rule:
    // `loop()` re-quiesces and only a CONFIRMED quiesce re-permits.
    radios_quiesced_ = false;
    if (disp_reset_intent_.want) disp_reset_intent_.pending = true;
    if (amp_intent_.pending || amp_intent_.want) {
      amp_intent_.pending = !amplifierConfirmed(amp_intent_.want);
    }
    (void)serviceDeferredCommands();
    log_("I2C/expander safety state RECOVERED after incomplete boot");
    return true;
  }

  // Liveness only: no rail is energized until qualification and the subsequent
  // VCELL permission both succeed.
  bool backgroundGaugeRequalification() {
    if (gauge_.activeReady() || acc3v3_ || acc5v_ ||
        expanders_.safeShutdownPending()) {
      return false;
    }
    const uint32_t now = millis();
    if (requal_started_ && now - last_gauge_requal_ms_ < kGaugeRequalPeriodMs) {
      return false;
    }
    requal_started_ = true;
    last_gauge_requal_ms_ = now;
    return configureFuelGaugeActiveMode();
  }

  void periodicBatteryGuard() {
    if (!acc3v3_ && !acc5v_) return;
    const uint32_t now = millis();
    if (guard_started_ && now - last_battery_guard_ms_ < kBatteryGuardPeriodMs) {
      return;
    }
    guard_started_ = true;
    last_battery_guard_ms_ = now;
    applyAccessoryRetention("periodic");
  }

  // -------------------------------------------------------------------------
  // D788-05.  THE SERIAL DISPATCH, EXECUTED.
  //
  // `demo/main.cpp` forwards every accessory/backlight console key here and
  // owns no second copy.  The backlight key calls the SHIPPED `backlightRamp()`
  // -- the same symbol `test_production_timing.cpp` already runs -- so a
  // duplicate live implementation placed beside it is caught by the duty/timing
  // claims of `test_production_callers.cpp` rather than passing unseen.
  //
  // Returns true when the key was one of ours.
  bool handleAccessoryConsole(char key) {
    switch (key) {
      case '3': {
        const bool want = !acc3v3_;
        float vcell = 0.0f, floor = 0.0f;
        if (want && !accessoryBatteryAllows(acc5v_, &vcell, &floor)) {
          char line[136];
          snprintf(line, sizeof(line),
                   "ACC_3V3_SW REFUSED: VCELL %.3f V / floor %.2f V",
                   double(vcell), double(floor));
          log_(line);
          return true;
        }
        const bool ok = expanders_.setAccessory3v3(bus_, want);
        if (ok) acc3v3_ = want;
        afterAccessoryChange();
        // D-794 / R13-01: the rail itself is a material load edge, in both
        // directions.  The settled recheck below must be taken on a
        // conversion that is entirely post-step, not on an average that is
        // still three quarters pre-step.
        if (ok) noteMaterialLoadEdge("the ACC_3V3_SW step");
        if (ok && want) settledAccessoryRecheck("ACC_3V3_SW");
        reportAccessoryCommand("ACC_3V3_SW", want, ok, acc3v3_);
        return true;
      }
      case '5': {
        const bool want = !acc5v_;
        float vcell = 0.0f, floor = 0.0f;
        if (want && !accessoryBatteryAllows(acc3v3_, &vcell, &floor)) {
          char line[136];
          snprintf(line, sizeof(line),
                   "ACC_5V_SW REFUSED: VCELL %.3f V / floor %.2f V",
                   double(vcell), double(floor));
          log_(line);
          return true;
        }
        // Boost first, switch second, and the reverse on the way down.  Both
        // disconnects are required by D-186 and neither is optional.
        const bool ok = expanders_.setAccessory5v(bus_, want);
        if (ok) acc5v_ = want;
        afterAccessoryChange();
        if (ok) noteMaterialLoadEdge("the ACC_5V_SW step");
        if (ok && want) settledAccessoryRecheck("ACC_5V_SW");
        reportAccessoryCommand("ACC_5V_SW", want, ok, acc5v_);
        return true;
      }
      case 'i': {
        const bool want = !accessory_i2c_;
        const bool ok = expanders_.setAccessoryI2cBuffer(bus_, want);
        if (ok) accessory_i2c_ = want;
        afterAccessoryChange();
        if (ok) noteMaterialLoadEdge("the accessory I2C buffer step");
        reportAccessoryCommand("ACC_PWR_EN", want, ok, accessory_i2c_);
        return true;
      }
      case 'l': {
        if (!blockingDemoTestAllowed("backlight ramp")) return true;
        log_("backlight ramp on GPIO46 (U17 TPS61169)");
        backlightRamp();
        // D-794 / R13-01: the backlight is the largest single +3V3 consumer
        // this image can switch, and the ramp ends by parking the duty.
        // Whatever it ends at, the gauge's average spans the whole ramp.
        noteMaterialLoadEdge("the backlight ramp");
        return true;
      }
      default:
        return false;
    }
  }

 private:
  Bus &bus_;
  DemoExpanders &expanders_;
  Max17048Guard &gauge_;
  Log log_;
  bool acc3v3_ = false;
  bool acc5v_ = false;
  bool accessory_i2c_ = false;
  CommandIntent amp_intent_;
  CommandIntent disp_reset_intent_;
  bool display_up_ = false;
  bool recovery_started_ = false;
  bool requal_started_ = false;
  bool guard_started_ = false;
  // D-792 / R11-04: the two high-load modes this class does not own the latch
  // for.  `subghz_tx_` is driven by `SpiBusB` through `AccessoryLoadAuthority`;
  // `wifi_tx_` by whatever brings the radio up.
  bool subghz_tx_ = false;
  bool wifi_tx_ = false;
  // D-793 / R12-03: FALSE until a confirmed quiesce.  The reset value is the
  // pessimistic one deliberately.
  bool radios_quiesced_ = false;
  // D-794 / R13-03: the same pessimism for the NFC front end, which D-793
  // left as "unknown but bounded" on a premise about the archive that was
  // not true.
  bool nfc_field_confirmed_off_ = false;
  uint8_t nfc_operation_control_ = 0xFF;
  // D-795 / R14-02: the liveness schedule and how often it revoked.
  bool nfc_liveness_started_ = false;
  uint32_t last_nfc_liveness_ms_ = 0;
  uint32_t nfc_revocations_ = 0;
  // D-796 / D796-05 item 4 + D796-10: the attached hardware probe, how often
  // it has answered, and whether a field-owning session holds U9.
  NfcLivenessProbe nfc_probe_ = nullptr;
  uint32_t nfc_liveness_probes_ = 0;
  bool nfc_session_active_ = false;
  // D-793 / R12-08.
  BurstArbiter burst_;
  // D-794 / R13-01: when the board's load last changed materially.
  GaugeLoadEpoch load_epoch_;
  // D-795 / R14-01: the admission read and the label its epoch points at.
  float last_admission_vcell_ = 0.0f;
  char admission_label_[96] = "none";
  uint32_t last_wait_ms_ = 0;
  uint32_t last_recovery_ms_ = 0;
  uint32_t last_gauge_requal_ms_ = 0;
  uint32_t last_battery_guard_ms_ = 0;
};

}  // namespace aqroot
