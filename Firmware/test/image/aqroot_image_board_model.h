#pragma once
// AQROOT Demo -- D-801 / D801-01 + D801-07.  THE IMAGE-TEST BOARD MODEL, SHARED.
//
// Moved VERBATIM out of `test_production_image.cpp` at D-801 so that the
// FAP-01 first-article image test (`test_fap01_image.cpp`) drives the SAME
// physical-latch PCAL9535A / MAX17048 model and the SAME independently
// retained CC1101 / SX1262 / ST25R3916 stub as the release-image test.  A
// diagnostic image proved against a second, friendlier model would prove
// nothing about the rules it shares with the release image.
//
// Include it from exactly one translation unit per test binary, after the
// image's own `setup()` / `loop()` have been declared.

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "Arduino.h"
#include "SPI.h"
#include "Wire.h"

#include "aqroot_demo_board.h"
#include "max17048_guard.h"
#include "pcal9535a.h"

void setup();
void loop();

using namespace aqroot;

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

  // =========================================================================
  // D-795 / R14-01.  THE TIMING MODEL ROUND-14 SAID D-794's WAS NOT.
  //
  //   PERIOD.  `conversion_period_us` is 250 000 at the nominal time base and
  //   258 750 at tERR +3.5 %, the slow end ADI 19-6171 Rev.7 publishes.
  //
  //   PHASE.  `conversion_phase_us` places the part's own conversion grid
  //   anywhere relative to the image's clock; the tests SWEEP it, because the
  //   worst case is a conversion that completes just before the edge and a
  //   read that lands just before the next one.
  //
  //   APERTURE.  With `integrating_conversions` each conversion is the MEAN
  //   of the node over its whole period -- the conservative reading of "the
  //   average of four ADC conversions" -- so the conversion that is running
  //   when an edge lands integrates both sides of it.  Without it each
  //   conversion is an instantaneous sample at its completion, which is
  //   D-794's model.
  //
  //   EXTERNAL EVENTS.  `external_events` are node changes the FIRMWARE CANNOT
  //   SEE -- a charger unplugged, a pack sagging on its own -- modelled as an
  //   offset added from a given instant.  They exist for the unannounced
  //   source-change counterexample Astra reproduced.
  //
  // THE CONTAMINATION AUDIT.  Every VCELL read records whether any of the four
  // conversions in the average began before a node edge that precedes the
  // read.  Edges the FIRMWARE made (accessory latches, the panel) and edges it
  // could not see are counted separately, because the rule is different: no
  // read may be contaminated by the firmware's own edges, and no ADMISSION
  // read may be contaminated by anything.
  // =========================================================================
  uint64_t conversion_period_us = 250000;
  uint64_t conversion_phase_us = 0;
  bool integrating_conversions = false;
  struct ExternalEvent { uint64_t t_us; double offset_V; };
  std::vector<ExternalEvent> external_events;
  struct VcellRead {
    uint64_t t_us;
    uint16_t counts;
    bool firmware_edge_contaminated;
    bool external_edge_contaminated;
  };
  std::vector<VcellRead> vcell_reads;

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

  double externalOffsetAt(uint64_t t_us) const {
    double off = 0.0;
    for (const auto &e : external_events) {
      if (e.t_us > t_us) break;
      off = e.offset_V;
    }
    return off;
  }

  // The node as the FIRMWARE's own switching leaves it, and as everything
  // else does.
  double firmwareNodeAt(uint64_t t_us) const {
    double v = ocv_V;
    if (displayUpAt(t_us)) v -= display_sag_V;
    if (accessoryOnAt(t_us, AQROOT_U3_ACC_3V3_EN)) v -= acc3v3_sag_V;
    if (accessoryOnAt(t_us, AQROOT_U3_ACC_5V_SW_EN)) v -= acc5v_sag_V;
    return v;
  }
  double nodeAt(uint64_t t_us) const {
    return firmwareNodeAt(t_us) + externalOffsetAt(t_us);
  }

  double conversionValue(uint64_t end_us) const {
    if (!integrating_conversions) return nodeAt(end_us) + gauge_error_V;
    const uint64_t start_us =
        end_us > conversion_period_us ? end_us - conversion_period_us : 0;
    const int n = 64;
    double sum = 0.0;
    for (int i = 1; i <= n; ++i) {
      sum += nodeAt(start_us + (end_us - start_us) * uint64_t(i) / n);
    }
    return sum / n + gauge_error_V;
  }

  // Completion time of the k-th conversion on the part's own grid.
  uint64_t conversionEnd(int64_t k) const {
    const int64_t t = int64_t(conversion_phase_us)
                    + k * int64_t(conversion_period_us);
    return t < 0 ? 0 : uint64_t(t);
  }
  int64_t lastCompletedConversion(uint64_t now_us) const {
    if (now_us < conversion_phase_us) return -1;
    return int64_t((now_us - conversion_phase_us) / conversion_period_us);
  }

  // Candidate edge instants, of each kind, in (from, to].
  bool firmwareEdgeIn(uint64_t from, uint64_t to) const {
    auto changed = [this](uint64_t t) {
      return firmwareNodeAt(t) != firmwareNodeAt(t == 0 ? 0 : t - 1);
    };
    for (const auto &e : latch_events) {
      if (e.t_us > from && e.t_us <= to && changed(e.t_us)) return true;
    }
    for (const auto &w : aqroot_hal::recorder().digital_writes) {
      if (w.pin == AQROOT_PIN_DISP_BL_PWM && w.t_us > from && w.t_us <= to
          && changed(w.t_us)) {
        return true;
      }
    }
    return false;
  }
  bool externalEdgeIn(uint64_t from, uint64_t to) const {
    for (const auto &e : external_events) {
      if (e.t_us > from && e.t_us <= to
          && externalOffsetAt(e.t_us) != externalOffsetAt(e.t_us - 1)) {
        return true;
      }
    }
    return false;
  }

  void advanceConversions() {
    if (!physical_conversions) return;
    const uint64_t now_us = aqroot_hal::recorder().clock_us;
    const int64_t last = lastCompletedConversion(now_us);
    uint32_t sum = 0;
    for (int64_t k = last - 3; k <= last; ++k) {
      sum += quantise(conversionValue(conversionEnd(k)));
    }
    // The register is the AVERAGE of the four, and it is the average that is
    // stale -- not one sample of it.
    vcell_counts = uint16_t(sum / 4u);
  }

  // The earliest instant any conversion in the present average saw.
  uint64_t oldestApertureStart(uint64_t now_us) const {
    const uint64_t end = conversionEnd(lastCompletedConversion(now_us) - 3);
    if (!integrating_conversions) return end;
    return end > conversion_period_us ? end - conversion_period_us : 0;
  }

  void recordVcellRead() {
    const uint64_t now_us = aqroot_hal::recorder().clock_us;
    const uint64_t from = physical_conversions ? oldestApertureStart(now_us)
                                               : now_us;
    // A read is contaminated when an edge lies after the oldest aperture
    // start: some conversion in the average began on the pre-edge board.
    // (For an instantaneous sample an edge AT the sample instant is already
    // seen by it, hence `>` in the interval tests.)
    vcell_reads.push_back({now_us, vcell_counts,
                           physical_conversions && firmwareEdgeIn(from, now_us),
                           physical_conversions && externalEdgeIn(from, now_us)});
  }
  int firmwareContaminatedReads() const {
    int n = 0;
    for (const auto &r : vcell_reads) n += r.firmware_edge_contaminated;
    return n;
  }
  int externalContaminatedReads() const {
    int n = 0;
    for (const auto &r : vcell_reads) n += r.external_edge_contaminated;
    return n;
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
        recordVcellRead();
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

  // D-801 / D801-07.  THE BYTE ONLY REACHES A PART ON THE PINS IT IS WIRED TO.
  //
  // D-800 made `test/image/SPI.h` record which SCK the peripheral is really
  // bound to, but this model still answered every SPI-B frame whatever that
  // was -- so an image that quiesced the radios with the peripheral bound to
  // the SPI-A pins (a wrong pin map in `bringUpSpiBAndQuiesceRadios`, or a
  // previous SPI-A user that never called `SPI.end()`, so the pinned core
  // IGNORED the SPI-B `begin`) passed every claim.  On the board those bytes
  // clock out on GPIO12/11/13: U7/U8/U9 see their chip select fall and NO
  // CLOCK, and the MCU samples the SPI-A MISO line.  So a selected SPI-B part
  // now answers only while the peripheral is bound to the SPI-B pins; any
  // other binding is COUNTED and returns what an undriven MISO reads.
  int spi_b_wrong_pin_transfers = 0;
  // D-801 / D801-01: what the FAP-01 stimuli did to the parts.
  int stx_strobes = 0;
  int cc_register_writes = 0;
  uint8_t cc_regs[64] = {0};
  bool tx_cw = false;                // SX1262 continuous wave keyed
  int cw_commands = 0;
  std::vector<uint8_t> sx_opcodes;
  // D-801 / D801-07: how long SO stays HIGH after an SRES strobe (0 = the
  // idealised part the pre-D-801 scenarios use).  While it is high the part
  // is still resetting: it ignores every byte and MISO reads all-ones.
  uint64_t so_busy_after_sres_us = 0;

  uint8_t transfer(uint8_t out) override {
    auto &r = aqroot_hal::recorder();
    const bool cc = r.pin_low[AQROOT_PIN_CC1101_CS_N];
    const bool sx = r.pin_low[AQROOT_PIN_SX1262_CS_N];
    const bool nfc = r.pin_low[AQROOT_PIN_NFC_CS_N];
    if ((cc || sx || nfc) && r.spi_bound_sck != AQROOT_PIN_SPI_B_SCK) {
      ++spi_b_wrong_pin_transfers;
      return 0xFF;
    }
    if (cc) {
      if (r.clock_us < cc_resetting_until_us_) return 0xFF;
      return cc1101(out);
    }
    if (sx) return sx1262(out);
    // D-795 / R14-02: U9 answers only inside ITS OWN chip-select frame, and a
    // new frame resets its SPI state machine -- which is what keeps a display
    // or microSD transfer on another select from being parsed as NFC traffic.
    if (!r.pin_low[AQROOT_PIN_NFC_CS_N]) return 0xFF;
    if (r.low_edges[AQROOT_PIN_NFC_CS_N] != nfc_frame_) {
      nfc_frame_ = r.low_edges[AQROOT_PIN_NFC_CS_N];
      nfc_pending_read_ = false;
      nfc_pending_write_ = 0;
      nfc_overheat_bytes_ = 0;
    }
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
  // ---- D-795 / R14-02.  THE BUS FAULTS A SAFE-LOOKING VALUE CAN HIDE. ----
  //
  // Each is a physical condition in which the part is NOT answering, and in
  // which D-794 could still read 0x00 back from 02h and call the field off.
  // The retained field itself is untouched by every one of them: a dead read
  // path says nothing about the carrier.
  bool nfc_zero_fill = false;       // MISO reads 0x00 on every byte
  bool nfc_ff_fill = false;         // MISO reads 0xFF on every byte
  bool nfc_stale_reply = false;     // every read returns the PREVIOUS read's value
  bool nfc_ignores_writes = false;  // register writes do not land
  // Operation control that will not clear: neither Set default nor a direct
  // 02h write moves it, while every other register behaves.
  bool nfc_opcontrol_sticky = false;
  // The part answers until it receives Set default and is DEAD after it --
  // a brown-out mid-sequence.  Every later read is zero, which is exactly the
  // "safe-looking" value D-794 accepted.
  bool nfc_dies_after_set_default = false;
  bool nfc_dead_ = false;
  // D-796 / C-NFC-QUIESCE-01.  The part stops answering at a CHOSEN INSTANT
  // of recorded time -- a lifted NFC_CS_N, a brown-out -- so a test can put
  // the loss at the worst phase of whatever the image is doing then: inside
  // the gauge window, inside the settled recheck, just after a probe.
  uint64_t nfc_dead_from_us = ~uint64_t(0);
  uint8_t nfc_regs[64] = {0};       // register space A
  int nfc_set_default_commands = 0;
  int nfc_stop_all_commands = 0;
  int nfc_operation_control_reads = 0;
  int nfc_operation_control_reads_while_field_up = 0;
  int nfc_overheat_frames = 0;
  int nfc_identity_reads = 0;
  int nfc_challenge_writes = 0;
  int nfc_operation_control_zero_writes = 0;
  bool nfcFieldIsUp() const { return (nfc_operation_control & 0x88) != 0; }

 private:
  uint8_t nfcRead(uint8_t addr) {
    if (addr == 0x02) return uint8_t(nfc_operation_control);
    if (addr == 0x3F) return nfc_ic_identity;
    return nfc_regs[addr & 0x3F];
  }
  uint8_t st25r3916(uint8_t out) {
    // DS12484 Rev 3 Table 11: the first two bits of the first byte are the
    // mode.  00 = register write, 01 = register read, 11 = direct command.
    const bool dead = nfc_zero_fill || nfc_ff_fill || nfc_dead_
                   || aqroot_hal::recorder().clock_us >= nfc_dead_from_us;
    const uint8_t idle = nfc_ff_fill ? 0xFF : 0x00;
    if (nfc_pending_read_) {
      nfc_pending_read_ = false;
      if (dead) return idle;
      if (nfc_read_addr_ == 0x02) {
        ++nfc_operation_control_reads;
        if (nfcFieldIsUp()) ++nfc_operation_control_reads_while_field_up;
      }
      if (nfc_read_addr_ == 0x3F) ++nfc_identity_reads;
      const uint8_t now = nfcRead(nfc_read_addr_);
      if (nfc_stale_reply) {
        const uint8_t prev = nfc_last_read_value_;
        nfc_last_read_value_ = now;
        return prev;
      }
      nfc_last_read_value_ = now;
      return now;
    }
    if (nfc_pending_write_ > 0) {
      --nfc_pending_write_;
      if (dead || nfc_ignores_writes) return idle;
      if (nfc_write_addr_ == 0x02) {
        if (nfc_opcontrol_sticky) return 0x00;
        nfc_operation_control = out;
        if (out == 0x00) ++nfc_operation_control_zero_writes;
      } else {
        if (nfc_write_addr_ == 0x11) ++nfc_challenge_writes;
        nfc_regs[nfc_write_addr_ & 0x3F] = out;
      }
      return 0x00;
    }
    if (nfc_overheat_bytes_ > 0) { --nfc_overheat_bytes_; return idle; }
    if (dead) return idle;
    // DS12484 Rev 3 Table 13: FCh is the Test access direct command, "Enable
    // R/W access to Test register", and section 4.1 requires the three-byte
    // frame FCh / 04h / 10h after power-on AND after Set default.
    if (out == 0xFC) {
      ++nfc_overheat_frames;
      nfc_overheat_bytes_ = 2;
      return 0x00;
    }
    const uint8_t mode = uint8_t(out & 0xC0);
    if (mode == 0xC0) {                        // direct command
      if (out == 0xC0 || out == 0xC1) {        // Set default, section 4.4.1
        ++nfc_set_default_commands;
        if (!nfc_ignores_set_default) {
          // "resets all registers to their default state"
          if (!nfc_opcontrol_sticky) nfc_operation_control = 0x00;
          for (uint8_t &r : nfc_regs) r = 0x00;
        }
        if (nfc_dies_after_set_default) nfc_dead_ = true;
        return 0x00;
      }
      if (out == 0xC2 || out == 0xC3) {        // Stop all activities, 4.4.2
        ++nfc_stop_all_commands;
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

  uint32_t nfc_frame_ = 0;
  bool nfc_pending_read_ = false;
  uint8_t nfc_read_addr_ = 0;
  uint8_t nfc_last_read_value_ = 0x00;
  int nfc_pending_write_ = 0;
  uint8_t nfc_write_addr_ = 0;
  int nfc_overheat_bytes_ = 0;

  uint8_t cc1101(uint8_t out) {
    // D-801 / D801-01: a single register write's DATA byte (header R/W and
    // BURST clear, address < 0x30, or PATABLE 0x3E) is data, never a strobe
    // -- TEST1 = 0x35 must not read as STX.
    if (cc_pending_write_) {
      cc_pending_write_ = false;
      cc_regs[cc_write_addr_ & 0x3F] = out;
      ++cc_register_writes;
      return 0x0F;
    }
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
      if (so_busy_after_sres_us > 0) {
        auto &r = aqroot_hal::recorder();
        cc_resetting_until_us_ = r.clock_us + so_busy_after_sres_us;
        r.pin_high_until_us[AQROOT_PIN_SPI_B_MISO] = cc_resetting_until_us_;
      }
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
    // D-801 / D801-01: STX keys the part -- the FAP-01 continuous TX.
    if (out == 0x35) {
      ++stx_strobes;
      if (!ignores_strobes) transmitting = true;
      return 0x00;
    }
    if (((out & 0xC0) == 0x00 && (out & 0x3F) < 0x30) || out == 0x3E) {
      cc_pending_write_ = true;
      cc_write_addr_ = uint8_t(out & 0x3F);
      return 0x0F;
    }
    return 0x00;
  }

  uint8_t sx1262(uint8_t out) {
    // D-801 / D801-01: the OPCODE is the first byte of a chip-select frame.
    // SetTxContinuousWave (D1h) keys the PA; SetStandby (80h) drops it.
    const auto &rr = aqroot_hal::recorder();
    const bool first = rr.low_edges[AQROOT_PIN_SX1262_CS_N] != sx_frame_;
    if (first) sx_frame_ = rr.low_edges[AQROOT_PIN_SX1262_CS_N];
    if (first && out == 0xD1) {
      ++cw_commands;
      if (!ignores_strobes) tx_cw = true;
      return sx_status_();
    }
    if (first && out == 0x80) tx_cw = false;
    if (first) sx_opcodes.push_back(out);
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
    if (tx_cw) return uint8_t(0x06 << 4);    // D-801: chip mode TX
    if (!sx1262_answers_standby || !standby_) return uint8_t(0x00 << 4);
    return uint8_t(0x02 << 4);               // STBY_RC
  }

  uint64_t cc_resetting_until_us_ = 0;
  bool cc_pending_write_ = false;
  uint8_t cc_write_addr_ = 0;
  uint32_t sx_frame_ = 0;
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
inline void rig(const char *keys = "") {
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
inline void rigWithRetainedRadio(Cc1101Stub &radio, const char *keys = "") {
  rig(keys);
  g_radio = &radio;
  aqroot_hal::spiModel() = &radio;
}

inline void press(const char *keys) {
  auto &r = aqroot_hal::recorder();
  r.serial_in = keys;
  r.serial_in_pos = 0;
}

inline void pump(int iterations) {
  for (int i = 0; i < iterations; ++i) loop();
}

inline const aqroot_hal::Recorder &rec() { return aqroot_hal::recorder(); }

inline bool bit(uint16_t latch, uint8_t b) { return Pcal9535a::bitOf(latch, b); }

}  // namespace
