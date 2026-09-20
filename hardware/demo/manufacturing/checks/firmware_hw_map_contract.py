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
  H6  FOUR HOST TESTS compile under `-Wall -Wextra -Werror` and pass.  Each
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

AND IT PROVES IT IS NOT VACUOUS.  Eleven controls mutate the policy table --
including the exact `P05`/`P06` swap D-732 found -- and each must be REFUSED.

    python3 hardware/demo/manufacturing/checks/firmware_hw_map_contract.py [-o OUT]
"""

import argparse
import copy
import hashlib
import json
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
]

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
    ("dual-rail floor collapses onto the single-rail floor",
     "aqroot_accessory_power_policy.h",
     "constexpr float kAccessoryDualRailFloorV = 3.85f;",
     "constexpr float kAccessoryDualRailFloorV = 3.50f;"),
    ("unreadable VCELL fails open instead of shedding active rails",
     "aqroot_accessory_power_policy.h",
     """  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::ShedAll;""",
     """  if (!vcell_valid || !vcellIsPlausible(vcell))
    return AccessoryBatteryAction::Keep;"""),
    ("a dual-rail load below the dual floor sheds everything instead of the 5 V rail alone",
     "aqroot_accessory_power_policy.h",
     """    return vcell >= kAccessorySingleRailFloorV
               ? AccessoryBatteryAction::Shed5v
               : AccessoryBatteryAction::ShedAll;""",
     "    return AccessoryBatteryAction::ShedAll;"),
    ("the VCELL plausibility band stops excluding the all-ones code",
     "aqroot_accessory_power_policy.h",
     "constexpr float kVcellPlausibleMaxV = 4.50f;",
     "constexpr float kVcellPlausibleMaxV = 5.50f;"),
]

# Round-4 R4-04: active-mode configuration/readiness is part of VCELL validity.
# Each mutation is realistic enough to compile and must be rejected by the
# dedicated MAX17048 host test.
FUEL_GAUGE_CONTROLS = [
    ("HIBRT=0 readback is trusted while MODE.HibStat still reports hibernate",
     "max17048_guard.h",
     """    active_ready_ = mode_read && verify[0] == 0x00 && verify[1] == 0x00 &&
                    (mode & kModeHibStatMask) == 0;""",
     """    active_ready_ = mode_read && verify[0] == 0x00 && verify[1] == 0x00 &&
                    (mode & kModeHibStatMask) == kModeHibStatMask;"""),
    ("later MODE.HibStat assertion is ignored before a safety VCELL read",
     "max17048_guard.h",
     """    if ((mode & kModeHibStatMask) != 0) {
      active_ready_ = false;
      return false;
    }""",
     """    if ((mode & kModeHibStatMask) != 0 && false) {
      active_ready_ = false;
      return false;
    }"""),
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

BUS_CONTROLS = [
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



def run_host_test(test, mutation=None):
    """Compile and run one host test, optionally against a mutated copy of the
    layer.  Returns (compiled, exit_code, stdout)."""
    with tempfile.TemporaryDirectory(prefix="aqroot-host-") as temporary:
        work = Path(temporary)
        shutil.copytree(HW_DIR, work / "hw")
        shutil.copy(test, work / test.name)
        if mutation is not None:
            _, filename, before, after = mutation
            target = work / "hw" / filename
            body = target.read_text(encoding="utf-8")
            if before not in body:
                return (False, -1, "control text not found in %s" % filename)
            target.write_text(body.replace(before, after, 1), encoding="utf-8")
        binary = work / "host_test"
        build = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-I", str(work / "hw"), "-o", str(binary), str(work / test.name)],
            capture_output=True, text=True)
        if build.returncode != 0:
            return (False, build.returncode, build.stderr[-2000:])
        run = subprocess.run([str(binary)], capture_output=True, text=True)
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
    for test, controls in zip(
            HOST_TESTS,
            (ORDER_CONTROLS, BUS_CONTROLS, POWER_POLICY_CONTROLS,
             FUEL_GAUGE_CONTROLS, TIMING_CONTROLS)):
        compiled, code, output = run_host_test(test)
        claims = [line for line in output.splitlines() if line.startswith("[")]
        entry = {
            "test": test.relative_to(ROOT).as_posix(),
            "compiled": compiled,
            "exit_code": code,
            "claims": len(claims),
            "failed_claims": [line for line in claims if line.startswith("[FAIL")],
            "controls": [],
        }
        for control in controls:
            c_compiled, c_code, c_output = run_host_test(test, control)
            c_claims = [line for line in c_output.splitlines()
                        if line.startswith("[FAIL")]
            entry["controls"].append(dict(
                control=control[0], compiled=c_compiled, exit_code=c_code,
                caught=(c_compiled and c_code != 0 and bool(c_claims)),
                first_failed_claim=c_claims[0] if c_claims else None))
        entry["verdict"] = ("PASS" if compiled and code == 0 and claims
                            and all(c["caught"] for c in entry["controls"])
                            else "FAIL")
        if entry["verdict"] != "PASS":
            h6["verdict"] = "FAIL"
        h6["tests"].append(entry)
    report["H6_host_tests_prove_the_orderings"] = h6

    # ---- H8: THE RELEASED FIRMWARE MUST ACTUALLY RUN THE TESTED SEAM -----
    # D-787 / R6-E01.  H6 proves that `aqroot_demo_timing_policy.h` orders the
    # gauge settle and the backlight prime correctly and that six evasions are
    # caught.  It proves NOTHING about whether the shipped firmware calls it.
    # A template nobody invokes is the same defect one level up from the
    # source-text gates Round-6 evaded, so the call sites are a clause: the
    # production entry points must route through the seam, and must not carry a
    # second, untested copy of the same ordering beside it.  Comments are
    # stripped first -- a commented-out call is not a call.
    def _seam_problems(main_text, periph_text):
        problems = []
        main_code = strip_comments(main_text)
        periph_code = strip_comments(periph_text)
        if "qualifyFuelGaugeActiveMode(" not in main_code:
            problems.append("demo/main.cpp does not call "
                            "qualifyFuelGaugeActiveMode()")
        if "runBacklightRampPolicy(" not in periph_code:
            problems.append("aqroot_demo_peripherals.h does not call "
                            "runBacklightRampPolicy()")
        # A local re-implementation beside the seam is an untested second path.
        if re.search(r"delay\s*\(\s*kFuelGaugeActiveSettleMs\s*\)", main_code):
            problems.append("demo/main.cpp waits the settle itself instead of "
                            "through the tested seam")
        if re.search(r"ledcWrite\s*\([^)]*,\s*255\s*\)", periph_code):
            problems.append("aqroot_demo_peripherals.h drives the full-duty "
                            "prime itself instead of through the tested seam")
        # A LITERAL microsecond hold is a re-implemented prime; the seam's own
        # `[](uint32_t us) { delayMicroseconds(us); }` injector is not, and must
        # not be mistaken for one.
        if re.search(r"delayMicroseconds\s*\(\s*\d", periph_code):
            problems.append("aqroot_demo_peripherals.h holds the prime itself "
                            "instead of through the tested seam")
        return problems

    main_src = DEMO_MAIN.read_text(encoding="utf-8", errors="replace") \
        if DEMO_MAIN.exists() else ""
    periph_src = (HW_DIR / "aqroot_demo_peripherals.h").read_text(
        encoding="utf-8", errors="replace") \
        if (HW_DIR / "aqroot_demo_peripherals.h").exists() else ""
    seam_problems = _seam_problems(main_src, periph_src)
    h8_controls = []
    for name, m_text, p_text in (
            ("the gauge call site drops back to a local delay",
             main_src.replace(
                 "return qualifyFuelGaugeActiveMode(",
                 "if (!g_fuel_gauge.configureActiveMode(g_bus)) return false;\n"
                 "  delay(kFuelGaugeActiveSettleMs);\n  return true;\n  "
                 "return qualifyFuelGaugeActiveMode(", 1), periph_src),
            ("the gauge call site is commented out",
             main_src.replace("return qualifyFuelGaugeActiveMode(",
                              "return false; // qualifyFuelGaugeActiveMode(", 1),
             periph_src),
            ("the backlight call site re-implements the prime",
             main_src,
             periph_src.replace(
                 "  runBacklightRampPolicy(",
                 "  ledcWrite(channel, 255);\n  delayMicroseconds(3000);\n"
                 "  runBacklightRampPolicy(", 1)),
            ("the backlight call site is commented out",
             main_src,
             periph_src.replace("  runBacklightRampPolicy(",
                                "  // runBacklightRampPolicy(", 1))):
        p_list = _seam_problems(m_text, p_text)
        h8_controls.append(dict(control=name, refused=bool(p_list),
                                first_reason=p_list[0] if p_list else None))
    report["H8_released_firmware_runs_the_tested_timing_seam"] = {
        "call_sites": {
            "gauge": DEMO_MAIN.relative_to(ROOT).as_posix(),
            "backlight": (HW_DIR / "aqroot_demo_peripherals.h")
                         .relative_to(ROOT).as_posix(),
            "seam": (HW_DIR / "aqroot_demo_timing_policy.h")
                    .relative_to(ROOT).as_posix(),
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
