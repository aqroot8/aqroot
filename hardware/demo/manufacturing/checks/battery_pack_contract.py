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
HARNESS = ROOT / "docs/full-beta-v2/assembly/BATTERY_HARNESS.json"
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
    # D-773 ADDS R99/R100/U21: the 5 V rail's setpoint is DERIVED from the
    # board's own feedback divider and the boost's own published VREF band, and
    # the envelope's pack cost scales directly with it.
    for ref in ("R97", "R101", "U20", "U22", "R75", "U18",
                "R99", "R100", "U21"):
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
    # Sounddon 785060 s8.3.2 expresses the discharge limit as <=2C5A rather
    # than as a literal amperes row.  C5 is the rated five-hour capacity; for
    # this exact 2500 mAh pack, 2C5 derives to 5.0 A.  Bind the stored ampere
    # figure to that notation so a PDF-text/OCR ambiguity cannot invent a
    # current rating (Round-4 Fable T2).
    c5_Ah = float(rec.get("capacity_mAh", 0)) / 1000.0
    c5_mult = float(rec.get("linked_datasheet_max_discharge_C5_multiplier", 0) or 0)
    derived_discharge_A = c5_Ah * c5_mult
    declared_discharge_A = float(rec.get("linked_datasheet_max_discharge_A", 0) or 0)
    discharge_basis_ok = (
        rec.get("linked_datasheet_max_discharge_notation") == "2C5A"
        and c5_mult == 2.0
        and abs(declared_discharge_A - derived_discharge_A) <= 1e-9
        and "section 8.3.2" in (rec.get("linked_datasheet_max_discharge_basis") or ""))
    checks["B5_pack_discharge_covers_live_D753_envelope"] = dict(
        ok=(discharge_basis_ok and
            derived_discharge_A >= req["required_pack_discharge_A"]),
        datasheet_notation=rec.get("linked_datasheet_max_discharge_notation"),
        c5_capacity_Ah=c5_Ah, c5_multiplier=c5_mult,
        derived_pack_max_discharge_A=derived_discharge_A,
        stored_pack_max_discharge_A=declared_discharge_A,
        derivation_is_pinned=discharge_basis_ok,
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
    harness = rec.get("_harness", {})
    board = harness.get("board_side", {})
    pack = harness.get("battery_side", {})
    rating = harness.get("controlling_rating", {})
    polarity = harness.get("polarity", {})
    relief = harness.get("strain_relief", {})
    relief_tds_rel = relief.get("archived_tds", "")
    relief_tds = ROOT / relief_tds_rel if relief_tds_rel else None
    relief_tds_actual_sha256 = (sha256(relief_tds)
                                if relief_tds and relief_tds.is_file() else None)
    relief_tds_expected_sha256 = relief.get("archived_tds_sha256")
    checks["B9_D781_board_harness_identity_is_frozen"] = dict(
        ok=(rec.get("board_harness") == "docs/full-beta-v2/assembly/BATTERY_HARNESS.json"
            and rec.get("board_connector") ==
                "J4 D-781 manual pigtail -> Molex Micro-Lock Plus 2.0 5055700201"
            and harness.get("status") == "FROZEN_FOR_FIRST_FIVE"
            and board.get("wire_AWG") == 26
            and board.get("receptacle_housing") == "5055700201"
            and float(board.get("nominal_drill_mm", 0)) == 0.75
            and float(board.get("required_finished_hole_min_mm", 0)) == 0.70
            and float(board.get("factory_tinned_tip_max_mm", 99)) <= 0.65
            and "do NOT cut/re-strip/re-tin" in board.get("assembly", "")
            and "2175012101" in board.get("precrimp_red", "")
            and "2175011101" in board.get("precrimp_black", "")
            and pack.get("factory_lead_AWG") == 26
            and pack.get("plug_housing") == "2137192021"
            and pack.get("male_terminal") == "2137201000"
            and relief.get("material") ==
                "DOWSIL 3145 RTV MIL-A-46146 Adhesive/Sealant, gray"
            and relief.get("manufacturer") == "Dow"
            and relief.get("primary_source_url") ==
                "https://www.dow.com/en-us/pdp.dowsil-3145-rtv-mil-a-46146-adhesive-sealant.01059548z.html"
            and relief_tds_expected_sha256 ==
                "905af2ec4eafd4fe54fe748cab36450a121b4b04cedc375120299baefb38e115"
            and relief_tds_actual_sha256 == relief_tds_expected_sha256
            and "non-flow" in relief.get("primary_source_basis", "").lower()
            and ">=35 mm" in relief.get("service_loop", "")
            and "never disconnect by pulling" in relief.get("disconnect_instruction", "")),
        status=harness.get("status"), board_connector=rec.get("board_connector"),
        board_wire_AWG=board.get("wire_AWG"), board_housing=board.get("receptacle_housing"),
        battery_wire_AWG=pack.get("factory_lead_AWG"), battery_plug=pack.get("plug_housing"),
        strain_relief_tds=relief_tds_rel,
        strain_relief_tds_expected_sha256=relief_tds_expected_sha256,
        strain_relief_tds_actual_sha256=relief_tds_actual_sha256)
    rated = float(rating.get("rated_current_A", 0) or 0)
    live = float(req["max_user_reachable_battery_A"])
    checks["B10_D781_harness_rating_and_polarity_cover_live_board"] = dict(
        ok=(rating.get("wire_AWG") == 26 and rated >= live
            and polarity.get("cavity_1") == "BAT+ / red / J4.1"
            and polarity.get("cavity_2") == "GND / black / J4.2"),
        controlling_rating_A=rated, live_max_battery_A=live,
        current_margin_A=round(rated-live, 4),
        current_margin_pct=round((rated/live-1.0)*100.0, 2) if live else None,
        cavity_1=polarity.get("cavity_1"), cavity_2=polarity.get("cavity_2"))
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    rec = json.loads(SELECTED.read_text())
    harness = json.loads(HARNESS.read_text())
    rec["_harness"] = harness
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
    for name, mutate, clause in (
        ("old_JST_board_header_refused",
         lambda m: m.__setitem__("board_connector", "J4 B2B-PH-K-S(LF)(SN)"),
         "B9_D781_board_harness_identity_is_frozen"),
        ("24AWG_harness_mismatch_refused",
         lambda m: m["_harness"]["board_side"].__setitem__("wire_AWG", 24),
         "B9_D781_board_harness_identity_is_frozen"),
        ("undersized_finished_J4_hole_process_refused",
         lambda m: m["_harness"]["board_side"].__setitem__(
             "required_finished_hole_min_mm", 0.60),
         "B9_D781_board_harness_identity_is_frozen"),
        ("retinning_factory_board_pigtail_without_requalification_refused",
         lambda m: m["_harness"]["board_side"].__setitem__(
             "assembly", "cut and re-tin the pigtail before fit"),
         "B9_D781_board_harness_identity_is_frozen"),
        ("unqualified_strain_relief_material_refused",
         lambda m: m["_harness"]["strain_relief"].__setitem__(
             "material", "generic RTV"),
         "B9_D781_board_harness_identity_is_frozen"),
        ("strain_relief_tds_hash_tamper_refused",
         lambda m: m["_harness"]["strain_relief"].__setitem__(
             "archived_tds_sha256", "0" * 64),
         "B9_D781_board_harness_identity_is_frozen"),
        ("2A_connector_rating_refused",
         lambda m: m["_harness"]["controlling_rating"].__setitem__("rated_current_A", 2.0),
         "B10_D781_harness_rating_and_polarity_cover_live_board"),
        ("reversed_harness_polarity_refused",
         lambda m: m["_harness"]["polarity"].__setitem__("cavity_1", "GND / black / J4.2"),
         "B10_D781_harness_rating_and_polarity_cover_live_board"),
    ):
        m = copy.deepcopy(rec)
        mutate(m)
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
