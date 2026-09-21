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
        snprintf(why, sizeof(why),
                 "%s: VCELL %.3f V below %.2f V single-rail floor",
                 ctx, double(vcell), double(kAccessorySingleRailFloorV));
      }
      forceAccessoriesOff(why);
    } else if (action == AccessoryBatteryAction::Shed5v) {
      const bool off5 = expanders_.setAccessory5v(bus_, false);
      if (off5) acc5v_ = false;
      afterAccessoryChange();
      if (off5) {
        char line[160];
        snprintf(line, sizeof(line),
                 "ACC_5V_SW SHED (%s): VCELL %.3f V below %.2f V dual-rail "
                 "floor", ctx, double(vcell),
                 double(kAccessoryDualRailFloorV));
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
  bool recovery_started_ = false;
  bool requal_started_ = false;
  bool guard_started_ = false;
  uint32_t last_recovery_ms_ = 0;
  uint32_t last_gauge_requal_ms_ = 0;
  uint32_t last_battery_guard_ms_ = 0;
};

}  // namespace aqroot
