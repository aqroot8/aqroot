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

  // =========================================================================
  // D-794 / R13-01.  A MAX17048 THAT CONVERTS ON ITS OWN SCHEDULE.
  //
  // ROUND-13: "Add the Astra stale-pre-light-step reproduction as a permanent
  // negative/regression test, including threshold/gauge quantization and one
  // constant gauge-error sign."
  //
  // Every scenario above this one reads `vcell_counts` as a constant, which
  // is the right model for a test about HIBRT, sleep or plausibility and the
  // wrong one for a test about AGE.  With `physical_conversions` set, the
  // register stops being a variable the test writes and becomes what ADI
  // 19-6171 Rev.7 describes: "VCELL is the average of four ADC conversions.
  // The value updates every 250ms in active mode."
  //
  // THE THREE THINGS THE ROUND-13 WORDING ASKS FOR, EXPLICITLY:
  //
  //   FOUR-DEEP AVERAGE, 250 ms APART.  `conversions_` is a ring of four and
  //   `advance()` pushes one per 250 ms of RECORDED time.  Immediately after
  //   a load step all four are pre-step; one update later three are; only
  //   after four is the register describing the present load.  This is the
  //   mechanism, not an approximation of it.
  //
  //   QUANTIZATION.  Every conversion is rounded to the register's own LSB,
  //   78.125 uV, exactly as the part reports it, so a threshold comparison in
  //   the image sees the same grid the silicon produces.
  //
  //   ONE CONSTANT GAUGE-ERROR SIGN.  `gauge_error_V` is added to every
  //   conversion and never flipped, so no scenario can pass because an error
  //   that hurt on one read happened to help on the next.  The default is the
  //   POSITIVE sign, which is the adverse one for admission: it makes the
  //   part report a healthier cell than it has.
  //
  // THE NODE.  Derived from what is physically ON at the moment of each
  // conversion -- the accessory latches (from this model's own write history,
  // so a conversion in the past sees the past) and the panel (from the
  // recorder's own `digitalWrite` log for DISP_BL_PWM, which is the line
  // `runDisplayInitialisation` raises).  Nothing here is told by the test
  // when a load arrived; it is read off what the image did.
  // =========================================================================
  bool physical_conversions = false;
  double ocv_V = 4.000;
  double display_sag_V = 0.0;
  double acc3v3_sag_V = 0.0;
  double acc5v_sag_V = 0.0;
  double gauge_error_V = +0.020;    // ADI 19-6171 Rev.7: +/-20 mV/cell
  struct LatchEvent { uint64_t t_us; uint16_t u3_output; };
  std::vector<LatchEvent> latch_events;
  uint32_t last_conversion_ms = 0;
  uint16_t conversions[4] = {0, 0, 0, 0};
  bool conversions_primed = false;

  static uint16_t quantise(double volts) {
    if (volts < 0.0) volts = 0.0;
    double counts = volts / double(Max17048Guard::kVcellLsbV);
    if (counts > 65535.0) counts = 65535.0;
    return uint16_t(counts);          // the part TRUNCATES to its own LSB
  }

  bool accessoryOnAt(uint64_t t_us, uint8_t bit) const {
    uint16_t latch = 0x0000;
    bool seen = false;
    for (const auto &e : latch_events) {
      if (e.t_us > t_us) break;
      latch = e.u3_output;
      seen = true;
    }
    if (!seen) return false;
    return Pcal9535a::bitOf(latch, bit);
  }

  static bool displayUpAt(uint64_t t_us) {
    bool up = false;
    for (const auto &w : aqroot_hal::recorder().digital_writes) {
      if (w.t_us > t_us) break;
      if (w.pin == AQROOT_PIN_DISP_BL_PWM) up = (w.value != LOW);
    }
    return up;
  }

  double nodeAt(uint64_t t_us) const {
    double v = ocv_V;
    if (displayUpAt(t_us)) v -= display_sag_V;
    if (accessoryOnAt(t_us, AQROOT_U3_ACC_3V3_EN)) v -= acc3v3_sag_V;
    if (accessoryOnAt(t_us, AQROOT_U3_ACC_5V_SW_EN)) v -= acc5v_sag_V;
    return v;
  }

  void advanceConversions() {
    if (!physical_conversions) return;
    const uint64_t now_us = aqroot_hal::recorder().clock_us;
    if (!conversions_primed) {
      conversions_primed = true;
      last_conversion_ms = uint32_t(now_us / 1000u);
      const uint16_t c = quantise(nodeAt(now_us) + gauge_error_V);
      for (uint16_t &x : conversions) x = c;
      vcell_counts = c;
      return;
    }
    uint64_t tick_us = uint64_t(last_conversion_ms) * 1000u;
    while (now_us >= tick_us + uint64_t(kGaugeVcellUpdateMs) * 1000u) {
      tick_us += uint64_t(kGaugeVcellUpdateMs) * 1000u;
      conversions[0] = conversions[1];
      conversions[1] = conversions[2];
      conversions[2] = conversions[3];
      conversions[3] = quantise(nodeAt(tick_us) + gauge_error_V);
    }
    last_conversion_ms = uint32_t(tick_us / 1000u);
    // The register is the AVERAGE of the four, and it is the average that is
    // stale -- not one sample of it.
    const uint32_t sum = uint32_t(conversions[0]) + conversions[1]
                       + conversions[2] + conversions[3];
    vcell_counts = uint16_t(sum / 4u);
  }

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
      if (reg == Pcal9535a::kRegOutput0) {
        out = value;
        // D-794 / R13-01: the latch history, so a conversion that happened
        // before this write sees the state that was there before it.
        if (address == AQROOT_EXP_U3_ADDR) {
          latch_events.push_back(
              {aqroot_hal::recorder().clock_us, u3_output});
        }
      }
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
        //
        // D-794 / R13-01: with `physical_conversions` set, the same sentence
        // is true of an AWAKE part for the first second after any load edge,
        // and that is the defect Round-13 reproduced.
        if (!asleep()) advanceConversions();
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
    return st25r3916(out);
  }

  // =========================================================================
  // D-794 / R13-03.  THE INDEPENDENTLY RETAINED ST25R3916.
  //
  // ROUND-13: "Add an independent retained-NFC peripheral stub to the real
  // production-image reset test: field active before MCU reset, U9 remains
  // powered, production setup must physically quiesce/verify before
  // permission."
  //
  // U9 is supplied from +3V3 and from ACC_5V's boost; an MCU reset touches
  // neither.  So this model, like the CC1101 above, is constructed BEFORE
  // `setup()` and is not owned by the image -- construction, which is what a
  // reset is, cannot clear it.  It starts with the Operation control register
  // holding `en | tx_en`: oscillator and regulators up, transmitter enabled.
  // That is a live 13.56 MHz carrier by DS12484 Rev 3 Table 21's own
  // definition, drawing continuously where the ledger charges 25 % duty.
  //
  // It leaves that state only when it is actually commanded to.  DS12484
  // section 4.4.1: Set default "puts the ST25R3916/7 in the same state as
  // power-up initialization", and section 4.2: "At power-on all its bits are
  // set to 0".  `ignores_set_default` is the negative control -- a part that
  // does not quiesce must leave the image refusing, not reporting success.
  //
  // `stop_all_activities_is_enough` is the OTHER negative control, and it is
  // the one R13-03 asks for by name ("Do not assume 'stop all activities' is
  // sufficient for every retained state").  With it false -- which is what
  // the datasheet describes -- C2/C3h clears the FIFO and the timers and
  // leaves Operation control ALONE, so an image that sent only that would
  // read back 0x88 and be refused.
  // =========================================================================
  uint16_t nfc_operation_control = 0x88;   // en | tx_en: the field is UP
  uint8_t nfc_ic_identity = 0x2A;          // DS12484 Table 117 default
  bool nfc_ignores_set_default = false;
  bool nfc_stop_all_activities_is_enough = false;
  int nfc_set_default_commands = 0;
  int nfc_stop_all_commands = 0;
  int nfc_operation_control_reads = 0;
  int nfc_operation_control_reads_while_field_up = 0;
  int nfc_overheat_frames = 0;
  bool nfcFieldIsUp() const { return (nfc_operation_control & 0x88) != 0; }

 private:
  uint8_t st25r3916(uint8_t out) {
    // DS12484 Rev 3 Table 11: the first two bits of the first byte are the
    // mode.  00 = register write, 01 = register read, 11 = direct command.
    if (nfc_pending_read_) {
      nfc_pending_read_ = false;
      if (nfc_read_addr_ == 0x02) {
        ++nfc_operation_control_reads;
        if (nfcFieldIsUp()) ++nfc_operation_control_reads_while_field_up;
        return uint8_t(nfc_operation_control);
      }
      // DS12484 Rev 3 Table 117: ic_type4..0 = 0b00101 and ic_rev2..0.
      // 0x2A is the documented power-up value; the probe asserts the
      // TYPE half and reports the revision.
      if (nfc_read_addr_ == 0x3F) return nfc_ic_identity;
      return 0x00;
    }
    if (nfc_pending_write_ > 0) {
      --nfc_pending_write_;
      if (nfc_write_addr_ == 0x02) nfc_operation_control = out;
      return 0x00;
    }
    if (nfc_overheat_bytes_ > 0) { --nfc_overheat_bytes_; return 0x00; }
    // DS12484 Rev 3 Table 13: FCh is the Test access direct command, "Enable
    // R/W access to Test register", and section 4.1 requires the three-byte
    // frame FCh / 04h / 10h after power-on AND after Set default.  It is
    // matched before the generic direct-command branch because its two
    // trailing bytes are a register write into the TEST space, not the
    // ordinary one.
    if (out == 0xFC) {
      ++nfc_overheat_frames;
      nfc_overheat_bytes_ = 2;
      return 0x00;
    }
    const uint8_t mode = uint8_t(out & 0xC0);
    if (mode == 0xC0) {                        // direct command
      if (out == 0xC0 || out == 0xC1) {        // Set default, section 4.4.1
        ++nfc_set_default_commands;
        if (!nfc_ignores_set_default) nfc_operation_control = 0x00;
        return 0x00;
      }
      if (out == 0xC2 || out == 0xC3) {        // Stop all activities, 4.4.2
        ++nfc_stop_all_commands;
        // Section 4.4.2 stops the FIFO, transmission/reception and the
        // timers.  It does NOT touch the Operation control register, so the
        // carrier keeps running -- unless this control says otherwise.
        if (nfc_stop_all_activities_is_enough) nfc_operation_control = 0x00;
        return 0x00;
      }
      return 0x00;
    }
    if (mode == 0x40) {                        // register read
      nfc_pending_read_ = true;
      nfc_read_addr_ = uint8_t(out & 0x3F);
      return 0x00;
    }
    if (mode == 0x00) {                        // register write
      nfc_pending_write_ = 1;
      nfc_write_addr_ = uint8_t(out & 0x3F);
      return 0x00;
    }
    return 0x00;
  }

  bool nfc_pending_read_ = false;
  uint8_t nfc_read_addr_ = 0;
  int nfc_pending_write_ = 0;
  uint8_t nfc_write_addr_ = 0;
  int nfc_overheat_bytes_ = 0;

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
    claim("...and the field really is still up", radio.nfcFieldIsUp());
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
          "arbiter", rec().consoleHas("NFC field is already drawing its "
                                      "burst"));
    press("x");
    pump(2);
    claim("...and so is an IR burst", rec().consoleCount(
        "NFC field is already drawing its burst") >= 2);
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
    claim("R13-03 control: Stop all activities alone does not clear the "
          "Operation control register, so the field survives it",
          radio.nfcFieldIsUp());
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
    for (int i = 0; i < 8 && radio.nfcFieldIsUp(); ++i) {
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

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
