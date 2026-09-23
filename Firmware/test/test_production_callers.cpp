// AQROOT Demo -- D-789 / D788-04 + D788-05 + D788-06.
//
// THIS TEST COMPILES AND RUNS THE PRODUCTION CALL SITES, NOT THE FUNCTIONS
// THEY CALL.
//
// D-788 closed Round-7 by making `backlightRamp()` and
// `configureFuelGaugeActiveModeOnHardware()` executable.  Round-8 then showed
// the same false green one level out: the CALLERS of those two, and the
// warm-reset/diagnostic call sites beside them, lived in `demo/main.cpp`,
// which no host test has ever compiled.  Astra's three counterexamples --
//
//   D788-04  an early return in the outer gauge caller leaves the tested
//            helper alive but dead and authorises VCELL with a 0 ms settle;
//   D788-05  a complete duplicate backlight implementation with a no-op
//            microsecond hold, placed beside the tested one in the serial
//            dispatch;
//   D788-06  a warm-reset retry with `DemoExpanders::begin()` removed, a
//            reset-release diagnostic forced to report success, and an
//            accessory report that prints the WANTED state instead of the
//            RECONCILED one
//
// -- all passed the complete D-788 gate suite.  Every one of them is a FAIL
// here, because `DemoBringupApp` is constructed over a recording bus that
// carries a PHYSICAL LATCH model (an output register only changes when a write
// is actually ACKed) and a MAX17048 register model, and the real methods are
// driven.
//
//   g++ -std=c++17 -I ../src/hw -I . -I harness
//       -o /tmp/t test_production_callers.cpp && /tmp/t

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "harness/Arduino.h"

#include "aqroot_demo_bringup_app.h"

using namespace aqroot;

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

namespace {

// ---------------------------------------------------------------------------
// THE BOARD MODEL.  Two PCAL9535As whose output latches are PHYSICAL -- a
// NACKed write does not move them -- and one MAX17048 whose HIBRT, MODE and
// VCELL registers are real state.  Nothing here models a temperature, a
// voltage rail or a timing: it models only which transactions were ACCEPTED
// and what the parts hold as a result, which is exactly what the mutants
// Round-8 ran get wrong.
class BoardBus : public I2cBus {
 public:
  // PCAL9535A power-on default: every output latch 0xFF (NXP Rev. 2 tables
  // 7/8), which is the UNSAFE value for all six enables on this board.
  uint16_t u2_output = 0xFFFF;
  uint16_t u3_output = 0xFFFF;
  uint16_t u2_config = 0xFFFF;
  uint16_t u3_config = 0xFFFF;
  uint16_t u2_inputs = 0xFFFF;
  uint16_t u3_inputs = 0xFFFF;

  // MAX17048.
  uint16_t hibrt = 0xFFFF;
  uint16_t mode = 0x0000;          // HibStat clear = active
  uint16_t vcell_counts = 51200;   // 51200 x 78.125 uV = 4.000 V

  // Failure injection.
  int fail_address = -1;
  int fail_reg = -1;
  bool bus_down = false;           // every transaction NACKs
  int reopen_calls = 0;
  int set_clock_calls = 0;
  uint32_t last_clock_hz = 0;

  bool reopen(uint32_t hz) {
    ++reopen_calls;
    last_clock_hz = hz;
    return !bus_down;
  }
  void setClock(uint32_t hz) {
    ++set_clock_calls;
    last_clock_hz = hz;
  }

  bool shouldFail(uint8_t address, uint8_t reg) const {
    if (bus_down) return true;
    if (fail_address < 0 || int(address) != fail_address) return false;
    if (fail_reg >= 0 && int(reg) != fail_reg) return false;
    return true;
  }

  bool write(uint8_t address, const uint8_t *data, size_t length) override {
    const uint8_t reg = data[0];
    if (shouldFail(address, reg)) return false;
    uint16_t value = 0;
    if (length == 3) {
      value = uint16_t(data[1]) | uint16_t(uint16_t(data[2]) << 8);
    } else if (length == 2) {
      value = data[1];
    }
    if (address == AQROOT_EXP_U2_ADDR || address == AQROOT_EXP_U3_ADDR) {
      uint16_t &out = (address == AQROOT_EXP_U2_ADDR) ? u2_output : u3_output;
      uint16_t &cfg = (address == AQROOT_EXP_U2_ADDR) ? u2_config : u3_config;
      if (reg == Pcal9535a::kRegOutput0) out = value;
      else if (reg == Pcal9535a::kRegConfig0) cfg = value;
      return true;
    }
    if (address == AQROOT_I2C_ADDR_FUEL_GAUGE) {
      // The gauge's registers are MSB-first, unlike the PCAL's port pair.
      if (reg == Max17048Guard::kRegHibrt && length == 3) {
        hibrt = uint16_t(uint16_t(data[1]) << 8) | data[2];
      }
      return true;
    }
    return true;
  }

  bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                    size_t length) override {
    if (shouldFail(address, reg)) return false;
    if (address == AQROOT_EXP_U2_ADDR || address == AQROOT_EXP_U3_ADDR) {
      uint16_t value = 0;
      const bool u2 = (address == AQROOT_EXP_U2_ADDR);
      if (reg == Pcal9535a::kRegInput0) value = u2 ? u2_inputs : u3_inputs;
      else if (reg == Pcal9535a::kRegOutput0) value = u2 ? u2_output : u3_output;
      else if (reg == Pcal9535a::kRegConfig0) value = u2 ? u2_config : u3_config;
      for (size_t i = 0; i < length; ++i) data[i] = uint8_t(value >> (8 * i));
      return true;
    }
    if (address == AQROOT_I2C_ADDR_FUEL_GAUGE) {
      uint16_t value = 0;
      if (reg == Max17048Guard::kRegHibrt) value = hibrt;
      else if (reg == Max17048Guard::kRegMode) value = mode;
      else if (reg == Max17048Guard::kRegVcell) value = vcell_counts;
      for (size_t i = 0; i < length; ++i) {
        data[i] = uint8_t(value >> (8 * (length - 1 - i)));   // MSB first
      }
      return true;
    }
    for (size_t i = 0; i < length; ++i) data[i] = 0;
    return true;
  }

  bool probe(uint8_t) override { return !bus_down; }
};

std::vector<std::string> g_log;
void recordLine(const char *line) { g_log.emplace_back(line); }

bool logHas(const char *needle) {
  for (const auto &line : g_log) {
    if (line.find(needle) != std::string::npos) return true;
  }
  return false;
}

using App = DemoBringupApp<BoardBus, void (*)(const char *)>;

struct Rig {
  BoardBus bus;
  DemoExpanders expanders;
  Max17048Guard gauge{AQROOT_I2C_ADDR_FUEL_GAUGE};
  App app{bus, expanders, gauge, &recordLine};

  Rig() {
    g_log.clear();
    aqroot_hal::recorder().reset();
    // D-793 / R12-03.  These scenarios are about the GAUGE and the EXPANDER
    // callers, so they start from a board whose radios have been quiesced.
    // The refusal an UNQUIESCED board produces has its own claims at the end
    // of this file and its own real-image scenarios in
    // `test_production_image.cpp`.
    app.noteRadiosQuiesced(true);
    // D-794 / R13-03: and from one whose NFC field has been commanded off and
    // CONFIRMED off.  The refusal an unconfirmed field produces has its own
    // claims at the end of this file.
    app.noteNfcFieldQuiesced(true, 0x00);
  }
  bool bringUp() {
    const bool ok = expanders.begin(bus);
    app.afterAccessoryChange();
    return ok;
  }
};

}  // namespace

int main() {
  // =========================================================================
  // D788-04 -- THE OUTER GAUGE CALLER.
  // =========================================================================
  {
    Rig r;
    claim("D788-04 model: the expanders come up", r.bringUp());
    const uint64_t before = aqroot_hal::recorder().clock_us;
    const bool allowed = r.app.accessoryBatteryAllows(false);
    const uint64_t spent = aqroot_hal::recorder().clock_us - before;

    claim("a first accessory request on a 4.000 V pack is permitted", allowed);
    // THE CLAIM D788-04's EARLY-RETURN MUTANT BREAKS.  The permission may not
    // be granted without the production qualification having been executed,
    // and that qualification carries a >=300 ms settle.
    // D-795 / R14-01: the admission now also waits out a fresh post-request
    // window, which would hide a skipped settle inside `spent`.  The settle
    // is therefore measured up to the ADMISSION STAMP, which is taken only
    // once the qualification has returned.
    const uint64_t to_admission =
        uint64_t(r.app.loadEpochEdgeMs()) * 1000u - before;
    claim("the production permission path spends the full gauge settle "
          "BEFORE the admission request is stamped",
          to_admission >= uint64_t(kFuelGaugeActiveSettleMs) * 1000u
          && spent >= to_admission);
    claim("the production permission path left the gauge qualified",
          r.gauge.activeReady());
    claim("the production permission path wrote HIBRT = 0x0000",
          r.bus.hibrt == 0x0000);
  }
  {
    // A gauge still reporting MODE.HibStat cannot be qualified, so no
    // permission may be granted -- and none of the settle may be spent.
    Rig r;
    r.bringUp();
    r.bus.mode = Max17048Guard::kModeHibStatMask;
    const uint64_t before = aqroot_hal::recorder().clock_us;
    const bool allowed = r.app.accessoryBatteryAllows(false);
    claim("a hibernating gauge refuses the accessory permission", !allowed);
    claim("a refused qualification buys no settle time",
          aqroot_hal::recorder().clock_us == before);
  }
  {
    // D-784: once a rail is on, lost readiness is fail-closed and may NOT be
    // hidden behind a blocking reconfiguration attempt.
    Rig r;
    r.bringUp();
    claim("the 3.3 V rail can be enabled", r.app.handleAccessoryConsole('3'));
    claim("the 3.3 V rail is retained", r.app.acc3v3());
    r.gauge.invalidate();
    const uint64_t before = aqroot_hal::recorder().clock_us;
    const bool allowed = r.app.accessoryBatteryAllows(true);
    claim("with a rail already on, lost gauge readiness is fail-closed",
          !allowed);
    claim("and is not hidden behind a blocking requalification",
          aqroot_hal::recorder().clock_us == before);
  }
  {
    // The floors themselves, reached through the production caller.
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(3.82f / Max17048Guard::kVcellLsbV);
    claim("3.82 V permits a single rail", r.app.accessoryBatteryAllows(false));
    claim("3.82 V permits the second rail too, because the D-793 dual floor "
          "is the DERATED pair and not two full budgets",
          r.app.accessoryBatteryAllows(true));
    // D-792 / R11-04.  ASTRA'S REPRODUCED CASE, THROUGH THE PRODUCTION CALLER.
    // D-791's own `kAccessorySingleRailFloorV` was 3.55 V and the image granted
    // at it; the D-793 floor is 3.80 V and the caller has to refuse both it and
    // D-792's own 3.65 V.
    r.bus.vcell_counts = uint16_t(3.55f / Max17048Guard::kVcellLsbV);
    claim("R11-04: a reported 3.55 V no longer enables a rail",
          !r.app.accessoryBatteryAllows(false));
    r.bus.vcell_counts = uint16_t(3.65f / Max17048Guard::kVcellLsbV);
    claim("...and neither does D-792's own 3.65 V",
          !r.app.accessoryBatteryAllows(false));
    r.bus.vcell_counts = 0xFFFF;
    claim("the all-ones VCELL code is refused",
          !r.app.accessoryBatteryAllows(false));
  }
  // =========================================================================
  // D-792 / R11-04.  THE MODE EDGE, THROUGH THE PRODUCTION CALLERS.
  //
  // The permission table is indexed by the observable mode set, so the image
  // has to (a) report the mode set it is actually in, (b) refuse a MODE it
  // cannot afford while an accessory rail is live, and (c) refuse the rail once
  // the mode is on.  All three are driven here rather than asserted.
  // =========================================================================
  {
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    claim("with no rail on, the amplifier may be energised at 4.10 V",
          r.app.setAmplifierIntent(true));
    claim("...and the app now reports the amplifier as ON",
          r.app.accessoryLoadState().amplifier_on);
    claim("...and the 3.3 V rail is still permitted at 4.10 V with it on",
          r.app.accessoryBatteryAllows(false));
    claim("the amplifier goes back off", !r.app.setAmplifierIntent(false)
          || !r.app.accessoryLoadState().amplifier_on);
  }
  {
    // D-792 / R11-04.  AN UNKNOWN AMPLIFIER LATCH COUNTS AS ON.
    //
    // `amplifierConfirmed(true)` is false both when the amplifier is off and
    // when U2's output shadow is UNKNOWN -- the state a NACKed write leaves --
    // so reading the mode set through it would understate the load exactly when
    // the amplifier may already be energised.  The reading is
    // `!amplifierConfirmed(false)`, and this drives the difference.
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    claim("a healthy board reports the amplifier OFF",
          !r.app.accessoryLoadState().amplifier_on);
    claim("the 3.3 V rail goes on", r.app.handleAccessoryConsole('3'));
    claim("...and goes off again, so the amplifier write below is taken on a "
          "quiet board -- at D-793 every MODE edge with a rail live is "
          "refused, and a refusal that never reaches the bus cannot void a "
          "shadow",
          r.app.handleAccessoryConsole('3') && !r.app.acc3v3());
    r.bus.fail_address = AQROOT_EXP_U2_ADDR;
    (void)r.app.setAmplifierIntent(true);      // NACKs; U2's shadow is now void
    claim("a NACKed U2 write leaves the output shadow UNKNOWN",
          !r.expanders.u2().outputShadowValid());
    claim("...and an UNKNOWN amplifier latch counts as ON, not as OFF",
          r.app.accessoryLoadState().amplifier_on);
    r.bus.fail_address = -1;
    r.bus.vcell_counts = uint16_t(3.82f / Max17048Guard::kVcellLsbV);
    claim("...so a 3.82 V pack that would permit a quiet FIRST rail refuses "
          "it while the amplifier state is unknown, because the amplifier's "
          "own rail-edge floor is 3.85 V",
          !r.app.accessoryBatteryAllows(false));
    r.bus.vcell_counts = uint16_t(3.86f / Max17048Guard::kVcellLsbV);
    claim("...and 3.86 V, which clears that floor, permits it again",
          r.app.accessoryBatteryAllows(false));
  }
  {
    Rig r;
    r.bringUp();
    // 3.82 V is above the quiet single-rail floor (3.80 V); at D-793 EVERY
    // mode edge with a rail live is refused, so the rail may go on and no mode
    // may be entered -- on a full pack either.
    r.bus.vcell_counts = uint16_t(3.82f / Max17048Guard::kVcellLsbV);
    claim("the 3.3 V rail goes on at 3.82 V", r.app.handleAccessoryConsole('3'));
    claim("...and is retained", r.app.acc3v3());
    claim("the amplifier is REFUSED at 3.82 V with a rail live",
          !r.app.setAmplifierIntent(true));
    claim("...and the refusal leaves the amplifier OFF, not pending-on",
          !r.app.accessoryLoadState().amplifier_on);
    claim("...and says so", logHas("AMP_SD_MODE enable REFUSED"));
    claim("a sub-GHz transmit is REFUSED at 3.82 V with a rail live",
          !r.app.subGhzTransmitPermitted());
    claim("...and the app still reports no sub-GHz transmission",
          !r.app.subGhzTransmitting());
  }
  {
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    claim("the 3.3 V rail goes on at 4.10 V", r.app.handleAccessoryConsole('3'));
    // Wi-Fi + sub-GHz is one of the six combinations with NO attainable VCELL.
    r.app.noteWifiRadioActive(true);
    claim("with Wi-Fi active, sub-GHz is refused even on a nearly full pack",
          !r.app.subGhzTransmitPermitted());
    claim("...and the log says there is no attainable VCELL rather than "
          "quoting a floor",
          logHas("NO attainable VCELL"));
    claim("...and Wi-Fi ALONE now REFUSES an accessory rail outright, on a "
          "nearly full pack -- new at D-793 and it is the cost of the "
          "corrected source path",
          !r.app.accessoryBatteryAllows(true));
    r.bus.vcell_counts = uint16_t(3.82f / Max17048Guard::kVcellLsbV);
    claim("...so a 3.82 V pack that would permit a quiet rail refuses it with "
          "Wi-Fi active",
          !r.app.accessoryBatteryAllows(true));
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    r.app.noteWifiRadioActive(false);
    claim("with Wi-Fi off again and a rail live, sub-GHz is still refused at "
          "4.10 V, because its own mode edge is refused",
          !r.app.subGhzTransmitPermitted());
  }

  // =========================================================================
  // D788-05 -- THE BACKLIGHT SERIAL DISPATCH.
  // =========================================================================
  {
    Rig r;
    r.bringUp();
    aqroot_hal::recorder().reset();
    const bool handled = r.app.handleAccessoryConsole('l');
    const auto &rec = aqroot_hal::recorder();
    claim("the backlight console key is handled by the production dispatch",
          handled);
    claim("the production dispatch issues PWM commands", !rec.pwm.empty());
    // R7-D787-06, now proved THROUGH THE DISPATCH: a duplicate implementation
    // placed here cannot satisfy these without reimplementing the policy.
    claim("the dispatch's first PWM command is full duty at t=0",
          !rec.pwm.empty() && rec.pwm.front().duty == 255 &&
          rec.pwm.front().t_us == 0);
    uint64_t first_dim_us = UINT64_MAX;
    bool has_5 = false, has_250 = false;
    int full_duty_commands = 0;
    for (const auto &e : rec.pwm) {
      if (e.duty == 5) has_5 = true;
      if (e.duty == 250) has_250 = true;
      if (e.duty == 255) ++full_duty_commands;
      if (first_dim_us == UINT64_MAX && e.duty > 0 && e.duty < 255) {
        first_dim_us = e.t_us;
      }
    }
    claim("no dim PWM is issued before the full prime interval",
          first_dim_us >= kBacklightStartupPrimeUs && first_dim_us >= 3000);
    claim("the dispatch passes the policy's duties unmodified",
          has_5 && has_250 && full_duty_commands >= 2);
    claim("the dispatch parks the pin low and detaches",
          !rec.pwm.empty() && rec.pwm.back().duty == 0 && rec.detached &&
          rec.digital_writes_low >= 1);
    claim("the dispatch attaches the mapped backlight pin",
          rec.attached_pin == AQROOT_PIN_DISP_BL_PWM);
  }
  {
    // The blocking-test gate is part of the dispatch: a live accessory rail
    // refuses the ramp outright, so no PWM at all may be issued.
    Rig r;
    r.bringUp();
    r.app.handleAccessoryConsole('3');
    aqroot_hal::recorder().reset();
    g_log.clear();
    const bool handled = r.app.handleAccessoryConsole('l');
    claim("the backlight key is still consumed while a rail is on", handled);
    claim("...but issues no PWM at all",
          aqroot_hal::recorder().pwm.empty());
    claim("...and says why", logHas("REFUSED"));
  }

  // =========================================================================
  // D788-06 -- WARM RESET, RESET RELEASE, AND TRUTHFUL REPORTING.
  // =========================================================================
  {
    // The warm-reset retry must run the COMPLETE boot-safe initialisation.
    // The physical latch starts at the PCAL power-on 0xFFFF -- every enable
    // ASSERTED -- and only a real `DemoExpanders::begin()` clears it.
    Rig r;
    r.bus.bus_down = true;
    claim("a down bus does not bring the expanders up", !r.bringUp());
    claim("the expanders report themselves not ready", !r.expanders.ready());
    const uint16_t latch_before = r.bus.u3_output;
    claim("the U3 latch is still at the unsafe power-on default",
          latch_before == 0xFFFF);

    // Retry while the bus is still down: no recovery, and the latch may not
    // move.
    claim("the first retry does not recover a down bus",
          !r.app.serviceExpanderRecovery());
    claim("...and the unsafe latch is untouched", r.bus.u3_output == 0xFFFF);

    // The bus comes back.  The retry is rate-limited, so advance the clock.
    r.bus.bus_down = false;
    delay(kExpanderRecoveryPeriodMs);
    const bool recovered = r.app.serviceExpanderRecovery();
    claim("the retry recovers once the bus returns", recovered);
    claim("the retry reopened the bus", r.bus.reopen_calls >= 1);
    // THE CLAIM D788-06's `begin()`-dropping MUTANT BREAKS.  Recovery is not
    // a flag: the physical output latch must now hold the complete safe value.
    claim("the retry actually wrote the complete U3 safe latch",
          r.bus.u3_output == kU3SafeLatch);
    // U2's latch is then moved again by the reset release the recovery runs,
    // so the claim is on the bit that matters: the accessory I2C buffer enable
    // must be OFF, and the three resets must have been released.
    claim("the retry left U2's accessory buffer enable off",
          !Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_ACC_PWR_EN));
    claim("the retry released U2's three reset lines",
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_DISP_RST_N) &&
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_TOUCH_RST_N) &&
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_SX1262_RST_N));
    claim("the retry raised the bus to run speed",
          r.bus.set_clock_calls >= 1 && r.bus.last_clock_hz == AQROOT_I2C_RUN_HZ);
    claim("the retry requalified the fuel gauge", r.gauge.activeReady());
    claim("the retry said so on the console", logHas("RECOVERED"));
  }
  {
    // =======================================================================
    // FABLE / D-792.  RECOVERY REBUILDS A SAFE STATE, NOT A WANTED ONE, AND AN
    // OUTSTANDING AMPLIFIER INTENT HAS TO BE RE-APPLIED.
    //
    // Fable found a mutation that dropped the reconciliation at the end of
    // `serviceExpanderRecovery()`: the boot-safe latch turns AMP_SD_MODE off,
    // the intent still said `want = true, pending = false`, and
    // `serviceDeferredCommands()` therefore had nothing to do -- so the tone
    // silently failed until the operator typed the next command.  Nothing
    // proved the reconciliation ran.  This does.
    // =======================================================================
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    claim("the amplifier is energised and CONFIRMED",
          r.app.setAmplifierIntent(true));
    claim("...and U2's physical latch really holds it on",
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...with no intent outstanding", !r.app.amplifierIntentPending());

    // A bus fault takes the expanders down.  The PCAL9535As are NOT reset by
    // it, so the amplifier is still physically energised while the software
    // has no confirmed picture of the latch.
    r.bus.bus_down = true;
    claim("a down bus takes the expanders out of the ready state",
          !r.expanders.begin(r.bus) && !r.expanders.ready());
    r.bus.bus_down = false;
    delay(kExpanderRecoveryPeriodMs);
    claim("recovery runs once the bus returns",
          r.app.serviceExpanderRecovery());
    // THE CLAIM FABLE'S MUTANT BREAKS.  Recovery wrote the boot-safe latch,
    // which turns the amplifier OFF; the outstanding intent must have been
    // re-marked pending and re-applied within the same call.
    claim("recovery RE-APPLIED the outstanding amplifier intent",
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...and left nothing pending behind it",
          !r.app.amplifierIntentPending());
    claim("...and said so on the console",
          logHas("AMP_SD_MODE intent CONFIRMED on retry"));
  }
  {
    // ...and the SAFETY direction of the same reconciliation: an intent that
    // was left OFF-pending by a NACK must be retired by the recovery rather
    // than re-energising anything.
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = uint16_t(4.10f / Max17048Guard::kVcellLsbV);
    r.bus.fail_address = AQROOT_EXP_U2_ADDR;
    claim("an amplifier enable onto a NACKing U2 is not confirmed",
          !r.app.setAmplifierIntent(true));
    claim("...and leaves an OFF intent pending", r.app.amplifierIntentPending());
    r.bus.fail_address = -1;
    r.bus.bus_down = true;
    claim("the expanders go not-ready", !r.expanders.begin(r.bus));
    r.bus.bus_down = false;
    delay(kExpanderRecoveryPeriodMs);
    claim("recovery runs", r.app.serviceExpanderRecovery());
    claim("recovery left the amplifier OFF", 
          !Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...and retired the pending OFF intent",
          !r.app.amplifierIntentPending());
  }
  {
    // LIVENESS.  A board that gave up would sit with an unknown latch state
    // forever.  Repeated retries must eventually recover.
    Rig r;
    r.bus.bus_down = true;
    r.bringUp();
    int attempts = 0;
    bool recovered = false;
    for (int i = 0; i < 20 && !recovered; ++i) {
      if (i == 7) r.bus.bus_down = false;
      recovered = r.app.serviceExpanderRecovery();
      ++attempts;
      delay(kExpanderRecoveryPeriodMs);
    }
    claim("the warm-reset retry keeps trying until it succeeds", recovered);
    claim("...and did not succeed before the bus came back", attempts > 7);
  }
  {
    // The reset-release diagnostic may not report CONFIRMED when the device
    // did not take the writes.
    Rig r;
    r.bringUp();
    g_log.clear();
    const ResetReleaseReport good = r.app.releaseExpanderResetLines();
    claim("a healthy reset release is CONFIRMED", good.ok());
    claim("...from the U2 output latch", logHas("CONFIRMED from U2 output latch"));
    claim("the three reset lines are actually released in the latch",
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_DISP_RST_N) &&
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_TOUCH_RST_N) &&
          Pcal9535a::bitOf(r.bus.u2_output, AQROOT_U2_SX1262_RST_N));
  }
  {
    Rig r;
    r.bringUp();
    g_log.clear();
    // Every U2 output write now NACKs: the de-asserts never reach the part.
    r.bus.fail_address = AQROOT_EXP_U2_ADDR;
    r.bus.fail_reg = Pcal9535a::kRegOutput0;
    const ResetReleaseReport bad = r.app.releaseExpanderResetLines();
    // THE CLAIM D788-06's forced-success MUTANT BREAKS.
    claim("a NACKed reset release is NOT reported as confirmed", !bad.ok());
    claim("...and is reported as UNKNOWN rather than as a pass",
          bad.verdict == ResetRelease::Unknown && logHas("UNKNOWN"));
    claim("...and never claims the lines were released",
          !logHas("CONFIRMED from U2 output latch"));
  }
  {
    // D-788 / R7-D787-09 + D788-06: the console line must print the RECONCILED
    // state, not the requested one.
    Rig r;
    r.bringUp();
    r.app.handleAccessoryConsole('3');
    claim("the rail is on before the shed", r.app.acc3v3());
    g_log.clear();
    // A flat pack: the settled recheck inside the 5 V request will shed
    // everything, so the 5 V request is refused outright and the 3.3 V rail
    // is dropped by the periodic guard.
    r.bus.vcell_counts = uint16_t(3.20f / Max17048Guard::kVcellLsbV);
    r.app.periodicBatteryGuard();
    delay(kBatteryGuardPeriodMs);
    r.app.periodicBatteryGuard();
    claim("a 3.20 V pack sheds the accessory rail", !r.app.acc3v3());
    claim("...and says which floor it failed",
          logHas("below 3.20 V retention floor"));
    g_log.clear();
    // Ask for it again at the same voltage: refused, and the line says so.
    r.app.handleAccessoryConsole('3');
    claim("a refused request names VCELL and the floor",
          logHas("ACC_3V3_SW REFUSED"));
  }
  {
    // The three-fact accessory report: request, acknowledgement, reconciled.
    Rig r;
    r.bringUp();
    // U16 is powered FROM ACC_3V3_SW, so the buffer cannot be enabled until
    // that rail is up -- itself a production ordering rule this dispatch keeps.
    r.app.handleAccessoryConsole('3');
    claim("the buffer's own supply rail is up first", r.app.acc3v3());
    g_log.clear();
    r.app.handleAccessoryConsole('i');
    claim("an accepted buffer command reports request + ACK + reconciled state",
          logHas("ACC_PWR_EN requested on, acknowledged yes, state after "
                 "reconciliation ON"));
    // Now make the write fail.  The request is `on`, the ACK is `no`, and the
    // state after reconciliation may NOT be printed as `ON`.
    Rig r2;
    r2.bringUp();
    r2.app.handleAccessoryConsole('3');
    g_log.clear();
    r2.bus.fail_address = AQROOT_EXP_U2_ADDR;
    r2.bus.fail_reg = Pcal9535a::kRegOutput0;
    r2.app.handleAccessoryConsole('i');
    claim("a NACKed buffer command is reported as not acknowledged",
          logHas("acknowledged no"));
    // THE CLAIM D788-06's wanted-state MUTANT BREAKS.
    claim("...and its state is never printed as ON",
          !logHas("state after reconciliation ON"));
  }
  {
    // R6-E06: a fail-closed shutdown whose writes did not land may not say
    // the rails are off.
    Rig r;
    r.bringUp();
    r.app.handleAccessoryConsole('3');
    g_log.clear();
    r.bus.fail_address = AQROOT_EXP_U3_ADDR;
    r.bus.fail_reg = Pcal9535a::kRegOutput0;
    r.app.forceAccessoriesOff("host test");
    claim("a fail-closed shutdown whose writes NACKed does not claim success",
          !logHas("hardware state CONFIRMED"));
    claim("...it reports the hardware state as pending/unknown",
          logHas("PENDING/UNKNOWN"));
  }

  // =========================================================================
  // D-793 / R12-03.  AN UNQUIESCED RADIO REFUSES ACCESSORY POWER, BY NAME.
  // =========================================================================
  {
    // FIRST, THE DEFAULT.  `Rig` calls `noteRadiosQuiesced(true)` so the other
    // scenarios are about something else; the value a FRESHLY CONSTRUCTED app
    // holds is the one an MCU reset produces, and it must be the pessimistic
    // one.  A default of `true` is the mutation this claim exists to catch.
    BoardBus bus0;
    DemoExpanders expanders0;
    Max17048Guard gauge0{AQROOT_I2C_ADDR_FUEL_GAUGE};
    App fresh{bus0, expanders0, gauge0, &recordLine};
    claim("a FRESHLY CONSTRUCTED app has NOT quiesced the radios",
          !fresh.radiosQuiesced());
    claim("...and therefore reports sub-GHz TX as KEYED",
          fresh.accessoryLoadState().subghz_tx);
    claim("...and refuses to answer the bus's keying question",
          !fresh.radioPhysicalStateIsKnown());
  }
  {
    // AND A WARM-RESET RECOVERY INVALIDATES IT, because that path re-asserts
    // and re-releases U2.P01 -- the SX1262's reset -- so whatever this object
    // believed about the radios is no longer proven.
    Rig r;
    r.bus.bus_down = true;
    claim("R12-03 recovery model: a down bus does not bring the expanders up",
          !r.bringUp());
    r.app.noteRadiosQuiesced(true);
    claim("the rig starts from a confirmed quiesce", r.app.radiosQuiesced());
    r.bus.bus_down = false;
    aqroot_hal::recorder().clock_us += 1000ull * 1000ull;
    claim("the loop recovers them", r.app.serviceExpanderRecovery());
    claim("...and the radio state is INVALIDATED by the recovery, because "
          "U2.P01 is the SX1262's reset and it was just re-asserted",
          !r.app.radiosQuiesced());
    claim("...so accessory power is refused again until a fresh quiesce",
          !r.app.accessoryBatteryAllows(false));
  }
  {
    Rig r;
    r.app.noteRadiosQuiesced(false);
    claim("R12-03 model: the expanders come up", r.bringUp());
    claim("the mode set reads sub-GHz TX as KEYED while the physical state "
          "is unknown", r.app.accessoryLoadState().subghz_tx);
    claim("...even though nothing has called noteSubGhzTransmitting",
          !r.app.subGhzTransmitting());
    claim("the accessory permission is REFUSED",
          !r.app.accessoryBatteryAllows(false));
    claim("...by name, not by a floor comparison",
          logHas("ACCESSORY REFUSED: the physical transmit state"));
    claim("...and the console rail key does not energise the rail",
          r.app.handleAccessoryConsole('3') && !r.app.acc3v3());
    r.app.noteRadiosQuiesced(true);
    claim("a confirmed quiesce clears the pessimistic mode",
          !r.app.accessoryLoadState().subghz_tx);
    claim("...and the permission is asked properly again",
          r.app.accessoryBatteryAllows(false));
  }

  // =========================================================================
  // D-793 / R12-08.  THE BURST ARBITER SERIALISES, AND THE CALL SITE LOGS.
  // =========================================================================
  {
    Rig r;
    claim("R12-08 model: the expanders come up", r.bringUp());
    claim("a burst is allowed when nothing holds the arbiter",
          r.app.burstAllowed(BurstLoad::MicroSdWrite, "microSD test"));
    {
      BurstArbiter::Hold hold(r.app.burstArbiter(), BurstLoad::MicroSdWrite);
      claim("the hold is taken", hold.ok());
      claim("a SECOND bursty load is refused while the first holds",
            !r.app.burstAllowed(BurstLoad::NfcField, "NFC read"));
      claim("...and the refusal names the load that is holding",
            logHas("microSD write is already drawing its burst"));
      claim("the IR path is refused on the same rule",
            !r.app.burstAllowed(BurstLoad::IrTransmit, "IR test"));
      claim("a nested hold on the SAME load is refused, so an inner scope "
            "cannot release the outer one's slot",
            !BurstArbiter::Hold(r.app.burstArbiter(),
                                BurstLoad::MicroSdWrite).ok());
    }
    claim("the RAII scope released the arbiter",
          r.app.burstArbiter().active() == BurstLoad::None);
    claim("...and the next burst is allowed again",
          r.app.burstAllowed(BurstLoad::NfcField, "NFC read"));
    claim("BurstLoad::None is never a valid hold",
          !r.app.burstArbiter().begin(BurstLoad::None));
    claim("burstLoadName is not a stub",
          std::strcmp(burstLoadName(BurstLoad::NfcField), "NFC field") == 0
          && std::strcmp(burstLoadName(BurstLoad::IrTransmit),
                         "IR transmit") == 0
          && std::strcmp(burstLoadName(BurstLoad::MicroSdWrite),
                         "microSD write") == 0);
  }

  // =========================================================================
  // D-795 / R14-01.  EVERY STAMP SITE, ONE CLAIM EACH.
  //
  // ROUND-14: "Bind every material internal load edge ... Add host/hardware-
  // map mutation controls for EACH stamp site.  Removing amplifier/backlight/
  // rail/shed stamps must fail."
  //
  // `test_production_image.cpp` proves PHYSICALLY that no reading the image
  // acts on contains a pre-edge conversion.  For several sites that proof is
  // carried by the ADMISSION epoch as well -- a backlight ramp can only run
  // with both rails off, so the next VCELL reading is necessarily an
  // admission, which stamps its own request -- and removing the site's own
  // stamp would leave the physics green.  That is defence in depth, not a
  // licence to drop the stamp, so every site is ALSO claimed here directly:
  // after the operation, the epoch names that edge, and it was taken at the
  // moment the operation finished.
  // =========================================================================
  {
    auto stamped = [](Rig &r, const char *what) {
      return std::strcmp(r.app.pendingLoadEdge(), what) == 0
          && r.app.loadEpochEdgeMs() == millis();
    };
    auto edges_named = [](Rig &r, const char *what) {
      return std::strcmp(r.app.pendingLoadEdge(), what) == 0;
    };
    {
      Rig r;
      r.bringUp();
      r.bus.vcell_counts = 51200;              // 4.000 V
      claim("R14-01 stamp: the ACC_3V3_SW rail step (on)",
            r.app.handleAccessoryConsole('3') && r.app.acc3v3()
            && edges_named(r, "the ACC_3V3_SW step"));
      claim("R14-01 stamp: the accessory I2C buffer step",
            r.app.handleAccessoryConsole('i') && r.app.accessoryI2c()
            && stamped(r, "the accessory I2C buffer step"));
      (void)r.app.handleAccessoryConsole('i');
      claim("R14-01 stamp: the ACC_3V3_SW rail step (off)",
            r.app.handleAccessoryConsole('3') && !r.app.acc3v3()
            && stamped(r, "the ACC_3V3_SW step"));
      claim("R14-01 stamp: the ACC_5V_SW rail step (on)",
            r.app.handleAccessoryConsole('5') && r.app.acc5v()
            && edges_named(r, "the ACC_5V_SW step"));
      claim("R14-01 stamp: the ACC_5V_SW rail step (off)",
            r.app.handleAccessoryConsole('5') && !r.app.acc5v()
            && stamped(r, "the ACC_5V_SW step"));
    }
    {
      Rig r;
      r.bringUp();
      claim("R14-01 stamp: the backlight ramp",
            r.app.handleAccessoryConsole('l')
            && stamped(r, "the backlight ramp"));
      claim("R14-01 stamp: the amplifier being energised",
            r.app.setAmplifierIntent(true)
            && stamped(r, "the amplifier being energised"));
      claim("R14-01 stamp: the amplifier being quieted",
            r.app.setAmplifierIntent(false)
            && stamped(r, "the amplifier being quieted"));
      r.app.noteDisplayInitialised(true);
      claim("R14-01 stamp: the display initialisation",
            stamped(r, "the ILI9488 display initialisation"));
      r.app.noteDisplayInitialised(false);
      claim("R14-01 stamp: the display going down",
            stamped(r, "the display going down"));
      (void)r.app.releaseDisplayResetIntent();
      claim("R14-01 stamp: the display reset being asserted",
            edges_named(r, "the display reset being asserted"));
      r.app.noteRadiosQuiesced(true);
      claim("R14-01 stamp: the sub-GHz radio quiesce",
            stamped(r, "the sub-GHz radio quiesce"));
      r.app.noteNfcFieldQuiesced(true, 0x00);
      claim("R14-01 stamp: the NFC field quiesce",
            stamped(r, "the NFC field quiesce"));
      r.app.noteSubGhzTransmitting(true);
      claim("R14-01 stamp: sub-GHz TX keying", stamped(r, "sub-GHz TX keying"));
      r.app.noteSubGhzTransmitting(false);
      claim("R14-01 stamp: sub-GHz TX unkeying",
            stamped(r, "sub-GHz TX unkeying"));
      r.app.noteWifiRadioActive(true);
      claim("R14-01 stamp: the Wi-Fi/BLE radio starting",
            stamped(r, "the Wi-Fi/BLE radio starting"));
      r.app.noteWifiRadioActive(false);
      claim("R14-01 stamp: the Wi-Fi/BLE radio stopping",
            stamped(r, "the Wi-Fi/BLE radio stopping"));
    }
    {
      // The shed stamps.
      Rig r;
      r.bringUp();
      r.bus.vcell_counts = 51200;
      (void)r.app.handleAccessoryConsole('3');
      r.app.forceAccessoriesOff("a D-795 stamp claim");
      claim("R14-01 stamp: the accessory shed",
            stamped(r, "the accessory shed"));
      (void)r.app.handleAccessoryConsole('3');
      (void)r.app.handleAccessoryConsole('5');
      claim("both rails are live before the 5 V retention shed",
            r.app.acc3v3() && r.app.acc5v());
      r.bus.vcell_counts = uint16_t(3.15 / 78.125e-6);   // under retention
      r.app.applyAccessoryRetention("a D-795 stamp claim");
      claim("R14-01 stamp: the ACC_5V_SW shed",
            !r.app.acc5v() && edges_named(r, "the ACC_5V_SW shed"));
    }
    {
      // The admission stamps, and that they name the request.
      Rig r;
      r.bringUp();
      r.bus.vcell_counts = 51200;
      const uint32_t before = r.app.loadEpochAdmissions();
      const uint32_t pressed = millis();
      (void)r.app.accessoryBatteryAllows(false);
      const uint32_t stamp = r.app.loadEpochEdgeMs();
      claim("R14-01 stamp: a rail admission is its own epoch",
            r.app.loadEpochAdmissions() == before + 1 && stamp >= pressed
            && edges_named(r, "the accessory rail admission request"));
      claim("...and the admission read waited the full window after it",
            millis() - stamp >= kGaugePostLoadConversionMs);
      (void)r.app.handleAccessoryConsole('3');
      AccessoryLoadState after = r.app.accessoryLoadState();
      after.amplifier_on = true;
      const uint32_t asked = millis();
      (void)r.app.modeEntryAllowed(after, "AMP_SD_MODE enable");
      claim("R14-01 stamp: a mode entry with a rail live is its own epoch",
            r.app.loadEpochEdgeMs() == asked
            && edges_named(r, "the AMP_SD_MODE enable admission request"));
    }
    {
      // Recovery.
      Rig r;
      claim("R14-01 stamp model: the expanders start unready", !r.app.acc3v3());
      (void)r.app.serviceExpanderRecovery();
      claim("R14-01 stamp: the expander recovery",
            edges_named(r, "the expander recovery"));
    }
    {
      // The window itself.
      claim("R14-01: the post-load window is 1300 ms, five periods at tERR "
            "+3.5 % rounded up, and not D-794's nominal 1000 ms",
            kGaugePostLoadConversionMs == 1300
            && kGaugeD794NominalWindowMs == 1000
            && kGaugeWorstCaseWindowUs == 1293750u);
    }
  }

  // =========================================================================
  // D-795 / R14-02.  UNKNOWN OWNS THE SLOT, AND LIVENESS LOSS REVOKES.
  // =========================================================================
  {
    Rig r;
    r.bringUp();
    r.bus.vcell_counts = 51200;
    (void)r.app.handleAccessoryConsole('3');
    claim("R14-02 model: a rail is live under a confirmed-quiet U9",
          r.app.acc3v3() && r.app.nfcFieldConfirmedOff());
    claim("a liveness probe is due on a confirmed-quiet part",
          r.app.nfcLivenessDue());
    claim("...and is not due again within its period", !r.app.nfcLivenessDue());
    r.app.noteNfcLiveness(true, 0x2A);
    claim("a live answer keeps the confirmation", r.app.nfcFieldConfirmedOff());
    r.app.noteNfcLiveness(false, 0x00);
    claim("R14-02: a lost identity REVOKES the OFF confirmation",
          !r.app.nfcFieldConfirmedOff() && r.app.nfcRevocations() == 1);
    claim("...and sheds the rail granted under it", !r.app.acc3v3());
    claim("...and U9 takes the burst slot",
          r.app.burstArbiter().active() == BurstLoad::NfcField);
    r.app.burstArbiter().end(BurstLoad::NfcField);
    claim("...and even with the arbiter cleared a microSD burst is refused "
          "while the field is UNKNOWN",
          !r.app.burstAllowed(BurstLoad::MicroSdWrite, "microSD test")
          && logHas("U9 owns the burst slot"));
    claim("...and so is a rail",
          !r.app.accessoryBatteryAllows(false)
          && logHas("the physical field state of U9"));
    claim("no liveness probe is scheduled while UNKNOWN -- the quiesce retry "
          "owns recovery", !r.app.nfcLivenessDue());
  }

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
