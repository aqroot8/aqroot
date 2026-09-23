#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- THE INDEPENDENT POWER ORACLE.

ADDED AT D-793 as Round-12's R12-04, which is a RELEASE BLOCKER in its own
words:

    "Astra halved canonical charger package heat and all F1-F13 still passed.
     Astra removed the 5V-first transition; completeness Boolean became false
     but final verdict remained PASS.  This is a release blocker: the
     canonical model cannot be its own oracle.
     Implement a SMALL INDEPENDENT equation oracle that does NOT import/call
     canonical solver derived functions."

BOTH HALVES OF THAT REPRODUCE, AND THE CAUSE IS THE SAME ONE TWICE.  D-792
added `charger_invariants`, and its `energy_balance` term compared

    p_in + p_from_cell - p_sys - p_stored   against   p_diss

where `p_diss` was DEFINED three lines earlier as exactly that expression.
The check was `0 == 0`.  Nothing in the whole D-792 suite ever compared the
TERMINAL power balance with the sum of the INTERNAL loss elements, so halving
the package heat moved a number that no equation was watching.  And F12's
verdict was a conjunction of clauses that did not include the transition-set
completeness Boolean, so a missing rail order was REPORTED and not RULED ON.

WHAT THIS MODULE IS, AND WHAT IT DELIBERATELY IS NOT.

It is a SECOND, SMALL, STRUCTURALLY INDEPENDENT implementation of the handful
of physical identities the release rests on.  It imports NOTHING from
`aqroot_power_model`, `audit_rail_ampacity` or `demo_feature_contract`.  It
solves nothing and iterates nothing: every function here takes an ALREADY
SOLVED state as plain numbers and re-derives the quantities that state claims,
from primitives, with arithmetic a reader can check by hand.

IT IS NOT A SECOND AUTHORITY, AND THE DISTINCTION MATTERS.  D-792 exists
because two files were allowed to describe two different boards.  The
primitives below are a CHECKSUM of the canonical registry, not a competing
copy: `primitives_agree()` compares every one of them with the canonical
model's own tagged value, and a disagreement is a FAILURE -- "the canonical
model and the oracle disagree about `bq.ron_in_max_ohm`" -- rather than a
silent second opinion.  So an edit to a canonical primitive that is not
mirrored here stops the release and puts a human in front of both files, which
is the only useful thing a second implementation can do.

COMPLETENESS IS A VERDICT HERE, NOT METADATA (convergence requirement 3).
`completeness()` returns a hard Boolean over: both rail orders present, every
required transition key present, every required charger branch exercised,
every REJECTED post-state retained in the rejection set rather than dropped,
and the independent residuals inside tolerance.  `audit()` ANDs it into `ok`.
"""

import math

# The canonical model returns its solved states ROUNDED to six decimals for
# the report and UNROUNDED under a `raw` key, exactly as F12's own residual
# check needs.  Every residual below is taken on the RAW values, so these
# tolerances mean what they say instead of measuring the rounding.
TOL_W = 1e-9            # power residuals
TOL_V = 1e-9            # voltage residuals
TOL_A = 1e-9            # current residuals
# The canonical source-path figure is rounded to six decimals, and so is
# each of the terms it sums, so a few micro-ohms of accumulated rounding is
# expected.  Five micro-ohms on a 355 mOhm path is 0.0014 %; the mutation this
# tolerance has to stay under is the omitted 11 mOhm ground return, which is
# three orders of magnitude larger.
TOL_PATH_OHM = 5e-6

# ==========================================================================
# 1.  THE PRIMITIVES.  A CHECKSUM OF THE CANONICAL REGISTRY, NOT A COPY.
#
# Each key is the canonical model's OWN registry key, so `primitives_agree()`
# can join them without a translation table.  The values are re-read from the
# same primary documents, by hand, at D-793.
# ==========================================================================
PRIMITIVES = {
    # --- the USB source ---------------------------------------------------
    # D-795: the NAMED adapter, 5.1 V x (1 +/- 0.07) -- load +/-5 % plus
    # line +/-2 %, Raspberry Pi 15W USB-C PSU product brief, by hand.
    "usb.rpi15w_regulation_fraction": 0.07,
    "usb.vbus_source_max_V": 5.457,
    "usb.vbus_source_min_V": 4.743,
    "usb.awg18_stranded_max_ohm_per_m": 0.0228,
    # --- the BQ25185 (TI SLUSF65B) ---------------------------------------
    "bq.vsys_reg_V": 4.5,
    "bq.ron_in_max_ohm": 0.470,
    "bq.ron_bat_max_ohm": 0.140,
    "bq.ron_bat_vbat_allowance": 1.40,
    "bq.ilim_min_A": 0.995,
    "bq.ilim_max_A": 1.100,
    "bq.ichg_A": 0.769,
    # D-795 / R14-04: the programmed charge current is a BAND.
    "bq.kiset_min_AOhm": 285.0,
    "bq.kiset_max_AOhm": 315.0,
    "bq.iprechg_fraction": 0.20,
    "bq.iprechg_accuracy": 0.10,
    "bq.vlowv_min_V": 2.9,
    "bq.treg_typ_C": 100.0,
    "bq.treg_declared_band_K": 10.0,
    # D-794 / R13-02.  THE FOUR CONTROL-LOOP THRESHOLDS, read off the same EC
    # table by hand.  Each is a DIFFERENT physical loop and the oracle checks
    # each branch against its own.
    "bq.vdppm_V": 0.100,
    "bq.vbsup1_V": 0.040,
    "bq.vbsup2_V": 0.020,
    "bq.vindpm_track_V": 0.330,
    "bq.vindpm_track_vbat_floor_V": 3.5,
    "bq.vindpm_fixed_V": 3.6,
    "bq.branch_threshold_sweep": 0.50,
    "bq.fixed_vindpm_sweep_ratio": 0.10,
    # --- the battery path (Molex 5055700003-PS, D-771, D-781) -------------
    "path.microlock_contact_aged_max_ohm": 0.040,      # 6.2.6/6.3.x
    "path.microlock_contact_initial_max_ohm": 0.020,   # 6.1.1
    "path.crimp_max_ohm": 0.005,                       # 6.1.4
    "path.j4_solder_joint_max_ohm": 0.001,
    "path.pack_ac_impedance_max_ohm": 0.035,
    "path.pack_ac_to_dc_multiplier": 2.5,
    "path.f1_fuse_max_ohm": 0.020,
    "path.f1_fuse_tolerance": 0.25,
    "path.r75_sense_max_ohm": 0.0101,
    "path.r75_sense_min_ohm": 0.0099,
    "path.awg26_stranded_max_ohm_per_m": 0.145800,
    "path.gnd_return_squares": 12.0,
    "path.gnd_return_barrel_ohm": 0.002,
    "path.inner_copper_thickness_m": 15.2e-6,
    # --- the MCU module (Espressif v1.8) ---------------------------------
    "mcu.ivdd_supply_requirement_A": 0.500,
    "mcu.modem_sleep_240MHz_dual_128bit_periph_on_A": 0.1079,
    "mcu.flash_access_A": 0.010,
    "mcu.psram_allowance_A": 0.020,
    "mcu.typ_to_bound_widening": 1.20,
    "mcu.rf_tx_peak_80211b_20p5dBm_A": 0.355,
}
# Constants this module needs that are NOT in the canonical registry because
# the canonical model carries them as module-level floats.  They are passed in
# by the caller and cross-checked, so they are listed here only as names.
REQUIRED_SCALARS = (
    "cu_tc_per_K", "cu_hot_rise_K", "rho_cu_ohm_m",
    "eta_u12", "eta_u21", "gauge_verr_V", "gauge_lsb_V",
    "buvlo_bound_V", "u12_vin_floor_V", "theta_ja_C_per_W",
    "tj_operating_max_C", "r_sys_K_per_W", "ambient_C",
)


def primitives_agree(registry, scalars):
    """Every primitive here must equal the canonical model's tagged value.

    `registry` is `aqroot_power_model.registry()` as DATA -- a list of dicts --
    so this function still calls nothing from that module.
    """
    by_key = {}
    for row in registry:
        by_key.setdefault(row["key"], row["value"])
    problems = []
    for key, mine in sorted(PRIMITIVES.items()):
        if key not in by_key:
            problems.append("the canonical registry has no entry %r" % key)
            continue
        theirs = by_key[key]
        if not isinstance(theirs, (int, float)):
            problems.append("%s is not numeric in the canonical registry"
                            % key)
        elif abs(float(theirs) - mine) > 1e-12:
            problems.append("the canonical model and the oracle disagree "
                            "about %s: %r vs %r" % (key, theirs, mine))
    missing = [k for k in REQUIRED_SCALARS if k not in scalars]
    if missing:
        problems.append("the caller did not supply %s" % ", ".join(missing))
    return (not problems), dict(
        checked=len(PRIMITIVES), problems=problems,
        method="the oracle's primitives are a CHECKSUM of the canonical "
               "registry, not a second authority.  A canonical value changed "
               "without mirroring it here stops the release and puts a human "
               "in front of both files.")


# ==========================================================================
# 2.  THE CHARGER.  TERMINAL POWER IS THE ORACLE; THE INTERNAL LOSS SUM IS
#     WHAT IT CHECKS.  R12-04: "Use terminal-power balance as an independent
#     oracle, not the same internal loss sum."
# ==========================================================================
# D-794 / R13-02.  THE BRANCH SET IS THE DEVICE'S OWN CONTROL LOOPS.
#
# D-793's four names collapsed SYS regulation, the input current limit and the
# DPPM loop into two, and the canonical solver and this oracle AGREED about
# the wrong physics because both were written from the same wrong list.  The
# names below are re-derived from SLUSF65B 6.3.1/6.3.2/6.3.3/6.3.5/6.3.6 and
# every inequality here is written out from the primitives rather than
# imported.
CHARGER_BRANCHES = ("SYS_REG", "CC_PATH_LIMITED", "TREG", "ILIM", "VINDPM",
                    "DPPM", "NO_CHARGE", "SUPPLEMENT")
# D-795: R37, read off the schematic by hand (390 R 1 %, UNI-ROYAL
# 0603WAF3900T5E).  The oracle derives the ICHG band from it and KISET itself.
ORACLE_R37_OHM = 390.0
ORACLE_R37_TOLERANCE = 0.01


def oracle_charge_program(vbat, ichg_corner):
    """The CC / precharge program, from primitives, independently."""
    p = PRIMITIVES
    if ichg_corner == "max":
        ichg = p["bq.kiset_max_AOhm"] / (ORACLE_R37_OHM
                                         * (1.0 - ORACLE_R37_TOLERANCE))
        acc = 1.0 + p["bq.iprechg_accuracy"]
    elif ichg_corner == "min":
        ichg = p["bq.kiset_min_AOhm"] / (ORACLE_R37_OHM
                                         * (1.0 + ORACLE_R37_TOLERANCE))
        acc = 1.0 - p["bq.iprechg_accuracy"]
    else:
        ichg, acc = p["bq.ichg_A"], 1.0
    if vbat < p["bq.vlowv_min_V"]:
        return ichg * p["bq.iprechg_fraction"] * acc, "PRECHARGE"
    return ichg, "CC"
# The branches that MUST appear somewhere in the derivation for it to have
# exercised the physics at all.  `completeness()` rules on this.
CHARGER_BRANCHES_THAT_FOLD_CHARGE = ("ILIM", "VINDPM", "DPPM")


# ==========================================================================
# D-794 / ROUND-13 FABLE DELTA.  A DUPLICATE REPRESENTATION IS A PLACE TO
# HIDE, AND THE ORACLE WAS LOOKING IN THE WRONG COPY.
#
# ROUND-13, IN ITS OWN WORDS: "Fable found aqroot_power_oracle.py
# charger_residuals prefers st['raw'] values, so corrupted canonical summary
# fields can be invisible.  Assert raw == public summary for every duplicated
# state field or eliminate the duplicate representation.  The oracle must
# detect a mismatch in input_A, system_A, battery_A, SYS, VIN, package heat
# and branch.  Add mutations that alter summary only and raw only; both must
# fail unless the duplicate is removed."
#
# IT IS EXACTLY RIGHT.  `charger_state()` publishes every solved quantity
# TWICE: once rounded into the public summary that every downstream consumer,
# document and human reads, and once at full precision in `raw` so an oracle
# can check an identity without fighting the rounding.  `charger_residuals`
# read `raw` wherever it could -- which is the correct choice for PRECISION
# and the wrong one for AUTHORITY, because it meant the public numbers were
# never checked at all.  Corrupt `input_A` alone and the terminal balance
# still closes on `raw`; the released figure is simply wrong.
#
# THE DUPLICATE IS NOT REMOVED, BECAUSE THE PRECISION IS GENUINELY NEEDED --
# a 1e-9 W energy residual cannot be taken on six-decimal numbers.  It is
# EQUALITY-GATED instead: the public field must be EXACTLY the published
# rounding of its raw twin, to the precision the model publishes at.  A
# summary-only mutation now fails here; a raw-only mutation fails here AND in
# the residuals; and no third possibility exists, because the two are checked
# against each other rather than each against itself.
#
# Package heat and the BRANCH have no raw twin -- they are DERIVED -- so they
# are covered where they always should have been: `package_W` is recomputed
# from the raw terminals in `charger_residuals` and compared with the
# published figure, and `mode` is re-derived from the inequalities in
# `charger_branch_is_valid`, which reads the PUBLIC fields on purpose.
# ==========================================================================
DUPLICATED_STATE_FIELDS = (
    # (public summary key, raw key, published decimals or None for exact)
    ("vsys_V", "vsys", 6),
    ("vbat_V", "vbat", 6),
    ("vin_pin_V", "v_pin", 6),
    ("system_W", "p_sys", 6),
    ("input_A", "i_in", 6),
    ("system_A", "i_sys", 6),
    ("charge_A", "i_chg", 6),
    ("supplement_A", "i_supp", 6),
    ("ilim_A", "ilim", None),
    ("vbus_source_V", "vbus", None),
    ("path_ohm", "path", None),
    # ---- D-795 / R14-05 (Fable R14-13/15): EVERY printed heat field. ------
    ("input_fet_W", "p_input_fet", 6),
    ("charge_fet_W", "p_charge_fet", 6),
    ("batfet_W", "p_batfet", 6),
    ("package_W", "p_pkg", 6),
    ("cable_W", "p_cable", 6),
    ("source_W", "p_in", 6),
    ("stored_W", "p_stored", 6),
    ("from_cell_W", "p_from_cell", 6),
    ("total_dissipation_W", "p_diss_total", 6),
    ("internal_loss_sum_W", "p_loss_sum", 6),
    ("input_fet_resistive_only_W", "p_ron_only", 6),
    ("package_W_treg_cannot_reduce", "p_treg_cannot", 6),
)
DUPLICATED_CONTROL_FIELDS = (
    ("vsys_reg_V", "vsys_reg", 6),
    ("vindpm_threshold_V", "v_vindpm", 6),
    ("vdppm_threshold_V", "v_dppm", 6),
    ("supplement_enter_V", "v_sup_enter", 6),
    ("supplement_exit_V", "v_sup_exit", 6),
    ("input_current_cap_A", "i_cap", 6),
    ("ilim_cap_A", "ilim", 6),
    ("batfet_off_comparator_node_V", "batfet_off_node_V", 6),
    ("charge_program_A", "ichg_max", 6),
    ("nominal_charge_program_A", "ichg_nominal", 6),
)


def raw_summary_divergence(st):
    """Every field published twice must agree.  Returns (ok, [problems])."""
    q = st.get("raw")
    why = []
    if not isinstance(q, dict):
        return False, ["the state publishes no `raw` block to check the "
                       "public summary against"]
    def compare(where, pub_key, raw_key, places, pub, raw_src):
        if pub_key not in pub:
            why.append("%s.%s is missing from the public summary" %
                       (where, pub_key))
            return
        if raw_key not in raw_src:
            why.append("%s raw.%s is missing" % (where, raw_key))
            return
        a, b = pub[pub_key], raw_src[raw_key]
        if a is None or b is None:
            if a is not b:
                why.append("%s.%s is %r but raw.%s is %r" %
                           (where, pub_key, a, raw_key, b))
            return
        want = float(b) if places is None else round(float(b), places)
        if float(a) != want:
            why.append("%s.%s publishes %r; raw.%s rounds to %r" %
                       (where, pub_key, a, raw_key, want))
    for pub_key, raw_key, places in DUPLICATED_STATE_FIELDS:
        compare("state", pub_key, raw_key, places, st, q)
    ctrl = st.get("controls")
    if not isinstance(ctrl, dict):
        why.append("the state publishes no `controls` block")
    else:
        for pub_key, raw_key, places in DUPLICATED_CONTROL_FIELDS:
            compare("controls", pub_key, raw_key, places, ctrl, q)
    return (not why), why


def charger_residuals(st, scalars):
    """Re-derive every claim a solved charger state makes, from primitives.

    `st` is one `charger_state()` result as DATA.  Nothing here calls the
    solver; every line is an identity that a correct solution satisfies.
    """
    p = PRIMITIVES
    q = st.get("raw") or {}
    vbus = q.get("vbus", st["vbus_source_V"])
    path = q.get("path", st["path_ohm"])
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    i_in = q.get("i_in", st["input_A"])
    i_sys = q.get("i_sys", st["system_A"])
    i_chg = q.get("i_chg", st["charge_A"])
    i_supp = q.get("i_supp", st["supplement_A"])
    vsys = q.get("vsys", st["vsys_V"])
    vbat = q.get("vbat", st["vbat_V"])
    v_pin = q.get("v_pin", st["vin_pin_V"])
    p_sys = q.get("p_sys", st["system_W"])

    # (a) the input node: VIN at the pin is the source less the cable drop.
    r_vpin = v_pin - (vbus - i_in * path)
    # (b) KCL at SYS.
    r_kcl = (i_in + i_supp) - (i_sys + i_chg)
    # (c) the load really is constant power at the solved node.
    r_load = vsys * i_sys - p_sys
    # (d) the three package elements, priced from the terminals they sit
    #     between -- NOT from the solver's own sum.
    w_input_fet = max(0.0, (v_pin - vsys) * i_in)
    w_charge_fet = max(0.0, (vsys - vbat) * i_chg)
    w_batfet = max(0.0, (vbat - vsys) * i_supp)
    w_pkg = w_input_fet + w_charge_fet + w_batfet
    # The REPORTED package figures are rounded, so the residual is taken
    # against what the model reports ONLY to the precision it reports at; the
    # identity that matters -- terminal balance vs internal loss sum -- is
    # taken on the raw values and carries the tight tolerance.
    r_pkg = round(w_pkg, 6) - st["package_W"]
    r_pkg_treg = round(w_input_fet + w_batfet, 6) - st[
        "package_W_treg_cannot_reduce"]
    # (e) THE ORACLE ITSELF.  Everything that enters the system, less
    #     everything that leaves it or is stored, must equal the sum of the
    #     dissipating elements.  Two different sets of quantities, one
    #     identity; D-792 compared an expression with itself.
    w_cable = i_in * i_in * path
    terminal = vbus * i_in + vbat * i_supp - p_sys - vbat * i_chg
    r_energy = terminal - (w_pkg + w_cable)
    # D-795 / R14-05: the raw heat twins must equal what the raw TERMINALS
    # say, so a raw-only corruption of a heat field cannot hide behind a
    # matching summary.
    for key, want in (("p_input_fet", w_input_fet), ("p_charge_fet",
                                                      w_charge_fet),
                      ("p_batfet", w_batfet), ("p_pkg", w_pkg),
                      ("p_cable", w_cable), ("p_diss_total", terminal),
                      ("p_loss_sum", w_pkg + w_cable)):
        if key in q:
            r_energy = max(r_energy, abs(q[key] - want), key=abs)
    return dict(
        vin_pin_V=r_vpin, kcl_A=r_kcl, constant_power_W=r_load,
        package_W=r_pkg, package_treg_W=r_pkg_treg,
        terminal_vs_internal_W=r_energy,
        independently_computed=dict(
            input_fet_W=round(w_input_fet, 9),
            charge_fet_W=round(w_charge_fet, 9),
            batfet_W=round(w_batfet, 9),
            cable_W=round(w_cable, 9),
            package_W=round(w_pkg, 9),
            terminal_balance_W=round(terminal, 9)))


def vindpm_threshold(vbat):
    """SLUSF65B 6.3.1 and the VINDPM_TRACK EC row, written out."""
    p = PRIMITIVES
    if vbat > p["bq.vindpm_track_vbat_floor_V"]:
        return vbat + p["bq.vindpm_track_V"]
    return p["bq.vindpm_fixed_V"]


def _oracle_thresholds(vbat, sweep):
    p = PRIMITIVES
    v_dppm = vbat + p["bq.vdppm_V"] * (1.0 + sweep)
    v_sup_enter = vbat - p["bq.vbsup1_V"] * (1.0 - sweep)
    v_sup_exit = vbat - p["bq.vbsup2_V"] * (1.0 - sweep)
    if vbat > p["bq.vindpm_track_vbat_floor_V"]:
        v_vindpm = vbat + p["bq.vindpm_track_V"] * (1.0 + sweep)
    else:
        v_vindpm = p["bq.vindpm_fixed_V"] * (
            1.0 + sweep * p["bq.fixed_vindpm_sweep_ratio"])
    return v_dppm, v_sup_enter, v_sup_exit, v_vindpm


def charger_branch_is_valid(st):
    """The branch INEQUALITIES, from primitives, independently.

    D-795 / R14-03: "F14 must not share the same wrong branch semantics.  Add
    an independent physical inequality: ICHG < programmed ICHG with SYS above
    VBAT+VDPPM is invalid unless a documented control such as TREG is
    active."  So the program is recomputed HERE from KISET, R37 and the
    precharge row; ILIM, VINDPM and DPPM must all hold SYS at VBAT + VDPPM;
    and a folded charge above that node is legal only in the TREG branch --
    whose junction the oracle re-derives from the state's own thermal block
    and requires to sit at the TREG threshold it names.
    """
    p = PRIMITIVES
    ctrl = st.get("controls") or {}
    sweep = float(ctrl.get("sweep") or 0.0)
    vsys_reg = p["bq.vsys_reg_V"] * 0.98
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    ilim = st["ilim_A"]
    path = st["path_ohm"]
    vbus = st["vbus_source_V"]
    r_src = path + ron_in
    vsys, vbat, v_pin = st["vsys_V"], st["vbat_V"], st["vin_pin_V"]
    i_in, i_chg, i_supp = st["input_A"], st["charge_A"], st["supplement_A"]
    mode = st["mode"]
    loop = ctrl.get("charge_loop")
    nominal, kind = oracle_charge_program(vbat, st.get("ichg_corner", "max"))
    if ctrl.get("treg_folds_charge_to_zero"):
        prog = 0.0
    elif loop == "TREG":
        prog = min(nominal, float(ctrl.get("charge_program_A") or 0.0))
    else:
        prog = nominal
    v_dppm, v_sup_enter, v_sup_exit, v_vindpm = _oracle_thresholds(vbat,
                                                                   sweep)
    i_vindpm_cap = max(0.0, (vbus - v_vindpm) / path) if path > 0 else 1e18
    cap = min(ilim, i_vindpm_cap)
    off_node = ctrl.get("batfet_off_comparator_node_V")
    # The public fields are rounded to 1e-6; a voltage re-derived through a
    # ~1.5 ohm source path from a rounded current can move by a few 1e-6.
    tol = 5e-6

    why = []
    if mode not in CHARGER_BRANCHES:
        why.append("unknown branch %r" % (mode,))
        return False, why
    # ---- universal ------------------------------------------------------
    if i_in > cap + tol:
        why.append("the input current exceeds the binding input-side loop")
    if i_in > 1e-9 and v_pin < v_vindpm - tol:
        why.append("the IN pin sits below the VINDPM threshold")
    if i_supp > 1e-9 and i_chg > 1e-9:
        why.append("charging and supplementing at the same time")
    if i_chg > prog + tol:
        why.append("more charge current than the program")
    if vsys > vsys_reg + tol:
        why.append("SYS above its regulation point")
    if min(i_in, i_chg, i_supp, st["system_A"]) < -1e-12:
        why.append("a negative current")
    if abs(float(ctrl.get("nominal_charge_program_A", nominal)) - nominal) \
            > tol:
        why.append("the state's nominal program is not KISET / R37 (%s)"
                   % kind)
    # ---- D-795 / R14-03: THE PHYSICAL INEQUALITY ------------------------
    if i_chg < nominal - tol and vsys > v_dppm + tol and loop != "TREG":
        why.append("a charge current below the %s program with SYS above "
                   "VBAT + VDPPM and no thermal regulation: no loop in the "
                   "part produces it" % kind)
    # ---- per branch -----------------------------------------------------
    if mode in ("SYS_REG", "CC_PATH_LIMITED", "TREG"):
        if abs(i_chg - prog) > tol:
            why.append("%s charges at the program" % mode)
        if vsys < v_dppm - tol:
            why.append("SYS is below VDPPM: the DPPM loop has control")
    if mode == "SYS_REG":
        if abs(vsys - vsys_reg) > tol:
            why.append("SYS is not at its regulation point")
        if vbus - i_in * r_src < vsys_reg - tol:
            why.append("the source cannot hold the regulation point claimed")
    elif mode == "CC_PATH_LIMITED":
        if abs(vsys - (vbus - i_in * r_src)) > tol:
            why.append("SYS is not what the source and RON_IN leave")
    elif mode == "TREG":
        if loop != "TREG":
            why.append("TREG claimed with no thermal loop")
        th = st.get("thermal")
        if not isinstance(th, dict):
            why.append("a TREG state carries no thermal evidence")
        else:
            internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                        - th.get("delivered_out_W", 0.0))
            tj = (th["ambient_C"] + th["r_sys_K_per_W"] * internal
                  + th["theta_ja_C_per_W"] * st["package_W"])
            if tj > th["treg_C"] + 0.01:
                why.append("a TREG state whose junction %.3f C is above the "
                           "TREG threshold it names" % tj)
            if i_chg < nominal - tol and tj < th["treg_C"] - 30.0:
                why.append("a TREG fold with the junction far below TREG")
    elif mode in ("ILIM", "VINDPM", "DPPM"):
        if abs(vsys - v_dppm) > tol:
            why.append("%s must hold SYS at VBAT + VDPPM" % mode)
        if vsys <= vbat:
            why.append("6.3.2: SYS is maintained ABOVE the battery")
        if i_supp > 1e-9:
            why.append("a DPPM-held branch may not supplement")
        held = (vbus - v_dppm) / r_src
        # PRECEDENCE.  The DPPM loop holds SYS at VBAT + VDPPM only because
        # the program CANNOT be delivered above it.  If it can, this branch
        # is a state no loop is in.
        p_sys = st["system_W"]
        i_reg = p_sys / vsys_reg + prog
        if vbus - i_reg * r_src >= vsys_reg:
            full_node, full_in = vsys_reg, i_reg
        else:
            b = vbus - prog * r_src
            d = b * b - 4.0 * p_sys * r_src
            full_node = 0.5 * (b + math.sqrt(d)) if d >= 0 else None
            full_in = (None if full_node is None
                       else p_sys / full_node + prog)
        if full_node is not None and full_in <= cap + 1e-9 \
                and full_node >= v_dppm - 1e-9 and prog > 0.0:
            why.append("%s claimed while the full program is deliverable "
                       "above VDPPM" % mode)
        if mode == "ILIM":
            if abs(i_in - ilim) > tol or ilim > i_vindpm_cap + 1e-9 \
                    or ilim > held + 1e-9:
                why.append("ILIM claimed where ILIM does not bind")
        elif mode == "VINDPM":
            if abs(v_pin - v_vindpm) > tol or i_vindpm_cap > ilim + 1e-9 \
                    or i_vindpm_cap > held + 1e-9:
                why.append("VINDPM claimed where VINDPM does not bind")
        else:
            if abs(i_in - held) > tol or held > cap + 1e-9:
                why.append("source-limited DPPM claimed where an input loop "
                           "binds")
    elif mode == "NO_CHARGE":
        if i_chg > 1e-9 or i_supp > 1e-9:
            why.append("NO_CHARGE must neither charge nor supplement")
        if abs(vsys - min(vsys_reg, vbus - i_in * r_src)) > tol:
            why.append("SYS is not what the regulator and the source leave")
        if prog > 1e-9 and vsys > v_dppm + tol:
            why.append("NO_CHARGE above VDPPM with the CC loop active: the "
                       "loop would pull SYS down to VDPPM")
        if vsys < v_sup_enter - 1e-9:
            why.append("SYS is below the supplement ENTRY threshold")
        if st.get("previous_mode") == "SUPPLEMENT" and vsys < v_sup_exit - 1e-9:
            why.append("the part was supplementing and SYS has not risen "
                       "back above VBAT - VBSUP2")
    elif mode == "SUPPLEMENT":
        if i_chg > 1e-9:
            why.append("SUPPLEMENT must not charge")
        if vsys > vbat + 1e-9:
            why.append("supplementing into a node ABOVE the cell")
        if abs(vsys - (vbat - i_supp * ron_bat)) > tol:
            why.append("SYS is not the cell less the BATFET drop")
        held = (vbus - vsys) / r_src
        if i_in < min(cap, held) - tol:
            why.append("the input is delivering less than it could")
        if off_node is not None:
            if off_node > v_sup_enter + 1e-9:
                if not (st.get("previous_mode") == "SUPPLEMENT"
                        and off_node <= v_sup_exit + 1e-9):
                    why.append("supplement entered with the BATFET-off node "
                               "above VBAT - VBSUP1 and nothing to latch it")
    return (not why), why


# ==========================================================================
# D-795 / R14-05.  AN INDEPENDENT CLASSIFIER, SO A MODE POPULATION IS EXACT.
#
# Round-14: "Supplement/no-charge/other required mode-history populations
# must be exact and nonempty."  A population can only be EXACT if the oracle
# knows, for every point, which branch the part must be in -- so the oracle
# builds EVERY branch's candidate state from its own closed forms, keeps the
# ones its own inequalities accept, and the canonical answer has to be the
# one that survives.  It is an elimination, not a second copy of the
# canonical control flow.
# ==========================================================================
def _candidate(mode, vsys, i_in, i_chg, i_supp, p_sys, vbat, vbus, path,
               ilim, sweep, prev, ichg_corner, off_node):
    return dict(mode=mode, vsys_V=vsys, vbat_V=vbat,
                vin_pin_V=vbus - i_in * path, input_A=i_in, charge_A=i_chg,
                supplement_A=i_supp,
                system_A=(p_sys / vsys if vsys > 0 else 0.0),
                ilim_A=ilim, path_ohm=path, vbus_source_V=vbus,
                previous_mode=prev, ichg_corner=ichg_corner,
                system_W=p_sys,
                controls=dict(sweep=sweep, charge_loop=None,
                              batfet_off_comparator_node_V=off_node))


def independent_branches(p_sys, vbat, vbus, path, ilim, sweep, prev,
                         ichg_corner):
    """Every branch whose own candidate passes the oracle's inequalities."""
    p = PRIMITIVES
    vsys_reg = p["bq.vsys_reg_V"] * 0.98
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    r_src = path + ron_in
    prog, _ = oracle_charge_program(vbat, ichg_corner)
    v_dppm, v_sup_enter, v_sup_exit, v_vindpm = _oracle_thresholds(vbat,
                                                                   sweep)
    cap = min(ilim, max(0.0, (vbus - v_vindpm) / path))
    args = (p_sys, vbat, vbus, path, ilim, sweep, prev, ichg_corner)
    cands = []

    def high_root(ichg):
        b = vbus - ichg * r_src
        d = b * b - 4.0 * p_sys * r_src
        if d < 0:
            return None
        return 0.5 * (b + math.sqrt(d))

    # full program, regulated
    cands.append(_candidate("SYS_REG", vsys_reg, p_sys / vsys_reg + prog,
                            prog, 0.0, *args, None))
    v = high_root(prog)
    if v is not None and v < vsys_reg:
        cands.append(_candidate("CC_PATH_LIMITED", v,
                                (vbus - v) / r_src, prog, 0.0, *args, None))
    # DPPM-held
    held = max(0.0, (vbus - v_dppm) / r_src)
    for mode, i_in in (("ILIM", ilim),
                       ("VINDPM", max(0.0, (vbus - v_vindpm) / path)),
                       ("DPPM", held)):
        i_chg = i_in - p_sys / v_dppm
        if -1e-12 <= i_chg:
            cands.append(_candidate(mode, v_dppm, i_in, max(0.0, i_chg), 0.0,
                                    *args, None))
    # no charge: the zero-charge node
    v0 = high_root(0.0)
    off = None
    if v0 is not None:
        v0 = min(v0, vsys_reg)
        i0 = p_sys / v0 if v0 > 0 else 0.0
        if i0 <= cap + 1e-12:
            off = v0
            cands.append(_candidate("NO_CHARGE", v0, i0, 0.0, 0.0, *args,
                                    None))
    # CC-loop necessity: an off node above VDPPM is not an equilibrium
    off_for_sup = off
    if off is not None and prog > 0.0 and off > v_dppm + 1e-12:
        off_for_sup = None
    # supplement, bisected independently
    def resid(vs):
        i_in = max(0.0, min(cap, (vbus - vs) / r_src))
        return vbat - (p_sys / vs - i_in) * ron_bat - vs
    lo, hi = 1e-3, vbat
    if resid(hi) < 0.0:
        for _ in range(90):
            mid = 0.5 * (lo + hi)
            if resid(mid) >= 0.0:
                lo = mid
            else:
                hi = mid
        vs = 0.5 * (lo + hi)
        if vs > 0.2:
            i_in = max(0.0, min(cap, (vbus - vs) / r_src))
            i_supp = max(0.0, p_sys / vs - i_in)
            cands.append(_candidate("SUPPLEMENT", vs, i_in, 0.0, i_supp,
                                    *args, off_for_sup))
    valid = []
    for c in cands:
        ok, _ = charger_branch_is_valid(c)
        if ok:
            valid.append(c["mode"])
    # PRECEDENCE BETWEEN FAMILIES.  A charging branch that is physical
    # excludes the no-charge ones: the CC loop takes the input first and the
    # BATFET only conducts when nothing else can hold SYS.
    charging = {"SYS_REG", "CC_PATH_LIMITED", "TREG", "ILIM", "VINDPM",
                "DPPM"}
    if charging & set(valid):
        valid = [v for v in valid if v in charging]
    # The hysteresis band is the one place two candidates may BOTH be
    # physical; the history decides, exactly as the part does.
    if "NO_CHARGE" in valid and "SUPPLEMENT" in valid:
        valid = ["SUPPLEMENT"] if prev == "SUPPLEMENT" else ["NO_CHARGE"]
    return sorted(set(valid))


def max_deliverable_W(vbat, vbus, path, ilim, sweep):
    """The most a constant-power load at SYS can be given at all -- input at
    its cap plus the battery through the BATFET -- scanned, so a refusal of
    'no operating point' can be checked against physics."""
    p = PRIMITIVES
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    r_src = path + ron_in
    _, _, _, v_vindpm = _oracle_thresholds(vbat, sweep)
    cap = min(ilim, max(0.0, (vbus - v_vindpm) / path))
    best = 0.0
    n = 4000
    for k in range(1, n):
        vs = 0.2 + (vbat - 0.2) * k / n
        i_in = max(0.0, min(cap, (vbus - vs) / r_src))
        best = max(best, vs * (i_in + (vbat - vs) / ron_bat))
    return best


def charger_junction_C(st, scalars, delivered_out_W=0.0):
    """The junction, from the same two thermal relations the release uses --
    written out here rather than called."""
    internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                - delivered_out_W)
    air = scalars["ambient_C"] + scalars["r_sys_K_per_W"] * internal
    return dict(
        internal_W=internal, internal_air_C=air,
        junction_with_charge_folded_back_C=(
            air + scalars["theta_ja_C_per_W"]
            * st["package_W_treg_cannot_reduce"]),
        junction_at_full_charge_current_C=(
            air + scalars["theta_ja_C_per_W"] * st["package_W"]))


# ==========================================================================
# 3.  THE SOURCE PATH.  RE-SUMMED FROM THE ITEMISATION, INDEPENDENTLY.
# ==========================================================================
def source_path_ohm(scalars, board_forward_ohm_20C, harness_lengths_mm=(60.0,
                                                                        75.0)):
    """Cell EMF -> BAT_PROTECTED_P and back, EXCLUDING the pass-pair channels.

    Written as one expression so a reader can check it against the itemisation
    by eye.  `board_forward_ohm_20C` is the measured J4 -> R75 board copper.
    """
    p = PRIMITIVES
    k = 1.0 + scalars["cu_tc_per_K"] * scalars["cu_hot_rise_K"]
    per_m = p["path.awg26_stranded_max_ohm_per_m"]
    conductors = sum(2.0 * (mm / 1000.0) * per_m for mm in harness_lengths_mm)
    harness = (conductors
               + 2.0 * p["path.microlock_contact_aged_max_ohm"]
               + 4.0 * p["path.crimp_max_ohm"]
               + 2.0 * p["path.j4_solder_joint_max_ohm"]) * k
    pack = p["path.pack_ac_impedance_max_ohm"] * p["path.pack_ac_to_dc_multiplier"]
    fuse = p["path.f1_fuse_max_ohm"] * (1.0 + p["path.f1_fuse_tolerance"])
    sheet = (scalars["rho_cu_ohm_m"] / p["path.inner_copper_thickness_m"]
             / 2.0)
    gnd = (p["path.gnd_return_squares"] * sheet
           + p["path.gnd_return_barrel_ohm"]) * k
    board = board_forward_ohm_20C * k
    return dict(
        pack_dc_ohm=pack, harness_ohm=harness, fuse_ohm=fuse,
        r75_ohm=p["path.r75_sense_max_ohm"], board_forward_ohm=board,
        gnd_return_ohm=gnd, hot_factor=k, sheet_ohm_per_square=sheet,
        total_ohm=pack + harness + fuse + p["path.r75_sense_max_ohm"]
        + board + gnd)


def pass_fet_drop_V(amps, channels, channel_ohm):
    """The conduction drop across the pass pair.  Four channels in SERIES."""
    return amps * channels * channel_ohm


def node_from_network(cell_V, amps, fixed_ohm, channels, channel_ohm):
    """KVL from the cell EMF to BAT_PROTECTED_P."""
    return cell_V - amps * (fixed_ohm + channels * channel_ohm)


# ==========================================================================
# 4.  THE PERMISSION EDGE.  THE GAUGE ERROR HAS A DIRECTION AND IT MATTERS.
# ==========================================================================
def reported_from_node(node_V, scalars, direction):
    """What the gauge may REPORT for a node at `node_V`.

    `direction` is 'high' for a pre-read (the reported value may be ABOVE the
    real node, so a permission is granted on an optimistic reading) and 'low'
    for a post-read (the reported value may be BELOW the real node, so a
    retention check is pessimistic).  Reversing them is one of the mutations
    R12-04 requires to be caught.
    """
    g = scalars["gauge_verr_V"] + scalars["gauge_lsb_V"]
    if direction == "high":
        return node_V + g
    if direction == "low":
        return node_V - g
    raise ValueError("direction must be 'high' or 'low'")


def transition_is_sound(tr, scalars):
    """One permission transition, re-checked from its own reported numbers.

    Two KINDS arrive here and they carry different evidence:

      `named`  one of the four enumerated rail transitions.  It carries the
               PRE node and the SETTLED POST node, so the retention rule and
               every hardware floor can be re-applied directly.
      `table`  one row of a permission table.  It carries the gridded floor
               and the reported ceiling of its OWN pre-state, so what can be
               re-checked is ATTAINABILITY -- a floor above what the pre-state
               can ever report authorises nothing, which is D790-A03.

    The oracle re-applies the rule rather than trusting the verdict that came
    with it.
    """
    why = []
    g = scalars["gauge_verr_V"] + scalars["gauge_lsb_V"]
    if tr.get("kind") == "table":
        if tr.get("permitted"):
            if tr.get("floor_V") is None:
                why.append("permitted with no floor")
            elif tr.get("pre_ceiling_V") is None:
                why.append("permitted with no pre-state ceiling to check "
                           "the floor against")
            elif tr["floor_V"] > tr["pre_ceiling_V"] + 1e-9:
                why.append("the floor is above what the pre-state can "
                           "report, so the row authorises nothing")
            elif tr["floor_V"] < tr["retention_floor_V"] - 1e-9:
                why.append("an enable floor below the retention floor would "
                           "authorise a state the next recheck sheds")
            # ---- D-794 / R13-04 + FABLE DELTA: RETENTION, NOT JUST REACH --
            #
            # "Every permitted table row must independently prove settled
            # post-load retention, not attainability only."  Everything above
            # this line is about whether the FLOOR can be reached.  A row can
            # pass all of it and still authorise a state that sheds the
            # instant the load arrives -- which is the R13-01 defect written
            # as a table row instead of as a call sequence.
            #
            # So the row must carry its SETTLED post-load node, and that node
            # -- read DOWN by the gauge error, as the firmware would read it
            # -- must clear the retention floor.  Both timescales: the
            # sustained state, and the same state with the worst coincident
            # burst, because the post-enable recheck can land inside one.
            elif tr.get("post_node_V") is None:
                why.append("a permitted row with no settled post-load node: "
                           "attainability was checked and retention was not")
            else:
                for label, node in (("settled", tr["post_node_V"]),
                                    ("settled-with-burst",
                                     tr.get("post_node_with_worst_burst_V"))):
                    if node is None:
                        if label != "settled":
                            why.append("a permitted row with no %s node"
                                       % label)
                        continue
                    if node - g < tr["retention_floor_V"] - 1e-9:
                        why.append("the %s post-load node reports %.6f V, "
                                   "below the %.4f V retention floor: this "
                                   "row authorises a state the next recheck "
                                   "sheds" % (label, node - g,
                                              tr["retention_floor_V"]))
                    if node < scalars["buvlo_bound_V"] - 1e-9:
                        why.append("the %s post-load node is under VBUVLO"
                                   % label)
        else:
            if tr.get("floor_V") is not None:
                why.append("a refused row still carries a floor")
        return (not why), why
    if tr.get("post_node_V") is None:
        if tr.get("permitted"):
            why.append("permitted with no attainable post state")
        return (not why), why
    post_reported_low = tr["post_node_V"] - g
    if tr.get("permitted"):
        if post_reported_low < tr["retention_floor_V"] - 1e-9:
            why.append("a granted enable settles below the retention floor "
                       "it is judged against")
        if tr["post_node_V"] < scalars["buvlo_bound_V"] - 1e-9:
            why.append("the settled node is under VBUVLO")
        if tr.get("post_vsys_V") is not None and \
                tr["post_vsys_V"] < scalars["u12_vin_floor_V"] - 1e-9:
            why.append("the settled SYS is under U12's input floor")
        if tr.get("floor_V") is not None and tr.get("pre_ceiling_V") is not None \
                and tr["floor_V"] > tr["pre_ceiling_V"] + 1e-9:
            why.append("the floor is above what the pre-state can report")
    return (not why), why


# ==========================================================================
# 5.  COMPLETENESS.  A HARD VERDICT TERM, NOT METADATA.
# ==========================================================================
REQUIRED_TRANSITION_KEYS = ("first_rail_3v3", "first_rail_5v",
                            "second_rail_5v", "second_rail_3v3")
REQUIRED_RAIL_ORDERS = ("3v3_first", "5v_first")
# D-794 / R13-02 + R13-04.  EVERY branch the device has must be exercised by
# the derivation, not a subset of them.  A branch that is never solved is a
# branch whose inequalities were never checked.
REQUIRED_CHARGER_BRANCHES = ("SYS_REG", "CC_PATH_LIMITED", "TREG", "ILIM",
                             "VINDPM", "DPPM", "NO_CHARGE", "SUPPLEMENT")
# D-793 / R12-04: at least one post-state must be REJECTED BY NAME, so the
# inclusion invariant cannot be true merely because nothing was tried.
REQUIRED_SEEDED_REJECTION = "seeded_canary/d790_declared"

# ==========================================================================
# D-794 / R13-04.  THE EXPECTED DOMAIN IS DECLARED HERE, NOT COLLECTED FROM
# WHAT ARRIVED.
#
# ROUND-13, IN ITS OWN WORDS: "Astra deleted every F14 table row, deleted
# every F14 network state, duplicated a named key, and altered the F6-only
# declared pair while the overall release remained green in important cases.
# F14 must independently construct the EXPECTED physical/state domain instead
# of accepting whatever collections the canonical model supplies.  Require
# exact unique key multisets, exact row/mode/refusal counts, all supported
# source regimes, both transition orders, all required charger branches and
# nonempty full expected network domain.  ... Duplicate transition keys must
# fail.  Missing rows/states must fail."
#
# ALL FOUR REPRODUCE ON D-793 FOR ONE REASON.  `completeness()` built a SET
# from whatever it was handed and then asked whether the required names were
# IN it.  A set answers "is this present"; it cannot answer "is this all of
# it", and it cannot answer "was this said twice".  Delete thirty-one of the
# thirty-two table rows and the remaining one still satisfies every `in`.
# Delete every network row and there is nothing left to be absent FROM.
#
# WHAT REPLACES IT.  The product's own domain is written out below -- three
# optional modes, two edges, two rail counts, seven cell-to-load states, five
# accessory configurations, two cell corners -- and the oracle CONSTRUCTS the
# key multiset it expects from those.  What arrived must equal it exactly:
# same keys, same count, each exactly once.  These constants are the product
# definition, not a copy of the canonical model's data structures; when the
# product genuinely gains a mode or a rail configuration, this list is where
# the change is declared and the release fails until it is.
# ==========================================================================
EXPECTED_OPTIONAL_MODES = 3          # Wi-Fi/BLE TX, audio, sub-GHz TX
EXPECTED_PERMISSION_EDGES = ("rail_edge_table", "mode_edge_table")
EXPECTED_RAIL_COUNTS = (1, 2)
EXPECTED_CELL_NET_STATES = (
    "display_only", "display_audio", "display_subghz", "display_subghz_audio",
    "display_wifi", "display_wifi_subghz", "d790_declared")
# The one state that is RETIRED: it carries no permission transitions of its
# own and is the seeded canary instead.
EXPECTED_RETIRED_CELL_NET_STATE = "d790_declared"
EXPECTED_ACCESSORY_CONFIGURATIONS = (
    "acc_3v3_only", "acc_5v_only", "both_rails",
    "both_rails_at_the_declared_pair", "no_accessory")
EXPECTED_CELL_CORNERS = ("at_a_full_cell", "at_the_lowest_supported_cell")


def expected_table_keys():
    """The permission-table key multiset, constructed rather than collected."""
    out = []
    for edge in EXPECTED_PERMISSION_EDGES:
        for bits in range(1 << EXPECTED_OPTIONAL_MODES):
            for rails in EXPECTED_RAIL_COUNTS:
                out.append("%s/bits%d/rails%d" % (edge, bits, rails))
    return out


def expected_named_transitions():
    """The (transition, state) multiset every live cell-to-load state owes."""
    out = []
    for state in EXPECTED_CELL_NET_STATES:
        if state == EXPECTED_RETIRED_CELL_NET_STATE:
            continue
        for k in REQUIRED_TRANSITION_KEYS:
            out.append((k, state))
    return out


# ==========================================================================
# D-795 / R14-05.  THE CHARGER, REGIME AND NETWORK DOMAINS, DECLARED HERE.
#
# ROUND-14: "F14 still passes when required network corners or charger
# histories are removed while superficial mode/branch names remain.
# Independently define the FULL semantic key domain for network states,
# charger source/BAT/threshold/history points, permission transitions and
# refusals.  Require exact key MULTISETS, not minimum counts or branch-name
# presence.  Every expected point must either be solved or carry an
# independently checkable physical refusal."
#
# D-794 checked that every branch NAME appeared somewhere.  One row per mode
# satisfied it; so did deleting every SUPPLEMENT-history row.  The domain is
# now a product of declared axes, the canonical side must deliver EXACTLY that
# multiset, and each point is either a solved state whose branch the oracle's
# own elimination agrees with, or a refusal the oracle can re-check.
# ==========================================================================
EXPECTED_CHARGER_CELLS_V = (2.85, 3.2, 3.52, 3.7, 4.2, 4.221)
EXPECTED_CHARGER_POWERS_W = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3,
                             3.6, 4.0, 4.5, 5.0, 5.65, 7.0,
                             # beyond what the input plus the BATFET can
                             # deliver at the low cells: the domain CONTAINS
                             # refusals by construction, so dropping them is
                             # a missing key rather than an invisible edit
                             15.0, 30.0)
EXPECTED_ILIM_CORNERS = ("max", "min")
EXPECTED_SOURCE_CLASSES = ("rpi15w_high", "rpi15w_low",
                           "generic_typec_24awg_2m", "unqualified_28awg_2m")
EXPECTED_QUALIFIED_SOURCE_CLASSES = ("rpi15w_high", "rpi15w_low")
EXPECTED_HISTORIES = (None, "NO_CHARGE", "SUPPLEMENT")
EXPECTED_ICHG_CORNERS = ("max", "min")
# (mode, previous mode) populations that MUST be non-empty -- and the one
# behaviour the hysteresis exists for: a point whose branch the history
# DECIDES.
REQUIRED_MODE_HISTORY_POPULATIONS = (
    ("SYS_REG", None), ("CC_PATH_LIMITED", None), ("ILIM", None),
    ("VINDPM", None), ("DPPM", None), ("SUPPLEMENT", None),
    ("SUPPLEMENT", "SUPPLEMENT"), ("NO_CHARGE", None),
    ("NO_CHARGE", "NO_CHARGE"), ("SUPPLEMENT", "NO_CHARGE"))
EXPECTED_REGIME_VBAT_GRID_V = (2.85, 3.0, 3.2, 3.4, 3.5, 3.52, 3.6, 3.8, 4.0,
                               4.1, 4.2, 4.221)
EXPECTED_REGIME_SWEEP_FRACTIONS = (-1.0, -0.5, 0.0, 0.5, 1.0)
EXPECTED_REGIME_HISTORIES = (None, "SUPPLEMENT")
EXPECTED_REGIME_AMBIENTS_C = (0.0, 25.0, 40.0)
REGIME_GUARDBAND = 0.05
REGIME_GRID_W = 0.05


def charger_domain_key(vbat, p_sys, ilim, source, hist, ichg):
    return "vbat%.3f/p%.3f/ilim_%s/%s/%s/ichg_%s" % (
        vbat, p_sys, ilim, source, hist or "none", ichg)


def expected_charger_keys():
    out = []
    for v in EXPECTED_CHARGER_CELLS_V:
        for w in EXPECTED_CHARGER_POWERS_W:
            for il in EXPECTED_ILIM_CORNERS:
                for c in EXPECTED_SOURCE_CLASSES:
                    for h in EXPECTED_HISTORIES:
                        for ic in EXPECTED_ICHG_CORNERS:
                            out.append(charger_domain_key(v, w, il, c, h, ic))
    return out


def expected_regime_keys():
    sw0 = PRIMITIVES["bq.branch_threshold_sweep"]
    out = []
    for c in EXPECTED_SOURCE_CLASSES:
        for v in EXPECTED_REGIME_VBAT_GRID_V:
            for il in EXPECTED_ILIM_CORNERS:
                for f in EXPECTED_REGIME_SWEEP_FRACTIONS:
                    for h in EXPECTED_REGIME_HISTORIES:
                        for a in EXPECTED_REGIME_AMBIENTS_C:
                            out.append("%s/vbat%.3f/ilim_%s/sweep%+.3f/%s/"
                                       "amb%.0f" % (c, v, il, round(f * sw0, 6),
                                                    h or "none", a))
    return out


def _floor_to_grid(x):
    return (math.floor(x * (1.0 - REGIME_GUARDBAND) / REGIME_GRID_W + 1e-12)
            * REGIME_GRID_W)


def charger_domain_problems(charger_states, charger_refusals):
    """Exact keys; every solved point agrees with the independent
    classifier; every refusal is physically re-checked."""
    why = []
    got = ([st.get("domain_key") for st in charger_states]
           + [r.get("domain_key") for r in charger_refusals])
    why += _multiset_problems("charger domain", got, expected_charger_keys())
    pops = {}
    by_key = {}
    disagreements = 0
    for st in charger_states:
        k = st.get("domain_key")
        by_key[k] = st
        pops[(st["mode"], st.get("previous_mode"))] = pops.get(
            (st["mode"], st.get("previous_mode")), 0) + 1
        want = independent_branches(
            st["system_W"], st["vbat_V"], st["vbus_source_V"], st["path_ohm"],
            st["ilim_A"], float((st.get("controls") or {}).get("sweep") or 0.0),
            st.get("previous_mode"), st.get("ichg_corner", "max"))
        if want != [st["mode"]]:
            disagreements += 1
            if disagreements <= 8:
                why.append("charger point %s: the canonical branch is %r but "
                           "the independent elimination leaves %r"
                           % (k, st["mode"], want))
    if disagreements > 8:
        why.append("... and %d more branch disagreements" % (disagreements - 8))
    if not charger_refusals:
        why.append("the charger refusal set is EMPTY, but the declared domain "
                   "contains powers no source-plus-BATFET can deliver")
    for r in charger_refusals:
        pmax = max_deliverable_W(r["vbat_V"], r["vbus_V"], r["path_ohm"],
                                 r["ilim_A"], r.get("sweep", 0.0))
        if r["system_W"] <= pmax * (1.0 + 1e-6):
            why.append("charger point %s is REFUSED as having no operating "
                       "point, but the input plus the BATFET can deliver "
                       "%.4f W against the %.4f W asked"
                       % (r.get("domain_key"), pmax, r["system_W"]))
    for pair in REQUIRED_MODE_HISTORY_POPULATIONS:
        if not pops.get(pair):
            why.append("the (branch, history) population %r is EMPTY" %
                       (pair,))
    # the hysteresis is DEMONSTRATED, not assumed
    latched = 0
    for st in charger_states:
        if st.get("previous_mode") != "SUPPLEMENT" or st["mode"] != "SUPPLEMENT":
            continue
        k0 = st["domain_key"].replace("/SUPPLEMENT/", "/none/")
        other = by_key.get(k0)
        if other is not None and other["mode"] == "NO_CHARGE":
            latched += 1
    if not latched:
        why.append("no point in the domain shows the VBSUP1/VBSUP2 "
                   "hysteresis deciding the branch: the history axis is not "
                   "exercised")
    return why, dict(
        expected_points=len(expected_charger_keys()),
        solved=len(charger_states), refused=len(charger_refusals),
        populations={"%s/%s" % (m, h or "none"): n
                     for (m, h), n in sorted(pops.items(),
                                             key=lambda x: repr(x))},
        points_where_history_decides=latched,
        classifier_disagreements=disagreements)


def regime_problems(rows, published, scalars):
    """Every regime row exists exactly once, its evidence brackets its own
    ceiling, and every PUBLISHED figure is the oracle's own minimum."""
    why = []
    got = [r.get("key") for r in rows]
    why += _multiset_problems("charge regime", got, expected_regime_keys())
    tj_max = scalars["tj_operating_max_C"]
    bad = 0
    for r in rows:
        ev = r.get("_evidence")
        if not isinstance(ev, dict):
            why.append("regime row %s carries no evidence" % r.get("key"))
            bad += 1
            continue
        for label in ("no_discharge_at", "junction_at"):
            st = ev.get(label)
            if st is None:
                if (label == "no_discharge_at" and r["no_discharge_W"] > 0) or \
                        (label == "junction_at" and r["junction_W"] > 0):
                    why.append("regime row %s: no %s state" % (r["key"], label))
                continue
            ok, w = charger_branch_is_valid(st)
            dok, dw = raw_summary_divergence(st)
            if not ok or not dok:
                bad += 1
                if bad <= 6:
                    why.append("regime row %s: the %s state is not physical: "
                               "%s" % (r["key"], label, (w + dw)[:2]))
        nd_at, nd_above = ev.get("no_discharge_at"), ev.get("no_discharge_above")
        if r["no_discharge_W"] < 7.99:
            if nd_at is not None and nd_at["mode"] == "SUPPLEMENT":
                why.append("regime row %s: the no-discharge ceiling is itself "
                           "in SUPPLEMENT" % r["key"])
            if nd_above is not None and nd_above["mode"] != "SUPPLEMENT":
                why.append("regime row %s: just ABOVE the no-discharge ceiling "
                           "the part is still not supplementing -- the "
                           "ceiling is not the boundary" % r["key"])
        th = ev.get("thermal") or {}

        def tj(st):
            internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                        - th.get("delivered_out_W", 0.0))
            return (th["ambient_C"] + th["r_sys_K_per_W"] * internal
                    + th["theta_ja_C_per_W"] * st["package_W"])
        if th.get("r_sys_K_per_W") != scalars["r_sys_K_per_W"] or \
                th.get("theta_ja_C_per_W") != scalars["theta_ja_C_per_W"]:
            why.append("regime row %s is solved on a thermal model the "
                       "oracle was not given" % r["key"])
        j_at, j_above = ev.get("junction_at"), ev.get("junction_above")
        if r["junction_W"] < 7.99:
            if j_at is not None and tj(j_at) > tj_max + 1e-6:
                why.append("regime row %s: the junction ceiling is over %.1f C"
                           % (r["key"], tj_max))
            if j_above is not None and tj(j_above) <= tj_max:
                why.append("regime row %s: just ABOVE the junction ceiling the "
                           "junction is still inside the maximum" % r["key"])
        if abs(r["ceiling_W"] - min(r["no_discharge_W"], r["junction_W"])) \
                > 1e-6:
            why.append("regime row %s: the ceiling is not the lower of its two "
                       "limits" % r["key"])
    # ---- the PUBLISHED figures, recomputed from the rows ------------------
    q = [r for r in rows if r.get("source_class")
         in EXPECTED_QUALIFIED_SOURCE_CLASSES]
    if q and published:
        u_nd = min(r["no_discharge_W"] for r in q)
        u_tj = min(r["junction_W"] for r in q)
        for key, want in (("universal_no_discharge_published_W",
                           _floor_to_grid(u_nd)),
                          ("junction_safe_published_W", _floor_to_grid(u_tj))):
            if abs(float(published.get(key, -1.0)) - want) > 1e-6:
                why.append("the published %s is %r; the oracle's minimum over "
                           "the qualified domain floors to %.6f"
                           % (key, published.get(key), want))
        env = {(e["source_class"], e["vbat_V"]): e
               for e in published.get("envelope", [])}
        for c in EXPECTED_SOURCE_CLASSES:
            for v in EXPECTED_REGIME_VBAT_GRID_V:
                sel = [r for r in rows if r["source_class"] == c
                       and abs(r["vbat_V"] - v) < 1e-9]
                e = env.get((c, v))
                if not sel or e is None:
                    why.append("the published envelope has no row for %s at "
                               "%.3f V" % (c, v))
                    continue
                for pub, field in (("no_discharge_published_W",
                                    "no_discharge_W"),
                                   ("junction_published_W", "junction_W")):
                    want = _floor_to_grid(min(r[field] for r in sel))
                    if abs(e[pub] - want) > 1e-6:
                        why.append("envelope %s/%.3f V %s is %r, the oracle "
                                   "floors to %.6f" % (c, v, pub, e[pub],
                                                       want))
    elif not published:
        why.append("no published regime figures were handed to the oracle")
    return why, dict(expected_rows=len(expected_regime_keys()),
                     rows_seen=len(rows), rows_with_bad_evidence=bad)


def _multiset_problems(what, got, want):
    """Exact multiset equality, reported as missing / extra / duplicated."""
    why = []
    gc, wc = {}, {}
    for k in got:
        gc[k] = gc.get(k, 0) + 1
    for k in want:
        wc[k] = wc.get(k, 0) + 1
    for k in sorted(wc, key=repr):
        if k not in gc:
            why.append("%s: %r is MISSING from the derivation" % (what, k))
        elif gc[k] > wc[k]:
            why.append("%s: %r appears %d times where %d is expected -- a "
                       "duplicated key hides whatever it shadows"
                       % (what, k, gc[k], wc[k]))
        elif gc[k] < wc[k]:
            why.append("%s: %r appears %d times where %d is expected"
                       % (what, k, gc[k], wc[k]))
    for k in sorted(gc, key=repr):
        if k not in wc:
            why.append("%s: %r is not in the expected domain" % (what, k))
    return why


def completeness(transitions, charger_states, rejected_post_states,
                 residual_worst_W, residual_worst_V, network_states=(),
                 charger_refusals=None, regime_rows=None,
                 regime_published=None, thermal_states=None, scalars=None):
    """R12-04's mandatory invariants, ANDed into the verdict."""
    keys = {t.get("transition") for t in transitions}
    orders = set()
    for t in transitions:
        if t.get("transition") in ("first_rail_3v3", "second_rail_5v"):
            orders.add("3v3_first")
        if t.get("transition") in ("first_rail_5v", "second_rail_3v3"):
            orders.add("5v_first")
    branches = {s.get("mode") for s in charger_states}
    problems = []
    for k in REQUIRED_TRANSITION_KEYS:
        if k not in keys:
            problems.append("transition %r is missing from the derivation" % k)
    for o in REQUIRED_RAIL_ORDERS:
        if o not in orders:
            problems.append("rail order %r is not enumerated" % o)
    thermal_branches = {s.get("mode") for s in (thermal_states or [])}
    for b in REQUIRED_CHARGER_BRANCHES:
        if b not in branches and b not in thermal_branches:
            problems.append("charger branch %r is never exercised" % b)
    # ---- D-795 / R14-05: the exact charger and regime domains --------------
    if charger_refusals is None:
        problems.append("the charger domain was handed with no refusal set: "
                        "an unsolved point could simply have been dropped")
        charger_extra = {}
    else:
        cp, charger_extra = charger_domain_problems(charger_states,
                                                    charger_refusals)
        problems += cp
    if regime_rows is None:
        problems.append("the charge-regime rows were not handed to the "
                        "oracle: the published regime claims are unbound")
        regime_extra = {}
    else:
        rp, regime_extra = regime_problems(regime_rows, regime_published,
                                           scalars or {})
        problems += rp
    if not thermal_states:
        problems.append("no thermally-closed charger state was handed to the "
                        "oracle, so the TREG branch was never checked")
    else:
        if "TREG" not in thermal_branches:
            problems.append("no thermally-closed state exercises TREG")
        for st in thermal_states:
            ok, w = charger_branch_is_valid(st)
            if not ok:
                problems.append("thermal state %s is not physical: %s"
                                % (st.get("domain_key"), w[:2]))
                break
    # ---- D-794 / R13-04.  EXACT MULTISETS OVER THE CONSTRUCTED DOMAIN -----
    got_table = [t.get("transition") for t in transitions
                 if t.get("kind") == "table"
                 and t.get("transition") != REQUIRED_SEEDED_REJECTION]
    got_named = [(t.get("transition"), t.get("state")) for t in transitions
                 if t.get("kind") == "named"]
    want_table = expected_table_keys()
    want_named = expected_named_transitions()
    problems += _multiset_problems("permission table", got_table, want_table)
    problems += _multiset_problems("named transition", got_named, want_named)

    # ---- the cell-to-load network domain ---------------------------------
    #
    # A refused state legitimately solves at FEWER corners than a permitted
    # one -- there is no operating point to report -- so the network domain
    # cannot be an exact multiset the way the tables can.  What it CAN be is
    # bounded on both sides: no key outside the constructed cross product, no
    # key twice, and every live state represented.  Astra's "delete every
    # network state" and a duplicated key both fail that, and so does
    # silently dropping one state's rows.
    # D-795 / R14-05: the network domain is an EXACT multiset now.  D-794
    # could only bound it on both sides because a refused state solves at
    # fewer corners; every unsolved corner is now delivered as a REFUSAL row
    # carrying the named physical limits it fails, so "delete selected
    # network rows" is a missing key rather than a smaller set.
    want_net = []
    for state in EXPECTED_CELL_NET_STATES:
        for cfg in EXPECTED_ACCESSORY_CONFIGURATIONS:
            for corner in EXPECTED_CELL_CORNERS:
                want_net.append("%s/%s/%s" % (state, cfg, corner))
    got_net = [n.get("key") for n in network_states]
    if not [n for n in network_states if not n.get("refused")]:
        problems.append("the cell-to-load network domain has no SOLVED row: "
                        "nothing was re-derived by KVL at all")
    problems += _multiset_problems("network", got_net, want_net)
    for n in network_states:
        if not n.get("refused"):
            continue
        lim = n.get("physical_limits")
        if not isinstance(lim, dict) or not lim:
            problems.append("network refusal %r carries no physical limits"
                            % (n.get("key"),))
        elif all(bool(x) for x in lim.values()):
            problems.append("network refusal %r passes every limit it names, "
                            "so its refusal is not physical" % (n.get("key"),))
    states_present = {(k or "").split("/")[0] for k in got_net}
    for state in EXPECTED_CELL_NET_STATES:
        if state == EXPECTED_RETIRED_CELL_NET_STATE:
            continue
        solved = [n for n in network_states if not n.get("refused")
                  and (n.get("key") or "").startswith(state + "/")]
        if not solved:
            problems.append("cell-to-load state %r contributes no SOLVED "
                            "network row: its KVL was never independently "
                            "checked" % (state,))

    # ---- the refusal count is a NUMBER, not a Boolean --------------------
    #
    # "exact row/mode/refusal counts".  Every table row that is not permitted
    # must be present in the rejection set, and nothing else may be -- apart
    # from the seeded canary, which is a real physical state rather than a
    # row.  D-793 asked only whether the set was non-empty.
    refused_rows = sorted(t.get("transition") for t in transitions
                          if t.get("kind") == "table" and not t.get("permitted")
                          and t.get("transition") != REQUIRED_SEEDED_REJECTION)
    rejected_keys = sorted(r.get("transition") for r in rejected_post_states
                           if r.get("transition") != REQUIRED_SEEDED_REJECTION)
    problems += _multiset_problems("rejection set", rejected_keys,
                                   refused_rows)
    if not rejected_post_states:
        problems.append("the rejection set is EMPTY: a derivation that "
                        "rejects nothing cannot be shown to reject anything, "
                        "so inclusion passes vacuously")
    canaries = [r for r in rejected_post_states
                if r.get("transition") == REQUIRED_SEEDED_REJECTION]
    if not canaries:
        problems.append("the seeded canary %r is not in the rejection set: "
                        "either it started passing, or the seed was dropped, "
                        "and either way the inclusion invariant is no longer "
                        "protected against vacuity"
                        % (REQUIRED_SEEDED_REJECTION,))
    else:
        # D-794 / R13-04: "A seeded canary must be a real rejected PHYSICAL
        # state, not merely an expected string/name."  A name in a list is a
        # bookkeeping fact.  What makes this canary load-bearing is that the
        # state it names has NO OPERATING POINT at either cell corner, and
        # that is checked here from the physics the row carries.
        c = canaries[0]
        if c.get("permitted"):
            problems.append("the seeded canary is marked permitted")
        limits = c.get("physical_limits")
        points = c.get("physical_operating_points")
        if not isinstance(limits, dict) or not limits:
            problems.append("the seeded canary carries no physical limits: "
                            "it is a NAME, and a name cannot be refused")
        else:
            for corner, named in sorted(limits.items()):
                if not isinstance(named, dict) or not named:
                    problems.append("the seeded canary names no limit at %r"
                                    % (corner,))
                elif all(bool(x) for x in named.values()):
                    problems.append("the seeded canary passes every named "
                                    "limit at %r, so its refusal is not "
                                    "physical" % (corner,))
        if isinstance(points, dict):
            for corner, raw in sorted(points.items()):
                if raw is not None:
                    problems.append("the seeded canary has an operating "
                                    "point at %r: the state it is supposed "
                                    "to demonstrate is now solvable"
                                    % (corner,))
        else:
            problems.append("the seeded canary carries no operating-point "
                            "evidence at all")
    if residual_worst_W > TOL_W:
        problems.append("the worst independent power residual %.3e W is over "
                        "tolerance" % residual_worst_W)
    if residual_worst_V > TOL_V:
        problems.append("the worst independent voltage residual %.3e V is "
                        "over tolerance" % residual_worst_V)
    return (not problems), dict(
        transition_keys=sorted(k for k in keys if k),
        rail_orders=sorted(orders),
        charger_branches=sorted(b for b in branches if b),
        rejected_post_states=len(rejected_post_states),
        # ---- D-794 / R13-04: the constructed domain, reported as counts ---
        expected_permission_table_rows=len(want_table),
        permission_table_rows_seen=len(got_table),
        expected_named_transitions=len(want_named),
        named_transitions_seen=len(got_named),
        expected_network_domain_size=len(want_net),
        network_rows_seen=len(got_net),
        network_states_represented=sorted(x for x in states_present if x),
        refused_permission_rows=len(refused_rows),
        seeded_rejection=REQUIRED_SEEDED_REJECTION,
        seeded_rejection_present=bool(any(
            r.get("transition") == REQUIRED_SEEDED_REJECTION
            for r in rejected_post_states)),
        worst_power_residual_W=residual_worst_W,
        worst_voltage_residual_V=residual_worst_V,
        charger_domain=charger_extra, regime_domain=regime_extra,
        thermal_states_checked=len(thermal_states or []),
        problems=problems,
        method="R12-04 convergence requirement 3: transition/state "
               "completeness is a HARD VERDICT REQUIREMENT, never "
               "informational metadata.  D-792 reported it and passed "
               "anyway.")


# ==========================================================================
# 6.  THE AUDIT.  Everything above, over the data the release produced.
# ==========================================================================
def audit(registry, scalars, charger_states, transitions,
          rejected_post_states, board_forward_ohm_20C,
          canonical_source_path_ohm, network_states=(),
          without_energy_oracle=False, charger_refusals=None,
          regime_rows=None, regime_published=None, thermal_states=None):
    """`without_energy_oracle` ABLATES THE ENERGY ACCOUNTING ENTIRELY.

    It removes both halves of it: the TERMINAL-vs-INTERNAL identity (what
    crosses the terminals equals what the elements dissipate) and the
    INDEPENDENTLY-RECOMPUTED package heat against the figure the canonical
    model reports.  Those are one idea seen from two directions, and D-792 had
    neither: its `energy_balance` compared `p_in + p_from_cell - p_sys -
    p_stored` with `p_diss`, which was DEFINED as that expression, so the
    check was `0 == 0` and a halved package heat passed the entire suite.

    It exists for exactly one purpose: R12-04 requires a mutation named
    "delete the energy oracle" which must be CAUGHT, and the only honest way
    to show a term is load-bearing is to remove it and watch something get
    through.  Nothing in the release path ever passes it as True.
    """
    prim_ok, prim = primitives_agree(registry, scalars)

    charger_rows, worst_W, worst_V = [], 0.0, 0.0
    for st in charger_states:
        res = charger_residuals(st, scalars)
        branch_ok, branch_why = charger_branch_is_valid(st)
        dup_ok, dup_why = raw_summary_divergence(st)
        worst_W = max(worst_W, abs(res["constant_power_W"]),
                      0.0 if without_energy_oracle else max(
                          abs(res["package_W"]), abs(res["package_treg_W"]),
                          abs(res["terminal_vs_internal_W"])))
        worst_V = max(worst_V, abs(res["vin_pin_V"]))
        charger_rows.append(dict(
            mode=st["mode"], source_key=st.get("source_key"),
            system_W=st["system_W"], residuals={
                k: v for k, v in res.items() if k != "independently_computed"},
            independently_computed=res["independently_computed"],
            branch_valid=branch_ok, branch_problems=branch_why,
            raw_agrees_with_summary=dup_ok,
            raw_summary_problems=dup_why,
            ok=bool(branch_ok and dup_ok
                    and (without_energy_oracle
                         or (abs(res["terminal_vs_internal_W"]) <= TOL_W
                             and abs(res["package_W"]) <= TOL_W
                             and abs(res["package_treg_W"]) <= TOL_W))
                    and abs(res["constant_power_W"]) <= TOL_W
                    and abs(res["vin_pin_V"]) <= TOL_V
                    and abs(res["kcl_A"]) <= TOL_A)))

    # The source path, re-summed.  The canonical figure is ROUNDED to six
    # decimals by the model that publishes it, so the tolerance here is half a
    # micro-ohm rather than machine epsilon; anything larger is a real
    # disagreement about the itemisation.
    path = source_path_ohm(scalars, board_forward_ohm_20C)
    path_residual = path["total_ohm"] - canonical_source_path_ohm
    path_ok = abs(path_residual) <= TOL_PATH_OHM

    # The cell-to-load network states, re-checked by KVL alone.
    net_rows = []
    for ns in network_states:
        if ns.get("refused"):
            continue
        node = node_from_network(ns["cell_V"], ns["amps"], ns["fixed_ohm"],
                                 ns["channels"], ns["channel_ohm"])
        drop = pass_fet_drop_V(ns["amps"], ns["channels"], ns["channel_ohm"])
        r = node - ns["node_V"]
        worst_V = max(worst_V, abs(r))
        net_rows.append(dict(key=ns.get("key"), residual_V=r,
                             independently_computed_node_V=node,
                             pass_pair_drop_V=drop,
                             ok=bool(abs(r) <= TOL_V)))

    tr_rows = []
    for tr in transitions:
        ok, why = transition_is_sound(tr, scalars)
        tr_rows.append(dict(transition=tr.get("transition"),
                            state=tr.get("state"), ok=ok, problems=why))

    comp_ok, comp = completeness(transitions, charger_states,
                                 rejected_post_states, worst_W, worst_V,
                                 network_states=network_states,
                                 charger_refusals=charger_refusals,
                                 regime_rows=regime_rows,
                                 regime_published=regime_published,
                                 thermal_states=thermal_states,
                                 scalars=scalars)
    ok = bool(prim_ok and comp_ok
              and all(r["ok"] for r in charger_rows)
              and all(r["ok"] for r in net_rows)
              and all(r["ok"] for r in tr_rows)
              and path_ok)
    return ok, dict(
        primitives=prim, primitives_ok=prim_ok,
        charger=charger_rows,
        charger_states_checked=len(charger_rows),
        source_path=dict(independently_summed=path,
                         canonical_ohm=canonical_source_path_ohm,
                         residual_ohm=path_residual,
                         tolerance_ohm=TOL_PATH_OHM,
                         ok=path_ok),
        network=net_rows,
        transitions=tr_rows,
        completeness=comp, completeness_ok=comp_ok,
        tolerance=dict(power_W=TOL_W, voltage_V=TOL_V, current_A=TOL_A,
                       source_path_ohm=TOL_PATH_OHM),
        energy_oracle_ablated=bool(without_energy_oracle),
        ok=ok,
        what="a SECOND, structurally independent implementation of the "
             "identities the release rests on.  It imports nothing from the "
             "canonical model and solves nothing; it re-derives what a solved "
             "state claims, from primitives, and refuses when the two "
             "disagree.")
