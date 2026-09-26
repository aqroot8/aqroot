#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- THE SEVENTEENTH STANDING CONTRACT, AND THE FIRST THAT LOOKS
AT THE FIRMWARE.

Sixteen contracts ask whether the COPPER is sound, whether the INSTRUMENT that
routes against it is honest, whether the SHIPPABLE package matches the board,
or -- D-745 -- whether the board still implements the PRODUCT.  Not one of them
has ever asked whether the software that will be flashed into the assembled
unit agrees with the board about which pin is which.

That question has already cost this programme once.  D-732 found that the
then-current expander table had `P05`/`P06` and `P16`/`P17` inverted, and
recorded what reading it would have done: masked `4Ah` bit 6 believing it was
`BQ25185_STAT2` when it is `TOUCH_INT_N`, silencing the touch interrupt while
leaving a second input free to hold the shared wake line forever.  The table
was corrected by hand.  Hand-corrected tables drift again, and a firmware pin
map that drifts is not caught by DRC, by the ledger, by parity, or by any gate
in the fab package -- it is caught by a dead peripheral on an assembled board.

WHAT IS PROVED

  H1  `Firmware/src/hw/aqroot_demo_board.h` and `.json` are byte-identical to
      what `gen_firmware_hw_map.py` produces from the board AS IT STANDS.  Not
      "consistent" -- identical.  Any copper, placement or population change
      that moves a pin, a net or a fitted pull makes this FAIL.
  H2  the `board_sha256` the header publishes is the board's actual digest.
  H3  every policy row is corroborated by the board: the net is on the pad the
      row claims, every expander OUTPUT's safe boot latch equals the level its
      fitted external pull already holds (or names why there is no pull), every
      UNMASKED input has a defined idle level, no two firmware roles claim one
      GPIO, and no expander bit or used `U1` pad is missing from the map.
  H4  the map agrees with the two governing owner decisions and with the ledger
      that enforces them: every net in `routing_ledger.APPROVED_UNROUTED` is
      MASKED and flagged as carrying no information, and every `J5` contact in
      `routing_ledger.APPROVED_NC` is absent from the firmware map.
  H5  the firmware layer implements what it was given: every role the generator
      emits is referenced by the C++ under `Firmware/src/hw/`, and the C++
      names no `AQROOT_` symbol the generator did not emit.
  H6  SIX HOST TESTS compile under `-Wall -Wextra -Werror` and pass.  Each
      carries load-bearing destructive controls that must make it FAIL.
        * the EXPANDER SAFE-ORDERING test.  The PCAL9535A resets to all-inputs
          with its output latches at 0xFF, and six of this board's expander
          outputs are safe at 0 while three are safe at 1, so writing the
          complete safe latch before policy registers and direction is a SAFETY
          property, not a style.  It is invisible to a compile and invisible
          to DRC; the test makes it visible by recording the I2C transactions.
        * the SPI BUS B ARBITER test.  U7, U8 and U9 share one bus and the two
          rules over it -- one chip select at a time, one transmitter at a time
          -- were comments until D-748.  A comment cannot refuse.

      D-801 / D801-01 adds the FAP-01 first-article image to H6: its host test
      runs against the FAP-01 build (every stimulus reachable, gated, bounded,
      quiesced) AND against the release build (every FAP-01 key inert), and
      the whole release-image host test is re-run on the FAP-01 build.
  H9  D-801 / D801-03: `Firmware/platformio.ini`'s `default_envs` is exactly
      and solely `aqroot-demo`, and every named environment still exists.
  H10 D-801 / D801-01: FAP-01 is ISOLATED -- `src/fap01/` and
      `AQROOT_FAP01_DIAGNOSTIC` reach `[env:aqroot-demo-fap01]` alone, the
      release `main.cpp` preprocesses to no FAP-01 token, and `src/fap01/`
      refuses to compile without its define.

AND IT PROVES IT IS NOT VACUOUS.  Eleven controls mutate the policy table --
including the exact `P05`/`P06` swap D-732 found -- and each must be REFUSED.

    python3 hardware/demo/manufacturing/checks/firmware_hw_map_contract.py [-o OUT]
"""

import argparse
import configparser
import copy
import csv
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(MFG))

import gen_firmware_hw_map as gen           # noqa: E402
import routing_ledger                        # noqa: E402

HW_DIR = ROOT / "Firmware/src/hw"
DEMO_MAIN = ROOT / "Firmware/src/demo/main.cpp"
MAX17048_PRIMARY = (
    ROOT / "hardware/demo/kicad/aqroot-demo/vendor/ADI/max17048-max17049-rev7.pdf"
)
MAX17048_PRIMARY_SHA256 = (
    "70dc8eef0e012276dcdc58b6dce64af08258304bcf865ceace64e856b8029330"
)
MAX17048_SOURCE_RECORD = (
    ROOT / "hardware/demo/kicad/aqroot-demo/vendor/ADI/max17048-max17049-rev7-source.json"
)
MAX17048_SOURCE_EXPECTED = {
    "vendor": "Analog Devices / Maxim Integrated",
    "device": "MAX17048/MAX17049",
    "document_number": "19-6171",
    "revision": "7",
    "official_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf",
    "MODE_address": "0x06",
    "HibStat_mask": "0x1000",
    "HibStat_semantics": "read-only; set while the IC is in hibernate mode",
    "HIBRT_address": "0x0A",
    "HIBRT_zero_semantics": "disables hibernate mode",
    "VCELL_active_update_ms_typ": 250,
    "VCELL_hibernate_update_s_typ": 45,
    "time_base_accuracy_pct_min": -3.5,
    "time_base_accuracy_pct_max": 3.5,
}
HOST_TESTS = [
    ROOT / "Firmware/test/test_expander_order.cpp",
    ROOT / "Firmware/test/test_spi_bus_b.cpp",
    ROOT / "Firmware/test/test_accessory_power_policy.cpp",
    ROOT / "Firmware/test/test_fuel_gauge_safety.cpp",
    ROOT / "Firmware/test/test_timing_policy.cpp",
    # D-788 / R7-D787-05 + R7-D787-06.  The one that compiles and RUNS the
    # SHIPPED entry points -- `backlightRamp()` and
    # `configureFuelGaugeActiveModeOnHardware()` -- against a recording
    # Arduino HAL, so the production callbacks themselves are load-bearing.
    ROOT / "Firmware/test/test_production_timing.cpp",
    # D-789 / D788-04 + D788-05 + D788-06.  The one that compiles and RUNS the
    # PRODUCTION CALL SITES -- `DemoBringupApp`'s gauge permission path, its
    # serial dispatch and its warm-reset/diagnostic methods -- over a recording
    # bus with a PHYSICAL-LATCH expander model.  Round-8 showed that making the
    # leaf entry points executable was not enough while their callers lived in
    # an uncompiled `demo/main.cpp`.
    ROOT / "Firmware/test/test_production_callers.cpp",
    # D-790 / D789-A04 (+ Fable V-01/V-02, D789-A09, D789-A10).  The one that
    # compiles and RUNS `src/demo/main.cpp` ITSELF -- `setup()`, `loop()` and
    # the console dispatch -- over a host Arduino core and a PHYSICAL-LATCH
    # board model.  Round-9 showed that making the CALL SITES executable was
    # not enough while the IMAGE that reaches them was compiled by nothing:
    # all five of Astra's counterexamples live in that file.
    ROOT / "Firmware/test/test_production_image.cpp",
]
# The tests that need the whole IMAGE -- `src/demo/` and the host Arduino core
# under `test/image/` -- rather than the headers alone.
IMAGE_TESTS = {"test_production_image.cpp", "test_fap01_image.cpp"}
# D-801 / D801-01.  The FAP-01 first-article diagnostic image.
FAP01_DIR = ROOT / "Firmware/src/fap01"
FAP01_TEST = ROOT / "Firmware/test/test_fap01_image.cpp"
FAP01_DEFINE = "AQROOT_FAP01_DIAGNOSTIC"
PLATFORMIO_INI = ROOT / "Firmware/platformio.ini"
RELEASE_ENV = "aqroot-demo"
FAP01_ENV = "aqroot-demo-fap01"
# Every environment that must still build BY NAME (D801-03).
NAMED_ENVS = ("esp32-s3-aqroot", "wokwi", "esp32-s3-aqroot-dm", RELEASE_ENV,
              FAP01_ENV)
# D-803 / D803-04: the CONFIGURED PlatformIO -- `AQROOT_PIO` if set, else the
# worker's venv -- then `pio` and `platformio` on PATH (`_pio_executable`).
PIO = Path(os.environ.get("AQROOT_PIO", "/home/aqroot8/.piovenv/bin/pio"))
IMAGE_HARNESS = ROOT / "Firmware/test/image"
DEMO_DIR = ROOT / "Firmware/src/demo"
# The recording Arduino core the production-entry-point test compiles against.
# Copied beside `hw/` for EVERY host test so one compile command serves all of
# them; the four seam tests do not include it and are unaffected.
HOST_HARNESS = ROOT / "Firmware/test/harness"

# Each control is (name, file under src/hw, exact text, replacement).  The
# replacement must be a DEFENSIBLE-LOOKING mistake -- the kind a future edit
# actually makes -- not a syntax error.
# D-775.  The accessory VCELL policy.  Both floors are DERIVED by
# checks/demo_feature_contract.py F6 -- which is what refuses a floor BELOW the
# derivation.  What H6 has to prove is the other half: that the C++ this board
# actually ships behaves as the derivation assumes, and that a plausible future
# edit to it is CAUGHT.  The first control is the pre-D-775 policy (one floor
# for both rails); the second is the fail-open inversion; the third drops the
# 5 V-first shed order, which is what keeps the 3.3 V rail's published budget
# available below the dual-rail floor.
POWER_POLICY_CONTROLS = [
    # D-791 / D790-A03 re-aimed these at the THREE derived constants.  The
    # first is unchanged in intent -- a dual ENABLE floor that collapses onto
    # the single one stops anticipating the second rail's own load step.
    ("the published dual-rail envelope drops below the single-rail one",
     "aqroot_accessory_power_policy.h",
     "constexpr float kAccessoryDualRailFloorV = 3.85f;",
     "constexpr float kAccessoryDualRailFloorV = 3.65f;"),
    # ---- D-792 / R11-04.  THE PERMISSION TABLE HAS TO BITE. ----------------
    # Every one of these compiles, and every one of them is a way the table
    # could be present and inert.  Round-11's finding was that D-791's two
    # scalars were derived from the wrong pre-state; these controls are about
    # the replacement not being decorative.
    ("the first-rail floor is put back to D-791's reproduced 3.55 V",
     "aqroot_accessory_power_policy.h",
     "      {3.80f, 3.80f},  // 0  no optional mode",
     "      {3.55f, 3.55f},  // 0  no optional mode"),
    ("a REFUSED mode combination is encoded as a high floor instead of a "
     "refusal, so a full pack authorises it",
     "aqroot_accessory_power_policy.h",
     "      {kAccessoryNotPermittedV, kAccessoryNotPermittedV},  // 5  Wi-Fi + sub-GHz",
     "      {4.15f, 4.15f},  // 5  Wi-Fi + sub-GHz"),
    ("the amplifier's own load stops raising the floor",
     "aqroot_accessory_power_policy.h",
     "      {3.85f, 3.85f},  // 2  audio at the capped level",
     "      {3.80f, 3.80f},  // 2  audio at the capped level"),
    ("the MODE edge's own refusal predicate stops refusing",
     "aqroot_accessory_power_policy.h",
     """inline bool accessoryModeEntryPermitted(const AccessoryLoadState &modes_after,
                                        int rails_on) {
  return accessoryModeEntryFloor(modes_after, rails_on)
         < kAccessoryNotPermittedV;""",
     """inline bool accessoryModeEntryPermitted(const AccessoryLoadState &modes_after,
                                        int rails_on) {
  (void)modes_after; (void)rails_on;
  return true;"""),
    ("the two edges are collapsed into one table, so the mode edge is granted "
     "on a floor derived from a heavier pre-state",
     "aqroot_accessory_power_policy.h",
     """  return accessoryEdgeFloor(
      accessoryModeEdgeRow(accessoryLoadBits(modes_after)), rails_on);""",
     """  return accessoryEdgeFloor(
      accessoryRailEdgeRow(accessoryLoadBits(modes_after)), rails_on);"""),
    # NOT the obvious mutation.  Simply DELETING the
    # `accessoryCombinationPermitted` line is an EQUIVALENT mutant, because the
    # refusal sentinel then falls through to `vcell >= 99.0f` and the
    # plausibility band tops out at 4.50 V, so the combination is still
    # refused.  The mutation that is NOT equivalent is the plausible REFACTOR
    # that turns the refusal into a default -- and that is the one reproduced
    # here, because it is the one a maintainer would actually write.
    ("a refused combination is turned into a default floor it can pass",
     "aqroot_accessory_power_policy.h",
     """  if (!accessoryModeEntryPermitted(after, rails_on)) return false;
  return vcell_valid && vcellIsPlausible(vcell)
         && vcell >= accessoryModeEntryFloor(after, rails_on);""",
     """  const float required = accessoryModeEntryPermitted(after, rails_on)
                            ? accessoryModeEntryFloor(after, rails_on)
                            : kAccessoryRetentionFloorV;
  return vcell_valid && vcellIsPlausible(vcell) && vcell >= required;"""),
    # D-797 / D797-02 re-aimed: the no-rail branch is now the CHARGING floor,
    # so the mutant takes that branch with a rail live as well -- the D-792
    # rail-live table is then never consulted.
    ("the mode edge is transparent while a rail is live (the no-rail "
     "charging branch taken with a rail live too)",
     "aqroot_accessory_power_policy.h",
     "  if (rails_on <= 0) {\n    // D-797 / D797-02",
     "  if (rails_on >= 0) {\n    // D-797 / D797-02"),
    ("the mode edge ignores an unreadable gauge",
     "aqroot_accessory_power_policy.h",
     """  return vcell_valid && vcellIsPlausible(vcell)
         && vcell >= accessoryModeEntryFloor(after, rails_on);""",
     """  (void)vcell_valid; (void)vcell;
  return true;"""),
    # D-793 RE-AIMED THIS.  D-792 swapped Wi-Fi with sub-GHz, and under the
    # D-793 table both of those rows are the SAME refusal sentinel, so the
    # swap became an EQUIVALENT MUTANT -- unobservable, and therefore not a
    # control.  Swapping Wi-Fi with the AMPLIFIER is observable in both
    # directions: a board with the amplifier on looks up a refusal, and a
    # board transmitting Wi-Fi looks up a 3.85 V floor it must not have.
    ("the mode bits are transposed, so the table is indexed by the wrong "
     "mode set",
     "aqroot_accessory_power_policy.h",
     """  return (s.wifi_tx ? 1u : 0u) | (s.amplifier_on ? 2u : 0u) |
         (s.subghz_tx ? 4u : 0u);""",
     """  return (s.wifi_tx ? 2u : 0u) | (s.amplifier_on ? 1u : 0u) |
         (s.subghz_tx ? 4u : 0u);"""),
    ("the refusal sentinel stops refusing and becomes a comparison a caller "
     "can pass",
     "aqroot_accessory_power_policy.h",
     """inline bool accessoryCombinationPermitted(const AccessoryLoadState &modes,
                                          int rails_after) {
  return accessoryEnableFloor(modes, rails_after) < kAccessoryNotPermittedV;""",
     """inline bool accessoryCombinationPermitted(const AccessoryLoadState &modes,
                                          int rails_after) {
  (void)modes; (void)rails_after;
  return true;"""),
    ("unreadable VCELL fails open instead of shedding active rails",
     "aqroot_accessory_power_policy.h",
     """  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::ShedAll;""",
     """  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::Keep;"""),
    ("a dual-rail load below the retention floor sheds everything instead of "
     "the 5 V rail alone",
     "aqroot_accessory_power_policy.h",
     """    return (rail3v3_on && rail5v_on) ? AccessoryBatteryAction::Shed5v
                                     : AccessoryBatteryAction::ShedAll;""",
     "    return AccessoryBatteryAction::ShedAll;"),
    # D-791 / D790-A03.  THE REGRESSION THE THIRD CONSTANT EXISTS TO STOP.
    # Judging RETENTION at an ENABLE floor sheds a rail 400 ms after
    # authorising it, every time, because the enable floor anticipates a load
    # step that has by then already happened.  That was D-790's behaviour and
    # it is what made the published dual-rail capability unreachable.
    ("retention is judged at the ENABLE envelope instead of the retention "
     "floor",
     "aqroot_accessory_power_policy.h",
     "  if (vcell < kAccessoryRetentionFloorV) {",
     "  if (vcell < kAccessorySingleRailFloorV) {"),
    ("the retention floor is pushed under the BQ25185's own VBUVLO bound",
     "aqroot_accessory_power_policy.h",
     "constexpr float kAccessoryRetentionFloorV = 3.20f;",
     "constexpr float kAccessoryRetentionFloorV = 3.00f;"),
    ("the VCELL plausibility band stops excluding the all-ones code",
     "aqroot_accessory_power_policy.h",
     "constexpr float kVcellPlausibleMaxV = 4.50f;",
     "constexpr float kVcellPlausibleMaxV = 5.50f;"),
    # ---- D-797 / D797-02.  THE CHARGING MODE-ENTRY FLOOR (no rail live).
    # F12 pins the table's VALUES; these prove the host test feels a change
    # in what the table DOES.
    ("D797-02: the charging floor is ignored with no rail live -- the "
     "pre-D-797 transparent guard",
     "aqroot_accessory_power_policy.h",
     "    const float f = accessoryChargingModeEntryFloor(accessoryLoadBits(after));",
     "    const float f = 0.0f;"),
    ("D797-02: a NotPermitted charging row is treated as allowed",
     "aqroot_accessory_power_policy.h",
     "    if (f >= kAccessoryNotPermittedV) return false;",
     "    if (f >= kAccessoryNotPermittedV) return true;"),
    ("D797-02: the generated audio + sub-GHz charging floor is edited 3.60 -> 3.50 V",
     "aqroot_accessory_power_policy.h",
     "      3.60f,                    // 6  audio + sub-GHz",
     "      3.50f,                    // 6  audio + sub-GHz"),
]

# Round-4 R4-04: active-mode configuration/readiness is part of VCELL validity.
# Each mutation is realistic enough to compile and must be rejected by the
# dedicated MAX17048 host test.
FUEL_GAUGE_CONTROLS = [
    # D-790 / D789-A10 moved both of these: the qualification now also
    # clears and verifies FORCED SLEEP, so the exact lines they mutate are
    # longer.  The mutants themselves are unchanged in intent.
    ("HIBRT=0 readback is trusted while MODE.HibStat still reports hibernate",
     "max17048_guard.h",
     """    active_ready_ = mode_read && verify[0] == 0x00 && verify[1] == 0x00 &&
                    (mode & kModeHibStatMask) == 0 &&
                    (mode & kModeEnSleepMask) == 0;""",
     """    active_ready_ = mode_read && verify[0] == 0x00 && verify[1] == 0x00 &&
                    (mode & kModeEnSleepMask) == 0;"""),
    ("later MODE.HibStat assertion is ignored before a safety VCELL read",
     "max17048_guard.h",
     """    if ((mode & kModeHibStatMask) != 0 || (mode & kModeEnSleepMask) != 0 ||
        (config & kConfigSleepMask) != 0) {""",
     """    if ((mode & kModeEnSleepMask) != 0 ||
        (config & kConfigSleepMask) != 0) {"""),
    ("VCELL bus failure leaves gauge readiness trusted",
     "max17048_guard.h",
     """    if (!bus.readRegister(address_, kRegVcell, raw, sizeof(raw))) {
      active_ready_ = false;
      return false;
    }""",
     """    if (!bus.readRegister(address_, kRegVcell, raw, sizeof(raw))) {
      return false;
    }"""),
    ("implausible VCELL does not invalidate gauge readiness",
     "max17048_guard.h",
     """    if (counts == 0x0000 || counts == 0xFFFF || !vcellIsPlausible(v)) {
      active_ready_ = false;
      return false;
    }""",
     """    if (counts == 0x0000 || counts == 0xFFFF || !vcellIsPlausible(v)) {
      return false;
    }"""),
]


# D-787 / Round-6 R6-E01/R6-E02. These mutate the EXECUTABLE policy seam
# and are caught by test_timing_policy.cpp. They are deliberately the exact
# classes Astra/Fable used to evade D-785's source-text gates.
TIMING_CONTROLS = [
    ("gauge settle is shortened to 5 ms",
     "aqroot_demo_timing_policy.h",
     "constexpr uint32_t kFuelGaugeActiveSettleMs = 300;",
     "constexpr uint32_t kFuelGaugeActiveSettleMs = 5;"),
    ("gauge settle is moved before qualification",
     "aqroot_demo_timing_policy.h",
     """  if (!gauge.configureActiveMode(bus)) return false;
  wait_ms(kFuelGaugeActiveSettleMs);
  return true;""",
     """  wait_ms(kFuelGaugeActiveSettleMs);
  if (!gauge.configureActiveMode(bus)) return false;
  return true;"""),
    ("gauge settle is hidden in dead code",
     "aqroot_demo_timing_policy.h",
     "  wait_ms(kFuelGaugeActiveSettleMs);",
     "  if (false) wait_ms(kFuelGaugeActiveSettleMs);"),
    ("backlight full-duty prime is dead code",
     "aqroot_demo_timing_policy.h",
     "  write_duty(255);",
     "  if (false) write_duty(255);"),
    ("backlight emits dim PWM before the prime",
     "aqroot_demo_timing_policy.h",
     """  write_duty(255);
  wait_us(kBacklightStartupPrimeUs);""",
     """  write_duty(3);
  wait_ms(50);
  write_duty(255);
  wait_us(kBacklightStartupPrimeUs);"""),
    ("backlight prime is shortened below 2 ms",
     "aqroot_demo_timing_policy.h",
     "constexpr uint32_t kBacklightStartupPrimeUs = 3000;",
     "constexpr uint32_t kBacklightStartupPrimeUs = 1500;"),
]

# D-788 / R7-D787-05 + R7-D787-06.  THE EXACT COUNTEREXAMPLES ROUND-7 RAN.
# Every one of these mutates a PRODUCTION callback -- the code the assembled
# board executes -- and every one of them passed the complete D-787 gate suite.
# They are caught here because `test_production_timing.cpp` compiles and runs
# those callbacks rather than a test's own fakes.
PRODUCTION_TIMING_CONTROLS = [
    ("the production gauge settle callback is halved",
     "aqroot_demo_gauge_bringup.h",
     "gauge, bus, [](uint32_t ms) { delay(ms); });",
     "gauge, bus, [](uint32_t ms) { delay(ms / 2); });"),
    ("the production gauge settle callback is a no-op",
     "aqroot_demo_gauge_bringup.h",
     "gauge, bus, [](uint32_t ms) { delay(ms); });",
     "gauge, bus, [](uint32_t ms) { (void)ms; });"),
    ("the production gauge caller waits before qualification",
     "aqroot_demo_gauge_bringup.h",
     """  return qualifyFuelGaugeActiveMode(
      gauge, bus, [](uint32_t ms) { delay(ms); });""",
     """  delay(kFuelGaugeActiveSettleMs);
  return gauge.configureActiveMode(bus);"""),
    ("the production backlight microsecond hold is halved",
     "aqroot_demo_backlight.h",
     "[](uint32_t us) { delayMicroseconds(us); },",
     "[](uint32_t us) { delayMicroseconds(us / 2); },"),
    ("the production backlight microsecond hold is a no-op",
     "aqroot_demo_backlight.h",
     "[](uint32_t us) { delayMicroseconds(us); },",
     "[](uint32_t us) { (void)us; },"),
    ("the production PWM duty writer is halved",
     "aqroot_demo_backlight.h",
     "[channel](uint8_t duty) { ledcWrite(channel, duty); },",
     "[channel](uint8_t duty) { ledcWrite(channel, uint8_t(duty / 2)); },"),
    ("the production backlight emits dim PWM before the seam",
     "aqroot_demo_backlight.h",
     "  runBacklightRampPolicy(",
     "  ledcWrite(channel, 3);\n  delay(50);\n  runBacklightRampPolicy("),
    ("the production backlight bypasses the seam entirely",
     "aqroot_demo_backlight.h",
     """  runBacklightRampPolicy(
      [channel](uint8_t duty) { ledcWrite(channel, duty); },
      [](uint32_t us) { delayMicroseconds(us); },
      [](uint32_t ms) { delay(ms); });""",
     """  ledcWrite(channel, 255);
  ledcWrite(channel, 0);"""),
]


# D-789 / D788-04 + D788-05 + D788-06.  THE EXACT COUNTEREXAMPLES ROUND-8 RAN,
# one level out from D-788's.  Every one of these mutates a PRODUCTION CALL
# SITE -- not the function it calls -- and every one of them passed the complete
# D-788 gate suite because `demo/main.cpp` was compiled by no host test.  They
# are caught here because `test_production_callers.cpp` constructs
# `DemoBringupApp` over a recording bus with a physical output-latch model and
# drives the real methods.
PRODUCTION_CALLER_CONTROLS = [
    # ---- D-793 / R12-03.  THE RETAINED RADIO STATE, WHICH AN MCU RESET
    # CANNOT SEE.  Every one of these compiles, and every one is a way the
    # image could go back to believing a powered transceiver is idle because
    # a C++ member says so.
    ("the radio state is assumed KNOWN at construction, which is exactly "
     "what an MCU reset makes it",
     "aqroot_demo_bringup_app.h",
     "  bool radios_quiesced_ = false;",
     "  bool radios_quiesced_ = true;"),
    ("the mode set stops reading an unquiesced radio as KEYED",
     "aqroot_demo_bringup_app.h",
     "    s.subghz_tx = subghz_tx_ || !radios_quiesced_;",
     "    s.subghz_tx = subghz_tx_;"),
    ("the accessory permission stops refusing while the physical radio "
     "state is unknown",
     "aqroot_demo_bringup_app.h",
     "    if (!radios_quiesced_) {",
     "    if (radios_quiesced_ && false) {"),
    ("a warm-reset recovery stops invalidating the radio state it can no "
     "longer vouch for",
     "aqroot_demo_bringup_app.h",
     "    radios_quiesced_ = false;\n    if (disp_reset_intent_.want)",
     "    if (disp_reset_intent_.want)"),
    # ---- D-793 / R12-08.  THE BURST ARBITER.  The permission table may be
    # derived at the worst SINGLE burst only because the firmware serialises
    # them; these are the ways that could stop being true.
    ("the burst arbiter admits a second concurrent bursty load",
     "aqroot_accessory_power_policy.h",
     "    if (active_ != BurstLoad::None) return false;\n    active_ = which;",
     "    active_ = which;"),
    ("the arbiter's RAII hold stops releasing, so one burst wedges every "
     "later one",
     "aqroot_accessory_power_policy.h",
     "    ~Hold() { if (ok_) arbiter_.end(which_); }",
     "    ~Hold() { }"),
    # --- D788-04: the outer gauge caller -----------------------------------
    ("the outer gauge caller early-returns and leaves the tested helper dead",
     "aqroot_demo_bringup_app.h",
     "    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);",
     "    return gauge_.configureActiveMode(bus_);"),
    ("the outer gauge caller reports success without qualifying at all",
     "aqroot_demo_bringup_app.h",
     "    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);",
     "    (void)gauge_.configureActiveMode(bus_);\n    return true;"),
    ("the accessory permission skips the qualification when the gauge is cold",
     "aqroot_demo_bringup_app.h",
     """    if (!gauge_.activeReady()) {
      if (acc3v3_ || acc5v_ || expanders_.safeShutdownPending() ||
          !configureFuelGaugeActiveMode()) {""",
     """    if (false) {
      if (acc3v3_ || acc5v_ || expanders_.safeShutdownPending() ||
          !configureFuelGaugeActiveMode()) {"""),
    ("a rail already being on stops being fail-closed on lost readiness",
     "aqroot_demo_bringup_app.h",
     "      if (acc3v3_ || acc5v_ || expanders_.safeShutdownPending() ||",
     "      if (expanders_.safeShutdownPending() ||"),
    # --- D-792 / R11-04: the mode set the permission is evaluated against ---
    ("the accessory permission is evaluated against an EMPTY mode set, so the "
     "state the board is actually in stops mattering",
     "aqroot_demo_bringup_app.h",
     "    const AccessoryLoadState modes = accessoryLoadState();",
     "    const AccessoryLoadState modes;"),
    ("the amplifier reading is optimistic, so an UNKNOWN U2 output latch "
     "counts as OFF and the permission is granted on a mode set the board is "
     "not in",
     "aqroot_demo_bringup_app.h",
     "  bool amplifierCountsAsOn() const { return !amplifierConfirmed(false); }",
     "  bool amplifierCountsAsOn() const { return amplifierConfirmed(true); }"),
    ("energising the amplifier stops consulting the mode edge",
     "aqroot_demo_bringup_app.h",
     """    if (on) {
      AccessoryLoadState after = accessoryLoadState();
      after.amplifier_on = true;
      if (!modeEntryAllowed(after, "AMP_SD_MODE enable")) return false;
    }""",
     "    // mode edge removed"),
    ("the mode edge is consulted and its refusal is ignored",
     "aqroot_demo_bringup_app.h",
     '      if (!modeEntryAllowed(after, "AMP_SD_MODE enable")) return false;',
     '      (void)modeEntryAllowed(after, "AMP_SD_MODE enable");'),
    ("the mode edge passes the mode set BEFORE the change instead of after",
     "aqroot_demo_bringup_app.h",
     """      AccessoryLoadState after = accessoryLoadState();
      after.amplifier_on = true;""",
     "      AccessoryLoadState after = accessoryLoadState();"),
    ("the sub-GHz authority answers yes without asking the table",
     "aqroot_demo_bringup_app.h",
     """    AccessoryLoadState after = accessoryLoadState();
    after.subghz_tx = true;
    return modeEntryAllowed(after, "sub-GHz TX");""",
     "    return true;"),
    ("the mode edge stops being fail-closed when no rail is on... and also "
     "when one is",
     "aqroot_demo_bringup_app.h",
     "    const int rails = accessoryRailsOn();\n"
     "    if (rails <= 0) return chargingModeEntryAllowed(after, what);",
     "    const int rails = accessoryRailsOn();\n    if (rails >= 0) return true;"),
    # --- FABLE / D-792: post-recovery amplifier-intent reconciliation -------
    # Recovery rebuilds a SAFE state, not a WANTED one.  Fable's mutation
    # dropped the reconciliation and the tone silently failed until the next
    # operator command, with nothing anywhere saying so.
    ("recovery stops reconciling an outstanding amplifier intent",
     "aqroot_demo_bringup_app.h",
     """    if (amp_intent_.pending || amp_intent_.want) {
      amp_intent_.pending = !amplifierConfirmed(amp_intent_.want);
    }""",
     "    // reconciliation removed"),
    ("recovery reconciles the intent but never re-applies it",
     "aqroot_demo_bringup_app.h",
     """    (void)serviceDeferredCommands();
    log_("I2C/expander safety state RECOVERED after incomplete boot");""",
     '    log_("I2C/expander safety state RECOVERED after incomplete boot");'),
    ("recovery marks the intent satisfied instead of testing the latch",
     "aqroot_demo_bringup_app.h",
     "      amp_intent_.pending = !amplifierConfirmed(amp_intent_.want);",
     "      amp_intent_.pending = false;"),
    # --- D788-05: the backlight serial caller ------------------------------
    ("the serial dispatch carries a duplicate backlight ramp with a no-op hold",
     "aqroot_demo_bringup_app.h",
     "        backlightRamp();",
     """        ledcSetup(0, kBacklightPwmHz, 8);
        ledcAttachPin(AQROOT_PIN_DISP_BL_PWM, 0);
        for (int duty = 5; duty <= 255; duty += 5) {
          ledcWrite(0, uint8_t(duty));
        }
        ledcWrite(0, 0);
        ledcDetachPin(AQROOT_PIN_DISP_BL_PWM);
        pinMode(AQROOT_PIN_DISP_BL_PWM, OUTPUT);
        digitalWrite(AQROOT_PIN_DISP_BL_PWM, LOW);"""),
    ("the serial dispatch emits a dim PWM command before the tested ramp",
     "aqroot_demo_bringup_app.h",
     "        backlightRamp();",
     "        ledcWrite(0, 3);\n        backlightRamp();"),
    ("the backlight key stops being gated on a confirmed safe accessory state",
     "aqroot_demo_bringup_app.h",
     '        if (!blockingDemoTestAllowed("backlight ramp")) return true;',
     '        (void)blockingDemoTestAllowed("backlight ramp");'),
    # --- D788-06: warm reset, reset release, truthful reporting -------------
    ("the warm-reset retry drops the complete expander initialisation",
     "aqroot_demo_bringup_app.h",
     "    const bool recovered = bus_open && expanders_.begin(bus_);",
     "    const bool recovered = bus_open;"),
    ("the warm-reset retry gives up after its first attempt",
     "aqroot_demo_bringup_app.h",
     "    if (expanders_.ready()) return false;",
     "    if (expanders_.ready() || recovery_started_) return false;"),
    # "force reset-release success" -- Astra's own words for D788-06.  Note
    # that mutating `released` or `writes_ok` ALONE is an EQUIVALENT mutant on
    # this device: `Pcal9535a::writeOutputs` invalidates the output shadow on
    # any NACK and `writeBit` then refuses, so `writes_ok` and `shadow_known`
    # cannot disagree.  The mutation that is NOT equivalent is the one that
    # forces the VERDICT, and that is the one reproduced here.
    ("the reset-release diagnostic forces a CONFIRMED verdict",
     "aqroot_demo_bringup_app.h",
     "    if (writes_ok && released) {\n      out.verdict = ResetRelease::Confirmed;",
     "    (void)released;\n    if (true) {\n      out.verdict = ResetRelease::Confirmed;"),
    ("the reset-release diagnostic trusts a shadow it has not proved valid",
     "aqroot_demo_bringup_app.h",
     "    const bool shadow_known = expanders_.u2().outputShadowValid();",
     "    const bool shadow_known = true;"),
    ("the accessory command line reports the WANTED state, not the reconciled one",
     "aqroot_demo_bringup_app.h",
     """    const char *state = uncertain ? "UNKNOWN (pending safe reconciliation)"
                                  : (retained ? "ON" : "OFF");""",
     """    (void)uncertain;
    (void)retained;
    const char *state = want ? "ON" : "OFF";"""),
    ("the fail-closed shutdown claims the rails are off while the state is unknown",
     "aqroot_demo_bringup_app.h",
     """    const bool pending = expanders_.safeShutdownPending() ||
                         !expanders_.u2().outputShadowValid() ||
                         !expanders_.u3().outputShadowValid();""",
     "    const bool pending = false;"),
    # ---- D-795 / R14-01.  EVERY STAMP SITE, ONE CONTROL EACH.  Round-14:
    # "Add host/hardware-map mutation controls for EACH stamp site.  Removing
    # amplifier/backlight/rail/shed stamps must fail."  Each deletes exactly
    # one `noteMaterialLoadEdge` and must be caught by the per-site claims in
    # test_production_callers.cpp.
    ("R14-01: the ACC_3V3_SW rail step is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '        if (ok) noteMaterialLoadEdge("the ACC_3V3_SW step");',
     "        (void)0;"),
    ("R14-01: the ACC_5V_SW rail step is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '        if (ok) noteMaterialLoadEdge("the ACC_5V_SW step");',
     "        (void)0;"),
    ("R14-01: the accessory I2C buffer step is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '        if (ok) noteMaterialLoadEdge("the accessory I2C buffer step");',
     "        (void)0;"),
    ("R14-01: the backlight ramp is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '        noteMaterialLoadEdge("the backlight ramp");',
     "        (void)0;"),
    ("R14-01: the amplifier edge (both directions) is no longer stamped",
     "aqroot_demo_bringup_app.h",
     """    if (acked) {
      noteMaterialLoadEdge(on ? "the amplifier being energised"
                              : "the amplifier being quieted");
    }""",
     "    (void)0;"),
    ("R14-01: the display initialisation is no longer stamped",
     "aqroot_demo_bringup_app.h",
     """    noteMaterialLoadEdge(up ? "the ILI9488 display initialisation"
                            : "the display going down");""",
     "    (void)0;"),
    ("R14-01: the display reset assertion is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '    if (acked) noteMaterialLoadEdge("the display reset being asserted");',
     "    (void)0;"),
    ("R14-01: the full accessory shed is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '    if (off5 || off3 || offbuf) noteMaterialLoadEdge("the accessory shed");',
     "    (void)0;"),
    ("R14-01: the ACC_5V_SW retention shed is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '      if (off5) noteMaterialLoadEdge("the ACC_5V_SW shed");',
     "      (void)0;"),
    ("R14-01: the sub-GHz quiesce is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '    if (confirmed) noteMaterialLoadEdge("the sub-GHz radio quiesce");',
     "    (void)0;"),
    ("R14-01: the NFC quiesce is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '      noteMaterialLoadEdge("the NFC field quiesce");',
     "      (void)0;"),
    ("R14-01: sub-GHz keying is no longer stamped",
     "aqroot_demo_bringup_app.h",
     """      noteMaterialLoadEdge(on ? "sub-GHz TX keying" : "sub-GHz TX unkeying");""",
     "      (void)0;"),
    ("R14-01: the Wi-Fi/BLE radio is no longer stamped",
     "aqroot_demo_bringup_app.h",
     """      noteMaterialLoadEdge(on ? "the Wi-Fi/BLE radio starting"
                              : "the Wi-Fi/BLE radio stopping");""",
     "      (void)0;"),
    ("R14-01: the expander recovery is no longer stamped",
     "aqroot_demo_bringup_app.h",
     '    noteMaterialLoadEdge("the expander recovery");',
     "    (void)0;"),
    ("R14-01: an admission no longer stamps its own request",
     "aqroot_demo_bringup_app.h",
     "    load_epoch_.noteAdmissionRequest(millis(), admission_label_);",
     "    (void)0;"),
    ("R14-01: the window is D-794's nominal 1000 ms again",
     "aqroot_accessory_power_policy.h",
     "    if (elapsed >= kGaugePostLoadConversionMs) return 0;\n"
     "    return kGaugePostLoadConversionMs - elapsed;",
     "    if (elapsed >= kGaugeD794NominalWindowMs) return 0;\n"
     "    return kGaugeD794NominalWindowMs - elapsed;"),
    # ---- D-795 / R14-02, at the app level.
    ("R14-02: a lost NFC liveness no longer revokes the OFF confirmation",
     "aqroot_demo_bringup_app.h",
     "    if (alive || !nfc_field_confirmed_off_) return;",
     "    if (alive || !nfc_field_confirmed_off_ || true) return;"),
    ("R14-02: a revocation no longer sheds the rails granted under it",
     "aqroot_demo_bringup_app.h",
     '      forceAccessoriesOff("the ST25R3916 field state became UNKNOWN");',
     "      (void)0;"),
    ("R14-02: an UNKNOWN field no longer blocks a burst once the arbiter is "
     "clear",
     "aqroot_demo_bringup_app.h",
     "    if (!nfc_field_confirmed_off_ && which != BurstLoad::NfcField) {",
     "    if (false) {"),
    # ---- D-796 / D796-10, at the app level.  A field-owning NFC session
    # owns U9, and the liveness probe -- every call of which writes 11h --
    # stands down for it.
    ("D796-10: a field session keeps the OFF confirmation, so the liveness "
     "probe keeps challenging 11h under the session's field",
     "aqroot_demo_bringup_app.h",
     "    nfc_session_active_ = true;\n    nfc_field_confirmed_off_ = false;",
     "    nfc_session_active_ = true;"),
    ("D796-10: a quiesce verdict restores the confirmation while a session "
     "still holds U9",
     "aqroot_demo_bringup_app.h",
     "    if (nfc_session_active_) return;\n"
     "    nfc_field_confirmed_off_ = confirmed;",
     "    nfc_field_confirmed_off_ = confirmed;"),
    ("D796-10: a session is begun beside a live accessory rail",
     "aqroot_demo_bringup_app.h",
     "    else if (acc3v3_ || acc5v_)\n",
     "    else if (false)\n"),
    ("D-796: the settled recheck's electrical settle stops polling liveness "
     "(equivalent at image level -- see PRODUCTION_IMAGE_CONTROLS)",
     "aqroot_demo_bringup_app.h",
     "      (void)serviceNfcLiveness();\n"
     "      const uint32_t elapsed = millis() - start;",
     "      const uint32_t elapsed = millis() - start;"),
    ("D796-10: a session is begun without re-proving liveness at the request",
     "aqroot_demo_bringup_app.h",
     "        serviceNfcLiveness(/*force=*/true) != NfcLivenessResult::Alive) {",
     "        false) {"),
    # ---- D-797 / D797-08 (Fable R16-03), at the app level.  A Deferred
    # forced probe at a grant refuses the grant and keeps the confirmation.
    ("D797-08: the admission reader treats a Deferred forced probe as no "
     "news (rail enable AND mode entry with a rail live)",
     "aqroot_demo_bringup_app.h",
     "    if (proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(label);",
     "    if (false && proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(label);"),
    ("D797-08: a non-NFC burst treats a Deferred forced probe as no news",
     "aqroot_demo_bringup_app.h",
     "    if (proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(what);",
     "    if (false && proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(what);"),
    ("D797-08: a Deferred grant revokes the confirmation instead of keeping "
     "it",
     "aqroot_demo_bringup_app.h",
     "  void logNfcGrantDeferred(const char *what) {\n",
     "  void logNfcGrantDeferred(const char *what) {\n"
     "    noteNfcLiveness(false, 0x00);\n"),
    ("D797-08: a Deferred forced probe at a grant is counted as a proof and "
     "consumes the schedule",
     "aqroot_demo_bringup_app.h",
     "    if (r == NfcLivenessResult::Deferred) {\n"
     "      nfc_liveness_started_ = was_started;\n"
     "      last_nfc_liveness_ms_ = was_last;\n      return r;\n    }\n"
     "    ++nfc_liveness_probes_;",
     "    (void)was_started;\n    (void)was_last;\n"
     "    ++nfc_liveness_probes_;\n"
     "    if (r == NfcLivenessResult::Deferred) {\n      return r;\n    }"),
    # ---- D-797 / D797-02.  THE CHARGING MODE-ENTRY FLOOR AT THE CALLERS.
    ("D797-02: the charging floor is ignored with no rail live -- the pre-D-797 `return true`",
     "aqroot_demo_bringup_app.h",
     "    if (rails <= 0) return chargingModeEntryAllowed(after, what);",
     "    if (rails <= 0) return true;"),
    ("D797-02: a NotPermitted charging row is treated as allowed at the "
     "caller (the Wi-Fi/BLE guard grants with no rail live)",
     "aqroot_demo_bringup_app.h",
     "    if (floor_v >= kAccessoryNotPermittedV) {\n",
     "    if (floor_v >= kAccessoryNotPermittedV) return true;\n"
     "    if (false) {\n"),
    ("D797-02: a positive charging floor is granted without any reading",
     "aqroot_demo_bringup_app.h",
     "    if (floor_v <= 0.0f) return accessoryModeEntryAllowed(false, 0.0f, 0, after);",
     "    if (floor_v < kAccessoryNotPermittedV) return true;"),
    ("D797-02: the positive charging floor is compared against a stale, "
     "unwaited reading that bypasses the admission reader (no epoch, no "
     "post-request window, no liveness proof at the grant)",
     "aqroot_demo_bringup_app.h",
     "    const bool read = readFuelCellVoltageForAdmission(what);\n"
     "    const float v = last_admission_vcell_;\n"
     "    if (accessoryModeEntryAllowed(read, v, 0, after)) return true;",
     "    const bool read = gauge_.readVcell(bus_, &last_admission_vcell_);\n"
     "    const float v = last_admission_vcell_;\n"
     "    if (accessoryModeEntryAllowed(read, v, 0, after)) return true;"),
    ("D797-02: an unqualified gauge is not qualified before the charging-floor "
     "reading, so a healthy 3.65 V pack is refused (availability, "
     "fail-closed)",
     "aqroot_demo_bringup_app.h",
     "    if (!gauge_.activeReady() && !expanders_.safeShutdownPending()) {\n"
     "      (void)configureFuelGaugeActiveMode();\n    }\n",
     ""),
    ("D797-02: the generated audio + sub-GHz charging floor is edited 3.60 -> 3.50 V",
     "aqroot_accessory_power_policy.h",
     "      3.60f,                    // 6  audio + sub-GHz",
     "      3.50f,                    // 6  audio + sub-GHz"),
]


# D-790 / D789-A04 + D789-A09 + D789-A10 + Fable V-01/V-02.  THE EXACT
# COUNTEREXAMPLES ROUND-9 RAN, ONE LEVEL FURTHER OUT AGAIN.
#
# Every one of these mutates the SHIPPED IMAGE -- `src/demo/main.cpp` -- or the
# app method its `loop()` reaches, and every one of them passed the complete
# D-789 gate suite because nothing compiled that file.  They are caught here
# because `test_production_image.cpp` compiles and RUNS `setup()`, `loop()`
# and the console dispatch over a host Arduino core and a physical-latch board
# model.
PRODUCTION_IMAGE_CONTROLS = [
    # ---- D-800 (Round-19 full review, firmware fail-closed audit) ----------
    ("D-800 image: a wedged I2C bus at boot returns before the radio quiesce",
     "demo/main.cpp",
     "    // expanders recover.  Its verdict stays pessimistic until confirmed.\n"
     "    (void)bringUpSpiBAndQuiesceRadios();\n",
     "    // expanders recover.  Its verdict stays pessimistic until confirmed.\n"),
    ("D-800 image: the quiesce retry is skipped while the expanders recover",
     "demo/main.cpp",
     "  serviceRadioQuiesceRetry();\n  if (!g_expanders.ready()) {",
     "  if (g_expanders.ready()) serviceRadioQuiesceRetry();\n"
     "  if (!g_expanders.ready()) {"),
    ("D-800 image: the IR self-test deadline is not wrap-safe",
     "aqroot_demo_peripherals.h",
     "  while (millis() - start <= 2) {",
     "  const uint32_t deadline = start + 2;\n  while (millis() <= deadline) {"),
    ("D-800 image: the SX1262 BUSY wait is not wrap-safe",
     "aqroot_demo_radios.h",
     "    if (millis() - start > timeout_ms) return false;",
     "    if (millis() > start + timeout_ms) return false;"),
    ("D-800 image: ACC_3V3 may be granted while U2's output state is UNKNOWN",
     "aqroot_demo_expanders.h",
     "  bool setAccessory3v3(I2cBus &bus, bool on) {\n    if (on) {\n      // D-800: never grant a rail while EITHER expander's output state is\n      // UNKNOWN -- a NACKed U2 write in the same loop iteration left U2's\n      // shadow invalid and D-799 still energised ACC_3V3 for 1300 ms.\n      if (!ready_ || fault_observability_lost_ || safe_shutdown_pending_ || accessoryFault()\n          || !u2_.outputShadowValid() || !u3_.outputShadowValid()) return false;",
     "  bool setAccessory3v3(I2cBus &bus, bool on) {\n    if (on) {\n      // D-800: never grant a rail while EITHER expander's output state is\n      // UNKNOWN -- a NACKed U2 write in the same loop iteration left U2's\n      // shadow invalid and D-799 still energised ACC_3V3 for 1300 ms.\n      if (!ready_ || fault_observability_lost_ || safe_shutdown_pending_ || accessoryFault()) return false;"),
    # ---- D-800 (Round-19 full review).  The boot / periodic radio quiesce
    # left the SPI peripheral bound to the SPI-B pins; the pinned core then
    # IGNORED the SPI-A begin of the display and the microSD probe.
    ("D-800 image: the radio quiesce never releases SPI, so SPI-A traffic "
     "goes out on the SPI-B pins",
     "demo/main.cpp",
     "  SPI.end();\n  return q.ok();",
     "  return q.ok();"),
    # ---- D-801 / D801-07 (Fable R20-02).  THE D-800 FIXES THAT HAD NO
    # CONTROL.  Each reverts ONE retained D-800 production fix and must fail
    # on the claim that states the behaviour the fix buys.
    ("D801-07 (a): ACC_5V may be granted while U2's output state is UNKNOWN "
     "(the 5 V twin of the ACC_3V3 control above)",
     "aqroot_demo_expanders.h",
     "  bool setAccessory5v(I2cBus &bus, bool on) {\n    if (on) {\n      // D-800: never grant a rail while EITHER expander's output state is\n      // UNKNOWN -- a NACKed U2 write in the same loop iteration left U2's\n      // shadow invalid and D-799 still energised ACC_3V3 for 1300 ms.\n      if (!ready_ || fault_observability_lost_ || safe_shutdown_pending_ || accessoryFault()\n          || !u2_.outputShadowValid() || !u3_.outputShadowValid()) return false;",
     "  bool setAccessory5v(I2cBus &bus, bool on) {\n    if (on) {\n      // D-800: never grant a rail while EITHER expander's output state is\n      // UNKNOWN -- a NACKed U2 write in the same loop iteration left U2's\n      // shadow invalid and D-799 still energised ACC_3V3 for 1300 ms.\n      if (!ready_ || fault_observability_lost_ || safe_shutdown_pending_ || accessoryFault()) return false;",
     "D801-07 (a)"),
    ("D801-07 (b): the radio quiesce binds the SPI peripheral to the SPI-A "
     "pins while it selects U7/U8/U9",
     "demo/main.cpp",
     "  g_selects.begin();\n  SPI.begin(AQROOT_PIN_SPI_B_SCK, AQROOT_PIN_SPI_B_MISO, AQROOT_PIN_SPI_B_MOSI,\n            -1);\n  const RadioQuiesce q = quiesceRadios(g_spi_b);",
     "  g_selects.begin();\n  SPI.begin(AQROOT_PIN_SPI_A_SCK, AQROOT_PIN_SPI_A_MISO, AQROOT_PIN_SPI_A_MOSI,\n            -1);\n  const RadioQuiesce q = quiesceRadios(g_spi_b);",
     "D801-07 (b)"),
    ("D801-07 (c): the microSD probe never releases SPI, so the next SPI-B "
     "begin is ignored and U9's liveness frames leave on the SPI-A pins",
     "aqroot_demo_peripherals.h",
     "  SPI.endTransaction();\n  SPI.end();\n  return result;",
     "  SPI.endTransaction();\n  return result;",
     "D801-07 (c)"),
    ("D801-07 (d1): the CC1101 quiesce's SO wait after SRES is put back on "
     "the D-799 wrapping deadline",
     "aqroot_demo_radios.h",
     "  so_start = millis();\n  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() - so_start < 10) {\n  }",
     "  const uint32_t deadline = millis() + 10;\n  while (digitalRead(AQROOT_PIN_SPI_B_MISO) == HIGH && millis() < deadline) {\n  }",
     "D801-07 (d1)"),
    ("D801-07 (d2): the microphone capture is put back on the D-799 "
     "wrapping deadline",
     "aqroot_demo_peripherals.h",
     "  const uint32_t mic_start = millis();    // D-800: wrap-safe\n  while (result.frames < want && millis() - mic_start < ms + 200) {",
     "  const uint32_t deadline = millis() + ms + 200;\n  while (result.frames < want && millis() < deadline) {",
     "D801-07 (d2)"),
    # ---- D-793 / R12-03, AT THE IMAGE LEVEL.  These are the mutations the
    # RETAINED-CC1101 scenarios in `test_production_image.cpp` exist to catch:
    # each one compiles, and each one puts the image back to believing a
    # powered transceiver is idle because a C++ member says so.
    # D-800: anchored on the NORMAL boot path -- the FATAL branch now carries
    # its own quiesce, and an unanchored replace would mutate that one.
    ("the image never quiesces the radios at boot",
     "demo/main.cpp",
     "  // and every accessory permission is refused.\n"
     "  (void)bringUpSpiBAndQuiesceRadios();",
     "  // and every accessory permission is refused.\n"
     "  (void)0;"),
    ("the image quiesces but reports the result as CONFIRMED regardless",
     "demo/main.cpp",
     "  g_app.noteRadiosQuiesced(q.cc1101_confirmed && q.sx1262_confirmed);",
     "  g_app.noteRadiosQuiesced(true);"),
    # --- D-794 / R13-03: the same mutation for the THIRD radio.  The NFC
    # field is a retained physical state on the same boot path, and reporting
    # it CONFIRMED regardless is exactly what D-793 did in prose.
    ("the image quiesces the NFC front end but reports the field as "
     "CONFIRMED OFF regardless",
     "demo/main.cpp",
     "  g_app.noteNfcFieldQuiesced(q.nfc_confirmed, q.nfc_operation_control,\n"
     "                             nfcQuiesceStepName(q.nfc.failed_at));",
     "  g_app.noteNfcFieldQuiesced(true, 0x00,\n"
     "                             nfcQuiesceStepName(q.nfc.failed_at));"),
    # --- D-794 / R13-03: the field is commanded off but never VERIFIED.  A
    # part that ACKs the Set default and keeps driving RFO1/RFO2 is exactly
    # the state the read-back exists for.
    ("the ST25R3916 quiesce trusts the power-down write instead of reading "
     "the Operation control register back",
     "aqroot_demo_radios.h",
     "  if (r.operation_control != 0x00) {",
     "  if (false) {"),
    # --- D-794 / R13-03: "Do not assume 'stop all activities' is sufficient
    # for every retained state."  C2/C3h leaves the Operation control register
    # alone, so the carrier survives it (DS12484 Rev 3 section 4.4.2).
    ("the NFC quiesce sends Stop all activities instead of Set default, "
     "which leaves the Operation control register -- and the carrier -- alone",
     "aqroot_demo_radios.h",
     "constexpr uint8_t kSetDefault = 0xC1;            // Table 13, section 4.4.1",
     "constexpr uint8_t kSetDefault = 0xC3;            // Stop all activities"),
    ("the CC1101 quiesce accepts ANY MARCSTATE at or above IDLE, which is "
     "every state including TX",
     "aqroot_demo_radios.h",
     "  return (marc & 0x1F) == kMarcstateIdle;",
     "  return (marc & 0x1F) >= kMarcstateIdle;"),
    ("the CC1101 quiesce issues the RESET STROBE as a PARTNUM read -- the "
     "burst-bit trap probeCc1101 documents, which identifies instead of "
     "resetting",
     "aqroot_demo_radios.h",
     "  SPI.transfer(kSres);                 // and reset the part outright",
     "  SPI.transfer(uint8_t(kReadBurst | kSres));"),
    ("the loop stops retrying a failed quiesce, so a board that missed it "
     "once refuses accessory power forever",
     "demo/main.cpp",
     "  if (!g_app.radiosQuiesced() ||\n"
     "      (!g_app.nfcFieldConfirmedOff() && !g_app.nfcFieldSessionActive())) {",
     "  if (false) {"),
    # --- D-792 / R11-04: the SPI-B transmit gate is never attached.  The image
    # still builds, still runs, still probes both radios -- and every future TX
    # path silently loses the accessory permission's mode edge.
    ("main never wires the SPI-B sub-GHz transmit gate to the app",
     "demo/main.cpp",
     "  g_spi_b.setAccessoryLoadAuthority(&g_app);",
     "  // gate never wired"),
    ("main wires the gate to nothing",
     "demo/main.cpp",
     "  g_spi_b.setAccessoryLoadAuthority(&g_app);",
     "  g_spi_b.setAccessoryLoadAuthority(nullptr);"),
    # --- Astra 1: the periodic battery guard is made unreachable in loop()
    ("main's periodic battery guard is made unreachable",
     "demo/main.cpp",
     "  g_app.periodicBatteryGuard();",
     "  if (false) g_app.periodicBatteryGuard();"),
    # --- Astra 2: cold boot bypasses the qualified settle
    ("main's cold boot bypasses the qualified settle with a direct "
     "configureActiveMode",
     "demo/main.cpp",
     "    const bool active = g_app.configureFuelGaugeActiveMode();",
     "    const bool active = g_fuel_gauge.configureActiveMode(g_bus);"),
    # --- Astra 3: a direct accessory enable beside a dead dispatch
    ("main enables an accessory rail directly and leaves the dispatch dead",
     "demo/main.cpp",
     """      case '3':
      case '5':
      case 'i':
      case 'l':
        (void)g_app.handleAccessoryConsole(key);
        break;""",
     """      case '3':
        (void)g_expanders.setAccessory3v3(g_bus, true);
        g_app.afterAccessoryChange();
        break;
      case '5':
      case 'i':
      case 'l':
        (void)g_app.handleAccessoryConsole(key);
        break;"""),
    # --- Astra 4 + Fable V-01: the settled post-enable recheck is removed
    ("the settled post-enable retention recheck is removed",
     "aqroot_demo_bringup_app.h",
     """  void settledAccessoryRecheck(const char *what) {
    waitServicingNfcLiveness(kAccessorySettledRecheckMs);
    applyAccessoryRetention(what);
    last_battery_guard_ms_ = millis();
  }""",
     """  void settledAccessoryRecheck(const char *what) {
    (void)what;
    last_battery_guard_ms_ = millis();
  }"""),
    # --- Fable V-01, the exact mutant: an early return before the wait
    ("settledAccessoryRecheck early-returns before its wait",
     "aqroot_demo_bringup_app.h",
     "    waitServicingNfcLiveness(kAccessorySettledRecheckMs);\n"
     "    applyAccessoryRetention(what);",
     "    if (acc3v3_ || acc5v_) return;\n"
     "    waitServicingNfcLiveness(kAccessorySettledRecheckMs);\n"
     "    applyAccessoryRetention(what);"),
    # --- D-794 / R13-01: the load-epoch rule, four ways.  Each of these is
    # the D-793 behaviour written back in, and each must be CAUGHT by the
    # stale-pre-light-step reproduction in test_production_image.cpp.
    ("the gauge reader stops waiting for a post-load conversion, which is "
     "D-793's behaviour exactly",
     "aqroot_demo_bringup_app.h",
     "    if (!waitForPostLoadConversion()) {\n      if (volts) *volts = 0.0f;\n"
     "      return false;\n    }\n    return gauge_.readVcell(bus_, volts);",
     "    return gauge_.readVcell(bus_, volts);"),
    ("the post-load window is shortened to D-779's one update, which leaves "
     "three quarters of the VCELL average describing the pre-load board",
     "aqroot_demo_bringup_app.h",
     "      delay(slice);",
     "      delay(slice / 4);"),
    # D-795 / R14-01 RETIRES D-794's IMAGE-LEVEL "the display initialisation
    # stops being a material load edge" CONTROL AS AN EQUIVALENT MUTANT AT
    # THIS LEVEL, AND SAYS WHY RATHER THAN LEAVING IT PASSING VACUOUSLY.  Every
    # admission now stamps its own request, and scenario (8) of
    # test_production_image.cpp PROVES the panel never comes up with a rail
    # live in the shipped image -- so the first VCELL reading after any panel
    # edge is necessarily an admission and the display stamp cannot change a
    # physical outcome here.  The stamp is kept (defence in depth) and its
    # control moved to PRODUCTION_CALLER_CONTROLS, where the per-site claim
    # sees it directly: "R14-01: the display initialisation is no longer
    # stamped".
    ("the load epoch never reports anything outstanding, so an armed edge "
     "costs nothing and the reader is D-793's again",
     "aqroot_accessory_power_policy.h",
     "    if (!armed_) return 0;",
     "    return 0;\n    if (!armed_) return 0;"),
    # --- Astra 5: the reset diagnostic is forced true in main's wrapper
    ("main's reset-release diagnostic is forced to report success",
     "demo/main.cpp",
     "  report(\"reset lines released (U2 P00/P01/P04)\", r.ok(), detail);",
     "  report(\"reset lines released (U2 P00/P01/P04)\", true,\n"
     "         \"CONFIRMED from U2 output latch 0xFFFF\");"),
    # --- Fable V-02: background gauge requalification disabled / no-op
    ("main's background gauge requalification is disabled",
     "demo/main.cpp",
     "  (void)g_app.backgroundGaugeRequalification();",
     "  // (void)g_app.backgroundGaugeRequalification();"),
    ("backgroundGaugeRequalification is made a no-op",
     "aqroot_demo_bringup_app.h",
     "    requal_started_ = true;\n    last_gauge_requal_ms_ = now;\n"
     "    return configureFuelGaugeActiveMode();",
     "    requal_started_ = true;\n    last_gauge_requal_ms_ = now;\n"
     "    return false;"),
    # --- D789-A09: the two non-accessory command intents
    ("main discards the amplifier shutdown result again",
     "demo/main.cpp",
     """        if (!g_app.setAmplifierIntent(false)) {
          Serial.println("audio: AMPLIFIER SHUTDOWN NOT CONFIRMED -- retry "
                         "pending; do not assume the speaker is quiet");
        }""",
     "        (void)g_expanders.setAmplifier(g_bus, false);"),
    ("the amplifier intent stops being retried from the loop",
     "demo/main.cpp",
     "  (void)g_app.serviceDeferredCommands();",
     "  // (void)g_app.serviceDeferredCommands();"),
    ("main claims the display is up without a confirmed reset release",
     "demo/main.cpp",
     """        if (!g_app.releaseDisplayResetIntent()) {
          Serial.println("display: ABORTED -- DISP_RST_N release not confirmed; "
                         "no SPI init attempted, retry pending");
          break;
        }""",
     """        (void)g_app.releaseDisplayResetIntent();"""),
    # D-791 / D790-A07 RETIRED D-790's `displayIsUp()` MUTANT AS AN EQUIVALENT
    # ONE, AND SAYS SO RATHER THAN LEAVING IT PASSING VACUOUSLY.
    #
    # D-790's control was
    #     displayIsUp() { return display_up_ && !disp_reset_intent_.pending; }
    #  -> displayIsUp() { return display_up_; }
    # and it was load-bearing THEN, because `display_up_` survived a new reset.
    # D790-A07 is the fix for exactly that, and the fix makes the mutant
    # EQUIVALENT: `releaseDisplayResetIntent()` now clears `display_up_` the
    # moment it asserts the reset, and `serviceExpanderRecovery()` clears it
    # too, so there is no reachable state in the shipped image in which
    # `display_up_` is true while a release is pending.  The `!pending` term is
    # retained as defence in depth and is documented in the header as such; a
    # control that cannot fail is not kept as if it could.  What replaces it is
    # the invariant the flag now stands for -- the flag may only go up behind a
    # real initialisation -- which IS reachable and IS mutated below.
    ("main sets the display up without re-running the initialisation",
     "demo/main.cpp",
     "        runDisplayInitialisation();\n        break;",
     "        g_app.noteDisplayInitialised(true);\n        break;"),
    # --- D789-A10: the forced-sleep guard
    ("the gauge qualification stops clearing forced sleep",
     "max17048_guard.h",
     "    if (!clearForcedSleep(bus)) return false;",
     "    (void)0;"),
    # BOTH EnSleep checks are load-bearing and each has its own control.
    # `clearForcedSleep` proves the write landed; the re-read in
    # `configureActiveMode` catches a part that fell asleep BETWEEN them,
    # which ADI's own tSLEEP mechanism does with no register write at all.
    ("clearForcedSleep stops verifying that CONFIG.SLEEP really cleared",
     "max17048_guard.h",
     "    return (after & kConfigSleepMask) == 0",
     "    return (after & 0x0000u) == 0"),
    ("the qualification stops re-checking MODE.EnSleep after the HIBRT write",
     "max17048_guard.h",
     "                    (mode & kModeHibStatMask) == 0 &&\n"
     "                    (mode & kModeEnSleepMask) == 0;",
     "                    (mode & kModeHibStatMask) == 0;"),
    # Written so it still USES `config` -- a mutant that does not compile
    # under -Wall -Wextra -Werror proves nothing.
    ("forced sleep asserted at runtime stops invalidating the reading",
     "max17048_guard.h",
     "    if ((mode & kModeHibStatMask) != 0 || (mode & kModeEnSleepMask) != 0 ||\n"
     "        (config & kConfigSleepMask) != 0) {",
     "    if ((mode & kModeHibStatMask) != 0 || (config & 0x0000u) != 0) {"),
    ("clearForcedSleep stops preserving the rest of CONFIG",
     "max17048_guard.h",
     "      const uint8_t frame[3] = {kRegConfig, uint8_t(wanted >> 8),\n"
     "                                uint8_t(wanted & 0xFF)};",
     "      const uint8_t frame[3] = {kRegConfig, 0x00, 0x00};"),
    ("an unreadable CONFIG is assumed awake instead of failing closed",
     "max17048_guard.h",
     "    if (!bus.readRegister(address_, kRegConfig, cfg, sizeof(cfg))) return false;",
     "    if (!bus.readRegister(address_, kRegConfig, cfg, sizeof(cfg))) return true;"),
    # --- D-791 / D790-A05 + Fable V-04: THE WARM-RESET RECOVERY CALL SITE.
    # Round-10's exact counterexample.  Deleting this ONE line from `loop()`'s
    # not-ready branch passed the complete D-790 release gate, because
    # `test_production_callers.cpp` drives `serviceExpanderRecovery()` as a
    # METHOD and nothing compiled the branch that calls it.  It is caught
    # BEHAVIOURALLY -- not by presence -- because `test_production_image.cpp`
    # boots the image onto a wedged bus with the PHYSICAL accessory latches
    # retained ON and requires the loop ALONE to turn them off once the bus
    # returns.
    ("main's warm-reset expander recovery is never called",
     "demo/main.cpp",
     "    (void)g_app.serviceExpanderRecovery();",
     "    // (void)g_app.serviceExpanderRecovery();"),
    ("main's warm-reset expander recovery is made unreachable",
     "demo/main.cpp",
     "    (void)g_app.serviceExpanderRecovery();",
     "    if (false) (void)g_app.serviceExpanderRecovery();"),
    ("the warm-reset recovery gives up before the bus returns",
     "aqroot_demo_bringup_app.h",
     "    const bool bus_open = bus_.reopen(AQROOT_I2C_BRINGUP_HZ);",
     "    const bool bus_open = recovery_started_ ? false\n"
     "        : bus_.reopen(AQROOT_I2C_BRINGUP_HZ);"),
    # --- D-791 / D790-A06: an aborted tone enable that later turns the
    # amplifier on.  Both halves of the cancellation are load-bearing.
    ("an aborted amplifier enable stops cancelling its ON intent",
     "aqroot_demo_bringup_app.h",
     "    if (on && !confirmed) {\n      cancelAmplifierEnable();\n    }",
     "    (void)confirmed;"),
    ("the amplifier cancellation keeps wanting the amplifier ON",
     "aqroot_demo_bringup_app.h",
     "  bool cancelAmplifierEnable() {\n    amp_intent_.want = false;",
     "  bool cancelAmplifierEnable() {\n    amp_intent_.want = true;"),
    # --- D-791 / D790-A07: a display-up flag that survives a new reset.
    ("a new display reset stops invalidating the previous initialisation",
     "aqroot_demo_bringup_app.h",
     "    display_up_ = false;\n    bool acked = expanders_.setDisplayReset(bus_, true);",
     "    bool acked = expanders_.setDisplayReset(bus_, true);"),
    ("a confirmed reset release is treated as a confirmed initialisation",
     "aqroot_demo_bringup_app.h",
     "    return disp_reset_intent_.want && !disp_reset_intent_.pending\n"
     "        && !display_up_ && expanders_.ready();",
     "    return false;"),
    ("main never completes the initialisation a deferred release owes",
     "demo/main.cpp",
     "  if (g_app.displayInitOwed()) {",
     "  if (false && g_app.displayInitOwed()) {"),
    # ---- D-795 / R14-01, PHYSICALLY.  Each of these must be caught by the
    # contamination audit or the outcome claims of the D-795 scenarios in
    # test_production_image.cpp, over the nominal and tERR +3.5 % models.
    ("R14-01 image: an admission no longer stamps its own request, so an "
     "unannounced charger unplug is admitted on the charging-era average",
     "aqroot_demo_bringup_app.h",
     "    load_epoch_.noteAdmissionRequest(millis(), admission_label_);",
     "    (void)0;"),
    ("R14-01 image: the window is D-794's nominal 1000 ms again",
     "aqroot_accessory_power_policy.h",
     "    if (elapsed >= kGaugePostLoadConversionMs) return 0;\n"
     "    return kGaugePostLoadConversionMs - elapsed;",
     "    if (elapsed >= kGaugeD794NominalWindowMs) return 0;\n"
     "    return kGaugeD794NominalWindowMs - elapsed;"),
    ("R14-01 image: the wait delays ONCE and assumes the time has passed",
     "aqroot_demo_bringup_app.h",
     "      delay(slice);\n      last_wait_ms_ += slice;",
     "      delay(slice);\n      last_wait_ms_ += slice;\n"
     "      load_epoch_.noteWindowSpent(millis() + remaining);\n"
     "      return true;"),
    ("R14-01 image: the ACC_3V3_SW rail step is no longer stamped, so the "
     "settled recheck reads an average that is still mostly pre-step",
     "aqroot_demo_bringup_app.h",
     '        if (ok) noteMaterialLoadEdge("the ACC_3V3_SW step");',
     "        (void)0;"),
    ("R14-01 image: the ACC_5V_SW retention shed is no longer stamped, so the "
     "3.3 V rail is judged on the pre-shed average and lost",
     "aqroot_demo_bringup_app.h",
     '      if (off5) noteMaterialLoadEdge("the ACC_5V_SW shed");',
     "      (void)0;"),
    # ---- D-795 / R14-02.  EVERY LIVENESS STEP, ONE CONTROL EACH.
    ("R14-02 image: the quiesce no longer proves identity BEFORE it trusts "
     "the bus -- Astra's zero-filled read then confirms FIELD OFF",
     "aqroot_demo_radios.h",
     "  if (!st25r3916IdentityIsValid(r.identity_before)) {\n"
     "    r.failed_at = NfcQuiesceStep::IdentityBefore;\n    return r;\n  }",
     "  (void)0;"),
    ("R14-02 image: the register challenge is dropped",
     "aqroot_demo_radios.h",
     "    if (r.challenge_readback[i] != kChallenge[i]) {",
     "    if (false) {"),
    ("R14-02 image: an ignored Set default is no longer detected",
     "aqroot_demo_radios.h",
     "  if (r.after_set_default != 0x00) {",
     "  if (false) {"),
    ("R14-02 image: the identity is not re-proved after the quiesce",
     "aqroot_demo_radios.h",
     "  if (!st25r3916IdentityIsValid(r.identity_after)) {",
     "  if (false) {"),
    ("R14-02 image: quiesceRadios is put back on D-794's Set-default-then-"
     "02h-equals-zero verdict, with no liveness proof at all",
     "aqroot_demo_radios.h",
     "  r.nfc = st25r3916QuiesceReport(bus);\n  r.nfc_confirmed = r.nfc.confirmed;\n"
     "  r.nfc_operation_control = r.nfc.operation_control;",
     "  (void)st25r3916_spi::command(bus, st25r3916_spi::kSetDefault);\n"
     "  (void)st25r3916_spi::readRegister(\n"
     "      bus, st25r3916_spi::kRegOperationControl, &r.nfc_operation_control);\n"
     "  r.nfc_confirmed = r.nfc_operation_control == 0x00;\n"
     "  r.nfc.confirmed = r.nfc_confirmed;\n"
     "  r.nfc.failed_at = NfcQuiesceStep::Confirmed;"),
    ("R14-02 image: main never checks the liveness of a confirmed-quiet U9",
     "demo/main.cpp",
     # D-800: the quiesce retry now sits between these two lines, so the
     # anchor is the liveness call and the comment that follows it.
     "  (void)g_app.serviceNfcLiveness();\n"
     "  // D-800: the radio quiesce retry needs SPI-B and not I2C",
     "  if (false) (void)g_app.serviceNfcLiveness();\n"
     "  // D-800: the radio quiesce retry needs SPI-B and not I2C"),
    ("R14-02 image: the liveness probe trusts the identity alone",
     "aqroot_demo_radios.h",
     "  if (!writeRegister(bus, kRegNoResponseTimer2, kChallenge[1]) ||\n"
     "      !readRegister(bus, kRegNoResponseTimer2, &back) ||\n"
     "      back != kChallenge[1]) {\n    return false;\n  }",
     "  (void)back;"),
    # ---- D-796 / D796-05 item 4 + D796-09 C-NFC-QUIESCE-01.  THE REVOCATION
    # DEADLINE.  Each of these puts back a piece of D-795's schedule, under
    # which the image left a lost U9 unrevoked for 2620 ms; each must be
    # caught by the loss sweep in test_production_image.cpp.
    ("D-796: the gauge window stops giving the liveness probe an "
     "opportunity per slice -- the 1300 ms window is unpolled again",
     "aqroot_demo_bringup_app.h",
     "      (void)serviceNfcLiveness();\n"
     "      if (nfc_revocations_ != revocations_at_entry) {",
     "      if (nfc_revocations_ != revocations_at_entry) {"),
    # D-796 MOVES "the settled recheck's electrical settle stops polling
    # liveness" TO PRODUCTION_CALLER_CONTROLS AS AN EQUIVALENT MUTANT AT THIS
    # LEVEL, AND SAYS WHY RATHER THAN LEAVING IT PASSING VACUOUSLY.  Every
    # rail admission re-proves U9's liveness AT the grant, and the 400 ms
    # recheck that follows is shorter than the 500 ms liveness period, so no
    # probe can fall due inside the recheck in the shipped image -- removing
    # its polling cannot change any physical outcome here.  The polling is
    # kept because that is a coincidence of two constants, and the caller
    # test claims it directly with the probe made due mid-recheck.
    ("D-796: an admission is granted on the last SCHEDULED liveness proof "
     "instead of one taken at the grant",
     "aqroot_demo_bringup_app.h",
     "    const NfcLivenessResult proof = serviceNfcLiveness(/*force=*/true);\n"
     "    if (!nfc_field_confirmed_off_) {\n      char line[232];",
     "    const NfcLivenessResult proof = NfcLivenessResult::Alive;\n"
     "    if (!nfc_field_confirmed_off_) {\n      char line[232];"),
    ("D-796: a burst is granted on the last SCHEDULED liveness proof",
     "aqroot_demo_bringup_app.h",
     "        ? serviceNfcLiveness(/*force=*/true)\n"
     "        : NfcLivenessResult::Alive;",
     "        ? NfcLivenessResult::Alive\n"
     "        : NfcLivenessResult::Alive;"),
    ("D-796: the liveness schedule is D-795's 1000 ms period again, which "
     "alone consumes the 1 s promise",
     "aqroot_demo_bringup_app.h",
     "now - last_nfc_liveness_ms_ < kNfcLivenessPeriodMs) {",
     "now - last_nfc_liveness_ms_ < 2 * kNfcLivenessPeriodMs) {"),
    ("D-796: setup never attaches the NFC liveness probe to the app",
     "demo/main.cpp",
     "  g_app.setNfcLivenessProbe(&probeNfcLivenessOnBusB);",
     "  g_app.setNfcLivenessProbe(nullptr);\n"
     "  (void)&probeNfcLivenessOnBusB;"),
    # ---- D-796 / D796-10.  A FIELD-OWNING SESSION OWNS 11h.
    ("D796-10: the raw liveness challenge writes 11h under a field session",
     "aqroot_demo_radios.h",
     "  if (nfcFieldSessionOwnsU9(bus)) {\n"
     "    if (identity_out) *identity_out = 0x00;\n    return false;\n  }\n",
     ""),
    ("D796-10: the scheduled probe reports a session-owned U9 as LOST, which "
     "would revoke on a scheduling fact and challenge the session's 11h",
     "aqroot_demo_radios.h",
     "  if (nfcFieldSessionOwnsU9(bus)) return NfcLivenessResult::Deferred;\n",
     ""),
    ("D796-10: the quiesce Set-defaults a field a session owns",
     "aqroot_demo_radios.h",
     "  if (nfcFieldSessionOwnsU9(bus)) {\n"
     "    r.failed_at = NfcQuiesceStep::OwnedBySession;\n    return r;\n  }\n",
     ""),
    # ---- D-796 / D796-09 C-GAUGE-EPOCH-01 (Fable G10).  A STALLED CLOCK.
    ("G10: a window the stalled clock never let pass is treated as spent, so "
     "a VCELL reading is taken with no post-load conversion behind it",
     "aqroot_demo_bringup_app.h",
     "         \"clock did not advance; no VCELL reading is taken (fail-closed)\");\n"
     "    return false;",
     "         \"clock did not advance; no VCELL reading is taken (fail-closed)\");\n"
     "    return true;"),
    ("G10: a clock that has not moved since the edge is read as a spent "
     "window",
     "aqroot_accessory_power_policy.h",
     "    const uint32_t elapsed = now_ms - edge_ms_;     // wraps correctly",
     "    const uint32_t elapsed = (now_ms == edge_ms_)\n"
     "        ? kGaugePostLoadConversionMs : now_ms - edge_ms_;"),
    # ---- D-797 / D797-08 (Fable R16-03).  A DEFERRED PROBE AT A GRANT IS NOT
    # "NO NEWS".  Each puts back D-796's reading of a Deferred forced probe
    # at one grant site -- the grant proceeds on the last scheduled proof --
    # and must be caught by the SPI-B-busy scenarios in
    # test_production_image.cpp.
    ("D797-08 image: a rail admission treats a Deferred forced probe as no "
     "news and grants on the last scheduled proof",
     "aqroot_demo_bringup_app.h",
     "    if (proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(label);",
     "    if (false && proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(label);"),
    ("D797-08 image: a non-NFC burst treats a Deferred forced probe as no "
     "news and runs on the last scheduled proof",
     "aqroot_demo_bringup_app.h",
     "    if (proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(what);",
     "    if (false && proof != NfcLivenessResult::Alive) {\n"
     "      logNfcGrantDeferred(what);"),
    ("D797-08 image: a Deferred grant REVOKES the confirmation instead of "
     "keeping it -- a scheduling accident treated as a lost part",
     "aqroot_demo_bringup_app.h",
     "  void logNfcGrantDeferred(const char *what) {\n",
     "  void logNfcGrantDeferred(const char *what) {\n"
     "    noteNfcLiveness(false, 0x00);\n"),
    # ---- D-797 / D797-10.  AN UNBOUNDED WAIT IS CAUGHT FOR A STATED REASON.
    # Before D-797 each of these ended only when the host core's recording
    # vector grew until std::bad_alloc terminated the image test with no
    # claim printed.  The fifth element is the claim text the failure MUST
    # carry: the host core's named wait guard, not memory exhaustion.
    ("D797-10: the gauge window loses its own attempt bound, so a stalled "
     "clock spins it for ever",
     "aqroot_demo_bringup_app.h",
     "    for (unsigned attempt = 0; attempt < kGaugeWindowWaitAttempts; "
     "++attempt) {",
     "    for (unsigned attempt = 0; ; ++attempt) {",
     "host guard (D797-10): a shipped wait loop kept waiting on a clock"),
    ("D797-10: the liveness-servicing wait (the settled recheck) loses its "
     "own attempt bound, so a stalled clock spins it for ever",
     "aqroot_demo_bringup_app.h",
     "    for (unsigned attempt = 0; attempt < attempts; ++attempt) {\n"
     "      (void)serviceNfcLiveness();",
     "    (void)attempts;\n"
     "    for (unsigned attempt = 0; ; ++attempt) {\n"
     "      (void)serviceNfcLiveness();",
     "host guard (D797-10): a shipped wait loop kept waiting on a clock"),
    # ---- D-797 / D797-02.  THE CHARGING FLOOR IN THE SHIPPED IMAGE: the tone
    # key with the image's own CC1101 keyed at 3.55 V.
    ("D797-02 image: the charging floor is ignored with no rail live -- the pre-D-797 `return true`",
     "aqroot_demo_bringup_app.h",
     "    if (rails <= 0) return chargingModeEntryAllowed(after, what);",
     "    if (rails <= 0) return true;"),
    ("D797-02 image: the generated audio + sub-GHz charging floor is edited 3.60 -> 3.50 V",
     "aqroot_accessory_power_policy.h",
     "      3.60f,                    // 6  audio + sub-GHz",
     "      3.50f,                    // 6  audio + sub-GHz"),
]


# ===========================================================================
# D-801 / D801-01 (Astra R20-01).  THE FAP-01 FIRST-ARTICLE IMAGE.
#
# `test_fap01_image.cpp` runs against the FAP-01 BUILD, and every control
# below is a plausible edit that would make a bench stimulus reachable where
# the release authority refuses it, unbounded, or unquiesced.  Each must fail
# on the claim that states that property (the fifth element).
FAP01_CONTROLS = [
    ("FAP-01: the CC1101 is keyed around SpiBusB::beginTransmit",
     "fap01/aqroot_fap01.cpp",
     "  if (!g_ctx.spi_b->beginTransmit(SpiBDevice::Cc1101)) {",
     "  if (false) {",
     "C: with an accessory rail live the key is REFUSED"),
    ("FAP-01: an unattended CC1101 carrier is unbounded",
     "fap01/aqroot_fap01.cpp",
     '  if (expired(g_cc_tx, kSubGhzTxMaxMs)) stopCc1101("30000 ms bound");\n',
     "",
     "C: an unattended carrier is STOPPED"),
    ("FAP-01: stopping the CC1101 releases the slot without quiescing the part",
     "fap01/aqroot_fap01.cpp",
     "  const bool idle = cc1101Quiesce(*g_ctx.spi_b, &marc);",
     "  const bool idle = true;",
     "C: the same key STOPS it"),
    ("FAP-01: an unattended SX1262 CW is unbounded",
     "fap01/aqroot_fap01.cpp",
     '  if (expired(g_sx_cw, kSubGhzTxMaxMs)) stopSx1262("30000 ms bound");\n',
     "",
     "L: an unattended CW is STOPPED"),
    ("FAP-01: the NFC field is turned on around beginNfcFieldSession",
     "fap01/aqroot_fap01.cpp",
     "  if (!g_ctx.app->beginNfcFieldSession(*g_ctx.spi_b)) return;",
     "  (void)0;",
     "N: with an accessory rail live the release session gate REFUSES"),
    ("FAP-01: an unattended NFC field is unbounded",
     "fap01/aqroot_fap01.cpp",
     '  if (expired(g_nfc_field, kNfcFieldMaxMs)) stopNfcField("60000 ms bound");\n',
     "",
     "N: an unattended field is turned OFF"),
    ("FAP-01: the Wi-Fi waiver loses its rail-off precondition",
     "fap01/aqroot_fap01.cpp",
     "        g_ctx.app->accessoryRailsOn() == 0 &&\n",
     "",
     "W: with an accessory rail live the burst is REFUSED"),
    ("FAP-01: the Wi-Fi burst never asks the release permission table",
     "fap01/aqroot_fap01.cpp",
     "  if (!g_ctx.app->wifiActivationPermitted()) {",
     "  if (true) {",
     "W: ...having ASKED the release permission table"),
    ("FAP-01: the Wi-Fi mode is never told to the permission table",
     "fap01/aqroot_fap01.cpp",
     "  g_ctx.app->noteWifiRadioActive(true);\n",
     "",
     "W: ...and the Wi-Fi mode is TOLD"),
    ("FAP-01: the Wi-Fi burst ignores the bench-source declaration",
     "fap01/aqroot_fap01.cpp",
     "  if (!benchDeclared()) {",
     "  if (false) {",
     "W: without the bench-source declaration"),
    ("FAP-01: an unattended Wi-Fi burst is unbounded",
     "fap01/aqroot_fap01.cpp",
     '  if (expired(g_wifi, kWifiBurstMaxMs)) stopWifi("10000 ms bound");\n',
     "",
     "W: an unattended burst is STOPPED"),
    ("FAP-01: the IR burst takes no burst slot",
     "fap01/aqroot_fap01.cpp",
     '  if (!g_ctx.app->burstAllowed(BurstLoad::IrTransmit, "FAP-01 IR NEC burst")) {\n'
     "    return;\n  }\n"
     "  BurstArbiter::Hold burst(g_ctx.app->burstArbiter(), BurstLoad::IrTransmit);\n"
     "  if (!burst.ok()) return;\n",
     "",
     "I: with U9's field UNKNOWN"),
    ("FAP-01: the chip-select hold-off never holds the pin",
     "fap01/aqroot_fap01.h",
     "    if (asserted && holdOffActive(device)) {",
     "    if (false && asserted && holdOffActive(device)) {",
     "H: ...the driver selected U7"),
    ("FAP-01: a hold-off armed before a warm reset is not restored at boot",
     "fap01/aqroot_fap01.cpp",
     "    if (mask & kHoldOffU7) g_ctx.selects->setHoldOff(SpiBDevice::Cc1101, true);\n",
     "",
     "H: ...the driver selected U7"),
    ("FAP-01: a chip-select hold-off is unbounded",
     "fap01/aqroot_fap01.cpp",
     '      releaseHoldOff(d, "60000 ms bound");\n',
     "      (void)d;\n",
     "H: the hold-off ends at its 60 s bound"),
    ("FAP-01: the held audio energises the amplifier around the mode edge",
     "fap01/aqroot_fap01.cpp",
     "  if (!g_ctx.app->setAmplifierIntent(true)) {",
     "  if (!g_ctx.expanders->setAmplifier(*g_ctx.bus, true)) {",
     "A: with a rail live the release mode edge REFUSES"),
    ("FAP-01: held audio is unbounded",
     "fap01/aqroot_fap01.cpp",
     '  if (expired(g_audio, kThermalHoldMaxMs)) stopAudio("30 min bound");\n',
     "",
     "A/B: unattended, both held states end"),
    ("FAP-01: the held backlight duty skips the D-784 full-duty prime",
     "fap01/aqroot_fap01.h",
     "  write_duty(255);\n  wait_us(kBacklightStartupPrimeUs);\n  write_duty(duty);",
     "  (void)wait_us;\n  write_duty(duty);",
     "B: the held backlight starts at FULL duty"),
    ("FAP-01: the VCELL poll's 10 ms pacing wait is cut to one tick",
     "fap01/aqroot_fap01.cpp",
     "         attempt < 2 * kVcellPollPeriodMs &&",
     "         attempt < 1 &&",
     "G: 200 raw VCELL samples"),
    # ---- D-802 (Round-21).  Each is the defect Round-21 reproduced, or the
    # step next to it, and each must fail on the claim that states it.
    ("D802-01: no sup3V write or read-back before the regulators (D-801's shape)",
     "fap01/aqroot_fap01.cpp",
     "  bool w = st25r3916_spi::writeRegister(*g_ctx.spi_b, kRegIoConfiguration2,\n"
     "                                        kNfcIoConfiguration2);\n"
     "  const bool supply = w && nfcSupplyModeConfirmed(&io2);",
     "  bool w = true;\n  const bool supply = true;",
     "N/sup3V: the field start writes and reads back sup3V"),
    ("D802-01: the image writes the 5 V supply mode on the 3.3 V board",
     "fap01/aqroot_fap01.cpp",
     "kNfcIoConfiguration2 = AQROOT_NFC_ON_3V3 ? kSup3v : 0x00;",
     "kNfcIoConfiguration2 = 0x00;",
     "N/sup3V: the field start writes and reads back sup3V"),
    ("D802-01: the sup3V read-back is dropped",
     "fap01/aqroot_fap01.cpp",
     "  const bool supply = w && nfcSupplyModeConfirmed(&io2);",
     "  const bool supply = w;",
     "N/sup3V: if sup3V does not read back"),
    ("D802-01: the BOM population is flipped (R106 DNP, R107 FIT) under the "
     "same image",
     "__population__", "", "",
     "N/sup3V: the field start writes and reads back sup3V"),
    ("D802-02: the Wi-Fi session is exclusive only at its start (D-801's shape)",
     "fap01/aqroot_fap01.cpp",
     "  if (g_wifi.on) {\n    switch (key) {",
     "  if (false) {\n    switch (key) {",
     "W+I: with the Wi-Fi session running"),
    ("D802-02: the session no longer starts only from a quiet board",
     "fap01/aqroot_fap01.cpp",
     "             g_backlight.on ||\n",
     "",
     "B then W: a held backlight refuses the session"),
    ("D802-03: Clear FIFO is not sent before the REQA",
     "fap01/aqroot_fap01.cpp",
     "    if (!st25r3916_spi::command(bus, kCmdClearFifo)) comm = false;\n",
     "",
     "T/stale: an ATQA left in the FIFO"),
    ("D802-03: Clear FIFO is not PROVED before the REQA",
     "fap01/aqroot_fap01.cpp",
     "    if (m0 != 0x00 || e0 != 0x00 || f1 != 0x00 || f2 != 0x00) {",
     "    if (((m0 | e0 | f1 | f2) & 0) != 0) {",
     "T/ignored: a part that ignores direct commands"),
    ("D802-03: the REQA is not required to have left (no I_txe)",
     "fap01/aqroot_fap01.cpp",
     "    } else if ((irq & kIrqTxe) == 0) {",
     "    } else if (false) {",
     "T/ignored: a part that ignores the REQA itself"),
    ("D802-03: the ATQA is not checked for ISO/IEC 14443-3 plausibility",
     "fap01/aqroot_fap01.cpp",
     "    } else if (drained && !atqaPlausible(atqa[1], atqa[2])) {",
     "    } else if (drained && !atqaPlausible(0x04, 0x00)) {",
     "T/implausible: a two-byte receive of FF FF"),
    ("D802-03: an armed U9 hold-off does not refuse the REQA",
     "fap01/aqroot_fap01.cpp",
     "  if (cs.holdOffArmed(SpiBDevice::St25r3916)) {",
     "  if (false) {",
     "T/chip-select: with a U9 hold-off armed"),
    ("D802-03: a failed U9 transfer is not treated as invalid evidence",
     "fap01/aqroot_fap01.cpp",
     '    invalid = "an SPI-B transfer on U9 did not complete (bus hold refused)";',
     "    (void)0;",
     "T/transfer: a U9 transfer that cannot take the bus"),
    # ---- D-803 (Round-22 R22-01).  Each is a way back to trusting a dead or
    # recovering bus; each must fail on the claim that states it.
    ("D803-01: liveness is proved at the END only (Astra R22-01's rejected "
     "shape)",
     "fap01/aqroot_fap01.cpp",
     "    if (invalid != nullptr || !comm) return;\n    if (!u9Live(bus, comm)",
     "    if (invalid != nullptr || !comm) return;\n"
     "    if (__builtin_strstr(where, \"after the REQA\") == nullptr) return;\n"
     "    if (!u9Live(bus, comm)",
     "T/live: a U9 that fails for any 1..40 bytes"),
    ("D803-01: no liveness proof across the IRQ / FIFO clear",
     "fap01/aqroot_fap01.cpp",
     '  live("U9 stopped answering live across the IRQ / FIFO clear");\n',
     "",
     "T/live: a stale I_rxe and a stale ATQA"),
    ("D803-01: no liveness proof during the REQA / ATQA read",
     "fap01/aqroot_fap01.cpp",
     '  live("U9 stopped answering live during the REQA / ATQA read");\n',
     "",
     "T/live: a U9 that fails for any 1..40 bytes"),
    ("D803-01: the liveness proof ends on the 00h restore, which a zero bus "
     "fakes",
     "fap01/aqroot_fap01.cpp",
     "  return live && rb == kNrt2Default && st25r3916IdentityIsValid(id);",
     "  return live && rb == kNrt2Default;",
     "T/live: a U9 that stops answering at ANY byte"),
    ("D803-01: the fresh boundary does not re-read the IRQs after the clear",
     "fap01/aqroot_fap01.cpp",
     "    if (m0 != 0x00 || e0 != 0x00 || f1 != 0x00 || f2 != 0x00) {",
     "    if (((m0 | e0) & 0) != 0 || f1 != 0x00 || f2 != 0x00) {",
     "T/live: a stale I_rxe that survived a deaf clear"),
    ("D803-01: the final FIFO / IRQ accounting is dropped",
     "fap01/aqroot_fap01.cpp",
     "    if (a1 != 0x00 || (a2 & 0xF0) != 0x00) {",
     "    if (((a1 | a2) & 0) != 0) {",
     "T/live: a U9 that fails for any 1..40 bytes"),
    ("D803-01: a receive error is judged only with I_rxe (D-802's order)",
     "fap01/aqroot_fap01.cpp",
     "    } else if ((err & kErrorIrqReceive) != 0) {",
     "    } else if ((irq & kIrqRxe) != 0 && (err & kErrorIrqReceive) != 0) {",
     "T/live: a receive that raised I_col"),
    ("D803-01: I_rxs without I_rxe is reported as no tag",
     "fap01/aqroot_fap01.cpp",
     '      if ((irq & kIrqRxs) != 0) invalid = "a receive started (I_rxs) but never ended";\n'
     "      else if (count != 0)",
     "      if (count != 0)",
     "T/live: a receive that raised I_col"),
    ("D803-01: the ATQA bit-frame anticollision rule is dropped (00 00 passes)",
     "fap01/aqroot_fap01.cpp",
     "  return anticollision != 0 && (anticollision & (anticollision - 1)) == 0\n"
     "      && (lsb & 0x20) == 0",
     "  (void)anticollision;\n  return (lsb & 0x20) == 0",
     "T/live: a two-byte receive of 00 00"),
    ("D803-01: the challenge leaves No-response timer 2 armed",
     "fap01/aqroot_fap01.cpp",
     "constexpr uint8_t kNrt2Default = 0x00;",
     "constexpr uint8_t kNrt2Default = 0x5A;",
     "T/live: the liveness challenge leaves No-response timer 2"),
    # ---- D-803 (Round-22 R22-05): the hold-off operator wording is bound
    # to the behaviour.
    ("D803-05: the arm line goes back to 'survives ONE warm reset'",
     "fap01/aqroot_fap01.cpp",
     '                    ? "; it is ALSO RECORDED for the NEXT FAP-01 boot of ANY "\n'
     '                      "kind (EN pulse, power cycle or reflash) -- press Q and "\n'
     '                      "see \'NVS confirmed clear\' before powering off or "\n'
     '                      "reflashing, unless you are testing persistence"\n',
     '                    ? "; it also survives ONE warm reset"\n',
     "J/record: the arm line says the hold-off is recorded"),
    ("D803-05: Q no longer erases a record it did not write this boot",
     "fap01/aqroot_fap01.cpp",
     "  if (p.getUChar(kNvsHoldOff, 0) != 0) (void)p.remove(kNvsHoldOff);\n"
     "  const bool clear",
     "  const bool clear",
     "J/record: a stale record with nothing armed is still ERASED"),
    ("D803-05: Q reports clear without reading the record back",
     "fap01/aqroot_fap01.cpp",
     "  if (p.getUChar(kNvsHoldOff, 0) != 0) (void)p.remove(kNvsHoldOff);\n"
     "  const bool clear = p.getUChar(kNvsHoldOff, 0) == 0;",
     "  const bool clear = true;",
     "J/record: a stale record with nothing armed is still ERASED"),
    ("D803-05: the boot no longer consumes the record (it would re-arm on "
     "every boot)",
     "fap01/aqroot_fap01.cpp",
     "    if (mask != 0) (void)p.remove(kNvsHoldOff);\n",
     "",
     "J/record: ...a POWER CYCLE carries it"),
    ("D802: an all-ones VCELL register is printed as a plain sample",
     "fap01/aqroot_fap01.cpp",
     "      const bool implausible = counts == 0xFFFF || counts == 0x0000;",
     "      const bool implausible = false;",
     "G: an all-ones VCELL register is marked IMPLAUSIBLE"),
    ("FAP-01: main.cpp stops servicing the FAP-01 bounds from loop()",
     "demo/main.cpp",
     "  fap01::service();\n",
     "",
     "C: an unattended carrier is STOPPED"),
]

# The NEGATIVE half: the same test compiled into the RELEASE build.  Its one
# control is the build-configuration leak -- the FAP-01 define and sources
# reaching the release image -- and it must fail on the claim that the
# release image does not recognise a FAP-01 key.
FAP01_RELEASE_CONTROLS = [
    ("RELEASE: the FAP-01 define and src/fap01/ leak into the release build",
     "__build__", "", "",
     "RELEASE: no FAP-01 key is recognised"),
]

BUS_CONTROLS = [
    # ---- D-793 / R12-03.  `transmitting_` is a C++ member and an MCU reset
    # zeroes it; U7 and U8 stay powered.  Until the boot path has proven the
    # physical state, NO transmitter may be keyed -- the NFC front end
    # included, which is exempt from the LOAD rule and not from this one.
    ("the bus stops asking whether the physical radio state is known before "
     "keying a transmitter",
     "aqroot_spi_bus_b.h",
     "    if (authority_ != nullptr && !authority_->radioPhysicalStateIsKnown()) {",
     "    if (authority_ == nullptr && false) {"),
    ("the bus accepts a second concurrent chip select",
     "aqroot_spi_bus_b.h",
     "    if (selected_ != SpiBDevice::None) return false;",
     "    if (selected_ != SpiBDevice::None && selected_ != device) return false;"),
    ("a second radio may key while the first is transmitting",
     "aqroot_spi_bus_b.h",
     "    if (transmitting_ != SpiBDevice::None) return false;",
     "    if (transmitting_ != SpiBDevice::None && transmitting_ != device) return false;"),
    ("Hold stops releasing the bus when it leaves scope",
     "aqroot_spi_bus_b.h",
     "    ~Hold() { if (ok_) bus_.release(); }",
     "    ~Hold() {}"),
    # ---- D-792 / R11-04.  THE SUB-GHZ MODE EDGE. --------------------------
    ("a sub-GHz transmitter may be keyed without asking the accessory load "
     "authority at all",
     "aqroot_spi_bus_b.h",
     """    if (isSubGhz(device) && authority_ != nullptr &&
        !authority_->subGhzTransmitPermitted()) {
      return false;
    }""",
     "    // gate removed"),
    ("the authority is asked but its refusal is ignored",
     "aqroot_spi_bus_b.h",
     "        !authority_->subGhzTransmitPermitted()) {",
     "        !authority_->subGhzTransmitPermitted() && false) {"),
    ("the authority is never told a transmission started, so its mode set "
     "goes stale",
     "aqroot_spi_bus_b.h",
     """    if (isSubGhz(device) && authority_ != nullptr) {
      authority_->noteSubGhzTransmitting(true);
    }""",
     "    // notification removed"),
    ("the authority is never told a transmission ENDED, so the mode set "
     "sticks on and refuses everything afterwards",
     "aqroot_spi_bus_b.h",
     """    if (isSubGhz(device) && authority_ != nullptr) {
      authority_->noteSubGhzTransmitting(false);
    }""",
     "    // notification removed"),
    ("the NFC field is gated too, which charges its bounded-duty allowance "
     "twice",
     "aqroot_spi_bus_b.h",
     "  static bool isSubGhz(SpiBDevice device) {\n    return device == SpiBDevice::Cc1101 || device == SpiBDevice::Sx1262;",
     "  static bool isSubGhz(SpiBDevice device) {\n    return device != SpiBDevice::None;"),
]

ORDER_CONTROLS = [
    ("UNKNOWN accessory latch state is falsely reported OFF to the caller",
     "aqroot_demo_expanders.h",
     "  if (!known) r3 = r5 = buf = true;",
     "  if (!known) r3 = r5 = buf = false;"),
    # Round 4: a runtime accessory fail-safe must not assert the display,
    # touch, and LoRa reset lines merely because they share U2 with ACC_PWR_EN.
    ("runtime accessory fail-safe blanket-writes U2's full boot-safe latch",
     "aqroot_demo_expanders.h",
     """    if (u2_known) {
      u2_ok = u2_.clearBits(bus, kU2AccessoryMask);
    }""",
     """    if (u2_known) {
      u2_ok = u2_.writeOutputs(bus, kU2SafeLatch);
    }"""),
    ("direction is written before the output latch",
     "pcal9535a.h",
     """    shadow_valid_ = false;
    if (!writeOutputs(bus, config.output_latch)) return false;""",
     """    shadow_valid_ = false;
    if (!writePortPair(bus, address_, kRegConfig0, config.direction)) return false;
    if (!writeOutputs(bus, config.output_latch)) return false;"""),
    ("a fresh MCU invents a valid zero output shadow after warm reset",
     "pcal9535a.h",
     "shadow_(0xFFFF), shadow_valid_(false)",
     "shadow_(0x0000), shadow_valid_(true)"),
    ("Output Port Configuration is changed to open-drain before outputs",
     "pcal9535a.h",
     "if (!writeRegister(bus, address_, kRegOutputConfig, 0x00)) return false;",
     "if (!writeRegister(bus, address_, kRegOutputConfig, 0xFF)) return false;"),
    ("warm reset skips the immediate U3 complete safe-latch write",
     "aqroot_demo_expanders.h",
     "const bool u3_safe = u3_.writeOutputs(bus, kU3SafeLatch);",
     "const bool u3_safe = true;"),
    ("the RGB cathodes boot at 0, lighting the LED at power-on",
     "aqroot_demo_expanders.h",
     "constexpr uint16_t kU3SafeLatch = kRgbMask;",
     "constexpr uint16_t kU3SafeLatch = 0x0000;"),
    ("the 5 V load switch is closed before the boost is enabled",
     "aqroot_demo_expanders.h",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_BOOST_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }
      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }""",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }
      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_BOOST_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }"""),
    ("a U2 configuration failure short-circuits the independent U3 configuration",
     "aqroot_demo_expanders.h",
     """    const bool u2_ok = u2_.apply(bus, u2);
    const bool u3_ok = u3_.apply(bus, u3);""",
     """    const bool u2_ok = u2_.apply(bus, u2);
    const bool u3_ok = u2_ok && u3_.apply(bus, u3);"""),
    ("a U2 read error stops U3 being serviced (service short-circuits)",
     "aqroot_demo_expanders.h",
     """    const bool a = u2_.readInterruptStatus(bus, &u2_irq_);
    const bool b = u3_.readInterruptStatus(bus, &u3_irq_);
    const bool c = u2_.readInputs(bus, &u2_inputs_);
    const bool d = u3_.readInputs(bus, &u3_inputs_);""",
     """    if (!u2_.readInterruptStatus(bus, &u2_irq_)) return false;
    if (!u3_.readInterruptStatus(bus, &u3_irq_)) return false;
    if (!u2_.readInputs(bus, &u2_inputs_)) return false;
    if (!u3_.readInputs(bus, &u3_inputs_)) return false;
    const bool a = true, b = true, c = true, d = true;"""),
    ("a failed output write leaves the shadow trusted",
     "pcal9535a.h",
     """    if (!writePortPair(bus, address_, kRegOutput0, value)) {
      shadow_valid_ = false;
      return false;
    }""",
     """    if (!writePortPair(bus, address_, kRegOutput0, value)) return false;"""),
    ("partial 5 V enable failure no longer enters safety recovery",
     "aqroot_demo_expanders.h",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }""",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true)) {
        return false;
      }"""),
    ("lost-ACK 3.3 V enable failure no longer enters safety recovery",
     "aqroot_demo_expanders.h",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_3V3_EN, true)) {
        (void)applyAccessorySafeState(bus);
        return false;
      }""",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_3V3_EN, true)) {
        return false;
      }"""),
    ("failed boot-safe latch write is forgotten instead of staying pending",
     "aqroot_demo_expanders.h",
     """    if (!u2_safe || !u3_safe || !u2_ok || !u3_ok) {
      if (!u2_safe || !u3_safe) safe_shutdown_pending_ = true;
      return false;
    }""",
     """    if (!u2_safe || !u3_safe || !u2_ok || !u3_ok) {
      return false;
    }"""),
    ("uncertain I2C-buffer OFF write is allowed to poison U2 state without safety recovery",
     "aqroot_demo_expanders.h",
     """      (void)applyAccessorySafeState(bus);
      return false;
    }
    return true;
  }

  Pcal9535a &u2()""",
     """      if (on) (void)applyAccessorySafeState(bus);
      return false;
    }
    return true;
  }

  Pcal9535a &u2()"""),
    ("generic invalid output shadow is never scheduled for accessory-safe reconciliation",
     "aqroot_demo_expanders.h",
     """    if (!u2_.outputShadowValid() || !u3_.outputShadowValid()) {
      safe_shutdown_pending_ = true;
    }""",
     """    if (!u2_.outputShadowValid() || !u3_.outputShadowValid()) {
      /* uncertainty ignored */
    }"""),
]



# ===========================================================================
# D-801 / D801-03 + D801-01.  platformio.ini, READ THE WAY PLATFORMIO READS IT.
#
# Round-20 (Astra R20-03, Fable R20-02 overlap): changing `default_envs` to the
# legacy `esp32-s3-aqroot` left H1-H8 green.  A bare `pio run -t upload` then
# flashes a placeholder-pin image onto a Demo board (D-800), and with FAP-01
# in the tree a default could just as easily be the diagnostic image.  H9
# asserts the default; H10 asserts where FAP-01 can and cannot reach.  Both
# parse the file -- comments, multi-line values, `${section.option}`
# interpolation and `extends` -- rather than grep it, and both are exercised by
# destructive controls on the TEXT, so a future edit that the parser misreads
# is a control that fails, not a gate that passes.
def _pio_parse(text):
    # D-803 / D803-04: STRICT, as PlatformIO is -- a duplicated option or
    # section is refused ("option 'default_envs' in section 'platformio'
    # already exists"), never resolved last-one-wins behind its back.
    cp = configparser.RawConfigParser(comment_prefixes=(";", "#"),
                                      inline_comment_prefixes=(";",),
                                      strict=True, delimiters=("=",))
    cp.optionxform = str
    cp.read_string(text)
    return cp


def _pio_get(cp, section, option, depth=0):
    """An option with PlatformIO's `${section.option}` interpolation and
    `extends` inheritance applied; None when absent."""
    if depth > 16 or not cp.has_section(section):
        return None
    if not cp.has_option(section, option):
        if cp.has_option(section, "extends"):
            for parent in re.split(r"[,\s]+", cp.get(section, "extends").strip()):
                if parent:
                    value = _pio_get(cp, parent, option, depth + 1)
                    if value is not None:
                        return value
        return None

    def _sub(match):
        sec, _, opt = match.group(1).rpartition(".")
        value = _pio_get(cp, sec, opt, depth + 1)
        return value if value is not None else ""
    return re.sub(r"\$\{([^}]+)\}", _sub, cp.get(section, option))


def _pio_default_envs(cp):
    raw = cp.get("platformio", "default_envs", fallback=None) \
        if cp.has_section("platformio") else None
    if raw is None:
        return None
    return [e for e in re.split(r"[,\s]+", raw.strip()) if e]


def _default_env_problems(text):
    problems = []
    try:
        cp = _pio_parse(text)
    except (configparser.DuplicateOptionError,
            configparser.DuplicateSectionError) as exc:
        return ["platformio.ini repeats an option or section (PlatformIO "
                "refuses the file; a last-one-wins reading would pick a "
                "default behind its back): %s" % exc]
    except configparser.Error as exc:
        return ["platformio.ini does not parse: %s" % exc]
    if not cp.has_section("platformio"):
        problems.append("no [platformio] section: a bare `pio run` builds and "
                        "uploads EVERY environment in file order")
        return problems
    if cp.has_option("platformio", "extra_configs"):
        problems.append("[platformio] names extra_configs, which can re-define "
                        "default_envs outside this file")
    envs = _pio_default_envs(cp)
    if envs is None:
        problems.append("default_envs is missing: a bare `pio run -t upload` "
                        "flashes every environment, legacy placeholder images "
                        "included")
    elif envs != [RELEASE_ENV]:
        problems.append("default_envs is %r; it must be exactly and solely "
                        "[%r]" % (envs, RELEASE_ENV))
    for name in NAMED_ENVS:
        if not cp.has_section("env:%s" % name):
            problems.append("[env:%s] is gone, so it no longer builds by name"
                            % name)
    return problems


def _src_files():
    base = ROOT / "Firmware/src"
    return sorted(p.relative_to(base).as_posix() for p in base.rglob("*")
                  if p.suffix in (".c", ".cc", ".cpp", ".S"))


def _src_filter_selects(filter_text, files):
    """PlatformIO's `build_src_filter`, applied in order: `+<p>` adds and
    `-<p>` removes; `dir/` means everything under it and `*` everything."""
    selected = set()
    for sign, pat in re.findall(r"([+-])<([^>]*)>", filter_text):
        if pat in ("*", "**", "*/", "**/"):
            hit = set(files)
        elif pat.endswith("/"):
            hit = {f for f in files if f.startswith(pat)}
        else:
            hit = {f for f in files
                   if fnmatch.fnmatch(f, pat) or f.startswith(pat + "/")}
        selected = selected | hit if sign == "+" else selected - hit
    return selected


def _preprocess_main(main_text, define):
    """`demo/main.cpp` through the host image core's preprocessor, with or
    without the FAP-01 define.  Returns (ok, text)."""
    with tempfile.TemporaryDirectory(prefix="aqroot-pp-") as temporary:
        work = Path(temporary)
        shutil.copytree(HW_DIR, work / "hw")
        shutil.copytree(IMAGE_HARNESS, work / "image")
        if HOST_HARNESS.exists():
            shutil.copytree(HOST_HARNESS, work / "harness")
        if FAP01_DIR.exists():
            shutil.copytree(FAP01_DIR, work / "fap01")
        (work / "demo").mkdir()
        (work / "demo" / "main.cpp").write_text(main_text, encoding="utf-8")
        cmd = ["g++", "-std=c++17", "-E", "-P", "-DARDUINO=200",
               "-I", str(work / "image"), "-I", str(work / "hw"),
               "-I", str(work)]
        if define:
            cmd.append("-D" + FAP01_DEFINE)
        run = subprocess.run(cmd + [str(work / "demo" / "main.cpp")],
                             capture_output=True, text=True)
        return run.returncode == 0, run.stdout if run.returncode == 0 \
            else run.stderr[-600:]


def _fap01_isolation_problems(ini_text, main_text, header_text, cpp_text):
    problems = []
    try:
        cp = _pio_parse(ini_text)
    except configparser.Error as exc:
        return ["platformio.ini does not parse: %s" % exc]
    files = _src_files()
    envs = [sec[4:] for sec in cp.sections() if sec.startswith("env:")]
    if FAP01_ENV not in envs:
        problems.append("[env:%s] is missing: FAP-01 has no build" % FAP01_ENV)
    for env in envs:
        section = "env:%s" % env
        flt = _pio_get(cp, section, "build_src_filter")
        if flt is None:
            flt = "+<*> -<.git/> -<.svn/>"       # PlatformIO's default
        flags = _pio_get(cp, section, "build_flags") or ""
        selected = _src_filter_selects(flt, files)
        fap_sources = sorted(f for f in selected if f.startswith("fap01/"))
        defined = re.search(r"-D\s*%s\b" % FAP01_DEFINE, flags) is not None
        if env == FAP01_ENV:
            # D-802 / D802-03 (Round-21 R21-03): the legacy PN532/I2C NFC
            # driver is the WRONG PART and is never an ST25R3916 fallback --
            # not compiled, not linked, not a dependency of FAP-01.
            legacy = sorted(f for f in selected
                            if not f.startswith(("demo/", "hw/", "fap01/")))
            if legacy:
                problems.append("[env:%s] compiles sources outside demo/ hw/ "
                                "fap01/ (the legacy tree, PN532 included): %s"
                                % (env, legacy[:6]))
            deps = _pio_get(cp, section, "lib_deps") or ""
            if re.search(r"PN532", deps, re.I):
                problems.append("[env:%s] depends on a PN532 library" % env)
            if not fap_sources:
                problems.append("[env:%s] does not compile src/fap01/" % env)
            if not defined:
                problems.append("[env:%s] does not define %s" % (env, FAP01_DEFINE))
            if "demo/main.cpp" not in selected:
                problems.append("[env:%s] does not compile the release "
                                "demo/main.cpp" % env)
        else:
            if fap_sources:
                problems.append("[env:%s] compiles FAP-01 sources %s"
                                % (env, fap_sources))
            if defined:
                problems.append("[env:%s] defines %s" % (env, FAP01_DEFINE))
    if RELEASE_ENV in envs:
        rel = _src_filter_selects(
            _pio_get(cp, "env:%s" % RELEASE_ENV, "build_src_filter") or "",
            files)
        if "demo/main.cpp" not in rel:
            problems.append("[env:%s] no longer compiles demo/main.cpp"
                            % RELEASE_ENV)
    for name, text in (("aqroot_fap01.h", header_text),
                       ("aqroot_fap01.cpp", cpp_text)):
        hits = sorted(set(re.findall(r"PN532\w*|\bnfc_init\b|drivers/nfc",
                                     strip_comments(text), re.I)))
        if hits:
            problems.append("src/fap01/%s reaches the legacy PN532 driver: %s"
                            % (name, hits))
    guard = re.compile(r"#if\s+!\s*defined\s*\(\s*%s\s*\)\s*\n\s*#error"
                       % FAP01_DEFINE)
    if not guard.search(header_text):
        problems.append("src/fap01/aqroot_fap01.h no longer refuses to compile "
                        "without %s" % FAP01_DEFINE)
    if not guard.search(cpp_text):
        problems.append("src/fap01/aqroot_fap01.cpp no longer refuses to "
                        "compile without %s" % FAP01_DEFINE)
    ok, text = _preprocess_main(main_text, define=False)
    if not ok:
        problems.append("the RELEASE demo/main.cpp does not preprocess without "
                        "%s: %s" % (FAP01_DEFINE, text.strip().splitlines()[-1]
                                    if text.strip() else "?"))
    else:
        leaked = sorted(set(re.findall(r"\bfap01::\w+|\bHoldOffChipSelects\b"
                                       r"|\bAQROOT_FAP01\w*", text)))
        if leaked:
            problems.append("the RELEASE demo/main.cpp preprocesses to FAP-01 "
                            "code: %s" % leaked)
    ok, text = _preprocess_main(main_text, define=True)
    hooks = ("fap01::begin", "fap01::announce", "fap01::service",
             "fap01::handleKey", "fap01::HoldOffChipSelects")
    missing = [h for h in hooks if not ok or h not in text]
    if missing:
        problems.append("the FAP-01 demo/main.cpp is missing its hooks %s"
                        % missing)
    return problems


FAP01_PROCEDURE = ROOT / "docs/full-beta-v2/assembly/FAP01_FIRST_ARTICLE_IMAGE.md"
FIRST_FIVE_PLAN = ROOT / "docs/full-beta-v2/assembly/FIRST_FIVE_ASSEMBLY_PLAN.md"
ACCEPTANCE_REGISTER = ROOT / "docs/full-beta-v2/assembly/RELEASE_ACCEPTANCE_REGISTER.json"
# D-803 / D803-05: the phrases that carry the hold-off rule, and the D-802
# phrases that understated it.
FAP01_WORDING_DOC = (
    "Also **recorded in NVS for the NEXT FAP-01 boot of ANY kind** — an `EN` "
    "pulse, a **power cycle**, or the first FAP-01 boot after a reflash "
    "(D-803).  **Press `Q` and see `NVS confirmed clear` before powering off "
    "or reflashing, unless you are intentionally testing persistence.**",
    "rule (D-803 / D803-05): press `Q` and see `NVS confirmed clear` before\n"
    "  powering off or reflashing — EXCEPT when persistence is the thing being\n"
    "  tested**")
FAP01_WORDING_PLAN = ("it is carried into the NEXT FAP-01 boot of ANY\n> kind — "
                      "`EN` pulse, power cycle or reflash — so press `Q` and see "
                      "`NVS\n> confirmed clear` before power-off or reflash "
                      "unless testing persistence")
FAP01_WORDING_STALE = ("survives ONE warm reset", "survives one reset",
                       "for **one** following reset", "recorded for one reset",
                       "survives at most one reset",
                       "exactly one reset of any kind (an `EN` pulse or a "
                       "power cycle)")


def _fap01_wording_problems(doc, plan, cpp, header):
    problems = []
    for phrase in FAP01_WORDING_DOC:
        if phrase not in doc:
            problems.append("FAP01_FIRST_ARTICLE_IMAGE.md does not carry the "
                            "hold-off rule: %r" % phrase[:70])
    if FAP01_WORDING_PLAN not in plan:
        problems.append("FIRST_FIVE_ASSEMBLY_PLAN.md does not carry the "
                        "hold-off rule (next FAP-01 boot of any kind; Q first)")
    register = (ACCEPTANCE_REGISTER.read_text(encoding="utf-8")
                if ACCEPTANCE_REGISTER.exists() else "")
    if "NEXT FAP-01 boot of ANY kind" not in register:
        problems.append("RELEASE_ACCEPTANCE_REGISTER.json's FAP-01 H row does "
                        "not carry the hold-off rule")
    for name, text in (("FAP01_FIRST_ARTICLE_IMAGE.md", doc),
                       ("FIRST_FIVE_ASSEMBLY_PLAN.md", plan),
                       ("RELEASE_ACCEPTANCE_REGISTER.json", register),
                       ("aqroot_fap01.cpp", cpp), ("aqroot_fap01.h", header)):
        for stale in FAP01_WORDING_STALE:
            if stale in text:
                problems.append("%s understates the hold-off record: %r"
                                % (name, stale))
    return problems


def _pio_executable(configured=None, path=None):
    """D-803 / D803-04.  The PlatformIO the cross-check runs: the CONFIGURED
    path first (`PIO`, i.e. `AQROOT_PIO` or the worker's venv), then `pio`
    and `platformio` on PATH.  Returns (path or None, how it was found)."""
    configured = PIO if configured is None else Path(configured)
    if configured.is_file() and os.access(str(configured), os.X_OK):
        return configured, "configured %s" % configured
    for name in ("pio", "platformio"):
        found = shutil.which(name, path=path)
        if found:
            return Path(found), "%s on PATH (%s)" % (name, found)
    return None, ("no PlatformIO: %s absent, neither `pio` nor `platformio` "
                  "on PATH" % configured)


def _pio_project_config(project_dir=None, configured=None, path=None):
    """What PlatformIO ITSELF resolves as the default, when it is installed."""
    exe, how = _pio_executable(configured, path)
    if exe is None:
        return {"available": False, "executable": None, "found_by": how}
    run = subprocess.run([str(exe), "project", "config", "--json-output",
                          "-d", str(project_dir or (ROOT / "Firmware"))],
                         capture_output=True, text=True, timeout=300)
    if run.returncode != 0:
        return {"available": True, "executable": str(exe), "found_by": how,
                "error": run.stderr[-400:]}
    try:
        sections = json.loads(run.stdout)
    except ValueError:
        return {"available": True, "error": "unparseable JSON"}
    table = {name: dict(opts) for name, opts in sections}
    return {
        "available": True, "executable": str(exe), "found_by": how,
        "default_envs": table.get("platformio", {}).get("default_envs"),
        "environments": sorted(n[4:] for n in table if n.startswith("env:")),
    }


def _h9_evaluate(ini_text, configured=None, path=None):
    """D-803 / D803-04.  H9's verdict on one platformio.ini: the parser, and
    the REQUIRED PlatformIO cross-check run on a fixture project holding
    exactly that file.  An unavailable or failing PlatformIO is a problem --
    it never contributes a PASS -- and the two readings must agree."""
    problems = list(_default_env_problems(ini_text))
    with tempfile.TemporaryDirectory(prefix="aqroot-h9-") as temporary:
        project = Path(temporary) / "Firmware"
        project.mkdir()
        (project / "platformio.ini").write_text(ini_text, encoding="utf-8")
        view = _pio_project_config(project, configured, path)
    if not view.get("available"):
        problems.append("the REQUIRED PlatformIO cross-check is UNAVAILABLE "
                        "(%s): the parser alone does not pass H9"
                        % view.get("found_by"))
    elif "error" in view:
        problems.append("`pio project config` failed: %s" % view["error"])
    else:
        if view.get("default_envs") != [RELEASE_ENV]:
            problems.append("PlatformIO itself resolves default_envs to %r"
                            % view.get("default_envs"))
        try:
            cp = _pio_parse(ini_text)
            parsed = _pio_default_envs(cp)
            parsed_envs = sorted(sec[4:] for sec in cp.sections()
                                 if sec.startswith("env:"))
        except configparser.Error:
            parsed, parsed_envs = None, None
        if parsed is not None and parsed != view.get("default_envs"):
            problems.append("the parser (%r) and PlatformIO (%r) DISAGREE on "
                            "default_envs" % (parsed, view.get("default_envs")))
        if parsed_envs is not None and \
                parsed_envs != view.get("environments"):
            problems.append("the parser and PlatformIO DISAGREE on the "
                            "environments: %r vs %r"
                            % (parsed_envs, view.get("environments")))
        for name in NAMED_ENVS:
            if name not in view.get("environments", []):
                problems.append("PlatformIO does not see [env:%s]" % name)
    return {"problems": problems, "pio_project_config": view}


def _h9_portability_controls(ini_text, default_line):
    """D-803 / D803-04.  Each row runs `_h9_evaluate` end to end and states
    the verdict it must reach."""
    rows = []
    real, _ = _pio_executable()
    absent = Path(tempfile.gettempdir()) / "aqroot-h9-no-such-pio"

    def row(case, text, must_pass, configured=None, path=None):
        ev = _h9_evaluate(text, configured, path)
        passed = not ev["problems"]
        rows.append(dict(case=case, must_pass=must_pass, passed=passed,
                         found_by=ev["pio_project_config"].get("found_by"),
                         first_problem=(ev["problems"] or [None])[0],
                         ok=passed == must_pass))
    row("the PlatformIO executable is ABSENT (no configured path, empty "
        "PATH): not a PASS", ini_text, False, absent, "")
    if real is None:
        rows.append(dict(case="PATH-only pio / platformio", ok=False,
                         first_problem="no real PlatformIO to link"))
    else:
        with tempfile.TemporaryDirectory(prefix="aqroot-h9-path-") as tmp:
            for name in ("pio", "platformio"):
                d_ = Path(tmp) / name
                d_.mkdir()
                (d_ / name).symlink_to(real)
                row("PATH-only `%s` (configured path absent) is FOUND and "
                    "the valid file passes" % name, ini_text, True, absent,
                    str(d_) + os.pathsep + "/usr/bin:/bin")
    row("the normal aqroot-demo default passes", ini_text, True)
    # a PlatformIO that reads the file differently from the parser -- a stub
    # executable reporting the release default beside a second environment
    # list -- must be a DISAGREEMENT, never a pass
    with tempfile.TemporaryDirectory(prefix="aqroot-h9-stub-") as tmp:
        stub = Path(tmp) / "pio"
        stub.write_text(
            "#!%s\nimport json\nprint(json.dumps([['platformio', "
            "[['default_envs', ['aqroot-demo', 'wokwi']]]], ['env:aqroot-demo', "
            "[]], ['env:wokwi', []]]))\n" % sys.executable, encoding="utf-8")
        stub.chmod(0o755)
        row("parser / PlatformIO DISAGREEMENT (a PlatformIO resolving a "
            "different default and environment list) fails", ini_text, False,
            stub, "")
    for case, text in (
            ("duplicate, CONFLICTING default_envs",
             ini_text.replace(default_line, "default_envs = aqroot-demo-fap01\n"
                              + default_line, 1)),
            ("duplicate, identical default_envs",
             ini_text.replace(default_line, default_line + default_line, 1)),
            ("mixed default (aqroot-demo, wokwi)",
             ini_text.replace(default_line,
                              "default_envs = aqroot-demo, wokwi\n", 1)),
            ("legacy default (esp32-s3-aqroot)",
             ini_text.replace(default_line,
                              "default_envs = esp32-s3-aqroot\n", 1)),
            ("FAP-01 default",
             ini_text.replace(default_line,
                              "default_envs = aqroot-demo-fap01\n", 1)),
            ("extra_configs added",
             ini_text.replace(default_line, default_line
                              + "extra_configs = local_override.ini\n", 1))):
        row(case + " fails with the real PlatformIO", text, False)
        row(case + " fails with PlatformIO ABSENT", text, False, absent, "")
    return rows


def run_host_test(test, mutation=None, variant=None):
    """Compile and run one host test, optionally against a mutated copy of the
    layer.  Returns (compiled, exit_code, stdout).

    D-790 / D789-A04: an IMAGE test additionally gets `src/demo/` and the host
    Arduino core under `test/image/`, and its mutations may name
    `demo/main.cpp` -- which is the point, because that is the file Round-9's
    five counterexamples live in.

    D-801 / D801-01: `variant` selects the BUILD an image test is linked into.
      None       the release image, as every earlier release;
      "fap01"    the FAP-01 diagnostic build: `-DAQROOT_FAP01_DIAGNOSTIC` and
                 `src/fap01/*.cpp` (with `-DAQROOT_TEST_EXPECT_FAP01` for the
                 FAP-01 test itself);
      "release"  the release build with `-DAQROOT_TEST_EXPECT_PRODUCTION`, for
                 the FAP-01 test's NEGATIVE half.  The one `__build__`
                 mutation leaks the FAP-01 define and sources into it -- the
                 build-configuration mistake the negative half exists to catch.
    """
    is_image = test.name in IMAGE_TESTS
    leak = mutation is not None and mutation[1] == "__build__"
    # D-802 / D802-01: `__population__` flips the BOM's U9 supply under an
    # unchanged image -- the board the model answers for is the other one.
    flip_population = mutation is not None and mutation[1] == "__population__"
    with tempfile.TemporaryDirectory(prefix="aqroot-host-") as temporary:
        work = Path(temporary)
        shutil.copytree(HW_DIR, work / "hw")
        if HOST_HARNESS.exists():
            shutil.copytree(HOST_HARNESS, work / "harness")
        if is_image:
            shutil.copytree(DEMO_DIR, work / "demo")
            shutil.copytree(IMAGE_HARNESS, work / "image")
            if FAP01_DIR.exists():
                shutil.copytree(FAP01_DIR, work / "fap01")
        shutil.copy(test, work / test.name)
        if mutation is not None and not leak and not flip_population:
            _, filename, before, after = mutation[:4]
            target = (work / filename) if "/" in filename \
                else (work / "hw" / filename)
            if not target.exists():
                return (False, -1, "control target %s is absent" % filename)
            body = target.read_text(encoding="utf-8")
            if before not in body:
                return (False, -1, "control text not found in %s" % filename)
            target.write_text(body.replace(before, after, 1), encoding="utf-8")
        binary = work / "host_test"
        sources = [str(work / test.name)]
        flags = []
        if is_image:
            sources += [str(work / "demo" / "main.cpp"),
                        str(work / "image" / "image_main.cpp")]
            supply = nfc_supply_3v3_from_bom()
            if supply is None:
                return (False, -1, "the fab BOM states no U9 supply population "
                                   "(R106 / R107)")
            if flip_population:
                supply = 1 - supply
            flags = ["-DARDUINO=200", "-I", str(work / "image"),
                     "-DAQROOT_TEST_NFC_SUPPLY_3V3=%d" % supply]
            fap_build = variant == "fap01" or leak
            if fap_build:
                flags.append("-D" + FAP01_DEFINE)
                sources += sorted(str(x) for x in (work / "fap01").glob("*.cpp"))
            if test.name == FAP01_TEST.name:
                flags.append("-DAQROOT_TEST_EXPECT_FAP01" if variant == "fap01"
                             else "-DAQROOT_TEST_EXPECT_PRODUCTION")
        build = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror"] + flags +
            ["-I", str(work / "hw"), "-I", str(work),
             "-I", str(work / "harness"),
             "-o", str(binary)] + sources,
            capture_output=True, text=True)
        if build.returncode != 0:
            return (False, build.returncode, build.stderr[-2000:])
        run = subprocess.run([str(binary)], capture_output=True, text=True,
                             timeout=300)
        return (True, run.returncode, run.stdout)


def with_policy(mutate):
    """Run `gen.build()` against a mutated copy of the policy tables."""
    saved = (copy.deepcopy(gen.MCU_POLICY), copy.deepcopy(gen.EXPANDER_POLICY))
    try:
        mutate(gen.MCU_POLICY, gen.EXPANDER_POLICY)
        _, problems = gen.build()
        return problems
    finally:
        gen.MCU_POLICY.clear()
        gen.MCU_POLICY.update(saved[0])
        gen.EXPANDER_POLICY.clear()
        gen.EXPANDER_POLICY.update(saved[1])


def with_bench_only(mutate):
    """Run `gen.build()` against a mutated copy of the D-776 BENCH_ONLY registry.

    The registry's WHOLE POINT is that it cannot be stale in either direction --
    an undeclared probed-and-unreachable net refuses, and a declaration for a
    net that has since been wired refuses too.  Both directions are controlled
    here, because a one-directional guard is how D-768/D-769's retired-name
    defects survived.
    """
    saved = copy.deepcopy(gen.BENCH_ONLY)
    try:
        mutate(gen.BENCH_ONLY)
        _, problems = gen.build()
        return problems
    finally:
        gen.BENCH_ONLY.clear()
        gen.BENCH_ONLY.update(saved)


def _drop(net):
    return lambda registry: registry.pop(net)


# D-802 / D802-01 (Round-21 R21-01).  `AQROOT_NFC_ON_3V3` -- which decides the
# ST25R3916 supply mode FAP-01 writes (sup3V) -- is DERIVED from the
# population now.  Each control re-runs `gen.build()` against a mutated
# (fitted, dnp) and must be refused with the NFC-supply reason.
def with_population(fit=(), unfit=()):
    saved = gen._FITTED_CACHE
    fitted, dnp = gen.fitted_refs()
    try:
        gen._FITTED_CACHE = ((set(fitted) | set(fit)) - set(unfit),
                             (set(dnp) | set(unfit)) - set(fit))
        _, problems = gen.build()
        return [p for p in problems if p.startswith("NFC supply")]
    finally:
        gen._FITTED_CACHE = saved


POPULATION_CONTROLS = [
    ("R106 DNP and R107 FIT: U9 on the 5 V PA branch",
     dict(fit=("R107",), unfit=("R106",))),
    ("R106 DNP alone: /NFC_SUPPLY unsourced", dict(unfit=("R106",))),
    ("R107 FIT beside R106: both sources tied to /NFC_SUPPLY",
     dict(fit=("R107",))),
    ("U13 FIT: the 5 V NFC PA boost populated", dict(fit=("U13",))),
]


def nfc_supply_3v3_from_bom():
    """D-802 / D802-01: the U9 supply as the FAB BOM populates it -- R106 0R
    FIT (+3V3 -> /NFC_SUPPLY) and R107 0R DNP -- read from the package the
    assembler builds, independently of the generator.  1, 0, or None if the
    BOM states neither population."""
    fitted, dnp = set(), set()
    bom = ROOT / "hardware/demo/fab/aqroot-Demo-BOM-full.csv"
    if not bom.exists():
        return None
    with open(bom, newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if not row or row[0] == "Refs":
                continue
            refs = set()
            for item in row[0].split(","):
                span = re.fullmatch(r"([A-Z]+)(\d+)-\1?(\d+)", item.strip())
                if span:
                    refs |= {"%s%d" % (span.group(1), n) for n in
                             range(int(span.group(2)), int(span.group(3)) + 1)}
                else:
                    refs.add(item.strip())
            (dnp if row[-1].strip().upper() == "DNP" else fitted).update(refs)
    if "R106" in fitted and "R107" in dnp:
        return 1
    if "R107" in fitted and "R106" in dnp:
        return 0
    return None


def _declare(net):
    return lambda registry: registry.__setitem__(
        net, dict(kind="signal", key="CONTROL_ONLY",
                  why="a control; this net is readable and must be refused"))


BENCH_ONLY_CONTROLS = [
    ("the VBUS_PRESENT declaration is dropped",
     _drop("/01_POWER_TREE/VBUS_PRESENT")),
    ("the breaker-fault declaration is dropped",
     _drop("/01_POWER_TREE/LTC4368_FAULT_N")),
    ("a net that IS readable is declared unreadable",
     _declare("/WAKE_INT_N")),
    ("a net that is not on the board at all is declared",
     _declare("/01_POWER_TREE/NO_SUCH_NET")),
]


def strip_comments(text):
    """Drop // and /* */ comments so only code is scanned for symbols."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def swap_nets(bits, left, right):
    bits[left]["net"], bits[right]["net"] = bits[right]["net"], bits[left]["net"]


CONTROLS = [
    ("D-732 swap: U2 P05 <-> P06",
     lambda mcu, exp: swap_nets(exp["U2"]["bits"], "P05", "P06")),
    ("D-733 swap: U2 P17 <-> U3 P17",
     lambda mcu, exp: exp["U2"]["bits"]["P17"].update(net="/BQ25185_STAT1")),
    ("ACC_5V_SW_EN safe latch flipped to 1 against R131",
     lambda mcu, exp: exp["U3"]["bits"]["P03"].update(safe=1)),
    ("FRONT_RGB_R_N claims an external pull it does not have",
     lambda mcu, exp: exp["U3"]["bits"]["P00"].update(safe_basis="external_pull")),
    ("TOUCH_INT_N claims an external pull it does not have",
     lambda mcu, exp: exp["U2"]["bits"]["P06"].update(
         idle_basis="external_pull", pull="NONE")),
    ("SX1262_DIO1 pulls against the module's push-pull driver",
     lambda mcu, exp: exp["U2"]["bits"]["P05"].update(pull="UP")),
    ("an expander bit is dropped from the map",
     lambda mcu, exp: exp["U3"]["bits"].pop("P11")),
    ("a U1 pad is re-pointed at the wrong net",
     lambda mcu, exp: mcu[9].update(net="/IR_RX_GPIO44")),
    ("two firmware roles share one C identifier",
     lambda mcu, exp: mcu[31].update(role="NATIVE_B")),
    ("an UNMASKED input is left with an undefined idle level",
     lambda mcu, exp: exp["U3"]["bits"]["P14"].update(
         idle_basis="hope", pull="NONE")),
    ("a strap loses the resistor that holds it",
     lambda mcu, exp: mcu[26].update(strap_part="R999")),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", type=Path)
    args = parser.parse_args()

    report = {"contract": "firmware_hw_map", "board": gen.BOARD.name}
    doc, problems = gen.build()
    report["board_sha256"] = doc["board_sha256"]

    # ---- H3 -------------------------------------------------------------
    report["H3_policy_corroborated"] = {
        "problems": problems,
        "mcu_pins_mapped": sum(1 for row in doc["mcu"]["pins"] if row["role"]),
        "expander_bits_mapped": sum(len(doc["expanders"][ref]["bits"])
                                    for ref in doc["expanders"]),
        "verdict": "PASS" if not problems else "FAIL",
    }

    # ---- H1 / H2 --------------------------------------------------------
    header = gen.emit_header(doc)
    payload = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    stale = []
    for path, want in ((gen.OUT_H, header), (gen.OUT_JSON, payload)):
        have = path.read_text(encoding="utf-8") if path.exists() else None
        if have != want:
            stale.append(dict(
                file=path.relative_to(ROOT).as_posix(),
                state="missing" if have is None else "differs",
                committed_sha256=hashlib.sha256(have.encode()).hexdigest() if have else None,
                regenerated_sha256=hashlib.sha256(want.encode()).hexdigest()))
    report["H1_generated_tree_is_fresh"] = {
        "files": [gen.OUT_H.relative_to(ROOT).as_posix(),
                  gen.OUT_JSON.relative_to(ROOT).as_posix()],
        "stale": stale,
        "verdict": "PASS" if not stale else "FAIL",
    }
    actual = hashlib.sha256(gen.BOARD.read_bytes()).hexdigest()
    published = re.search(r'AQROOT_DEMO_BOARD_SHA256 "([0-9a-f]{64})"',
                          gen.OUT_H.read_text(encoding="utf-8") if gen.OUT_H.exists()
                          else "")
    report["H2_board_digest"] = {
        "board_sha256": actual,
        "published_in_header": published.group(1) if published else None,
        "verdict": "PASS" if published and published.group(1) == actual else "FAIL",
    }

    # ---- H4 -------------------------------------------------------------
    h4 = {"approved_unrouted": [], "approved_nc_absent": True, "problems": []}
    masked_nets = {}
    for ref, expander in doc["expanders"].items():
        for row in expander["bits"]:
            if row["net"]:
                masked_nets.setdefault(row["net"], []).append((ref, row))
    for contact, entry in routing_ledger.APPROVED_UNROUTED.items():
        net = entry["net"]
        rows = masked_nets.get(net, [])
        record = dict(contact=contact, net=net,
                      expander_bits=["%s.%s" % (ref, row["bit"]) for ref, row in rows])
        for ref, row in rows:
            if row["irq"] != "MASKED":
                h4["problems"].append(
                    "%s %s carries approved-unrouted %s and is not MASKED"
                    % (ref, row["bit"], net))
            if row.get("carries_information") is not False:
                h4["problems"].append(
                    "%s %s carries approved-unrouted %s and is not flagged as "
                    "carrying no information" % (ref, row["bit"], net))
        record["masked"] = all(row["irq"] == "MASKED" for _, row in rows)
        h4["approved_unrouted"].append(record)
    emitted_nets = {row["net"] for expander in doc["expanders"].values()
                    for row in expander["bits"] if row["net"]}
    emitted_nets |= {row["net"] for row in doc["mcu"]["pins"] if row["net"]}
    board = gen.pcbnew.LoadBoard(str(gen.BOARD))
    nc_nets = set()
    for footprint in board.GetFootprints():
        if footprint.GetReference() != "J5":
            continue
        for pad in footprint.Pads():
            contact = "J5.%s" % pad.GetNumber()
            if contact in routing_ledger.APPROVED_NC and pad.GetNetname():
                nc_nets.add(pad.GetNetname())
    leaked = sorted(nc_nets & emitted_nets)
    h4["approved_nc_contacts"] = sorted(routing_ledger.APPROVED_NC)
    h4["approved_nc_nets_on_board"] = sorted(nc_nets)
    h4["leaked_into_firmware_map"] = leaked
    if leaked:
        h4["problems"].append("approved-NC nets reached the firmware map: %s" % leaked)
    h4["verdict"] = "PASS" if not h4["problems"] else "FAIL"
    report["H4_owner_decisions_are_machine_checked"] = h4

    # ---- H5 -------------------------------------------------------------
    emitted = set(re.findall(r"#define\s+(AQROOT_\w+)", header))
    sources = sorted(p for p in HW_DIR.rglob("*")
                     if p.suffix in (".h", ".cpp") and p.name != gen.OUT_H.name)
    used = set()
    for path in sources:
        # COMMENTS ARE NOT REFERENCES.  H5's claim is about code: the layer
        # prose names documents and decisions, and `AQROOT_DEMO_EXPANDER_
        # DEPENDENCIES.md` is a filename, not a symbol the generator owes.
        body = strip_comments(path.read_text(encoding="utf-8"))
        used |= set(re.findall(r"\b(AQROOT_\w+)", body))
    roles = {"AQROOT_PIN_%s" % row["role"] for row in doc["mcu"]["pins"] if row["role"]}
    roles |= {"AQROOT_%s_%s" % (ref, row["role"])
              for ref, expander in doc["expanders"].items() for row in expander["bits"]}
    unreferenced = sorted(roles - used)
    invented = sorted(used - emitted)
    report["H5_firmware_layer_uses_the_map"] = {
        "sources": [p.relative_to(ROOT).as_posix() for p in sources],
        "symbols_emitted": len(emitted),
        "roles_unreferenced_by_the_layer": unreferenced,
        "symbols_the_generator_never_emitted": invented,
        "verdict": "PASS" if not unreferenced and not invented else "FAIL",
    }

    # ---- H6 -------------------------------------------------------------
    h6 = {"tests": [], "verdict": "PASS"}
    # D-801 / D801-01: the three FAP-01 runs -- the FAP-01 test on the FAP-01
    # build (positive), the same test on the release build (negative), and
    # the whole release-image test on the FAP-01 build (FAP-01 weakens none
    # of the release rules it shares).
    runs = [(test, controls, None, None) for test, controls in zip(
            HOST_TESTS,
            (ORDER_CONTROLS, BUS_CONTROLS, POWER_POLICY_CONTROLS,
             FUEL_GAUGE_CONTROLS, TIMING_CONTROLS,
             PRODUCTION_TIMING_CONTROLS, PRODUCTION_CALLER_CONTROLS,
             PRODUCTION_IMAGE_CONTROLS))]
    runs += [
        (FAP01_TEST, FAP01_CONTROLS, "fap01", "FAP-01 build: every stimulus "
         "reachable, gated, bounded, quiesced"),
        (FAP01_TEST, FAP01_RELEASE_CONTROLS, "release", "RELEASE build: every "
         "FAP-01 key inert"),
        (ROOT / "Firmware/test/test_production_image.cpp", [], "fap01",
         "FAP-01 build: the whole release-image test"),
    ]
    for test, controls, variant, label in runs:
        compiled, code, output = run_host_test(test, variant=variant)
        claims = [line for line in output.splitlines() if line.startswith("[")]
        entry = {
            "test": test.relative_to(ROOT).as_posix()
                    + ("" if label is None else " [%s]" % label),
            "variant": variant or "release",
            "compiled": compiled,
            "exit_code": code,
            "claims": len(claims),
            "failed_claims": [line for line in claims if line.startswith("[FAIL")],
            "controls": [],
        }
        for control in controls:
            c_compiled, c_code, c_output = run_host_test(test, control,
                                                         variant=variant)
            c_claims = [line for line in c_output.splitlines()
                        if line.startswith("[FAIL")]
            # D-797 / D797-10: a mutant is CAUGHT only by a claim the test
            # printed and an ordinary non-zero exit.  A death by signal --
            # std::bad_alloc's abort, a segfault -- is harness exhaustion,
            # not a stated reason, and never counts; and a control that
            # names the claim it must fail on (a fifth element) is caught
            # only by that claim.
            expected = control[4] if len(control) > 4 else None
            reason_ok = (expected is None
                         or any(expected in line for line in c_claims))
            entry["controls"].append(dict(
                control=control[0], compiled=c_compiled, exit_code=c_code,
                terminated_by_signal=bool(c_compiled and c_code < 0),
                expected_failure=expected,
                caught=(c_compiled and c_code > 0 and bool(c_claims)
                        and reason_ok),
                first_failed_claim=c_claims[0] if c_claims else None))
        entry["verdict"] = ("PASS" if compiled and code == 0 and claims
                            and all(c["caught"] for c in entry["controls"])
                            else "FAIL")
        if entry["verdict"] != "PASS":
            h6["verdict"] = "FAIL"
        h6["tests"].append(entry)
    report["H6_host_tests_prove_the_orderings"] = h6

    # ---- H8: THE RELEASED FIRMWARE MUST ACTUALLY RUN THE TESTED SEAM -----
    # D-787 / R6-E01 wrote this clause as a SOURCE-TEXT check over the call
    # sites, and D-788 / R7-D787-05+06 is what that cost: Round-7 halved the
    # production `delay(ms)`, made the production `delayMicroseconds(us)` a
    # no-op and halved the production `ledcWrite(channel, duty)`, and every
    # clause of H1-H8 still passed -- because the ONLY executable proof drove
    # `aqroot_demo_timing_policy.h` through a test's own fakes.
    #
    # H8 is now TWO claims:
    #   (a) the shipped call sites route through the seam and own no second
    #       untested copy of the ordering (the D-787 claim, kept), and
    #   (b) `Firmware/test/test_production_timing.cpp` -- which compiles and
    #       RUNS `backlightRamp()` and `configureFuelGaugeActiveModeOnHardware()`
    #       against a recording Arduino HAL -- passed in H6 with every one of
    #       its eight production mutations CAUGHT.
    # Comments are stripped first: a commented-out call is not a call.
    PRODUCTION_TEST = ROOT / "Firmware/test/test_production_timing.cpp"
    CALLER_TEST = ROOT / "Firmware/test/test_production_callers.cpp"
    APP_HEADER = HW_DIR / "aqroot_demo_bringup_app.h"
    GAUGE_BRINGUP = HW_DIR / "aqroot_demo_gauge_bringup.h"
    BACKLIGHT = HW_DIR / "aqroot_demo_backlight.h"

    def _seam_problems(main_text, periph_text, bringup_text, backlight_text,
                       app_text=None):
        problems = []
        main_code = strip_comments(main_text)
        periph_code = strip_comments(periph_text)
        bringup_code = strip_comments(bringup_text)
        backlight_code = strip_comments(backlight_text)
        app_code = strip_comments(app_text if app_text is not None
                                  else _read(APP_HEADER))
        # D-789 / D788-04.  THE CALL MOVED, AND THAT IS THE FIX.  D-788 put
        # this clause on `demo/main.cpp` because that is where the caller was;
        # Round-8's counterexample was that nothing COMPILES `demo/main.cpp`.
        # The production entry point is now reached from
        # `aqroot_demo_bringup_app.h`, which `test_production_callers.cpp`
        # builds and runs -- and the clause below still refuses a `main.cpp`
        # that reimplements it.
        if "configureFuelGaugeActiveModeOnHardware(" not in app_code:
            problems.append("aqroot_demo_bringup_app.h does not call the "
                            "production gauge entry point")
        if "qualifyFuelGaugeActiveMode(" not in bringup_code:
            problems.append("aqroot_demo_gauge_bringup.h does not call "
                            "qualifyFuelGaugeActiveMode()")
        if "runBacklightRampPolicy(" not in backlight_code:
            problems.append("aqroot_demo_backlight.h does not call "
                            "runBacklightRampPolicy()")
        # A local re-implementation beside the seam is an untested second path.
        if re.search(r"delay\s*\(\s*kFuelGaugeActiveSettleMs\s*\)", main_code):
            problems.append("demo/main.cpp waits the settle itself instead of "
                            "through the tested production entry point")
        if "qualifyFuelGaugeActiveMode(" in main_code:
            problems.append("demo/main.cpp carries a second copy of the gauge "
                            "ordering beside the production entry point")
        for name, code in (("aqroot_demo_peripherals.h", periph_code),
                           ("aqroot_demo_backlight.h", backlight_code)):
            if re.search(r"ledcWrite\s*\([^)]*,\s*255\s*\)", code):
                problems.append("%s drives the full-duty prime itself instead "
                                "of through the tested seam" % name)
            # A LITERAL microsecond hold is a re-implemented prime; the seam's
            # own `[](uint32_t us) { delayMicroseconds(us); }` injector is not.
            if re.search(r"delayMicroseconds\s*\(\s*\d", code):
                problems.append("%s holds the prime itself instead of through "
                                "the tested seam" % name)
        if "runBacklightRampPolicy(" in periph_code:
            problems.append("aqroot_demo_peripherals.h carries a second copy "
                            "of the backlight ordering")
        # D-789 / D788-04 + D788-05 + D788-06.  THE CALL SITES THEMSELVES MUST
        # STAY WHERE A HOST TEST COMPILES THEM.  Round-8's three mutants all
        # lived in `demo/main.cpp`, which no host test has ever built, so the
        # only durable fix is that this file reaches each behaviour THROUGH
        # `DemoBringupApp` and owns no second implementation of any of them.
        if "DemoBringupApp<" not in main_code:
            problems.append("demo/main.cpp does not instantiate "
                            "DemoBringupApp, so its call sites are compiled "
                            "by no host test")
        for symbol, why in (
                ("g_app.handleAccessoryConsole(",
                 "the accessory/backlight console dispatch"),
                ("g_app.serviceExpanderRecovery(",
                 "the warm-reset expander recovery retry"),
                ("g_app.releaseExpanderResetLines(",
                 "the reset-release diagnostic"),
                ("g_app.backgroundGaugeRequalification(",
                 "the background gauge requalification"),
                ("g_app.periodicBatteryGuard(",
                 "the periodic accessory battery guard")):
            if symbol not in main_code:
                problems.append("demo/main.cpp does not reach %s through the "
                                "host-tested production app" % why)
        # ...and no second copy of any of them beside it.
        for pattern, why in (
                (r"\bbacklightRamp\s*\(", "a backlight ramp"),
                (r"\bledcWrite\s*\(", "a raw PWM duty command"),
                (r"\bconfigureFuelGaugeActiveModeOnHardware\s*\(",
                 "the gauge production entry point"),
                (r"\bqualifyFuelGaugeActiveMode\s*\(",
                 "the gauge qualification seam"),
                (r"\baccessoryRetentionAction\s*\(",
                 "the accessory retention rule"),
                (r"\baccessoryEnableAllowed\s*\(",
                 "the accessory enable rule"),
                (r"expanders?\.begin\s*\(|g_expanders\.begin\s*\(",
                 "a second expander initialisation retry")):
            for m in re.finditer(pattern, main_code):
                # setup()'s ONE boot-time `g_expanders.begin` is the legitimate
                # cold-start call; the retry is the app's.
                line = main_code[max(0, m.start() - 200):m.start()]
                if "g_expanders.begin" in m.group(0) and \
                        "const bool i2c_open" in line:
                    continue
                problems.append("demo/main.cpp carries %s outside the "
                                "host-tested production app" % why)
                break
        return problems

    def _read(path):
        return path.read_text(encoding="utf-8", errors="replace") \
            if path.exists() else ""

    main_src = _read(DEMO_MAIN)
    periph_src = _read(HW_DIR / "aqroot_demo_peripherals.h")
    bringup_src = _read(GAUGE_BRINGUP)
    backlight_src = _read(BACKLIGHT)
    seam_problems = _seam_problems(main_src, periph_src, bringup_src,
                                   backlight_src, _read(APP_HEADER))
    app_src = _read(APP_HEADER)
    h8_controls = []
    for name, m_text, p_text, g_text, b_text, a_text in (
            # D-789 / D788-04: the gauge call site now lives in the app header
            # -- which is the whole point -- so these two mutate it THERE.
            ("the gauge call site drops back to a local delay",
             main_src, periph_src, bringup_src, backlight_src,
             app_src.replace(
                 "    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);",
                 "    if (!gauge_.configureActiveMode(bus_)) return false;\n"
                 "    delay(kFuelGaugeActiveSettleMs);\n    return true;", 1)),
            ("the gauge call site is commented out",
             main_src, periph_src, bringup_src, backlight_src,
             app_src.replace(
                 "    return configureFuelGaugeActiveModeOnHardware(gauge_, bus_);",
                 "    return false; "
                 "// configureFuelGaugeActiveModeOnHardware(gauge_, bus_);", 1)),
            ("the gauge bring-up header stops calling the seam",
             main_src, periph_src,
             bringup_src.replace("return qualifyFuelGaugeActiveMode(",
                                 "return gauge.configureActiveMode(bus); "
                                 "// qualifyFuelGaugeActiveMode(", 1),
             backlight_src, app_src),
            ("the backlight call site re-implements the prime",
             main_src, periph_src, bringup_src,
             backlight_src.replace(
                 "  runBacklightRampPolicy(",
                 "  ledcWrite(channel, 255);\n  delayMicroseconds(3000);\n"
                 "  runBacklightRampPolicy(", 1), app_src),
            ("the backlight call site is commented out",
             main_src, periph_src, bringup_src,
             backlight_src.replace("  runBacklightRampPolicy(",
                                   "  // runBacklightRampPolicy(", 1), app_src),
            ("a second backlight ordering reappears in peripherals.h",
             main_src,
             periph_src + "\nnamespace aqroot { inline void backlightRamp2("
                          "uint8_t c) { runBacklightRampPolicy("
                          "[c](uint8_t d) { ledcWrite(c, d); },"
                          "[](uint32_t u) { delayMicroseconds(u); },"
                          "[](uint32_t m) { delay(m); }); } }\n",
             bringup_src, backlight_src, app_src),
            # D-789 / D788-04+05+06: the call sites move back out of the
            # host-tested app, which is exactly what Round-8 exploited.
            ("the console dispatch moves back into demo/main.cpp",
             main_src.replace("(void)g_app.handleAccessoryConsole(key);",
                              "backlightRamp();", 1),
             periph_src, bringup_src, backlight_src, app_src),
            # D-790 / D789-A09 removed `g_display_up` from `demo/main.cpp` --
            # the display's up-ness is now an app fact that depends on a
            # CONFIRMED reset release -- so the mutant is re-aimed at the call
            # that is still there.
            ("the warm-reset retry moves back into demo/main.cpp",
             main_src.replace(
                 "(void)g_app.serviceExpanderRecovery();",
                 "(void)(g_bus.reopen(AQROOT_I2C_BRINGUP_HZ) && "
                 "g_expanders.begin(g_bus));", 1),
             periph_src, bringup_src, backlight_src, app_src),
            ("the reset-release diagnostic moves back into demo/main.cpp",
             main_src.replace("g_app.releaseExpanderResetLines();",
                              "releaseResetsLocally();", 1),
             periph_src, bringup_src, backlight_src, app_src),
            ("demo/main.cpp regains a private accessory permission rule",
             main_src + "\nstatic bool allowLocally(bool v, float x, bool o) "
                        "{ return accessoryEnableAllowed(v, x, o); }\n",
             periph_src, bringup_src, backlight_src, app_src),
            ("the app is not instantiated at all",
             main_src.replace("using DemoApp = DemoBringupApp<",
                              "using DemoApp = int; // DemoBringupApp<", 1),
             periph_src, bringup_src, backlight_src, app_src)):
        p_list = _seam_problems(m_text, p_text, g_text, b_text, a_text)
        h8_controls.append(dict(control=name, refused=bool(p_list),
                                first_reason=p_list[0] if p_list else None))

    # (b) the EXECUTABLE half: the production-entry-point test must be one of
    # the host tests H6 ran, must have passed, and every one of its production
    # mutations must have been caught.
    production_entry = next(
        (entry for entry in h6["tests"]
         if entry["test"].endswith("test_production_timing.cpp")), None)
    production_ok = bool(
        production_entry
        and production_entry["compiled"]
        and production_entry["exit_code"] == 0
        and production_entry["claims"] >= 15
        and not production_entry["failed_claims"]
        and production_entry["controls"]
        and all(c["caught"] for c in production_entry["controls"]))
    if not PRODUCTION_TEST.exists():
        seam_problems.append("Firmware/test/test_production_timing.cpp is absent")
    if not production_ok:
        seam_problems.append(
            "the production-entry-point host test did not pass with every "
            "production mutation caught")
    # D-789 / D788-04 + D788-05 + D788-06: and the CALL-SITE test beside it.
    caller_entry = next(
        (entry for entry in h6["tests"]
         if entry["test"].endswith("test_production_callers.cpp")), None)
    caller_ok = bool(
        caller_entry
        and caller_entry["compiled"]
        and caller_entry["exit_code"] == 0
        and caller_entry["claims"] >= 40
        and not caller_entry["failed_claims"]
        and len(caller_entry["controls"]) >= 12
        and all(c["caught"] for c in caller_entry["controls"]))
    if not CALLER_TEST.exists():
        seam_problems.append("Firmware/test/test_production_callers.cpp is absent")
    if not caller_ok:
        seam_problems.append(
            "the production-CALL-SITE host test did not pass with every "
            "call-site mutation caught")

    report["H8_released_firmware_runs_the_tested_timing_seam"] = {
        "call_sites": {
            "gauge": DEMO_MAIN.relative_to(ROOT).as_posix(),
            "gauge_production_entry": GAUGE_BRINGUP.relative_to(ROOT).as_posix(),
            "backlight": BACKLIGHT.relative_to(ROOT).as_posix(),
            "seam": (HW_DIR / "aqroot_demo_timing_policy.h")
                    .relative_to(ROOT).as_posix(),
        },
        "executable_production_proof": {
            "test": PRODUCTION_TEST.relative_to(ROOT).as_posix(),
            "ran_in_H6": production_entry is not None,
            "claims": (production_entry or {}).get("claims"),
            "controls": [c["control"] for c in
                         (production_entry or {}).get("controls", [])],
            "every_production_mutation_caught": production_ok,
        },
        "executable_call_site_proof": {
            "test": CALLER_TEST.relative_to(ROOT).as_posix(),
            "app": (HW_DIR / "aqroot_demo_bringup_app.h")
                   .relative_to(ROOT).as_posix(),
            "ran_in_H6": caller_entry is not None,
            "claims": (caller_entry or {}).get("claims"),
            "controls": [c["control"] for c in
                         (caller_entry or {}).get("controls", [])],
            "every_call_site_mutation_caught": caller_ok,
            "why": ("D788-04/05/06: making the leaf entry points executable "
                    "left their CALLERS in demo/main.cpp, which no host test "
                    "compiles.  The call sites now live in DemoBringupApp and "
                    "are driven over a physical-latch expander model."),
        },
        "problems": seam_problems,
        "controls": h8_controls,
        "verdict": ("PASS" if not seam_problems
                    and all(c["refused"] for c in h8_controls) else "FAIL"),
    }

    # ---- H7: MAX17048 primary-source semantics and timing are pinned ----
    # D-785: a hash alone proves document identity, not that firmware's safety
    # interpretation or its active-conversion wait still matches that source.
    # Gate the exact PDF, the critical register semantics, AND the 300 ms wait
    # against the datasheet's 250 ms active period plus +3.5% time-base limit.
    primary_sha = (
        hashlib.sha256(MAX17048_PRIMARY.read_bytes()).hexdigest()
        if MAX17048_PRIMARY.exists() else None
    )
    try:
        source = json.loads(MAX17048_SOURCE_RECORD.read_text(encoding="utf-8"))
    except Exception:
        source = None
    timing_policy_path = HW_DIR / "aqroot_demo_timing_policy.h"
    demo_main_text = (
        timing_policy_path.read_text(encoding="utf-8", errors="replace")
        if timing_policy_path.exists() else ""
    )

    def _max17048_source_problems(source_obj, pdf_sha, main_text):
        problems = []
        if pdf_sha != MAX17048_PRIMARY_SHA256:
            problems.append(
                "primary PDF SHA256 expected %s, got %s" %
                (MAX17048_PRIMARY_SHA256, pdf_sha))
        if not isinstance(source_obj, dict):
            problems.append("source record is missing or is not valid JSON")
            return problems, None, None
        facts = source_obj.get("register_facts", {})
        actual = {
            "vendor": source_obj.get("vendor"),
            "device": source_obj.get("device"),
            "document_number": source_obj.get("document_number"),
            "revision": source_obj.get("revision"),
            "official_url": source_obj.get("official_url"),
            "MODE_address": facts.get("MODE_address"),
            "HibStat_mask": facts.get("HibStat_mask"),
            "HibStat_semantics": facts.get("HibStat_semantics"),
            "HIBRT_address": facts.get("HIBRT_address"),
            "HIBRT_zero_semantics": facts.get("HIBRT_zero_semantics"),
            "VCELL_active_update_ms_typ": facts.get("VCELL_active_update_ms_typ"),
            "VCELL_hibernate_update_s_typ": facts.get("VCELL_hibernate_update_s_typ"),
            "time_base_accuracy_pct_min": facts.get("time_base_accuracy_pct_min"),
            "time_base_accuracy_pct_max": facts.get("time_base_accuracy_pct_max"),
        }
        for key, expected in MAX17048_SOURCE_EXPECTED.items():
            if actual.get(key) != expected:
                problems.append(
                    "%s expected %r, got %r" % (key, expected, actual.get(key)))

        settle_match = re.search(
            r"kFuelGaugeActiveSettleMs\s*=\s*(\d+)", main_text)
        settle_ms = int(settle_match.group(1)) if settle_match else None
        timing_bound_ms = None
        try:
            timing_bound_ms = float(actual["VCELL_active_update_ms_typ"]) * (
                1.0 + float(actual["time_base_accuracy_pct_max"]) / 100.0)
        except (TypeError, ValueError):
            problems.append("active-conversion timing bound cannot be derived")
        if settle_ms is None:
            problems.append("kFuelGaugeActiveSettleMs is missing from aqroot_demo_timing_policy.h")
        elif timing_bound_ms is not None and settle_ms < timing_bound_ms:
            problems.append(
                "active settle %d ms is below derived %.3f ms timing bound" %
                (settle_ms, timing_bound_ms))
        # H6/test_timing_policy.cpp proves that this constant actually executes
        # AFTER successful gauge qualification. H7's job is only to bind the
        # numeric minimum to the archived primary-source timing.
        return problems, settle_ms, timing_bound_ms

    source_problems, settle_ms, timing_bound_ms = _max17048_source_problems(
        source, primary_sha, demo_main_text)

    h7_controls = []
    if isinstance(source, dict):
        def _source_mutation(name, mutate):
            candidate = copy.deepcopy(source)
            mutate(candidate)
            p, _, _ = _max17048_source_problems(
                candidate, primary_sha, demo_main_text)
            h7_controls.append(dict(control=name, refused=bool(p),
                                    first_reason=p[0] if p else None))

        _source_mutation(
            "HibStat mask moves to the wrong MODE bit",
            lambda d: d["register_facts"].__setitem__("HibStat_mask", "0x0800"))
        _source_mutation(
            "HIBRT=0 is misdescribed as forcing hibernate",
            lambda d: d["register_facts"].__setitem__(
                "HIBRT_zero_semantics", "forces hibernate mode"))
        _source_mutation(
            "active ADC period drifts to 450 ms",
            lambda d: d["register_facts"].__setitem__(
                "VCELL_active_update_ms_typ", 450))
        _source_mutation(
            "time-base maximum is silently removed",
            lambda d: d["register_facts"].pop("time_base_accuracy_pct_max", None))
    fake_sha_problems, _, _ = _max17048_source_problems(
        source, "0" * 64, demo_main_text)
    h7_controls.append(dict(
        control="archived primary PDF bytes change",
        refused=bool(fake_sha_problems),
        first_reason=fake_sha_problems[0] if fake_sha_problems else None))
    short_wait_text = re.sub(
        r"(kFuelGaugeActiveSettleMs\s*=\s*)300", r"\g<1>250",
        demo_main_text, count=1)
    short_wait_problems, _, _ = _max17048_source_problems(
        source, primary_sha, short_wait_text)
    h7_controls.append(dict(
        control="active-mode settle is shortened below the source-derived bound",
        refused=bool(short_wait_problems),
        first_reason=short_wait_problems[0] if short_wait_problems else None))

    h7_controls_ok = all(c["refused"] for c in h7_controls)
    report["H7_MAX17048_primary_source_is_pinned"] = {
        "pdf": MAX17048_PRIMARY.relative_to(ROOT).as_posix(),
        "expected_pdf_sha256": MAX17048_PRIMARY_SHA256,
        "actual_pdf_sha256": primary_sha,
        "source_record": MAX17048_SOURCE_RECORD.relative_to(ROOT).as_posix(),
        "expected_facts": MAX17048_SOURCE_EXPECTED,
        "active_settle_ms": settle_ms,
        "derived_active_sample_period_max_ms": timing_bound_ms,
        "problems": source_problems,
        "controls": h7_controls,
        "controls_verdict": "PASS" if h7_controls_ok else "FAIL",
        "verdict": ("PASS" if not source_problems and h7_controls_ok else "FAIL"),
    }

    # ---- H9: THE SOLE DEFAULT ENVIRONMENT IS THE RELEASE IMAGE -----------
    # D-801 / D801-03.  Parsed, cross-checked against PlatformIO's own
    # resolution, and exercised by controls that rewrite the file the ways a
    # maintainer actually would.
    #
    # D-803 / D803-04 (Round-22 R22-04): the cross-check is REQUIRED.  D-802
    # returned PASS with no PlatformIO at all (and never looked on PATH), and
    # its lenient parser read a duplicated, conflicting `default_envs` last-
    # one-wins where PlatformIO refuses the file.  Now PlatformIO is found
    # (configured path, then `pio` / `platformio` on PATH), an unavailable or
    # failing cross-check is a PROBLEM, a duplicate is refused, and the
    # parser and PlatformIO must AGREE on the default and the environments.
    ini_text = _read(PLATFORMIO_INI)
    h9_eval = _h9_evaluate(ini_text)
    h9_problems = h9_eval["problems"]
    pio_view = h9_eval["pio_project_config"]
    default_line = "default_envs = aqroot-demo\n"
    h9_controls = []
    for name, mutated in (
            ("default_envs is removed", ini_text.replace(default_line, "", 1)),
            ("the legacy placeholder image is the default",
             ini_text.replace(default_line,
                              "default_envs = esp32-s3-aqroot\n", 1)),
            ("a second, legacy default is added beside the release one",
             ini_text.replace(default_line,
                              "default_envs = aqroot-demo, wokwi\n", 1)),
            ("a multi-line default list adds the DM image",
             ini_text.replace(default_line, "default_envs =\n    aqroot-demo\n"
                              "    esp32-s3-aqroot-dm\n", 1)),
            ("the FAP-01 diagnostic image is the default",
             ini_text.replace(default_line,
                              "default_envs = aqroot-demo-fap01\n", 1)),
            ("the FAP-01 diagnostic image is a second default",
             ini_text.replace(default_line,
                              "default_envs = aqroot-demo, aqroot-demo-fap01\n",
                              1)),
            ("extra_configs is added, which can re-define the default elsewhere",
             ini_text.replace(default_line, default_line
                              + "extra_configs = local_override.ini\n", 1)),
            ("a named environment disappears (wokwi renamed)",
             ini_text.replace("[env:wokwi]\n", "[env:wokwi-sim]\n", 1)),
            # D-803 / D803-04
            ("a duplicated, CONFLICTING default_envs (FAP-01 first)",
             ini_text.replace(default_line, "default_envs = aqroot-demo-fap01\n"
                              + default_line, 1)),
            ("a duplicated, identical default_envs",
             ini_text.replace(default_line, default_line + default_line, 1))):
        if mutated == ini_text:
            h9_controls.append(dict(control=name, refused=False,
                                    first_reason="control text not found"))
            continue
        p_list = _default_env_problems(mutated)
        h9_controls.append(dict(control=name, refused=bool(p_list),
                                first_reason=p_list[0] if p_list else None))
    # D-803 / D803-04: the WHOLE evaluation -- parser AND the real
    # PlatformIO cross-check -- on fixture projects, with the tool absent,
    # present only on PATH as `pio` or as `platformio`, and each bad form.
    h9_portability = _h9_portability_controls(ini_text, default_line)
    try:
        parsed_default = _pio_default_envs(_pio_parse(ini_text))
    except configparser.Error:
        parsed_default = None
    report["H9_platformio_default_is_the_release_image"] = {
        "file": PLATFORMIO_INI.relative_to(ROOT).as_posix(),
        "default_envs_parsed": parsed_default,
        "required_default": [RELEASE_ENV],
        "environments_that_build_by_name": list(NAMED_ENVS),
        "pio_project_config": pio_view,
        "problems": h9_problems,
        "controls": h9_controls,
        "portability_controls": h9_portability,
        "verdict": ("PASS" if not h9_problems
                    and all(c["refused"] for c in h9_controls)
                    and all(c["ok"] for c in h9_portability) else "FAIL"),
    }

    # ---- H10: FAP-01 REACHES ITS OWN ENVIRONMENT AND NOTHING ELSE ----------
    # D-801 / D801-01.  The behavioural half is H6 (the FAP-01 test compiled
    # into the RELEASE build, every key inert); this is the configuration
    # half: which environment compiles `src/fap01/`, which defines the
    # diagnostic macro, whether the release `main.cpp` preprocesses to any
    # FAP-01 token, and whether `src/fap01/` still refuses to compile alone.
    fap_header = _read(FAP01_DIR / "aqroot_fap01.h")
    fap_cpp = _read(FAP01_DIR / "aqroot_fap01.cpp")
    h10_problems = _fap01_isolation_problems(ini_text, main_src, fap_header,
                                             fap_cpp)
    release_filter = "build_src_filter = -<*> +<demo/> +<hw/>\nlib_deps ="
    release_flags_end = ("    -DARDUINO_USB_CDC_ON_BOOT=1\n"
                         "build_src_filter = -<*> +<demo/> +<hw/>\nlib_deps =")
    h10_controls = []
    for name, i_text, m_text, h_text in (
            ("the release build_src_filter admits src/fap01/",
             ini_text.replace(release_filter, "build_src_filter = -<*> +<demo/>"
                              " +<hw/> +<fap01/>\nlib_deps =", 1),
             main_src, fap_header),
            ("the release build_src_filter becomes +<*>",
             ini_text.replace(release_filter,
                              "build_src_filter = +<*>\nlib_deps =", 1),
             main_src, fap_header),
            ("the release build_flags gain the FAP-01 define",
             ini_text.replace(release_flags_end,
                              "    -DARDUINO_USB_CDC_ON_BOOT=1\n"
                              "    -DAQROOT_FAP01_DIAGNOSTIC\n"
                              "build_src_filter = -<*> +<demo/> +<hw/>\n"
                              "lib_deps =", 1),
             main_src, fap_header),
            ("the legacy filter stops excluding src/fap01/",
             ini_text.replace("legacy_src_filter = +<*> -<demo/> -<hw/> "
                              "-<fap01/>", "legacy_src_filter = +<*> -<demo/> "
                              "-<hw/>", 1),
             main_src, fap_header),
            ("the FAP-01 environment loses its define",
             ini_text.replace("    -DAQROOT_FAP01_DIAGNOSTIC\nbuild_src_filter"
                              " = -<*> +<demo/> +<hw/> +<fap01/>",
                              "build_src_filter = -<*> +<demo/> +<hw/> "
                              "+<fap01/>", 1),
             main_src, fap_header),
            ("demo/main.cpp's console hook is compiled unguarded",
             ini_text,
             main_src.replace("#if defined(AQROOT_FAP01_DIAGNOSTIC)\n    // "
                              "D-801: FAP-01's upper-case keys",
                              "#if 1\n    // D-801: FAP-01's upper-case keys",
                              1), fap_header),
            ("demo/main.cpp includes the FAP-01 header unguarded",
             ini_text,
             main_src.replace("#if defined(AQROOT_FAP01_DIAGNOSTIC)\n#include "
                              "\"../fap01/aqroot_fap01.h\"",
                              "#if 1\n#include \"../fap01/aqroot_fap01.h\"", 1),
             fap_header),
            ("src/fap01/aqroot_fap01.h loses its compile guard",
             ini_text, main_src,
             fap_header.replace("#if !defined(AQROOT_FAP01_DIAGNOSTIC)\n"
                                "#error", "#if 0\n#error", 1))):
        if (i_text, m_text, h_text) == (ini_text, main_src, fap_header):
            h10_controls.append(dict(control=name, refused=False,
                                     first_reason="control text not found"))
            continue
        p_list = _fap01_isolation_problems(i_text, m_text, h_text, fap_cpp)
        h10_controls.append(dict(control=name, refused=bool(p_list),
                                 first_reason=p_list[0] if p_list else None))
    # D-802 / D802-03: the legacy PN532 driver as an ST25R3916 fallback, in
    # each of the three ways it could arrive.
    fap_filter = "build_src_filter = -<*> +<demo/> +<hw/> +<fap01/>"
    for name, i_text, c_text in (
            ("the FAP-01 environment compiles the legacy drivers/ (PN532)",
             ini_text.replace(fap_filter, fap_filter + " +<drivers/>", 1),
             fap_cpp),
            ("the FAP-01 environment gains the Adafruit PN532 dependency",
             ini_text.replace(fap_filter, fap_filter + "\nlib_deps = "
                              "adafruit/Adafruit PN532 @ ^1.3.3", 1), fap_cpp),
            ("src/fap01 calls the legacy PN532 driver as a fallback",
             ini_text, fap_cpp.replace("void sendReqa() {",
                                       "void sendReqa() {\n  nfc_init();", 1))):
        if (i_text, c_text) == (ini_text, fap_cpp):
            h10_controls.append(dict(control=name, refused=False,
                                     first_reason="control text not found"))
            continue
        p_list = _fap01_isolation_problems(i_text, main_src, fap_header, c_text)
        h10_controls.append(dict(control=name, refused=bool(p_list),
                                 first_reason=p_list[0] if p_list else None))
    # D-803 / D803-05 (Round-22 R22-05): the operator documents say what the
    # image does -- the hold-off record reaches the NEXT FAP-01 boot of ANY
    # kind, a power cycle included, and Q ("NVS confirmed clear") comes
    # before power-off or reflash unless persistence is under test.  The
    # behaviour itself is H6 (`J/record:` claims); this binds the words.
    fap_doc = _read(FAP01_PROCEDURE)
    fa_plan = _read(FIRST_FIVE_PLAN)
    h10_problems += _fap01_wording_problems(fap_doc, fa_plan, fap_cpp,
                                            fap_header)
    for name, d_text, pl_text in (
            ("the procedure goes back to 'survives exactly one reset of any "
             "kind (an EN pulse or a power cycle)' with no Q rule",
             fap_doc.replace(FAP01_WORDING_DOC[1], "", 1), fa_plan),
            ("the procedure's H row says 'for one following reset'",
             fap_doc.replace(FAP01_WORDING_DOC[0],
                             "Also recorded in NVS for **one** following "
                             "reset.", 1), fa_plan),
            ("the assembly plan says 'it survives one reset'",
             fap_doc, fa_plan.replace(FAP01_WORDING_PLAN, "it survives one "
                                      "reset", 1))):
        if (d_text, pl_text) == (fap_doc, fa_plan):
            h10_controls.append(dict(control=name, refused=False,
                                     first_reason="control text not found"))
            continue
        p_list = _fap01_wording_problems(d_text, pl_text, fap_cpp, fap_header)
        h10_controls.append(dict(control=name, refused=bool(p_list),
                                 first_reason=p_list[0] if p_list else None))
    report["H10_fap01_diagnostic_image_is_isolated"] = {
        "environment": FAP01_ENV,
        "define": FAP01_DEFINE,
        "sources": sorted(p.relative_to(ROOT).as_posix()
                          for p in FAP01_DIR.glob("*")) if FAP01_DIR.exists()
                   else [],
        "problems": h10_problems,
        "controls": h10_controls,
        "verdict": ("PASS" if not h10_problems
                    and all(c["refused"] for c in h10_controls) else "FAIL"),
    }

    # ---- controls -------------------------------------------------------
    controls = []
    for name, mutate in CONTROLS:
        refused = with_policy(mutate)
        controls.append(dict(control=name, refused=bool(refused),
                             first_reason=refused[0] if refused else None))
    # D-776's four.  These prove the PROBED-BUT-NOT-READABLE registry refuses
    # in both directions rather than merely existing.
    for name, mutate in BENCH_ONLY_CONTROLS:
        refused = with_bench_only(mutate)
        controls.append(dict(control=name, refused=bool(refused),
                             first_reason=refused[0] if refused else None))
    # D-802 / D802-01: the NFC supply mode is derived, so a population that
    # is not R106 FIT / R107 + U13 DNP must refuse to emit.
    for name, change in POPULATION_CONTROLS:
        refused = with_population(**change)
        controls.append(dict(control="D802-01 population: " + name,
                             refused=bool(refused),
                             first_reason=refused[0] if refused else None))
    report["controls"] = controls
    report["controls_verdict"] = (
        "PASS" if all(entry["refused"] for entry in controls) else "FAIL")

    verdicts = [report[key]["verdict"] for key in report if key.startswith("H")]
    verdicts.append(report["controls_verdict"])
    report["verdict"] = "PASS" if all(v == "PASS" for v in verdicts) else "FAIL"

    text = json.dumps(report, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
