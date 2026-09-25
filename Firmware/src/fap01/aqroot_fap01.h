#pragma once
// AQROOT Demo -- FAP-01, THE FIRST-ARTICLE DIAGNOSTIC IMAGE.  NEVER SHIP IT.
//
// ADDED AT D-801 / D801-01 (Astra R20-01).
//
// D-800 found that the release image (`[env:aqroot-demo]`) keys NOTHING -- no
// sub-GHz carrier, no NFC field, no Wi-Fi, no IR frame, no held audio or
// backlight duty, no 10 ms VCELL poll, and no way to hold a push-pull chip
// select high -- and that eight first-article steps need exactly those
// states.  It named the image that provides them (`FAP-01`) as a
// prerequisite and left it PENDING.  Round-20: "no executable
// image/environment/build/flash/command set exists".  This is it.
//
// WHAT IT IS.  The SAME `src/demo/main.cpp` and the SAME `src/hw/` layer as
// the release image, plus this directory, built ONLY by
// `pio run -e aqroot-demo-fap01` with `-DAQROOT_FAP01_DIAGNOSTIC`.  Every
// release console key, gate, permission row, quiesce and liveness rule is
// therefore the release image's own, unmodified; `firmware_hw_map_contract`
// H6 runs the whole release-image host test against this build to prove it.
// The stimuli below are ADDITIONS, and every one of them:
//
//   * keys through the release image's own authority -- sub-GHz only through
//     `SpiBusB::beginTransmit` (the D-792 permission table's mode edge and the
//     D-793 "physical state known" rule), the NFC field only through
//     `DemoBringupApp::beginNfcFieldSession` (D796-10), audio only through
//     `setAmplifierIntent` (the mode edge), IR only through `burstAllowed` and
//     the burst arbiter, and Wi-Fi through `wifiActivationPermitted` (below);
//   * stamps the D-794 gauge load epoch on both edges, directly or through the
//     app method it keys through;
//   * is BOUNDED by a constant in this file, enforced by `service()` from the
//     top of every `loop()`, and stoppable from the console (the same key
//     again, or `Q` for everything);
//   * is QUIESCED on stop with the release image's own quiesce where one
//     exists (`cc1101Quiesce`, `sx1262Quiesce`), and otherwise left UNKNOWN
//     for the release image's quiesce retry to prove (the NFC field, D796-10).
//
// THE Wi-Fi CONFLICT, RESOLVED IN THE OPEN.  The production policy refuses
// every Wi-Fi/BLE mode set: `accessoryChargingModeEntryFloor` carries it as
// `kAccessoryNotPermittedV`, because the firmware cannot see the adapter
// (D-776) and a charger SUPPLEMENTING a Wi-Fi-sized load is ABSORBING (D-797 /
// D797-02).  FAP-01 still ASKS `wifiActivationPermitted()` and prints its
// refusal; it then waives ONLY that charging-row refusal, ONLY with no
// accessory rail live (a rail-live Wi-Fi row is a D-792 table refusal and is
// never waived), ONLY after the operator has declared the bench source
// (`V`: no charger -- VBUS blocked on the console cable, pack or bench supply
// only), ONLY with no other transmitter, field, audio or burst live, for at
// most `kWifiBurstMaxMs`, and never again inside `kWifiCooldownMs`.  None of
// this exists in the release image: `src/fap01/` is outside its
// `build_src_filter`, `aqroot_fap01.cpp` refuses to compile without
// `AQROOT_FAP01_DIAGNOSTIC`, and `test_fap01_image.cpp` compiled against the
// release sources proves every FAP-01 key is inert there.
//
// THE CONSOLE.  Upper-case keys (the release image uses lower case and
// digits), documented in `docs/full-beta-v2/assembly/FAP01_FIRST_ARTICLE_IMAGE.md`
// with the first-article step each one serves:
//
//   C  CC1101 continuous TX, 433.92 MHz, PATABLE 0xC0 (toggle)   <= 30 s
//   L  SX1262 CW, 915 MHz, +22 dBm (toggle)                      <= 30 s
//   N  ST25R3916 field ON through an NFC field session (toggle)   <= 60 s
//   T  one ISO14443A REQA while the field is on (report only)
//   V  declare the bench source for Wi-Fi (no charger)            valid 120 s
//   W  Wi-Fi TX burst (raw probe requests, 19.5 dBm)              <= 10 s
//   I  38 kHz NEC IR burst from D1, ten frames                    ~1.1 s
//   H  chip-select hold-off, U7 CC1101_CS_N (toggle)              <= 60 s
//   J  chip-select hold-off, U9 NFC_CS_N (toggle)                 <= 60 s
//   K  U9 hold-off armed to begin 700 ms after the key           <= 60 s
//   Y  U9 hold-off armed to begin 2000 ms after the key          <= 60 s
//   A  held audio drive at the release tone's level (toggle)      <= 30 min
//   B  held backlight PWM duty 50 %, after the D-784 prime        <= 30 min
//   G  VCELL raw poll every 10 ms for 2 s (timestamp + value)
//   Q  stop every FAP-01 stimulus now
//   ?  print this list
//
// This header needs only the Arduino surface `Firmware/test/image/` provides,
// so `Firmware/test/test_fap01_image.cpp` compiles and RUNS it.

#if !defined(AQROOT_FAP01_DIAGNOSTIC)
#error "src/fap01/ is the FAP-01 first-article DIAGNOSTIC image and is NEVER part of the release image -- build it only with `pio run -e aqroot-demo-fap01`"
#endif

#include <stdint.h>

#include <Arduino.h>

#include "../hw/aqroot_demo_bringup_app.h"
#include "../hw/aqroot_demo_expanders.h"
#include "../hw/aqroot_demo_timing_policy.h"
#include "../hw/aqroot_i2c_arduino.h"
#include "../hw/aqroot_spi_bus_b.h"

namespace aqroot {
namespace fap01 {

// ---------------------------------------------------------------------------
// THE BOUNDS.  Every keyed state ends on its own at these, whatever the
// operator does, from `service()` at the top of `loop()`.  A blocking release
// test (a gauge admission, `l`, `p`) can delay the stop by its own length --
// at most a few seconds -- and never removes it.
constexpr uint32_t kSubGhzTxMaxMs = 30000;
constexpr uint32_t kNfcFieldMaxMs = 60000;
constexpr uint32_t kWifiBurstMaxMs = 10000;
constexpr uint32_t kWifiCooldownMs = 30000;
constexpr uint32_t kBenchDeclarationMs = 120000;
constexpr uint32_t kHoldOffMaxMs = 60000;
constexpr uint32_t kHoldOffNearDelayMs = 700;    // inside a 1300 ms admission window
constexpr uint32_t kHoldOffFarDelayMs = 2000;    // inside the settled recheck after it
constexpr uint32_t kThermalHoldMaxMs = 30u * 60u * 1000u;
constexpr unsigned kIrNecFrames = 10;
constexpr uint32_t kIrNecFramePeriodMs = 110;    // NEC repeat period
constexpr uint32_t kVcellPollPeriodMs = 10;
constexpr uint32_t kVcellPollSpanMs = 2000;
constexpr uint8_t kHeldBacklightDuty = 128;      // 50 % at 8 bits
// "The capped level".  No firmware constant anywhere in the tree defines an
// audio cap; the ledger's 120 mA line is a DECLARED estimate of the release
// tone.  FAP-01 therefore holds the release tone itself -- `playTone`'s default
// amplitude, a 1 kHz square wave in both slots -- and C-THERM-01 RECORDS the
// current it draws.  If the owner defines a different cap, it changes HERE.
constexpr uint16_t kAudioCappedAmplitude = 6000;
constexpr uint32_t kAudioToneHz = 1000;

static_assert(kSubGhzTxMaxMs <= 60000u && kNfcFieldMaxMs <= 60000u &&
              kWifiBurstMaxMs <= 10000u && kHoldOffMaxMs <= 60000u,
              "FAP-01 RF, field and hold-off states are bounded to a minute");
static_assert(kHoldOffNearDelayMs < kGaugePostLoadConversionMs,
              "the near hold-off lands inside a rail admission's gauge window");
static_assert(kHoldOffFarDelayMs > kGaugePostLoadConversionMs,
              "the far hold-off lands after the grant, in the settled recheck");

// ---------------------------------------------------------------------------
// THE HELD BACKLIGHT DUTY, AS A SEAM.  D-784 / D-787: the TPS61169's Q11 gate
// hold network must be charged at 100 % CTRL duty for the prime interval
// before ANY dim duty is applied.  The release ramp does that through
// `runBacklightRampPolicy`; a HELD duty is a different shape (it stays), so it
// has its own two-line policy on the SAME constant, and the host test checks
// the recorded PWM stream, not this function's text.
template <typename WriteDuty, typename WaitUs>
void runHeldBacklightPolicy(WriteDuty write_duty, WaitUs wait_us, uint8_t duty) {
  write_duty(255);
  wait_us(kBacklightStartupPrimeUs);
  write_duty(duty);
}

// ---------------------------------------------------------------------------
// THE CHIP-SELECT HOLD-OFF INJECTION.  "The pin held high while the driver
// believes it selected the part."  `SpiBusB` still records the device as
// selected, and every transaction still runs; only the PHYSICAL select is
// held deasserted, which is what a lifted pin or a dead select does -- and
// what a 10 kOhm pull-up cannot do against the MCU's push-pull drive.  Only
// U7 and U9 are injectable, the two the first-article steps name.
class HoldOffChipSelects : public BoardChipSelects {
 public:
  void driveSelect(SpiBDevice device, bool asserted) override {
    if (asserted && holdOffActive(device)) {
      ++injected_;
      BoardChipSelects::driveSelect(device, false);
      return;
    }
    BoardChipSelects::driveSelect(device, asserted);
  }
  // Arm (or release) a hold-off that begins `delay_ms` from now.
  void setHoldOff(SpiBDevice device, bool on, uint32_t delay_ms = 0) {
    Slot *s = slot(device);
    if (s == nullptr) return;
    s->armed = on;
    s->armed_ms = millis();
    s->delay_ms = delay_ms;
  }
  bool holdOffArmed(SpiBDevice device) const {
    const Slot *s = slot(device);
    return s != nullptr && s->armed;
  }
  bool holdOffActive(SpiBDevice device) const {
    const Slot *s = slot(device);
    return s != nullptr && s->armed && millis() - s->armed_ms >= s->delay_ms;
  }
  // Milliseconds the hold-off has been ACTIVE (0 while only armed).
  uint32_t holdOffActiveMs(SpiBDevice device) const {
    const Slot *s = slot(device);
    if (s == nullptr || !s->armed) return 0;
    const uint32_t since = millis() - s->armed_ms;
    return since >= s->delay_ms ? since - s->delay_ms : 0;
  }
  uint32_t injected() const { return injected_; }
  void clearAll() {
    u7_ = Slot();
    u9_ = Slot();
  }

 private:
  struct Slot {
    bool armed = false;
    uint32_t armed_ms = 0;
    uint32_t delay_ms = 0;
  };
  Slot *slot(SpiBDevice d) {
    return d == SpiBDevice::Cc1101 ? &u7_
         : d == SpiBDevice::St25r3916 ? &u9_ : nullptr;
  }
  const Slot *slot(SpiBDevice d) const {
    return d == SpiBDevice::Cc1101 ? &u7_
         : d == SpiBDevice::St25r3916 ? &u9_ : nullptr;
  }
  Slot u7_, u9_;
  uint32_t injected_ = 0;
};

// The release image's app type, spelled once so the two translation units
// agree.  `demo/main.cpp` has the same `using DemoApp = ...`.
using App = DemoBringupApp<ArduinoI2cBus, void (*)(const char *)>;

struct Context {
  App *app;
  SpiBusB *spi_b;
  HoldOffChipSelects *selects;
  DemoExpanders *expanders;
  ArduinoI2cBus *bus;
};

// Called by `demo/main.cpp` -- and ONLY inside
// `#if defined(AQROOT_FAP01_DIAGNOSTIC)`:
//   begin     in `setup()`, after the expander safe latches and BEFORE the
//             boot radio quiesce, so a hold-off armed before a warm reset is
//             in force when the boot quiesce runs;
//   announce  in `setup()`, once the console is up;
//   service   first in every `loop()`, before any early return;
//   handleKey first in the console dispatch; true = the key was consumed.
void begin(const Context &ctx);
void announce();
void service();
bool handleKey(char key);
void stopAll(const char *why);
bool anyActive();

}  // namespace fap01
}  // namespace aqroot
