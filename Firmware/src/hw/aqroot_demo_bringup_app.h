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
#include "max17048_guard.h"

namespace aqroot {

// How long the board waits after an accessory step before re-reading VCELL.
// D-779: the MAX17048 updates VCELL about every 250 ms in active mode, which
// the HIBRT write guarantees it is in; 400 ms covers one update with margin.
constexpr uint32_t kAccessorySettledRecheckMs = 400;
// The warm-reset recovery retry period and the background requalification
// period, both of which are LIVENESS requirements: a board that gave up would
// sit with an unknown latch state forever.
constexpr uint32_t kExpanderRecoveryPeriodMs = 250;
constexpr uint32_t kGaugeRequalPeriodMs = 1000;
constexpr uint32_t kBatteryGuardPeriodMs = 500;

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
class DemoBringupApp {
 public:
  DemoBringupApp(Bus &bus, DemoExpanders &expanders, Max17048Guard &gauge,
                 Log log)
      : bus_(bus), expanders_(expanders), gauge_(gauge), log_(log) {}

  bool acc3v3() const { return acc3v3_; }
  bool acc5v() const { return acc5v_; }
  bool accessoryI2c() const { return accessory_i2c_; }

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
    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);
  }

  bool readFuelCellVoltage(float *volts) {
    return gauge_.readVcell(bus_, volts);
  }

  // D-784 / Round-5: HIBRT=0 is configuration, not proof of the present mode.
  // A first-rail request may requalify the gauge while the accessory tree is
  // completely off; once any rail is active, loss of gauge readiness is
  // fail-closed and may not be hidden behind a blocking reconfiguration.
  bool accessoryBatteryAllows(bool other_rail_on, float *volts = nullptr,
                              float *floor = nullptr) {
    if (!gauge_.activeReady()) {
      if (acc3v3_ || acc5v_ || expanders_.safeShutdownPending() ||
          !configureFuelGaugeActiveMode()) {
        if (volts) *volts = 0.0f;
        if (floor) *floor = accessoryEnableFloor(other_rail_on);
        return false;
      }
    }
    float v = 0.0f;
    const bool read = readFuelCellVoltage(&v);
    const float required = accessoryEnableFloor(other_rail_on);
    if (volts) *volts = v;
    if (floor) *floor = required;
    return accessoryEnableAllowed(read, v, other_rail_on);
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
  void settledAccessoryRecheck(const char *what) {
    delay(kAccessorySettledRecheckMs);
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
    amp_intent_.want = on;
    const bool acked = expanders_.setAmplifier(bus_, on);
    const bool confirmed = acked && amplifierConfirmed(on);
    amp_intent_.pending = !confirmed;
    ++amp_intent_.attempts;
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
  void noteDisplayInitialised(bool up) { display_up_ = up; }

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
        if (ok && want) settledAccessoryRecheck("ACC_5V_SW");
        reportAccessoryCommand("ACC_5V_SW", want, ok, acc5v_);
        return true;
      }
      case 'i': {
        const bool want = !accessory_i2c_;
        const bool ok = expanders_.setAccessoryI2cBuffer(bus_, want);
        if (ok) accessory_i2c_ = want;
        afterAccessoryChange();
        reportAccessoryCommand("ACC_PWR_EN", want, ok, accessory_i2c_);
        return true;
      }
      case 'l': {
        if (!blockingDemoTestAllowed("backlight ramp")) return true;
        log_("backlight ramp on GPIO46 (U17 TPS61169)");
        backlightRamp();
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
  uint32_t last_recovery_ms_ = 0;
  uint32_t last_gauge_requal_ms_ = 0;
  uint32_t last_battery_guard_ms_ = 0;
};

}  // namespace aqroot
