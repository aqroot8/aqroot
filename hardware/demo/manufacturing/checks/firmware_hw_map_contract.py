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
  H6  TWO HOST TESTS compile under `-Wall -Wextra -Werror` and pass, and live
      destructive controls must make them FAIL.
        * the EXPANDER SAFE-ORDERING test.  The PCAL9535A resets to all-inputs
          with its output latches at 0xFF, while six of this board's expander
          outputs are safe at 0.  A warm MCU reset can also inherit arbitrary
          old output commands.  The complete SAFE LATCH must therefore be the
          first write, direction last, independent failures must not suppress
          the other shutdown path, and an ambiguous partial port-pair write
          must invalidate the software shadow and fall back to an absolute
          safe-latch write.  The test records those I2C transactions directly.
        * the SPI BUS B ARBITER test.  U7, U8 and U9 share one bus and the two
          rules over it -- one chip select at a time, one transmitter at a time
          -- were comments until D-748.  A comment cannot refuse.
  H7  the actual Demo `setup()` establishes I2C and the complete PCAL safe
      state BEFORE `Serial.begin`, the optional three-second console wait, I2C
      scanning or peripheral discovery.  This closes the round-2 warm-reset
      integration defect that was invisible inside the driver-level H6 test.

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
HOST_TESTS = [
    ROOT / "Firmware/test/test_expander_order.cpp",
    ROOT / "Firmware/test/test_spi_bus_b.cpp",
]
DEMO_MAIN = ROOT / "Firmware/src/demo/main.cpp"
I2C_ARDUINO = ROOT / "Firmware/src/hw/aqroot_i2c_arduino.h"

# Each control is (name, file under src/hw, exact text, replacement).  The
# replacement must be a DEFENSIBLE-LOOKING mistake -- the kind a future edit
# actually makes -- not a syntax error.
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
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_BOOST_EN, true)) return false;
      return u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true);""",
     """      if (!u3_.writeBit(bus, AQROOT_U3_ACC_5V_SW_EN, true)) return false;
      return u3_.writeBit(bus, AQROOT_U3_ACC_5V_BOOST_EN, true);"""),
    # D-751 -- THE THREE INDEPENDENT-FAILURE CONTROLS.  D-750 repaired three
    # `||` short circuits that an external review named, and nothing proved the
    # repair: a bus that always ACKs cannot tell an independent sequence from a
    # short-circuiting one, which is exactly why the bug lived so long.  These
    # put each short circuit BACK; the host test's T10 must refuse all three.
    ("a U2 bus failure leaves U3 unconfigured (begin short-circuits)",
     "aqroot_demo_expanders.h",
     """    const bool u2_ok = u2_.apply(bus, u2);
    const bool u3_ok = u3_.apply(bus, u3);
    if (!u2_safe || !u3_safe || !u2_ok || !u3_ok) return false;""",
     """    if (!u2_safe || !u3_safe) return false;
    if (!u2_.apply(bus, u2) || !u3_.apply(bus, u3)) return false;"""),
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
    ("a failed output-pair write keeps a stale software shadow",
     "pcal9535a.h",
     """      shadow_valid_ = false;
      return false;
    }
    shadow_ = value;""",
     """      return false;
    }
    shadow_ = value;"""),
    ("a failed 5 V shutdown skips the absolute safe-latch fallback",
     "aqroot_demo_expanders.h",
     "    if (!sw || !clear) fallback = u3_.writeOutputs(bus, kU3SafeLatch);",
     "    if (false) fallback = u3_.writeOutputs(bus, kU3SafeLatch);"),
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


def strip_comments(text):
    """Drop // and /* */ comments so only code is scanned for symbols."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def setup_safety_order(text):
    """D-766: prove integration order in the real Demo entry point, not merely
    inside the expander driver.  The first Serial/logging/discovery action must
    come after I2C open and the complete PCAL safe-state transaction."""
    code = strip_comments(text)
    markers = {
        "i2c_open": "const bool i2c_open = g_bus.begin(AQROOT_I2C_BRINGUP_HZ);",
        "expanders_safe": "const bool expanders_safe = i2c_open && g_expanders.begin(g_bus);",
        "serial_begin": "Serial.begin(115200);",
        "i2c_scan": "scanI2c();",
    }
    positions = {k: code.find(v) for k, v in markers.items()}
    present = all(v >= 0 for v in positions.values())
    ordered = (present and positions["i2c_open"] < positions["expanders_safe"] <
               positions["serial_begin"] < positions["i2c_scan"])
    return ordered, positions


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
    for test, controls in zip(HOST_TESTS, (ORDER_CONTROLS, BUS_CONTROLS)):
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
                caught=(c_code != 0),
                first_failed_claim=c_claims[0] if c_claims else None))
        entry["verdict"] = ("PASS" if compiled and code == 0 and claims
                            and all(c["caught"] for c in entry["controls"])
                            else "FAIL")
        if entry["verdict"] != "PASS":
            h6["verdict"] = "FAIL"
        h6["tests"].append(entry)
    report["H6_host_tests_prove_the_orderings"] = h6

    # ---- H7 -------------------------------------------------------------
    main_text = DEMO_MAIN.read_text(encoding="utf-8")
    ordered, positions = setup_safety_order(main_text)
    recovery = "if (!recoverStuckBus()) return false;" in strip_comments(
        I2C_ARDUINO.read_text(encoding="utf-8"))
    # Live negative control: insert an early Serial.begin immediately before
    # the I2C-open marker.  The same checker must refuse that realistic
    # regression even though the later safe initialization still exists.
    marker = "  const bool i2c_open = g_bus.begin(AQROOT_I2C_BRINGUP_HZ);"
    mutated = main_text.replace(marker, "  Serial.begin(115200);\n" + marker, 1)
    control_ordered, _ = setup_safety_order(mutated)
    report["H7_warm_reset_safe_state_precedes_console_and_discovery"] = {
        "positions": positions,
        "i2c_bus_recovery_precedes_Wire_begin": recovery,
        "early_serial_control_refused": not control_ordered,
        "verdict": "PASS" if ordered and recovery and not control_ordered else "FAIL",
    }

    # ---- controls -------------------------------------------------------
    controls = []
    for name, mutate in CONTROLS:
        refused = with_policy(mutate)
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
