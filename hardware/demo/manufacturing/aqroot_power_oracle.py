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
import re

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
    # D-796 / R15-02: the source classes' own path terms, so the oracle can
    # rebuild every class's physics and bind a key's source label to it.
    "usb.awg24_stranded_max_ohm_per_m": 0.0918,
    "usb.awg28_stranded_max_ohm_per_m": 0.232,
    "usb.mated_receptacle_pair_ohm": 0.03,
    "usb.board_vbus_copper_ohm": 0.02,
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
    "bq.vlowv_max_V": 3.1,
    "bq.treg_typ_C": 100.0,
    "bq.treg_declared_band_K": 10.0,
    # D-796 / D796-08: VBUVLO and its hysteresis, SLUSF65B EC, by hand.
    "bq.vbuvlo_typ_V": 3.0,
    "bq.vbuvlo_declared_tolerance": 0.05,
    "bq.vbuvlo_hys_max_V": 0.190,
    # D-797 / D797-01: SLUSF65B EC TSHUT_RISING 150 C (TYP column), by hand.
    "bq.tshut_rising_C": 150.0,
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
                    "DPPM", "NO_CHARGE", "SUPPLEMENT", "SUPPLEMENT_CYCLE")
# D-798 / D798-01: the branches in which the CELL discharges into SYS.
ORACLE_SUPPLEMENTING = ("SUPPLEMENT", "SUPPLEMENT_CYCLE")
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
# D-796 / D796-08.  THE BATFET BELOW VBUVLO, WRITTEN OUT.
#
# SLUSF65B 6.3.3: supplement needs VBAT > VBUVLO; 6.3.7.2: BUVLO disconnects
# BAT from SYS.  The falling trip is 3.0 V TYP with the DECLARED +/-5 %; a
# cell that fell through it re-connects at trip + VBUVLO_HYS (190 mV MAX).
# ==========================================================================
def oracle_buvlo_band():
    p = PRIMITIVES
    lo = p["bq.vbuvlo_typ_V"] * (1.0 - p["bq.vbuvlo_declared_tolerance"])
    hi = p["bq.vbuvlo_typ_V"] * (1.0 + p["bq.vbuvlo_declared_tolerance"])
    return lo, hi, hi + p["bq.vbuvlo_hys_max_V"]


def oracle_batfet_states(vbat):
    lo, _hi, reconnect = oracle_buvlo_band()
    if vbat <= lo + 1e-9:
        return ("uvlo_open",)
    if vbat >= reconnect - 1e-9:
        return ("connected",)
    return ("connected", "uvlo_open")


# ==========================================================================
# D-796 / R15-02 (D796-03).  THE SOURCE CLASSES, REBUILT FROM PRIMITIVES.
#
# A key that says `rpi15w_high` must carry the named adapter's +7 % VBUS on
# its captive 1.5 m 18 AWG cable with ONE mated pair -- not merely the name.
# ==========================================================================
ORACLE_RPI_NOMINAL_V = 5.1


def oracle_source_classes():
    p = PRIMITIVES
    def path(awg_key, length_m, pairs):
        return round(2.0 * length_m * p[awg_key]
                     + pairs * p["usb.mated_receptacle_pair_ohm"]
                     + p["usb.board_vbus_copper_ohm"], 6)
    reg = p["usb.rpi15w_regulation_fraction"]
    return {
        "rpi15w_high": dict(vbus_V=round(ORACLE_RPI_NOMINAL_V * (1 + reg), 6),
                            path_ohm=path("usb.awg18_stranded_max_ohm_per_m",
                                          1.5, 1), qualified=True),
        "rpi15w_low": dict(vbus_V=round(ORACLE_RPI_NOMINAL_V * (1 - reg), 6),
                           path_ohm=path("usb.awg18_stranded_max_ohm_per_m",
                                         1.5, 1), qualified=True),
        "generic_typec_24awg_2m": dict(
            vbus_V=4.75, path_ohm=path("usb.awg24_stranded_max_ohm_per_m",
                                       2.0, 2), qualified=False),
        "unqualified_28awg_2m": dict(
            vbus_V=4.75, path_ohm=path("usb.awg28_stranded_max_ohm_per_m",
                                       2.0, 2), qualified=False),
    }


def oracle_ilim(corner):
    p = PRIMITIVES
    return {"max": p["bq.ilim_max_A"], "min": p["bq.ilim_min_A"]}.get(corner)


def oracle_treg_band():
    p = PRIMITIVES
    return (p["bq.treg_typ_C"] - p["bq.treg_declared_band_K"],
            p["bq.treg_typ_C"] + p["bq.treg_declared_band_K"])


TREG_TOL_K = 0.05
ORACLE_ABSORBING_REGIMES = ("SUPPLEMENT_ABSORBING", "TSHUT_PROTECTION_CYCLE")


def thermal_label_problems(st):
    """D-796 / R15-01, independently: a thermal label must be HELD by the
    loop it names.  The junction is re-derived from the state's own terminal
    powers and thermal block, never read from `junction_C`."""
    th = st.get("thermal")
    if not isinstance(th, dict):
        return ["no thermal block"]
    why = []
    internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                - th.get("delivered_out_W", 0.0))
    tj = (th["ambient_C"] + th["r_sys_K_per_W"] * internal
          + th["theta_ja_C_per_W"] * st["package_W"])
    treg = th["treg_C"]
    lo, hi = oracle_treg_band()
    if not (lo - 1e-9 <= treg <= hi + 1e-9):
        why.append("a thermal solve at %.3f C, outside the declared TREG "
                   "band" % treg)
    if abs(tj - th.get("junction_C", float("nan"))) > 1e-3:
        why.append("the published junction %.4f C is not what the state's "
                   "own powers give (%.4f C)" % (th.get("junction_C",
                                                        float("nan")), tj))
    regime = th.get("regime")
    active = bool(th.get("treg_active"))
    charging = st["charge_A"] > 1e-9
    nominal, _k = oracle_charge_program(st["vbat_V"],
                                        st.get("ichg_corner", "max"))
    folded = st["charge_A"] < nominal - 5e-6
    if st["mode"] == "TREG" and regime not in ("TREG_EQUILIBRIUM",
                                               "TREG_AT_ZERO_CHARGE"):
        why.append("a TREG branch that no thermal solve produced")
    if regime == "NO_TREG":
        if active:
            why.append("NO_TREG with the loop marked active")
        if tj > treg + TREG_TOL_K and charging:
            why.append("a charging state at %.3f C above TREG %.1f C with "
                       "the thermal loop inactive" % (tj, treg))
    elif regime == "TREG_EQUILIBRIUM":
        if abs(tj - treg) > TREG_TOL_K:
            why.append("a TREG equilibrium at %.3f C, not at its %.1f C "
                       "threshold -- a COLD TREG state" % (tj, treg))
        if not folded:
            why.append("a TREG equilibrium that folds nothing")
    elif regime == "TREG_AT_ZERO_CHARGE":
        if charging:
            why.append("TREG at zero charge with a charge current")
        if tj < treg - TREG_TOL_K:
            why.append("zero charge claimed by TREG with the junction "
                       "%.3f C below the threshold" % tj)
    elif regime in ORACLE_ABSORBING_REGIMES:
        # D-797 / D797-01, independently: a supplementing part carries no
        # charge for TREG to fold and cannot lift its own SYS to the exit,
        # so its junction is STATIC; at or above TSHUT_RISING the device's
        # own protection -- "stops charging and shuts down VSYS" (SLUSF65B
        # 6.3.7.6) -- is what acts, which is not an operating state.
        if st["mode"] not in ORACLE_SUPPLEMENTING:
            why.append("an absorbing supplement regime on a %s state"
                       % st["mode"])
        if active:
            why.append("TREG marked active on a supplement it cannot fold")
        tshut = PRIMITIVES["bq.tshut_rising_C"]
        if (regime == "TSHUT_PROTECTION_CYCLE") != (tj >= tshut):
            why.append("the TSHUT label disagrees with the junction %.3f C "
                       "against TSHUT_RISING %.1f C" % (tj, tshut))
    elif regime == "TREG_LIMIT_CYCLE_HOT_PHASE":
        if st["mode"] not in CHARGER_BRANCHES_THAT_FOLD_CHARGE:
            why.append("a limit-cycle hot phase that is not DPPM-held (D-797:"
                       " a supplement has no path out of the hot phase)")
        if tj < treg - TREG_TOL_K:
            why.append("a limit-cycle hot phase below TREG")
        lc = th.get("limit_cycle") or {}
        if lc.get("cold_phase_junction_C") is None or \
                lc["cold_phase_junction_C"] >= treg - TREG_TOL_K:
            why.append("a limit cycle whose cold phase is not below TREG: "
                       "a static TREG state existed and was not used")
    else:
        why.append("unknown thermal regime %r" % (regime,))
    if st["mode"] in ORACLE_SUPPLEMENTING \
            and regime not in ORACLE_ABSORBING_REGIMES:
        why.append("a SUPPLEMENT state labelled %r: it is absorbing and TREG "
                   "cannot act on it" % (regime,))
    if regime not in ("NO_TREG",) + ORACLE_ABSORBING_REGIMES and not active:
        why.append("%s with the loop marked inactive" % regime)
    return why


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


def oracle_supplementing_node(p_sys, vbat, vbus, path, cap):
    """D-798 / D798-01, independently.  The SYS a supplementing part holds:
    SLUSF65B 6.3.3 -- "the battery supplement current is not regulated" --
    so the BATFET is ON and SYS is the cell less RON_BAT x the shortfall.
    None where the input carries the whole load at SYS = VBAT."""
    p = PRIMITIVES
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    r_src = path + ron_in

    def resid(vs):
        i_in = max(0.0, min(cap, (vbus - vs) / r_src))
        return vbat - (p_sys / vs - i_in) * ron_bat - vs
    if resid(vbat) >= 0.0:
        return None
    lo, hi = 1e-3, vbat
    for _ in range(90):
        mid = 0.5 * (lo + hi)
        if resid(mid) >= 0.0:
            lo = mid
        else:
            hi = mid
    vs = 0.5 * (lo + hi)
    return vs if vs > 0.2 else None


def oracle_settle_node(p_sys, vbus, path, cap, v_from, v_enter):
    """D-798 / D798-01, independently.  Once the VBSUP2 comparator opens the
    BATFET at `v_from`, SYS falls (the input's surplus is negative there)
    until the input carries the load -- which, the input being a CONSTANT
    current wherever ILIM or VINDPM caps it, can only happen on the path-
    limited stretch, at the high root of  P = V (VBUS - V) / (R_PATH + RON_IN).
    None if that root is not inside [VBAT - VBSUP1, v_from]."""
    r_src = path + PRIMITIVES["bq.ron_in_max_ohm"]
    d = vbus * vbus - 4.0 * p_sys * r_src
    if d < 0.0:
        return None
    vh = 0.5 * (vbus + math.sqrt(d))
    if vh > v_from + 1e-12 or vh <= v_enter + 1e-12:
        return None
    if (vbus - vh) / r_src > cap + 1e-12:
        return None
    return vh


def oracle_supplement_verdict(p_sys, vbat, vbus, path, cap, sweep):
    """(branch, supplementing node, settle node) the exit comparator gives a
    part that is supplementing -- or (None, None, None) where the input
    carries the load at SYS = VBAT."""
    _d, v_enter, v_exit, _v = _oracle_thresholds(vbat, sweep)
    node = oracle_supplementing_node(p_sys, vbat, vbus, path, cap)
    if node is None:
        return None, None, None
    if node <= v_exit + 1e-12:
        return "SUPPLEMENT", node, None
    vh = oracle_settle_node(p_sys, vbus, path, cap, node, v_enter)
    if vh is not None:
        return "NO_CHARGE", node, vh
    return "SUPPLEMENT_CYCLE", node, None


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
    # ---- D-796 / D796-08: the BATFET below VBUVLO ------------------------
    bf = st.get("batfet")
    if bf not in ("connected", "uvlo_open"):
        why.append("the state names no BATFET state (%r)" % (bf,))
    elif bf not in oracle_batfet_states(vbat):
        why.append("BATFET %r is not a state a %.3f V cell can be in" %
                   (bf, vbat))
    if bf == "uvlo_open" and st.get("previous_mode") == "SUPPLEMENT":
        why.append("a SUPPLEMENT history with the BATFET disconnected by "
                   "BUVLO")
    if (mode in ORACLE_SUPPLEMENTING or i_supp > 1e-9) and (
            bf != "connected" or vbat <= oracle_buvlo_band()[0] + 1e-9):
        why.append("supplement at or under VBUVLO: SLUSF65B 6.3.3 -- the "
                   "BATFET cannot supply SYS there")
    # ---- D-797 / D797-01: EXIT IS JUDGED ON THE ACTUAL SYS ---------------
    # Whether the input can carry the whole load with SYS AT the cell -- the
    # node a supplementing part actually holds.  If it cannot, a part that
    # was supplementing stays supplementing, whatever a BATFET-OFF node
    # elsewhere would have done.
    p_sys_ = st["system_W"]
    i_in_at_vbat = max(0.0, min(cap, (vbus - vbat) / r_src))
    # `system_W` is the PUBLIC field, rounded to 1e-6 W, so the comparison
    # carries the same 5 uA tolerance as every other public-field inequality.
    short_at_vbat = bool(bf == "connected"
                         and p_sys_ / vbat > i_in_at_vbat + tol)
    # D-798 / D798-01: the VBSUP2 comparator on the ACTUAL supplementing SYS.
    # Judged at the state's full-precision load: a boundary probe sits 1e-7 W
    # above an onset, under the 1e-6 W rounding of the public field (the two
    # are equality-gated against each other in `raw_summary_divergence`).
    _p_exact = (st.get("raw") or {}).get("p_sys", p_sys_)
    if not isinstance(_p_exact, (int, float)) or \
            abs(_p_exact - p_sys_) > 6e-7:
        _p_exact = p_sys_
    verdict, sup_node, settle = (oracle_supplement_verdict(
        _p_exact, vbat, vbus, path, cap, sweep) if bf == "connected"
        else (None, None, None))
    if bf == "connected":
        short_at_vbat = bool(short_at_vbat or verdict is not None)
    if st.get("previous_mode") == "SUPPLEMENT" and short_at_vbat \
            and verdict is not None and mode != verdict:
        if verdict in ORACLE_SUPPLEMENTING and \
                mode not in ORACLE_SUPPLEMENTING:
            kind = ("EXIT TOO EARLY: the part was supplementing and %s is "
                    "not reachable from that history (the D-796 defect -- "
                    "a hypothetical BATFET-off node)" % mode)
        elif mode == "SUPPLEMENT":
            kind = ("RETENTION TOO LATE: a static supplement held above the "
                    "VBSUP2 exit (the D-797 defect -- a bare shortfall at "
                    "SYS = VBAT)")
        else:
            kind = "the wrong branch for that history"
        why.append("%s; its supplementing SYS %.6f V against the VBSUP2 exit "
                   "%.6f V makes the branch %s, not %s"
                   % (kind, sup_node, v_sup_exit, verdict, mode))
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
        if not isinstance(st.get("thermal"), dict):
            why.append("a TREG state carries no thermal evidence")
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
        if vsys < v_sup_enter - 1e-9 and st.get("batfet") != "uvlo_open":
            why.append("SYS is below the supplement ENTRY threshold")
        if st.get("previous_mode") == "SUPPLEMENT" and vsys < v_sup_exit - 1e-9:
            # D-798 / D798-01: inside the band with a SUPPLEMENT history only
            # at the node the exit settled to.
            if not (verdict == "NO_CHARGE" and settle is not None
                    and abs(vsys - settle) <= tol):
                why.append("the part was supplementing and SYS sits under "
                           "VBAT - VBSUP2 at a node the exit comparator did "
                           "not settle to")
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
        if not short_at_vbat and p_sys_ / vbat <= i_in_at_vbat - 1e-6:
            why.append("SUPPLEMENT where the input carries the whole load at "
                       "SYS = VBAT: no shortfall for the cell to supply")
        if off_node is not None and st.get("previous_mode") != "SUPPLEMENT":
            if off_node > v_sup_enter + 1e-9:
                why.append("supplement entered with the BATFET-off node "
                           "above VBAT - VBSUP1 and nothing to latch it")
        # D-798 / D798-01: a STATIC supplement sits at or under the exit.
        if vsys > v_sup_exit + tol:
            why.append("a static SUPPLEMENT with SYS %.6f V above the VBSUP2 "
                       "exit %.6f V: the comparator has opened the BATFET"
                       % (vsys, v_sup_exit))
    elif mode == "SUPPLEMENT_CYCLE":
        # D-798 / D798-01: the comparator relaxation cycle, at its FLOOR.
        if i_chg > 1e-9:
            why.append("a supplement cycle must not charge")
        if abs(vsys - v_sup_enter) > tol:
            why.append("a supplement cycle is carried at its floor, "
                       "VBAT - VBSUP1")
        held = (vbus - vsys) / r_src
        if abs(i_in - min(cap, held)) > tol:
            why.append("the input is not delivering what it can at the "
                       "cycle floor")
        if verdict != "SUPPLEMENT_CYCLE":
            why.append("a supplement cycle where the exit comparator gives "
                       "%r" % (verdict,))
        if abs(i_supp - (p_sys_ / vsys - i_in)) > 1e-5:
            why.append("the cycle's shortfall is not the load less the input "
                       "at its floor")
        if off_node is not None and st.get("previous_mode") != "SUPPLEMENT":
            if off_node > v_sup_enter + 1e-9:
                why.append("a supplement cycle entered with the BATFET-off "
                           "node above VBAT - VBSUP1 and nothing to latch it")
    # ---- D-796 / R15-01: every thermally-closed state, whatever its branch
    if isinstance(st.get("thermal"), dict):
        why += thermal_label_problems(st)
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
               ilim, sweep, prev, ichg_corner, off_node, batfet="connected"):
    return dict(mode=mode, vsys_V=vsys, vbat_V=vbat, batfet=batfet,
                vin_pin_V=vbus - i_in * path, input_A=i_in, charge_A=i_chg,
                supplement_A=i_supp,
                system_A=(p_sys / vsys if vsys > 0 else 0.0),
                ilim_A=ilim, path_ohm=path, vbus_source_V=vbus,
                previous_mode=prev, ichg_corner=ichg_corner,
                system_W=p_sys,
                controls=dict(sweep=sweep, charge_loop=None,
                              batfet_off_comparator_node_V=off_node))


def independent_branches(p_sys, vbat, vbus, path, ilim, sweep, prev,
                         ichg_corner, batfet="connected", zero_program=False):
    """Every branch whose own candidate passes the oracle's inequalities.

    An EMPTY answer means no static state: with the BATFET open that is SYS
    collapse, and the canonical side must deliver a refusal there."""
    return sorted({c["mode"] for c in independent_candidates(
        p_sys, vbat, vbus, path, ilim, sweep, prev, ichg_corner, batfet,
        zero_program)})


def independent_candidates(p_sys, vbat, vbus, path, ilim, sweep, prev,
                           ichg_corner, batfet="connected",
                           zero_program=False):
    """The surviving candidate STATES themselves (D-797 / D797-03), so a
    boundary can be re-derived here -- heat and junction included -- rather
    than accepted from the canonical evidence.  `zero_program` is the state
    TREG leaves when it has folded the charge program to zero."""
    p = PRIMITIVES
    vsys_reg = p["bq.vsys_reg_V"] * 0.98
    ron_in = p["bq.ron_in_max_ohm"]
    ron_bat = p["bq.ron_bat_max_ohm"] * p["bq.ron_bat_vbat_allowance"]
    r_src = path + ron_in
    prog, _ = oracle_charge_program(vbat, ichg_corner)
    if zero_program:
        prog = 0.0
    v_dppm, v_sup_enter, v_sup_exit, v_vindpm = _oracle_thresholds(vbat,
                                                                   sweep)
    cap = min(ilim, max(0.0, (vbus - v_vindpm) / path))
    args = (p_sys, vbat, vbus, path, ilim, sweep, prev, ichg_corner)
    cands = []

    def _cand(*a):
        c = _candidate(*a, batfet=batfet)
        if zero_program:
            c["controls"].update(treg_folds_charge_to_zero=True,
                                 charge_loop="TREG")
        return c

    def high_root(ichg):
        b = vbus - ichg * r_src
        d = b * b - 4.0 * p_sys * r_src
        if d < 0:
            return None
        return 0.5 * (b + math.sqrt(d))

    # full program, regulated
    cands.append(_cand("SYS_REG", vsys_reg, p_sys / vsys_reg + prog,
                            prog, 0.0, *args, None))
    v = high_root(prog)
    if v is not None and v < vsys_reg:
        cands.append(_cand("CC_PATH_LIMITED", v,
                                (vbus - v) / r_src, prog, 0.0, *args, None))
    # DPPM-held
    held = max(0.0, (vbus - v_dppm) / r_src)
    for mode, i_in in (("ILIM", ilim),
                       ("VINDPM", max(0.0, (vbus - v_vindpm) / path)),
                       ("DPPM", held)):
        i_chg = i_in - p_sys / v_dppm
        if -1e-12 <= i_chg:
            cands.append(_cand(mode, v_dppm, i_in, max(0.0, i_chg), 0.0,
                                    *args, None))
    # no charge: the zero-charge node
    v0 = high_root(0.0)
    off = None
    if v0 is not None:
        v0 = min(v0, vsys_reg)
        i0 = p_sys / v0 if v0 > 0 else 0.0
        if i0 <= cap + 1e-12:
            off = v0
            cands.append(_cand("NO_CHARGE", v0, i0, 0.0, 0.0, *args,
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
    if batfet == "connected" and resid(hi) < 0.0:
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
            cands.append(_cand("SUPPLEMENT", vs, i_in, 0.0, i_supp,
                                    *args, off_for_sup))
            # D-798 / D798-01: the comparator cycle, at its floor.
            i_in_c = max(0.0, min(cap, (vbus - v_sup_enter) / r_src))
            cands.append(_cand("SUPPLEMENT_CYCLE", v_sup_enter, i_in_c, 0.0,
                               max(0.0, p_sys / v_sup_enter - i_in_c),
                               *args, off_for_sup))
    if zero_program:
        # No program, no charging branch: with the charge folded to zero the
        # part is NO_CHARGE or SUPPLEMENT (or has no state at all).
        cands = [c for c in cands
                 if c["mode"] in ("NO_CHARGE",) + ORACLE_SUPPLEMENTING]
    valid, by_mode = [], {}
    for c in cands:
        ok, _ = charger_branch_is_valid(c)
        if ok:
            valid.append(c["mode"])
            by_mode.setdefault(c["mode"], c)
    # PRECEDENCE BETWEEN FAMILIES.  A charging branch that is physical
    # excludes the no-charge ones: the CC loop takes the input first and the
    # BATFET only conducts when nothing else can hold SYS.
    charging = {"SYS_REG", "CC_PATH_LIMITED", "TREG", "ILIM", "VINDPM",
                "DPPM"}
    if charging & set(valid):
        valid = [v for v in valid if v in charging]
    # D-797 / D797-01.  RETENTION PRECEDES EVERYTHING.  A part that was
    # supplementing, where the input cannot carry the load at SYS = VBAT,
    # is still supplementing: no charge can flow below the cell, and the
    # actual SYS cannot rise to the exit.  Checked from the oracle's own
    # closed form, not from the candidate list.
    # D-798 / D798-01: and the branch it retains is the one the VBSUP2 exit
    # comparator gives on the actual supplementing SYS.
    if prev == "SUPPLEMENT" and batfet == "connected":
        i_at_vbat = max(0.0, min(cap, (vbus - vbat) / r_src))
        if p_sys / vbat > i_at_vbat + 5e-6:
            verdict, _n, _s = oracle_supplement_verdict(p_sys, vbat, vbus,
                                                        path, cap, sweep)
            return [by_mode[verdict]] if verdict in valid else []
    # Otherwise, where both a no-charge node and a supplementing solution
    # are physical, the history decides, exactly as the part does.
    sup_valid = [m for m in valid if m in ORACLE_SUPPLEMENTING]
    if "NO_CHARGE" in valid and sup_valid:
        valid = sup_valid if prev == "SUPPLEMENT" else ["NO_CHARGE"]
    # D-796 / D796-08: with the BATFET open, a NO_CHARGE node the CC loop
    # would pull down to VDPPM is not an equilibrium either -- there is no
    # supplement to end in, so SYS collapses and nothing is valid.
    if batfet != "connected" and valid == ["NO_CHARGE"] and prog > 0.0 \
            and off is not None and off > v_dppm + 1e-12:
        valid = []
    return [by_mode[m] for m in sorted(set(valid))]


def candidate_heat(c):
    """The terminal powers and package heat of an oracle candidate, from its
    own currents and nodes -- the same three package elements
    `charger_residuals` prices, written out again."""
    v_pin = c["vbus_source_V"] - c["input_A"] * c["path_ohm"]
    vsys, vbat = c["vsys_V"], c["vbat_V"]
    pkg = (max(0.0, (v_pin - vsys) * c["input_A"])
           + max(0.0, (vsys - vbat) * c["charge_A"])
           + max(0.0, (vbat - vsys) * c["supplement_A"]))
    return dict(package_W=pkg, source_W=c["vbus_source_V"] * c["input_A"],
                from_cell_W=vbat * c["supplement_A"],
                stored_W=vbat * c["charge_A"])


def oracle_reachable(p_sys, vbat, cls, ilim, sweep, hist, batfet):
    """D-797 / D797-01, independently: the states the part can be in at
    `p_sys` from a cold start at the full program with this history.  A
    SUPPLEMENT at the full program is absorbing -- it is the state; otherwise
    TREG can fold the charge down to zero, and the zero-program state is the
    one it cannot improve on.  None: no static state."""
    full = independent_candidates(p_sys, vbat, cls["vbus_V"],
                                  cls["path_ohm"], ilim, sweep, hist, "max",
                                  batfet)
    if len(full) == 1 and full[0]["mode"] in ORACLE_SUPPLEMENTING:
        return full
    zero = independent_candidates(p_sys, vbat, cls["vbus_V"],
                                  cls["path_ohm"], ilim, sweep, hist, "max",
                                  batfet, zero_program=True)
    return zero if len(zero) == 1 else None


def oracle_candidate_tj(c, th):
    h = candidate_heat(c)
    internal = (h["source_W"] + h["from_cell_W"] - h["stored_W"]
                - th.get("delivered_out_W", 0.0))
    return (th["ambient_C"] + th["r_sys_K_per_W"] * internal
            + th["theta_ja_C_per_W"] * h["package_W"])


def max_deliverable_W(vbat, vbus, path, ilim, sweep, batfet="connected"):
    """The most a constant-power load at SYS can be given at all -- input at
    its cap plus the battery through the BATFET -- scanned, so a refusal of
    'no operating point' can be checked against physics.  D-796: with the
    BATFET open (under VBUVLO) the battery term is zero."""
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
        i_bat = (vbat - vs) / ron_bat if batfet == "connected" else 0.0
        best = max(best, vs * (i_in + i_bat))
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
                             "VINDPM", "DPPM", "NO_CHARGE", "SUPPLEMENT",
                             # D-798 / D798-01
                             "SUPPLEMENT_CYCLE")
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


# ==========================================================================
# D-796 / R15-02 (D796-03).  THE LOAD SET BEHIND EVERY NETWORK KEY.
#
# "A network row labelled lowest-supported-cell carrying a full-cell solve
# MUST fail.  A canary name carrying another refused state's physics MUST
# fail unless the physical load set itself is exactly the named canary."
# The product definition below is what a network KEY means; the currents are
# a CHECKSUM of the canonical load table (`network_terms_agree`).
# ==========================================================================
EXPECTED_STATE_MODES = {
    "display_only": (),
    "display_audio": ("audio at the capped level",),
    "display_subghz": ("sub-GHz TX",),
    "display_subghz_audio": ("sub-GHz TX", "audio at the capped level"),
    "display_wifi": ("Wi-Fi / BLE TX",),
    "display_wifi_subghz": ("Wi-Fi / BLE TX", "sub-GHz TX"),
    "d790_declared": ("Wi-Fi / BLE TX", "sub-GHz TX",
                      "audio at the capped level"),
}
ORACLE_ALWAYS_ON_A = 0.466034
ORACLE_BURSTY_AVERAGE_A = 0.08
ORACLE_OPTIONAL_A = {"Wi-Fi / BLE TX": 0.426, "sub-GHz TX": 0.14,
                     "audio at the capped level": 0.12}
ORACLE_PUBLISHED_BUDGET_A = {"ACC_3V3": 0.400, "ACC_5V": 0.300}
ORACLE_DECLARED_PAIR_A = {"acc_3v3_A": 0.22, "acc_5v_A": 0.17}
CANARY_ACCESSORY = "acc_3v3_only"


def oracle_accessory_currents(cfg):
    b, d = ORACLE_PUBLISHED_BUDGET_A, ORACLE_DECLARED_PAIR_A
    return {"acc_3v3_only": (b["ACC_3V3"], 0.0),
            "acc_5v_only": (0.0, b["ACC_5V"]),
            "both_rails": (b["ACC_3V3"], b["ACC_5V"]),
            "both_rails_at_the_declared_pair": (d["acc_3v3_A"], d["acc_5v_A"]),
            "no_accessory": (0.0, 0.0)}.get(cfg)


def network_terms_agree(terms):
    why = []
    if not isinstance(terms, dict):
        return ["no network power terms were handed to the oracle"]
    for label, mine, theirs in (
            ("always-on", ORACLE_ALWAYS_ON_A, terms.get("always_on_A")),
            ("bursty average", ORACLE_BURSTY_AVERAGE_A,
             terms.get("bursty_time_averaged_A"))):
        if theirs is None or abs(mine - theirs) > 1e-9:
            why.append("the canonical %s current %r is not the oracle's %r"
                       % (label, theirs, mine))
    for m, mine in ORACLE_OPTIONAL_A.items():
        theirs = (terms.get("optional_A") or {}).get(m)
        if theirs is None or abs(mine - theirs) > 1e-9:
            why.append("mode %r: canonical %r vs oracle %r" % (m, theirs, mine))
    for k, mine in ORACLE_PUBLISHED_BUDGET_A.items():
        theirs = (terms.get("published_budget_A") or {}).get(k)
        if theirs is None or abs(mine - theirs) > 1e-9:
            why.append("budget %s: canonical %r vs oracle %r"
                       % (k, theirs, mine))
    for k, mine in ORACLE_DECLARED_PAIR_A.items():
        theirs = (terms.get("declared_pair_A") or {}).get(k)
        if theirs is None or abs(mine - theirs) > 1e-9:
            why.append("declared pair %s: canonical %r vs oracle %r"
                       % (k, theirs, mine))
    return why


def oracle_demand_W(modes, cfg, terms, scalars):
    i_int = (ORACLE_ALWAYS_ON_A + ORACLE_BURSTY_AVERAGE_A
             + sum(ORACLE_OPTIONAL_A[m] for m in modes))
    i3, i5 = oracle_accessory_currents(cfg)
    p12 = ((i_int + i3) * terms["v_3v3_V"] + i3 * i3 * terms["r_a3_ohm"]) \
        / scalars["eta_u12"]
    p21 = ((i5 * terms["v_acc5v_V"] + i5 * i5 * terms["r_a5_ohm"])
           / scalars["eta_u21"]) if i5 else 0.0
    return i_int, i3, i5, p12, p21


def load_set_problems(key, load_set, state, cfg, terms, scalars):
    why = []
    want_modes = EXPECTED_STATE_MODES.get(state)
    if want_modes is None:
        return ["%s names an unknown state %r" % (key, state)]
    if oracle_accessory_currents(cfg) is None:
        return ["%s names an unknown accessory configuration %r" % (key, cfg)]
    if not isinstance(load_set, dict):
        return ["%s carries no load set" % key]
    if sorted(load_set.get("modes") or []) != sorted(want_modes):
        why.append("%s is labelled %s but its load set runs %r"
                   % (key, state, load_set.get("modes")))
    i_int, i3, i5, p12, p21 = oracle_demand_W(want_modes, cfg, terms,
                                              scalars)
    for field, want in (("internal_3v3_A", i_int), ("acc_3v3_A", i3),
                        ("acc_5v_A", i5), ("demand_W", p12 + p21)):
        got = load_set.get(field)
        if got is None or abs(float(got) - want) > 2e-6:
            why.append("%s: %s is %r, the %s/%s load set gives %.6f"
                       % (key, field, got, state, cfg, want))
    return why


def network_row_problems(ns, terms, scalars):
    parts = (ns.get("key") or "").split("/")
    if len(parts) != 3:
        return ["network key %r does not parse" % (ns.get("key"),)]
    state, cfg, corner = parts
    why = load_set_problems(ns["key"], ns.get("load_set"), state, cfg, terms,
                            scalars)
    if ns.get("refused") or why:
        return why
    full = terms["full_cell_V"]
    if corner == "at_a_full_cell":
        if abs(ns["cell_V"] - full) > 1e-9:
            why.append("%s is labelled a full cell (%.4f V) and is solved at "
                       "%.6f V" % (ns["key"], full, ns["cell_V"]))
    elif corner == "at_the_lowest_supported_cell":
        floor = (ns.get("load_set") or {}).get("lowest_supported_cell_ocv_V")
        if floor is None or abs(ns["cell_V"] - floor) > 6e-5:
            why.append("%s is labelled the lowest supported cell (%r V) and "
                       "is solved at %.6f V" % (ns["key"], floor,
                                                ns["cell_V"]))
        if ns["cell_V"] >= full - 1e-4:
            why.append("%s is labelled the lowest supported cell and carries "
                       "a FULL-cell solve" % ns["key"])
    else:
        why.append("%s names an unknown cell corner" % ns["key"])
    # the demand the load set implies is what the solved node delivers at SYS
    i_int, i3, i5, p12, p21 = oracle_demand_W(EXPECTED_STATE_MODES[state],
                                              cfg, terms, scalars)
    trunk = 0.0
    if p21:
        i_u21 = p21 / ns["vsys_V"]
        for _ in range(400):
            i_u21 = p21 / (ns["vsys_V"] - i_u21 * terms["r_trunk_ohm"])
        trunk = i_u21 * i_u21 * terms["r_trunk_ohm"]
    r = ns["vsys_V"] * ns["amps"] - (p12 + p21 + trunk)
    if abs(r) > 1e-6:
        why.append("%s: SYS delivers %.6f W but its %s/%s load set demands "
                   "%.6f W" % (ns["key"], ns["vsys_V"] * ns["amps"], state,
                               cfg, p12 + p21 + trunk))
    kvl = ns["vsys_V"] - (ns["cell_V"] - ns["amps"] * (
        ns["fixed_ohm"] + ns["channels"] * ns["channel_ohm"]
        + terms["r_bat_ohm"]))
    if abs(kvl) > 1e-6:
        why.append("%s: KVL to SYS misses by %.3e V" % (ns["key"], kvl))
    return why


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
# D-797 / D797-01: 3.4 V added -- Astra's retained-supplement cell, where the
# BATFET-off node sits at 4.41 V while the supplementing SYS is under 3.4 V.
# D-798 / D798-01: 3.8 V and 3.8 W added -- Astra's Round-17 witness (the
# 5.457 V / 0.1184 ohm class at ILIM_min with a SUPPLEMENT history), where
# the supplementing SYS sits ABOVE the VBSUP2 exit and D-797 still held a
# static supplement.
EXPECTED_CHARGER_CELLS_V = (2.85, 3.2, 3.4, 3.52, 3.7, 3.8, 4.2, 4.221)
EXPECTED_CHARGER_POWERS_W = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.3,
                             3.6, 3.8, 4.0, 4.5, 5.0, 5.65, 7.0,
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
    ("NO_CHARGE", "NO_CHARGE"), ("SUPPLEMENT", "NO_CHARGE"),
    # D-798 / D798-01: the comparator cycle, from a supplement history
    ("SUPPLEMENT_CYCLE", "SUPPLEMENT"))
# D-797 / D797-02: 50 mV wide (firmware floors are read off it), plus 2.86 V --
# the lowest cell at which the BATFET can be connected -- 3.52 V and 4.221 V.
# Written out by hand so a narrowed canonical grid is a missing key.
EXPECTED_REGIME_VBAT_GRID_V = (
    2.85, 2.86, 2.9, 2.95, 3.0, 3.05, 3.1, 3.15, 3.2, 3.25, 3.3, 3.35, 3.4,
    3.45, 3.5, 3.52, 3.55, 3.6, 3.65, 3.7, 3.75, 3.8, 3.85, 3.9, 3.95, 4.0,
    4.05, 4.1, 4.15, 4.2, 4.221)
EXPECTED_REGIME_SWEEP_FRACTIONS = (-1.0, -0.5, 0.0, 0.5, 1.0)
EXPECTED_REGIME_HISTORIES = (None, "SUPPLEMENT")
EXPECTED_REGIME_AMBIENTS_C = (0.0, 25.0, 40.0)
REGIME_GUARDBAND = 0.05
REGIME_GRID_W = 0.05


EXPECTED_HISTORIES_WITH_THE_BATFET_OPEN = (None, "NO_CHARGE")


def histories_for(batfet, histories=EXPECTED_HISTORIES):
    """D-796 / D796-08: a SUPPLEMENT history is meaningless under the trip."""
    return tuple(h for h in histories
                 if batfet == "connected" or h != "SUPPLEMENT")


def charger_domain_key(vbat, p_sys, ilim, source, hist, ichg,
                       batfet="connected"):
    return "vbat%.3f/batfet_%s/p%.3f/ilim_%s/%s/%s/ichg_%s" % (
        vbat, batfet, p_sys, ilim, source, hist or "none", ichg)


_CHARGER_KEY = re.compile(
    r"^vbat(?P<vbat>[0-9.]+)/batfet_(?P<batfet>[a-z_]+)/p(?P<p>[0-9.]+)/"
    r"ilim_(?P<ilim>max|min)/(?P<source>[a-z0-9_]+)/(?P<hist>[A-Z_]+|none)/"
    r"ichg_(?P<ichg>max|min)$")


def parse_charger_key(k):
    m = _CHARGER_KEY.match(k or "")
    if not m:
        return None
    d = m.groupdict()
    return dict(vbat=float(d["vbat"]), batfet=d["batfet"],
                p_sys=float(d["p"]), ilim=d["ilim"], source=d["source"],
                hist=None if d["hist"] == "none" else d["hist"],
                ichg=d["ichg"])


def expected_charger_keys():
    out = []
    for v in EXPECTED_CHARGER_CELLS_V:
        for bf in oracle_batfet_states(v):
            for w in EXPECTED_CHARGER_POWERS_W:
                for il in EXPECTED_ILIM_CORNERS:
                    for c in EXPECTED_SOURCE_CLASSES:
                        for h in histories_for(bf):
                            for ic in EXPECTED_ICHG_CORNERS:
                                out.append(charger_domain_key(
                                    v, w, il, c, h, ic, bf))
    return out


def regime_row_key(source, vbat, batfet, ilim, sweep, hist, amb):
    return "%s/vbat%.3f/batfet_%s/ilim_%s/sweep%+.3f/%s/amb%.0f" % (
        source, vbat, batfet, ilim, sweep, hist or "none", amb)


_REGIME_KEY = re.compile(
    r"^(?P<source>[a-z0-9_]+)/vbat(?P<vbat>[0-9.]+)/batfet_(?P<batfet>[a-z_]+)"
    r"/ilim_(?P<ilim>max|min)/sweep(?P<sweep>[+-][0-9.]+)/"
    r"(?P<hist>[A-Z_]+|none)/amb(?P<amb>[0-9]+)$")


def parse_regime_key(k):
    m = _REGIME_KEY.match(k or "")
    if not m:
        return None
    d = m.groupdict()
    return dict(source=d["source"], vbat=float(d["vbat"]),
                batfet=d["batfet"], ilim=d["ilim"], sweep=float(d["sweep"]),
                hist=None if d["hist"] == "none" else d["hist"],
                amb=float(d["amb"]))


def expected_regime_keys():
    sw0 = PRIMITIVES["bq.branch_threshold_sweep"]
    out = []
    for c in EXPECTED_SOURCE_CLASSES:
        for v in EXPECTED_REGIME_VBAT_GRID_V:
            for bf in oracle_batfet_states(v):
                for il in EXPECTED_ILIM_CORNERS:
                    for f in EXPECTED_REGIME_SWEEP_FRACTIONS:
                        for h in histories_for(bf, EXPECTED_REGIME_HISTORIES):
                            for a in EXPECTED_REGIME_AMBIENTS_C:
                                out.append(regime_row_key(
                                    c, v, bf, il, round(f * sw0, 6), h, a))
    return out


# ==========================================================================
# D-796 / R15-02 (D796-03).  A KEY IS A CLAIM ABOUT THE STATE IT LABELS.
#
# ROUND-15: "Exact domain key multisets are necessary but not sufficient.
# Parse/reconstruct every semantic key and require equality with the physical
# state fields it names ... A charger key labelled vbat4.221 carrying a 4.2 V
# solve MUST fail."  D-795 checked that the right KEYS arrived exactly once
# and never that the state behind a key was the state the key names.
# ==========================================================================
def state_content_problems(st, want):
    """`want`: vbat, batfet, p_sys (or None), ilim, source, hist (or
    'ANY'), ichg (or None), sweep (or None).  Checks the PUBLIC fields, the
    ones every consumer reads."""
    why = []
    cls = oracle_source_classes().get(want["source"])
    if cls is None:
        return ["an unknown source class %r" % (want["source"],)]

    def neq(a, b, tol=1e-9):
        return a is None or b is None or abs(float(a) - float(b)) > tol
    if neq(st.get("vbat_V"), want["vbat"]):
        why.append("labelled a %.3f V cell, solved at %r V"
                   % (want["vbat"], st.get("vbat_V")))
    if st.get("batfet") != want["batfet"]:
        why.append("labelled BATFET %s, solved %r" % (want["batfet"],
                                                     st.get("batfet")))
    if want.get("p_sys") is not None and neq(st.get("system_W"),
                                             want["p_sys"]):
        why.append("labelled %.3f W, solved at %r W" % (want["p_sys"],
                                                       st.get("system_W")))
    if neq(st.get("ilim_A"), oracle_ilim(want["ilim"])):
        why.append("labelled ILIM %s (%.3f A), solved at %r A" % (
            want["ilim"], oracle_ilim(want["ilim"]), st.get("ilim_A")))
    if neq(st.get("vbus_source_V"), cls["vbus_V"]) or \
            neq(st.get("path_ohm"), cls["path_ohm"]):
        why.append("labelled source %s (%.4f V, %.4f ohm), solved on "
                   "%r V / %r ohm" % (want["source"], cls["vbus_V"],
                                      cls["path_ohm"],
                                      st.get("vbus_source_V"),
                                      st.get("path_ohm")))
    if st.get("source_key") is not None and st["source_key"] != want["source"]:
        why.append("labelled source %s, the state names %r"
                   % (want["source"], st["source_key"]))
    if want.get("hist", "ANY") != "ANY" and \
            st.get("previous_mode") != want["hist"]:
        why.append("labelled history %r, solved with %r"
                   % (want["hist"], st.get("previous_mode")))
    if want.get("ichg") is not None and st.get("ichg_corner") != want["ichg"]:
        why.append("labelled ICHG corner %r, solved at %r"
                   % (want["ichg"], st.get("ichg_corner")))
    if want.get("sweep") is not None:
        got = float((st.get("controls") or {}).get("sweep") or 0.0)
        if abs(got - want["sweep"]) > 1e-9:
            why.append("labelled threshold sweep %+.3f, solved at %+.3f"
                       % (want["sweep"], got))
    return why


def refusal_content_problems(r, want):
    why = []
    cls = oracle_source_classes().get(want["source"])
    if cls is None:
        return ["an unknown source class %r" % (want["source"],)]
    for field, value in (("vbat_V", want["vbat"]), ("system_W", want["p_sys"]),
                         ("ilim_A", oracle_ilim(want["ilim"])),
                         ("vbus_V", cls["vbus_V"]),
                         ("path_ohm", cls["path_ohm"]),
                         ("sweep", 0.0)):
        if r.get(field) is None or abs(float(r[field]) - value) > 1e-9:
            why.append("refusal labelled %s=%r carries %r"
                       % (field, value, r.get(field)))
    if r.get("batfet") != want["batfet"]:
        why.append("refusal labelled BATFET %s carries %r"
                   % (want["batfet"], r.get("batfet")))
    if r.get("previous_mode", "ABSENT") != want["hist"]:
        why.append("refusal labelled history %r carries %r"
                   % (want["hist"], r.get("previous_mode", "ABSENT")))
    if r.get("ichg_corner") != want["ichg"]:
        why.append("refusal labelled ICHG %r carries %r"
                   % (want["ichg"], r.get("ichg_corner")))
    return why


def _floor_to_grid(x):
    return (math.floor(x * (1.0 - REGIME_GUARDBAND) / REGIME_GRID_W + 1e-12)
            * REGIME_GRID_W)


def charger_domain_problems(charger_states, charger_refusals):
    """Exact keys; every key's CONTENT is the state it names (D796-03);
    every solved point agrees with the independent classifier; every refusal
    is physically re-checked."""
    why = []
    got = ([st.get("domain_key") for st in charger_states]
           + [r.get("domain_key") for r in charger_refusals])
    why += _multiset_problems("charger domain", got, expected_charger_keys())
    pops = {}
    by_key = {}
    disagreements = 0
    mislabelled = 0
    uvlo_solved = uvlo_refused = 0
    for st in charger_states:
        k = st.get("domain_key")
        by_key[k] = st
        want = parse_charger_key(k)
        if want is None:
            why.append("charger key %r does not parse" % (k,))
            continue
        cp = state_content_problems(st, dict(want, sweep=0.0))
        if cp:
            mislabelled += 1
            if mislabelled <= 8:
                why.append("charger point %s: the key is not the state it "
                           "labels: %s" % (k, cp[:2]))
        pops[(st["mode"], st.get("previous_mode"))] = pops.get(
            (st["mode"], st.get("previous_mode")), 0) + 1
        if want["batfet"] == "uvlo_open":
            uvlo_solved += 1
        branches = independent_branches(
            want["p_sys"], want["vbat"],
            oracle_source_classes()[want["source"]]["vbus_V"]
            if want["source"] in oracle_source_classes() else 0.0,
            oracle_source_classes()[want["source"]]["path_ohm"]
            if want["source"] in oracle_source_classes() else 1.0,
            oracle_ilim(want["ilim"]), 0.0, want["hist"], want["ichg"],
            want["batfet"])
        if branches != [st["mode"]]:
            disagreements += 1
            if disagreements <= 8:
                why.append("charger point %s: the canonical branch is %r but "
                           "the independent elimination leaves %r"
                           % (k, st["mode"], branches))
    if mislabelled > 8:
        why.append("... and %d more mislabelled charger points"
                   % (mislabelled - 8))
    if disagreements > 8:
        why.append("... and %d more branch disagreements" % (disagreements - 8))
    if not charger_refusals:
        why.append("the charger refusal set is EMPTY, but the declared domain "
                   "contains powers no source-plus-BATFET can deliver")
    bad_ref = 0
    for r in charger_refusals:
        want = parse_charger_key(r.get("domain_key"))
        if want is None:
            why.append("charger refusal key %r does not parse"
                       % (r.get("domain_key"),))
            continue
        rp = refusal_content_problems(r, want)
        cls = oracle_source_classes().get(want["source"])
        if cls is not None:
            left = independent_branches(
                want["p_sys"], want["vbat"], cls["vbus_V"], cls["path_ohm"],
                oracle_ilim(want["ilim"]), 0.0, want["hist"], want["ichg"],
                want["batfet"])
            if left:
                rp.append("REFUSED as having no operating point, but the "
                          "independent elimination finds %r" % (left,))
            if want["batfet"] == "connected":
                pmax = max_deliverable_W(want["vbat"], cls["vbus_V"],
                                         cls["path_ohm"],
                                         oracle_ilim(want["ilim"]), 0.0)
                if want["p_sys"] <= pmax * (1.0 + 1e-6):
                    rp.append("the input plus the BATFET can deliver %.4f W "
                              "against the %.4f W asked" % (pmax,
                                                            want["p_sys"]))
            else:
                uvlo_refused += 1
                if r.get("reason") != "sys_collapse_below_vbuvlo":
                    rp.append("a refusal under the trip must be the SYS "
                              "collapse, not %r" % (r.get("reason"),))
        if rp:
            bad_ref += 1
            if bad_ref <= 8:
                why.append("charger refusal %s: %s" % (r.get("domain_key"),
                                                       rp[:2]))
    for pair in REQUIRED_MODE_HISTORY_POPULATIONS:
        if not pops.get(pair):
            why.append("the (branch, history) population %r is EMPTY" %
                       (pair,))
    # D-796 / D796-08: the under-the-trip population exists, solved AND
    # collapsed, and it never supplements (charger_branch_is_valid).
    if not uvlo_solved:
        why.append("no charger point is solved with the BATFET open: the "
                   "VBUVLO regime is not exercised")
    if not uvlo_refused:
        why.append("no charger point collapses with the BATFET open: the "
                   "input-carrying boundary under VBUVLO is not exercised")
    # the hysteresis is DEMONSTRATED, not assumed
    latched = 0
    for st in charger_states:
        if st.get("previous_mode") != "SUPPLEMENT" \
                or st["mode"] not in ORACLE_SUPPLEMENTING:
            continue
        k0 = st["domain_key"].replace("/SUPPLEMENT/", "/none/")
        other = by_key.get(k0)
        if other is not None and other["mode"] == "NO_CHARGE":
            latched += 1
    if not latched:
        why.append("no point in the domain shows the VBSUP1/VBSUP2 "
                   "hysteresis deciding the branch: the history axis is not "
                   "exercised")
    # ---- D-797 / D797-01: THE TWO ROUND-16 CLASSES MUST BE EXERCISED ------
    # (a) Astra: a RETAINED supplement whose hypothetical BATFET-off node is
    #     ABOVE the exit threshold -- exactly the state D-796 discarded.
    # (b) Fable: a COLD-START supplement at a low cell, entered from the full
    #     program, which the corrected physics makes absorbing.
    retained_high_off = cold_low = 0
    for st in charger_states:
        c = st.get("controls") or {}
        if st["mode"] != "SUPPLEMENT" or st.get("batfet") != "connected":
            continue
        off = c.get("batfet_off_comparator_node_V")
        if st.get("previous_mode") == "SUPPLEMENT" and off is not None and \
                off > c.get("supplement_exit_V", 1e9):
            retained_high_off += 1
        if st.get("previous_mode") is None and st["vbat_V"] <= 3.4 + 1e-9:
            cold_low += 1
    if not retained_high_off:
        why.append("no point retains a SUPPLEMENT whose BATFET-off node is "
                   "above the exit: the Round-16 retained-supplement class is "
                   "not exercised")
    if not cold_low:
        why.append("no point enters SUPPLEMENT from a cold start at a cell at "
                   "or under 3.4 V: the Round-16 low-cell absorbing class is "
                   "not exercised")
    # ---- D-798 / D798-01: THE ROUND-17 CLASSES MUST BE EXERCISED ---------
    # (a) a SUPPLEMENT history, a shortfall at SYS = VBAT, and the actual
    #     supplementing SYS ABOVE the VBSUP2 exit -- Astra's witness, which
    #     D-797 held as a static supplement.  It must be the cycle here.
    # (b) a SUPPLEMENT history whose drop holds SYS at or under the exit --
    #     the truly retained static supplement D-796 dropped.
    cycle_retained = static_retained = 0
    for st in charger_states:
        c = st.get("controls") or {}
        if st.get("previous_mode") != "SUPPLEMENT" \
                or st.get("batfet") != "connected":
            continue
        node = c.get("supplementing_node_V")
        ex = c.get("supplement_exit_V")
        if node is None or ex is None:
            continue
        if st["mode"] == "SUPPLEMENT_CYCLE" and node > ex:
            cycle_retained += 1
        if st["mode"] == "SUPPLEMENT" and node <= ex + 1e-6:
            static_retained += 1
    if not cycle_retained:
        why.append("no point with a SUPPLEMENT history has its supplementing "
                   "SYS above the VBSUP2 exit: the Round-17 exit class is "
                   "not exercised")
    if not static_retained:
        why.append("no point retains a STATIC supplement under the VBSUP2 "
                   "exit: the D-796 dropped-retention class is not "
                   "exercised")
    return why, dict(
        expected_points=len(expected_charger_keys()),
        solved=len(charger_states), refused=len(charger_refusals),
        solved_with_the_batfet_open=uvlo_solved,
        collapsed_with_the_batfet_open=uvlo_refused,
        populations={"%s/%s" % (m, h or "none"): n
                     for (m, h), n in sorted(pops.items(),
                                             key=lambda x: repr(x))},
        points_where_history_decides=latched,
        retained_supplements_above_a_high_off_node=retained_high_off,
        retained_cycles_above_the_vbsup2_exit=cycle_retained,
        retained_static_supplements_under_the_exit=static_retained,
        cold_start_supplements_at_or_under_3v4=cold_low,
        classifier_disagreements=disagreements,
        mislabelled_points=mislabelled)


REGIME_JUNCTION_UNBOUNDED_W = 8.0


def _row_tj(st, th):
    internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                - th.get("delivered_out_W", 0.0))
    return (th["ambient_C"] + th["r_sys_K_per_W"] * internal
            + th["theta_ja_C_per_W"] * st["package_W"])


def regime_row_problems(r, scalars):
    """One regime row: its key is its content, its evidence brackets each
    ceiling it publishes, and every evidence state is physical."""
    why = []
    want = parse_regime_key(r.get("key"))
    if want is None:
        return ["regime key %r does not parse" % (r.get("key"),)]
    cls = oracle_source_classes().get(want["source"])
    if cls is None:
        return ["regime row %s names an unknown source" % r["key"]]
    # ---- D796-03: the row's own fields are the key's ----------------------
    for field, value in (("vbat_V", want["vbat"]), ("sweep", want["sweep"]),
                         ("ambient_C", want["amb"]),
                         ("ilim_A", oracle_ilim(want["ilim"])),
                         ("vbus_V", cls["vbus_V"]),
                         ("path_ohm", cls["path_ohm"])):
        if r.get(field) is None or abs(float(r[field]) - value) > 1e-9:
            why.append("row %s: %s is %r, the key says %r"
                       % (r["key"], field, r.get(field), value))
    for field, value in (("source_class", want["source"]),
                         ("batfet", want["batfet"]),
                         ("ilim_corner", want["ilim"]),
                         ("previous_mode", want["hist"]),
                         ("qualified", cls["qualified"])):
        if r.get(field, "ABSENT") != value:
            why.append("row %s: %s is %r, the key says %r"
                       % (r["key"], field, r.get(field, "ABSENT"), value))
    ev = r.get("_evidence")
    if not isinstance(ev, dict):
        return why + ["regime row %s carries no evidence" % r["key"]]
    th = ev.get("thermal") or {}
    if th.get("r_sys_K_per_W") != scalars.get("r_sys_K_per_W") or \
            th.get("theta_ja_C_per_W") != scalars.get("theta_ja_C_per_W"):
        why.append("regime row %s is solved on a thermal model the oracle "
                   "was not given" % r["key"])
    if th.get("ambient_C") is None or abs(th["ambient_C"] - want["amb"]) > 1e-9:
        why.append("row %s: the evidence is solved at %r C, the key says "
                   "%.0f C" % (r["key"], th.get("ambient_C"), want["amb"]))
    treg_low = oracle_treg_band()[0]
    if th.get("treg_low_C") is None or abs(th["treg_low_C"] - treg_low) > 1e-9:
        why.append("row %s: the TREG condition is judged at %r C, not the "
                   "declared low end %.1f C" % (r["key"], th.get("treg_low_C"),
                                                treg_low))
    want_state = dict(want, p_sys=None, hist=want["hist"], ichg="max")
    # ---- D-797 / D797-03: EVERY BOUNDARY STATE IS BOUND TO THE EXACT
    # SCALAR IT PROVES.  D-796 checked that each evidence state was the
    # key's state at SOME power; a row whose published ceiling was inflated
    # while its evidence stayed at the old, lower power passed.  Each label
    # must now be PRESENT (a None value is allowed only where the physics
    # says no state exists, and that is re-checked independently below), its
    # raw AND summary system power must be the published scalar -- the `_at`
    # state at it, the `_above` state at the declared probe offset
    # p x (1 + 1e-7) + 1e-7 from the `_at` state's own raw power.
    _bound = {"no_discharge": r.get("no_discharge_electrical_W"),
              "treg_zero": r.get("treg_zero_unreachable_W"),
              "junction": r.get("junction_boundary_W")}
    for _fam, _scalar in _bound.items():
        _at_l, _ab_l = _fam + "_at", _fam + "_above"
        for _l in (_at_l, _ab_l):
            if _l not in ev:
                why.append("row %s: the boundary evidence %r is MISSING"
                           % (r["key"], _l))
        if _scalar is None:
            why.append("row %s: the %s boundary scalar is not published"
                       % (r["key"], _fam))
            continue
        _at, _ab = ev.get(_at_l), ev.get(_ab_l)
        _p_at = None
        if isinstance(_at, dict):
            _p_at = (_at.get("raw") or {}).get("p_sys")
            if _p_at is None or abs(_p_at - _scalar) > 6e-7 or \
                    abs(float(_at.get("system_W", -1.0)) - _scalar) > 6e-7:
                why.append("row %s: the %s state is solved at %r W (summary "
                           "%r W), not at the published %.6f W it proves"
                           % (r["key"], _at_l, _p_at, _at.get("system_W"),
                              _scalar))
        if isinstance(_ab, dict):
            _p_ab = (_ab.get("raw") or {}).get("p_sys")
            _base = _p_at if _p_at is not None else _scalar
            if _p_ab is None or abs(_p_ab - (_base * (1.0 + 1e-7)
                                             + 1e-7)) > 1e-9:
                why.append("row %s: the %s state is at %r W, not at the "
                           "declared probe offset above %.6f W"
                           % (r["key"], _ab_l, _p_ab, _scalar))
    for label in ("no_discharge_at", "no_discharge_above", "treg_zero_at",
                  "treg_zero_above", "junction_at", "junction_above"):
        st = ev.get(label)
        if st is None:
            continue
        cp = state_content_problems(st, want_state)
        if cp:
            why.append("row %s: the %s state is not the state the key names: "
                       "%s" % (r["key"], label, cp[:2]))
        ok, w = charger_branch_is_valid(st)
        dok, dw = raw_summary_divergence(st)
        if not ok or not dok:
            why.append("row %s: the %s state is not physical: %s"
                       % (r["key"], label, (w + dw)[:2]))
        _zero = bool((st.get("controls") or {}).get(
            "treg_folds_charge_to_zero") and st["charge_A"] <= 1e-12)
        if label.startswith("treg_zero") and not _zero:
            why.append("row %s: the %s state is not the zero-charge state"
                       % (r["key"], label))
        # D-797: junction evidence is the hottest REACHABLE state -- the
        # zero-charge state, or an absorbing SUPPLEMENT reached at the full
        # program.  WHICH one is not judged here: these states sit 1e-7 from
        # the boundary, inside the two implementations' tolerances, and the
        # supplement onset is often exactly that boundary.  The independent
        # one-step-below / one-step-above search in
        # `_independent_boundary_problems` decides it instead.
        if label.startswith("junction") and not (
                _zero or (st["mode"] in ORACLE_SUPPLEMENTING
                          and st["charge_A"] <= 1e-12)):
            why.append("row %s: the %s state is %s -- neither the zero-charge "
                       "state nor an absorbing supplement"
                       % (r["key"], label, st["mode"]))
    tj_max = scalars["tj_operating_max_C"]
    nd_e = r.get("no_discharge_electrical_W")
    t0 = r.get("treg_zero_unreachable_W")
    if nd_e is None or t0 is None:
        return why + ["row %s: the two halves of the no-discharge ceiling "
                      "are not published" % r["key"]]
    if abs(r["no_discharge_W"] - min(nd_e, t0)) > 1e-6:
        why.append("row %s: no-discharge %.6f W is not min(electrical %.6f, "
                   "TREG-zero %.6f)" % (r["key"], r["no_discharge_W"], nd_e,
                                        t0))
    # ---- the electrical half: supplement onset, or collapse under the trip
    nd_at, nd_above = ev.get("no_discharge_at"), ev.get("no_discharge_above")
    if nd_e < REGIME_JUNCTION_UNBOUNDED_W - 0.01:
        if nd_e > 0 and (nd_at is None
                         or nd_at["mode"] in ORACLE_SUPPLEMENTING):
            why.append("row %s: at the electrical no-discharge ceiling the "
                       "part is supplementing or has no state" % r["key"])
        p_above = nd_e * (1.0 + 1e-7) + 1e-7
        if want["batfet"] == "connected":
            if nd_above is not None \
                    and nd_above["mode"] not in ORACLE_SUPPLEMENTING:
                why.append("row %s: just ABOVE the no-discharge ceiling the "
                           "part is still not supplementing -- the ceiling "
                           "is not the boundary" % r["key"])
        else:
            if nd_above is not None:
                why.append("row %s: under the trip, just above the input-"
                           "carrying ceiling a state still exists (%s)"
                           % (r["key"], nd_above["mode"]))
            # probed 0.01 % above: the oracle's own inequalities carry a
            # 5 uA tolerance, so a probe at 1e-7 would sit inside it
            left = independent_branches(
                nd_e * (1.0 + 1e-4) + 1e-4, want["vbat"], cls["vbus_V"],
                cls["path_ohm"],
                oracle_ilim(want["ilim"]), want["sweep"], want["hist"],
                "max", "uvlo_open")
            if left:
                why.append("row %s: the oracle finds %r just above the "
                           "claimed input-carrying ceiling" % (r["key"], left))
            if r.get("input_carrying_W") is None or \
                    abs(r["input_carrying_W"] - nd_e) > 1e-6:
                why.append("row %s: the input-carrying figure is not the "
                           "collapse point" % r["key"])
    if want["batfet"] == "connected" and r.get("input_carrying_W") is not None:
        why.append("row %s: an input-carrying limit on a connected BATFET"
                   % r["key"])
    # ---- the TREG half: the zero-charge junction against TREG's LOW end ---
    z_at, z_above = ev.get("treg_zero_at"), ev.get("treg_zero_above")
    if t0 > 0 and (z_at is None or _row_tj(z_at, th) >= treg_low):
        why.append("row %s: at the TREG-zero ceiling the zero-charge "
                   "junction is not below %.1f C" % (r["key"], treg_low))
    if t0 < REGIME_JUNCTION_UNBOUNDED_W - 0.01 and z_above is not None \
            and _row_tj(z_above, th) < treg_low:
        why.append("row %s: just above the TREG-zero ceiling the junction "
                   "is still below %.1f C -- not the boundary"
                   % (r["key"], treg_low))
    binding = r.get("no_discharge_binding")
    want_binding = ("input_carrying_below_vbuvlo"
                    if want["batfet"] != "connected" and nd_e <= t0
                    else "supplement_onset" if nd_e <= t0
                    else "treg_could_fold_the_charge_to_zero")
    if binding != want_binding:
        why.append("row %s: the no-discharge binding is %r, the halves say "
                   "%r" % (r["key"], binding, want_binding))
    # ---- the junction ------------------------------------------------------
    j_at, j_above = ev.get("junction_at"), ev.get("junction_above")
    jb = r.get("junction_binding")
    if jb == "domain_cap":
        if r.get("junction_limited") or \
                abs(r["junction_W"] - REGIME_JUNCTION_UNBOUNDED_W) > 1e-9:
            why.append("row %s: 'domain_cap' on a junction-limited row"
                       % r["key"])
        if j_at is not None and _row_tj(j_at, th) > tj_max + 1e-6:
            why.append("row %s: the junction is over %.1f C at the domain "
                       "cap" % (r["key"], tj_max))
    elif jb == "input_carrying_below_vbuvlo":
        if want["batfet"] == "connected" or r.get("junction_limited") or \
                abs(r["junction_W"] - REGIME_JUNCTION_UNBOUNDED_W) > 1e-9:
            why.append("row %s: an input-carrying junction label on a row "
                       "that is not under the trip or is junction-limited"
                       % r["key"])
        if j_above is not None:
            why.append("row %s: the junction is called unbounded by the "
                       "collapse but a zero-charge state exists above it"
                       % r["key"])
    elif jb in ("junction", "no_operating_point_above"):
        if not r.get("junction_limited"):
            why.append("row %s: %s but not junction-limited" % (r["key"], jb))
        if j_at is not None and _row_tj(j_at, th) > tj_max + 1e-6:
            why.append("row %s: the junction ceiling is over %.1f C"
                       % (r["key"], tj_max))
        if jb == "junction":
            if j_above is None or _row_tj(j_above, th) <= tj_max:
                why.append("row %s: just ABOVE the junction ceiling the "
                           "junction is still inside the maximum"
                           % r["key"])
        elif j_above is not None:
            why.append("row %s: 'no operating point above' with a state "
                       "above" % r["key"])
    else:
        why.append("row %s: unknown junction binding %r" % (r["key"], jb))
    if abs(r["ceiling_W"] - min(r["no_discharge_W"], r["junction_W"])) > 1e-6:
        why.append("regime row %s: the ceiling is not the lower of its two "
                   "limits" % r["key"])
    why += _independent_boundary_problems(r, want, cls, th, scalars)
    return why


# The one-step probe for the independent boundary search: 0.01 % of the
# boundary plus 0.1 mW either side.  The oracle's own inequalities carry
# micro-amp tolerances, so a probe inside them would test the tolerance and
# not the boundary.
BOUNDARY_PROBE_REL = 1e-4
BOUNDARY_PROBE_ABS = 1e-4


def _independent_boundary_problems(r, want, cls, th, scalars):
    """D-797 / D797-03.  THE CLAIM IS RECOMPUTED, NOT ACCEPTED.

    For every published boundary of the row, the oracle solves its OWN
    states one step below and one step above the scalar and requires the
    physics to change there: below the no-discharge figure the part does not
    supplement and above it it does (or, under the trip, collapses); below
    the TREG-zero figure the zero-charge junction is under TREG's low end and
    above it it is not; below the junction figure every reachable state is
    inside 125 C and above it one is not.  An inflated figure -- even one
    whose evidence and publication were edited to agree with it -- fails
    here, because the state one step below it is already on the wrong side.
    Enum labels that carry meaning are re-derived the same way."""
    why = []
    ilim = oracle_ilim(want["ilim"])
    tj_max = scalars["tj_operating_max_C"]
    treg_low = oracle_treg_band()[0]
    unb = REGIME_JUNCTION_UNBOUNDED_W - 0.01

    def below(x):
        return x * (1.0 - BOUNDARY_PROBE_REL) - BOUNDARY_PROBE_ABS

    def above(x):
        return x * (1.0 + BOUNDARY_PROBE_REL) + BOUNDARY_PROBE_ABS

    def modes(p, zero=False):
        return [c["mode"] for c in independent_candidates(
            p, want["vbat"], cls["vbus_V"], cls["path_ohm"], ilim,
            want["sweep"], want["hist"], "max", want["batfet"], zero)]

    def zero_tj(p):
        c = independent_candidates(p, want["vbat"], cls["vbus_V"],
                                   cls["path_ohm"], ilim, want["sweep"],
                                   want["hist"], "max", want["batfet"], True)
        return None if len(c) != 1 else oracle_candidate_tj(c[0], th)

    def reach_tj(p):
        rs = oracle_reachable(p, want["vbat"], cls, ilim, want["sweep"],
                              want["hist"], want["batfet"])
        return None if rs is None else max(oracle_candidate_tj(c, th)
                                           for c in rs)
    # ---- no-discharge (electrical) ----------------------------------------
    nd = r.get("no_discharge_electrical_W")
    if nd is not None:
        if nd > 2 * BOUNDARY_PROBE_ABS:
            m = modes(below(nd))
            if not m or (len(m) == 1 and m[0] in ORACLE_SUPPLEMENTING):
                why.append("row %s: one step BELOW the published no-discharge "
                           "figure %.6f W the oracle finds %r" % (r["key"],
                                                                  nd, m))
        if nd < unb:
            m = modes(above(nd))
            if want["batfet"] == "connected" and not (
                    len(m) == 1 and m[0] in ORACLE_SUPPLEMENTING):
                why.append("row %s: one step ABOVE the published no-discharge "
                           "figure %.6f W the oracle finds %r, not a "
                           "supplementing branch"
                           % (r["key"], nd, m))
            if want["batfet"] != "connected" and m:
                why.append("row %s: one step above the input-carrying figure "
                           "%.6f W a state still exists (%r)"
                           % (r["key"], nd, m))
        ev_at = (r.get("_evidence") or {}).get("no_discharge_at")
        if (r.get("mode_at_no_discharge_ceiling")
                != (ev_at or {}).get("mode", None)):
            why.append("row %s: mode_at_no_discharge_ceiling %r is not the "
                       "evidence's own mode" % (r["key"],
                                                r.get("mode_at_no_discharge_"
                                                      "ceiling")))
    # ---- TREG-zero ----------------------------------------------------------
    t0 = r.get("treg_zero_unreachable_W")
    if t0 is not None:
        if t0 > 2 * BOUNDARY_PROBE_ABS:
            tj = zero_tj(below(t0))
            if tj is None or tj >= treg_low:
                why.append("row %s: one step BELOW the TREG-zero figure %.6f W "
                           "the zero-charge junction is %r C, not under %.1f C"
                           % (r["key"], t0, tj, treg_low))
        if t0 < unb:
            tj = zero_tj(above(t0))
            if tj is not None and tj < treg_low:
                why.append("row %s: one step ABOVE the TREG-zero figure %.6f W "
                           "the zero-charge junction is still %.3f C"
                           % (r["key"], t0, tj))
    # ---- junction over the REACHABLE states --------------------------------
    jb = r.get("junction_boundary_W")
    if jb is not None:
        if jb > 2 * BOUNDARY_PROBE_ABS:
            tj = reach_tj(below(jb))
            if tj is None or tj > tj_max + 1e-6:
                why.append("row %s: one step BELOW the junction boundary "
                           "%.6f W a reachable state is at %r C (max %.1f C)"
                           % (r["key"], jb, tj, tj_max))
        if r.get("junction_limited"):
            if abs(r["junction_W"] - jb) > 1e-9:
                why.append("row %s: the junction figure %.6f W is not its "
                           "own boundary %.6f W" % (r["key"], r["junction_W"],
                                                    jb))
            tj = reach_tj(above(jb))
            if r.get("junction_binding") == "junction" and (
                    tj is None or tj <= tj_max):
                why.append("row %s: one step ABOVE the junction figure "
                           "%.6f W the reachable junction is %r C -- not the "
                           "boundary" % (r["key"], jb, tj))
            if r.get("junction_binding") == "no_operating_point_above" and \
                    tj is not None:
                why.append("row %s: 'no operating point above' but the oracle "
                           "finds a reachable state there" % r["key"])
            # the label of what lies above, re-derived
            rs = oracle_reachable(above(jb), want["vbat"], cls, ilim,
                                  want["sweep"], want["hist"], want["batfet"])
            if rs:
                c = rs[0]
                ctj = oracle_candidate_tj(c, th)
                lab = ("ZERO_CHARGE_ABOVE_TJ_MAX"
                       if c["mode"] not in ORACLE_SUPPLEMENTING
                       else "TSHUT_PROTECTION_CYCLE"
                       if ctj >= PRIMITIVES["bq.tshut_rising_C"]
                       else "SUPPLEMENT_ABSORBING")
                if r.get("junction_above_regime") != lab:
                    why.append("row %s: junction_above_regime %r, the oracle "
                               "finds %r" % (r["key"],
                                             r.get("junction_above_regime"),
                                             lab))
    binding = ("no_discharge" if r["no_discharge_W"] <= r["junction_W"]
               else "junction")
    if r.get("binding") != binding:
        why.append("row %s: binding %r, the limits say %r"
                   % (r["key"], r.get("binding"), binding))
    return why


def regime_problems(rows, published, scalars):
    """Every regime row exists exactly once, is the row its key names, its
    evidence brackets its own ceilings, and every PUBLISHED figure is the
    oracle's own minimum."""
    why = []
    got = [r.get("key") for r in rows]
    why += _multiset_problems("charge regime", got, expected_regime_keys())
    bad = 0
    for r in rows:
        w = regime_row_problems(r, scalars)
        if w:
            bad += 1
            if bad <= 8:
                why += w[:2]
    if bad > 8:
        why.append("... and %d more regime rows with problems" % (bad - 8))
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
        # D-798 / D798-05 (Astra R17-05).  THE PUBLICATION IS A MULTISET
        # BEFORE IT IS A TABLE.  D-797 projected the envelope into a dict and
        # THEN looked rows up, so a duplicate (source, cell) row -- a bad
        # figure first and the correct one after it -- was overwritten
        # before anything read it.  The exact key multiset, each key's
        # shape, and every published value's finiteness are checked on the
        # LIST; the projection happens only once they are.
        _env_list = published.get("envelope")
        if not isinstance(_env_list, list):
            why.append("the published envelope is not a list of rows")
            _env_list = []
        _pkeys, _pbad = [], 0
        for e in _env_list:
            if not isinstance(e, dict) or \
                    not isinstance(e.get("source_class"), str) or \
                    not isinstance(e.get("vbat_V"), (int, float)) or \
                    isinstance(e.get("vbat_V"), bool) or \
                    not math.isfinite(e["vbat_V"]):
                _pbad += 1
                why.append("a published envelope row has no valid (source "
                           "class, cell) key: %r" % (
                               (e.get("source_class"), e.get("vbat_V"))
                               if isinstance(e, dict) else e,))
                continue
            _pkeys.append((e["source_class"], round(e["vbat_V"], 6)))
            for f in ("no_discharge_published_W", "junction_published_W",
                      "input_carrying_published_W", "no_discharge_raw_W",
                      "junction_raw_W", "input_carrying_raw_W"):
                x = e.get(f)
                if x is not None and (
                        not isinstance(x, (int, float))
                        or isinstance(x, bool) or not math.isfinite(x)):
                    why.append("envelope %s/%.3f V %s is not a finite "
                               "number: %r" % (e["source_class"],
                                               e["vbat_V"], f, x))
        why += _multiset_problems(
            "published envelope", _pkeys,
            [(c, round(v, 6)) for c in EXPECTED_SOURCE_CLASSES
             for v in EXPECTED_REGIME_VBAT_GRID_V])
        for key in ("universal_no_discharge_published_W",
                    "junction_safe_published_W"):
            x = published.get(key)
            if not isinstance(x, (int, float)) or isinstance(x, bool) or \
                    not math.isfinite(x):
                why.append("the published %s is not a finite number: %r"
                           % (key, x))
        env = {}
        for e in _env_list:
            if isinstance(e, dict) and isinstance(e.get("source_class"), str) \
                    and isinstance(e.get("vbat_V"), (int, float)):
                # EVERY row is judged: a duplicate is compared, not shadowed.
                env.setdefault((e["source_class"], e["vbat_V"]), []).append(e)
        for c in EXPECTED_SOURCE_CLASSES:
            for v in EXPECTED_REGIME_VBAT_GRID_V:
                sel = [r for r in rows if r["source_class"] == c
                       and abs(r["vbat_V"] - v) < 1e-9]
                es = env.get((c, v)) or []
                if not sel or not es:
                    why.append("the published envelope has no row for %s at "
                               "%.3f V" % (c, v))
                    continue
                nd_want = _floor_to_grid(min(r["no_discharge_W"]
                                             for r in sel))
                jl = [r["junction_W"] for r in sel if r["junction_limited"]]
                tj_want = _floor_to_grid(min(jl)) if jl else None
                cr = [r["input_carrying_W"] for r in sel
                      if r.get("input_carrying_W") is not None]
                cr_want = _floor_to_grid(min(cr)) if cr else None
                for e in es:
                    for pub, want in (("no_discharge_published_W", nd_want),
                                      ("junction_published_W", tj_want),
                                      ("input_carrying_published_W",
                                       cr_want)):
                        got_v = e.get(pub, "ABSENT")
                        if (want is None) != (got_v is None) or (
                                want is not None and (
                                    not isinstance(got_v, (int, float))
                                    or isinstance(got_v, bool)
                                    or not math.isfinite(got_v)
                                    or abs(got_v - want) > 1e-6)):
                            why.append("envelope %s/%.3f V %s is %r, the "
                                       "oracle floors to %r"
                                       % (c, v, pub, got_v, want))
                    if sorted(e.get("batfet_states") or []) != sorted(
                            oracle_batfet_states(v)):
                        why.append("envelope %s/%.3f V names BATFET states %r"
                                   % (c, v, e.get("batfet_states")))
    elif not published:
        why.append("no published regime figures were handed to the oracle")
    return why, dict(expected_rows=len(expected_regime_keys()),
                     rows_seen=len(rows), rows_with_problems=bad)


# ==========================================================================
# D-796 / R15-02 (D796-03).  THE THERMALLY-CLOSED POPULATION IS EXACT.
#
# ROUND-15: "Thermal-domain completeness must require the exact expected
# population for each ambient/source/BAT/threshold/history combination.  A
# collapsed thermal population must fail even if one valid TREG state
# remains."  D-795 asked only that TREG appear somewhere.
# ==========================================================================
EXPECTED_COMPLETION_SCENARIOS = (("idle", 0.0), ("housekeeping", 0.35),
                                 ("display_quiet", 1.0))
EXPECTED_COMPLETION_AMBIENTS_C = (0.0, 25.0, 40.0)
EXPECTED_COMPLETION_STEPS = 23
ORACLE_VBATREG_V = 4.2


def completion_key(source, amb, scenario, vbat, batfet):
    return "completion/%s/amb%.0f/%s/vbat%.4f/batfet_%s" % (
        source, amb, scenario, vbat, batfet)


def expected_thermal_population():
    """{key: the physical content that key must carry}."""
    p = PRIMITIVES
    lo = p["bq.vlowv_max_V"]
    out = {}
    for c in EXPECTED_QUALIFIED_SOURCE_CLASSES:
        for a in EXPECTED_COMPLETION_AMBIENTS_C:
            for name, w in EXPECTED_COMPLETION_SCENARIOS:
                for k in range(EXPECTED_COMPLETION_STEPS + 1):
                    vb = lo + (ORACLE_VBATREG_V - lo) * k / float(
                        EXPECTED_COMPLETION_STEPS)
                    for bf in oracle_batfet_states(vb):
                        out[completion_key(c, a, name, vb, bf)] = dict(
                            source=c, amb=a, p_sys=w, vbat=round(vb, 6),
                            batfet=bf, ilim="min", ichg="min", hist=None,
                            sweep=p["bq.branch_threshold_sweep"],
                            treg_C=oracle_treg_band()[0])
    return out


def thermal_population_problems(thermal_states):
    why = []
    want = expected_thermal_population()
    why += _multiset_problems("thermal population",
                              [st.get("domain_key") for st in thermal_states],
                              list(want))
    bad = 0
    regimes = {}
    for st in thermal_states:
        w = want.get(st.get("domain_key"))
        th = st.get("thermal") or {}
        regimes[th.get("regime")] = regimes.get(th.get("regime"), 0) + 1
        if w is None:
            continue
        p = state_content_problems(st, w)
        if th.get("ambient_C") is None or abs(th["ambient_C"] - w["amb"]) \
                > 1e-9:
            p.append("labelled %.0f C, solved at %r C" % (w["amb"],
                                                          th.get("ambient_C")))
        if th.get("treg_C") is None or abs(th["treg_C"] - w["treg_C"]) > 1e-9:
            p.append("solved at TREG %r C, the completion domain is %.1f C"
                     % (th.get("treg_C"), w["treg_C"]))
        ok, bw = charger_branch_is_valid(st)
        if not ok:
            p += bw[:4]
        if p:
            bad += 1
            if bad <= 8:
                # D-797: every problem of the state, not the first two -- a
                # wrong label behind a content mismatch is still a finding.
                why.append("thermal state %s: %s" % (st.get("domain_key"),
                                                     p[:8]))
    if bad > 8:
        why.append("... and %d more thermal states with problems" % (bad - 8))
    if not regimes.get("TREG_EQUILIBRIUM"):
        why.append("no thermally-closed state is a TREG equilibrium")
    return why, dict(expected=len(want), seen=len(thermal_states),
                     with_problems=bad, regimes=regimes)


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


# D-797 / D797-04.  THE CACHE IS KEYED BY CONTENT, NEVER BY IDENTITY.
#
# ROUND-16 (Astra R16-02): D-796 cached the regime audit by Python object
# IDENTITY, so a list that had PASSED once and was then mutated IN PLACE was
# handed back its old PASS.  The regime audit re-checks thousands of rows and
# every F14 mutation that does not touch the regime hands the same content
# back, so a cache is still worth having -- keyed by a SHA-256 over a
# deterministic serialisation of every argument, taken at LOOKUP time.  An
# in-place edit changes the bytes, misses, and is re-audited.  Nothing is
# kept but the digest and the verdict.
_REGIME_CACHE = []


def content_digest(*objs):
    """SHA-256 of a deterministic serialisation of `objs`.  Pickle protocol 4
    of the same content in the same insertion order is byte-identical; any
    other difference can only cause a MISS, which is safe."""
    import hashlib
    import pickle
    h = hashlib.sha256()
    for o in objs:
        h.update(pickle.dumps(o, protocol=4))
    return h.hexdigest()


def _regime_problems_cached(rows, published, scalars):
    key = content_digest(rows, published, dict(sorted(scalars.items())))
    for k_, res in _REGIME_CACHE:
        if k_ == key:
            return list(res[0]), dict(res[1])
    res = regime_problems(rows, published, scalars)
    _REGIME_CACHE.append((key, (list(res[0]), dict(res[1]))))
    del _REGIME_CACHE[:-4]
    return list(res[0]), dict(res[1])


def completeness(transitions, charger_states, rejected_post_states,
                 residual_worst_W, residual_worst_V, network_states=(),
                 charger_refusals=None, regime_rows=None,
                 regime_published=None, thermal_states=None, scalars=None,
                 network_terms=None):
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
        rp, regime_extra = _regime_problems_cached(
            regime_rows, regime_published, scalars or {})
        problems += rp
    thermal_extra = {}
    if not thermal_states:
        problems.append("no thermally-closed charger state was handed to the "
                        "oracle, so the TREG branch was never checked")
    else:
        if "TREG" not in thermal_branches:
            problems.append("no thermally-closed state exercises TREG")
        tp, thermal_extra = thermal_population_problems(thermal_states)
        problems += tp
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
    # ---- D-796 / R15-02: every network key IS its load set and corner ----
    problems += network_terms_agree(network_terms)
    net_bad = 0
    if isinstance(network_terms, dict):
        for n in network_states:
            w = network_row_problems(n, network_terms, scalars or {})
            if w:
                net_bad += 1
                if net_bad <= 8:
                    problems += w[:2]
    if net_bad > 8:
        problems.append("... and %d more network rows with problems"
                        % (net_bad - 8))
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
        # D-796 / R15-02 (PM2 class): the canary's physics must be the
        # canary's own load set -- the named state at the named accessory.
        if isinstance(network_terms, dict):
            ls = c.get("load_set") or {}
            if ls.get("accessory") != CANARY_ACCESSORY:
                problems.append("the seeded canary names accessory %r, not "
                                "%r" % (ls.get("accessory"), CANARY_ACCESSORY))
            problems += load_set_problems(
                "seeded canary", ls, REQUIRED_SEEDED_REJECTION.split("/")[1],
                CANARY_ACCESSORY, network_terms, scalars or {})
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
        thermal_population=thermal_extra,
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
          regime_rows=None, regime_published=None, thermal_states=None,
          network_terms=None):
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
                                 scalars=scalars,
                                 network_terms=network_terms)
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
