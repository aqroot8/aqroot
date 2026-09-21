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
    claim("the production permission path spends the full gauge settle",
          spent >= uint64_t(kFuelGaugeActiveSettleMs) * 1000u);
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
    r.bus.vcell_counts = uint16_t(3.60f / Max17048Guard::kVcellLsbV);
    claim("3.60 V permits a single rail", r.app.accessoryBatteryAllows(false));
    claim("3.60 V refuses the second rail", !r.app.accessoryBatteryAllows(true));
    r.bus.vcell_counts = 0xFFFF;
    claim("the all-ones VCELL code is refused",
          !r.app.accessoryBatteryAllows(false));
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

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
