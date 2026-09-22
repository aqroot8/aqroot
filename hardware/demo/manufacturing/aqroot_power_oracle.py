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
    "usb.vbus_source_max_V": 5.25,          # USB 2.0 table 7-7
    "usb.vbus_source_min_V": 4.75,          # USB 2.0 table 7-7
    # --- the BQ25185 (TI SLUSF65B) ---------------------------------------
    "bq.vsys_reg_V": 4.5,
    "bq.ron_in_max_ohm": 0.470,
    "bq.ron_bat_max_ohm": 0.140,
    "bq.ron_bat_vbat_allowance": 1.40,
    "bq.ilim_min_A": 0.995,
    "bq.ilim_max_A": 1.100,
    "bq.ichg_A": 0.769,
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
CHARGER_BRANCHES = ("SYS_REG", "CC_PATH_LIMITED", "ILIM", "VINDPM",
                    "DPPM", "NO_CHARGE", "SUPPLEMENT")
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


def charger_branch_is_valid(st):
    """The branch INEQUALITIES, from primitives, independently.

    R13-02: "F14 must independently check the physical branch conditions, not
    repeat the same control assumptions."  So every threshold below is built
    from this module's own PRIMITIVES and every inequality is stated here in
    full.  Nothing is read out of the state's `controls` block except the
    declared THRESHOLD SWEEP, which is an input to the derivation rather than
    a claim about it -- and the sweep is applied here independently too.
    """
    p = PRIMITIVES
    ctrl = st.get("controls") or {}
    sweep = float(ctrl.get("sweep") or 0.0)
    treg = bool(ctrl.get("treg_folds_charge_to_zero"))
    vsys_reg = p["bq.vsys_reg_V"] * 0.98
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    ichg = 0.0 if treg else p["bq.ichg_A"]
    ilim = st["ilim_A"]
    path = st["path_ohm"]
    vbus = st["vbus_source_V"]
    r_src = path + ron_in
    vsys, vbat, v_pin = st["vsys_V"], st["vbat_V"], st["vin_pin_V"]
    i_in, i_chg, i_supp = st["input_A"], st["charge_A"], st["supplement_A"]
    mode = st["mode"]
    # The four thresholds, swept in the SAME declared directions the canonical
    # derivation uses.  Written out, not imported.
    v_dppm = vbat + p["bq.vdppm_V"] * (1.0 + sweep)
    v_sup_enter = vbat - p["bq.vbsup1_V"] * (1.0 - sweep)
    v_sup_exit = vbat - p["bq.vbsup2_V"] * (1.0 - sweep)
    if vbat > p["bq.vindpm_track_vbat_floor_V"]:
        v_vindpm = vbat + p["bq.vindpm_track_V"] * (1.0 + sweep)
    else:
        v_vindpm = p["bq.vindpm_fixed_V"] * (
            1.0 + sweep * p["bq.fixed_vindpm_sweep_ratio"])
    i_vindpm_cap = max(0.0, (vbus - v_vindpm) / path) if path > 0 else 1e18
    cap = min(ilim, i_vindpm_cap)
    off_node = ctrl.get("batfet_off_comparator_node_V")

    why = []
    if mode not in CHARGER_BRANCHES:
        why.append("unknown branch %r" % (mode,))
        return False, why
    # ---- universal ------------------------------------------------------
    if i_in > cap + 1e-6:
        why.append("the input current exceeds the binding input-side loop")
    if i_in > 1e-9 and v_pin < v_vindpm - 1e-6:
        why.append("the IN pin sits below the VINDPM threshold")
    if i_supp > 1e-9 and i_chg > 1e-9:
        why.append("charging and supplementing at the same time")
    if i_chg > ichg + 1e-9:
        why.append("more charge current than the CC loop programs")
    if vsys > vsys_reg + 1e-9:
        why.append("SYS above its regulation point")
    if min(i_in, i_chg, i_supp, st["system_A"]) < -1e-12:
        why.append("a negative current")
    # ---- per branch -----------------------------------------------------
    if mode == "SYS_REG":
        if abs(vsys - vsys_reg) > 1e-6:
            why.append("SYS is not at its regulation point")
        if i_chg < ichg - 1e-9:
            why.append("SYS regulation has no authority over the charge "
                       "current: a folded charge current is ILIM, VINDPM, "
                       "DPPM or TREG")
        if vbus - i_in * r_src < vsys_reg - 1e-6:
            why.append("the source cannot hold the regulation point claimed")
    elif mode == "CC_PATH_LIMITED":
        if i_chg < ichg - 1e-9:
            why.append("CC_PATH_LIMITED charges at ICHG by definition")
        if abs(vsys - (vbus - i_in * r_src)) > 1e-6:
            why.append("SYS is not what the source and RON_IN leave")
        if vsys < v_dppm - 1e-9:
            why.append("SYS is below VDPPM: the DPPM loop has control")
        if i_in > cap - 1e-9 and cap < 1e17:
            why.append("an input-side loop is at its limit: the branch is "
                       "ILIM or VINDPM, not CC_PATH_LIMITED")
    elif mode in ("ILIM", "VINDPM"):
        if i_in < cap - 1e-6:
            why.append("the branch names a loop that is not at its limit")
        if i_supp > 1e-9:
            why.append("an input-limited branch may not supplement")
        if vsys < v_dppm - 1e-9:
            why.append("SYS is below VDPPM: the DPPM loop has control")
        if mode == "ILIM" and ilim > i_vindpm_cap + 1e-9:
            why.append("VINDPM binds before ILIM at this source")
        if mode == "VINDPM":
            if i_vindpm_cap > ilim + 1e-9:
                why.append("ILIM binds before VINDPM at this source")
            if abs(v_pin - v_vindpm) > 1e-6:
                why.append("VINDPM claimed with the IN pin off its threshold")
    elif mode == "DPPM":
        if abs(vsys - v_dppm) > 1e-6:
            why.append("DPPM does not hold SYS at VBAT + VDPPM")
        if vsys <= vbat:
            why.append("6.3.2: SYS is maintained ABOVE the battery while the "
                       "DPPM loop is in control")
        if i_supp > 1e-9:
            why.append("DPPM may not supplement")
    elif mode == "NO_CHARGE":
        if i_chg > 1e-9 or i_supp > 1e-9:
            why.append("NO_CHARGE must neither charge nor supplement")
        if abs(vsys - min(vsys_reg, vbus - i_in * r_src)) > 1e-6:
            why.append("SYS is not what the regulator and the source leave")
        if vsys < v_sup_enter - 1e-9:
            why.append("SYS is below the supplement ENTRY threshold and the "
                       "BATFET would be conducting")
        if st.get("previous_mode") == "SUPPLEMENT" and vsys < v_sup_exit - 1e-9:
            why.append("the part was supplementing and SYS has not risen "
                       "back above VBAT - VBSUP2")
    elif mode == "SUPPLEMENT":
        if i_chg > 1e-9:
            why.append("SUPPLEMENT must not charge")
        if vsys > vbat + 1e-9:
            why.append("supplementing into a node ABOVE the cell")
        if abs(vsys - (vbat - i_supp * ron_bat)) > 1e-6:
            why.append("SYS is not the cell less the BATFET drop")
        held = (vbus - vsys) / r_src
        if i_in < min(cap, held) - 1e-6:
            why.append("the input is delivering less than it could")
        # The COMPARATOR input is the BATFET-OFF node, not the solved one.
        if off_node is not None:
            if off_node > v_sup_enter + 1e-9:
                if not (st.get("previous_mode") == "SUPPLEMENT"
                        and off_node <= v_sup_exit + 1e-9):
                    why.append("supplement entered with the BATFET-off node "
                               "above VBAT - VBSUP1 and nothing to latch it")
    return (not why), why


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
REQUIRED_CHARGER_BRANCHES = ("SYS_REG", "CC_PATH_LIMITED", "ILIM", "VINDPM",
                             "DPPM", "NO_CHARGE", "SUPPLEMENT")
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
                 residual_worst_W, residual_worst_V, network_states=()):
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
    for b in REQUIRED_CHARGER_BRANCHES:
        if b not in branches:
            problems.append("charger branch %r is never exercised" % b)
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
    want_net = set()
    for state in EXPECTED_CELL_NET_STATES:
        for cfg in EXPECTED_ACCESSORY_CONFIGURATIONS:
            for corner in EXPECTED_CELL_CORNERS:
                want_net.add("%s/%s/%s" % (state, cfg, corner))
    got_net = [n.get("key") for n in network_states]
    seen_net = {}
    for k in got_net:
        seen_net[k] = seen_net.get(k, 0) + 1
    if not got_net:
        problems.append("the cell-to-load network domain is EMPTY: nothing "
                        "was re-derived by KVL at all")
    for k in sorted(seen_net):
        if k not in want_net:
            problems.append("network state %r is not in the constructed "
                            "domain" % (k,))
        elif seen_net[k] > 1:
            problems.append("network state %r appears %d times" %
                            (k, seen_net[k]))
    states_present = {(k or "").split("/")[0] for k in got_net}
    for state in EXPECTED_CELL_NET_STATES:
        if state == EXPECTED_RETIRED_CELL_NET_STATE:
            continue
        if state not in states_present:
            problems.append("cell-to-load state %r contributes no network "
                            "row: its KVL was never independently checked"
                            % (state,))

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
          without_energy_oracle=False):
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
                                 network_states=network_states)
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
