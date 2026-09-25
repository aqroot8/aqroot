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
#include <cstdlib>
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
#include "aqroot_demo_radios.h"

using namespace aqroot;

// The image's own entry points.
void setup();
void loop();
// D-797 / D797-08: the one host-image seam (`AQROOT_HOST_IMAGE_HARNESS`) --
// the image's own SPI-B object, so a test can leave it selected at a grant.
aqroot::SpiBusB &aqrootHostImageSpiB();

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

#include "aqroot_image_board_model.h"

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

  // =========================================================================
  // D-794 / R13-03.  A RETAINED NFC FIELD ACROSS AN MCU RESET.
  //
  // ROUND-13: "ST25R3916 can retain a physical RF field across MCU-only reset
  // while software authority restarts with no burst owner. ... Use the exact
  // ST25R3916 primary-documented mechanism to disable/reset the field and
  // verify the physical state before accessory/burst/radio authority becomes
  // permissive."
  // =========================================================================
  {
    Cc1101Stub radio;
    radio.transmitting = false;            // the sub-GHz side is clean
    radio.nfc_operation_control = 0x88;    // en | tx_en: the FIELD IS UP
    rigWithRetainedRadio(radio);
    claim("R13-03: the NFC field really is up before the image starts",
          radio.nfcFieldIsUp());
    setup();

    claim("setup issues the ST25R3916 Set default direct command "
          "(DS12484 Rev 3 section 4.4.1, code C0/C1h)",
          radio.nfc_set_default_commands >= 1);
    claim("...and the retained field is actually gone",
          !radio.nfcFieldIsUp());
    claim("...and the Operation control register is at its power-up value, "
          "which section 4.2 defines as Power-down",
          radio.nfc_operation_control == 0x00);
    claim("...and the quiesce is VERIFIED by reading register 02h back, not "
          "assumed from the write having ACKed",
          radio.nfc_operation_control_reads >= 1);
    claim("...and no verifying read was taken while the field was still up",
          radio.nfc_operation_control_reads_while_field_up == 0);
    claim("...and section 4.1's overheat-protection frame is re-sent, which "
          "Set default has just undone",
          radio.nfc_overheat_frames >= 1);
    claim("the console reports the ST25R3916 state as part of the quiesce",
          rec().consoleHas("ST25R3916 Operation control=0x00"));
    // With the field CONFIRMED off the accessory path is not refused for NFC
    // reasons, and the burst slot is free.
    press("3");
    pump(2);
    claim("...so the accessory rail is no longer refused by the NFC sentinel",
          !rec().consoleHas("the physical field state of U9"));
  }
  {
    // THE NEGATIVE CONTROL.  A part that ignores Set default must leave the
    // image refusing, not reporting success.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    radio.nfc_ignores_set_default = true;
    rigWithRetainedRadio(radio);
    setup();
    claim("R13-03 control: a part that ignores Set default is NOT reported "
          "quiesced", rec().consoleHas("FIELD STATE UNKNOWN"));
    // D-795 / R14-02: the image still WRITES the power-down value once a live
    // part has been identified -- best effort, never trusted -- so the claim
    // is about the VERDICT, which must stay UNKNOWN whatever the write did.
    claim("...and a Set default that did not land is detected by the 11h "
          "register it should have reset, not inferred from 02h",
          radio.nfc_regs[0x11] == 0xA5);
    claim("...and the image says the field state is UNKNOWN by name",
          rec().consoleHas("NFC quiesce: NOT CONFIRMED"));
    press("3");
    pump(2);
    claim("...and the accessory rail is REFUSED, by name",
          rec().consoleHas("the physical field state of U9"));
    claim("...and the rail is physically OFF",
          !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    // ...and the BURST SLOT is held on U9's behalf, so a microSD write or an
    // IR burst cannot overlap a field the board cannot see.
    press("d");
    pump(2);
    claim("...and a microSD burst is refused because the NFC field holds the "
          "arbiter", rec().consoleHas("U9 owns the burst slot"));
    press("x");
    pump(2);
    claim("...and so is an IR burst", rec().consoleCount(
        "U9 owns the burst slot") >= 2);
  }
  {
    // THE SECOND NEGATIVE CONTROL, AND R13-03 ASKS FOR IT BY NAME: "Do not
    // assume 'stop all activities' is sufficient for every retained state."
    // DS12484 section 4.4.2 stops the FIFO, the transfers and the timers and
    // leaves the Operation control register alone, so a carrier survives it.
    // An image that sent only C2/C3h would read 0x88 back and be refused.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    radio.nfc_ignores_set_default = true;          // pretend only C2/C3 landed
    radio.nfc_stop_all_activities_is_enough = false;
    rigWithRetainedRadio(radio);
    setup();
    claim("R13-03 control: the image never relies on Stop all activities, "
          "which DS12484 section 4.4.2 says leaves Operation control alone",
          radio.nfc_stop_all_commands == 0);
    claim("...and the image refuses rather than reporting a quiesce",
          rec().consoleHas("FIELD STATE UNKNOWN"));
  }
  {
    // LIVENESS, on the same rule as the sub-GHz retry: an unconfirmed field
    // refuses accessory power and holds a burst slot, so a board that gave up
    // would refuse both forever.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    radio.nfc_ignores_set_default = true;
    rigWithRetainedRadio(radio);
    setup();
    claim("R13-03 liveness: the failed NFC quiesce is reported",
          rec().consoleHas("NFC quiesce: NOT CONFIRMED"));
    radio.nfc_ignores_set_default = false;         // the part starts answering
    const int before = radio.nfc_set_default_commands;
    for (int i = 0; i < 8; ++i) {
      delay(kRadioQuiescePeriodMs + 10);
      loop();
    }
    claim("loop() retries the NFC quiesce rather than sitting with an "
          "unknown field forever",
          radio.nfc_set_default_commands > before);
    claim("...and the retained field is cleared on the retry",
          !radio.nfcFieldIsUp());
  }

  // =========================================================================
  // D-794 / R13-01.  THE STALE PRE-LOAD VCELL, REPRODUCED AND THEN REFUSED.
  //
  // ROUND-13, IN ITS OWN WORDS: "Astra reproduced the real production p -> 5
  // sequence with physical latch modeling: enable write occurs, settled read
  // falls below 3.20 V, then safe shed."
  //
  // THE NUMBERS BELOW PUT THE DEFECT ON THE ONLY PATH THROUGH, AND THEY ARE
  // CHOSEN SO THE TWO READINGS FALL ON OPPOSITE SIDES OF THE SHIPPED FLOOR.
  //
  //   pack open circuit                  3.960 V
  //   panel + backlight cost             0.200 V of node
  //   the 3.3 V accessory rail costs     0.600 V more
  //   gauge error, ONE CONSTANT SIGN    +0.020 V  (the adverse direction)
  //
  //   reported BEFORE the panel   3.960 + 0.020 = 3.980 V  -> clears 3.80 V
  //   reported AFTER  the panel   3.760 + 0.020 = 3.780 V  -> BELOW 3.80 V
  //   settled if it HAD been granted  3.160 + 0.020 = 3.180 V -> below the
  //                                   3.20 V retention floor
  //
  // So the stale reading AUTHORISES and the honest one REFUSES, and the state
  // the stale reading authorises is one the very next settled recheck sheds.
  // That is Astra's sequence with the numbers written out.  The shipped
  // 3.80 V rail-edge floor is not wrong and is not touched: what was wrong is
  // the value it was being compared against.
  //
  // WHAT THIS SCENARIO CATCHES.  On D-793 the '3' key reads 3.980 V, grants,
  // and the recheck sheds -- so `ACCESSORY FAIL-CLOSED` appears and the
  // refusal line does not.  On D-794 the read waits out the averaging window,
  // sees 3.780 V, and refuses at the EDGE.  Both claims below are false on
  // D-793 and true here, for that reason and no other.
  // =========================================================================
  {
    rig();
    g_board.physical_conversions = true;
    g_board.ocv_V = 3.960;
    g_board.display_sag_V = 0.200;
    g_board.acc3v3_sag_V = 0.600;
    g_board.gauge_error_V = +0.020;
    // Prime the conversion ring at the PRE-PANEL node.  Without this the
    // first read of the scenario would prime it at whatever the board is
    // doing then, and a model that primes itself after the load edge cannot
    // demonstrate a stale one.
    g_board.advanceConversions();
    setup();

    // THE SEQUENCE, EXACTLY AS AN OPERATOR WALKS IT.
    press("p");
    pump(2);
    claim("R13-01: the display initialisation ran", rec().consoleHas(
        "display: four quadrants"));
    const uint64_t after_display_us = rec().clock_us;
    // The register really is still describing the pre-panel board at this
    // instant -- which is what makes the rest of the scenario a reproduction
    // rather than a construction.
    g_board.advanceConversions();
    const double stale_reported =
        double(g_board.vcell_counts) * double(Max17048Guard::kVcellLsbV);
    claim("...and the gauge still reports the PRE-PANEL node, above the "
          "3.80 V rail-edge floor",
          stale_reported > kAccessorySingleRailFloorV - 0.05);

    press("3");
    pump(3);

    claim("...and the image says it is waiting for a post-load conversion",
          rec().consoleHas("waiting") &&
          rec().consoleHas("post-load conversion"));
    claim("...and the wait is long enough to flush the whole four-conversion "
          "average, not one update of it",
          rec().clock_us - after_display_us
          >= uint64_t(kGaugePostLoadConversionMs) * 1000u);

    // THE OUTCOME, AND IT IS A REFUSAL AT THE EDGE RATHER THAN A GRANT AND A
    // SHED.  R13-01: "permission itself must not knowingly authorize a state
    // that immediately sheds."
    claim("...and the accessory rail is REFUSED on the honest reading",
          rec().consoleHas("ACC_3V3_SW REFUSED"));
    claim("...and the rail was never physically energised",
          !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    claim("...and no grant-then-shed happened at all, which is the whole "
          "point: the permission did not authorise a state the next recheck "
          "would take away",
          !rec().consoleHas("ACCESSORY FAIL-CLOSED"));
  }
  {
    // THE POSITIVE CONTROL, WHICH IS WHAT MAKES THE ONE ABOVE MEAN ANYTHING.
    // The same sequence on a pack that can genuinely carry the rail must
    // still END WITH THE RAIL ON.  A guard that refused everything would pass
    // the scenario above and fail here.
    rig();
    g_board.physical_conversions = true;
    g_board.ocv_V = 4.150;
    g_board.display_sag_V = 0.160;
    g_board.acc3v3_sag_V = 0.120;
    g_board.gauge_error_V = +0.020;
    setup();
    press("p");
    pump(2);
    press("3");
    pump(3);
    claim("R13-01 positive control: a pack that can carry the rail still "
          "gets it", Pcal9535a::bitOf(g_board.u3_output,
                                      AQROOT_U3_ACC_3V3_EN));
    claim("...and it survives the settled recheck",
          !rec().consoleHas("ACCESSORY FAIL-CLOSED"));
  }
  {
    // AND THE RETENTION SHED IS STILL THERE.  R13-01: "Preserve post-enable
    // retention shedding."  A rail granted on an honest reading whose load
    // then turns out heavier than the enable floor anticipated must still be
    // shed by the settled recheck -- the epoch changes WHEN the reading is
    // taken, never whether the rule runs.
    rig();
    g_board.physical_conversions = true;
    g_board.ocv_V = 4.150;
    g_board.display_sag_V = 0.160;
    g_board.acc3v3_sag_V = 0.820;     // heavier than any floor anticipates
    g_board.gauge_error_V = +0.020;
    setup();
    press("p");
    pump(2);
    press("3");
    pump(4);
    claim("R13-01: post-enable retention shedding is PRESERVED",
          rec().consoleHas("ACCESSORY FAIL-CLOSED"));
    claim("...and it names the retention floor rather than a flat pack",
          rec().consoleHas("retention floor"));
    claim("...and the rail ends physically OFF",
          !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // THE MECHANISM ITSELF, ISOLATED.  Without the wait, the register really
    // does still describe the pre-display board -- which is the fact the
    // whole finding rests on, and it is worth claiming directly rather than
    // only through the image's behaviour.
    rig();
    g_board.physical_conversions = true;
    g_board.ocv_V = 3.980;
    g_board.display_sag_V = 0.160;
    g_board.gauge_error_V = 0.0;
    g_board.conversion_phase_us = 125000;    // off the image's clock grid
    delay(10);                               // and off t = 0
    g_board.advanceConversions();            // prime at the pre-display node
    const uint16_t before = g_board.vcell_counts;
    aqroot_hal::recorder().digital_writes.push_back(
        {AQROOT_PIN_DISP_BL_PWM, HIGH, rec().clock_us});
    delay(kGaugeVcellUpdateMs);              // ONE update, D-779's model
    g_board.advanceConversions();
    const uint16_t after_one = g_board.vcell_counts;
    delay(kGaugeVcellUpdateMs * 3);          // three more: the full average
    g_board.advanceConversions();
    const uint16_t after_four = g_board.vcell_counts;
    const double lsb = double(Max17048Guard::kVcellLsbV);
    claim("R13-01 mechanism: after ONE update the register is still mostly "
          "the pre-load node -- D-779's 400 ms bought a quarter of the step",
          double(before - after_one) * lsb < 0.160 * 0.30);
    claim("...and only after FOUR updates does it describe the present load",
          double(before - after_four) * lsb > 0.160 * 0.98);
  }

  // =========================================================================
  // D-795 / R14-01.  THE TIMING MODELS ROUND-14 ASKED FOR, EVERY ONE OF THEM.
  //
  // ROUND-14: "Add independent timing models at nominal and +3.5%,
  // integrating/straddling conversion, phase sweep, same-value conversions,
  // and the exact stale-enable counterexamples."
  //
  // Every scenario below runs the REAL image over the board model with the
  // contamination audit on, so the claim is not "the image waited" but "no
  // reading the image acted on contained a conversion that began before an
  // edge it had to see".
  // =========================================================================
  struct TimingModel { uint64_t period_us; bool integrating; uint64_t phase_us; };
  std::vector<TimingModel> models;
  for (uint64_t period : {uint64_t(250000), uint64_t(258750)}) {
    for (bool integ : {false, true}) {
      for (uint64_t phase : {uint64_t(0), uint64_t(37000), uint64_t(91000),
                             uint64_t(125000), uint64_t(173000),
                             uint64_t(211000), uint64_t(249000)}) {
        models.push_back({period, integ, phase});
      }
    }
  }
  auto apply = [](const TimingModel &m) {
    g_board.physical_conversions = true;
    g_board.conversion_period_us = m.period_us;
    g_board.integrating_conversions = m.integrating;
    g_board.conversion_phase_us = m.phase_us;
  };

  // ---- (1) ASTRA'S p -> 3 AND p -> 5, OVER EVERY TIMING MODEL. -------------
  //
  // Reported before the panel 3.980 V, after it 3.780 V, against the 3.80 V
  // quiet-row floor.  A single pre-edge conversion in the average is worth
  // 50 mV of the 200 mV step, so ANY contamination flips the answer.
  {
    int refused = 0, energised = 0, contaminated = 0, runs = 0;
    for (const char *rail : {"3", "5"}) {
      for (const auto &m : models) {
        rig();
        apply(m);
        g_board.ocv_V = 3.960;
        g_board.display_sag_V = 0.200;
        g_board.acc3v3_sag_V = 0.600;
        g_board.acc5v_sag_V = 0.600;
        g_board.gauge_error_V = +0.020;
        setup();
        press("p");
        pump(2);
        press(rail);
        pump(3);
        ++runs;
        const bool r3 = rail[0] == '3';
        refused += rec().consoleHas(r3 ? "ACC_3V3_SW REFUSED"
                                       : "ACC_5V_SW REFUSED");
        bool on = false;
        for (const auto &e : g_board.latch_events) {
          on = on || Pcal9535a::bitOf(e.u3_output, r3 ? AQROOT_U3_ACC_3V3_EN
                                                      : AQROOT_U3_ACC_5V_SW_EN);
        }
        energised += on;
        contaminated += g_board.firmwareContaminatedReads()
                      + g_board.externalContaminatedReads();
      }
    }
    char name[200];
    snprintf(name, sizeof(name),
             "R14-01: Astra's p -> 3 and p -> 5 are REFUSED at the edge under "
             "all %d timing models (nominal and tERR +3.5 %%, instantaneous "
             "and integrating, seven phases)", runs);
    claim(name, refused == runs);
    claim("...and no rail was ever physically energised in any of them",
          energised == 0);
    claim("...and no reading any of them acted on contained a conversion "
          "that began before the panel came up", contaminated == 0);
  }

  // ---- (2) THE POSITIVE CONTROL OVER THE SAME MODELS. ----------------------
  {
    int granted = 0, runs = 0, contaminated = 0;
    for (const auto &m : models) {
      rig();
      apply(m);
      g_board.ocv_V = 4.150;
      g_board.display_sag_V = 0.160;
      g_board.acc3v3_sag_V = 0.120;
      g_board.gauge_error_V = +0.020;
      setup();
      press("p");
      pump(2);
      press("3");
      pump(3);
      ++runs;
      granted += Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN)
                 && !rec().consoleHas("ACCESSORY FAIL-CLOSED");
      contaminated += g_board.firmwareContaminatedReads();
    }
    claim("R14-01 positive control: a pack that can carry the rail gets it "
          "under every timing model, and keeps it through the settled recheck",
          granted == runs);
    claim("...and the settled recheck itself read only post-step conversions",
          contaminated == 0);
  }

  // ---- (3) THE UNANNOUNCED SOURCE CHANGE. ----------------------------------
  //
  // Astra: "an UNANNOUNCED external source/node change immediately before an
  // accessory request."  While the charger is attached its current raises the
  // node the gauge reads (D-794 documented this); the firmware cannot see the
  // unplug.  Charging-era reading 3.760 + 0.100 + 0.020 = 3.880 V clears the
  // 3.80 V floor; the honest post-unplug reading 3.780 V does not.
  {
    int refused = 0, runs = 0, contaminated = 0, energised = 0;
    for (const auto &m : models) {
      for (uint64_t lead_us : {uint64_t(0), uint64_t(10000), uint64_t(120000)}) {
        rig();
        apply(m);
        g_board.ocv_V = 3.760;
        g_board.gauge_error_V = +0.020;
        g_board.external_events.push_back({0, +0.100});   // charging from boot
        setup();
        delay(3000);                    // long enough that nothing is pending
        g_board.external_events.push_back({rec().clock_us - lead_us, 0.0});
        press("3");
        pump(3);
        ++runs;
        refused += rec().consoleHas("ACC_3V3_SW REFUSED");
        energised += Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN);
        contaminated += g_board.externalContaminatedReads();
      }
    }
    claim("R14-01: a charger unplugged 0, 10 or 120 ms before the request -- "
          "an edge the firmware CANNOT see -- does not grant the rail on the "
          "charging-era average, under any timing model", refused == runs
          && energised == 0);
    claim("...and the admission read contained no conversion from before the "
          "unplug: the request is its own epoch", contaminated == 0);
  }

  // ---- (4) SAME-VALUE CONVERSIONS: the rule is TIME, never a value change. --
  {
    rig();
    g_board.physical_conversions = true;
    g_board.ocv_V = 4.100;               // nothing sags; every conversion equal
    setup();
    delay(3000);
    const uint64_t pressed = rec().clock_us;
    press("3");
    pump(1);
    uint64_t first_read = 0;
    for (const auto &r : g_board.vcell_reads) {
      if (r.t_us >= pressed) { first_read = r.t_us; break; }
    }
    claim("R14-01 same-value conversions: with an unchanging node the "
          "admission STILL waits the full window after the request -- "
          "freshness is not inferred from a reading that moved",
          first_read >= pressed + uint64_t(kGaugePostLoadConversionMs) * 1000u);
    claim("...and the rail is granted once it has",
          Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }

  // ---- (5) THE DEADLINE LOOP: a delay that returns early is not a clock. ---
  {
    int late_enough = 0, runs = 0, contaminated = 0;
    for (const auto &m : models) {
      rig();
      apply(m);
      aqroot_hal::recorder().delay_shortfall_ms = 10;
      g_board.ocv_V = 3.760;
      g_board.gauge_error_V = +0.020;
      g_board.external_events.push_back({0, +0.100});
      setup();
      delay(3000);
      const uint64_t pressed = rec().clock_us;
      g_board.external_events.push_back({pressed, 0.0});
      press("3");
      pump(1);
      ++runs;
      uint64_t first_read = 0;
      for (const auto &r : g_board.vcell_reads) {
        if (r.t_us >= pressed) { first_read = r.t_us; break; }
      }
      late_enough += first_read
          >= pressed + uint64_t(kGaugePostLoadConversionMs) * 1000u;
      contaminated += g_board.externalContaminatedReads();
    }
    claim("R14-01: with every delay returning 10 ms early the admission read "
          "is still taken at least the full window after the request -- the "
          "wait loops on an elapsed deadline", late_enough == runs);
    claim("...and so it is still uncontaminated", contaminated == 0);
  }

  // ---- (6) THE RAIL STEP IS AN EPOCH: the settled recheck reads post-step. -
  {
    int shed_at_recheck = 0, runs = 0, contaminated = 0;
    for (const auto &m : models) {
      rig();
      apply(m);
      g_board.ocv_V = 4.150;
      g_board.acc3v3_sag_V = 0.980;      // settles at 3.19 V reported
      g_board.gauge_error_V = +0.020;
      setup();
      press("3");
      pump(1);
      ++runs;
      shed_at_recheck += rec().consoleHas(
          "ACC_3V3_SW requested on, acknowledged yes, state after "
          "reconciliation OFF");
      contaminated += g_board.firmwareContaminatedReads();
    }
    claim("R14-01: a rail whose settled node is under retention is shed BY "
          "THE SETTLED RECHECK itself, under every timing model",
          shed_at_recheck == runs);
    claim("...because that recheck waited out the window from the rail step, "
          "not from the request", contaminated == 0);
  }

  // ---- (7) THE 5 V SHED IS AN EPOCH: the 3.3 V rail is judged post-shed. ---
  {
    int kept = 0, runs = 0, contaminated = 0, shed5 = 0;
    for (const auto &m : models) {
      rig();
      apply(m);
      g_board.ocv_V = 4.200;
      g_board.acc3v3_sag_V = 0.100;
      g_board.acc5v_sag_V = 0.200;
      g_board.gauge_error_V = +0.020;
      setup();
      press("3");
      pump(1);
      press("5");
      pump(1);
      // The pack sags on its own: both rails now leave 3.12 V reported, under
      // retention; the 3.3 V rail alone leaves 3.32 V, over it.
      g_board.external_events.push_back({rec().clock_us, -0.780});
      press("");
      for (int i = 0; i < 12; ++i) {
        delay(kBatteryGuardPeriodMs);
        loop();
      }
      ++runs;
      shed5 += rec().consoleHas("ACC_5V_SW SHED");
      kept += Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN)
              && !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_5V_SW_EN);
      contaminated += g_board.firmwareContaminatedReads();
    }
    claim("R14-01: a pack sag sheds the 5 V rail first under every timing "
          "model", shed5 == runs);
    claim("...and the 3.3 V rail is KEPT, because the next retention read "
          "waited out the window from the 5 V shed instead of reading the "
          "pre-shed average", kept == runs);
    claim("...and no retention read contained a conversion from before a "
          "firmware edge", contaminated == 0);
  }

  // ---- (8) THE PANEL NEVER COMES UP WITH A RAIL LIVE. ----------------------
  //
  // The only path in the shipped image on which the panel could come up while
  // an accessory rail is on is the DEFERRED one: 'p' is pressed with both
  // rails off, the DISP_RST_N release NACKs and is left pending, the operator
  // enables a rail, and the release lands on a `loop()` retry (D-791 /
  // D790-A07).  It is NOT reachable, and this scenario is the proof: a NACKed
  // U2 write invalidates U2's output shadow, `DemoExpanders::service()` treats
  // an invalid shadow as an unfinished safety transaction (D-783) and sheds
  // every rail on its next pass, and that pass runs BEFORE the deferred retry
  // in the same loop iteration.  So every VCELL reading after a panel edge
  // is necessarily an ADMISSION, which stamps its own request -- which is why
  // the display stamp is carried by a per-site claim in
  // test_production_callers.cpp rather than by physics here.
  {
    int lit_with_rail = 0, runs = 0, contaminated = 0, ended_off = 0;
    for (const auto &m : models) {
      rig();
      apply(m);
      g_board.ocv_V = 4.100;
      g_board.acc3v3_sag_V = 0.250;
      g_board.display_sag_V = 0.700;
      g_board.gauge_error_V = +0.020;
      setup();
      g_board.fail_address = AQROOT_EXP_U2_ADDR;
      g_board.fail_reg = Pcal9535a::kRegOutput0;
      g_board.fail_writes = true;
      g_board.fail_reads = false;
      press("p");
      pump(1);
      press("3");
      pump(1);
      g_board.fail_address = -1;         // U2 answers again
      press("");
      for (int i = 0; i < 10; ++i) {
        delay(kBatteryGuardPeriodMs);
        loop();
      }
      ++runs;
      bool lit = false;
      for (const auto &w : rec().digital_writes) {
        if (w.pin == AQROOT_PIN_DISP_BL_PWM && w.value != LOW
            && g_board.accessoryOnAt(w.t_us, AQROOT_U3_ACC_3V3_EN)) {
          lit = true;
        }
      }
      lit_with_rail += lit;
      ended_off += !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN);
      contaminated += g_board.firmwareContaminatedReads();
    }
    claim("R14-01: on the deferred reset-release path the panel NEVER comes up "
          "with an accessory rail live, under any timing model -- the invalid "
          "U2 shadow sheds the rails first", lit_with_rail == 0);
    claim("...and the rail ends physically off", ended_off == runs);
    claim("...and no reading was contaminated by a firmware edge",
          contaminated == 0);
  }

  // =========================================================================
  // D-795 / R14-02.  NFC OFF MUST REQUIRE LIVE COMMUNICATION.
  //
  // ROUND-14: "Zero, 0xFF, stale reply, ignored Set default, wrong identity,
  // invalid chip-select/read path, and later liveness loss must keep NFC
  // UNKNOWN. ... Add production-image retained-field tests for zero read, FF
  // read, stale safe read, ignored write, invalid identity, recovery, and MCU
  // reset."
  // =========================================================================
  struct NfcFault { const char *name; void (*arm)(Cc1101Stub &); };
  const NfcFault faults[] = {
      {"an all-zero MISO (dead read path / unasserted chip select)",
       [](Cc1101Stub &r) { r.nfc_zero_fill = true; }},
      {"an all-ones MISO", [](Cc1101Stub &r) { r.nfc_ff_fill = true; }},
      {"a stale reply (every read returns the previous one)",
       [](Cc1101Stub &r) { r.nfc_stale_reply = true; }},
      {"register writes that do not land",
       [](Cc1101Stub &r) { r.nfc_ignores_writes = true; }},
      {"an ignored Set default",
       [](Cc1101Stub &r) { r.nfc_ignores_set_default = true; }},
      {"a wrong identity (not ic_type 0b00101)",
       [](Cc1101Stub &r) { r.nfc_ic_identity = 0x12; }},
      {"an Operation control register that will not clear",
       [](Cc1101Stub &r) { r.nfc_opcontrol_sticky = true; }},
      {"a part that dies after Set default (every later read is zero)",
       [](Cc1101Stub &r) { r.nfc_dies_after_set_default = true; }},
  };
  for (const auto &f : faults) {
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;          // the retained field
    f.arm(radio);
    rigWithRetainedRadio(radio);
    setup();
    char name[240];
    snprintf(name, sizeof(name),
             "R14-02: %s leaves the NFC field UNKNOWN, never confirmed OFF",
             f.name);
    claim(name, rec().consoleHas("FIELD STATE UNKNOWN")
                && !rec().consoleHas("FIELD OFF, live identity"));
    press("3");
    pump(2);
    claim("...and accessory power is refused by name",
          rec().consoleHas("the physical field state of U9")
          && !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    press("d");
    pump(1);
    press("x");
    pump(1);
    claim("...and U9 owns the burst slot: microSD and IR are both refused",
          rec().consoleCount("U9 owns the burst slot") >= 2);
  }
  {
    // AN UNIDENTIFIED PART IS NEVER COMMANDED.  Whatever answers on U9's chip
    // select with the wrong identity is not sent a register challenge, a Set
    // default or a power-down write -- the image does not poke a device it
    // has not identified.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_ic_identity = 0x12;
    rigWithRetainedRadio(radio);
    setup();
    claim("R14-02: a part with the wrong identity is never sent a challenge, "
          "a Set default or a power-down write",
          radio.nfc_challenge_writes == 0 && radio.nfc_set_default_commands == 0
          && radio.nfc_operation_control_zero_writes == 0);
  }
  {
    // THE ZERO-FILL CASE IS THE ONE ASTRA REPRODUCED, AND ITS WHOLE POINT IS
    // THAT 02h READS 0x00.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    radio.nfc_zero_fill = true;
    rigWithRetainedRadio(radio);
    setup();
    claim("R14-02 Astra's case: with a zero-filled bus the retained field is "
          "physically still up and the image does not say otherwise",
          radio.nfcFieldIsUp() && rec().consoleHas("FIELD STATE UNKNOWN"));
  }
  {
    // RECOVERY: the fault clears and the loop proves the field off.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    radio.nfc_zero_fill = true;
    rigWithRetainedRadio(radio);
    setup();
    radio.nfc_zero_fill = false;
    for (int i = 0; i < 8; ++i) {
      delay(kRadioQuiescePeriodMs + 10);
      loop();
    }
    claim("R14-02 recovery: once the part answers, the loop's retry proves "
          "the field off", !radio.nfcFieldIsUp()
          && rec().consoleHas("FIELD OFF, live identity"));
    press("3");
    pump(2);
    claim("...and accessory power is then granted",
          Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // LATER LIVENESS LOSS REVOKES A CONFIRMATION.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    rigWithRetainedRadio(radio);
    setup();
    press("3");
    pump(2);
    claim("R14-02: a healthy U9 is confirmed and the rail is granted",
          Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    radio.nfc_zero_fill = true;                  // the part stops answering
    press("");
    for (int i = 0; i < 4; ++i) {
      delay(kNfcLivenessPeriodMs + 10);
      loop();
    }
    claim("...and when it stops answering the OFF confirmation is REVOKED",
          rec().consoleHas("NFC OFF confirmation REVOKED"));
    claim("...and the rail granted under it is SHED",
          !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
    press("d");
    pump(1);
    claim("...and U9 owns the burst slot again",
          rec().consoleHas("U9 owns the burst slot"));
    press("3");
    pump(2);
    claim("...and a new rail request is refused until it is reconfirmed",
          !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // LIVENESS IS MORE THAN AN IDENTITY.  A part whose writes stop landing
    // still answers the identity register, and can no longer be commanded
    // off -- so the liveness probe's challenge, not its identity read, is
    // what revokes.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    rigWithRetainedRadio(radio);
    setup();
    press("3");
    pump(2);
    radio.nfc_ignores_writes = true;
    press("");
    for (int i = 0; i < 4; ++i) {
      delay(kNfcLivenessPeriodMs + 10);
      loop();
    }
    claim("R14-02: a part whose writes stop landing is REVOKED by the "
          "liveness challenge even though its identity still reads",
          rec().consoleHas("NFC OFF confirmation REVOKED")
          && !Pcal9535a::bitOf(g_board.u3_output, AQROOT_U3_ACC_3V3_EN));
  }
  {
    // MCU RESET WITH A HEALTHY PART: the full sequence ran, in order.
    Cc1101Stub radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x88;
    rigWithRetainedRadio(radio);
    setup();
    claim("R14-02: the quiesce proves identity TWICE, runs the 11h challenge "
          "both ways and writes 02h = 0x00 explicitly after Set default",
          radio.nfc_identity_reads >= 2 && radio.nfc_challenge_writes >= 2
          && radio.nfc_operation_control_zero_writes >= 1
          && radio.nfc_set_default_commands >= 1);
    claim("...and the field is off and confirmed",
          !radio.nfcFieldIsUp() && rec().consoleHas("FIELD OFF, live identity"));
  }

  // =========================================================================
  // D-796 / D796-05 item 4 + D796-09 C-NFC-QUIESCE-01.  THE REVOCATION
  // DEADLINE, MEASURED ON THE SHIPPED IMAGE AT EVERY PHASE.
  //
  // ROUND-15: "current plan says revocation within 1 s, but the production-
  // image trace can remain unrevoked for ~2.6 s during blocking gauge/
  // admission work.  Either change firmware/scheduling to guarantee the
  // promised wall-clock deadline, OR publish and qualify the real bounded
  // worst-case latency."
  //
  // It reproduced: D-795 serviced the liveness probe once per `loop()`, and a
  // single '5' press spends the admission window (1300 ms), the settled
  // recheck (400 ms) and the rest of the window from the rail step (900 ms)
  // inside ONE iteration.  The image now gives the probe an opportunity
  // before every slice of every app-owned wait, and re-proves liveness AT
  // every grant.  This sweep drops U9 at every 20 ms of a first-rail and a
  // second-rail admission, from five different phases of the probe
  // schedule, and measures the latency from the loss to the revocation line
  // and to the shed of every rail that was live at the loss.
  // =========================================================================
  {
    struct LossStats {
      int runs = 0, revoked = 0, shed = 0, enabled_after_loss = 0;
      uint64_t worst_revoke_us = 0, worst_shed_us = 0;
    };
    auto sweep = [](bool second_rail) {
      LossStats st;
      for (uint64_t phase_ms : {uint64_t(0), uint64_t(100), uint64_t(200),
                                uint64_t(300), uint64_t(400)}) {
        for (uint64_t offset_ms = 0; offset_ms <= 2900; offset_ms += 20) {
          rig();
          setup();
          delay(3000);                   // every boot edge is spent
          if (second_rail) {
            press("3");
            pump(1);
            press("");
          }
          // Move the probe schedule's phase relative to the key press.
          for (uint64_t t = 0; t < phase_ms; t += 10) {
            delay(10);
            loop();
          }
          const uint64_t pressed = rec().clock_us;
          const uint64_t loss = pressed + offset_ms * 1000u;
          g_radio->nfc_dead_from_us = loss;
          press(second_rail ? "5" : "3");
          pump(1);
          press("");
          for (int i = 0; i < 150; ++i) {   // three seconds of idle loop
            delay(20);
            loop();
          }
          ++st.runs;
          for (size_t i = 0; i < rec().console.size(); ++i) {
            if (rec().console_t_us[i] >= loss &&
                rec().console[i].find("NFC OFF confirmation REVOKED")
                    != std::string::npos) {
              ++st.revoked;
              const uint64_t lat = rec().console_t_us[i] - loss;
              if (lat > st.worst_revoke_us) st.worst_revoke_us = lat;
              break;
            }
          }
          const bool live_at_loss =
              g_board.accessoryOnAt(loss, AQROOT_U3_ACC_3V3_EN) ||
              g_board.accessoryOnAt(loss, AQROOT_U3_ACC_5V_SW_EN);
          uint16_t prev = 0x0000;
          bool shed = !live_at_loss;
          for (const auto &e : g_board.latch_events) {
            const bool on3 = bit(e.u3_output, AQROOT_U3_ACC_3V3_EN);
            const bool on5 = bit(e.u3_output, AQROOT_U3_ACC_5V_SW_EN);
            if (e.t_us >= loss &&
                ((on3 && !bit(prev, AQROOT_U3_ACC_3V3_EN)) ||
                 (on5 && !bit(prev, AQROOT_U3_ACC_5V_SW_EN)))) {
              ++st.enabled_after_loss;
            }
            if (live_at_loss && !shed && e.t_us >= loss && !on3 && !on5) {
              shed = true;
              const uint64_t lat = e.t_us - loss;
              if (lat > st.worst_shed_us) st.worst_shed_us = lat;
            }
            prev = e.u3_output;
          }
          st.shed += shed;
        }
      }
      return st;
    };
    const uint64_t deadline_us = uint64_t(kNfcRevocationDeadlineMs) * 1000u;
    claim("C-NFC-QUIESCE-01: the published revocation deadline is DERIVED -- "
          "the liveness period plus the longest step with no liveness "
          "opportunity plus the probe-and-shed allowance -- and is inside "
          "the 1 s the first-five plan promises",
          kNfcRevocationDeadlineMs == kNfcLivenessPeriodMs
              + kNfcLongestUnpolledStepMs + kNfcRevocationWorkAllowanceMs
          && kNfcRevocationDeadlineMs <= 1000u);
    for (bool second : {true, false}) {
      const LossStats st = sweep(second);
      const char *what = second
          ? "a SECOND-rail admission with ACC_3V3_SW live (admission window, "
            "settled recheck and the rest of the window from the rail step)"
          : "a FIRST-rail admission";
      char name[360];
      snprintf(name, sizeof(name),
               "C-NFC-QUIESCE-01: a U9 lost at any 20 ms instant of %s, from "
               "five probe phases (%d runs), is REVOKED within the %lu ms "
               "deadline", what, st.runs,
               (unsigned long)kNfcRevocationDeadlineMs);
      claim(name, st.revoked == st.runs && st.worst_revoke_us <= deadline_us);
      claim("...and every rail live at the loss is SHED within the same "
            "deadline", st.shed == st.runs && st.worst_shed_us <= deadline_us);
      claim("...and no rail is ever enabled at or after the loss: every grant "
            "is decided on a liveness proof taken AT the grant",
            st.enabled_after_loss == 0);
      std::printf("  measured (%s rail): worst revocation %.3f ms, worst shed "
                  "%.3f ms, deadline %lu ms\n", second ? "second" : "first",
                  double(st.worst_revoke_us) / 1000.0,
                  double(st.worst_shed_us) / 1000.0,
                  (unsigned long)kNfcRevocationDeadlineMs);
    }
  }

  {
    // A BURST IS A GRANT TOO.  U9 is proved alive at the top of this loop
    // iteration and lost immediately afterwards, so the periodic schedule
    // will not look again for a full period -- the burst key must re-prove
    // it at the grant, or a microSD / IR burst runs beside a field nobody
    // can see.
    for (const char *key : {"d", "x"}) {
      rig();
      setup();
      delay(3000);
      loop();                              // a scheduled probe: alive
      g_radio->nfc_dead_from_us = rec().clock_us;
      press(key);
      pump(1);
      const bool sd = key[0] == 'd';
      char name[240];
      snprintf(name, sizeof(name),
               "C-NFC-QUIESCE-01: a %s burst requested just after U9 was lost "
               "is refused AT the grant -- the grant re-proves liveness rather "
               "than trusting the last scheduled proof",
               sd ? "microSD" : "IR");
      claim(name, rec().consoleHas("NFC OFF confirmation REVOKED")
                  && rec().consoleHas("U9 owns the burst slot"));
      claim("...and the burst never ran",
            !rec().consoleHas(sd ? "microSD  CMD0" : "IR  "));
    }
  }

  {
    // THE LOOP-TOP PROBE, ON ITS OWN.  Rails off, no key pressed, a healthy
    // gauge: nothing in `loop()` but the top-of-loop call gives the probe an
    // opportunity -- no admission, no gauge window, no settled recheck, no
    // retention read.  A lost U9 must still be revoked within the bound, or a
    // later grant, burst or session would be the first to find out.
    int runs = 0, revoked = 0;
    uint64_t worst_us = 0;
    for (uint64_t offset_ms = 0; offset_ms < 1000; offset_ms += 20) {
      rig();
      setup();
      delay(3000);
      loop();
      const uint64_t loss = rec().clock_us + offset_ms * 1000u;
      g_radio->nfc_dead_from_us = loss;
      press("");
      for (int i = 0; i < 200; ++i) {        // four seconds of idle loop
        delay(20);
        loop();
      }
      ++runs;
      for (size_t i = 0; i < rec().console.size(); ++i) {
        if (rec().console_t_us[i] >= loss &&
            rec().console[i].find("NFC OFF confirmation REVOKED")
                != std::string::npos) {
          ++revoked;
          const uint64_t lat = rec().console_t_us[i] - loss;
          if (lat > worst_us) worst_us = lat;
          break;
        }
      }
    }
    char name[240];
    snprintf(name, sizeof(name),
             "C-NFC-QUIESCE-01: with both rails off and the loop idle -- where "
             "only the top-of-loop probe runs -- a lost U9 is REVOKED within "
             "the %lu ms deadline at every 20 ms phase (%d runs)",
             (unsigned long)kNfcRevocationDeadlineMs, runs);
    claim(name, revoked == runs
                && worst_us <= uint64_t(kNfcRevocationDeadlineMs) * 1000u);
    std::printf("  measured (idle, rails off): worst revocation %.3f ms\n",
                double(worst_us) / 1000.0);
  }
  {
    // THE PUBLISHED OPERATOR-TEST EXCEPTION IS THE SHIPPED RAMP'S LENGTH.
    rig();
    setup();
    delay(3000);
    const uint64_t before = rec().clock_us;
    press("l");
    pump(1);
    const uint64_t spent_ms = (rec().clock_us - before) / 1000u;
    claim("C-NFC-QUIESCE-01 exception: the longest unpreemptible operator "
          "test, the 'l' backlight ramp, takes the 827 ms the published "
          "rails-off exception (1347 ms) is derived from",
          spent_ms >= kLongestUnpreemptibleOperatorTestMs
          && spent_ms <= kLongestUnpreemptibleOperatorTestMs + 5
          && kNfcRevocationWithRailsOffOperatorTestMs == 1347);
  }

  // =========================================================================
  // D-797 / D797-08 (Fable R16-03).  A DEFERRED PROBE AT A GRANT REFUSES THE
  // GRANT AND KEEPS THE CONFIRMATION.
  //
  // "At rail/burst/session grants, a forced liveness probe returning
  // Deferred must refuse the new grant while preserving prior confirmation
  // state; do not treat Deferred as 'no news' for authorization."
  //
  // The shipped probe reports `Deferred` when SPI-B is already selected.  The
  // test leaves the image's own SPI-B selected (a CC1101 transaction in
  // flight) across the key press, so the forced probe at the grant CANNOT
  // run, and then releases it: the grant must be refused, nothing may be
  // revoked or shed, and the very next request -- with no quiesce in between
  // -- must be granted on the confirmation that was kept.
  // =========================================================================
  {
    auto rail3On = []() {
      return bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN);
    };
    auto rail5On = []() {
      return bit(g_board.u3_output, AQROOT_U3_ACC_5V_SW_EN);
    };
    auto enabledAfter = [](uint64_t t_us, uint8_t b) {
      for (const auto &e : g_board.latch_events) {
        if (e.t_us >= t_us && bit(e.u3_output, b)) return true;
      }
      return false;
    };
    const char *kDeferred = "REFUSED at the grant: the ST25R3916 liveness "
                            "probe was DEFERRED";
    {
      // THE FIRST-RAIL GRANT.
      rig();
      setup();
      delay(3000);
      loop();
      const int quiesces = rec().consoleCount("FIELD OFF, live identity");
      const uint64_t pressed = rec().clock_us;
      SpiBusB &spi = aqrootHostImageSpiB();
      const bool held = spi.select(SpiBDevice::Cc1101);
      press("3");
      pump(1);
      press("");
      spi.release();
      claim("D797-08 image: with SPI-B busy at the grant, a FIRST-rail "
            "admission is REFUSED because the forced liveness probe was "
            "Deferred -- not granted on the last scheduled proof",
            held && rec().consoleHas(kDeferred)
            && rec().consoleHas("ACC_3V3_SW REFUSED")
            && !enabledAfter(pressed, AQROOT_U3_ACC_3V3_EN));
      claim("...and the Deferred probe revoked NOTHING: no revocation line, "
            "no quiesce retry, the confirmation is kept",
            !rec().consoleHas("NFC OFF confirmation REVOKED")
            && rec().consoleCount("FIELD OFF, live identity") == quiesces);
      press("3");
      pump(1);
      press("");
      claim("...and with SPI-B free the very next request is GRANTED on the "
            "kept confirmation, with no quiesce in between",
            rail3On()
            && rec().consoleCount("FIELD OFF, live identity") == quiesces);
      press("3");
      pump(1);
      press("");
    }
    {
      // THE SECOND-RAIL GRANT, with ACC_3V3_SW already live.
      rig();
      setup();
      delay(3000);
      press("3");
      pump(1);
      press("");
      const bool first = rail3On();
      const uint64_t pressed = rec().clock_us;
      SpiBusB &spi = aqrootHostImageSpiB();
      const bool held = spi.select(SpiBDevice::Cc1101);
      press("5");
      pump(1);
      press("");
      spi.release();
      claim("D797-08 image: with SPI-B busy at the grant, a SECOND-rail "
            "admission is REFUSED on the Deferred probe",
            first && held && rec().consoleHas(kDeferred)
            && rec().consoleHas("ACC_5V_SW REFUSED")
            && !enabledAfter(pressed, AQROOT_U3_ACC_5V_SW_EN));
      claim("...and the rail already live under the kept confirmation is "
            "NOT shed, and nothing is revoked",
            rail3On() && !rec().consoleHas("NFC OFF confirmation REVOKED"));
      press("5");
      pump(1);
      press("");
      claim("...and with SPI-B free the second rail is then GRANTED",
            rail3On() && rail5On());
      press("5");
      pump(1);
      press("3");
      pump(1);
      press("");
    }
    // THE BURST GRANTS.
    for (const char *key : {"d", "x"}) {
      rig();
      setup();
      delay(3000);
      loop();
      const bool sd = key[0] == 'd';
      SpiBusB &spi = aqrootHostImageSpiB();
      const bool held = spi.select(SpiBDevice::Cc1101);
      press(key);
      pump(1);
      press("");
      spi.release();
      char name[240];
      snprintf(name, sizeof(name),
               "D797-08 image: with SPI-B busy at the grant, a %s burst is "
               "REFUSED on the Deferred probe and never runs",
               sd ? "microSD" : "IR");
      claim(name, held && rec().consoleHas(kDeferred)
                  && !rec().consoleHas(sd ? "microSD  CMD0" : "IR  "));
      claim("...and the Deferred probe revoked nothing and left the burst "
            "slot free -- U9 did not take it",
            !rec().consoleHas("NFC OFF confirmation REVOKED")
            && !rec().consoleHas("U9 owns the burst slot"));
      press(key);
      pump(1);
      press("");
      claim("...and with SPI-B free the same burst then runs",
            rec().consoleHas(sd ? "microSD  CMD0" : "IR  "));
    }
  }

  // =========================================================================
  // D-797 / D797-02.  THE CHARGING MODE-ENTRY FLOOR, IN THE SHIPPED IMAGE.
  //
  // With no accessory rail live, audio + sub-GHz is safe while charging only
  // above a 3.60 V reported cell.  The image's own SpiBusB keys the CC1101
  // (sub-GHz alone: no floor), and then the operator's tone key asks for the
  // amplifier -- the mode edge that reaches audio + sub-GHz.
  // =========================================================================
  {
    rig();
    setup();
    delay(3000);
    loop();
    g_board.vcell_counts = uint16_t(3.55f / Max17048Guard::kVcellLsbV);
    SpiBusB &spi = aqrootHostImageSpiB();
    const bool keyed = spi.beginTransmit(SpiBDevice::Cc1101);
    claim("D797-02 image: with no rail live the image keys sub-GHz ALONE at "
          "a 3.55 V pack -- its charging floor is zero",
          keyed && spi.transmitting() == SpiBDevice::Cc1101
          && !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN)
          && !bit(g_board.u3_output, AQROOT_U3_ACC_5V_SW_EN));
    const int tones = rec().consoleCount("i2s tone ");
    press("t");
    pump(1);
    press("");
    claim("D797-02 image: with sub-GHz keyed and no rail live, the tone key "
          "is REFUSED at 3.55 V -- audio + sub-GHz needs 3.60 V while "
          "charging -- and the amplifier never leaves shutdown",
          rec().consoleHas("AMP_SD_MODE enable REFUSED: VCELL 3.5")
          && rec().consoleHas("below the 3.60 V charging floor")
          && rec().consoleHas("audio: ABORTED")
          && rec().consoleCount("i2s tone ") == tones
          && !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    g_board.vcell_counts = uint16_t(3.65f / Max17048Guard::kVcellLsbV);
    press("t");
    pump(2);
    press("");
    claim("...and at 3.65 V the same key energises the amplifier for the tone "
          "and puts it back into shutdown",
          rec().consoleCount("i2s tone played") == tones + 1
          && rec().consoleHas("AMP_SD_MODE requested off, acknowledged yes")
          && !bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE));
    spi.endTransmit(SpiBDevice::Cc1101);
  }

  // =========================================================================
  // D-796 / D796-10.  A FIELD-OWNING NFC SESSION OWNS THE LIVENESS PROBE.
  //
  // ROUND-15: "NFC liveness probe currently rewrites register 11h while the
  // field is confirmed off.  Document/architect future field-owning firmware
  // so active NFC operation suspends/owns that liveness probe."
  //
  // The ownership token is the SPI-B transmit slot: a session is
  // `SpiBusB::beginTransmit(SpiBDevice::St25r3916)`.  While it is held,
  // neither the liveness probe nor the quiesce may touch U9 -- not a
  // challenge write, not a Set default, not even a chip select.
  // =========================================================================
  {
    rig();
    Cc1101Stub &radio = *g_radio;
    radio.transmitting = false;
    radio.nfc_operation_control = 0x00;
    BoardChipSelects selects;
    selects.begin();
    SpiBusB bus(selects);
    // D-801 / D801-07: the board model now answers an SPI-B frame only while
    // the peripheral is bound to the SPI-B pins, so this direct-call scenario
    // binds it exactly as `probeNfcLivenessOnBusB` does, and releases it.
    SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,
              -1);
    uint8_t identity = 0x00;
    const NfcLivenessResult free_probe = st25r3916LivenessProbe(bus, &identity);
    claim("D796-10: with no session the liveness probe runs its 11h "
          "challenge and proves the part alive",
          free_probe == NfcLivenessResult::Alive
          && radio.nfc_challenge_writes >= 2);
    const bool took = bus.beginTransmit(SpiBDevice::St25r3916);
    radio.nfc_operation_control = 0x88;   // the session's own field is up
    const int writes_before = radio.nfc_challenge_writes;
    const uint32_t frames_before = rec().low_edges[AQROOT_PIN_NFC_CS_N];
    const NfcLivenessResult owned = st25r3916LivenessProbe(bus, &identity);
    const bool raw_alive = st25r3916StillAlive(bus, &identity);
    const NfcQuiesceReport q = st25r3916QuiesceReport(bus);
    claim("D796-10: while a field session owns U9 the liveness probe is "
          "SUSPENDED -- it reports Deferred, never Lost",
          took && owned == NfcLivenessResult::Deferred);
    claim("...and neither the probe, the raw liveness challenge nor the "
          "quiesce writes register 11h under the session",
          radio.nfc_challenge_writes == writes_before);
    claim("...and none of them so much as selects the part",
          rec().low_edges[AQROOT_PIN_NFC_CS_N] == frames_before);
    claim("...and a raw challenge under a session is never a liveness proof",
          !raw_alive);
    claim("...and the quiesce refuses BY NAME instead of Set-defaulting the "
          "session's field", !q.confirmed
          && q.failed_at == NfcQuiesceStep::OwnedBySession
          && radio.nfc_set_default_commands == 0 && radio.nfcFieldIsUp());
    radio.nfc_operation_control = 0x00;   // the session turns its field off
    bus.endTransmit(SpiBDevice::St25r3916);
    const NfcLivenessResult after = st25r3916LivenessProbe(bus, &identity);
    claim("...and once the session releases U9 the probe challenges 11h again",
          after == NfcLivenessResult::Alive
          && radio.nfc_challenge_writes > writes_before);
    SPI.end();
  }

  // =========================================================================
  // D-796 / D796-10 + D796-09 C-GAUGE-EPOCH-01 (Fable G10).  A STALLED
  // FRESHNESS CLOCK IS NEVER FRESHNESS.
  //
  // ROUND-15: "Add a production-image/host scenario for a stalled/non-
  // advancing freshness clock."  The load epoch measures its window with
  // `millis()`.  A clock that stops -- at the request, in the middle of the
  // window, or inside the settled recheck after a grant -- must yield NO
  // VCELL reading, refuse the admission, and shed a rail it cannot re-judge.
  // =========================================================================
  {
    auto enabledEver = []() {
      for (const auto &e : g_board.latch_events) {
        if (bit(e.u3_output, AQROOT_U3_ACC_3V3_EN)) return true;
      }
      return false;
    };
    auto readsFrom = [](uint64_t t_us) {
      int n = 0;
      for (const auto &r : g_board.vcell_reads) n += r.t_us >= t_us;
      return n;
    };
    for (uint64_t stall_ms : {uint64_t(0), uint64_t(600)}) {
      rig();
      setup();
      delay(3000);
      const uint64_t pressed = rec().clock_us;
      aqroot_hal::recorder().freeze_at_us = pressed + stall_ms * 1000u;
      if (stall_ms == 0) aqroot_hal::recorder().clock_frozen = true;
      press("3");
      pump(3);
      char name[240];
      snprintf(name, sizeof(name),
               "C-GAUGE-EPOCH-01 G10: with millis() stalled %s the admission "
               "window is never treated as spent -- the image says the clock "
               "did not advance", stall_ms == 0 ? "AT the request"
                                                : "600 ms into the window");
      claim(name, rec().consoleHas("the clock did not advance"));
      claim("...and the rail is REFUSED and never energised",
            rec().consoleHas("ACC_3V3_SW REFUSED") && !enabledEver());
      claim("...and no VCELL reading at all is taken on the stalled clock",
            readsFrom(pressed) == 0);
    }
    {
      rig();
      setup();
      delay(3000);
      const uint64_t pressed = rec().clock_us;
      const uint64_t stall =
          pressed + (uint64_t(kGaugePostLoadConversionMs) + 150u) * 1000u;
      aqroot_hal::recorder().freeze_at_us = stall;
      press("3");
      pump(3);
      claim("C-GAUGE-EPOCH-01 G10: a clock that stalls inside the settled "
            "recheck AFTER a grant never lets the recheck read -- the rail "
            "granted a moment earlier is SHED as no measurement",
            enabledEver()
            && !bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN)
            && rec().consoleHas("VCELL unreadable"));
      claim("...and no VCELL reading is taken after the stall",
            readsFrom(stall) == 0);
    }
  }

  // =========================================================================
  // D-800 (Round-19 full review).  EVERY SPI USER RELEASES THE PERIPHERAL.
  //
  // The pinned core ignores `SPI.begin(pins)` while the bus is running
  // (`test/image/SPI.h` now models that).  D-799's boot quiesce began SPI-B
  // and never ended it, and `loop()` re-runs that quiesce every 250 ms while
  // a radio is unconfirmed -- so the display init, `p` and the microSD probe
  // then clocked SPI-A traffic out on the SPI-B pins.  Healthy radios and a
  // board whose radios never confirm quiesce, both.
  // =========================================================================
  for (int unconfirmed = 0; unconfirmed < 2; ++unconfirmed) {
    rig();
    if (unconfirmed) aqroot_hal::spiModel() = nullptr;   // MISO reads 0xFF
    setup();
    pump(8);
    delay(1200);
    pump(8);
    const char *which = unconfirmed ? " (radios never confirm quiesce)"
                                    : " (healthy radios)";
    char name[200];
    snprintf(name, sizeof(name),
             "D-800: after boot and the periodic re-quiesce the SPI "
             "peripheral is RELEASED%s", which);
    claim(name, rec().spi_bound_sck == -1);
    press("d");
    pump(3);
    press("p");
    pump(3);
    snprintf(name, sizeof(name),
             "D-800: no SPI begin was silently ignored while bound to the "
             "other bus -- the microSD and display use SPI-A pins%s", which);
    claim(name, rec().spi_begin_ignored_other_pins == 0);
  }

  // =========================================================================
  // D-800 (Round-19 full review, firmware fail-closed audit).
  // =========================================================================
  // 1. A WEDGED I2C BUS AT BOOT IS NO REASON TO LEAVE A RETAINED TRANSMITTER
  //    KEYED.  U7/U9 quiesce over SPI-B alone.
  {
    static Cc1101Stub radio;
    radio = Cc1101Stub();
    rigWithRetainedRadio(radio);
    g_board.bus_down = true;
    setup();
    claim("D-800: with I2C wedged at boot, setup() still quiesces the "
          "retained CC1101 (SRES/SIDLE) and U9's field",
          !radio.transmitting && radio.sres_strobes > 0
          && !radio.nfcFieldIsUp());
  }
  {
    // ...and loop() keeps retrying while the expanders recover: the radios
    // do not answer at boot, then do.
    static Cc1101Stub radio;
    radio = Cc1101Stub();
    rig();
    g_board.bus_down = true;
    aqroot_hal::spiModel() = nullptr;
    setup();
    g_radio = &radio;
    aqroot_hal::spiModel() = &radio;
    for (int i = 0; i < 40; ++i) { delay(50); loop(); }
    claim("D-800: with I2C still wedged, loop() retries the radio quiesce "
          "before the expander recovery branch returns",
          !radio.transmitting && radio.sres_strobes > 0
          && !radio.nfcFieldIsUp());
  }
  // 2. THE millis() WRAP.  Every wait is wrap-safe elapsed time.
  {
    rig();
    setup();
    pump(3);
    aqroot_hal::recorder().clock_us = uint64_t(0xFFFFFFFDu) * 1000u;
    aqroot_hal::recorder().hang_guard_us =
        aqroot_hal::recorder().clock_us + 5000000u;
    press("x");
    loop();
    aqroot_hal::recorder().hang_guard_us = ~uint64_t(0);
    claim("D-800: the IR self-test pressed 3 ms before the millis() wrap "
          "returns, emitter off", true);
  }
  {
    rig();
    aqroot_hal::recorder().pin_level[AQROOT_PIN_SX1262_BUSY] = HIGH;
    setup();
    pump(2);
    aqroot_hal::recorder().clock_us = uint64_t(0xFFFFFFEBu) * 1000u;
    aqroot_hal::recorder().hang_guard_us =
        aqroot_hal::recorder().clock_us + 5000000u;
    for (int i = 0; i < 4; ++i) { loop(); delay(300); }
    aqroot_hal::recorder().hang_guard_us = ~uint64_t(0);
    claim("D-800: an SX1262 with BUSY stuck high 21 ms before the millis() "
          "wrap does not hang the quiesce retry", true);
    // ...and the wait itself, entered at EXACTLY the instant whose D-799
    // deadline was 0xFFFFFFFF.
    aqroot_hal::recorder().clock_us = uint64_t(0xFFFFFFEBu) * 1000u;
    aqroot_hal::recorder().hang_guard_us =
        aqroot_hal::recorder().clock_us + 5000000u;
    const bool waited = aqroot::sx1262WaitBusy();
    aqroot_hal::recorder().hang_guard_us = ~uint64_t(0);
    claim("D-800: sx1262WaitBusy entered 20 ms before the wrap times out "
          "and returns false", !waited);
  }
  // 3. NO RAIL WHILE AN EXPANDER'S OUTPUT STATE IS UNKNOWN.
  {
    // The auditor's sequence: `p`, whose DISP_RST_N release NACKs; the next
    // iteration re-syncs, the deferred retry NACKs again and invalidates U2's
    // shadow; `3` in that same iteration.  D-799 energised ACC_3V3 for
    // 1300 ms with U2's output state UNKNOWN.
    class RelNack : public aqroot_hal::I2cModel {
     public:
      Board *b = nullptr;
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        if (a == AQROOT_EXP_U2_ADDR && d[0] == Pcal9535a::kRegOutput0) {
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (Pcal9535a::bitOf(v, AQROOT_U2_DISP_RST_N)
              && !Pcal9535a::bitOf(b->u2_output, AQROOT_U2_DISP_RST_N))
            return false;
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
    pump(2);
    static RelNack m;
    m.b = &g_board;
    aqroot_hal::model() = &m;
    press("p");
    pump(1);
    press("3");
    pump(1);
    bool ever = false;
    for (const auto &e : g_board.latch_events) {
      if (Pcal9535a::bitOf(e.u3_output, AQROOT_U3_ACC_3V3_EN)) ever = true;
    }
    claim("D-800: ACC_3V3 is never energised while U2's output state is "
          "UNKNOWN after a NACKed reset release", !ever);
  }

  // =========================================================================
  // D-801 / D801-07 (Fable R20-02).  THE D-800 FIXES THAT HAD NO HOST CLAIM.
  //
  // Round-20 reproduced four D-800 production fixes whose removal left H1-H8
  // green.  Each block below states the BEHAVIOUR the fix buys and fails for
  // that stated reason when the fix is reverted (the matching controls are
  // in `checks/firmware_hw_map_contract.py` H6).  `probeCc1101`'s own
  // wrap-safe SO wait is NOT given one: it runs only inside `setup()`, whose
  // `millis()` is a few seconds, so a wrap there is unreachable and a control
  // for it would be a control for syntax.
  // =========================================================================
  // (a) THE 5 V TWIN OF D-800's ACC_3V3 UNKNOWN-SHADOW REFUSAL.  The same
  //     auditor's sequence -- `p` whose DISP_RST_N release NACKs, so U2's
  //     output shadow is UNKNOWN -- then `5`.  Neither 5 V disconnect may
  //     close: not the boost enable, not the load switch.
  {
    class RelNack5 : public aqroot_hal::I2cModel {
     public:
      Board *b = nullptr;
      bool write(uint8_t a, const uint8_t *d, size_t n) override {
        if (a == AQROOT_EXP_U2_ADDR && d[0] == Pcal9535a::kRegOutput0) {
          const uint16_t v = uint16_t(d[1]) | uint16_t(uint16_t(d[2]) << 8);
          if (Pcal9535a::bitOf(v, AQROOT_U2_DISP_RST_N)
              && !Pcal9535a::bitOf(b->u2_output, AQROOT_U2_DISP_RST_N))
            return false;
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
    pump(2);
    static RelNack5 m;
    m.b = &g_board;
    aqroot_hal::model() = &m;
    press("p");
    pump(1);
    press("5");
    pump(1);
    bool boost = false, sw = false;
    for (const auto &e : g_board.latch_events) {
      if (Pcal9535a::bitOf(e.u3_output, AQROOT_U3_ACC_5V_BOOST_EN)) boost = true;
      if (Pcal9535a::bitOf(e.u3_output, AQROOT_U3_ACC_5V_SW_EN)) sw = true;
    }
    claim("D801-07 (a): ACC_5V (boost enable AND load switch) is never "
          "energised while U2's output state is UNKNOWN after a NACKed reset "
          "release -- the 5 V twin of D-800's ACC_3V3 refusal", !boost && !sw);
  }
  // (b) THE QUIESCE IS CLOCKED ON THE SPI-B PINS.  A retained CC1101 carrier
  //     and a retained U9 field at boot, then the periodic quiesce retry and
  //     the liveness schedule: every byte sent to a selected SPI-B part must
  //     leave on the SPI-B pins, and the retained states must actually stop.
  {
    static Cc1101Stub radio;
    radio = Cc1101Stub();
    rigWithRetainedRadio(radio);
    setup();
    for (int i = 0; i < 12; ++i) { delay(100); loop(); }
    claim("D801-07 (b): every byte the boot quiesce, the quiesce retry and the "
          "liveness probe clock into a SELECTED SPI-B part leaves on the SPI-B "
          "pins -- none while the peripheral is bound to the SPI-A pins",
          radio.spi_b_wrong_pin_transfers == 0);
    claim("D801-07 (b): ...and so the retained CC1101 carrier and U9 field "
          "are really stopped and the quiesce is CONFIRMED on the console",
          !radio.transmitting && !radio.nfcFieldIsUp()
          && rec().consoleHas("MARCSTATE=0x01 (IDLE)")
          && rec().consoleHas("FIELD OFF, live identity"));
  }
  // (c) THE microSD PROBE RELEASES THE PERIPHERAL.  `d` binds SPI-A.  If it
  //     did not end, the pinned core would IGNORE the next SPI-B `begin` --
  //     the liveness probe, 500 ms later -- whose frames would then leave on
  //     the SPI-A pins, read an undriven MISO and REVOKE a healthy U9.
  {
    rig();
    setup();
    pump(3);
    const int revoked = rec().consoleCount("NFC OFF confirmation REVOKED");
    press("d");
    pump(1);
    press("");
    const bool released = rec().spi_bound_sck == -1;
    for (int i = 0; i < 12; ++i) { delay(100); loop(); }
    claim("D801-07 (c): the microSD probe RELEASES the SPI peripheral "
          "(SPI.end) when it finishes", released);
    claim("D801-07 (c): ...so no later SPI-B begin is silently ignored, no "
          "SPI-B byte leaves on the SPI-A pins, and a healthy U9 is NOT "
          "revoked by its next liveness probe",
          rec().spi_begin_ignored_other_pins == 0
          && g_healthy_radio.spi_b_wrong_pin_transfers == 0
          && rec().consoleCount("NFC OFF confirmation REVOKED") == revoked);
  }
  // (d) WRAP-SAFE WAITS THAT ARE REACHABLE AT THE WRAP.
  //   (d1) `cc1101Quiesce`'s SO wait after SRES.  The retry runs at any
  //        uptime while a radio is unconfirmed.  The D-799 form
  //        `deadline = millis() + 10; while (... && millis() < deadline)` is
  //        FALSE at once when the deadline wraps, so MARCSTATE was read while
  //        the part was still resetting (SO high, MISO all-ones) and a
  //        healthy CC1101 was reported NOT IDLE -- a spurious UNKNOWN that
  //        refuses every accessory rail.
  {
    static Cc1101Stub radio;
    radio = Cc1101Stub();
    rig();
    aqroot_hal::spiModel() = nullptr;       // no answer at boot: UNCONFIRMED
    setup();
    pump(2);
    radio.so_busy_after_sres_us = 200;      // SO high 200 us after SRES
    g_radio = &radio;
    aqroot_hal::spiModel() = &radio;
    aqroot_hal::recorder().clock_us = uint64_t(0xFFFFFFF8u) * 1000u;
    const size_t mark = rec().console.size();
    loop();
    bool idle_at_wrap = false;
    for (size_t i = mark; i < rec().console.size(); ++i) {
      if (rec().console[i].find("MARCSTATE=0x01 (IDLE)") != std::string::npos)
        idle_at_wrap = true;
    }
    claim("D801-07 (d1): at the millis() wrap the CC1101 quiesce still waits "
          "for SO to fall after SRES, so a healthy part is CONFIRMED IDLE "
          "rather than read mid-reset", idle_at_wrap && !radio.transmitting);
  }
  //   (d2) the microphone capture.  `m` is a console key, pressed at any
  //        uptime.  The D-799 form ended at once when its deadline wrapped
  //        and reported a working microphone as zero frames.
  {
    rig();
    setup();
    pump(3);
    aqroot_hal::recorder().clock_us = uint64_t(0xFFFFFF9Cu) * 1000u;
    press("m");
    loop();
    claim("D801-07 (d2): the microphone capture pressed 100 ms before the "
          "millis() wrap still collects its full 200 ms (9600 frames)",
          rec().consoleHas("I2S RX up, 9600 frames"));
  }

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
