#!/usr/bin/env python3
"""AQROOT Demo -- selected first-five battery contract (CTO-BAT-01).

The PCB can pass every board gate while an underspecified LiPo still browns out
or trips its PCM under the D-753 accessory envelope.  This contract binds the
first-five pack to the live hardware load limit and to one exact supplier SKU.
"""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import demo_feature_contract as dfc

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
SELECTED = ROOT / "docs/full-beta-v2/assembly/SELECTED_BATTERY.json"
DIMENSION_LIMITS = {"thickness": 8.0, "width": 57.0, "length": 75.0}
DISCHARGE_MARGIN = 1.20

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resistor_ohms(text):
    import re
    t = (text or "").strip().upper().replace("Ω", "")
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)([KMR]?)([0-9]*)", t)
    if not m:
        raise ValueError("unreadable resistor value: %r" % text)
    whole, suffix, frac = m.groups()
    n = float(whole + (("." + frac) if frac else ""))
    return n * {"": 1.0, "R": 1.0, "K": 1e3, "M": 1e6}[suffix]


def board_requirements():
    board = pcbnew.LoadBoard(str(BOARD))
    values = {}
    # D-765: the envelope is a function of the two programming resistors AND the
    # two limiter part numbers -- an ILIM setting outside the fitted part's own
    # published range is not an envelope, so U20/U22 are read here as well.
    # D-771 ADDS R75 AND U18.  `judge_accessory_envelope` now also orders the
    # PROTECTION CHAIN over tolerance, and it reads the sense element and the
    # breaker part from the same {ref: value} map; omitting them makes the whole
    # envelope unreadable rather than merely unchecked.
    for ref in ("R97", "R101", "U20", "U22", "R75", "U18"):
        fp = board.FindFootprintByReference(ref)
        if not fp:
            raise RuntimeError("missing %s" % ref)
        values[ref] = fp.GetValue()
    env_ok, env = dfc.judge_accessory_envelope(values)
    if not env_ok:
        failed = sorted(k for k, v in env.items() if isinstance(v, bool) and not v)
        raise RuntimeError("D-753/D-765 accessory envelope itself does not pass: %s"
                           % (failed or env.get("error")))
    modes = env["modes_I_bat_A"]
    # D-771: the same REACHABLE set `judge_accessory_envelope` uses, including
    # the state where BOTH rails deliver the budget D-098 publishes for them.
    reachable = (
        "acc3v3_alone_at_its_limiter",
        "acc5v_alone_at_its_limiter",
        "both_at_their_guaranteed_currents",
        "both_at_their_published_budgets",
    )
    max_reachable = max(modes[k] for k in reachable)

    r37 = board.FindFootprintByReference("R37")
    if not r37:
        raise RuntimeError("missing R37")
    r37_ohm = resistor_ohms(r37.GetValue())
    ichg_nom = 300.0 / r37_ohm
    # BQ25185 fast-charge accuracy ±10%; fitted R37 is a 1 % resistor.
    ichg_max = ichg_nom * 1.10 / 0.99
    board_digest = sha256(BOARD)
    return dict(
        board_sha256=board_digest,
        accessory_modes_A=modes,
        max_user_reachable_battery_A=max_reachable,
        required_pack_discharge_A=max_reachable * DISCHARGE_MARGIN,
        discharge_margin_ratio=DISCHARGE_MARGIN,
        r37_ohm=r37_ohm,
        ichg_nominal_A=ichg_nom,
        required_pack_charge_A=ichg_max,
    )


def evaluate(rec, req, actual_pdf_hash):
    dims = rec.get("max_pack_dimensions_mm", {})
    expected_pdf = rec.get("datasheet_sha256")
    checks = {}
    checks["B1_exact_first_five_identity"] = dict(
        ok=(rec.get("status") == "SELECTED_FOR_FIRST_FIVE"
            and rec.get("supplier") == "Adafruit Industries"
            and rec.get("supplier_sku") == "328"),
        supplier=rec.get("supplier"), supplier_sku=rec.get("supplier_sku"))
    checks["B2_datasheet_is_pinned"] = dict(
        ok=(bool(expected_pdf) and expected_pdf == actual_pdf_hash),
        expected_sha256=expected_pdf, actual_sha256=actual_pdf_hash)
    checks["B3_capacity_is_the_selected_low_timer_margin_option"] = dict(
        ok=(rec.get("capacity_mAh") == 2500),
        capacity_mAh=rec.get("capacity_mAh"))
    checks["B4_pack_fits_reserved_envelope"] = dict(
        ok=all(float(dims.get(k, 1e9)) <= v for k, v in DIMENSION_LIMITS.items()),
        dimensions_mm=dims, limits_mm=DIMENSION_LIMITS)
    checks["B5_pack_discharge_covers_live_D753_envelope"] = dict(
        ok=float(rec.get("linked_datasheet_max_discharge_A", 0))
           >= req["required_pack_discharge_A"],
        pack_max_discharge_A=rec.get("linked_datasheet_max_discharge_A"),
        max_user_reachable_battery_A=req["max_user_reachable_battery_A"],
        required_with_margin_A=round(req["required_pack_discharge_A"], 4),
        margin_ratio=DISCHARGE_MARGIN)
    checks["B6_pack_charge_rating_covers_BQ25185_envelope"] = dict(
        ok=float(rec.get("supplier_recommended_max_charge_A", 0))
           >= req["required_pack_charge_A"],
        supplier_max_charge_A=rec.get("supplier_recommended_max_charge_A"),
        board_required_A=round(req["required_pack_charge_A"], 4))
    checks["B7_protection_connector_and_polarity_are_explicit"] = dict(
        ok=(rec.get("pcm_protection") is True
            and rec.get("connector") == "genuine 2-pin JST-PH"
            and rec.get("board_positive_pin") == "J4.1"
            and rec.get("incoming_polarity_verification_required") is True),
        pcm=rec.get("pcm_protection"), connector=rec.get("connector"),
        board_positive_pin=rec.get("board_positive_pin"),
        incoming_polarity_check=rec.get("incoming_polarity_verification_required"))
    charge_temp = rec.get("linked_datasheet_charge_temp_C", [])
    checks["B8_no_thermistor_requires_supervised_prototype_charging"] = dict(
        ok=(rec.get("thermistor_present") is False
            and rec.get("prototype_charging_supervised") is True
            and charge_temp == [0, 40]),
        thermistor_present=rec.get("thermistor_present"),
        supervised=rec.get("prototype_charging_supervised"),
        permitted_charge_temp_C=charge_temp)
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    rec = json.loads(SELECTED.read_text())
    pdf = ROOT / rec["datasheet_path"]
    actual_pdf_hash = sha256(pdf) if pdf.exists() else None
    req = board_requirements()
    checks = evaluate(rec, req, actual_pdf_hash)
    controls = {}
    mutations = (
        ("1p5A_discharge_variant_refused", "linked_datasheet_max_discharge_A", 1.5,
         "B5_pack_discharge_covers_live_D753_envelope"),
        ("700mA_charge_variant_refused", "supplier_recommended_max_charge_A", 0.7,
         "B6_pack_charge_rating_covers_BQ25185_envelope"),
        ("8p1mm_thick_variant_refused", "max_pack_dimensions_mm", {"thickness": 8.1, "width": 50.5, "length": 60.5},
         "B4_pack_fits_reserved_envelope"),
        ("unprotected_pack_refused", "pcm_protection", False,
         "B7_protection_connector_and_polarity_are_explicit"),
        ("wrong_connector_refused", "connector", "generic 2-pin lead",
         "B7_protection_connector_and_polarity_are_explicit"),
        ("skipped_polarity_check_refused", "incoming_polarity_verification_required", False,
         "B7_protection_connector_and_polarity_are_explicit"),
        ("unsupervised_no_thermistor_refused", "prototype_charging_supervised", False,
         "B8_no_thermistor_requires_supervised_prototype_charging"),
        ("datasheet_hash_tamper_refused", "datasheet_sha256", "0" * 64,
         "B2_datasheet_is_pinned"),
    )
    for name, field, value, clause in mutations:
        m = copy.deepcopy(rec)
        m[field] = value
        got = evaluate(m, req, actual_pdf_hash)
        controls[name] = not got[clause]["ok"]

    all_checks = all(c["ok"] for c in checks.values())
    all_controls = all(controls.values())
    doc = dict(
        schema=1, contract="battery_pack", decision="CTO-BAT-01",
        board=str(BOARD), board_sha256=req["board_sha256"],
        selected_record=str(SELECTED.relative_to(ROOT)), requirements=req,
        checks=checks, controls_refused=controls,
        all_pass=(all_checks and all_controls),
        verdict="PASS" if all_checks and all_controls else "FAIL")
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
