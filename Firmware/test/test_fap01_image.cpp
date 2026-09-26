// AQROOT Demo -- D-801 / D801-01.  THE FAP-01 FIRST-ARTICLE IMAGE, RUN ON THE
// HOST -- AND THE RELEASE IMAGE, RUN WITH THE SAME KEYS.
//
// ROUND-20 (Astra R20-01): "Add positive tests proving each required FAP
// stimulus is reachable in FAP-01 and negative tests proving production image
// continues to refuse forbidden states."
//
// ONE FILE, TWO BUILDS.  `checks/firmware_hw_map_contract.py` H6 compiles it
// twice against the unmodified `src/demo/main.cpp` and the physical-latch
// board model in `test/image/aqroot_image_board_model.h`:
//
//   -DAQROOT_FAP01_DIAGNOSTIC -DAQROOT_TEST_EXPECT_FAP01   + src/fap01/*.cpp
//        every stimulus the first-article plan needs is REACHABLE, keyed only
//        through the release image's own authority, refused where that
//        authority refuses, BOUNDED, and QUIESCED on stop;
//
//   -DAQROOT_TEST_EXPECT_PRODUCTION                        (release sources)
//        every FAP-01 key is typed into the release image and NOTHING
//        happens: no carrier, no field, no Wi-Fi, no chip-select hold-off, no
//        held duty, no poll -- and the release image still grants a rail
//        afterwards, so nothing was left keyed.
//
// The release-image test (`test_production_image.cpp`) is ALSO run against
// the FAP-01 build by H6, which is what proves FAP-01 weakens none of the
// release rules it shares.
//
//   g++ -std=c++17 -DARDUINO=200 -DAQROOT_FAP01_DIAGNOSTIC
//       -DAQROOT_TEST_EXPECT_FAP01 -I test/image -I src/hw -I src
//       test/test_fap01_image.cpp src/demo/main.cpp src/fap01/aqroot_fap01.cpp
//       test/image/image_main.cpp

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "Arduino.h"
#include "Preferences.h"
#include "SPI.h"
#include "WiFi.h"
#include "Wire.h"

#include "aqroot_demo_board.h"
#include "aqroot_demo_bringup_app.h"
#include "aqroot_demo_expanders.h"
#include "aqroot_demo_radios.h"
#include "aqroot_spi_bus_b.h"
#include "max17048_guard.h"
#include "pcal9535a.h"

#if defined(AQROOT_TEST_EXPECT_FAP01) == defined(AQROOT_TEST_EXPECT_PRODUCTION)
#error "build this test with exactly one of AQROOT_TEST_EXPECT_FAP01 / AQROOT_TEST_EXPECT_PRODUCTION"
#endif
#if defined(AQROOT_TEST_EXPECT_FAP01)
#include "fap01/aqroot_fap01.h"
#endif

using namespace aqroot;

void setup();
void loop();
aqroot::SpiBusB &aqrootHostImageSpiB();
bool aqrootHostImageWifiTold();

static int failures = 0;
static void claim(const char *name, bool ok) {
  std::printf("[%s] %s\n", ok ? "PASS" : "FAIL", name);
  if (!ok) ++failures;
}

#include "aqroot_image_board_model.h"

namespace {

// THE HOST IS NOT AN MCU RESET.  `rig()` rebuilds the board model and the
// recorder, but the image's own statics (`g_spi_b`, `g_app`) outlive it on
// the host where silicon would lose them.  So a simulated MCU reset first
// forgets what the SPI-B arbiter believed was keyed -- exactly what
// construction does on the board -- and leaves the PARTS (the retained stub)
// as they are.
inline void mcuReset(const char *keys = "") {
  SpiBusB &b = aqrootHostImageSpiB();
  if (b.selected() != SpiBDevice::None) b.release();
  if (b.transmitting() != SpiBDevice::None) b.endTransmit(b.transmitting());
  rig(keys);
}

// A fresh board AND a fresh non-volatile store and radio model -- a POWER
// cycle.  In the FAP-01 build every stimulus the previous scenario left
// running is stopped first, through the image, so no session or intent
// survives into the next scenario on the host's persistent statics.
inline void coldBoot(const char *keys = "") {
#if defined(AQROOT_TEST_EXPECT_FAP01)
  press("Q");
  loop();
  press("");
#endif
  mcuReset(keys);
  aqroot_hal::wifi().reset();
  aqroot_hal::nvs().clear();
  aqroot_hal::nvsWrites() = 0;
  setup();
  pump(3);
}

inline bool rail3() { return bit(g_board.u3_output, AQROOT_U3_ACC_3V3_EN); }
inline bool rail5() { return bit(g_board.u3_output, AQROOT_U3_ACC_5V_SW_EN); }
inline bool ampOn() { return bit(g_board.u2_output, AQROOT_U2_AMP_SD_MODE); }

// Press `keys` and run exactly one loop() per key.
inline void keys(const char *k) {
  press(k);
  pump(int(std::strlen(k)));
  press("");
}

// Run the loop for `ms` of recorded time in `step` slices.
inline void runFor(uint32_t ms, uint32_t step = 50) {
  for (uint32_t t = 0; t < ms; t += step) {
    delay(step);
    loop();
  }
}

// The recorded time of the first console line at or after `from` that
// contains `needle`, or ~0.
inline uint64_t lineTime(const char *needle, size_t from = 0) {
  const auto &r = rec();
  for (size_t i = from; i < r.console.size(); ++i) {
    if (r.console[i].find(needle) != std::string::npos) return r.console_t_us[i];
  }
  return ~uint64_t(0);
}
inline bool hasFrom(const char *needle, size_t from) {
  return lineTime(needle, from) != ~uint64_t(0);
}

}  // namespace

int main() {
#if defined(AQROOT_TEST_EXPECT_FAP01)
  // =========================================================================
  // THE BANNER, AND THE RELEASE GATE STILL WIRED.
  // =========================================================================
  coldBoot();
  claim("FAP-01: the image announces itself as the first-article DIAGNOSTIC "
        "image, never shipped, never a default",
        rec().consoleHas("FAP-01 FIRST-ARTICLE DIAGNOSTIC IMAGE -- NEVER SHIP"));
  claim("FAP-01: ...and the release SPI-B transmit gate is still wired to the "
        "accessory permission table",
        rec().consoleHas("[PASS] SPI-B sub-GHz transmit gate wired"));

  // =========================================================================
  // C -- CC1101 CONTINUOUS TX (C-RADIO-QUIESCE-01, C-MCU-01 by difference).
  // =========================================================================
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    claim("C: the boot quiesce left the CC1101 idle before the key",
          !radio.transmitting && radio.stx_strobes == 0);
    keys("C");
    claim("C: the key KEYS the CC1101 -- STX strobed, random-TX infinite "
          "length, PATABLE 0xC0, MARCSTATE confirmed TX",
          radio.transmitting && radio.stx_strobes == 1
          && radio.cc_regs[0x08] == 0x22 && radio.cc_regs[0x3E] == 0xC0
          && rec().consoleHas("CC1101 continuous TX KEYED"));
    claim("C: ...through SpiBusB::beginTransmit -- the bus records U7 as the "
          "keyed transmitter",
          aqrootHostImageSpiB().transmitting() == SpiBDevice::Cc1101);
    keys("3");
    claim("C: ...so the release permission table refuses ACC_3V3 while it is "
          "keyed (sub-GHz TX has no rail row)",
          rec().consoleHas("ACC_3V3_SW REFUSED") && !rail3());
    keys("L");
    claim("C: ...and a second transmitter is refused (one TX at a time)",
          !radio.tx_cw && rec().consoleHas("SX1262 CW REFUSED"));
    keys("C");
    claim("C: the same key STOPS it with the release quiesce (SIDLE/SRES, "
          "MARCSTATE IDLE) and releases the transmit slot",
          !radio.transmitting && radio.sres_strobes >= 2
          && aqrootHostImageSpiB().transmitting() == SpiBDevice::None
          && rec().consoleHas("CC1101 continuous TX STOPPED (operator key)")
          && rec().consoleHas("IDLE, quiesced"));
  }
  {
    coldBoot();
    keys("C");
    const uint64_t keyed = lineTime("CC1101 continuous TX KEYED");
    runFor(35000, 500);
    const uint64_t stopped = lineTime("CC1101 continuous TX STOPPED (30000 ms bound)");
    claim("C: an unattended carrier is STOPPED at its 30 s bound and the part "
          "is quiesced",
          !g_radio->transmitting && stopped != ~uint64_t(0)
          && stopped - keyed <= 31000000u
          && aqrootHostImageSpiB().transmitting() == SpiBDevice::None);
  }
  {
    coldBoot();
    keys("3");
    const int stx = g_radio->stx_strobes;
    claim("C: (setup) ACC_3V3 is live", rail3());
    keys("C");
    claim("C: with an accessory rail live the key is REFUSED by the release "
          "gate and the CC1101 is never strobed into TX",
          g_radio->stx_strobes == stx && !g_radio->transmitting
          && rec().consoleHas("CC1101 TX REFUSED by SpiBusB::beginTransmit"));
  }

  // =========================================================================
  // L -- SX1262 CW AT +22 dBm (C-MCU-01, C-RADIO-QUIESCE-01's SX1262 case).
  // =========================================================================
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    keys("L");
    auto sent = [&radio](uint8_t op) {
      for (uint8_t o : radio.sx_opcodes) if (o == op) return true;
      return false;
    };
    claim("L: the key keys SX1262 CW -- TCXO on DIO3, DIO2 RF switch, PA "
          "config, TX params, SetTxContinuousWave, chip mode confirmed TX",
          radio.tx_cw && radio.cw_commands == 1 && sent(0x97) && sent(0x9D)
          && sent(0x95) && sent(0x8E)
          && aqrootHostImageSpiB().transmitting() == SpiBDevice::Sx1262
          && rec().consoleHas("SX1262 CW KEYED"));
    keys("L");
    claim("L: the same key stops it with the release quiesce (SetStandby, "
          "STANDBY confirmed)",
          !radio.tx_cw && aqrootHostImageSpiB().transmitting() == SpiBDevice::None
          && rec().consoleHas("STANDBY, quiesced"));
    keys("L");
    runFor(35000, 500);
    claim("L: an unattended CW is STOPPED at its 30 s bound",
          !radio.tx_cw && rec().consoleHas("SX1262 CW STOPPED (30000 ms bound)"));
  }

  // =========================================================================
  // N / T -- THE NFC FIELD, THROUGH A FIELD SESSION (C-NFC-TUNE-01,
  // C-NFC-QUIESCE-01).
  // =========================================================================
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    claim("N: (setup) the boot quiesce proved the field off",
          !radio.nfcFieldIsUp()
          && rec().consoleHas("FIELD OFF, live identity"));
    keys("N");
    claim("N: the key turns the field ON (Operation control 0xC8) through a "
          "field session that owns the SPI-B transmit slot",
          radio.nfcFieldIsUp() && radio.nfc_operation_control == 0xC8
          && aqrootHostImageSpiB().transmitting() == SpiBDevice::St25r3916
          && rec().consoleHas("NFC field ON"));
    const int challenges = radio.nfc_challenge_writes;
    runFor(2000, 100);
    claim("N: ...and while the session owns U9 the liveness probe stands down "
          "(no 11h challenge under the field)",
          radio.nfc_challenge_writes == challenges && radio.nfcFieldIsUp());
    keys("T");
    claim("T: a REQA is sent while the field is on (report only)",
          rec().consoleHas("REQA sent"));
    const size_t mark = rec().console.size();
    keys("N");
    runFor(600, 50);
    claim("N: the same key turns the field OFF, ends the session, and the "
          "release quiesce retry re-proves it OFF from a live part",
          !radio.nfcFieldIsUp()
          && aqrootHostImageSpiB().transmitting() == SpiBDevice::None
          && hasFrom("NFC field OFF (operator key)", mark)
          && hasFrom("FIELD OFF, live identity", mark));
    keys("T");
    claim("T: without a field the REQA is refused",
          rec().consoleHas("REQA REFUSED: the NFC field is off"));
    keys("N");
    runFor(65000, 500);
    claim("N: an unattended field is turned OFF at its 60 s bound",
          !radio.nfcFieldIsUp()
          && rec().consoleHas("NFC field OFF (60000 ms bound)"));
  }
  {
    coldBoot();
    keys("3");
    keys("N");
    claim("N: with an accessory rail live the release session gate REFUSES "
          "the field by name",
          !g_radio->nfcFieldIsUp()
          && rec().consoleHas("NFC field session REFUSED: an accessory rail "
                              "is live"));
  }

  // =========================================================================
  // D-802 / D802-01 (Round-21 R21-01) -- THE SUPPLY MODE BEFORE THE
  // REGULATORS.  The model judges every `en` write and every Adjust
  // regulators command against the supply the BOM population gives U9
  // (R106 FIT / R107 DNP -> +3V3 -> sup3V = 1), passed in by H6 from the fab
  // BOM, not from the image's own constant.
  // =========================================================================
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    const int adjust0 = radio.nfc_adjust_regulators;
    const int en0 = radio.nfc_en_writes;
    keys("N");
    claim("N/sup3V: the field start writes and reads back sup3V BEFORE `en` "
          "and Adjust regulators -- the supply mode the R106 FIT / R107 DNP "
          "population gives U9 (DS12484 Table 20); no regulator is enabled or "
          "adjusted in the wrong mode",
          radio.nfcFieldIsUp() && radio.nfc_en_writes > en0
          && radio.nfc_adjust_regulators == adjust0 + 1
          && radio.nfc_en_in_wrong_supply_mode == 0
          && radio.nfc_adjust_in_wrong_supply_mode == 0
          && rec().consoleHas("IO configuration 2 0x80: sup3V"));
    keys("N");
    runFor(1500, 50);
    claim("N/sup3V: (setup) the release quiesce retry's Set default between "
          "sessions returned U9 to its default 5 V mode (sup3V = 0)",
          !radio.nfcFieldIsUp() && (radio.nfc_regs[0x01] & 0x80) == 0
          && radio.nfc_set_default_commands > 0);
    keys("N");
    claim("N/sup3V: ...and the NEXT field start after that Set default writes "
          "sup3V again before `en` and Adjust regulators",
          radio.nfcFieldIsUp() && radio.nfc_adjust_regulators == adjust0 + 2
          && radio.nfc_en_in_wrong_supply_mode == 0
          && radio.nfc_adjust_in_wrong_supply_mode == 0);
    keys("N");
  }
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    radio.nfc_io2_stuck = true;
    const int en0 = radio.nfc_en_writes;
    const int adjust0 = radio.nfc_adjust_regulators;
    keys("N");
    runFor(600, 50);
    claim("N/sup3V: if sup3V does not read back the field is REFUSED and the "
          "regulators are never enabled or adjusted",
          !radio.nfcFieldIsUp() && radio.nfc_en_writes == en0
          && radio.nfc_adjust_regulators == adjust0
          && rec().consoleHas("NFC field REFUSED -- IO configuration 2 reads "
                              "0x00, want 0x80"));
    radio.nfc_io2_stuck = false;
  }

  // =========================================================================
  // D-802 / D802-03 (Round-21 R21-03) -- A REQA ANSWER ONLY FROM FRESH,
  // VALIDATED EVIDENCE.  One valid answer; then every fault Round-21 used
  // and the ones next to it.  None may print "a tag answered", and a fault
  // may not print "no tag answered" either -- that is also a finding.
  // =========================================================================
  {
    coldBoot();
    Cc1101Stub &radio = *g_radio;
    radio.nfc_tag_present = true;
    keys("N");
    size_t mark = rec().console.size();
    keys("T");
    claim("T/valid: with a tag in the field the REQA reports a VALID ANSWER -- "
          "ATQA 04 00 from a FIFO cleared first, I_txe + I_rxe, exactly two "
          "bytes, drained",
          hasFrom("REQA -- VALID ANSWER: a tag answered, ATQA 04 00", mark)
          && radio.nfc_clear_fifo_commands >= 1 && radio.nfc_reqa_commands == 1
          && radio.nfc_fifo.empty());
    radio.nfc_tag_present = false;
    mark = rec().console.size();
    keys("T");
    claim("T/valid: the tag removed, the next REQA reports no tag -- the "
          "previous ATQA is not re-read",
          hasFrom("REQA -- no tag answered", mark)
          && !hasFrom("a tag answered", mark));
    radio.nfcSetFifo({0x04, 0x00});
    mark = rec().console.size();
    keys("T");
    claim("T/stale: an ATQA left in the FIFO from before the REQA is CLEARED "
          "first and never reported as an answer",
          hasFrom("REQA -- no tag answered", mark)
          && !hasFrom("a tag answered", mark));
    radio.nfc_ignores_commands = true;
    radio.nfcSetFifo({0x04, 0x00});
    mark = rec().console.size();
    keys("T");
    claim("T/ignored: a part that ignores direct commands with a stale FIFO "
          "count of 2 gives NO VALID EVIDENCE (Clear FIFO not confirmed)",
          hasFrom("NO VALID EVIDENCE: Clear FIFO NOT CONFIRMED", mark)
          && !hasFrom("a tag answered", mark)
          && !hasFrom("no tag answered", mark));
    radio.nfcSetFifo({});
    mark = rec().console.size();
    keys("T");
    claim("T/ignored: a part that ignores the REQA itself (FIFO already empty) "
          "gives NO VALID EVIDENCE -- not 'no tag answered'",
          hasFrom("NO VALID EVIDENCE: no end-of-transmission IRQ", mark)
          && !hasFrom("no tag answered", mark));
    radio.nfc_ignores_commands = false;
    radio.nfc_ff_fill = true;
    mark = rec().console.size();
    keys("T");
    claim("T/all-ones: an all-FF bus (FIFO 255, ATQA FF FF) gives NO VALID "
          "EVIDENCE",
          hasFrom("REQA -- NO VALID EVIDENCE", mark)
          && !hasFrom("a tag answered", mark)
          && !hasFrom("no tag answered", mark));
    radio.nfc_ff_fill = false;
    radio.nfc_zero_fill = true;
    mark = rec().console.size();
    keys("T");
    claim("T/all-zero: an all-zero bus gives NO VALID EVIDENCE -- not 'no tag "
          "answered'",
          hasFrom("REQA -- NO VALID EVIDENCE", mark)
          && !hasFrom("no tag answered", mark));
    radio.nfc_zero_fill = false;
    radio.nfc_tag_present = true;
    radio.nfc_tag_atqa[0] = 0xFF;
    radio.nfc_tag_atqa[1] = 0xFF;
    mark = rec().console.size();
    keys("T");
    claim("T/implausible: a two-byte receive of FF FF (ISO/IEC 14443-3 RFU "
          "bits set) gives NO VALID EVIDENCE",
          hasFrom("NO VALID EVIDENCE: the ATQA fails ISO/IEC 14443-3", mark)
          && !hasFrom("a tag answered", mark));
    radio.nfc_tag_atqa[0] = 0x04;
    radio.nfc_tag_atqa[1] = 0x00;
    aqrootHostImageSpiB().select(SpiBDevice::Sx1262);
    mark = rec().console.size();
    keys("T");
    aqrootHostImageSpiB().release();
    claim("T/transfer: a U9 transfer that cannot take the bus gives NO VALID "
          "EVIDENCE",
          hasFrom("NO VALID EVIDENCE: an SPI-B transfer on U9 did not complete",
                  mark)
          && !hasFrom("a tag answered", mark));
    keys("J");
    mark = rec().console.size();
    const int reqa0 = radio.nfc_reqa_commands;
    keys("T");
    claim("T/chip-select: with a U9 hold-off armed the REQA is REFUSED -- no "
          "transaction whose select may be held high is evidence",
          hasFrom("REQA REFUSED: a U9 NFC_CS_N hold-off is armed", mark)
          && radio.nfc_reqa_commands == reqa0
          && !hasFrom("a tag answered", mark));
    keys("J");
    keys("K");
    mark = rec().console.size();
    keys("T");
    claim("T/chip-select: ...and so while a DELAYED hold-off is pending",
          hasFrom("REQA REFUSED: a U9 NFC_CS_N hold-off is armed", mark)
          && !hasFrom("a tag answered", mark));
    keys("Q");
  }

  // =========================================================================
  // V / W -- THE Wi-Fi BURST (C-MCU-01).
  // =========================================================================
  {
    coldBoot();
    keys("W");
    claim("W: without the bench-source declaration the burst is REFUSED",
          aqroot_hal::wifi().sta_starts == 0
          && rec().consoleHas("bench source is not declared"));
    keys("VW");
    runFor(500, 50);
    claim("W: after V, with both rails off and nothing keyed, the burst runs "
          "-- the radio is started and frames are transmitted",
          aqroot_hal::wifi().sta_starts == 1 && aqroot_hal::wifi().frames > 0
          && aqroot_hal::wifi().current_mode == WIFI_MODE_STA);
    claim("W: ...having ASKED the release permission table's Wi-Fi row, which "
          "refused, and waived ONLY its no-rail charging refusal",
          rec().consoleHas("Wi-Fi / BLE radio REFUSED: no reported cell "
                           "excludes an absorbing charger supplement")
          && rec().consoleHas("DIAGNOSTIC WAIVER of the no-rail CHARGING row "
                              "only"));
    keys("3");
    claim("W: ...and the Wi-Fi mode is TOLD to the permission table, and a rail "
          "enable during the burst is REFUSED",
          aqrootHostImageWifiTold() && !rail3()
          && rec().consoleHas("'3' REFUSED -- the Wi-Fi burst session is "
                              "EXCLUSIVE"));
    runFor(11000, 250);
    const auto &w = aqroot_hal::wifi();
    claim("W: an unattended burst is STOPPED at its 10 s bound and the radio "
          "turned off",
          w.current_mode == WIFI_MODE_NULL && w.off_calls >= 1
          && w.last_off_us - w.first_on_us <= 10600000u
          && rec().consoleHas("Wi-Fi burst STOPPED (10000 ms bound)"));
    keys("VW");
    claim("W: a second burst inside the 30 s cool-down is REFUSED",
          aqroot_hal::wifi().sta_starts == 1
          && rec().consoleHas("cool-down"));
  }
  {
    coldBoot();
    keys("3");
    claim("W: (setup) ACC_3V3 is live", rail3());
    keys("VW");
    claim("W: with an accessory rail live the burst is REFUSED and the radio "
          "never starts -- a rail-live Wi-Fi row is never waived",
          aqroot_hal::wifi().sta_starts == 0 && aqroot_hal::wifi().frames == 0
          && rec().consoleHas("never waived"));
  }
  {
    coldBoot();
    keys("CVW");
    claim("W: with a sub-GHz transmitter keyed the burst is REFUSED (one "
          "transmitter at a time)",
          aqroot_hal::wifi().sta_starts == 0
          && rec().consoleHas("Wi-Fi burst REFUSED: a sub-GHz transmitter"));
  }

  // =========================================================================
  // D-802 / D802-02 (Round-21 R21-02) -- THE Wi-Fi SESSION IS EXCLUSIVE FOR
  // ITS WHOLE LIFE.  Round-21 reproduced V-W-I and V-W-x: the IR burst ran
  // beside the waived radio.  Every key is refused while it runs except W,
  // Q, ? and s; stopping it (W, Q, the bound) ends the exclusion at once.
  // =========================================================================
  {
    coldBoot();
    keys("VW");
    runFor(300, 50);
    size_t mark = rec().console.size();
    size_t pwm0 = rec().pwm.size();
    keys("I");
    claim("W+I: with the Wi-Fi session running, I (the FAP-01 IR burst) is "
          "REFUSED and no carrier is driven",
          rec().pwm.size() == pwm0 && !hasFrom("IR 10 NEC frames", mark)
          && hasFrom("'I' REFUSED -- the Wi-Fi burst session is EXCLUSIVE",
                     mark));
    mark = rec().console.size();
    keys("x");
    claim("W+x: ...and so is the release IR self-test x",
          rec().pwm.size() == pwm0 && !hasFrom("IR  ", mark)
          && hasFrom("'x' REFUSED -- the Wi-Fi burst session is EXCLUSIVE",
                     mark));
    mark = rec().console.size();
    const int installs = rec().i2s_installs;
    keys("dpmtl35iACLNGBHJKYrgbwoVT");
    runFor(300, 50);
    claim("W+*: ...and EVERY other key -- microSD, display, microphone, tone, "
          "backlight ramp, both rails, the accessory buffer, held audio, both "
          "sub-GHz transmitters, the NFC field, the VCELL poll, the held "
          "backlight, every hold-off, the RGB LED, V and T -- is refused and "
          "changes nothing while the radio stays up",
          rec().consoleCount("REFUSED -- the Wi-Fi burst session is EXCLUSIVE")
              >= 25
          && rec().pwm.size() == pwm0 && rec().i2s_installs == installs
          && !rail3() && !rail5() && !ampOn() && !g_radio->transmitting
          && !g_radio->tx_cw && !g_radio->nfcFieldIsUp()
          && !hasFrom("hold-off ARMED", mark) && !hasFrom("vcell t_ms=", mark)
          && !hasFrom("microSD  CMD0", mark) && !hasFrom("display: pulsing", mark)
          && aqroot_hal::wifi().current_mode == WIFI_MODE_STA);
    mark = rec().console.size();
    keys("s?");
    claim("W+s/?: status and the key list stay available during the session",
          !hasFrom("REFUSED -- the Wi-Fi burst session", mark)
          && hasFrom("FAP-01 keys", mark) && hasFrom("charger", mark));
    keys("W");
    mark = rec().console.size();
    pwm0 = rec().pwm.size();
    keys("I");
    claim("W stop: the exclusion ends the moment the session stops -- I runs "
          "at once, inside the 30 s cool-down",
          hasFrom("IR 10 NEC frames", mark) && rec().pwm.size() > pwm0);
    mark = rec().console.size();
    keys("VW");
    claim("W stop: ...while the cool-down still refuses another W",
          hasFrom("cool-down", mark) && aqroot_hal::wifi().sta_starts == 1);
  }
  {
    coldBoot();
    keys("VW");
    keys("Q");
    const size_t mark = rec().console.size();
    keys("x");
    claim("W then Q: Q stops the session and ends the exclusion -- the release "
          "x runs",
          aqroot_hal::wifi().current_mode == WIFI_MODE_NULL
          && hasFrom("IR  ", mark)
          && !hasFrom("REFUSED -- the Wi-Fi burst session", mark));
  }
  {
    coldBoot();
    keys("VW");
    runFor(11000, 250);
    const size_t mark = rec().console.size();
    keys("I");
    claim("W then bound: the 10 s bound ends the session and the exclusion",
          hasFrom("IR 10 NEC frames", mark));
  }
  {
    coldBoot();
    keys("VW");
    mcuReset();
    setup();
    pump(2);
    const size_t mark = rec().console.size();
    keys("I");
    claim("W then reset: a warm reset ends the FAP-01 session -- nothing is "
          "refused as 'session running' afterwards",
          hasFrom("IR 10 NEC frames", mark)
          && !hasFrom("REFUSED -- the Wi-Fi burst session", mark));
  }
  {
    // The other order: a FAP-01 state first, then W.
    coldBoot();
    keys("B");
    keys("VW");
    claim("B then W: a held backlight refuses the session -- it starts only "
          "from a quiet board",
          aqroot_hal::wifi().sta_starts == 0
          && rec().consoleHas("a FAP-01 stimulus is held or armed"));
    keys("B");
    keys("J");
    keys("VW");
    claim("J then W: ...and so does an armed chip-select hold-off",
          aqroot_hal::wifi().sta_starts == 0
          && rec().consoleCount("a FAP-01 stimulus is held or armed") == 2);
    keys("J");
    keys("N");
    keys("VW");
    claim("N then W: ...and a live NFC field",
          aqroot_hal::wifi().sta_starts == 0 && g_radio->nfcFieldIsUp());
    keys("Q");
  }

  // =========================================================================
  // I -- 38 kHz NEC FROM D1 (C-IR-01).
  // =========================================================================
  {
    coldBoot();
    const size_t pwm0 = rec().pwm.size();
    const uint64_t t0 = rec().clock_us;
    keys("I");
    int marks = 0;
    for (size_t i = pwm0; i < rec().pwm.size(); ++i) {
      if (rec().pwm[i].duty == 128) ++marks;
    }
    bool first_mark_9ms = false;
    if (rec().pwm.size() > pwm0 + 1) {
      first_mark_9ms = rec().pwm[pwm0].duty == 128
          && rec().pwm[pwm0 + 1].duty == 0
          && rec().pwm[pwm0 + 1].t_us - rec().pwm[pwm0].t_us >= 9000;
    }
    const auto &dw = rec().digital_writes;
    bool ir_low_last = false;
    for (const auto &d : dw) {
      if (d.pin == AQROOT_PIN_IR_TX) ir_low_last = (d.value == LOW);
    }
    claim("I: ten NEC frames at 38 kHz from D1 -- 9 ms leader, 34 carrier "
          "marks per frame",
          rec().ledc_hz == 38000 && marks == 10 * 34 && first_mark_9ms
          && rec().consoleHas("IR 10 NEC frames"));
    claim("I: ...BOUNDED (under 1.5 s) and the emitter is left OFF (carrier "
          "0, LEDC detached, IR_TX driven LOW)",
          rec().clock_us - t0 < 1500000u && rec().pwm.back().duty == 0
          && rec().detached && ir_low_last);
  }
  {
    // The burst slot: U9's select lifted with no rail live, so the field is
    // UNKNOWN and U9 owns the slot -- C-NFC-QUIESCE-01's "refuse microSD and
    // IR with U9 owns the burst slot".
    coldBoot();
    keys("J");
    runFor(700, 50);
    const size_t pwm0 = rec().pwm.size();
    keys("I");
    claim("I: with U9's field UNKNOWN (select held off, confirmation revoked) "
          "the burst is REFUSED because U9 owns the burst slot",
          rec().pwm.size() == pwm0
          && rec().consoleHas("FAP-01 IR NEC burst REFUSED: the ST25R3916 "
                              "field state is UNKNOWN"));
  }
  {
    coldBoot();
    keys("3");
    const size_t pwm0 = rec().pwm.size();
    keys("I");
    claim("I: with an accessory rail live the burst is REFUSED (the release "
          "blocking-test rule)",
          rec().pwm.size() == pwm0
          && rec().consoleHas("FAP-01 IR NEC burst REFUSED: turn both "
                              "accessory rails off"));
  }

  // =========================================================================
  // H / J / K / Y -- CHIP-SELECT HOLD-OFF (C-RADIO-QUIESCE-01,
  // C-NFC-QUIESCE-01).
  // =========================================================================
  {
    // A CC1101 keyed, U7's select held off, then a WARM reset: U7 stays
    // powered and keeps transmitting, the MCU restarts.
    coldBoot();
    keys("CH");
    claim("H: the U7 hold-off is ARMED and recorded for ONE warm reset",
          rec().consoleHas("hold-off ARMED on U7 CC1101_CS_N")
          && aqroot_hal::nvs().count("aqroot-fap01/holdoff") == 1);
    mcuReset();                 // warm reset: the stub is retained-TX, NVS kept
    Cc1101Stub &radio = *g_radio;
    setup();
    pump(2);
    claim("H: the boot restores the hold-off BEFORE the quiesce and consumes "
          "the record",
          rec().consoleHas("hold-off RESTORED across the reset on U7")
          && aqroot_hal::nvs().count("aqroot-fap01/holdoff") == 0);
    claim("H: ...the driver selected U7 but its select never fell, so the "
          "boot quiesce reports the radio NOT IDLE (UNKNOWN) and the retained "
          "carrier is still up",
          rec().low_edges[AQROOT_PIN_CC1101_CS_N] == 0 && radio.transmitting
          && rec().consoleHas("(NOT IDLE)"));
    keys("3");
    claim("H: ...and the accessory keys are REFUSED by name",
          !rail3() && rec().consoleHas("ACCESSORY REFUSED: the physical "
                                       "transmit state of U7/U8 is UNKNOWN"));
    runFor(62000, 500);
    claim("H: the hold-off ends at its 60 s bound and the release quiesce "
          "retry then STOPS the retained carrier",
          rec().consoleHas("hold-off RELEASED on U7 CC1101_CS_N (60000 ms "
                           "bound)")
          && !radio.transmitting && rec().consoleHas("MARCSTATE=0x01 (IDLE)"));
  }
  {
    // A rail live, then U9's select lifted: revocation and shed within the
    // firmware's own 820 ms bound, and the burst slot owned by U9.
    coldBoot();
    keys("3");
    claim("J: (setup) ACC_3V3 is live on a confirmed-off field", rail3());
    const uint64_t lifted = rec().clock_us;
    keys("J");
    uint64_t shed = ~uint64_t(0);
    for (int i = 0; i < 100 && shed == ~uint64_t(0); ++i) {
      delay(20);
      loop();
      if (!rail3()) shed = rec().clock_us;
    }
    claim("J: U9's select held off with a rail live: the OFF confirmation is "
          "REVOKED and the rail SHED within kNfcRevocationDeadlineMs (820 ms)",
          shed != ~uint64_t(0) && shed - lifted <= 820000u
          && rec().consoleHas("NFC OFF confirmation REVOKED"));
    keys("d");
    claim("J: ...microSD is refused while U9 owns the burst slot",
          rec().consoleHas("microSD test REFUSED: the ST25R3916 field state "
                           "is UNKNOWN and U9 owns the burst slot"));
    const size_t mark = rec().console.size();
    keys("J");
    runFor(1500, 50);
    claim("J: releasing the hold-off, the release quiesce retry re-proves the "
          "field OFF from a live part",
          hasFrom("hold-off RELEASED on U9 NFC_CS_N (operator key)", mark)
          && hasFrom("FIELD OFF, live identity", mark));
  }
  {
    // K: the lift lands INSIDE a first-rail admission's gauge window.
    coldBoot();
    keys("K3");
    claim("K: a lift 700 ms into the admission's 1300 ms window REVOKES the "
          "confirmation and the rail is NEVER energised",
          !rail3() && rec().consoleHas("NFC OFF confirmation REVOKED"));
    runFor(61000, 500);
    claim("K: ...and the delayed hold-off still ends at its 60 s bound",
          rec().consoleHas("hold-off RELEASED on U9 NFC_CS_N (60000 ms bound)"));
  }
  {
    // Y: the lift lands in the settled recheck AFTER the grant.
    coldBoot();
    const uint64_t pressed = rec().clock_us;
    keys("Y3");
    bool energised = false;
    for (const auto &e : g_board.latch_events) {
      if (bit(e.u3_output, AQROOT_U3_ACC_3V3_EN)) energised = true;
    }
    const uint64_t revoked = lineTime("NFC OFF confirmation REVOKED");
    claim("Y: a lift 2000 ms after the key -- after the grant, in the settled "
          "recheck -- sheds the rail that was just granted within 820 ms of "
          "the lift",
          energised && !rail3() && revoked != ~uint64_t(0)
          && revoked >= pressed + 2000000u
          && revoked - (pressed + 2000000u) <= 820000u);
  }

  // =========================================================================
  // A / B -- HELD AUDIO AND HELD BACKLIGHT (C-THERM-01, Q11-TEMP-01).
  // =========================================================================
  {
    coldBoot();
    const int installs = rec().i2s_installs;
    keys("A");
    const uint64_t fed0 = rec().i2s_bytes_written;
    runFor(500, 20);
    claim("A: the key holds the release tone -- AMP_SD_MODE confirmed out of "
          "shutdown, I2S TX installed and kept FED",
          ampOn() && rec().i2s_installs == installs + 1
          && rec().i2s_bytes_written > fed0
          && rec().consoleHas("held audio STARTED"));
    const int tones = rec().consoleCount("i2s tone ");
    keys("t");
    claim("A: ...the release tone key cannot fight it for I2S",
          rec().consoleCount("i2s tone ") == tones
          && rec().consoleHas("the held audio owns I2S"));
    keys("B");
    const size_t pwm0 = rec().pwm.size() >= 2 ? rec().pwm.size() - 2 : 0;
    claim("B: the held backlight starts at FULL duty and holds it for the "
          "D-784 prime (>= 3000 us) before its 50 % duty",
          rec().pwm.size() >= 2 && rec().pwm[pwm0].duty == 255
          && rec().pwm[pwm0 + 1].duty == 128
          && rec().pwm[pwm0 + 1].t_us - rec().pwm[pwm0].t_us
                 >= uint64_t(kBacklightStartupPrimeUs)
          && rec().attached_pin == AQROOT_PIN_DISP_BL_PWM);
    keys("3");
    keys("5");
    claim("A+B: C-THERM-01's heaviest admitted state is reachable -- held "
          "audio and backlight, then BOTH accessory rails through the release "
          "rail-edge table (audio row)",
          ampOn() && rail3() && rail5() && rec().pwm.back().duty == 128);
    keys("Q");
    bool bl_low = false;
    for (const auto &d : rec().digital_writes) {
      if (d.pin == AQROOT_PIN_DISP_BL_PWM) bl_low = (d.value == LOW);
    }
    claim("Q: stops every FAP-01 stimulus -- amplifier confirmed in shutdown, "
          "I2S uninstalled, backlight duty 0 and the pin LOW",
          !ampOn() && rec().i2s_uninstalls >= 1 && rec().pwm.back().duty == 0
          && bl_low && rec().consoleHas("every stimulus STOPPED"));
  }
  {
    coldBoot();
    keys("3");
    keys("A");
    claim("A: with a rail live the release mode edge REFUSES the amplifier "
          "(audio has no mode-edge row with a rail live)",
          !ampOn() && rec().consoleHas("AMP_SD_MODE enable REFUSED")
          && rec().consoleHas("held audio REFUSED"));
  }
  {
    coldBoot();
    keys("AB");
    runFor(31u * 60u * 1000u, 60000);
    claim("A/B: unattended, both held states end at their 30 min bound",
          !ampOn() && rec().consoleHas("held audio STOPPED (30 min bound)")
          && rec().consoleHas("held backlight STOPPED (30 min bound)")
          && rec().pwm.back().duty == 0);
  }

  // =========================================================================
  // G -- THE 10 ms VCELL CADENCE (C-GAUGE-EPOCH-01).
  // =========================================================================
  {
    coldBoot();
    const size_t mark = rec().console.size();
    keys("G");
    std::vector<unsigned long> t;
    for (size_t i = mark; i < rec().console.size(); ++i) {
      unsigned long ms = 0;
      unsigned raw = 0;
      if (std::sscanf(rec().console[i].c_str(), "vcell t_ms=%lu raw=0x%X", &ms,
                      &raw) == 2) {
        t.push_back(ms);
      }
    }
    bool cadence = t.size() == 200;
    for (size_t i = 1; cadence && i < t.size(); ++i) {
      if (t[i] - t[i - 1] < 9 || t[i] - t[i - 1] > 12) cadence = false;
    }
    claim("G: 200 raw VCELL samples, one every 10 ms for 2 s, each with its "
          "timestamp and value",
          cadence && !t.empty() && t.back() >= 1980 && t.back() <= 2020
          && rec().consoleHas("V=4.00000"));
  }
  {
    // D-802 (hygiene beside R21-03): an all-ones register is a bus fault,
    // not a sample.
    coldBoot();
    g_board.vcell_counts = 0xFFFF;
    const size_t mark = rec().console.size();
    keys("G");
    claim("G: an all-ones VCELL register is marked IMPLAUSIBLE, never printed "
          "as a plain sample, and counted in the END line",
          hasFrom("raw=0xFFFF V=5.11992 IMPLAUSIBLE", mark)
          && hasFrom("200 failed or implausible read(s)", mark));
    g_board.vcell_counts = 51200;
  }
  {
    coldBoot();
    keys("3");
    keys("G");
    claim("G: with a rail live the poll is REFUSED (the release blocking-test "
          "rule)",
          !rec().consoleHas("vcell t_ms=")
          && rec().consoleHas("FAP-01 VCELL poll REFUSED"));
  }

#else   // AQROOT_TEST_EXPECT_PRODUCTION
  // =========================================================================
  // THE RELEASE IMAGE, GIVEN EVERY FAP-01 KEY.
  // =========================================================================
  coldBoot();
  Cc1101Stub &radio = *g_radio;
  const size_t pwm0 = rec().pwm.size();
  const int installs = rec().i2s_installs;
  for (const char *k : {"C", "L", "N", "T", "V", "W", "I", "H", "J", "K", "Y",
                        "A", "B", "G", "Q", "?"}) {
    keys(k);
    runFor(300, 50);
  }
  runFor(3000, 50);
  claim("RELEASE: no FAP-01 key is recognised -- the image never announces "
        "or answers as FAP-01",
        !rec().consoleHas("FAP-01"));
  claim("RELEASE: no sub-GHz carrier -- the CC1101 is never strobed into TX, "
        "the SX1262 never receives SetTxContinuousWave, nothing holds the "
        "SPI-B transmit slot",
        radio.stx_strobes == 0 && !radio.transmitting && radio.cw_commands == 0
        && !radio.tx_cw
        && aqrootHostImageSpiB().transmitting() == SpiBDevice::None);
  claim("RELEASE: no NFC field -- U9 stays in the power-down state the boot "
        "quiesce proved", !radio.nfcFieldIsUp()
        && radio.nfc_operation_control == 0x00);
  claim("RELEASE: no Wi-Fi activation of any kind",
        aqroot_hal::wifi().mode_calls == 0 && aqroot_hal::wifi().frames == 0);
  claim("RELEASE: no chip-select hold-off -- U9 keeps proving liveness (no "
        "revocation) and nothing is stored for the next boot",
        !rec().consoleHas("REVOKED") && aqroot_hal::nvsWrites() == 0);
  claim("RELEASE: no held audio, no held or primed backlight duty, no IR "
        "carrier, no VCELL poll",
        rec().i2s_installs == installs && rec().pwm.size() == pwm0
        && !ampOn() && !rec().consoleHas("vcell t_ms="));
  keys("3");
  claim("RELEASE: ...and the image still grants ACC_3V3 afterwards -- the "
        "keys left nothing keyed and nothing UNKNOWN", rail3());
  {
    // The release image's quiesce must also stay the ONLY thing that ever
    // selects U7: a warm reset with an NVS record present is not honoured.
    mcuReset();
    aqroot_hal::nvs()["aqroot-fap01/holdoff"] = 0x03;
    setup();
    pump(2);
    claim("RELEASE: a hold-off record in NVS is ignored -- the boot quiesce "
          "really selects U7 and stops the retained carrier",
          rec().low_edges[AQROOT_PIN_CC1101_CS_N] > 0
          && !g_radio->transmitting && !rec().consoleHas("FAP-01"));
    aqroot_hal::nvs().clear();
  }
#endif

  std::printf("\n%s -- %d failure(s)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}
