// AQROOT Demo -- D-790 / D789-A04 (+ Fable V-01/V-02, D789-A09, D789-A10).
//
// THIS TEST COMPILES AND RUNS `src/demo/main.cpp` ITSELF.
//
// `test_production_callers.cpp` constructs `DemoBringupApp` and drives its
// methods.  Round-9 showed that is still one level in: Astra's five
// counterexamples all live in `demo/main.cpp` -- in `setup()`, in `loop()`
// and in the console `switch` -- and every one of them passed the complete
// D-789 gate suite because no host test had ever COMPILED that file:
//
//   1  `periodicBatteryGuard()` made unreachable in `loop()`;
//   2  cold boot bypassing the qualified settle with a direct
//      `configureActiveMode()` on the gauge;
//   3  a direct accessory enable in the console `switch`, with the proper
//      dispatch left in the file but dead;
//   4  the settled post-enable retention/recheck removed;
//   5  the reset-release diagnostic forced to report success.
//
// Plus Fable's two: V-01 an early return in `settledAccessoryRecheck`, and
// V-02 `backgroundGaugeRequalification` disabled or made a no-op.
//
// The image is linked against `test/image/`, a host Arduino core that records
// what the firmware DOES -- the console lines, the PWM commands, the pin
// writes and the passage of the time the image asks for -- over a BOARD MODEL
// with PHYSICAL PCAL9535A output latches and real MAX17048 registers.  A
// write that NACKs really does leave the latch where it was.
//
//   g++ -std=c++17 -DARDUINO=200 -I test/image -I src/hw
//       -o /tmp/t test/test_production_image.cpp src/demo/main.cpp
//       test/image/image_main.cpp && /tmp/t

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "Arduino.h"
#include "SPI.h"
#include "Wire.h"

#include "aqroot_demo_board.h"
#include "aqroot_demo_expanders.h"
#include "aqroot_demo_bringup_app.h"
#include "max17048_guard.h"
#include "pcal9535a.h"
#include "aqroot_demo_pins.h"

using namespace aqroot;

// The image's own entry points.
void setup();
void loop();

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

namespace {

// ---------------------------------------------------------------------------
// THE BOARD MODEL, behind the stubbed `Wire`.
class Board : public aqroot_hal::I2cModel {
 public:
  // PCAL9535A power-on default: every output latch 0xFF, which is the UNSAFE
  // value for all six enables on this board.
  uint16_t u2_output = 0xFFFF, u3_output = 0xFFFF;
  uint16_t u2_config = 0xFFFF, u3_config = 0xFFFF;
  uint16_t u2_inputs = 0xFFFF, u3_inputs = 0xFFFF;

  // MAX17048.
  uint16_t hibrt = 0xFFFF;
  uint16_t mode = 0x0000;          // HibStat and EnSleep clear = awake
  uint16_t config = 0x971C;        // RCOMP POR 0x97, ATHD POR 0x1C
  uint16_t vcell_counts = 51200;   // 4.000 V

  int gauge_writes = 0;            // how often the image re-qualifies
  bool sticky_ensleep = false;     // a part that will not leave sleep
  bool sticky_config_sleep = false;  // CONFIG.SLEEP that will not clear
  // A part that goes to sleep BETWEEN the two reads of the qualification --
  // which is a real mechanism: ADI 19-6171 Rev.7 says holding SDA and SCL low
  // for tSLEEP enters sleep with no register write at all.  Only the SECOND
  // MODE check can catch this, which is what makes it load-bearing.
  bool sleeps_after_hibrt_write = false;
  bool bus_down = false;
  int fail_address = -1;
  int fail_reg = -1;
  // D-790: reads and writes fail INDEPENDENTLY.  A part that NACKs a write
  // but still answers a read is the exact condition D789-A09 is about -- the
  // command did not land and the board can still SEE that it did not.
  bool fail_writes = true;
  bool fail_reads = true;

  bool shouldFail(uint8_t address, uint8_t reg, bool writing) const {
    if (bus_down) return true;
    if (fail_address < 0 || int(address) != fail_address) return false;
    if (fail_reg >= 0 && int(reg) != fail_reg) return false;
    return writing ? fail_writes : fail_reads;
  }

  bool asleep() const {
    return (mode & Max17048Guard::kModeEnSleepMask) != 0
        && (config & Max17048Guard::kConfigSleepMask) != 0;
  }

  bool write(uint8_t address, const uint8_t *data, size_t length) override {
    const uint8_t reg = data[0];
    if (shouldFail(address, reg, true)) return false;
    uint16_t value = 0;
    if (length == 3) value = uint16_t(data[1]) | uint16_t(uint16_t(data[2]) << 8);
    else if (length == 2) value = data[1];
    if (address == AQROOT_EXP_U2_ADDR || address == AQROOT_EXP_U3_ADDR) {
      uint16_t &out = (address == AQROOT_EXP_U2_ADDR) ? u2_output : u3_output;
      uint16_t &cfg = (address == AQROOT_EXP_U2_ADDR) ? u2_config : u3_config;
      if (reg == Pcal9535a::kRegOutput0) out = value;
      else if (reg == Pcal9535a::kRegConfig0) cfg = value;
      return true;
    }
    if (address == AQROOT_I2C_ADDR_FUEL_GAUGE) {
      // MSB-first, unlike the PCAL's port pair.
      const uint16_t msb_first =
          (length == 3) ? uint16_t(uint16_t(data[1]) << 8) | data[2] : 0;
      ++gauge_writes;
      if (reg == Max17048Guard::kRegHibrt) {
        hibrt = msb_first;
        if (sleeps_after_hibrt_write) {
          mode |= Max17048Guard::kModeEnSleepMask;
          config |= Max17048Guard::kConfigSleepMask;
        }
      } else if (reg == Max17048Guard::kRegMode) {
        // ADI 19-6171 Rev.7 Figure 8: HibStat is READ ONLY.  A MODE write
        // moves QuickStart and EnSleep and cannot clear hibernate status.
        mode = uint16_t((msb_first & ~Max17048Guard::kModeHibStatMask)
                        | (mode & Max17048Guard::kModeHibStatMask));
        if (sticky_ensleep) mode |= Max17048Guard::kModeEnSleepMask;
      }
      else if (reg == Max17048Guard::kRegConfig) {
        config = msb_first;
        if (sticky_config_sleep) config |= Max17048Guard::kConfigSleepMask;
      }
      return true;
    }
    return true;
  }

  bool readRegister(uint8_t address, uint8_t reg, uint8_t *data,
                    size_t length) override {
    if (shouldFail(address, reg, false)) return false;
    if (address == AQROOT_EXP_U2_ADDR || address == AQROOT_EXP_U3_ADDR) {
      const bool u2 = (address == AQROOT_EXP_U2_ADDR);
      uint16_t value = 0;
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
      else if (reg == Max17048Guard::kRegConfig) value = config;
      else if (reg == Max17048Guard::kRegVcell) {
        // A SLEEPING gauge stops converting, so VCELL is whatever it was --
        // the model returns the LAST value, which is the whole point: a stale
        // reading is indistinguishable from a fresh one by its value alone.
        value = vcell_counts;
      } else if (reg == 0x08) value = 0x0012;   // VERSION
      for (size_t i = 0; i < length; ++i) {
        data[i] = uint8_t(value >> (8 * (length - 1 - i)));   // MSB first
      }
      return true;
    }
    // The IMU and the touch controller answer with plausible ids.
    for (size_t i = 0; i < length; ++i) data[i] = (reg == 0x00) ? 0x24 : 0x01;
    return true;
  }

  bool probe(uint8_t address) override {
    if (bus_down) return false;
    if (fail_address >= 0 && int(address) == fail_address && fail_reg < 0) {
      return false;
    }
    return address == AQROOT_EXP_U2_ADDR || address == AQROOT_EXP_U3_ADDR
        || address == AQROOT_I2C_ADDR_FUEL_GAUGE
        || address == AQROOT_I2C_ADDR_IMU || address == AQROOT_I2C_ADDR_TOUCH;
  }
};

Board g_board;

// ===========================================================================
// D-793 / R12-03.  THE INDEPENDENTLY RETAINED CC1101.
//
// ROUND-12, IN ITS OWN WORDS: "Add real-image/real-driver host test with an
// independently retained CC1101 stub: keyed before MCU reset, retained
// through setup, then verify SRES/SIDLE/quiesce occurs before load authority
// and TX arbitration become permissive."
//
// The stub is constructed BEFORE `setup()` and is not owned by the image, so
// the image's construction -- which is what an MCU reset is -- cannot clear
// it.  It starts in TX, exactly as a radio keyed by the previous image would
// be, and it only leaves TX when it is actually STROBED.  `ignores_strobes`
// is the negative control: a part that does not quiesce must leave the image
// reporting UNKNOWN and refusing accessory power, not reporting success.
//
// Header byte on this part is {R/W, BURST, addr[5:0]}.  A write with BURST
// clear and addr 0x30 is SRES; 0x36 is SIDLE.  0xC0 | 0x35 is a burst READ of
// MARCSTATE, whose value is 0x13 in TX and 0x01 in IDLE.
class Cc1101Stub : public aqroot_hal::SpiModel {
 public:
  bool transmitting = true;          // RETAINED from before the MCU reset
  bool ignores_strobes = false;      // the negative control
  bool sx1262_answers_standby = true;
  int sidle_strobes = 0;
  int sres_strobes = 0;
  int marcstate_reads = 0;
  int marcstate_reads_before_quiesce = 0;
  int tx_permission_questions = 0;

  uint8_t transfer(uint8_t out) override {
    const auto &r = aqroot_hal::recorder();
    const bool cc = r.pin_low[AQROOT_PIN_CC1101_CS_N];
    const bool sx = r.pin_low[AQROOT_PIN_SX1262_CS_N];
    if (cc) return cc1101(out);
    if (sx) return sx1262(out);
    return 0x3F;                     // the NFC part answers with a plausible id
  }

 private:
  uint8_t cc1101(uint8_t out) {
    if (pending_marcstate_) {
      pending_marcstate_ = false;
      ++marcstate_reads;
      if (transmitting) ++marcstate_reads_before_quiesce;
      return transmitting ? 0x13 : 0x01;
    }
    if (out == 0x36) {                       // SIDLE
      ++sidle_strobes;
      if (!ignores_strobes) transmitting = false;
      return 0x00;
    }
    if (out == 0x30) {                       // SRES -- BURST CLEAR
      ++sres_strobes;
      if (!ignores_strobes) transmitting = false;
      return 0x00;
    }
    if (out == uint8_t(0xC0 | 0x35)) {       // burst read of MARCSTATE
      pending_marcstate_ = true;
      return 0x00;
    }
    if (out == uint8_t(0xC0 | 0x30)) {       // burst read of PARTNUM
      pending_partnum_ = true;
      return 0x00;
    }
    if (pending_partnum_) { pending_partnum_ = false; return 0x00; }
    if (out == uint8_t(0xC0 | 0x31)) { pending_version_ = true; return 0x00; }
    if (pending_version_) { pending_version_ = false; return 0x14; }
    return 0x00;
  }

  uint8_t sx1262(uint8_t out) {
    if (pending_status_) { pending_status_ = false; return sx_status_(); }
    if (out == 0xC0) { pending_status_ = true; return sx_status_(); }
    if (out == 0x80) { standby_ = true; return 0x00; }
    if (out == 0x1D) { pending_reg_ = 3; return 0x00; }
    if (pending_reg_ > 0) {
      --pending_reg_;
      if (pending_reg_ == 0) return 0x14;    // the sync-word MSB the probe wants
      return 0x00;
    }
    return 0x00;
  }

  uint8_t sx_status_() const {
    if (!sx1262_answers_standby || !standby_) return uint8_t(0x00 << 4);
    return uint8_t(0x02 << 4);               // STBY_RC
  }

  bool pending_marcstate_ = false;
  bool pending_partnum_ = false;
  bool pending_version_ = false;
  bool pending_status_ = false;
  bool standby_ = false;
  int pending_reg_ = 0;
};

Cc1101Stub *g_radio = nullptr;
// Every scenario gets a HEALTHY radio pair by default -- one that answers the
// quiesce -- because a board whose radios cannot be quiesced refuses accessory
// power by design, and the other scenarios are about something else.  D-793 /
// R12-03's own scenarios install their own stub over this one.
Cc1101Stub g_healthy_radio;

// Reset the image between scenarios.  `setup()` re-initialises every static
// the image owns that matters here, because the app object's flags are
// reconciled from the PHYSICAL latch on every `afterAccessoryChange()`.
void rig(const char *keys = "") {
  g_board = Board();
  aqroot_hal::recorder().reset();
  aqroot_hal::model() = &g_board;
  aqroot_hal::recorder().serial_in = keys;
  // A healthy board: the CC1101 has released SO and the SX1262 is not busy.
  aqroot_hal::recorder().pin_level[AQROOT_PIN_SPI_B_MISO] = LOW;
  aqroot_hal::recorder().pin_level[AQROOT_PIN_SX1262_BUSY] = LOW;
  g_healthy_radio = Cc1101Stub();
  g_radio = &g_healthy_radio;
  aqroot_hal::spiModel() = &g_healthy_radio;
}

// D-793 / R12-03.  Same rig, plus a radio that was ALREADY TRANSMITTING when
// the MCU reset.  The stub outlives `setup()` because it is not the image's.
void rigWithRetainedRadio(Cc1101Stub &radio, const char *keys = "") {
  rig(keys);
  g_radio = &radio;
  aqroot_hal::spiModel() = &radio;
}

void press(const char *keys) {
  auto &r = aqroot_hal::recorder();
  r.serial_in = keys;
  r.serial_in_pos = 0;
}

void pump(int iterations) {
  for (int i = 0; i < iterations; ++i) loop();
}

const aqroot_hal::Recorder &rec() { return aqroot_hal::recorder(); }

bool bit(uint16_t latch, uint8_t b) { return Pcal9535a::bitOf(latch, b); }

}  // namespace

int main() {
  // =========================================================================
  // ASTRA 2 + 5, and D789-A10 -- COLD BOOT.
  // =========================================================================
  {
    rig();
    const uint64_t before = rec().clock_us;
    setup();
    const uint64_t spent = rec().clock_us - before;

    claim("the image brings the expanders up to the safe latches",
          g_board.u3_output == kU3SafeLatch);
    // ASTRA 2: a cold boot that qualified the gauge with a direct
    // `configureActiveMode()` would never spend the settle.
    claim("cold boot spends the full qualified gauge settle",
          spent >= uint64_t(kFuelGaugeActiveSettleMs) * 1000u);
    claim("cold boot wrote HIBRT = 0x0000", g_board.hibrt == 0x0000);
    // D789-A10: forced sleep is cleared and the rest of CONFIG is preserved.
    claim("cold boot cleared CONFIG.SLEEP",
          (g_board.config & Max17048Guard::kConfigSleepMask) == 0);
    claim("cold boot preserved CONFIG RCOMP and ATHD",
          (g_board.config & 0xFF00) == 0x9700
          && (g_board.config & 0x001F) == 0x001C);
    claim("cold boot cleared MODE.EnSleep",
          (g_board.mode & Max17048Guard::kModeEnSleepMask) == 0);
    claim("cold boot never commanded a QuickStart",
          (g_board.mode & Max17048Guard::kModeQuickStartMask) == 0);
    // ASTRA 5: the reset-release diagnostic must report from the latch.
    // D-792 / R11-04.  THE GATE IS WIRED, AND THE IMAGE SAYS SO.
    claim("setup() wires the SPI-B sub-GHz transmit gate to the app",
          rec().consoleHas("[PASS] SPI-B sub-GHz transmit gate wired to the "
                           "accessory permission table"));
    claim("the image reports the reset release as CONFIRMED",
          rec().consoleHas("CONFIRMED from U2 output latch"));
    claim("...and the three reset lines really are released",
          bit(g_board.u2_output, AQROOT_U2_DISP_RST_N)
          && bit(g_board.u2_output, AQROOT_U2_TOUCH_RST_N)
          && bit(g_board.u2_output, AQROOT_U2_SX1262_RST_N));
  }
  {
    // ASTRA 5, the mutant's own case.  The boot-safe latch write must be
    // ALLOWED through -- otherwise the image aborts before the diagnostic and
    // the clause would pass for the wrong reason -- and only the RESET
    // RELEASE writes that follow it are NACKed.  Reads keep working, so the
    // image can see that the writes did not land.
    class AfterBegin : public aqroot_hal::I2cModel {
     public:
      Board *b = nullptr;
      // The boot-safe latch IS kU2SafeLatch, and asserting the three resets
      // leaves it there, because all three are active low.  RELEASING them is
      // the only write that moves it -- so failing every U2 output write whose
      // value differs from the safe latch fails exactly the release and
      // nothing else.
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        if (a == AQROOT_EXP_U2_ADDR && d[0] == Pcal9535a::kRegOutput0) {
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (v != kU2SafeLatch) return false;
        }
        return b->write(a, d, n);
      }
      bool readRegister(uint8_t a, uint8_t r, uint8_t *d, size_t n) override {
        return b->readRegister(a, r, d, n);
      }
      bool probe(uint8_t a) override { return b->probe(a); }
    };
    rig();
    static AfterBegin after;
    after.b = &g_board;
    aqroot_hal::model() = &after;
    setup();
    claim("a NACKed reset release is never reported CONFIRMED",
          !rec().consoleHas("CONFIRMED from U2 output latch"));
    claim("...and is reported UNKNOWN", rec().consoleHas("UNKNOWN"));
    aqroot_hal::model() = &g_board;
  }
  {
    // D789-A10, the retained-forced-sleep case: a gauge left asleep before the
    // MCU reset must NOT be qualified on the strength of HIBRT and HibStat.
    rig();
    g_board.mode = Max17048Guard::kModeEnSleepMask;
    g_board.config = 0x9700 | Max17048Guard::kConfigSleepMask | 0x1C;
    setup();
    claim("a retained forced sleep is cleared, not accepted",
          (g_board.config & Max17048Guard::kConfigSleepMask) == 0
          && (g_board.mode & Max17048Guard::kModeEnSleepMask) == 0);
    claim("...and the gauge is reported ready afterwards",
          rec().consoleHas("HIBRT=0x0000 verified"));
  }
  {
    // D789-A10: an unreadable CONFIG is FAIL-CLOSED, not assumed awake.
    rig();
    g_board.fail_address = AQROOT_I2C_ADDR_FUEL_GAUGE;
    g_board.fail_reg = Max17048Guard::kRegConfig;
    setup();
    claim("an unreadable CONFIG fails the qualification closed",
          rec().consoleHas("gauge NOT READY"));
    press("3");
    pump(2);
    claim("...and no accessory rail may be enabled",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }

  {
    // D789-A10: a gauge that will NOT leave sleep may not be qualified, and no
    // rail may be enabled on its reading.
    rig();
    g_board.sticky_ensleep = true;
    g_board.mode = Max17048Guard::kModeEnSleepMask;
    g_board.config = 0x9700 | Max17048Guard::kConfigSleepMask | 0x1C;
    setup();
    claim("a gauge that will not leave sleep is refused at boot",
          rec().consoleHas("gauge NOT READY"));
    press("3");
    pump(2);
    claim("...and no accessory rail may be enabled on its reading",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // D789-A10: CONFIG.SLEEP that will not clear.  `configureActiveMode` never
    // re-reads CONFIG, so `clearForcedSleep`'s own verification is the ONLY
    // thing that can catch this.
    rig();
    g_board.sticky_config_sleep = true;
    g_board.mode = Max17048Guard::kModeEnSleepMask;
    g_board.config = 0x9700 | Max17048Guard::kConfigSleepMask | 0x1C;
    setup();
    claim("a CONFIG.SLEEP that will not clear is refused at boot",
          rec().consoleHas("gauge NOT READY"));
    press("3");
    pump(2);
    claim("...and no accessory rail may be enabled on its reading",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // D789-A10: a part that falls asleep BETWEEN the two reads of the
    // qualification.  `clearForcedSleep` saw it awake; the MODE read that
    // follows the HIBRT write is the only thing that can catch it.
    rig();
    g_board.sleeps_after_hibrt_write = true;
    setup();
    claim("a gauge that sleeps mid-qualification is refused",
          rec().consoleHas("gauge NOT READY"));
    press("3");
    pump(2);
    claim("...and no accessory rail may be enabled on its reading",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // D789-A10: sleep asserted at RUNTIME, after a clean qualification and
    // with a rail already live, must shed rather than act on a stale VCELL.
    rig();
    setup();
    press("3");
    pump(2);
    claim("the rail is live before the gauge is put to sleep",
          bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    g_board.mode |= Max17048Guard::kModeEnSleepMask;
    g_board.config |= Max17048Guard::kConfigSleepMask;
    press("");
    for (int i = 0; i < 8; ++i) {
      delay(kBatteryGuardPeriodMs);
      loop();
    }
    claim("forced sleep asserted at runtime sheds the accessory rail",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    claim("...and is reported as no measurement, not as a flat pack",
          rec().consoleHas("VCELL unreadable"));
  }

  // =========================================================================
  // ASTRA 3 + 4 and FABLE V-01 -- THE CONSOLE ACCESSORY KEY.
  // =========================================================================
  {
    rig();
    setup();
    const uint64_t before = rec().clock_us;
    press("3");
    pump(2);
    const uint64_t spent = rec().clock_us - before;

    claim("the console '3' enables the 3.3 V accessory rail",
          bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    // ASTRA 3: a direct `setAccessory3v3()` in the switch would move the latch
    // but would NOT print the dispatch's three-fact line.
    claim("the enable went through the production dispatch",
          rec().consoleHas("ACC_3V3_SW requested on, acknowledged yes, "
                           "state after reconciliation ON"));
    // ASTRA 4 + FABLE V-01: the settled post-enable recheck must be spent.
    claim("the enable spent the settled post-enable recheck",
          spent >= uint64_t(kAccessorySettledRecheckMs) * 1000u);
  }
  {
    // ASTRA 1: the periodic battery guard has to be REACHED from `loop()`.
    // A flat pack with a rail on must be shed by running the loop alone.
    rig();
    setup();
    press("3");
    pump(2);
    claim("the rail is on before the pack goes flat",
          bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    g_board.vcell_counts = uint16_t(3.20f / Max17048Guard::kVcellLsbV);
    for (int i = 0; i < 8; ++i) {
      delay(kBatteryGuardPeriodMs);
      loop();
    }
    claim("the loop's periodic battery guard sheds a flat pack",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    claim("...and says which floor it failed",
          rec().consoleHas("below 3.20 V retention floor"));
  }
  {
    // FABLE V-02: `backgroundGaugeRequalification()` must be reached from
    // `loop()`.  Boot with the gauge hibernating -- so qualification fails --
    // then let it recover and require the loop alone to requalify it.
    rig();
    g_board.mode = Max17048Guard::kModeHibStatMask;
    setup();
    claim("a hibernating gauge is not qualified at boot",
          rec().consoleHas("gauge NOT READY"));
    press("3");
    pump(2);
    claim("...and no rail may be enabled while it is not",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    g_board.mode = 0x0000;                       // the gauge leaves hibernate
    // THE OBSERVABLE IS A RE-QUALIFICATION THE LOOP DOES BY ITSELF, with no
    // console input at all.  The '3' key would requalify on its own, so
    // counting gauge writes during a SILENT loop is the only thing that
    // distinguishes a live background retry from a dead one.
    press("");
    g_board.gauge_writes = 0;
    for (int i = 0; i < 12; ++i) {
      delay(kGaugeRequalPeriodMs);
      loop();
    }
    claim("the loop requalifies the gauge with no console input at all",
          g_board.gauge_writes > 0 && g_board.hibrt == 0x0000);
    claim("...and the rail may then be enabled with no further qualification",
          [&] {
            const int before = g_board.gauge_writes;
            press("3");
            pump(2);
            return bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN)
                && g_board.gauge_writes == before;
          }());
  }

  // =========================================================================
  // D789-A09 -- NON-ACCESSORY COMMAND INTENT.
  // =========================================================================
  {
    // The amplifier leaves shutdown for the tone and goes BACK in.  A healthy
    // board confirms both.
    rig();
    setup();
    press("t");
    pump(2);
    claim("the tone test confirms the amplifier shutdown afterwards",
          !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...and reports the reconciled state, not the request",
          rec().consoleHas("AMP_SD_MODE requested off, acknowledged yes, "
                           "state after reconciliation OFF"));
  }
  {
    // ONE-SHOT NACK on the amplifier-OFF write.  The image may NOT report the
    // amplifier as off, and the loop must retry until the latch confirms it.
    rig();
    setup();
    press("t");
    // Fail exactly the write that puts the amplifier back into shutdown: let
    // the enable through, then break the bus for the next U2 output write.
    g_board.u2_output = g_board.u2_output;       // (no-op; readability)
    class OneShot : public aqroot_hal::I2cModel {
     public:
      Board *b;
      int remaining = 0;
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        if (a == AQROOT_EXP_U2_ADDR && d[0] == Pcal9535a::kRegOutput0
            && remaining > 0) {
          // Only break the write that CLEARS the amplifier bit.
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (!Pcal9535a::bitOf(v, AQROOT_U2_AMP_SD_MODE)) {
            --remaining;
            return false;
          }
        }
        return b->write(a, d, n);
      }
      bool readRegister(uint8_t a, uint8_t r, uint8_t *d, size_t n) override {
        return b->readRegister(a, r, d, n);
      }
      bool probe(uint8_t a) override { return b->probe(a); }
    };
    static OneShot one;
    one.b = &g_board;
    one.remaining = 1;
    aqroot_hal::model() = &one;
    // ONE loop iteration: the key is dispatched and the amplifier-off write
    // NACKs.  The retry has not had its turn yet, which is the state the
    // image must report honestly.
    pump(1);
    claim("a NACKed amplifier shutdown is NOT reported as off",
          rec().consoleHas("AMPLIFIER SHUTDOWN NOT CONFIRMED"));
    claim("...and the physical latch still shows it energised",
          bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    // The loop must retry the intent until the latch confirms it.
    pump(3);
    claim("the loop retries the amplifier-off intent until it lands",
          !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...and says so", rec().consoleHas("AMP_SD_MODE intent CONFIRMED"));
    aqroot_hal::model() = &g_board;
  }
  {
    // PERSISTENT NACK on the display reset release.  The image may not claim
    // the display is up, and must abort the SPI init rather than drive a
    // panel that is still held in reset.
    rig();
    setup();
    g_board.fail_address = AQROOT_EXP_U2_ADDR;
    g_board.fail_reg = Pcal9535a::kRegOutput0;
    g_board.fail_reads = false;          // the part answers; it just NACKs writes
    press("p");
    pump(2);
    claim("a NACKed DISP_RST_N release aborts the display test",
          rec().consoleHas("ABORTED -- DISP_RST_N release not confirmed"));
    claim("...and is reported as not confirmed",
          rec().consoleHas("DISP_RST_N release NOT CONFIRMED"));
    claim("...and the backlight pin is never driven high for it",
          rec().digital_writes.empty()
          || !rec().consoleHas("four quadrants R/G/B/W, backlight ON"));
    press("s");
    pump(2);
    claim("status reports the display as NOT up while the release is pending",
          rec().consoleHas("display initialised = 0"));
  }
  {
    // The healthy display path still works end to end.
    rig();
    setup();
    press("p");
    pump(2);
    claim("a confirmed DISP_RST_N release runs the display test",
          rec().consoleHas("four quadrants R/G/B/W, backlight ON"));
    press("s");
    pump(2);
    claim("...and status then reports the display up",
          rec().consoleHas("display initialised = 1"));
    // ...and a LATER release that does not land takes it back down, even
    // though the panel was initialised once.
    g_board.fail_address = AQROOT_EXP_U2_ADDR;
    g_board.fail_reg = Pcal9535a::kRegOutput0;
    g_board.fail_reads = false;
    press("p");
    pump(1);
    aqroot_hal::recorder().console.clear();
    press("s");
    pump(1);
    claim("a later unconfirmed release takes the display back down",
          rec().consoleHas("display initialised = 0")
          && rec().consoleHas("DISP_RST_N release UNCONFIRMED"));
  }

  // =========================================================================
  // D-791 / D790-A05 -- THE WARM-RESET RECOVERY CALL SITE, IN THE IMAGE.
  //
  // Round-10 reproduced the escape: deleting `serviceExpanderRecovery()` from
  // `loop()`'s not-ready branch passed the complete D-790 H1-H8 suite, because
  // `test_production_callers.cpp` drives the METHOD and nothing compiled the
  // branch that CALLS it.  The scenario below is the one that matters on a
  // real board: a warm MCU reset leaves the PCAL9535As powered, so their
  // output latches still carry the previous instance's state -- here BOTH
  // accessory rails physically ON -- while every software flag is newly
  // constructed and says they are off.
  // =========================================================================
  {
    rig();
    // The physical latches a warm reset leaves behind.
    g_board.u3_output = uint16_t(kU3SafeLatch | kU3AccessoryMask);
    g_board.bus_down = true;          // ...and the bus is wedged at boot
    setup();
    claim("a warm reset onto a wedged bus cannot establish the safe latches",
          rec().consoleHas("FATAL: accessory/reset safety state"));
    claim("...and the retained accessory latches are still physically ON",
          (g_board.u3_output & kU3AccessoryMask) == kU3AccessoryMask);
    const size_t console_after_setup = rec().console.size();
    for (int i = 0; i < 24; ++i) { delay(kExpanderRecoveryPeriodMs); loop(); }
    claim("a persistently failed bus is never reported as recovered",
          !rec().consoleHas("I2C/expander safety state RECOVERED"));
    claim("...and nothing claims the rails are off while the bus is down",
          !rec().consoleHas("CONFIRMED off from the expander output latches"));
    claim("...and the rails really are still energised, which is the fact "
          "the image must keep retrying against",
          (g_board.u3_output & kU3AccessoryMask) == kU3AccessoryMask);
    (void)console_after_setup;
    // The bus comes back.  NOTHING ELSE HAPPENS -- no console input, no reset,
    // no operator action.  The loop alone must reach the physical latches.
    g_board.bus_down = false;
    for (int i = 0; i < 24; ++i) { delay(kExpanderRecoveryPeriodMs); loop(); }
    claim("the loop alone recovers the expanders once the bus returns",
          rec().consoleHas("I2C/expander safety state RECOVERED"));
    claim("...and the retained accessory latches are physically turned OFF",
          (g_board.u3_output & kU3AccessoryMask) == 0);
    claim("...and the whole boot-safe U3 latch is restored",
          g_board.u3_output == kU3SafeLatch);
  }

  // =========================================================================
  // D-791 / D790-A06 -- AN ABORTED TONE ENABLE MAY NOT TURN THE AMPLIFIER ON
  // LATER.
  //
  // The console tone command aborts when `setAmplifierIntent(true)` cannot be
  // confirmed -- and D-790 left the recorded intent at `want = on`, so the
  // main loop's deferred retry drove AMP_SD_MODE HIGH some milliseconds later,
  // with no tone, no operator action and no matching OFF anywhere.
  // =========================================================================
  {
    // (a) the enable write NACKs and NEVER lands.
    class FailAmpEnable : public aqroot_hal::I2cModel {
     public:
      Board *b = nullptr;
      bool fail = true;
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        if (fail && a == AQROOT_EXP_U2_ADDR && d[0] == Pcal9535a::kRegOutput0) {
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (Pcal9535a::bitOf(v, AQROOT_U2_AMP_SD_MODE)) return false;
        }
        return b->write(a, d, n);
      }
      bool readRegister(uint8_t a, uint8_t r, uint8_t *d, size_t n) override {
        return b->readRegister(a, r, d, n);
      }
      bool probe(uint8_t a) override { return b->probe(a); }
    };
    rig();
    setup();
    static FailAmpEnable amp;
    amp.b = &g_board;
    aqroot_hal::model() = &amp;
    press("t");
    pump(1);
    claim("an unconfirmed amplifier enable aborts the tone command",
          rec().consoleHas("audio: ABORTED -- AMP_SD_MODE enable not "
                           "confirmed"));
    claim("...and the ON intent is CANCELLED rather than left pending",
          rec().consoleHas("AMP_SD_MODE enable ABORTED: ON intent CANCELLED"));
    claim("...and the amplifier is not energised by the aborted command",
          !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    // The loop runs for a long time with a perfectly healthy bus.  A retained
    // ON intent would land HERE, which is exactly the defect.
    amp.fail = false;
    press("");
    for (int i = 0; i < 12; ++i) { delay(kBatteryGuardPeriodMs); loop(); }
    claim("no later deferred retry ever turns the amplifier on",
          !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    // A deferred retry is legitimate -- but only ever for the OFF direction.
    claim("...and no deferred retry ever reconciles the amplifier to ON",
          !rec().consoleHas("AMP_SD_MODE requested on, acknowledged yes, "
                            "state after reconciliation ON"));
    aqroot_hal::model() = &g_board;
  }
  {
    // (b) THE LOST FINAL ACK.  The enable write physically LANDS and the
    // master still sees a NACK, which is a real I2C failure mode: the device
    // latched the byte and the acknowledge bit was lost.  The image cannot
    // tell the two apart, so it must drive the amplifier back OFF rather than
    // leave a latch it believes did not move.
    class LostAck : public aqroot_hal::I2cModel {
     public:
      Board *b = nullptr;
      int swallow = 1;
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        const bool landed = b->write(a, d, n);
        if (swallow > 0 && a == AQROOT_EXP_U2_ADDR
            && d[0] == Pcal9535a::kRegOutput0) {
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (Pcal9535a::bitOf(v, AQROOT_U2_AMP_SD_MODE)) {
            --swallow;
            return false;            // the byte landed; the ACK did not
          }
        }
        return landed;
      }
      bool readRegister(uint8_t a, uint8_t r, uint8_t *d, size_t n) override {
        return b->readRegister(a, r, d, n);
      }
      bool probe(uint8_t a) override { return b->probe(a); }
    };
    rig();
    setup();
    static LostAck lost;
    lost.b = &g_board;
    aqroot_hal::model() = &lost;
    press("t");
    pump(1);
    claim("a lost ACK on the amplifier enable really did energise the part",
          true);
    // Whatever the latch did, the command aborted and the intent is OFF, so
    // the loop must drive it off and CONFIRM it from the physical shadow.
    press("");
    for (int i = 0; i < 8; ++i) { delay(kBatteryGuardPeriodMs); loop(); }
    claim("a lost-ACK enable is driven back off and confirmed",
          !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    claim("...and the image never claims the tone was played",
          !rec().consoleHas("i2s tone played"));
    aqroot_hal::model() = &g_board;
  }

  // =========================================================================
  // D-791 / D790-A07 -- A CONFIRMED RESET RELEASE IS NOT A CONFIRMED PANEL
  // INITIALISATION.
  //
  // success -> reset -> NACKed release -> deferred release -> RE-INIT.  D-790
  // ended that sequence with `displayIsUp()` true again the instant the retry
  // landed, with no SPI init in between.
  // =========================================================================
  {
    rig();
    setup();
    press("p");
    pump(2);
    claim("the first display test initialises the panel",
          rec().consoleCount("four quadrants R/G/B/W, backlight ON") == 1);
    press("s");
    pump(1);
    claim("...and status reports it up", rec().consoleHas(
          "display initialised = 1"));
    // A SECOND display test.  Its reset invalidates the first initialisation,
    // and its release does not land.
    g_board.fail_address = AQROOT_EXP_U2_ADDR;
    g_board.fail_reg = Pcal9535a::kRegOutput0;
    g_board.fail_reads = false;
    press("p");
    pump(1);
    claim("a new reset takes the panel down even though it was up before",
          rec().consoleCount("four quadrants R/G/B/W, backlight ON") == 1);
    press("s");
    pump(1);
    claim("...and status reports it NOT up while the release is pending",
          rec().consoleHas("display initialised = 0"));
    // The bus recovers.  The release lands on a deferred retry -- and the
    // panel must be RE-INITIALISED before anything may report it up again.
    g_board.fail_address = -1;
    g_board.fail_reg = -1;
    g_board.fail_reads = true;
    press("");
    pump(4);
    claim("a deferred release re-runs the display initialisation",
          rec().consoleHas("re-running the ILI9488 initialisation")
          && rec().consoleCount("four quadrants R/G/B/W, backlight ON") == 2);
    press("s");
    pump(1);
    claim("...and only then is the panel reported up again",
          rec().consoleHas("display initialised = 1"));
    // REPEATED REQUESTS.  A second 'p' on a healthy board re-initialises once
    // more and does not double-count or leave an owed initialisation behind.
    press("p");
    pump(2);
    claim("a repeated display request initialises exactly once more",
          rec().consoleCount("four quadrants R/G/B/W, backlight ON") == 3);
    press("");
    pump(4);
    claim("...and leaves no further initialisation owed",
          rec().consoleCount("four quadrants R/G/B/W, backlight ON") == 3);
  }

  // =========================================================================
  // THE BACKLIGHT CONSOLE KEY, THROUGH THE IMAGE.
  // =========================================================================
  {
    rig();
    setup();
    press("l");
    aqroot_hal::recorder().serial_in_pos = 0;
    const size_t pwm_before = rec().pwm.size();
    pump(2);
    const auto &pwm = rec().pwm;
    claim("the image's backlight key issues PWM", pwm.size() > pwm_before);
    claim("the image's first PWM command is full duty",
          pwm.size() > pwm_before && pwm[pwm_before].duty == 255);
    uint64_t first_dim = UINT64_MAX;
    const uint64_t t0 = pwm.size() > pwm_before ? pwm[pwm_before].t_us : 0;
    for (size_t i = pwm_before; i < pwm.size(); ++i) {
      if (first_dim == UINT64_MAX && pwm[i].duty > 0 && pwm[i].duty < 255) {
        first_dim = pwm[i].t_us;
      }
    }
    claim("no dim PWM before the full-duty prime interval",
          first_dim != UINT64_MAX
          && first_dim - t0 >= kBacklightStartupPrimeUs);
  }

  // =========================================================================
  // D-793 / R12-03.  A RETAINED CC1101 TRANSMIT STATE ACROSS AN MCU RESET.
  // =========================================================================
  {
    Cc1101Stub radio;                      // keyed BEFORE the reset
    rigWithRetainedRadio(radio);
    claim("the radio really is transmitting before the image starts",
          radio.transmitting);
    setup();

    claim("setup STROBES the CC1101 out of TX (SIDLE)",
          radio.sidle_strobes >= 1);
    claim("...and resets it (SRES, BURST CLEAR -- not a PARTNUM read)",
          radio.sres_strobes >= 1);
    claim("...and the retained transmit state is actually gone",
          !radio.transmitting);
    claim("...and the quiesce is VERIFIED from MARCSTATE, not assumed",
          radio.marcstate_reads >= 1);
    claim("...and the verifying read happened AFTER the strobes, so no "
          "MARCSTATE was read while the part was still keyed",
          radio.marcstate_reads_before_quiesce == 0);
    claim("the image reports the quiesce on the console",
          rec().consoleHas("radios quiesced after MCU reset"));
    // The whole point: the quiesce precedes anything that could authorise a
    // load.  The console is ordered, so the ordering is checkable.
    size_t quiesce_line = SIZE_MAX, gauge_line = SIZE_MAX;
    for (size_t i = 0; i < rec().console.size(); ++i) {
      if (quiesce_line == SIZE_MAX &&
          rec().console[i].find("radios quiesced after MCU reset")
          != std::string::npos) {
        quiesce_line = i;
      }
      if (gauge_line == SIZE_MAX &&
          rec().console[i].find("MAX17048 U14 hibernate disabled")
          != std::string::npos) {
        gauge_line = i;
      }
    }
    claim("the quiesce precedes the gauge qualification, which is the first "
          "thing that can lead to an accessory permission",
          quiesce_line != SIZE_MAX && gauge_line != SIZE_MAX
          && quiesce_line < gauge_line);

    // ...and with the quiesce CONFIRMED the accessory path is no longer
    // refused for radio reasons: the floor it is judged against is a real
    // derived floor, not the NOT-PERMITTED sentinel.
    press("3");
    pump(2);
    bool sentinel_refusal = false;
    for (const auto &l : rec().console) {
      if (l.find("ACC_3V3_SW REFUSED") != std::string::npos
          && l.find("floor 99.00") != std::string::npos) {
        sentinel_refusal = true;
      }
    }
    claim("a confirmed quiesce does not leave the accessory rail refused by "
          "the sub-GHz sentinel", !sentinel_refusal);
  }

  // ---- NEGATIVE CONTROL: a part that does NOT quiesce. --------------------
  {
    Cc1101Stub radio;
    radio.ignores_strobes = true;          // the strobes land and change nothing
    rigWithRetainedRadio(radio);
    setup();
    claim("a CC1101 that ignores the strobes is still transmitting",
          radio.transmitting);
    claim("...and the image does NOT report a confirmed quiesce",
          !rec().consoleHas("[ok] radios quiesced after MCU reset"));
    claim("...and says the physical transmit state is UNKNOWN",
          rec().consoleHas("radio quiesce: NOT CONFIRMED"));
    press("3");
    pump(2);
    bool sentinel_refusal = false;
    for (const auto &l : rec().console) {
      if (l.find("ACC_3V3_SW REFUSED") != std::string::npos
          && l.find("floor 99.00") != std::string::npos) {
        sentinel_refusal = true;
      }
    }
    claim("...and accessory power is REFUSED BY NAME, not granted against a "
          "load the board may actually be carrying",
          rec().consoleHas("ACCESSORY REFUSED: the physical transmit state"));
    claim("...and the rail is physically still OFF",
          !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    claim("...and the sentinel floor is what the refusal quotes",
          sentinel_refusal || rec().consoleHas("ACCESSORY REFUSED"));
  }

  // ---- NEGATIVE CONTROL: the SX1262 half. ---------------------------------
  {
    Cc1101Stub radio;
    radio.sx1262_answers_standby = false;
    rigWithRetainedRadio(radio);
    setup();
    claim("an SX1262 that will not confirm STANDBY blocks the quiesce too",
          rec().consoleHas("radio quiesce: NOT CONFIRMED"));
  }

  // ---- LIVENESS: a board that failed once must be able to recover. --------
  {
    Cc1101Stub radio;
    radio.ignores_strobes = true;
    rigWithRetainedRadio(radio);
    setup();
    claim("the failed quiesce is reported", rec().consoleHas(
        "radio quiesce: NOT CONFIRMED"));
    radio.ignores_strobes = false;         // the part starts answering
    const int sres_before = radio.sres_strobes;
    for (int i = 0; i < 8 && radio.transmitting; ++i) {
      delay(kRadioQuiescePeriodMs + 10);
      loop();
    }
    claim("loop() retries the quiesce rather than sitting with an unknown "
          "radio state forever", radio.sres_strobes > sres_before);
    claim("...and the retained transmit state is cleared on the retry",
          !radio.transmitting);
  }

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
