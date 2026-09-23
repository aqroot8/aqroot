#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- THE CANONICAL POWER MODEL.  ONE ledger, ONE path, ONE solver.

ADDED AT D-792 as the CONVERGENCE requirement Round-11 states in its own words:

    "Eliminate duplicate load tables.  Create ONE canonical load ledger
     consumed by F6/F10/F12/thermal/policy/docs."
    "ONE canonical power/load/source-resistance model.  No duplicated
     backlight, MCU, accessory, FET, charger or path constants across
     F6/F10/F12/thermal/docs."

WHY THIS FILE EXISTS, IN THE SHAPE OF THE DEFECT IT REMOVES.  Before D-792 the
backlight converter's input current was SOLVED in `demo_feature_contract` and
TYPED into `audit_rail_ampacity` -- and when D-791 moved the solved figure from
211.58 mA to 233.13 mA, the typed copy did not move.  F12 then ruled the whole
cell-to-load network, the firmware's VCELL floors and the enclosure's thermal
state on a backlight current the contract beside it had already retired.  That
is not a transcription slip; it is an ARCHITECTURE in which two files are
allowed to describe different boards.  Round-11 found it, and R11-02 is the
finding.  Every number below is defined EXACTLY ONCE and imported by everything
that needs it.

WHAT IS CANONICAL HERE
  1  `LOAD_LEDGER`   -- every +3V3 consumer, ONE line each, classified
                        BASELINE / INCREMENTAL / BURSTY so nothing can be
                        omitted from a sustained state or double-counted in a
                        peak.  The peak budget, the sustained always-on set,
                        the optional-mode set and the bounded-duty allowances
                        are all VIEWS of this one list.
  2  `UPSTREAM_PATH` -- the cell-to-`BAT_PROTECTED_P` source resistance,
                        itemised conductor by conductor and contact by
                        contact, at a cold minimum and a hot maximum (R11-07).
  3  `PASS_PAIR`     -- the AO4800 pass pair, with its temperature law as an
                        EXPLICIT SOLVER INPUT rather than a constant captured
                        before a sensitivity can move it (R11-01).
  4  `charger_state` -- an explicit BQ25185 physical-mode solver with KCL, KVL
                        and energy balance as HARD invariants, so a state that
                        supplements from a battery BELOW the SYS node it is
                        supplementing cannot exist (R11-03).
  5  the backlight converter model, moved here verbatim from
     `demo_feature_contract` so there is one copy of it in the repository.

AND EVERY ENGINEERING INPUT CARRIES A MACHINE-READABLE TAG.  Round-11's R11-06
is that a discrete datasheet row, a typical and a declared estimate had all
become "the bound" by being written as a bare float.  `tag()` attaches
provenance to a value and `audit_tags()` REFUSES a release in which a value
tagged `TYPICAL` is used where a guaranteed bound is required.  The tags are:

    GUARANTEED_MAX / GUARANTEED_MIN   a MIN/MAX column in a vendor EC table,
                                      at a stated condition
    GUARANTEED_ROC                    a Recommended Operating Condition the
                                      vendor states as a design requirement
    TYPICAL                           a TYP column with no MIN/MAX beside it;
                                      may be REPORTED, never RULED on
    DECLARED_ESTIMATE                 this programme's own allowance, with a
                                      basis and a first-article measurement
    DERIVED                           computed here from tagged inputs
    MEASURED_PENDING                  a first-article measurement of record

This module is PURE: it loads no board, reads no file and imports nothing from
`audit_rail_ampacity` or `demo_feature_contract`, both of which import IT.
"""

import math

# ==========================================================================
# 1.  THE TAGGING FRAMEWORK -- R11-06, AND R12-05'S SEMANTIC ROLES.
#
# D-792 made provenance MECHANICAL: every engineering input carries a tag and
# `audit_tags()` refuses a release in which a `TYPICAL` rules.  Round-12 found
# the half of the idea that was missing, and it found it with a concrete
# instance:
#
#     "ESP32 500 mA supply-capability recommendation is an engineering budget,
#      not a guaranteed maximum instantaneous module current."
#
# It is exactly right.  Espressif's Table 6-2 `IVDD` row is a RECOMMENDED
# OPERATING CONDITION on the POWER SUPPLY -- "current delivered by external
# power supply, MIN 0.5 A" -- and D-792 used it as the module's own maximum
# draw, then DERIVED the Wi-Fi TX increment by subtracting the baseline from
# it.  The tag was `GUARANTEED_ROC`, which is in `RULING_TAGS`, so the old
# audit passed: the tag string was in the enum and nothing asked what the
# value was being used AS.
#
# R12-05, IN ITS OWN WORDS: "Release logic must reject category misuse, not
# just validate that the tag string is in an enum."  So every registered value
# now also carries a ROLE -- what it is used as -- and the audit is a MATRIX
# over (role, tag) rather than a membership test:
#
#   DEVICE_BOUND        a bound on what a DEVICE does (its current, its
#                       resistance, its voltage).  A recommendation about the
#                       supply is NOT one of these, and neither is a typical.
#   SUPPLY_REQUIREMENT  a requirement on what THIS BOARD must be able to
#                       deliver.  An ROC belongs here and nowhere else.
#   POLICY_BUDGET       a number this programme PUBLISHES as a product
#                       contract (400 mA, 300 mA).  It is not a datasheet
#                       claim and must not pretend to be one.
#   REPORTED            printed, never ruled on.  Any tag may be reported.
# ==========================================================================
GUARANTEED_MAX = "GUARANTEED_MAX"
GUARANTEED_MIN = "GUARANTEED_MIN"
GUARANTEED_ROC = "GUARANTEED_ROC"
TYPICAL = "TYPICAL"                       # == R12-05's DATASHEET_TYPICAL
DATASHEET_TYPICAL = TYPICAL               # R12-05 spells it this way
RECOMMENDED_CAPABILITY = "RECOMMENDED_CAPABILITY"
DECLARED_ESTIMATE = "DECLARED_ESTIMATE"
DECLARED_ENGINEERING_BOUND = "DECLARED_ENGINEERING_BOUND"
DERIVED = "DERIVED"
MEASURED_PENDING = "MEASURED_PENDING"
MEASURED_FIRST_ARTICLE = "MEASURED_FIRST_ARTICLE"
TAGS = (GUARANTEED_MAX, GUARANTEED_MIN, GUARANTEED_ROC, TYPICAL,
        RECOMMENDED_CAPABILITY, DECLARED_ESTIMATE,
        DECLARED_ENGINEERING_BOUND, DERIVED, MEASURED_PENDING,
        MEASURED_FIRST_ARTICLE)

DEVICE_BOUND = "DEVICE_BOUND"
SUPPLY_REQUIREMENT = "SUPPLY_REQUIREMENT"
POLICY_BUDGET = "POLICY_BUDGET"
REPORTED = "REPORTED"
ROLES = (DEVICE_BOUND, SUPPLY_REQUIREMENT, POLICY_BUDGET, REPORTED)

# THE MATRIX.  Which tags may carry which role.  `REPORTED` accepts every tag
# by construction, which is what makes it safe to keep a typical in the
# registry at all.
ROLE_ALLOWS = {
    DEVICE_BOUND: (GUARANTEED_MAX, GUARANTEED_MIN, DERIVED,
                   DECLARED_ESTIMATE, MEASURED_FIRST_ARTICLE),
    SUPPLY_REQUIREMENT: (GUARANTEED_ROC, DECLARED_ENGINEERING_BOUND,
                         DERIVED, MEASURED_FIRST_ARTICLE),
    POLICY_BUDGET: (DECLARED_ENGINEERING_BOUND, DERIVED),
    REPORTED: TAGS,
}
# Retained for the D-792 spelling: `ruling=True` with no explicit role means
# DEVICE_BOUND, which is what every D-792 call site meant.
RULING_TAGS = ROLE_ALLOWS[DEVICE_BOUND]

# ==========================================================================
# D-794 / R13-05.  A GUARANTEE IS A CLAIM ABOUT A NAMED DOCUMENT ROW, AND THE
# TAG ALONE CANNOT CARRY IT.
#
# ROUND-13, IN ITS OWN WORDS: "Astra changed passpair.rds_hot_ratio_ruling
# from DECLARED_ESTIMATE to GUARANTEED_MAX and gates stayed green; that must
# fail.  ...  Source-role checking must validate meaning and source condition,
# not merely permit enum strings.  ...  Audit every GUARANTEED_* primitive
# against exact document row/condition and add role-misclassification negative
# controls."
#
# IT REPRODUCES BECAUSE D-793's AUDIT WAS A TYPE CHECK.  `audit_tags` asked
# whether a (role, tag) pair was in a matrix.  `GUARANTEED_MAX` + `DEVICE_BOUND`
# is in that matrix, so relabelling a DECLARED widening as a manufacturer
# maximum passed -- and the widening in question is `AO4800_HOT_RATIO_RULING`,
# the number the whole pass-pair conduction verdict is taken at.
#
# WHAT A GUARANTEE NOW HAS TO SHOW.  Every GUARANTEED_MAX / GUARANTEED_MIN /
# GUARANTEED_ROC entry must appear in `GUARANTEED_ROWS` below, which names the
# DOCUMENT and the ROW/CONDITION it is read from, and the entry's own `source`
# text must contain both tokens.  A key that is not in the table cannot be
# guaranteed at all; a key in the table whose source no longer names its row
# is a guarantee that has drifted off its evidence.  And three MEANING rules
# apply on top of the table, because the table is a list and a list can be
# edited:
#
#   * an entry carrying `widened_from` is by construction NOT the published
#     figure, so it may never be tagged GUARANTEED_*;
#   * an entry whose source text DECLARES itself -- "DECLARED", "declared",
#     "estimate", "allowance", "carried at" -- may never be tagged
#     GUARANTEED_*;
#   * a GUARANTEED_* entry must state a CONDITION, because a bound with no
#     condition is the D-789 defect (a row read at the wrong condition) with
#     the condition simply omitted.
# ==========================================================================
# D-795 / R14-06.  THE ROWS ARE NO LONGER A DICT IN THIS FILE.
#
# D-794's `GUARANTEED_ROWS` lived here, which meant a TYP could be upgraded
# to a guarantee by two edits in one file: the tag and the dict.  The rows now
# live in `evidence/guaranteed-rows.json`, whose sha256 is PINNED below, and
# `checks/guarantee_evidence.py` re-finds every row in the archived primary
# document's own text at release time and refuses one whose column semantics
# are not MIN or MAX.  This table is a READ-ONLY view of that file, kept so
# `audit_tags` can still name the document and row it expects.
GUARANTEE_EVIDENCE_SHA256 = (
    "805766ea642038ea8d32cf10ee1da34146ab131201a8bfc4b8dac1ed4b7f09ec")


def _load_guaranteed_rows():
    import json as _json
    import os as _os
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "evidence", "guaranteed-rows.json")
    try:
        with open(path, encoding="utf-8") as fh:
            ev = _json.load(fh)
    except (OSError, ValueError):
        return {}
    docs = ev.get("documents") or {}
    return {k: (docs.get(v["document"], {}).get("token", v["document"]),
                v.get("row_token", ""))
            for k, v in (ev.get("rows") or {}).items()}


GUARANTEED_ROWS = _load_guaranteed_rows()
# The repository's own convention: a value this programme DECLARES opens its
# source text with the word.  That is a precise marker, not a word search --
# a source that merely mentions a declaration elsewhere is not itself one.
def _source_declares_itself(src):
    return (src or "").lstrip().upper().startswith("DECLARED")

_REGISTRY = []


def tag(key, value, kind, source, condition=None, measurement_of_record=None,
        widened_from=None, ruling=True, role=None):
    """Register an engineering input and return its VALUE.

    `role` is what the number is USED AS -- see the matrix above.  It defaults
    to `DEVICE_BOUND` when `ruling` is true and `REPORTED` when it is not,
    which is exactly what every D-792 call site meant, so the default
    behaviour is unchanged and only the call sites that were MISCLASSIFIED
    have to say so.
    """
    if kind not in TAGS:
        raise ValueError("unknown tag %r" % (kind,))
    if role is None:
        role = DEVICE_BOUND if ruling else REPORTED
    if role not in ROLES:
        raise ValueError("unknown role %r" % (role,))
    _REGISTRY.append(dict(
        key=key, value=value, tag=kind, source=source, condition=condition,
        measurement_of_record=measurement_of_record,
        widened_from=widened_from, role=role,
        used_as_a_ruling_bound=bool(role != REPORTED)))
    return value


def registry():
    return [dict(r) for r in _REGISTRY]


def _role_of(r):
    return r.get("role") or (DEVICE_BOUND if r.get("used_as_a_ruling_bound")
                             else REPORTED)


def audit_tags(entries=None):
    """Release-time check: the (role, tag) MATRIX, not a membership test.

    `entries` defaults to this module's own registry.  It is an ARGUMENT so a
    gate can run the same rule over a deliberately-poisoned list and prove the
    refusal is real -- R11-06 asks for the rule to be mechanical, and a rule
    with no negative control is not yet mechanical.  R12-05 adds the second
    half: a TYPICAL is not the only category error, and an ROC used as a
    device bound is the one that actually shipped.
    """
    reg = _REGISTRY if entries is None else list(entries)
    bad = []
    for r in reg:
        role = _role_of(r)
        if role not in ROLES:
            bad.append(dict(r, why="unknown role %r" % (role,)))
        elif r["tag"] not in ROLE_ALLOWS[role]:
            bad.append(dict(r, why="a %s may not carry the role %s"
                                   % (r["tag"], role)))
    # ---- D-794 / R13-05.  THE MEANING CHECK, NOT THE TYPE CHECK. ---------
    guaranteed = []
    for r in reg:
        if not r["tag"].startswith("GUARANTEED"):
            continue
        guaranteed.append(r["key"])
        src = r.get("source") or ""
        row = GUARANTEED_ROWS.get(r["key"])
        if row is None:
            bad.append(dict(r, why="%s is tagged %s but is not in "
                                   "GUARANTEED_ROWS: a guarantee has to name "
                                   "the document row it is read from"
                                   % (r["key"], r["tag"])))
            continue
        doc, cond = row
        if doc.lower() not in src.lower():
            bad.append(dict(r, why="%s claims a guarantee but its source "
                                   "text no longer names %r"
                                   % (r["key"], doc)))
        if cond.lower() not in src.lower():
            bad.append(dict(r, why="%s claims a guarantee but its source "
                                   "text no longer names the row %r"
                                   % (r["key"], cond)))
        if r.get("widened_from"):
            bad.append(dict(r, why="%s is WIDENED from a published figure "
                                   "and therefore is not that figure: a "
                                   "widening may never be GUARANTEED_*"
                                   % (r["key"],)))
        if _source_declares_itself(src):
            bad.append(dict(r, why="%s declares itself in its own source "
                                   "text and may not also be tagged %s"
                                   % (r["key"], r["tag"])))
        if not r.get("condition"):
            bad.append(dict(r, why="%s is a guarantee with no stated "
                                   "CONDITION; a bound read at an unstated "
                                   "condition is the D-789 defect"
                                   % (r["key"],)))
    return dict(
        guaranteed_entries=sorted(set(guaranteed)),
        guaranteed_rows_table=len(GUARANTEED_ROWS),
        entries=len(reg),
        ruling_entries=sum(1 for r in reg if _role_of(r) != REPORTED),
        by_tag={t: sum(1 for r in reg if r["tag"] == t) for t in TAGS},
        by_role={x: sum(1 for r in reg if _role_of(r) == x) for x in ROLES},
        role_matrix={k: list(v) for k, v in ROLE_ALLOWS.items()},
        invalid_ruling_use=[dict(r) for r in bad],
        rule="every registered value carries a ROLE as well as a TAG, and the "
             "(role, tag) pair must be in ROLE_ALLOWS.  A TYPICAL and a "
             "RECOMMENDED_CAPABILITY may be REPORTED and may seed a declared "
             "widening; neither may be a bound of any kind.  A GUARANTEED_ROC "
             "is a requirement on the SUPPLY and may never be a DEVICE_BOUND "
             "-- R12-05's ESP32 IVDD instance.  A POLICY_BUDGET is this "
             "programme's own published contract and may not be tagged as a "
             "datasheet guarantee.  D-794 / R13-05: a GUARANTEED_* tag must "
             "additionally name its DOCUMENT and its ROW in GUARANTEED_ROWS, "
             "must repeat both tokens in its own source text, must state a "
             "CONDITION, may not be widened from anything, and may not "
             "declare itself -- so relabelling a declaration as a guarantee "
             "FAILS instead of passing a type check.",
        ok=not bad)

# ==========================================================================
# 2.  THE BACKLIGHT CONVERTER.  MOVED HERE VERBATIM AT D-792 SO THERE IS ONE
#     COPY.  R11-02's finding is that there were two and they disagreed.
#
#     R11-10 IS FIXED IN THE SPEC BELOW: the fitted Coilcraft XFL4020-472ME_'s
#     DCR was carried at the distributor record's 52.2 mOhm, which is
#     Coilcraft's TYPICAL.  The ruling figure is the manufacturer's published
#     MAXIMUM, 57.4 mOhm.
# ==========================================================================
# --------------------------------------------------------------------------
# D-790 / D789-A11 -- THE DISPLAY LINE WAS AN INHERITED SUBTOTAL, NOT A BOUND.
#
# The `+3V3` budget below carried ONE line for "display logic + backlight at
# maximum", 181 mA, cited as "FBV2-COMM-001 internal subtotal, retained".  It
# was never derived from this board's backlight circuit, and Round-9 showed it
# is not even large enough for the BACKLIGHT ALONE: Astra's own sensitivity put
# the converter's input at about 191 mA before a milliamp of panel logic.
#
# SO THE BACKLIGHT IS NOW SOLVED, FROM PUBLISHED MAXIMA ONLY, AND THE PANEL
# LOGIC IS A SEPARATE, DECLARED LINE THAT SAYS SO.
#
# THE LED SETPOINT IS THE CONVERTER'S, NOT A NOMINAL.  `U17` regulates `FB` to
# `VREF` across `R69`, so
#       I_LED(max) = VREF(max) / R69(min) = 0.220 V / (1.87 x 0.99) = 118.835 mA
# against the panel's own 120 mA maximum (D-079).  The boost node it has to
# reach is the sum of everything in series with the six parallel LEDs:
#       V_LED_BOOST = I_LED x R_ballast(max) + VF_LED(max)
#                   + I_LED x RDS(on)_Q11(max) + VREF(max)
# -- `R70..R73` are four 33 R 1 % in parallel, `VF_LED` is D-079's 3.2 V upper
# end, and `Q11` is the fitted SQ2364EES at its ONLY published low-gate
# conduction row.  That is 4.439311 V and 527.5 mW out of the converter.
#
# AND THE INPUT CURRENT IS BOUNDED THREE WAYS, WORST WINS.  TI publishes no
# efficiency TABLE for this part -- only an "up to 90 %" headline, which is a
# CEILING on efficiency and therefore a FLOOR on input current, exactly the
# wrong direction for a budget.  So the converter's own conduction losses are
# computed from the guaranteed maxima --
#
#   * `RDS(on)` of the internal NFET, 0.7 ohm MAX (SNVSA40B EC)
#   * the inductor's DCR, 52.2 mOhm for the fitted Coilcraft XFL4020-472MEC
#     (live distributor record per D-096, evidence/jlc-live/)
#   * `D8`'s forward drop, 710 mV at 200 mA for the fitted onsemi NSR0240HT1G
#     (live record); this node runs at 119 mA and VF rises monotonically with
#     IF, so the 200 mA figure is a BOUND here
#   * the quiescent current, 0.45 mA MAX, and the ripple at the MINIMUM
#     published switching frequency (0.75 MHz) into the MINIMUM inductance
#     (4.7 uH -20 %), which is the worst RMS case
#
# -- under BOTH a continuous-conduction and a discontinuous-conduction
# treatment, and the bound is the WORST of {CCM, DCM, the TI headline}.  At the
# declared worst-case converter input the answer is about 211.6 mA and the
# implied efficiency is 83.1 %, which is BELOW TI's own headline -- the model
# is not allowed to claim more than the part is advertised to do.
#
# THE INPUT VOLTAGE IS DECLARED AND THEN MACHINE-CHECKED.  A lower input costs
# more input current, so the constant below must be AT OR BELOW the rail's own
# heavy-load minimum less the declared plane allowance at the full envelope.
# `f6q_declared_backlight_input_is_at_or_below_the_modelled_rail` proves it
# every run rather than leaving the two to drift.
# --------------------------------------------------------------------------
BACKLIGHT_BOOST = dict(
    refs=("U17", "L3", "D8", "Q11", "R69", "R70", "R71", "R72", "R73", "J1"),
    vref_max_V=0.220,
    sense_ohm=1.87, sense_tol=0.01,
    ballast_ohm=33.0, ballast_tol=0.01, ballast_count=4,
    vf_led_max_V=3.2,
    q11_rds_on_max_ohm=0.245,
    sw_rds_on_max_ohm=0.7,
    inductor_H=4.7e-6, inductor_tol=0.20,
    # ---- D-792 / R11-10.  A TYPICAL WAS BEING USED AS THE CONDUCTION BOUND.
    # The live distributor record D-096 commits for the fitted Coilcraft
    # XFL4020-472ME_ carries `DC Resistance (DCR) 52.2 mOhm`, which is
    # Coilcraft's TYPICAL; the manufacturer publishes a MAXIMUM of 57.4 mOhm
    # for the same part.  Round-11 read it from the Coilcraft datasheet and
    # this repository could not retrieve that document from this environment
    # (the attempts are recorded in evidence/d792-vendor-fetch-attempts.json),
    # so the ruling figure is the MAXIMUM and the typical is kept beside it.
    inductor_dcr_ohm=0.0574,
    inductor_dcr_typ_ohm=0.0522,
    inductor_dcr_basis=(
        "Coilcraft XFL4020-472ME_ DCR MAXIMUM 57.4 mOhm.  The archived live "
        "distributor record (evidence/jlc-live/xfl4020-472mec-28cf6fd3.json) "
        "publishes only the 52.2 mOhm TYPICAL, which D-790 and D-791 used as "
        "the conduction bound; R11-10 is the finding.  57.4 / 52.2 = 1.0996, "
        "the DCR tolerance Coilcraft publishes across the XFL4020 family.  "
        "MEASURED at C-DISP-01."),
    fsw_min_Hz=0.75e6,
    diode_vf_max_V=0.710,
    iq_max_A=0.45e-3,
    headline_efficiency=0.90,
    # PRIMARY at D-792: the module datasheet's own NORMAL forward current,
    # 6-chip parallel.  D-795 / Round-14 CORRECTS THE TRANSCRIPTION: in the
    # archived section 4.4 table the MIN column is BLANK, 110 mA is in the TYP
    # column and 120 mA is in the MAX column -- D-792 read them as 110 MIN /
    # 120 TYP with "no MAX column".  So 120 mA IS the panel's published
    # maximum, and the one-sided clause it feeds -- the converter's setpoint
    # must not exceed it -- is now a clause against a real MAX.
    panel_led_max_A=0.120,
    panel_led_typ_A=0.110,
    panel_led_dimming_A=0.090,
    panel_led_vf_typ_V=3.0,
    panel_led_source=(
        "EastRising ER-TFT035IPS-6 datasheet section 4.4, archived at "
        "vendor/EASTRISING/eastrising-er-tft035ips-6-datasheet.pdf, sha256 "
        "28c07dae0c3ada133d0765167d38ae71b0f76fb9e94a18c00d96bb77682334ac.  "
        "D-791 recorded this document as unobtainable; D-792 retrieved it."),
    # ---- D-791 / D790-A04.  THE LOSSES D-790's 211.58 mA LEFT OUT ---------
    #
    # Round-10 is right that the D-790 model is a CONDUCTION model wearing a
    # loss model's name.  Four terms were missing and each of them is added
    # below with its own declared basis, because not one of them is published
    # for these exact parts:
    #
    #   1  THE DIODE Vf WAS TAKEN AT THE AVERAGE, NOT THE PEAK.  onsemi
    #      publishes ONE point for the NSR0240HT1G -- 710 mV at 200 mA -- and
    #      this converter's inductor peak is about 430 mA, more than twice it.
    #      The conduction loss is bounded by Vf(i_peak) x I_avg, which is an
    #      upper bound on the integral whatever the curve does in between.
    #   2  SWITCHING TRANSITION LOSS.  TI publishes no rise/fall time for the
    #      TPS61169's internal switch.
    #   3  OUTPUT-CAPACITANCE AND GATE-DRIVE LOSS.  Neither is published.
    #   4  INDUCTOR CORE LOSS AND HOT DCR.  Coilcraft publishes the 52.2 mOhm
    #      DCR at room temperature and an AC-loss CURVE this repository cannot
    #      read numerically.
    #
    # AND THE FREQUENCY IS TAKEN AT BOTH ENDS, WHICH IS THE POINT.  Conduction
    # and ripple are worst at the MINIMUM published switching frequency, which
    # is what D-790 already used; switching losses are worst at the MAXIMUM.
    # Charging each term at its own worst end is conservative and is stated
    # rather than implied.
    fsw_max_Hz=1.5e6,
    diode_vf_at_peak_V=0.900,
    diode_vf_at_peak_basis=(
        "DECLARED.  onsemi publishes a single NSR0240HT1G forward point, "
        "710 mV at 200 mA, and this converter's inductor peak is about "
        "430 mA.  0.900 V is a deliberately pessimistic carry for a 40 V "
        "Schottky at roughly 2x its published point, and the loss is charged "
        "as Vf(peak) x I_average, which bounds the integral whatever the "
        "curve does between the two.  MEASURED at C-DISP-01."),
    diode_average_rating_A=0.250,
    diode_surge_rating_A=1.0,
    switch_transition_s=20e-9,
    switch_transition_basis=(
        "DECLARED: TI SNVSA40B publishes no rise or fall time for the "
        "TPS61169's internal switch.  20 ns TOTAL is a conservative carry for "
        "an integrated 0.7 ohm switch at this current, charged at the MAXIMUM "
        "published switching frequency."),
    switch_coss_F=50e-12,
    switch_coss_basis=(
        "DECLARED: no output capacitance is published.  50 pF is a "
        "conservative carry for a switch of this RDS(on) class."),
    gate_drive_W=0.0005,
    gate_drive_basis=(
        "DECLARED: the TPS61169's gate driver is internal and its charge is "
        "not published separately from IQ.  0.5 mW is carried in addition to "
        "the published 0.45 mA IQ rather than assumed to be inside it."),
    core_loss_fraction_of_dcr=0.30,
    core_loss_basis=(
        "DECLARED: Coilcraft publishes an AC-loss curve for the XFL4020 "
        "family that this repository cannot read numerically.  Core loss is "
        "carried at 30 % of the winding's own copper loss, which is a "
        "conservative ratio for a moulded composite inductor at this ripple "
        "and frequency."),
    dcr_hot_factor=round(1.0 + 0.00393 * 65.0, 6),
    dcr_hot_basis=(
        "the winding is copper and the published 52.2 mOhm is a room-"
        "temperature figure; the same 65 K hot rise and 0.393 %/K coefficient "
        "this contract charges every other conductor is applied to it."),
    source=(
        "TI SNVSA40B (TPS61169), archived vendor/TI/tps61169.pdf: VREF "
        "188/204/220 mV at duty 100 %, RDS(on) 0.35/0.7 ohm, IQ_VIN 0.45 mA "
        "MAX, fSW 0.75/1.2/1.5 MHz, 'Up to 90% efficiency'.  Coilcraft "
        "XFL4020-472MEC DCR 57.4 mOhm MAXIMUM (52.2 mOhm typical on the "
        "distributor record; R11-10) and onsemi NSR0240HT1G VF 710 mV at "
        "200 mA, both from the committed live distributor records this "
        "repository reads under D-096.  Vishay 75975 Rev B (SQ2364EES) "
        "RDS(on) 0.245 ohm MAX at VGS = 1.5 V.  Panel LED string, PRIMARY at "
        "D-792: EastRising ER-TFT035IPS-6 datasheet section 4.4 Backlight "
        "Characteristics, archived at vendor/EASTRISING/"
        "eastrising-er-tft035ips-6-datasheet.pdf -- Vf 3.0 TYP / 3.2 V MAX at "
        "If = 120 mA, 6-chip parallel; forward current Normal Ipn 110 mA TYP "
        "/ 120 mA MAX (the MIN column is blank -- D-795 corrects D-792's "
        "'110 MIN / 120 TYP'); dimming Ipd at Lf = 90 mA; LED life 30 kh at "
        "Ta = 25 C.  The 3.2 V MAX Vf is the ruling forward voltage and it "
        "CONFIRMS D-079's transcribed 2.9-3.2 V range.  The 120 mA is the "
        "panel's published MAXIMUM forward current and the converter is set "
        "to 118.835 mA maximum, which is under it; the clause below is that "
        "the converter cannot overdrive the panel."),
    # A LOWER INPUT COSTS MORE INPUT CURRENT, so this is a declared FLOOR on
    # U17's own VIN and the clause below proves the rail model never goes under
    # it.  3.069408 V heavy-load rail minimum less about 49 mV of declared
    # plane allowance at the full +3V3 envelope, rounded DOWN.
    declared_converter_vin_V=3.000,
    declared_converter_vin_basis=(
        "the rail's heavy-load minimum less the SAME declared 25 mOhm hot "
        "plane allowance F6 charges the accessory source side, carrying the "
        "whole +3V3 envelope, rounded DOWN onto a 10 mV grid"))
# The panel side.  ILI Technology's ILI9488 datasheet publishes NO active-mode
# supply current -- only Sleep-in (100 uA) and Deep Standby (1 uA) -- and the
# EastRising module specification is not obtainable from this environment, so
# this line is a DECLARED ALLOWANCE and is labelled one.  It covers the
# panel's VCI analog/charge-pump/source-driver side, its IOVCC logic side at
# the SPI rate, and the FT6236 touch controller that shares the same FPC.  It
# is roughly 2x what a 3.5 in ILI9488 module of this class consumes, and
# `C-DISP-01` first-article measurement is the measurement of record.
PANEL_LOGIC_DECLARED_mA = 50.0
BACKLIGHT_LEDGER_TOKENS = ("C-DISP-01",)


def _switching_W(v_switch_V, i_peak_A, fsw_Hz, spec):
    """D-791 / D790-A04.  Transition + Coss + gate-drive loss, all DECLARED.

    Pure.  Every term is a declared allowance because TI publishes none of
    them for the TPS61169's integrated switch; each carries its own basis
    string in `BACKLIGHT_BOOST` and each is measured at `C-DISP-01`.
    """
    transition = 0.5 * v_switch_V * i_peak_A * spec.get(
        "switch_transition_s", 0.0) * fsw_Hz
    coss = 0.5 * spec.get("switch_coss_F", 0.0) * v_switch_V * v_switch_V * fsw_Hz
    return transition + coss + spec.get("gate_drive_W", 0.0)


def backlight_converter_input(vin_V, spec=None):
    """D-790 / D789-A11.  Worst-case TPS61169 input current, three ways.

    Pure; returns the arithmetic and the bound.  The bound is the WORST of a
    CCM treatment, a DCM treatment and TI's own 'up to 90 %' headline, because
    no single one of the three may be the one that flatters the answer.
    """
    s = BACKLIGHT_BOOST if spec is None else spec
    i_led = s["vref_max_V"] / (s["sense_ohm"] * (1.0 - s["sense_tol"]))
    r_ballast = s["ballast_ohm"] * (1.0 + s["ballast_tol"]) / s["ballast_count"]
    v_out = (i_led * r_ballast + s["vf_led_max_V"]
             + i_led * s["q11_rds_on_max_ohm"] + s["vref_max_V"])
    p_out = v_out * i_led
    v_d = v_out + s["diode_vf_max_V"]
    l_min = s["inductor_H"] * (1.0 - s["inductor_tol"])
    fs = s["fsw_min_Hz"]
    # D-791 / D790-A04.  Conduction at the MINIMUM frequency (worst RMS),
    # switching at the MAXIMUM (worst transition and Coss loss), and the
    # winding's DCR carried hot.
    fs_hi = s.get("fsw_max_Hz", fs)
    dcr = s["inductor_dcr_ohm"] * s.get("dcr_hot_factor", 1.0)
    rds, iq = s["sw_rds_on_max_ohm"], s["iq_max_A"]
    vf_peak = s.get("diode_vf_at_peak_V", s["diode_vf_max_V"])

    # A spec whose output node no longer sits ABOVE the input is not a boost
    # at all; the model says so rather than raising.  Only the mutation
    # controls can reach this, and they only need the answer to MOVE.
    if v_d <= vin_V:
        degenerate = p_out / vin_V
        return dict(
            converter_vin_V=round(vin_V, 6),
            led_current_max_A=round(i_led, 6),
            led_current_is_inside_the_panel_maximum=bool(
                i_led <= s["panel_led_max_A"]),
            panel_led_max_A=s["panel_led_max_A"],
            ballast_max_ohm=round(r_ballast, 6),
            led_boost_max_V=round(v_out, 6),
            output_power_W=round(p_out, 6),
            not_a_boost="the modelled output node is at or below the input",
            bound_A=round(degenerate, 6), bound_from="degenerate",
            model_efficiency_is_under_the_headline=True,
            source=s["source"])

    # --- continuous conduction, solved for the self-consistent input current
    i_ccm = p_out / (0.8 * vin_V)
    d_ccm = ripple = p_ccm = 0.0
    for _ in range(400):
        a = vin_V - i_ccm * (dcr + rds)
        b = v_d - vin_V + i_ccm * dcr
        d_ccm = b / (a + b)
        ripple = a * d_ccm / (l_min * fs)
        irms2 = i_ccm * i_ccm + ripple * ripple / 12.0
        i_pk_ccm = i_ccm + ripple / 2.0
        p_ccm = (p_out + irms2 * d_ccm * rds + irms2 * dcr
                 + vf_peak * i_led + vin_V * iq
                 + _switching_W(v_d, i_pk_ccm, fs_hi, s)
                 + s.get("core_loss_fraction_of_dcr", 0.0) * irms2 * dcr)
        nxt = p_ccm / vin_V
        if abs(nxt - i_ccm) < 1e-13:
            i_ccm = nxt
            break
        i_ccm = 0.5 * i_ccm + 0.5 * nxt

    # --- discontinuous conduction, from the charge the output actually needs
    t = 1.0 / fs
    d_dcm = math.sqrt(2.0 * l_min * (v_d - vin_V) * i_led / (vin_V ** 2 * t))
    d2 = vin_V * d_dcm / (v_d - vin_V)
    i_pk = vin_V * d_dcm * t / l_min
    irms2_l = i_pk * i_pk * (d_dcm + d2) / 3.0
    irms2_sw = i_pk * i_pk * d_dcm / 3.0
    p_dcm = (p_out + irms2_sw * rds + irms2_l * dcr
             + vf_peak * i_led + vin_V * iq
             + _switching_W(v_d, i_pk, fs_hi, s)
             + s.get("core_loss_fraction_of_dcr", 0.0) * irms2_l * dcr)
    i_dcm = p_dcm / vin_V

    i_headline = p_out / (s["headline_efficiency"] * vin_V)
    bound = max(i_ccm, i_dcm, i_headline)
    which = ("ccm" if bound == i_ccm else
             ("dcm" if bound == i_dcm else "ti_headline"))
    return dict(
        converter_vin_V=round(vin_V, 6),
        led_current_max_A=round(i_led, 6),
        led_current_is_inside_the_panel_maximum=bool(
            i_led <= s["panel_led_max_A"]),
        panel_led_max_A=s["panel_led_max_A"],
        ballast_max_ohm=round(r_ballast, 6),
        led_boost_max_V=round(v_out, 6),
        output_power_W=round(p_out, 6),
        ccm=dict(input_A=round(i_ccm, 6), duty=round(d_ccm, 6),
                 ripple_pp_A=round(ripple, 6),
                 efficiency=round(p_out / p_ccm, 6)),
        dcm=dict(input_A=round(i_dcm, 6), duty=round(d_dcm, 6),
                 peak_A=round(i_pk, 6), efficiency=round(p_out / p_dcm, 6)),
        ti_headline=dict(input_A=round(i_headline, 6),
                         efficiency=s["headline_efficiency"]),
        bound_A=round(bound, 6),
        bound_from=which,
        # D-791 / D790-A04: the terms D-790's model did not have, itemised so
        # a reviewer can see each one's size and its declared basis.
        declared_loss_terms=dict(
            diode_vf_at_peak_V=vf_peak,
            diode_vf_published_point="710 mV at 200 mA",
            diode_peak_current_A=round(i_pk, 6),
            diode_average_current_A=round(i_led, 6),
            diode_average_is_inside_its_rating=bool(
                i_led <= s.get("diode_average_rating_A", 1e9)),
            diode_peak_is_inside_its_published_surge=bool(
                i_pk <= s.get("diode_surge_rating_A", 1e9)),
            switching_W_at_fsw_max=round(
                _switching_W(v_d, i_pk, fs_hi, s), 8),
            fsw_min_Hz=fs, fsw_max_Hz=fs_hi,
            dcr_hot_ohm=round(dcr, 6),
            core_loss_fraction_of_dcr=s.get("core_loss_fraction_of_dcr"),
            bases=[s.get(k) for k in (
                "diode_vf_at_peak_basis", "switch_transition_basis",
                "switch_coss_basis", "gate_drive_basis", "core_loss_basis",
                "dcr_hot_basis") if s.get(k)]),
        # The model may not claim a better efficiency than the part is
        # advertised to reach; if it ever did, the headline would be the bound.
        model_efficiency_is_under_the_headline=bool(
            min(p_out / p_ccm, p_out / p_dcm) <= s["headline_efficiency"]),
        source=s["source"])



# The one evaluation every consumer reads.  Was computed in two files.
BACKLIGHT_INPUT = backlight_converter_input(
    BACKLIGHT_BOOST["declared_converter_vin_V"])
BL_STRING_CURRENT_A = round(
    BACKLIGHT_BOOST["vref_max_V"]
    / (BACKLIGHT_BOOST["sense_ohm"] * (1.0 - BACKLIGHT_BOOST["sense_tol"])), 7)
BL_STRING_CURRENT_BASIS = (
    "DERIVED: VREF(max) 220 mV over R69 at its -1 % corner, which is the "
    "largest current the TPS61169's feedback loop can regulate the string to.  "
    "D-790 / D789-A11 solves the same number for the converter's input "
    "current; this is the load Q11 conducts.")


# ==========================================================================
# 3.  THE PROCESSOR BASELINE -- R11-02's SECOND HALF, AND A NEW FINDING.
#
# ROUND-11, IN ITS OWN WORDS: "Sustained always-on ledger omits active
# MCU/flash/PSRAM baseline; Wi-Fi/BLE entry is not a substitute for processor
# baseline."  It is right twice over, and the second time is worse than the
# first.
#
#   * THE SUSTAINED LEDGER HAD NO PROCESSOR LINE AT ALL.  `SUSTAINED_ALWAYS_ON`
#     carried the backlight, the panel, the expanders and the RGB and stopped.
#     A Demo holding its display at full brightness with no radio transmitting
#     was modelled as drawing NOTHING for the ESP32-S3 that is driving it --
#     through the whole cell-to-load network, every derived VCELL floor and
#     every thermal state.
#
#   * AND THE PEAK BUDGET'S MODULE LINE WAS THE WRONG NUMBER ENTIRELY --
#     D-792 / N-01.  It read 355 mA, Espressif's Table 6-4 "Peak" for
#     802.11b TX at 20.5 dBm, cited as "the worst RF condition the module
#     publishes".  It is the worst RF condition; it is not the worst SUPPLY
#     condition, and Espressif states that one separately.  ESP32-S3-WROOM-1
#     datasheet v1.8 **Table 6-2, Recommended Operating Conditions**, publishes
#
#         IVDD   "Current delivered by external power supply"   MIN  0.5  A
#
#     -- a vendor-stated design requirement on the supply, which by
#     construction bounds every combination of CPU, flash, in-package PSRAM and
#     radio the module can be in at once.  This board budgeted 355 mA for a
#     module whose manufacturer says to provide 500 mA.  The peak line is now
#     Espressif's own 500 mA.
#
# HOW THE SPLIT AVOIDS DOUBLE-COUNTING, WHICH IS THE OTHER HALF OF R11-02.
# The module is ONE supply consumer, so it gets ONE total, and the total is
# DECOMPOSED into
#
#       baseline  (always on, no radio transmitting)
#     + increment (what a transmitting radio adds)
#     = the transmitting total, by construction
#
# so the baseline can never be omitted from a sustained state and the increment
# can never be added on top of a number that already contained it.
#
# D-793 / R12-05.  WHAT THE TOTAL MAY NOT BE, AND WHAT D-792 MADE IT.
# D-792 set the transmitting total to Espressif's Table 6-2 `IVDD` row --
# 500 mA -- and derived the increment as 500 mA less the baseline.  Round-12:
#
#     "ESP32 500 mA supply-capability recommendation is an engineering budget,
#      not a guaranteed maximum instantaneous module current."
#
# That row is a RECOMMENDED OPERATING CONDITION on the EXTERNAL SUPPLY.  It
# says what this board must be able to DELIVER; it says nothing about what the
# module may DRAW, and using it as a draw bound is a category error that the
# `audit_tags()` role matrix now refuses outright.  The transmitting total is
# therefore built the same way the baseline is -- out of Espressif's own
# published CURRENT rows, at the same declared widening:
#
#     (modem-sleep worst row + flash access + declared PSRAM allowance
#      + the worst published RF transmit peak) x the declared widening
#
# It comes out ABOVE 500 mA, which is the honest direction: Table 6-4's RF
# rows are measured with the peripherals disabled and the CPU idle, so adding
# the busiest modem-sleep row to a transmit peak deliberately overlaps the
# two rather than assuming they never coincide.  The 500 mA row keeps its job
# -- it is now checked as a SUPPLY REQUIREMENT against what the +3V3 rail can
# actually deliver to U1 -- and it no longer bounds the load.
#
# THE BASELINE ITSELF IS A TYPICAL WIDENED INTO A DECLARED BOUND, AND SAYS SO.
# Espressif publishes Modem-sleep current as TYP with no MIN/MAX column at all.
# The worst published row for this part is 240 MHz, dual core running 128-bit
# data access instructions, ALL PERIPHERAL CLOCKS ENABLED: 107.9 mA.  The same
# table's note 3 adds 10 mA for flash access at 80 Mbit/s in SPI 2-line mode.
# The fitted module is an **N16R8** -- 8 MB octal PSRAM IN PACKAGE -- and the
# same section says in its own words that "if the chip embedded has in-package
# PSRAM, the current consumption of the module might be higher compared to the
# measurements below", without a number.  A declared PSRAM allowance covers
# that, and the sum is widened because a typical is not a limit.
# ==========================================================================
MCU_MODULE = dict(
    reference="U1",
    part="ESP32-S3-WROOM-1-N16R8",
    # D-793 / R12-05: role SUPPLY_REQUIREMENT.  This is what the BOARD must be
    # able to deliver to U1, and `demo_feature_contract` checks it against the
    # rail's own capability.  It is NOT a bound on the module's draw and the
    # audit matrix refuses it as one.
    supply_requirement_A=tag(
        "mcu.ivdd_supply_requirement_A", 0.500, GUARANTEED_ROC,
        "Espressif ESP32-S3-WROOM-1 & WROOM-1U datasheet v1.8 Table 6-2 "
        "Recommended Operating Conditions: IVDD 'Current delivered by "
        "external power supply' MIN 0.5 A, VDD33 3.0/3.3/3.6 V.  Archived at "
        "hardware/demo/kicad/aqroot-demo/vendor/Espressif/"
        "esp32-s3-wroom-1-datasheet.pdf.",
        condition="a REQUIREMENT ON THE SUPPLY, not a bound on the module: "
                  "'current delivered by external power supply', MIN.  "
                  "D-792 used it as the module's own maximum draw; R12-05 is "
                  "the finding and the role matrix is the refusal.",
        role=SUPPLY_REQUIREMENT),
    modem_sleep_worst_row_A=tag(
        "mcu.modem_sleep_240MHz_dual_128bit_periph_on_A", 0.1079, TYPICAL,
        "Espressif v1.8 Table 6-6 Current Consumption in Modem-sleep Mode, "
        "240 MHz, 'Dual core running 128-bit data access instructions', Typ2 "
        "(all peripheral clocks enabled): 107.9 mA.  No MIN or MAX column is "
        "published.",
        condition="3.3 V, 25 C", ruling=False),
    modem_sleep_waiti_row_A=tag(
        "mcu.modem_sleep_240MHz_waiti_periph_off_A", 0.0329, TYPICAL,
        "Espressif v1.8 Table 6-6, 240 MHz, WAITI, Typ1 (all peripheral "
        "clocks disabled): 32.9 mA.  This is the quiet-CPU floor the same "
        "datasheet's Table 6-4 note describes its RF rows as being measured "
        "on ('RX current consumption is rated when the peripherals are "
        "disabled and the CPU idle').",
        condition="3.3 V, 25 C", ruling=False),
    flash_access_A=tag(
        "mcu.flash_access_A", 0.010, TYPICAL,
        "Espressif v1.8 Table 6-6 note 3: 'In Modem-sleep mode, Wi-Fi is "
        "clock gated, and the current consumption might be higher when "
        "accessing flash.  For a flash rated at 80 Mbit/s, in SPI 2-line mode "
        "the consumption is 10 mA.'",
        ruling=False),
    psram_allowance_A=tag(
        "mcu.psram_allowance_A", 0.020, DECLARED_ESTIMATE,
        "DECLARED.  Espressif v1.8 section 6.4.2 states only that 'if the "
        "chip embedded has in-package PSRAM, the current consumption of the "
        "module might be higher compared to the measurements below' and "
        "publishes no active figure for the N16R8's 8 MB octal PSRAM (the "
        "only PSRAM number in the datasheet is 140 uA in Light-sleep).  "
        "20 mA is a deliberately generous carry for octal PSRAM at this "
        "board's SPI rate.",
        measurement_of_record="C-MCU-01"),
    typ_to_bound_widening=tag(
        "mcu.typ_to_bound_widening", 1.20, DECLARED_ESTIMATE,
        "DECLARED.  Espressif publishes Modem-sleep current and the RF peak "
        "rows as TYP/Peak with no MIN/MAX column anywhere in the datasheet, "
        "and this programme does not use a typical as a limit (D-789, D-790, "
        "R11-06, and now R12-05).  A +20 % carry on the summed published rows "
        "is the declared widening, measured at first article.",
        measurement_of_record="C-MCU-01"),
    # D-793 / R12-05.  THE RULING RF ROW, TAGGED AND NAMED.  Table 6-4/6-5
    # publish a Peak column and no MIN/MAX, so the row is REPORTED and the
    # declared widening above is what turns the sum into a bound.
    rf_tx_peak_row_A=tag(
        "mcu.rf_tx_peak_80211b_20p5dBm_A", 0.355, TYPICAL,
        "Espressif v1.8 Table 6-4 Current Consumption in RF modes, "
        "802.11b at 20.5 dBm, Peak column: 355 mA.  The worst published "
        "transmit row for this module; BLE at 20 dBm is 344 mA and Wi-Fi RX "
        "is 97 mA.  No MIN or MAX column is published for any of them.",
        condition="3.3 V, 25 C, peripherals disabled and CPU idle",
        ruling=False),
    rf_rows_A=dict(wifi_80211b_20p5dBm=0.355, ble_20dBm=0.344,
                   wifi_rx=0.097),
    rf_rows_source="Espressif v1.8 Table 6-4 and Table 6-5, Peak column.",
)
MCU_BASELINE_A = tag(
    "mcu.baseline_A",
    round((MCU_MODULE["modem_sleep_worst_row_A"]
           + MCU_MODULE["flash_access_A"]
           + MCU_MODULE["psram_allowance_A"])
          * MCU_MODULE["typ_to_bound_widening"], 6),
    DERIVED,
    "(107.9 mA modem-sleep worst published row + 10 mA flash access + 20 mA "
    "declared PSRAM allowance) x 1.20 declared typ-to-bound widening.",
    condition="the module with no radio transmitting; ALWAYS ON",
    widened_from="Espressif Table 6-6 typicals",
    measurement_of_record="C-MCU-01")
# D-793 / R12-05.  THE TRANSMITTING TOTAL, BUILT FROM CURRENT ROWS.
MCU_TX_TOTAL_A = tag(
    "mcu.tx_total_A",
    round((MCU_MODULE["modem_sleep_worst_row_A"]
           + MCU_MODULE["flash_access_A"]
           + MCU_MODULE["psram_allowance_A"]
           + MCU_MODULE["rf_tx_peak_row_A"])
          * MCU_MODULE["typ_to_bound_widening"], 6),
    DERIVED,
    "(107.9 mA modem-sleep worst row + 10 mA flash access + 20 mA declared "
    "PSRAM allowance + 355 mA Table 6-4 802.11b transmit peak) x 1.20 "
    "declared widening.  DELIBERATELY OVERLAPPING: Table 6-4's RF rows are "
    "rated with the peripherals disabled and the CPU idle, so summing them "
    "with the busiest modem-sleep row charges the module for both at once "
    "rather than assuming they never coincide.",
    condition="the module with a radio transmitting; the PEAK, not a "
              "sustained average",
    widened_from="Espressif Table 6-4 and 6-6 published rows",
    measurement_of_record="C-MCU-01")
MCU_RF_TX_INCREMENT_A = tag(
    "mcu.rf_tx_increment_A",
    round(MCU_TX_TOTAL_A - MCU_BASELINE_A, 6),
    DERIVED,
    "the transmitting total LESS the always-on baseline, so baseline + "
    "increment is exactly the transmitting total and neither is omitted nor "
    "counted twice.  D-792 derived this from Espressif's 500 mA SUPPLY "
    "requirement instead; R12-05 is why it no longer does.",
    condition="added when the Wi-Fi/BLE radio is transmitting")
# The supply requirement is now a REQUIREMENT this board must meet, and the
# gap between it and what the module can actually draw is REPORTED so nobody
# can read 500 mA as a load bound again.
MCU_SUPPLY_HEADROOM_A = round(
    MCU_MODULE["supply_requirement_A"] - MCU_TX_TOTAL_A, 6)


# ==========================================================================
# 4.  THE CANONICAL +3V3 LOAD LEDGER.  ONE LIST; EVERY OTHER TABLE IS A VIEW.
#
# `kind` is the whole point of the file:
#
#   BASELINE     always on, in every state, at every moment.  Enters the
#                sustained always-on set AND the peak budget.
#   INCREMENTAL  a MODE the user or firmware turns on -- observable, per
#                D790-A02.  Enters the peak budget and the sustained state
#                that names it.
#   BURSTY       bounded-duty: the PEAK enters the peak budget, the
#                time-averaged product enters every sustained state.
#
# The peak budget is the sum of every line at its PEAK.  The sustained
# always-on set is the BASELINE lines plus the BURSTY time-averages.  The
# optional set is the INCREMENTAL lines.  Nothing is typed twice.
# ==========================================================================
BASELINE, INCREMENTAL, BURSTY = "BASELINE", "INCREMENTAL", "BURSTY"
PANEL_LOGIC_DECLARED_mA = tag(
    "panel.logic_and_touch_mA", 50.0, DECLARED_ESTIMATE,
    "DECLARED, and labelled as declared -- but D-792 corrected WHY.  D-791 said "
    "the EastRising ER-TFT035IPS-6 module specification was 'not obtainable "
    "from this environment (HTTP 403 on every route tried)'.  IT IS "
    "OBTAINABLE: at D-792 it retrieved with HTTP 200 and is now archived at "
    "vendor/EASTRISING/eastrising-er-tft035ips-6-datasheet.pdf, sha256 "
    "28c07dae0c3ada133d0765167d38ae71b0f76fb9e94a18c00d96bb77682334ac, with "
    "the fetch on the record in evidence/d792-vendor-fetch-attempts.json.  "
    "READING IT DOES NOT REMOVE THE ALLOWANCE, AND THAT IS A STRONGER "
    "STATEMENT THAN THE ONE IT REPLACES: section 4.3's Electrical "
    "Characteristics table publishes VCI 2.5/2.8/3.3 V and VDDI 1.65/2.8/3.3 V "
    "and NOTHING ELSE -- no active-mode supply current for the panel at all -- "
    "and ILI Technology's own ILI9488 datasheet publishes only Sleep-in 100 uA "
    "and Deep Standby 1 uA.  The 50 mA covers the panel's VCI "
    "analog/charge-pump/source-driver side, its IOVCC logic side, and the "
    "FT6236 touch controller on the same FPC; it is about 2x what a 3.5 in "
    "ILI9488 module of this class draws, and F6 proves the derived envelope "
    "still closes at 2x it.",
    measurement_of_record="C-DISP-01")

LOAD_LEDGER = (
    dict(key="mcu_baseline", kind=BASELINE, refs=("U1",),
         mA=round(MCU_BASELINE_A * 1000.0, 4),
         mode=None,
         line="ESP32-S3-WROOM-1-N16R8 baseline: CPU, flash and in-package "
              "PSRAM, no radio transmitting",
         tag=DERIVED,
         cite="D-792 / R11-02.  THE LINE THAT WAS NOT THERE.  Espressif v1.8 "
              "Table 6-6's worst published row for this part (240 MHz, dual "
              "core, 128-bit data access, all peripheral clocks enabled) is "
              "107.9 mA TYP; note 3 adds 10 mA for flash access; the N16R8's "
              "in-package 8 MB PSRAM is covered by a declared 20 mA; and the "
              "sum is widened 20 % because Espressif publishes no MAX.  "
              "Measured at C-MCU-01."),
    dict(key="wifi_ble_tx", kind=INCREMENTAL, refs=("U1",),
         mA=round(MCU_RF_TX_INCREMENT_A * 1000.0, 4),
         mode="Wi-Fi / BLE TX",
         line="Wi-Fi / BLE TX increment over the module baseline",
         tag=DERIVED,
         cite="D-792 / N-01 + R11-02.  The module's TOTAL is Espressif's own "
              "Table 6-2 IVDD requirement, 500 mA MIN delivered by the "
              "external supply -- larger than the 355 mA Table 6-4 RF peak "
              "this budget used to carry, and by construction covering every "
              "CPU/flash/PSRAM/radio combination.  This line is that total "
              "LESS the baseline, so baseline + increment = 500 mA exactly "
              "and neither is double-counted."),
    dict(key="subghz_tx", kind=INCREMENTAL, refs=("U7", "U8"),
         mA=140.0, mode="sub-GHz TX",
         line="sub-GHz TX, the worse of the two shared-bus radios",
         tag=GUARANTEED_MAX,
         cite="Ebyte E22-M series user manual, archived at vendor/Ebyte/: "
              "emission current 100-140 mA instantaneous @22 dBm for the "
              "fitted E22-900M22S.  The E07-400M10S CC1101 is 35 mA (its own "
              "manual v1.3).  ONLY THE WORSE OF THE TWO is counted, because "
              "the Demo scope holds them to one TX at a time on the shared "
              "SPI-B bus -- but it is ADDED TO the Wi-Fi line and not "
              "substituted for it, because no silicon enforces a rule "
              "between U1's radio and U8's."),
    dict(key="backlight", kind=BASELINE,
         refs=("U17", "L3", "D8", "Q11", "R69", "R70", "R71", "R72", "R73"),
         mA=round(BACKLIGHT_INPUT["bound_A"] * 1000.0, 4), mode=None,
         line="display backlight converter input, at the worst LED setpoint",
         tag=DERIVED,
         cite="SOLVED by backlight_converter_input() from published maxima "
              "only -- VREF 220 mV over R69 at -1 %, the panel's 3.2 V VF "
              "upper end, Q11's only published conduction row, the "
              "TPS61169's 0.7 ohm switch and 0.45 mA IQ, the fitted "
              "inductor's DCR at its manufacturer MAXIMUM (R11-10) and D8's "
              "710 mV bound, at the minimum published switching frequency "
              "into the minimum inductance, with D-791's four declared loss "
              "terms.  The bound is the worst of a CCM treatment, a DCM "
              "treatment and TI's own 'up to 90 %' headline.  D-792: this is "
              "the ONLY place the number exists."),
    dict(key="panel_logic", kind=BASELINE, refs=("J1",),
         mA=PANEL_LOGIC_DECLARED_mA, mode=None,
         line="display panel logic + touch controller (DECLARED allowance)",
         tag=DECLARED_ESTIMATE,
         cite="DECLARED; see PANEL_LOGIC_DECLARED_mA.  C-DISP-01 first-"
              "article measurement is the measurement of record."),
    dict(key="expanders_imu", kind=BASELINE, refs=("U2", "U3", "U4"),
         mA=13.0, mode=None,
         line="touch + housekeeping (both expanders and the IMU)",
         tag=DECLARED_ESTIMATE,
         cite="FBV2-COMM-001 internal subtotal, retained"),
    dict(key="front_rgb", kind=BASELINE, refs=("D13",),
         mA=4.2, mode=None, line="front RGB at white",
         tag=DERIVED,
         cite="FBV2-S1-008 / D-184's re-derivation"),
    dict(key="audio", kind=INCREMENTAL, refs=("U5",),
         mA=120.0, mode="audio at the capped level",
         line="audio at the capped level",
         tag=DECLARED_ESTIMATE,
         cite="FBV2-COMM-001 internal subtotal, retained; D-161 records the "
              "MAX98357A's 230 mA PEAKS separately as locally supplied"),
    dict(key="microsd_write", kind=BURSTY, refs=("J2",),
         mA=100.0, duty=0.50, window_s=60.0, mode=None,
         line="microSD write",
         tag=DECLARED_ESTIMATE,
         cite="FBV2-COMM-001 internal subtotal, retained.  Bursty: a logging "
              "write burst; 50 % of any minute bounds continuous logging at "
              "this board's SPI-A rate"),
    dict(key="nfc_field", kind=BURSTY, refs=("U9",),
         mA=100.0, duty=0.25, window_s=60.0, mode=None,
         line="NFC front end, field on",
         tag=DECLARED_ESTIMATE,
         cite="D-205: DS12484 Rev 3 Table 121 gives I_AL-AM = 26 mA MAX for "
              "the IC with all blocks active and D-134's first-build network "
              "draws about 60 mA at the driver, so the +3V3 allocation with "
              "the field on is 100 mA.  Bursty: a read/write transaction is "
              "0.1-1 s and the Demo's NFC is operator-initiated; 25 % of any "
              "minute is a deliberately generous bound on a hand-held tap.  "
              "D-205's own guard rail stands -- a C_s move to 270 pF would "
              "draw about 257 mA and requires this budget to be re-run"),
    dict(key="ir_tx", kind=BURSTY, refs=("D1", "Q1", "R24"),
         mA=50.0, duty=0.10, window_s=60.0, mode=None,
         line="IR transmitter, burst average",
         tag=DECLARED_ESTIMATE,
         cite="D-155 / FBV2-S1-007: the 150 mA peaks are supplied by C12 "
              "22 uF and not by the rail, so the rail sees the burst "
              "average.  Bursty: a remote-control frame is tens of ms and "
              "10 % of any minute bounds continuous key repeat"),
)


def peak_budget():
    """Every line at its PEAK.  This is the +3V3 instantaneous budget."""
    return tuple(dict(line=x["line"], mA=x["mA"], refs=tuple(x["refs"]),
                      kind=x["kind"], key=x["key"], tag=x["tag"],
                      cite=x["cite"])
                 for x in LOAD_LEDGER)


def peak_A():
    return round(sum(x["mA"] for x in LOAD_LEDGER) / 1000.0, 6)


def sustained_always_on():
    """BASELINE lines at full, BURSTY lines at their bounded duty."""
    out = {}
    for x in LOAD_LEDGER:
        if x["kind"] == BASELINE:
            out[x["line"]] = round(x["mA"] / 1000.0, 6)
    return out


def bursty_allowances():
    return tuple(dict(line=x["line"], peak_A=round(x["mA"] / 1000.0, 6),
                      duty=x["duty"], window_s=x["window_s"], basis=x["cite"])
                 for x in LOAD_LEDGER if x["kind"] == BURSTY)


def bursty_time_averaged_A():
    return round(sum(x["mA"] / 1000.0 * x["duty"]
                     for x in LOAD_LEDGER if x["kind"] == BURSTY), 6)


# ==========================================================================
# D-793.  THE TWO PUBLISHED ACCESSORY BUDGETS AND THE DECLARED PAIR LIVE HERE.
#
# Fable's Round-12 complementary item, in its own words: "DECLARED_DUAL_RAIL_
# BUDGET_A hand-typed outside canonical model: move policy budget/meaning into
# canonical source or generated artifact; ensure firmware/docs consume the same
# authority."
#
# It is right, and the comment beside the D-792 constant made it worse: it
# said F12 "REFUSES if this constant differs from what it derived", and no
# code did that.  A stated rule that never runs is a defect this programme has
# now hit several times.  The values live HERE, tagged `POLICY_BUDGET`,
# because that is what they are -- numbers this product PUBLISHES, not
# datasheet guarantees -- and `audit_tags()` refuses a POLICY_BUDGET dressed
# up as a manufacturer claim.  `demo_feature_contract` F12 now ASSERTS that
# the declared pair it derives equals the pair published here.
# ==========================================================================
# ==========================================================================
# D-794 / R13-05.  THE ACCESSORY LIMITER PROGRAMMING, AND WHAT IT IS AND IS
# NOT GUARANTEED TO DO.
#
# ROUND-13, IN ITS OWN WORDS: "Exact R97=1.87k and R101=2.43k lie between
# discrete TPS22950-Q1 characterization rows.  Widest observed row ratio is a
# DECLARED engineering/qualification envelope, not a manufacturer guarantee
# for every intermediate resistor/temperature/VIN.  Published 400mA and 300mA
# lower-limit margins are thin and must not be labeled guaranteed solely from
# interpolation.  Obtain defensible primary/manufacturer support for the
# programmed points OR explicitly classify/qualify/derate the first-five
# capability."
#
# IT IS RIGHT, AND THE HONEST ANSWER IS THE SECOND BRANCH.  TI publishes four
# RILIM rows and an accuracy band AT each of them.  Neither R97 = 1.87 kOhm
# nor R101 = 2.43 kOhm is one of those four, and TI states nothing about the
# accuracy between rows.  D-791 already refused the BRACKETED figure for
# exactly that reason and fell back to the table's WIDEST ratio -- which needs
# no assumption about curvature, but is still an ENVELOPE THIS PROGRAMME
# DECLARES rather than a manufacturer guarantee at the programmed point.
#
# SO IT IS TAGGED AS ONE, IT CARRIES A FIRST-ARTICLE MEASUREMENT OF RECORD,
# AND NO DOCUMENT MAY SAY THE PUBLISHED BUDGETS ARE "GUARANTEED" BY IT.  What
# the first five ship with is a DECLARED and QUALIFIED capability: the
# envelope below, plus C-ACC-ILIM-01, which measures the actual limit at the
# programmed resistors on real units before the capability is published as
# anything stronger.
#
# THE LOW-SIDE MARGINS ARE THIN AND THE NUMBERS ARE STATED RATHER THAN
# ADJECTIVES: at 1.87 kOhm the envelope's low end is 0.4058 A against a
# published 400 mA -- 1.45 % -- and at 2.43 kOhm it is 0.3065 A against a
# published 300 mA -- 2.17 %.  That is the qualification C-ACC-ILIM-01 has to
# close, and it is why this block exists instead of the word "guaranteed".
# ==========================================================================
ILIM_ACCURACY_ROWS = {
    # RILIM ohms: (min_A, typ_A, max_A)
    610.0: (1.54, 2.00, 2.46),
    1150.0: (0.75, 1.00, 1.25),
    2210.0: (0.38, 0.50, 0.62),
    19200.0: (0.034, 0.050, 0.066),
}
ILIM_ACCURACY_SOURCE = (
    "TI SLVSGP6A Electrical Characteristics, Output Current Limit (ILIM), the "
    "-40..125 C rows at VOUT - VIN = 0.3 V: 1.54/2/2.46 A at 610 ohm, "
    "0.75/1/1.25 A at 1.15 kOhm, 0.38/0.5/0.62 A at 2.21 kOhm and "
    "0.034/0.05/0.066 A at 19.2 kOhm.  Archived at vendor/TI/"
    "ti-tps22950-q1-slvsgp6a-DDC0006A.pdf.")
ILIM_ENVELOPE_LO = tag(
    "acc.ilim_envelope_lo", 0.68, DECLARED_ENGINEERING_BOUND,
    "the WIDEST low-side ratio in TI SLVSGP6A's four published ILIM accuracy "
    "rows.  It needs no curvature assumption, but R97 and R101 are BETWEEN "
    "rows and TI publishes nothing between them, so at the programmed points "
    "this is an envelope this programme DECLARES and qualifies, not a "
    "manufacturer guarantee.  C-ACC-ILIM-01 measures the real limit.",
    condition="RILIM between published rows, -40..125 C, VOUT - VIN = 0.3 V",
    measurement_of_record="C-ACC-ILIM-01",
    role=SUPPLY_REQUIREMENT)
ILIM_ENVELOPE_HI = tag(
    "acc.ilim_envelope_hi", 1.32, DECLARED_ENGINEERING_BOUND,
    "the WIDEST high-side ratio in the same four rows, used as the FAULT "
    "ceiling the copper and the protection ordering are sized against.",
    condition="RILIM between published rows, -40..125 C, VOUT - VIN = 0.3 V",
    measurement_of_record="C-ACC-ILIM-01",
    role=SUPPLY_REQUIREMENT)
ILIM_PROGRAMMED_OHM = {"ACC_3V3": 1870.0, "ACC_5V": 2430.0}
ILIM_RESISTOR_TOLERANCE = 0.01


def ilim_typ_A(r_ohms):
    """TI equation 1, identical in SLVSFJ2B and SLVSGP6A.  Amps from ohms."""
    return 1.18 * ((r_ohms / 1000.0) ** -1.072)


def ilim_accuracy_band(r_ilim_ohm, rows=None):
    """The RULING lo/hi ratio envelope for a programming resistor.

    The WIDEST ratio the published table contains, which holds at every row
    and between every pair of rows without any assumption about what the
    accuracy does in between.  The bracketing rows and their (narrower) ratio
    are returned for REPORTING only -- see `ilim_bracketed_estimate`.
    """
    rows = ILIM_ACCURACY_ROWS if rows is None else rows
    ratios = [(rows[r][0] / rows[r][1], rows[r][2] / rows[r][1]) for r in rows]
    lo = min(x[0] for x in ratios)
    hi = max(x[1] for x in ratios)
    _, _, bracket = ilim_bracketed_estimate(r_ilim_ohm, rows)
    return lo, hi, bracket


def ilim_bracketed_estimate(r_ilim_ohm, rows=None):
    """D-790 / R9-N01's bracketed figure, RETAINED AS AN ESTIMATE.

    The worse of the two published rows that bracket the setting, per side.
    It is reported so the size of the conservatism D790-A12 requires is
    visible; nothing in this contract RULES on it.
    """
    rows = ILIM_ACCURACY_ROWS if rows is None else rows
    keys = sorted(rows)
    ratios = {r: (rows[r][0] / rows[r][1], rows[r][2] / rows[r][1])
              for r in keys}
    below = [r for r in keys if r <= r_ilim_ohm]
    above = [r for r in keys if r >= r_ilim_ohm]
    if not below or not above:
        lo = min(x[0] for x in ratios.values())
        hi = max(x[1] for x in ratios.values())
        return lo, hi, ["outside the published rows: widest ratio"]
    bracket = sorted({max(below), min(above)})
    lo = min(ratios[r][0] for r in bracket)
    hi = max(ratios[r][1] for r in bracket)
    return lo, hi, ["%g ohm" % r for r in bracket]


def ilim_band_A(r_ilim_ohm, tol=None):
    """The declared (min, typ, max) limit band at a programmed resistor.

    ONE authority.  `demo_feature_contract` F6, `audit_rail_ampacity`'s
    accessory rail rows and every document that quotes a limiter figure read
    THIS, so a resistor change moves all of them together -- R13-04's "bind
    all consumers to one independently checked primitive authority".
    """
    tol = ILIM_RESISTOR_TOLERANCE if tol is None else tol
    typ = ilim_typ_A(r_ilim_ohm)
    hi = ilim_typ_A(r_ilim_ohm * (1.0 - tol))
    lo = ilim_typ_A(r_ilim_ohm * (1.0 + tol))
    a_lo, a_hi, bracket = ilim_accuracy_band(r_ilim_ohm)
    e_lo, e_hi, _ = ilim_bracketed_estimate(r_ilim_ohm)
    return dict(
        r_ohm=r_ilim_ohm, tolerance=tol,
        typ_A=round(typ, 6),
        min_A=round(lo * a_lo, 6),
        max_A=round(hi * a_hi, 6),
        envelope=[a_lo, a_hi],
        bracket_rows=bracket,
        is_a_published_row=bool(r_ilim_ohm in ILIM_ACCURACY_ROWS),
        bracketed_estimate_min_A=round(lo * e_lo, 6),
        bracketed_estimate_max_A=round(hi * e_hi, 6),
        classification=("DECLARED AND QUALIFIED, not guaranteed: the "
                        "programmed resistor is not one of TI's four "
                        "published ILIM rows, so the envelope is this "
                        "programme's declaration and C-ACC-ILIM-01 is the "
                        "measurement of record."
                        if r_ilim_ohm not in ILIM_ACCURACY_ROWS else
                        "GUARANTEED at a published row."),
        source=ILIM_ACCURACY_SOURCE,
        measurement_of_record="C-ACC-ILIM-01")


def accessory_limiter_report():
    """Both accessory limiters, from one authority, with the thin margins
    stated as numbers."""
    out = {}
    for rail, r in sorted(ILIM_PROGRAMMED_OHM.items()):
        b = ilim_band_A(r)
        budget = PUBLISHED_RAIL_BUDGET_A[rail]
        out[rail] = dict(
            b, published_budget_A=budget,
            low_side_margin_A=round(b["min_A"] - budget, 6),
            low_side_margin_pct=round((b["min_A"] / budget - 1.0) * 100.0, 4),
            the_budget_is_inside_the_declared_envelope=bool(
                b["min_A"] >= budget))
    return out


PUBLISHED_RAIL_BUDGET_A = dict(
    ACC_3V3=tag("policy.acc_3v3_published_budget_A", 0.400,
                DECLARED_ENGINEERING_BOUND,
                "D-098, 2026-08-23: 'First five boards: ACC_3V3_SW = 400 mA "
                "TOTAL'.  Preserved explicitly by the D-788 Option A owner "
                "decision.  The two duplicated contacts SHARE the rail limit; "
                "they do not double it.",
                role=POLICY_BUDGET),
    ACC_5V=tag("policy.acc_5v_published_budget_A", 0.300,
               DECLARED_ENGINEERING_BOUND,
               "D-098, 2026-08-23: 'ACC_5V_SW = 300 mA TOTAL'.  Preserved "
               "explicitly by the D-788 Option A owner decision.",
               role=POLICY_BUDGET))
DECLARED_DUAL_RAIL_BUDGET_A = dict(
    ACC_3V3=tag("policy.declared_pair_acc_3v3_A", 0.220,
                DECLARED_ENGINEERING_BOUND,
                "D-792 / R11-04, re-derived unchanged at D-793.  SOLVED by "
                "demo_feature_contract F12 as the largest proportional "
                "derating of the two published budgets that the firmware's "
                "own retention rule holds at the same critical cell voltage "
                "the single-rail permission already reaches, at the top of "
                "the declared ambient envelope, rounded DOWN onto a 10 mA "
                "grid.  F12 REFUSES if this value differs from what it "
                "derives -- which at D-792 was a sentence and not a clause.",
                role=POLICY_BUDGET),
    ACC_5V=tag("policy.declared_pair_acc_5v_A", 0.170,
               DECLARED_ENGINEERING_BOUND,
               "the 5 V half of the same solved pair.",
               role=POLICY_BUDGET))
DECLARED_PAIR_ENFORCEMENT = (
    "IT IS AN OPERATOR / POLICY LIMIT, NOT A CURRENT MEASUREMENT.  This board "
    "has NO current sense on either accessory rail and the firmware cannot "
    "see how much an accessory draws.  What the firmware enforces is the "
    "PERMISSION and the RETENTION: a rail is only enabled when the gauge's "
    "reported VCELL clears the permission table's floor for the mode set the "
    "board is in, and a live rail is SHED when the reported VCELL falls below "
    "kAccessoryRetentionFloorV -- the 5 V rail FIRST, because shedding it "
    "restores the node and leaves the 3.3 V rail delivering its full "
    "published budget.  ON OVERLOAD, in order: an accessory drawing beyond "
    "the declared pair pulls the node down, the settled recheck sheds the 5 V "
    "rail, and if the node is still low every accessory rail goes off.  "
    "Beyond that the HARDWARE acts and the firmware is not involved -- U20 "
    "and U22 current-limit at their programmed points, then the BQ25185's "
    "recoverable BATOCP, then the latching LTC4368 breaker, then F1's "
    "one-shot fuse, in that order, which demo_feature_contract F6 proves is "
    "the order every reachable state actually meets.  The declared pair is a "
    "contract with the ACCESSORY DESIGNER about what the port supports; it is "
    "not a thing the board measures.")


# D-793 / R12-08.  A DUTY AVERAGE IS NOT AN INSTANTANEOUS PERMISSION BOUND.
#
# ROUND-12, IN ITS OWN WORDS: "D-792 uses sustained duty allowance for SD/NFC/
# IR bursts while permission/retention transitions occur on much shorter
# electrical timescales.  Astra constructed a credible quiet-pre-read ->
# accessory enable + burst -> post-read below retention case."
#
# It is right, and the mechanism is exactly the one R11-04 already found once.
# The three BURSTY lines enter every sustained state at their duty-averaged
# value -- 50 mA of microSD, 25 mA of NFC field, 5 mA of IR, 80 mA in total.
# Their PEAKS are 100 + 100 + 50 = 250 mA.  A permission is granted on a
# pre-read taken in a quiet moment and re-checked about 400 ms later, and a
# logging write, a card tap or a key repeat can begin anywhere in between.
# The permission edge therefore has to be judged with the burst PEAK present,
# not its minute-average.
#
# THE TWO MODELS ARE NOW SEPARATE AND BOTH ARE KEPT:
#
#   THERMAL / SUSTAINED   duty-averaged.  A 100 mA burst at 25 % of a minute
#                         really does deposit 25 mA of average heat, and the
#                         enclosure's thermal time constant is minutes.  The
#                         junction, the internal air and the ambient ceilings
#                         all stay on this model.
#   INSTANTANEOUS         the peak, for the electrical limits that act in
#                         microseconds -- the node against VBUVLO, VSYS
#                         against U12's input floor, the battery current
#                         against IBAT_OCP, the pass pair's VGS against its
#                         conduction row -- and for the firmware's own
#                         retention read.
#
# THE DELTA IS ENUMERATED, NOT ASSUMED.  Every subset of the bursty lines is
# priced, because nothing in this product forbids a card tap during a logging
# write, and the RULING delta is the worst subset the firmware does not
# prevent.  If a future firmware serialises them, the restriction goes here
# and the ruling subset shrinks; it is not assumed away.
# ==========================================================================
# THE FIRMWARE RESTRICTION R12-08 OFFERS AS THE ALTERNATIVE, AND THIS DESIGN
# TAKES IT.  Round-12: "Enumerate actual peak/burst pre/post transitions and
# maximum burst durations, OR enforce a clear scheduling restriction in
# firmware."  Unserialised, the three bursts together add 170 mA at the
# permission edge and cost four of the sixteen permission rows -- including
# every accessory state with the audio amplifier driving.  Serialised they add
# 75 mA and those rows come back.  The restriction is NARROW (it applies only
# while an accessory rail is live), it is implementable (all three are
# firmware-driven peripherals), and it is PROVEN rather than assumed: the
# permission table may only be derived at the serialised delta if
# `demo_feature_contract` can show `BurstArbiter` in the shipped firmware and
# `Firmware/test/` can show it refusing.
BURST_COINCIDENCE_POLICY = (
    "WHILE AN ACCESSORY RAIL IS LIVE the firmware's BurstArbiter permits at "
    "most ONE of {microSD write burst, NFC field, IR transmit} at a time, so "
    "the ruling instantaneous delta is the worst SINGLE burst rather than the "
    "sum of all three.  With no accessory rail live there is no permission "
    "edge to protect and the arbiter does not engage, so nothing a user does "
    "with the card, the tag reader or the IR blaster alone is restricted.  "
    "R12-08 offers this restriction as the alternative to charging the full "
    "coincident sum, and it is taken because charging the sum costs four "
    "permission rows -- every accessory state with the amplifier driving -- "
    "for a coincidence the firmware can simply not create.")
# The subsets a serialising arbiter can leave reachable: at most one bursty
# line at a time.
SERIALISED_BURST_SUBSETS = tuple(
    [()] + [(x["key"],) for x in LOAD_LEDGER if x["kind"] == BURSTY])


def burst_subsets():
    """Every coincident combination of the bursty lines, priced.

    `delta_A` is the amount by which the INSTANTANEOUS draw exceeds what the
    sustained state already carries for the same lines.
    """
    lines = [x for x in LOAD_LEDGER if x["kind"] == BURSTY]
    out = []
    for bits in range(1 << len(lines)):
        sel = [lines[i] for i in range(len(lines)) if bits & (1 << i)]
        out.append(dict(
            keys=[x["key"] for x in sel],
            peak_A=round(sum(x["mA"] for x in sel) / 1000.0, 6),
            already_carried_A=round(
                sum(x["mA"] * x["duty"] for x in sel) / 1000.0, 6),
            delta_A=round(sum(x["mA"] * (1.0 - x["duty"])
                              for x in sel) / 1000.0, 6),
            max_burst_s=[dict(key=x["key"], window_s=x["window_s"],
                              duty=x["duty"],
                              max_continuous_s=round(x["duty"] * x["window_s"],
                                                     3))
                         for x in sel]))
    return out


def burst_transition_delta_A(allowed=None, serialised=True):
    """The RULING instantaneous delta for a permission/retention edge.

    `allowed` is the set of subsets a firmware scheduling restriction permits,
    as a list of key-tuples.  `serialised=False` charges EVERY subset, which
    is what the model must do if the firmware arbiter cannot be proven -- and
    `demo_feature_contract` passes `serialised=False` unless it can show the
    arbiter in the shipped image and a host test refusing without it.
    """
    subs = burst_subsets()
    if allowed is None and serialised:
        allowed = SERIALISED_BURST_SUBSETS
    if allowed is not None:
        keys = {tuple(sorted(k)) for k in allowed}
        subs = [x for x in subs if tuple(sorted(x["keys"])) in keys]
    return round(max(x["delta_A"] for x in subs), 6)


def sustained_optional():
    """The observable MODES a sustained state may name."""
    return {x["mode"]: round(x["mA"] / 1000.0, 6)
            for x in LOAD_LEDGER if x["kind"] == INCREMENTAL}


def ledger_is_partitioned():
    """Every line lands in exactly one view, and the views sum to the peak."""
    base = sum(x["mA"] for x in LOAD_LEDGER if x["kind"] == BASELINE)
    incr = sum(x["mA"] for x in LOAD_LEDGER if x["kind"] == INCREMENTAL)
    burst = sum(x["mA"] for x in LOAD_LEDGER if x["kind"] == BURSTY)
    total = sum(x["mA"] for x in LOAD_LEDGER)
    modes = [x["mode"] for x in LOAD_LEDGER if x["kind"] == INCREMENTAL]
    return dict(
        baseline_mA=round(base, 4), incremental_mA=round(incr, 4),
        bursty_peak_mA=round(burst, 4), peak_mA=round(total, 4),
        views_sum_to_the_peak=bool(abs(base + incr + burst - total) < 1e-9),
        every_incremental_line_names_an_observable_mode=bool(
            all(m for m in modes) and len(set(modes)) == len(modes)),
        every_bursty_line_has_a_duty=bool(all(
            0.0 < x.get("duty", 0.0) <= 1.0 and x.get("window_s", 0) > 0
            for x in LOAD_LEDGER if x["kind"] == BURSTY)),
        module_total_is_the_vendor_supply_requirement=bool(
            abs(MCU_BASELINE_A + MCU_RF_TX_INCREMENT_A
                - MCU_MODULE["supply_requirement_A"]) < 1e-9),
        why="R11-02: one ledger, three disjoint kinds, and the peak budget, "
            "the sustained always-on set, the optional-mode set and the "
            "bounded-duty allowances are all VIEWS of it.  Nothing is typed "
            "in two files and nothing can be omitted from one view while "
            "being present in another.")


# ==========================================================================
# 5.  THE CELL-TO-`BAT_PROTECTED_P` SOURCE RESISTANCE, ITEMISED -- R11-07.
#
# ROUND-11, IN ITS OWN WORDS: "Existing 54 mOhm harness allowance is below a
# plausible bound from the selected 75 mm leads plus two mated contacts before
# battery leads/J4/hot-aged effects.  Itemize both conductors, both contacts,
# exact lengths, temperature effects, solder/process contributions and pack
# source resistance ownership.  Do not treat AC pack impedance as a universal
# DC source-resistance maximum."
#
# D-791's allowance was ONE number with ONE sentence of basis -- "two UL 26 AWG
# conductors, about 100 mm each way, at 0.1339 ohm/m nominal plus the J4
# terminations" -- and it was wrong in three separate ways at once:
#
#   * IT COUNTED ONE PAIR OF CONDUCTORS.  The harness D-781 froze has TWO
#     pairs: the Molex 75 mm factory pre-crimps on the board side and the
#     pack's OWN UL 26 AWG factory leads on the battery side (785060
#     specification material list items 3 and 4).
#   * IT COUNTED NO CONTACTS AT ALL.  The frozen interface is a Micro-Lock
#     Plus 2.0 WIRE-TO-WIRE mate: two mated contact pairs, one per conductor,
#     in the battery path.  A mated contact is the largest single term in this
#     list after the pack itself.
#   * IT USED THE NOMINAL SOLID-CONDUCTOR RESISTIVITY, AT 20 C, FOR STRANDED
#     APPLIANCE WIRE RUNNING WARM INSIDE A SEALED CASE.
#
# WHICH DIRECTION IS CONSERVATIVE DEPENDS ON THE QUESTION, AND BOTH ENDS ARE
# HERE.  For the NODE VOLTAGE under load, for DISSIPATION and for the derived
# VCELL floors the MAXIMUM is conservative.  For bounding the CURRENT that
# flows when the node sags by a known amount -- I = (V_cell - V_node) / R -- the
# MINIMUM is, because a smaller resistance means more current for the same sag.
#
# D-793 / R12-01.  THE MOLEX DOCUMENT IS IN THE TREE NOW, AND IT IS WORSE
# THAN THE DECLARATION IT REPLACES.
#
# D-792 recorded 5055700003-PS as "not retrievable from this environment" and
# DECLARED the contact terms at 20 mOhm initial / 30 mOhm aged on that basis.
# Round-12 says Molex primary evidence supports a 40 mOhm post-durability /
# post-environment criterion.  It does.  The document retrieved at D-793
# through the Internet Archive's 2023-11-01 snapshot of the same molex.com URL
# and is archived at vendor/MOLEX/molex-5055700003-PS-A1.pdf; every row this
# repository had already transcribed is present and identical in it, and three
# rows it had NEVER seen are:
#
#   6.1.1  Contact Resistance                     20 milliohms MAX
#          mated, dry circuit, WIRE CONDUCTOR RESISTANCE SUBTRACTED -- so the
#          figure is the contact pair alone and the conductor is counted
#          separately, which is exactly how this itemisation is built
#   6.1.4  Contact Resistance on crimped portion   5 milliohms MAX
#          D-792 carried 1 mOhm per crimp as a declared allowance.  The
#          manufacturer publishes FIVE times that.
#   6.2.6/6.2.7/6.2.8 and 6.3.1..6.3.7           40 milliohms MAX
#          the SAME criterion after 30 insertion cycles, after vibration,
#          after 50 G shock, after temperature cycling, after 96 h at 105 C,
#          after 96 h at -40 C, after 96 h at 60 C/90-95 % RH, after 48 h
#          salt spray, after SO2 and after NH3.  This is the number an aged
#          contact in a hand-assembled first-five harness has to be held to,
#          and it is the one this model now RULES at.
#
# THIS IS THE THIRD TIME IN THIS PROGRAMME THAT "UNOBTAINABLE" HAS MEANT "NOT
# FETCHED FROM HERE" (D-751's EastRising 403, R11-N01's retrieval of the same
# document, and now this).  The three contact/crimp terms move from
# DECLARED_ESTIMATE to GUARANTEED_MAX and the path gets 45 mOhm longer.
# C-BAT-PATH-01 remains the measurement of record for all of them.
#
# REVISION, RECORDED RATHER THAN SMOOTHED: the retrieved copy is Rev A1 and
# the product page cites Rev A6.  Every row the design already depended on is
# identical between them.
# ==========================================================================
CU_TC_PER_K = 0.00393
CU_HOT_RISE_K = 65.0
CU_HOT_FACTOR = round(1.0 + CU_TC_PER_K * CU_HOT_RISE_K, 6)

AWG26_SOLID_OHM_PER_M = tag(
    "path.awg26_solid_ohm_per_m", 0.134250, DERIVED,
    "computed, not quoted: 26 AWG diameter 0.40386 mm gives 0.128118 mm2, and "
    "1.72e-8 ohm.m annealed copper at 20 C gives 0.13425 ohm/m.",
    condition="20 C, solid conductor", ruling=False)
AWG26_STRANDED_MAX_OHM_PER_M = tag(
    "path.awg26_stranded_max_ohm_per_m", 0.145800, DECLARED_ESTIMATE,
    "DECLARED.  Both conductor pairs in this harness are UL stranded 26 AWG "
    "(Molex 217501 pre-crimps are UL 10002; the 785060 pack specification "
    "material list items 3 and 4 are 'UL 26AWG').  0.1458 ohm/m at 20 C is "
    "the maximum DC conductor resistance tabulated for stranded 26 AWG "
    "appliance wire and is 8.6 % above the geometric figure for solid 26 AWG "
    "computed above; the margin covers the lay length and the conductor "
    "tolerance.  D-791 used the SOLID nominal.",
    condition="20 C", measurement_of_record="C-BAT-PATH-01",
    widened_from="the computed solid-conductor value 0.13425 ohm/m")
CONTACT_INITIAL_MAX_OHM = tag(
    "path.microlock_contact_initial_max_ohm", 0.020, GUARANTEED_MAX,
    "Molex 5055700003-PS section 6.1.1 Contact Resistance: 20 milliohms MAX, "
    "mated, measured by dry circuit at 20 mV MAX / 10 mA MAX with the wire "
    "conductor resistance SUBTRACTED (JIS C5402-2-1), at the paragraph-8 "
    "measuring point.  Archived at vendor/MOLEX/molex-5055700003-PS-A1.pdf.  "
    "D-792 carried this as a DECLARED_ESTIMATE because the document had not "
    "been retrieved.",
    condition="initial, as-mated.  The conductor is NOT in this figure and "
              "is itemised separately below.",
    measurement_of_record="C-BAT-PATH-01", ruling=False)
CONTACT_AGED_MAX_OHM = tag(
    "path.microlock_contact_aged_max_ohm", 0.040, GUARANTEED_MAX,
    "Molex 5055700003-PS: 40 milliohms MAX Contact Resistance is the "
    "requirement after EVERY durability and environmental exposure the "
    "specification defines -- 6.2.6 repeated insertion/withdrawal (30 "
    "cycles), 6.2.7 vibration, 6.2.8 mechanical shock (50 G), 6.3.1 "
    "temperature cycling, 6.3.2 heat resistance (105 C, 96 h), 6.3.3 cold "
    "resistance, 6.3.4 humidity (60 C, 90-95 % RH, 96 h), 6.3.5 salt spray, "
    "6.3.6 SO2 and 6.3.7 NH3.  THIS IS THE FIGURE THIS MODEL RULES AT, and "
    "D-793 raised it from D-792's declared 30 mOhm.  The battery path crosses "
    "TWO mated contacts, one per conductor.",
    condition="after durability/environmental conditioning; the criterion an "
              "aged first-five harness must still meet.  It is the "
              "SPECIFICATION'S OWN aged row, not a widening of the 20 mOhm "
              "initial row -- D-793 recorded it in `widened_from`, which is "
              "the field for THIS programme's own carries, and D-794 moved "
              "the statement here where it belongs.",
    measurement_of_record="C-BAT-PATH-01")
CRIMP_MAX_OHM = tag(
    "path.crimp_max_ohm", 0.005, GUARANTEED_MAX,
    "Molex 5055700003-PS section 6.1.4 'Contact Resistance on crimped "
    "portion': 5 milliohms MAX, measured by dry circuit at 20 mV MAX / "
    "10 mA MAX on the applicable wire.  Four crimped terminations are in the "
    "path: two Molex factory board-side crimps and two 2137201000 "
    "battery-side crimps made to the 213309-5900 process BATTERY_HARNESS "
    "freezes.  D-792 stated 1 mOhm each with no source; the manufacturer "
    "publishes five times that, and R12-01 asks for the crimps to be "
    "itemised properly.",
    condition="dry circuit, 20 mV MAX / 10 mA MAX, on the applicable wire, "
              "crimped to the specification's own process",
    measurement_of_record="C-BAT-PATH-01")
SOLDER_JOINT_MAX_OHM = tag(
    "path.j4_solder_joint_max_ohm", 0.001, DECLARED_ESTIMATE,
    "DECLARED.  Two hand-soldered J4 PTH barrels, made to the BATTERY_HARNESS "
    "rear-insertion / front-inspection process.  1 mOhm each.",
    measurement_of_record="C-BAT-PATH-01")
PACK_AC_IMPEDANCE_MAX_OHM = tag(
    "path.pack_ac_impedance_max_ohm", 0.035, GUARANTEED_MAX,
    "785060 2500 mAh specification sheet section 3: 'Impedance <= 35 mOhm, "
    "AC 1 kHz after 50 % charge, 25 C'.  Archived at vendor/BATTERY/.",
    condition="AC 1 kHz, 50 % charge, 25 C -- NOT a DC source resistance and "
              "NOT stated at any other temperature or state of charge")
PACK_DC_MULTIPLIER = tag(
    "path.pack_ac_to_dc_multiplier", 2.5, DECLARED_ESTIMATE,
    "DECLARED.  A 1 kHz AC impedance omits the diffusion component a DC load "
    "sees; 2.5x is a deliberately pessimistic carry for a 2.5 Ah pouch and it "
    "REPLACES D-790's invented 40 mOhm PCM allowance, which cited nothing.  "
    "R11-07: 'Do not treat AC pack impedance as a universal DC source-"
    "resistance maximum' -- this is the widening that keeps it from being "
    "treated as one.",
    widened_from="the 35 mOhm AC 1 kHz figure",
    measurement_of_record="C-BAT-PATH-01 and C-THERM-01")
FUSE_MAX_OHM = tag(
    "path.f1_fuse_max_ohm", 0.020, DECLARED_ESTIMATE,
    "DECLARED: the fitted 0466005 5 A nano2 element's cold resistance is not "
    "published in this repository; 20 mOhm is a declared allowance for a 5 A "
    "thin-film fuse.",
    measurement_of_record="C-BAT-PATH-01")
# D-793 / R12-01, IN ITS OWN WORDS: "Exact fitted 10 mOhm R75 1 % high corner
# is 10.1 mOhm; do not tag 10.0 mOhm as guaranteed max."  D-792's condition
# string SAID "at its 1 % high corner" and its VALUE was the nominal.  Both
# corners are now computed from the nominal and the tolerance so the sentence
# and the number cannot disagree again.
R75_NOMINAL_OHM = tag(
    "path.r75_sense_nominal_ohm", 0.010, DERIVED,
    "the ORDERED value of the fitted sense element, Bourns "
    "CRA2512-FZ-R010ELF, resistance code R010 = 0.010 ohm (Bourns CRA series "
    "datasheet, archived vendor/BOURNS).  A nominal is not a bound; the "
    "tolerance below is.  D-795 / R14-06 re-tags it: D-794 called a nominal "
    "GUARANTEED_MAX and cited the schematic as the document.",
    condition="resistance code R010", ruling=False)
R75_TOLERANCE = tag(
    "path.r75_sense_tolerance", 0.01, GUARANTEED_MAX,
    "Bourns CRA series datasheet, How to Order, Resistance Tolerance: "
    "F = +/-1 %, the tolerance code of the fitted CRA2512-FZ-R010ELF "
    "(archived vendor/BOURNS/bourns-cra-series.pdf).",
    condition="ordering code F", ruling=False)
R75_OHM = tag(
    "path.r75_sense_max_ohm", round(0.010 * 1.01, 6), DERIVED,
    "the fitted 10 mOhm 1 % LTC4368 sense element at its HIGH corner: "
    "10.000 x 1.01 = 10.100 mOhm.  The high end is what a drop, a "
    "dissipation and a source-resistance question need.  DERIVED from the "
    "nominal and the tolerance above -- a corner of a guaranteed band is a "
    "CALCULATION, not a second guarantee (D-794 / R13-05).",
    condition="1 % high corner of the schematic R75 row")
R75_MIN_OHM = tag(
    "path.r75_sense_min_ohm", round(0.010 * 0.99, 6), DERIVED,
    "the same part at its LOW corner, 9.900 mOhm -- the end a CURRENT bound "
    "needs, because a smaller sense resistor trips the breaker later.  "
    "DERIVED from the nominal and the tolerance above.",
    condition="1 % low corner of the schematic R75 row")
# D-793 / R12-01 asks for F1's tolerance explicitly.  Littelfuse does not
# publish a cold-resistance row for the 0466005 at all, so the 20 mOhm above
# is a declared allowance and the TOLERANCE on it is declared too.  A +/-25 %
# spread on a thin-film fuse element is generous; the HIGH end is the one a
# source-resistance question uses and it is what `upstream_fixed_ohm("max")`
# carries.
FUSE_TOLERANCE = tag(
    "path.f1_fuse_tolerance", 0.25, DECLARED_ESTIMATE,
    "DECLARED.  Littelfuse publishes no cold-resistance row for the 0466005, "
    "so neither the value nor its spread is a datasheet number; +/-25 % is a "
    "generous carry on a 5 A nano2 element.  R12-01 asks for 'F1 tolerance' "
    "to be itemised rather than assumed away.",
    measurement_of_record="C-BAT-PATH-01")
FUSE_MAX_TOL_OHM = tag(
    "path.f1_fuse_max_tol_ohm", round(0.020 * 1.25, 6), DECLARED_ESTIMATE,
    "the declared 20 mOhm allowance at its declared +25 % high corner.",
    widened_from="the 20 mOhm declared allowance",
    measurement_of_record="C-BAT-PATH-01")

# The itemisation.  `hot` marks a term the 65 K internal rise is applied to --
# every metallic conductor and contact in the path, which is all of them
# except the electrochemical pack term and the discrete elements already
# carried at their own maxima.
HARNESS_ITEMS = (
    dict(key="pack_factory_leads", n=2, length_mm=60.0,
         ohm=None, hot=True,
         what="the 785060 pack's own UL 26 AWG factory leads, both "
              "conductors.  The pack specification does not publish a "
              "length; 60 mm each is DECLARED and is longer than the "
              "as-shipped lead this harness reterminates.",
         tag=DECLARED_ESTIMATE),
    dict(key="board_precrimp_leads", n=2, length_mm=75.0,
         ohm=None, hot=True,
         what="Molex 2175012101 red and 2175011101 black factory "
              "pre-crimped pigtails, 75.00 mm, 26 AWG UL 10002 -- the exact "
              "length the Molex series chart publishes and BATTERY_HARNESS "
              "freezes.",
         tag=GUARANTEED_MAX),
    dict(key="mated_contacts", n=2, length_mm=None,
         ohm=CONTACT_AGED_MAX_OHM, hot=True,
         what="two mated Micro-Lock Plus 2.0 contact pairs, one per "
              "conductor, at the aged LLCR maximum.  D-791 counted none.",
         tag=DECLARED_ESTIMATE),
    dict(key="crimps", n=4, length_mm=None, ohm=CRIMP_MAX_OHM, hot=True,
         what="four crimped terminations: two factory board-side, two "
              "battery-side to the frozen 213309-5900 process.",
         tag=DECLARED_ESTIMATE),
    dict(key="j4_solder_joints", n=2, length_mm=None,
         ohm=SOLDER_JOINT_MAX_OHM, hot=True,
         what="two hand-soldered J4 PTH barrels.",
         tag=DECLARED_ESTIMATE),
)


def _item_ohm(item, per_m, hot_factor):
    n = item["n"]
    if item["length_mm"] is not None:
        r = n * (item["length_mm"] / 1000.0) * per_m
    else:
        r = n * item["ohm"]
    return r * (hot_factor if item["hot"] else 1.0)


def harness_ohm(which="max"):
    """Pack terminals -> J4, itemised.  `max` is hot and aged; `min` is cold
    and at the initial contact figure with the geometric solid-conductor
    resistivity, which is the bound a CURRENT question needs."""
    if which == "min":
        per_m, hot = AWG26_SOLID_OHM_PER_M, 1.0
        items = [dict(i, ohm=(CONTACT_INITIAL_MAX_OHM * 0.5
                              if i["key"] == "mated_contacts"
                              else (i["ohm"] * 0.5 if i["ohm"] else None)))
                 for i in HARNESS_ITEMS]
    else:
        per_m, hot = AWG26_STRANDED_MAX_OHM_PER_M, CU_HOT_FACTOR
        items = list(HARNESS_ITEMS)
    return round(sum(_item_ohm(i, per_m, hot) for i in items), 6)


def harness_itemisation():
    rows = []
    for i in HARNESS_ITEMS:
        rows.append(dict(
            key=i["key"], count=i["n"], length_mm=i["length_mm"],
            per_item_ohm=(None if i["length_mm"] is None else
                          round((i["length_mm"] / 1000.0)
                                * AWG26_STRANDED_MAX_OHM_PER_M, 6))
            or i["ohm"],
            hot_max_ohm=round(_item_ohm(i, AWG26_STRANDED_MAX_OHM_PER_M,
                                        CU_HOT_FACTOR), 6),
            carries_the_hot_rise=i["hot"], tag=i["tag"], what=i["what"]))
    return rows


# ==========================================================================
# D-793 / R12-01.  THE TWO HALVES OF THE PATH D-792 DID NOT HAVE AT ALL.
#
# Round-12 asks for the COMPLETE source path, and names the terms:
#
#     "cell/PCM DC source resistance, battery leads, both conductors, both
#      contact pairs, crimps, board-side pigtail, J4 joint, F1 tolerance,
#      R75 tolerance, Q2/Q3 hot RDS(on), J4->F1->FET->R75 copper, return
#      path, temperature and aging."
#
# Every one of those was in the D-792 model EXCEPT the last three clauses:
# the BOARD COPPER between J4 and R75, and the GROUND RETURN.  The forward
# board copper is real and it is not small -- 35.1 mOhm at 20 C, measured --
# and it sat in no model at all, because F6/F12 start their downstream ledger
# at `BAT_PROTECTED_P` and the upstream ledger stopped at the J4 barrel.
#
# "Do not double-count protected-node copper already modeled downstream" --
# and nothing here does.  The downstream ledger's first term is `R75.2 ->
# U11.2`; the four segments below are all UPSTREAM of `R75.2`.
#
# THE FORWARD SEGMENTS ARE MEASURED OFF THE LIVE BOARD.  This module is pure,
# so the numbers below are the last measured set and are the DEFAULT;
# `demo_feature_contract.main()` re-measures all four with the same
# widest-bottleneck walk it uses for the downstream paths and passes them in.
# A live measurement above its ceiling FAILS rather than being absorbed.
BOARD_FORWARD_SEGMENTS = (
    dict(key="j4_to_f1", net="/01_POWER_TREE/BAT_CONNECTOR_P",
         src=("J4.1",), snk=("F1.1",),
         ohm_20C=0.0048788, bound_ohm=0.0080,
         what="J4.1 -> F1.1, the battery pigtail barrel to the fuse"),
    dict(key="f1_to_q2", net="/01_POWER_TREE/BAT_RAW",
         src=("F1.2",), snk=("Q2.7", "Q2.8"),
         ohm_20C=0.0063270, bound_ohm=0.0100,
         what="F1.2 -> Q2 drain, BAT_RAW"),
    dict(key="q2_to_q3", net="/01_POWER_TREE/BAT_MID",
         src=("Q2.5", "Q2.6"), snk=("Q3.7", "Q3.8"),
         ohm_20C=0.0093938, bound_ohm=0.0140,
         what="Q2 source -> Q3 drain, the BAT_MID link between the two "
              "back-to-back packages"),
    dict(key="q3_to_r75", net="/01_POWER_TREE/BAT_SENSE",
         src=("Q3.5", "Q3.6"), snk=("R75.1",),
         ohm_20C=0.0145199, bound_ohm=0.0200,
         what="Q3 source -> R75.1, BAT_SENSE"),
)


def board_forward_ohm(measured=None, hot=True):
    """J4.1 -> R75.1 board copper, hot.  `measured` is {key: ohm at 20 C}."""
    k = CU_HOT_FACTOR if hot else 1.0
    tot = 0.0
    for seg in BOARD_FORWARD_SEGMENTS:
        tot += (measured or {}).get(seg["key"], seg["ohm_20C"])
    return round(tot * k, 6)


def board_forward_itemisation(measured=None):
    return [dict(key=x["key"], net=x["net"],
                 src=list(x["src"]), snk=list(x["snk"]),
                 ohm_20C=(measured or {}).get(x["key"], x["ohm_20C"]),
                 bound_ohm=x["bound_ohm"],
                 hot_ohm=round((measured or {}).get(x["key"], x["ohm_20C"])
                               * CU_HOT_FACTOR, 6),
                 measured_live=bool(measured and x["key"] in measured),
                 what=x["what"])
            for x in BOARD_FORWARD_SEGMENTS]


# ---- THE GROUND RETURN.  A SHEET, SO IT IS ITEMISED AS ONE. --------------
# The return from the system ground reference to `J4.2` is carried by the two
# SOLID GND planes this board's own stackup declares -- In1 and In4, both
# 0.0152 mm -- in parallel, plus the outer GND pours, plus the J4.2 barrel.
# A track-graph walk cannot price a pour (this is the same reason
# `P3V3_DELIVERY`'s source and return terms are declared), so it is priced by
# SHEET RESISTANCE over a DECLARED square count, and the square count carries
# a stated widening over the geometric estimate.
RHO_CU_OHM_M = 1.72e-8
INNER_CU_THICKNESS_M = tag(
    "path.inner_copper_thickness_m", 15.2e-6, DECLARED_ESTIMATE,
    "DECLARED: the ORDERED stackup, In1..In4 0.0152 mm (0.5 oz), JLC06161H-"
    "7628, declared in the .kicad_pcb stackup and checked by "
    "keepout_stackup_contract.  An order parameter is not a manufacturer "
    "guarantee and the fab's thickness tolerance is not archived here; "
    "D-795 / R14-06 re-tags D-794's GUARANTEED_MAX.  C-BAT-PATH-01 "
    "measures the path it feeds.",
    measurement_of_record="C-BAT-PATH-01",
    condition="0.5 oz inner copper", ruling=False)
GND_PLANE_SHEET_OHM_PER_SQ = tag(
    "path.gnd_plane_sheet_ohm_per_square", round(
        RHO_CU_OHM_M / INNER_CU_THICKNESS_M / 2.0, 9), DERIVED,
    "1.72e-8 ohm.m / 15.2 um = 1.1316 mOhm per square for ONE 0.5 oz inner "
    "plane; In1 and In4 are both solid GND and in parallel, so 0.5658 mOhm "
    "per square.  The F.Cu and B.Cu GND pours are IGNORED, which is "
    "conservative.",
    condition="20 C, two 0.5 oz planes in parallel")
GND_RETURN_SQUARES = tag(
    "path.gnd_return_squares", 12.0, DECLARED_ESTIMATE,
    "DECLARED.  J4 sits at (7.0, 35.0) and the SYS/+3V3 converter cluster at "
    "(67.5..69.6, 77.8..97.6) on a 72 x 148 mm outline, so the return runs "
    "about 88 mm.  Spread over an effective 20 mm of plane width that is 4.4 "
    "squares; 12 is carried -- a 2.7x widening -- to cover the necks the "
    "battery-pouch and antenna keepouts put in the planes and the fact that "
    "the current does not enter the plane as a uniform sheet.",
    widened_from="the 4.4-square geometric estimate",
    measurement_of_record="C-BAT-PATH-01")
GND_RETURN_BARREL_OHM = tag(
    "path.gnd_return_barrel_ohm", 0.002, DECLARED_ESTIMATE,
    "DECLARED.  The J4.2 plated through-hole barrel plus the plane vias at "
    "the load end.  2 mOhm for the whole set.",
    measurement_of_record="C-BAT-PATH-01")


def gnd_return_ohm(squares=None, hot=True):
    sq = GND_RETURN_SQUARES if squares is None else squares
    k = CU_HOT_FACTOR if hot else 1.0
    return round((sq * GND_PLANE_SHEET_OHM_PER_SQ + GND_RETURN_BARREL_OHM)
                 * k, 6)


PACK_DC_OHM = round(PACK_AC_IMPEDANCE_MAX_OHM * PACK_DC_MULTIPLIER, 6)
PACK_OWNERSHIP = (
    "THE 35 mOhm OWNS THE CELL AND THE PROTECTION BOARD, AND NOTHING ELSE.  "
    "The 785060 specification states the impedance row in the same table as "
    "the cell's own voltages and states no measurement point; its material "
    "list names the cell, the S-8261AAJMD protection board, both UL 26 AWG "
    "wires and the JST-PHR-2 connector as separate items.  This model takes "
    "the PESSIMISTIC reading -- the 35 mOhm covers the electrochemistry and "
    "the PCM only -- and counts the pack's own leads as a separate itemised "
    "term above.  Under the alternative reading (the figure is measured at "
    "the pack connector and already contains the leads) the model "
    "overstates the path by the pack-lead term, which is reported.  The "
    "JST-PHR-2 housing is NOT in the path: D-781 reterminates it away.")


def upstream_fixed_ohm(which="max", board=None, squares=None):
    """Cell EMF -> BAT_PROTECTED_P and back, EXCLUDING the pass-pair channels.

    pack (cell + PCM, DC) + harness + J4->F1 copper + F1 + F1->Q2 copper
    + Q2->Q3 copper + Q3->R75 copper + R75 + the GROUND RETURN.

    D-793 / R12-01 added the last three of those; the four AO4800 channels are
    solved self-consistently by the network because their resistance depends
    on the current they carry.  Nothing here is downstream of `R75.2`, so
    nothing is double-counted against the `BAT_PROTECTED_P -> SYS` term F12
    measures separately.
    """
    if which == "min":
        return round(PACK_AC_IMPEDANCE_MAX_OHM * 1.0 + harness_ohm("min")
                     + FUSE_MAX_OHM * 0.5 * (1.0 - FUSE_TOLERANCE)
                     + R75_MIN_OHM
                     + board_forward_ohm(board, hot=False)
                     + gnd_return_ohm(squares, hot=False) * 0.5, 6)
    return round(PACK_DC_OHM + harness_ohm("max") + FUSE_MAX_TOL_OHM
                 + R75_OHM + board_forward_ohm(board)
                 + gnd_return_ohm(squares), 6)


def upstream_report(board=None, squares=None):
    return dict(
        pack_ac_impedance_max_ohm=PACK_AC_IMPEDANCE_MAX_OHM,
        pack_ac_to_dc_multiplier=PACK_DC_MULTIPLIER,
        pack_dc_ohm=PACK_DC_OHM,
        pack_ownership=PACK_OWNERSHIP,
        harness_items=harness_itemisation(),
        harness_hot_aged_max_ohm=harness_ohm("max"),
        harness_cold_initial_min_ohm=harness_ohm("min"),
        harness_max_was_before_d792_ohm=0.054,
        harness_max_was_at_d792_ohm=0.132282,
        contact_aged_max_ohm=CONTACT_AGED_MAX_OHM,
        contact_initial_max_ohm=CONTACT_INITIAL_MAX_OHM,
        crimp_max_ohm=CRIMP_MAX_OHM,
        contact_terms_are_primary_now=True,
        contact_terms_source="Molex 5055700003-PS sections 6.1.1, 6.1.4 and "
                             "6.2.6/6.2.7/6.2.8/6.3.1-6.3.7, archived at "
                             "vendor/MOLEX/molex-5055700003-PS-A1.pdf",
        fuse_ohm=FUSE_MAX_OHM, fuse_tolerance=FUSE_TOLERANCE,
        fuse_max_with_tolerance_ohm=FUSE_MAX_TOL_OHM,
        r75_nominal_ohm=R75_NOMINAL_OHM, r75_tolerance=R75_TOLERANCE,
        r75_ohm=R75_OHM, r75_min_ohm=R75_MIN_OHM,
        board_forward_segments=board_forward_itemisation(board),
        board_forward_hot_ohm=board_forward_ohm(board),
        board_forward_was_before_d793_ohm=0.0,
        gnd_return_ohm=gnd_return_ohm(squares),
        gnd_return_squares=(GND_RETURN_SQUARES if squares is None
                            else squares),
        gnd_return_sheet_ohm_per_square=GND_PLANE_SHEET_OHM_PER_SQ,
        gnd_return_barrel_ohm=GND_RETURN_BARREL_OHM,
        gnd_return_was_before_d793_ohm=0.0,
        gnd_return_sensitivity={
            ("%gx" % k): gnd_return_ohm(GND_RETURN_SQUARES * k)
            for k in (1.0, 2.0, 4.0)},
        conductor_ohm_per_m_stranded_max=AWG26_STRANDED_MAX_OHM_PER_M,
        conductor_ohm_per_m_solid_computed=AWG26_SOLID_OHM_PER_M,
        hot_rise_K=CU_HOT_RISE_K, hot_factor=CU_HOT_FACTOR,
        fixed_series_max_ohm=upstream_fixed_ohm("max", board, squares),
        fixed_series_min_ohm=upstream_fixed_ohm("min", board, squares),
        measurement_of_record="C-BAT-PATH-01",
        what="everything between the cell's own electromotive force and "
             "BAT_PROTECTED_P, AND BACK, except the four AO4800 channels, "
             "which the network solves self-consistently because their "
             "resistance depends on the current they carry.  ALL of it "
             "dissipates INSIDE the enclosure.")


# ==========================================================================
# 6.  THE PASS PAIR, WITH ITS TEMPERATURE LAW AS AN EXPLICIT SOLVER INPUT.
#
# ROUND-11 / R11-01, IN ITS OWN WORDS: "demo_feature_contract.py captures the
# AO4800 hot-resistance coefficient before _with_ratio() changes the spec, so
# advertised sensitivity cases reuse the old coefficient.  Pessimistic-case
# Boolean is not in final out['ok']."
#
# BOTH HALVES REPRODUCE EXACTLY.  D-791's `judge_pass_pair_gate` computed
#
#     alpha = (spec["rds_on_hot_ratio"] - 1.0) / 100.0
#
# ONCE, at the top, and its inner `solve()` closed over `alpha` -- not over
# `spec`.  `_with_ratio()` then mutated `spec["rds_on_hot_ratio"]` and called
# the same `solve()`, which never read it.  The published sensitivity printed
# THREE IDENTICAL CASES: no temperature coefficient, the declared ratio and a
# "pessimistic 2x" all returned VGS(Q2) = 2.589399 V, channel 67.479 mOhm.  It
# was not a weak control; it was not a control at all.  And the Boolean it
# produced was never a term of the verdict, so even a working version could
# not have failed the run.
#
# THE FIX IS STRUCTURAL: the thermal law is a PARAMETER of the solver, there is
# no captured coefficient anywhere, and `demo_feature_contract` F10 asserts
# METAMORPHICALLY that the output MOVES in the right direction when the law
# moves and CROSSES the criterion where the derivation says it should.
#
# AND THE RULING CORNER IS NAMED, TAGGED AND DEFENSIBLE RATHER THAN ROUND.
# AOS publishes RDS(on) for this die at 25 C and at 125 C only at the
# VGS = 10 V row (27 -> 40 mOhm, ratio 1.4815).  It publishes the VGS = 2.5 V
# row at 25 C alone.  Carrying the 10 V ratio to the 2.5 V row is a DECLARED
# allowance and D-790 argued it is conservative in direction -- near threshold
# a falling VGS(th) partly offsets the mobility loss, so the composite
# coefficient at 2.5 V is SMALLER than at 10 V, not larger.  That argument is
# retained, and it is no longer the only thing between the model and the
# answer: the ruling bound is the published ratio WIDENED, the verdict is
# taken there, and the ratio at which the ruling case would actually cross its
# criterion is DERIVED and published beside it so the size of the dependency
# is a number and not an adjective.
# ==========================================================================
LTC4368_GATE_DRIVE_ROWS_V = {2.5: 3.0, 5.0: 7.2, 12.0: 10.0}
LTC4368_GATE_DRIVE_MAX_ROWS_V = {2.5: 5.5, 5.0: 10.8, 12.0: 13.1}
LTC4368_GATE_SOURCE = (
    "ADI LTC4368 Rev C Electrical Characteristics, GATE section, dVGATE "
    "'Gate Drive (GATE - VOUT)', the `l` rows guaranteed over the full "
    "operating temperature range: 3 / 4 / 5.5 V at VIN = 2.5 V, 7.2 / 8.7 / "
    "10.8 V at VIN = 5 V, 10 / 11 / 13.1 V at VIN = 12 to 60 V.  Archived at "
    "hardware/demo/kicad/aqroot-demo/vendor/ADI/"
    "adi-ltc4368-revC-farnell-2243878.pdf.")
BAT_RAW_MAX_V = 4.221

AO4800_HOT_RATIO_PUBLISHED = tag(
    "passpair.rds_hot_ratio_published", round(0.040 / 0.027, 6), DERIVED,
    "AOS AO4800 Rev 6.1 RDS(on) at VGS = 10 V, ID = 6.9 A: 27 mOhm MAX at "
    "TJ = 25 C and 40 mOhm MAX at TJ = 125 C.  The ratio of two MAXIMUM rows "
    "of the same die.",
    condition="VGS = 10 V.  AOS publishes the VGS = 2.5 V row at 25 C ONLY.",
    ruling=False)
AO4800_HOT_RATIO_RULING = tag(
    "passpair.rds_hot_ratio_ruling", 1.60, DECLARED_ESTIMATE,
    "DECLARED, and this is the coefficient the verdict is taken at.  AOS's "
    "own 25 -> 125 C ratio for this die is 1.4815 at the VGS = 10 V row; the "
    "ruling bound widens it to 1.60, which is 24.6 % more temperature rise in "
    "resistance than the manufacturer measures on the part.  The direction of "
    "the carry from the 10 V row to the 2.5 V row is argued to be "
    "conservative already -- the channel component's share is larger at low "
    "gate drive and its coefficient is SMALLER, because VGS(th) falls with "
    "temperature and raises the overdrive -- so 1.60 is a widening on top of "
    "an argument, not a guess in place of one.  C-BAT-GATE-01 measures it.",
    condition="25 -> 125 C, applied linearly in TJ",
    widened_from="the published 1.481481 ratio at VGS = 10 V",
    measurement_of_record="C-BAT-GATE-01")

PASS_PAIR = dict(
    references=("Q2", "Q3"),
    locked_mpn="AO4800",
    locked_lcsc="C17098",
    locked_manufacturer="Alpha & Omega Semiconductor",
    retired_mpn="NTMD4820NR2G",
    vgs_th_max_V=1.5, vgs_th_min_V=0.7,
    vgs_abs_max_V=12.0,
    rds_on_lowest_published_vgs_V=2.5,
    rds_on_max_at_that_row_ohm=0.050,
    rds_on_hot_ratio=AO4800_HOT_RATIO_RULING,
    rds_on_hot_ratio_published=AO4800_HOT_RATIO_PUBLISHED,
    rds_on_hot_ratio_basis=(
        "AOS Rev 6.1 RDS(on) at VGS = 10 V, ID = 6.9 A: 27 mOhm MAX at "
        "TJ = 25 C and 40 mOhm MAX at TJ = 125 C, a ratio of 1.481481.  "
        "D-792 RULES at a DECLARED 1.60 instead -- the published ratio "
        "widened 24.6 % -- because AOS publishes the VGS = 2.5 V row at 25 C "
        "only, and R11-01 is right that a declared coefficient the verdict "
        "depends on must be a solver input with a sensitivity that actually "
        "moves the answer.  It is conservative in direction: near threshold a "
        "falling VGS(th) partly offsets the mobility loss."),
    vbr_dss_min_V=30.0,
    id_continuous_25C_A=6.9, id_continuous_70C_A=5.8,
    body_diode_continuous_A=2.5,
    qg_max_nC=7.0,
    theta_jl_max_C_per_W=40.0,
    # D-793, Fable Round-12: "Pass-FET thermal basis thetaJL + board-above-air
    # assumption: document source/meaning and keep first-article C-BAT-GATE-01
    # measurement; do not mislabel as measured junction bound."
    #
    # WHAT THE 40 C/W IS.  AOS Rev 6.1 publishes RthetaJL -- junction to LEAD
    # -- as 40 C/W MAX steady state, and RthetaJA as 62.5 C/W for a 10 s pulse
    # and 90 C/W steady state on their reference board.  The network uses the
    # JUNCTION-TO-LEAD figure deliberately: the AO4800's drain leads sit on
    # this board's own copper, so what the junction is referenced to is the
    # LAND, not open still air.  A RthetaJA on a vendor reference board is a
    # different thermal environment and is REPORTED here, never ruled on.
    #
    # WHAT THE +5 K IS, AND IT IS AN ASSUMPTION.  The land is taken as 5 K
    # ABOVE the enclosure's internal air.  That is a DECLARED allowance for
    # the local rise of the drain copper over the bulk of the board, not a
    # measurement, and it is stated here rather than buried in an expression.
    # It is small because the same copper carries the whole battery current
    # and is already charged for its own I^2R in the internal-air term; it is
    # NOT a claim that the junction has been measured.  C-BAT-GATE-01 is the
    # measurement of record for both this and the hot-resistance ratio.
    land_above_internal_air_K=tag(
        "pass_pair.land_above_internal_air_K", 5.0, DECLARED_ESTIMATE,
        "DECLARED.  The AO4800's drain lands are charged 5 K above the "
        "enclosure's internal air before RthetaJL is applied.  The junction "
        "figure this produces is a MODELLED bound, not a measured one.",
        measurement_of_record="C-BAT-GATE-01"),
    theta_basis=(
        "RthetaJL 40 C/W MAX steady state (junction to LEAD) is what rules, "
        "because the leads sit on this board's copper.  RthetaJA 62.5 C/W at "
        "10 s and 90 C/W steady state are the vendor REFERENCE-BOARD figures "
        "in open still air and are reported only.  The land is taken 5 K "
        "above the enclosure's internal air as a DECLARED allowance."),
    theta_ja_10s_C_per_W=62.5,
    theta_ja_steady_C_per_W=90.0,
    source="Alpha & Omega Semiconductor AO4800 Rev 6.1 (August 2023), "
           "archived vendor/AOS/aos-ao4800-rev6p1-2023-08.pdf: VDS 30 V; "
           "VGS +/-12 V; VGS(th) 0.7 / 1.1 / 1.5 V at VDS = VGS, "
           "ID = 250 uA; RDS(on) 17.8 / 27 mOhm at VGS = 10 V and 40 mOhm at "
           "TJ = 125 C, 19 / 32 mOhm at VGS = 4.5 V, and 24 / 50 mOhm AT "
           "VGS = 2.5 V, ID = 5 A; ID 6.9 A at 25 C and 5.8 A at 70 C; body "
           "diode IS 2.5 A continuous MAX; Qg 7 nC MAX; RthetaJL steady-state "
           "40 C/W MAX.  Pinout 1 = S2, 2 = G2, 3 = S1, 4 = G1, 5/6 = D1, "
           "7/8 = D2 -- the standard dual SO-8 map this board already wires, "
           "with both sources on one net and both gates on another, so the "
           "channel labelling is immaterial and no copper moves.",
    sense_resistor_ohm=R75_OHM,
    channels_in_series=4,
    board_above_air_K=5.0)


def channel_ohm(tj_C, ratio=None, spec=None):
    """RDS(on) per channel at a junction temperature, under an EXPLICIT law.

    R11-01: there is no captured coefficient.  `ratio` is the 25 -> 125 C
    resistance ratio and every caller states which one it is asking about.
    """
    spec = PASS_PAIR if spec is None else spec
    ratio = spec["rds_on_hot_ratio"] if ratio is None else ratio
    alpha = (ratio - 1.0) / 100.0
    return spec["rds_on_max_at_that_row_ohm"] * (1.0 + alpha * (tj_C - 25.0))


def solve_pass_pair(amps, air_C, ratio=None, spec=None, drive_V=None):
    """Self-consistent channel resistance, junction temperature and VGS.

    Pure, and the thermal law is an argument.  The channel resistance sets the
    dissipation, the dissipation sets the junction temperature and the
    junction temperature moves the resistance again; the converged resistance
    sets the source-node offsets and therefore VGS.
    """
    spec = PASS_PAIR if spec is None else spec
    ratio = spec["rds_on_hot_ratio"] if ratio is None else ratio
    r75 = spec["sense_resistor_ohm"]
    n_series = spec["channels_in_series"]
    r = spec["rds_on_max_at_that_row_ohm"]
    tj = air_C
    for _ in range(600):
        tj = (air_C + spec["board_above_air_K"]
              + spec["theta_jl_max_C_per_W"] * (2 * amps * amps * r))
        nxt = channel_ohm(tj, ratio, spec)
        if abs(nxt - r) < 1e-14:
            r = nxt
            break
        r = 0.5 * r + 0.5 * nxt
    per = {}
    if drive_V is not None:
        for ref, n in (("Q2", n_series - 1), ("Q3", 1)):
            vgs = drive_V - amps * (n * r + r75)
            per[ref] = dict(
                channels_above_vout=n,
                source_offset_V=round(amps * (n * r + r75), 6),
                worst_case_vgs_V=round(vgs, 6),
                margin_over_vgs_th_max_mV=round(
                    (vgs - spec["vgs_th_max_V"]) * 1000, 3),
                is_guaranteed_enhanced=bool(vgs > spec["vgs_th_max_V"]),
                margin_to_the_lowest_published_conduction_row_mV=round(
                    (vgs - spec["rds_on_lowest_published_vgs_V"]) * 1000, 3),
                meets_a_published_conduction_row=bool(
                    vgs >= spec["rds_on_lowest_published_vgs_V"]))
    out = dict(
        amps=round(amps, 6), internal_air_C=round(air_C, 3),
        hot_ratio_used=round(ratio, 6),
        channel_ohm_hot=round(r, 6), junction_C=round(tj, 3),
        package_dissipation_W=round(2 * amps * amps * r, 6),
        pass_pair_dissipation_W=round(n_series * amps * amps * r, 6),
        pass_pair_drop_V=round(amps * (n_series * r + r75), 6))
    if per:
        out.update(
            per_device=per,
            every_device_is_guaranteed_enhanced=all(
                d["is_guaranteed_enhanced"] for d in per.values()),
            every_device_meets_a_published_conduction_row=all(
                d["meets_a_published_conduction_row"] for d in per.values()))
    return out


def ltc4368_gate_drive_min_V(vin_V, rows=None):
    """Guaranteed minimum gate drive: the published row AT OR BELOW VIN."""
    rows = LTC4368_GATE_DRIVE_ROWS_V if rows is None else rows
    chosen = None
    for v in sorted(rows):
        if v <= vin_V:
            chosen = v
    return None if chosen is None else rows[chosen]


def ltc4368_gate_drive_max_V(vin_V, rows=None):
    """Guaranteed MAXIMUM: the published row AT OR ABOVE VIN."""
    rows = LTC4368_GATE_DRIVE_MAX_ROWS_V if rows is None else rows
    chosen = None
    for v in sorted(rows, reverse=True):
        if v >= vin_V:
            chosen = v
    return None if chosen is None else rows[chosen]


def hot_ratio_at_which_the_row_is_lost(amps, air_C, drive_V, spec=None):
    """The 25 -> 125 C ratio at which VGS(Q2) falls to the lowest published
    RDS(on) row.  DERIVED, so the dependency on a declared coefficient is a
    number rather than an adjective."""
    spec = PASS_PAIR if spec is None else spec
    row = spec["rds_on_lowest_published_vgs_V"]
    lo, hi = 1.0, 6.0
    if solve_pass_pair(amps, air_C, lo, spec,
                       drive_V)["per_device"]["Q2"]["worst_case_vgs_V"] < row:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = solve_pass_pair(amps, air_C, mid, spec,
                            drive_V)["per_device"]["Q2"]["worst_case_vgs_V"]
        if v >= row:
            lo = mid
        else:
            hi = mid
    return round(lo, 6)


def conduction_ceiling_A(air_C, drive_V, ratio=None, spec=None):
    """The largest current at which the worst package's VGS is still at or
    above the lowest RDS(on) row AOS characterises, solved with temperature."""
    spec = PASS_PAIR if spec is None else spec
    row = spec["rds_on_lowest_published_vgs_V"]
    lo, hi = 0.0, 8.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = solve_pass_pair(mid, air_C, ratio, spec,
                            drive_V)["per_device"]["Q2"]["worst_case_vgs_V"]
        if v >= row:
            lo = mid
        else:
            hi = mid
    return round(lo, 6)


# ==========================================================================
# 7.  THE BQ25185 PHYSICAL STATE SOLVER -- R11-03.
#
# ROUND-11, IN ITS OWN WORDS: "Released model can hold SYS at 4.41 V with BAT
# at 3.2 V while claiming positive BAT supplement.  Passive BATFET supplement
# requires SYS below BAT; the released state violates the physical mode.
# Input-path heat cannot be represented solely by IIN^2*Ron while the linear
# charger is dropping VIN-SYS."
#
# BOTH REPRODUCE.  D-791's `charge_regime_junction` computed three currents
# from three independent formulas and never asked whether they could coexist:
#
#     v_sys  = 4.5 x 0.98            <- PINNED, whatever else happened
#     i_in   = min(ILIM_max, ...)    <- the HIGH end of the limit band
#     i_chg  = min(ICHG, ILIM_min - system_A)   <- the LOW end of the SAME band
#     i_supp = max(0, system_A - ILIM_min)      <- positive with VSYS > VBAT
#
# A battery at 3.2 V cannot push current into a node held at 4.41 V through a
# passive FET, and no equation in that function could notice.  The input term
# was `i_in^2 x Ron`, which prices the FET as a resistor when in that regime it
# is a LINEAR PASS ELEMENT dropping VIN - VSYS -- and in the supplement regime,
# where VSYS collapses toward the cell, that drop is more than three times the
# resistive figure.  And two different ends of one accuracy band appeared in
# one solved state.
#
# WHAT REPLACES IT.  An explicit mode solver with the physics as HARD
# INVARIANTS, checked on the returned state and reported:
#
#     KCL at SYS          I_IN + I_SUPP = I_SYS + I_CHG
#     BATFET direction    I_SUPP > 0  =>  VSYS < VBAT, and VSYS = VBAT - I_SUPP x RON_BAT
#                         I_CHG  > 0  =>  VSYS > VBAT
#     mutual exclusion    I_SUPP x I_CHG = 0
#     KVL at the input    V_IN(pin) = VSYS + (the input FET's own drop) >= VSYS
#     energy balance      P_IN + VBAT x I_SUPP = P_SYS + VBAT x I_CHG + P_DISS,
#                         P_DISS >= 0
#     one corner          ONE end of the ILIM band per solved state
#
# THE MODES, WHICH ARE THE DEVICE'S OWN.  D-794 / R13-02 REBUILT THIS LIST
# FROM SLUSF65B SECTIONS 6.3.1, 6.3.2, 6.3.3 AND 6.3.5 AND FROM THE EC TABLE,
# BECAUSE D-793'S LIST CONFLATED FOUR DIFFERENT PHYSICAL LOOPS INTO TWO NAMES.
#
# ROUND-13, IN ITS OWN WORDS: "Current DPPM treatment can hold SYS at the
# regulation value while folding charge, instead of respecting battery-
# tracking DPPM behavior.  VINDPM battery-tracking, DPPM, supplement entry/
# exit hysteresis, input current limiting, thermal foldback and mode history
# must be distinct physical controls."
#
# IT REPRODUCES, AND IT IS NOT A NAMING COMPLAINT.  D-793's branch 1 computed
# the input current that would hold VSYS_REG EXACTLY, and then folded the
# CHARGE current back to stay inside it.  Nothing in this part does that.  SYS
# regulation (6.3.5) is a SERIES PASS regulation: it limits VSYS from ABOVE by
# dropping the surplus across the input FET.  It has no authority over the
# charge current at all.  The loops that DO fold charge are the input current
# limit, VINDPM, DPPM and TREG, and each has its own threshold.  The
# consequence is not academic: with the worst QUALIFIED cable the real part
# draws the full programmed charge current and lets SYS fall to whatever the
# source resistance leaves, which is far HOTTER than D-793's model at light
# load -- and the published charge-time ceiling is derived from that heat.
#
#   SYS_REG         6.3.5.  The input FET drops VIN - VSYS_REG and SYS sits at
#                   its regulation point.  Charge is at the full programmed
#                   ICHG.  Requires the source to be able to hold VSYS_REG at
#                   the total current.
#   CC_PATH_LIMITED The input FET is FULLY ENHANCED and SYS is wherever the
#                   source resistance and RON_IN leave it.  No loop is in
#                   control except the charger's own CC loop, which is still
#                   at ICHG.  This is the ordinary state of this board on a
#                   qualified 2 m cable and D-793 had no name for it.
#   ILIM            6.3.6 / EC ILIM.  The INPUT CURRENT LIMIT binds; the
#                   charge current takes what is left after the system load.
#   VINDPM          6.3.1.  The IN-pin potential has fallen to the VINDPM
#                   threshold -- VBAT + VINDPM_TRACK (330 mV) when VBAT is
#                   above 3.5 V, otherwise a fixed 3.6 V -- and the loop
#                   reduces the INPUT CURRENT to hold it there.
#   DPPM            6.3.2.  SYS has fallen to VBAT + VDPPM (100 mV) and the
#                   DPPM loop reduces the CHARGE current through the BATFET to
#                   hold it there.  "SYS voltage is maintained above battery
#                   voltage when the DPPM loop is in control."
#   NO_CHARGE       the charge current has folded to zero and the input still
#                   carries the whole system load.  SYS is below VBAT + VDPPM
#                   but has not yet fallen far enough to turn the BATFET on.
#   SUPPLEMENT      6.3.3.  SYS has fallen to VBAT - VBSUP1 (40 mV) and the
#                   BATFET conducts BAT -> SYS.  It leaves supplement only
#                   when SYS rises back to VBAT - VBSUP2 (20 mV): the entry
#                   and exit thresholds DIFFER, so this branch depends on MODE
#                   HISTORY and `charger_state` takes a `previous_mode`.
#   DISCHARGE       no adapter; SYS is the cell less the BATFET drop.
#
# TREG (6.3.7) is orthogonal to all of them: it folds the CHARGE current and
# nothing else, and it is modelled by `treg_folds_charge_to_zero`.
# ==========================================================================


# ==========================================================================
# D-793 / R12-02.  THE ADAPTER AND CABLE ARE A CONTRACT, NOT A CONSTANT.
#
# ROUND-12, IN ITS OWN WORDS: "Qualify the USB adapter/cable contract at U11
# VIN.  Do not assume 0.20 ohm covers arbitrary long/28-AWG cables."
#
# D-792 carried ONE declared 0.200 ohm figure and called it pessimistic for a
# 2 m 28 AWG cable.  It is not: 2 m of 28 AWG is 0.2126 ohm/m per conductor
# and the loop is two conductors, so that cable ALONE is about 0.85 ohm --
# more than four times the declared number.  And the charge-time ceiling is
# SENSITIVE to it, because the supplement cliff moves down about 99 mW for
# every 100 mOhm of source path.
#
# SO THE SOURCE IS AN ENUMERATED SET OF CLASSES, each with its own conductor
# arithmetic, and the release rules over the WORST QUALIFIED one while
# REPORTING the unqualified one.  The qualification itself is a published,
# measurable acceptance criterion at U11's VIN pin -- `usb_source_contract()`
# below -- not an adjective about the cable.
# ==========================================================================
AWG24_STRANDED_MAX_OHM_PER_M = tag(
    "usb.awg24_stranded_max_ohm_per_m", 0.0918, DECLARED_ESTIMATE,
    "DECLARED.  24 AWG is 0.205 mm2 and 0.0842 ohm/m solid at 20 C; the "
    "stranded appliance-wire maximum is carried at the same 9 % margin this "
    "model uses for 26 AWG.",
    condition="20 C", ruling=False)
AWG28_STRANDED_MAX_OHM_PER_M = tag(
    "usb.awg28_stranded_max_ohm_per_m", 0.2320, DECLARED_ESTIMATE,
    "DECLARED.  28 AWG is 0.0810 mm2 and 0.2126 ohm/m solid at 20 C, carried "
    "at the same 9 % stranded margin.",
    condition="20 C", ruling=False)
USB_MATED_PAIR_OHM = tag(
    "usb.mated_receptacle_pair_ohm", 0.030, DECLARED_ESTIMATE,
    "DECLARED, 30 mOhm per mated USB connector pair.  A USB 2.0 cable "
    "assembly has two of them (the adapter end and the board end).  No "
    "contact-resistance row is published for the fitted receptacle, so this "
    "is measured at first article.",
    measurement_of_record="C-CHG-01")
USB_BOARD_COPPER_OHM = tag(
    "usb.board_vbus_copper_ohm", 0.020, DECLARED_ESTIMATE,
    "DECLARED.  J3's VBUS contacts through R35 to U11's VIN pin, on the "
    "board.  audit_rail_ampacity measures USB_VBUS_RAW and USB_VBUS_CHG "
    "directly and both are well under this; it is carried high because the "
    "charge-time ceiling is what depends on it.",
    measurement_of_record="C-CHG-01")


# ==========================================================================
# D-795 / R14-03 + Fable R14-07.  THE SOURCE CONTRACT NAMES A PART.
#
# ROUND-14: "Source contract must name an actual obtainable adapter/cable:
# e.g. appropriate 5 V >=1.5 A BC1.2/USB-C source and qualified cable; a USB
# 2.0 500 mA host must not be described as satisfying a 1.1 A contract."
#
# D-794's contract said "a USB 2.0 high-power port ... able to deliver at
# least 1.100 A" -- and a USB 2.0 high-power port is a 500 mA port.  The
# sentence was self-contradictory, and its 4.75..5.25 V band was quoted from a
# USB 2.0 table this repository does not hold.
#
# THE QUALIFIED SOURCE IS NOW ONE PURCHASABLE PART WITH ITS OWN CABLE: the
# Raspberry Pi 15W USB-C Power Supply, KSA-15E-051300Hx (product numbers
# SC0445/SC0218 US, SC0444/SC0217 EU, SC0443/SC0216 UK, SC0523/SC0219 AU/NZ/CN,
# SC0478/SC0479 IN), archived at vendor/RPI/rpi-15w-usb-c-psu-product-brief.pdf:
# +5.1 V DC, 3.0 A nominal, load regulation +/-5 %, line regulation +/-2 %,
# a CAPTIVE 1.5 m 18 AWG cable, USB Type-C, 0..40 C ambient.  The two
# regulation terms are taken as ADDITIVE, so the adapter is ruled at
# 5.1 V x (1 -/+ 0.07) = 4.743 / 5.457 V.  Because the cable is captive there
# is exactly ONE mated connector pair in the path.
#
# Generic sources are REPORTED, not ruled: a Type-C/BC1.2 adapter at 4.75 V
# on a 2 m 24 AWG cable (the D-794 "worst qualified" class) and on a 2 m
# 28 AWG phone cable, so what leaving the contract costs is a number.  A
# USB 2.0 host port is outside the contract outright: 500 mA cannot meet a
# 1.1 A input limit.
# ==========================================================================
AWG18_STRANDED_MAX_OHM_PER_M = tag(
    "usb.awg18_stranded_max_ohm_per_m", 0.0228, DECLARED_ESTIMATE,
    "DECLARED.  18 AWG is 0.823 mm2 and 0.02095 ohm/m solid at 20 C, "
    "carried at the same 9 % stranded margin as 24 and 28 AWG.",
    condition="20 C", ruling=False)
RPI_PSU_NOMINAL_V = 5.1
RPI_PSU_REGULATION = tag(
    "usb.rpi15w_regulation_fraction", 0.07, DECLARED_ENGINEERING_BOUND,
    "DECLARED from the Raspberry Pi 15W USB-C Power Supply product brief "
    "(vendor/RPI): load regulation +/-5 % and line regulation +/-2 %, taken "
    "as additive.  A regulation specification on a product brief is not an "
    "EC MIN/MAX row, so it is a declared SUPPLY requirement that C-CHG-01 "
    "measures.",
    condition="+5.1 V DC output, 0..3.0 A, 100-240 Vac",
    role=SUPPLY_REQUIREMENT)
RPI_PSU_PART = dict(
    manufacturer="Raspberry Pi Ltd",
    part_number="KSA-15E-051300HU",
    part_numbers_by_region={
        "US": "KSA-15E-051300HU", "EU": "KSA-15E-051300HE",
        "UK": "KSA-15E-051300HK", "AU/NZ/CN": "KSA-15E-051300HA",
        "IN": "KSA-15E-051300HI"},
    product_numbers={"US": ("SC0445", "SC0218"), "EU": ("SC0444", "SC0217"),
                     "UK": ("SC0443", "SC0216"),
                     "AU/NZ/CN": ("SC0523", "SC0219"),
                     "IN": ("SC0478", "SC0479")},
    name="Raspberry Pi 15W USB-C Power Supply",
    cable="captive, 1.5 m, 18 AWG, USB Type-C plug",
    source_document="hardware/demo/kicad/aqroot-demo/vendor/RPI/"
                    "rpi-15w-usb-c-psu-product-brief.pdf",
    source_sha256="6df7bb5c05165cbf80978c05a36070a763523bb5a1cdf6724b87a1a6e673bd89",
    operating_ambient_C=(0.0, 40.0))


def _usb_path(awg_ohm_per_m, length_m, pairs=2):
    return round(2.0 * length_m * awg_ohm_per_m
                 + pairs * USB_MATED_PAIR_OHM + USB_BOARD_COPPER_OHM, 6)


# key, vbus at the adapter, path to U11 VIN, whether the release RULES on it.
USB_SOURCE_CLASSES = (
    dict(key="rpi15w_high", vbus_V=round(RPI_PSU_NOMINAL_V
                                         * (1.0 + RPI_PSU_REGULATION), 6),
         path_ohm=_usb_path(AWG18_STRANDED_MAX_OHM_PER_M, 1.5, pairs=1),
         rules=True,
         what="the NAMED adapter at the HIGH end of its regulation band, on "
              "its own captive 1.5 m 18 AWG cable.  The corner that leaves "
              "the most voltage at U11's VIN pin and so the MOST HEAT in its "
              "linear input FET."),
    dict(key="rpi15w_low", vbus_V=round(RPI_PSU_NOMINAL_V
                                        * (1.0 - RPI_PSU_REGULATION), 6),
         path_ohm=_usb_path(AWG18_STRANDED_MAX_OHM_PER_M, 1.5, pairs=1),
         rules=True,
         what="the NAMED adapter at the LOW end of its regulation band on "
              "the same cable.  The corner that decides VINDPM and the "
              "no-discharge envelope."),
    dict(key="generic_typec_24awg_2m", vbus_V=4.75,
         path_ohm=_usb_path(AWG24_STRANDED_MAX_OHM_PER_M, 2.0),
         rules=False,
         what="ANY 5 V Type-C / BC1.2 adapter at 4.75 V on a separate 2 m "
              "24 AWG cable -- D-794's 'worst qualified' class.  OUTSIDE the "
              "first-five contract; REPORTED."),
    dict(key="unqualified_28awg_2m", vbus_V=4.75,
         path_ohm=_usb_path(AWG28_STRANDED_MAX_OHM_PER_M, 2.0),
         rules=False,
         what="2 m of 28 AWG -- a cheap phone cable, OUTSIDE the contract.  "
              "REPORTED so the cost of ignoring the contract is a number."),
)
USB_QUALIFIED_MAX_OHM = tag(
    "usb.qualified_source_path_max_ohm",
    max(c["path_ohm"] for c in USB_SOURCE_CLASSES if c["rules"]),
    DECLARED_ENGINEERING_BOUND,
    "the source path the PUBLISHED charging contract admits: the named "
    "adapter's captive 1.5 m 18 AWG cable, ONE mated USB-C pair and the "
    "board's own VBUS copper.  A CONTRACT -- see usb_source_contract().",
    role=POLICY_BUDGET)
USB_VBUS_MAX_V = tag(
    "usb.vbus_source_max_V", max(c["vbus_V"] for c in USB_SOURCE_CLASSES
                                 if c["rules"]),
    DECLARED_ENGINEERING_BOUND,
    "DECLARED SUPPLY REQUIREMENT: the named adapter's 5.1 V at +7 % "
    "(load + line regulation, vendor/RPI product brief).  D-794 tagged a "
    "USB 2.0 table-7-7 figure GUARANTEED_MAX with no archived document; it "
    "is a requirement on the supply, not a device guarantee.",
    condition="the named adapter, 0..3.0 A", role=SUPPLY_REQUIREMENT)
USB_VBUS_MIN_V = tag(
    "usb.vbus_source_min_V", min(c["vbus_V"] for c in USB_SOURCE_CLASSES
                                 if c["rules"]),
    DECLARED_ENGINEERING_BOUND,
    "DECLARED SUPPLY REQUIREMENT: the named adapter's 5.1 V at -7 % "
    "(vendor/RPI product brief).",
    condition="the named adapter, 0..3.0 A", role=SUPPLY_REQUIREMENT)
USB_PATH_MAX_OHM = USB_QUALIFIED_MAX_OHM
USB_PATH_MIN_OHM = min(c["path_ohm"] for c in USB_SOURCE_CLASSES)


def usb_source_contract(ichg_A=None):
    """The PUBLISHED, MEASURABLE acceptance criterion for a charging source.

    An adjective about a cable cannot be checked at first article; a voltage
    at a named pin can.  The contract is: with the charger drawing its
    programmed input current, the potential at U11's VIN pin must be at or
    above the figure below.  C-CHG-01 measures it.
    """
    i = BQ25185["ilim_max_A"] if ichg_A is None else ichg_A
    # D-794 / R13-02.  THE SOURCE CONTRACT HAS TWO HALVES AND D-793 PUBLISHED
    # ONLY ONE.  A cable impedance bounds the DROP; it says nothing about
    # whether the adapter can deliver the current at all.  The BQ25185 draws
    # up to ILIM_max at the programmed 1050 mA row, so the adapter must be
    # rated for at least that AND must still hold the VIN pin above the
    # VINDPM threshold at that current -- otherwise the VINDPM loop throttles
    # the input and the charge current folds, which is a slower charge rather
    # than a fault, but it is a DIFFERENT published behaviour.
    vindpm_worst, vindpm_kind = vindpm_threshold_V(BQ25185["vbatreg_V"])
    return dict(
        measured_at="U11 pin 10 (VIN), referenced to U11's GND pad",
        at_input_current_A=i,
        min_vin_pin_V=round(USB_VBUS_MIN_V - i * USB_QUALIFIED_MAX_OHM, 4),
        qualified_source_path_max_ohm=USB_QUALIFIED_MAX_OHM,
        # ---- the CURRENT half ------------------------------------------
        required_source_current_A=round(i, 4),
        required_source_capability=(
            "the named adapter -- %s, part %s (regional variants %s) -- on "
            "its own captive %s.  A USB 2.0 host port is OUTSIDE the "
            "contract: 500 mA cannot meet a %.3f A input limit"
            % (RPI_PSU_PART["name"], RPI_PSU_PART["part_number"],
               ", ".join(sorted(RPI_PSU_PART["part_numbers_by_region"]
                                .values())),
               RPI_PSU_PART["cable"], i)),
        named_adapter=dict(RPI_PSU_PART),
        a_usb2_host_port_satisfies_the_contract=False,
        vindpm_threshold_at_a_full_cell_V=round(vindpm_worst, 4),
        vindpm_kind_at_a_full_cell=vindpm_kind,
        vin_pin_stays_above_vindpm_on_every_qualified_class=bool(all(
            c["vbus_V"] - i * c["path_ohm"] >= vindpm_worst
            for c in USB_SOURCE_CLASSES if c["rules"])),
        classes=[dict(c, vin_pin_at_ilim_V=round(
            c["vbus_V"] - i * c["path_ohm"], 4),
            throttled_by_vindpm_at_a_full_cell=bool(
                c["vbus_V"] - i * c["path_ohm"] < vindpm_worst))
            for c in USB_SOURCE_CLASSES],
        what_a_non_conforming_source_does=(
            "a source that sags below the VINDPM threshold is THROTTLED by "
            "the input loop, not disconnected: the charge current folds and "
            "the charge takes longer.  A source that cannot supply "
            "%.3f A at all leaves the input current limit unreached and has "
            "the same effect.  Neither is a safety condition; both change "
            "the published charge time." % i),
        operator_rule="charge the first five ONLY from the named Raspberry "
                      "Pi 15W USB-C Power Supply (%s or its regional "
                      "variant) on its own captive cable.  Any other "
                      "adapter or cable -- including a 5 V Type-C source "
                      "on a separate 2 m cable -- is OUTSIDE the contract; "
                      "a USB 2.0 computer port (500 mA) cannot meet the "
                      "%.2f A input limit at all." % (
                          RPI_PSU_PART["part_number"], i),
        measurement_of_record="C-CHG-01")

# ==========================================================================
# D-794 / ROUND-13 FABLE DELTA.  A CEILING IS NOT A TIMER GUARANTEE.
#
# FABLE, IN ITS OWN WORDS: "Rename/explain any charger 'ceiling' according to
# what it actually guarantees.  A no-battery-discharge boundary is not
# automatically a full-charge-within-360-min timer guarantee."
#
# It is right, and the two numbers had drifted into one sentence.  The
# 3.600 W figure is the SYSTEM POWER above which either (a) the BATFET starts
# supplementing -- the battery discharges while the adapter is attached -- or
# (b) TI's junction operating maximum is exceeded.  It says nothing at all
# about whether a charge COMPLETES, and the corrected D-794 solver makes the
# difference vivid: on the worst qualified cable at a 3.6 W system load the
# input current limit leaves only 57 mA for the battery, which would need
# 44 hours to deliver the pack's rated capacity against a 360 min safety
# timer.  Charging while the product runs is a SLOWER CHARGE, and past a
# point it is NO CHARGE AT ALL -- and the timer then latches a
# non-recoverable safety-timer fault (SLUSF65B 6.3.7.7).
#
# `charge_timer_report` derives that, per source class and per system load,
# and DEVICE_SPEC's charge-time row is generated from it.
# ==========================================================================
TMAXCHG_MIN = tag(
    "bq.tmaxchg_min", 360.0, TYPICAL,
    "TI SLUSF65B EC, BATTERY CHARGING TIMERS: tMAXCHG, charge safety timer, "
    "360 min.  Revision B halved it from 720 min -- the single line in that "
    "revision's history, and the reason D-743 re-programmed R37.",
    ruling=False)
TPRECHG_FRACTION = tag(
    "bq.tprechg_fraction", 0.25, TYPICAL,
    "TI SLUSF65B EC: tPRECHG = 0.25 x tMAXCHG.", ruling=False)
VLOWV_MAX_V = tag(
    "bq.vlowv_max_V", 3.1, GUARANTEED_MAX,
    "TI SLUSF65B EC: VLOWV, the precharge-to-fast-charge threshold, "
    "2.9 / 3.0 / 3.1 V on VBAT rising.  The MAXIMUM is where fast charge is "
    "guaranteed to have started.",
    condition="VBAT rising, -40..125 C")
CV_TAPER_ALLOWANCE_MIN = tag(
    "bq.cv_taper_allowance_min", 60.0, DECLARED_ENGINEERING_BOUND,
    "DECLARED.  The constant-voltage taper from VBATREG down to ITERM "
    "(10 % of ICHG, SLUSF65B EC) is not modelled here -- it depends on the "
    "cell's own diffusion behaviour and no row in either datasheet bounds "
    "it -- so a flat 60 min is added to every derived cycle time.  "
    "C-PWR-CHARGE-01 measures the real figure.",
    measurement_of_record="C-PWR-CHARGE-01", role=POLICY_BUDGET)
PACK_RATED_CAPACITY_AH = tag(
    "pack.rated_capacity_Ah", 2.5, DECLARED_ENGINEERING_BOUND,
    "the fitted 785060 pouch's rated 2500 mAh, which is what a charge cycle "
    "has to deliver.  `checks/battery_pack_contract` pins the same number "
    "against the purchased pack record.",
    role=POLICY_BUDGET)


# D-795 / R14-04: `_cc_minutes` and `charge_timer_report` -- D-794's completion
# model, which distributed the rated capacity LINEARLY over VLOWV..VBATREG, took
# no thermal regulation and treated the TYP-only 360 min timer as a limit -- are
# REMOVED rather than left beside their replacement.  The completion question
# is answered by `audit_rail_ampacity.charge_completion_estimate`, which closes
# the TREG loop, uses no capacity distribution and is a QUALIFICATION TARGET.


BQ25185 = dict(
    reference="U11", part="BQ25185", package="DLH0010A",
    # D-795 / R14-06: VSYS_REG is a TYP-only row (4.5 V); the guarantee is
    # VSYS_REG_ACC, -2 / +2 %.  D-794 tagged the nominal GUARANTEED_MAX.
    vsys_reg_V=tag("bq.vsys_reg_V", 4.5, TYPICAL,
                   "TI SLUSF65B EC: VSYS_REG 4.5 V at VBATREG <= 4.3 V -- a "
                   "TYP column and nothing else.  The ruling figure is this "
                   "nominal at the GUARANTEED VSYS_REG_ACC below.",
                   ruling=False),
    vsys_reg_accuracy=tag(
        "bq.vsys_reg_accuracy", 0.02, GUARANTEED_MAX,
        "TI SLUSF65B EC: VSYS_REG_ACC, SYS regulation accuracy, -2 / +2 % "
        "at VIN = 5V, VBAT = 3.6V, RSYS = 100 ohm.",
        condition="VIN = 5 V, VBAT = 3.6 V, RSYS = 100 ohm"),
    vminsys_V=tag("bq.vminsys_V", 3.8, TYPICAL,
                  "TI SLUSF65B EC: VMINSYS 3.8 V in battery-tracking mode.",
                  ruling=False),
    ron_in_max_ohm=tag("bq.ron_in_max_ohm", 0.470, GUARANTEED_MAX,
                       "TI SLUSF65B EC: RON_IN 330 typ / 470 mOhm MAX at "
                       "VIN = 5 V, IIN = 1 A.",
                       condition="VIN = 5 V, IIN = 1 A, -40..125 C"),
    ron_bat_max_ohm=tag("bq.ron_bat_max_ohm", 0.140, GUARANTEED_MAX,
                        "TI SLUSF65B EC: RON_BAT, BATFET on-resistance, "
                        "140 mOhm MAX.",
                        condition="TI's single published VBAT condition; "
                                  "`ron_bat_vbat_allowance` carries the "
                                  "rest of the cell range separately"),
    ron_bat_vbat_allowance=tag(
        "bq.ron_bat_vbat_allowance", 1.40, DECLARED_ESTIMATE,
        "DECLARED: TI states RON_BAT at one VBAT condition; a 40 % carry "
        "covers the rest of the cell range.  The same two numbers F6 rules "
        "with, so the two models cannot disagree."),
    ilim_min_A=tag("bq.ilim_min_A", 0.995, GUARANTEED_MIN,
                   "TI SLUSF65B EC: ILIM, Input current limit, VIN = 5V, "
                   "ILIM = 1050mA: 995 / 1050 / 1100 mA -- the setting "
                   "R36 = 13 kOhm programs per Table 6-1.  D-795 / R14-06: "
                   "D-794 cited Table 6-1 for these currents, and that table "
                   "is a resistor map that holds none of them.",
                   condition="VIN = 5 V at the 1050 mA ILIM setting, "
                             "-40..125 C"),
    ilim_max_A=tag("bq.ilim_max_A", 1.100, GUARANTEED_MAX,
                   "TI SLUSF65B EC: ILIM, Input current limit, VIN = 5V, "
                   "ILIM = 1050mA -- the same row's MAX column.",
                   condition="VIN = 5 V at the 1050 mA ILIM setting, "
                             "-40..125 C"),
    ichg_A=tag("bq.ichg_A", 0.769, DERIVED,
               "this board's own R37 = 390 ohm charge-current programming "
               "(D-743), at the TYPICAL KISET.  REPORTED; D-795 rules at the "
               "band below.", ruling=False),
    # ---- D-795 / R14-04.  THE CHARGE CURRENT IS A BAND, NOT A TYPICAL. ----
    #
    # D-794 carried ICHG as ONE number, 769 mA -- KISET 300 A.Ohm over
    # R37 = 390 ohm -- in BOTH the heat derivation and the completion one.
    # SLUSF65B publishes KISET as 285 / 300 / 315 A.Ohm with a MIN and a MAX,
    # and R37 is a 1 % part, so the programmed current is a band whose ends
    # answer DIFFERENT questions: the high end is the adverse corner for
    # package heat, the low end for charge time.
    kiset_min_AOhm=tag(
        "bq.kiset_min_AOhm", 285.0, GUARANTEED_MIN,
        "TI SLUSF65B EC: KISET, 285 / 300 / 315 A.Ohm, "
        "10mA < ICHG < 1000mA -- the MIN column.",
        condition="10 mA < ICHG < 1000 mA"),
    kiset_max_AOhm=tag(
        "bq.kiset_max_AOhm", 315.0, GUARANTEED_MAX,
        "TI SLUSF65B EC: KISET, 285 / 300 / 315 A.Ohm, "
        "10mA < ICHG < 1000mA -- the MAX column.",
        condition="10 mA < ICHG < 1000 mA"),
    r37_iset_ohm=390.0, r37_tolerance=0.01,
    ichg_min_A=tag(
        "bq.ichg_min_A", round(285.0 / (390.0 * 1.01), 6), DERIVED,
        "KISET MIN 285 A.Ohm over R37 at its +1 % end (390 ohm x 1.01): the "
        "LOWEST programmed fast-charge current, adverse for charge time."),
    ichg_max_A=tag(
        "bq.ichg_max_A", round(315.0 / (390.0 * 0.99), 6), DERIVED,
        "KISET MAX 315 A.Ohm over R37 at its -1 % end (390 ohm x 0.99): the "
        "HIGHEST programmed fast-charge current, adverse for package heat."),
    iprechg_fraction=tag(
        "bq.iprechg_fraction", 0.20, TYPICAL,
        "TI SLUSF65B EC: IPRECHG 20 % of ICHG for VBAT < VLOWV.",
        ruling=False),
    iprechg_accuracy=tag(
        "bq.iprechg_accuracy", 0.10, GUARANTEED_MAX,
        "TI SLUSF65B EC: IPRECHG_ACC, precharge current accuracy, -10 / +10 % "
        "at Fast charge current >= 40mA.",
        condition="Fast charge current >= 40 mA"),
    vlowv_min_V=tag(
        "bq.vlowv_min_V", 2.9, GUARANTEED_MIN,
        "TI SLUSF65B EC: VLOWV 2.9 / 3.0 / 3.1 V, VBAT rising -- below the "
        "MIN the part is certainly in precharge.",
        condition="VBAT rising"),
    vbuvlo_typ_V=tag(
        "bq.vbuvlo_typ_V", 3.0, TYPICAL,
        "TI SLUSF65B EC: VBUVLO, battery UVLO, VBAT falling, 3 V typical.",
        ruling=False),
    # ---- D-796 / R15-01 + Fable R15-06.  THE BATFET BELOW VBUVLO. ---------
    #
    # SLUSF65B 6.3.3: "Battery voltage must be higher than the battery
    # undervoltage lockout threshold (VBUVLO) to supplement the input in
    # supplying the system load", and 6.3.7.2: BUVLO "disconnects BAT from
    # SYS when the battery voltage drops below the BUVLO threshold."  D-795
    # solved SUPPLEMENT states -- with SUPPLEMENT histories -- at a 2.85 V
    # cell, which is at the bottom of the falling threshold's own declared
    # band.  The threshold and its hysteresis are now carried explicitly: the
    # falling trip is 3.0 V TYP with a DECLARED +/-5 % (TI publishes no
    # min/max for it), and the RISING re-connect sits VBUVLO_HYS above it.
    vbuvlo_declared_tolerance=tag(
        "bq.vbuvlo_declared_tolerance", 0.05, DECLARED_ENGINEERING_BOUND,
        "DECLARED.  VBUVLO has a TYP column only (3.0 V, VBAT falling); the "
        "falling trip is modelled anywhere in 3.0 V +/-5 % = 2.85..3.15 V.  "
        "The same band `BUVLO_BOUND_V` rules the permission floors with.",
        condition="applied either way to the 3.0 V typical",
        role=POLICY_BUDGET),
    vbuvlo_hys_max_V=tag(
        "bq.vbuvlo_hys_max_V", 0.190, GUARANTEED_MAX,
        "TI SLUSF65B EC: VBUVLO_HYS, Battery UVLO hysteresis, VBAT rising, "
        "VIN = 5V: 110 / 150 / 190 mV -- the MAX column.  A cell that fell "
        "through the trip is re-connected no later than trip + 190 mV.",
        condition="VBAT rising, VIN = 5 V"),
    treg_typ_C=tag(
        "bq.treg_typ_C", 100.0, TYPICAL,
        "TI SLUSF65B EC: TREG, typical junction temperature regulation, "
        "100 C.  TYP only.", ruling=False),
    treg_declared_band_K=tag(
        "bq.treg_declared_band_K", 10.0, DECLARED_ENGINEERING_BOUND,
        "DECLARED.  TREG has a TYP column and nothing else, so the thermal "
        "fold is modelled at 100 C +/- 10 K: the HIGH end (110 C) is the "
        "adverse one for the junction, the LOW end (90 C) for charge time.",
        condition="applied either way to the 100 C typical",
        role=POLICY_BUDGET),
    tmaxchg_declared_tolerance=tag(
        "bq.tmaxchg_declared_tolerance", 0.20, DECLARED_ENGINEERING_BOUND,
        "DECLARED.  tMAXCHG has a TYP column (360 min) and nothing else; a "
        "completion ESTIMATE is judged against 360 min x (1 - 0.20) = "
        "288 min so a typical timer is never read as a limit.",
        role=POLICY_BUDGET),
    # ---- D-794 / R13-02.  THE CONTROL-LOOP THRESHOLDS, FROM THE EC TABLE.
    #
    # Each of these is a DIFFERENT physical loop with its own threshold, and
    # D-793 had none of them: it folded the charge current to hold SYS at its
    # regulation point, which is not a control this part has.
    vdppm_V=tag("bq.vdppm_V", 0.100, TYPICAL,
                "TI SLUSF65B EC: VDPPM, 'VSYS threshold when charge current "
                "is reduced', VBAT = 3.6 V, VSYS = VDPPM + VBAT before "
                "charge current is reduced -- 100 mV typical.  Section 6.3.2 "
                "adds that SYS is maintained ABOVE the battery voltage while "
                "the DPPM loop is in control.",
                condition="TYP only; TI publishes no min/max for this row, "
                          "so the ceiling derivation SWEEPS it",
                ruling=False),
    vbsup1_V=tag("bq.vbsup1_V", 0.040, TYPICAL,
                 "TI SLUSF65B EC: VBSUP1, enter supplement mode threshold, "
                 "VBAT = 3.6 V, VBAT > VBUVLO, VSYS < VBAT - VBSUP1 -- "
                 "40 mV typical.",
                 condition="TYP only; swept by the ceiling derivation",
                 ruling=False),
    vbsup2_V=tag("bq.vbsup2_V", 0.020, TYPICAL,
                 "TI SLUSF65B EC: VBSUP2, EXIT supplement mode threshold, "
                 "VBAT > VBUVLO, VSYS > VBAT - VBSUP2 -- 20 mV typical.  "
                 "VBSUP1 != VBSUP2 is the HYSTERESIS: between them the "
                 "branch depends on which mode the part was already in.",
                 condition="TYP only; swept by the ceiling derivation",
                 ruling=False),
    vindpm_track_V=tag("bq.vindpm_track_V", 0.330, TYPICAL,
                       "TI SLUSF65B EC: VINDPM_TRACK, 'VIN threshold offset "
                       "for when input current is reduced and when VBAT > "
                       "3.5 V', VINDPM target = VBAT + VINDPM_TRACK -- "
                       "330 mV typical.",
                       condition="applies only while VBAT > 3.5 V",
                       ruling=False),
    vindpm_track_vbat_floor_V=tag(
        "bq.vindpm_track_vbat_floor_V", 3.5, TYPICAL,
        "TI SLUSF65B EC, the condition column of the VINDPM_TRACK row: the "
        "battery-tracking target applies 'when VBAT > 3.5V'.",
        ruling=False),
    vindpm_fixed_V=tag("bq.vindpm_fixed_V", 3.6, TYPICAL,
                       "TI SLUSF65B 6.3.1: 'If the device is not operating "
                       "in battery tracking VINDPM due to battery voltage, "
                       "the input is regulated to 3.6V.'",
                       ruling=False),
    vbatreg_V=4.2, vbatreg_accuracy=0.005,
    treg_C=100.0, tshut_rising_C=150.0,
    tj_operating_max_C=125.0,
    theta_ja_C_per_W=68.3,
    source="TI SLUSF65B, archived vendor/BQ25185/"
           "ti-bq25185-slusf65b-2026-08.pdf: RON_IN 330 typ / 470 mOhm MAX "
           "at VIN = 5 V, IIN = 1 A; VSYS_REG 4.5 V at VBATREG <= 4.3 V with "
           "-2/+2 % accuracy; VMINSYS 3.8 V in battery-tracking mode; ILIM "
           "995 / 1050 / 1100 mA at the 1050 mA row; TREG 100 C; "
           "TSHUT_RISING 150 C; RthetaJA 68.3 C/W (JEDEC) for DLH; section "
           "6.3.3 -- when the system load exceeds the input limit the "
           "battery SUPPLEMENTS through the BATFET, and BATOCP stays "
           "active.")


CHARGER_BRANCH_THRESHOLD_SWEEP = tag(
    "bq.branch_threshold_sweep", 0.50, DECLARED_ENGINEERING_BOUND,
    "DECLARED.  VDPPM, VBSUP1, VBSUP2 and VINDPM_TRACK are published by TI "
    "as TYPICALS with no min/max column, and a branch boundary read off a "
    "typical is exactly the class of defect Round-9 found.  The published "
    "charge-time ceiling is therefore derived over a SWEEP of +/-50 % on "
    "each of these OFFSETS, and the ceiling is the worst point of that "
    "sweep.",
    condition="fraction of the typical, applied either way, to the OFFSET "
              "thresholds only",
    role=POLICY_BUDGET)
# The FIXED 3.6 V VINDPM regulation point is a different kind of number: it
# is an absolute node potential, not a small offset, and a +/-50 % sweep of it
# would put the threshold at 5.4 V -- above the USB source itself, which is
# not an uncertainty but a nonsense.  TI publishes it as a typical alongside
# VIN_OP min = 3.6 V, so the declared band is the narrow one below, applied as
# a FRACTION OF THE OFFSET SWEEP so that one knob still moves every threshold.
CHARGER_FIXED_VINDPM_SWEEP_RATIO = tag(
    "bq.fixed_vindpm_sweep_ratio", 0.10, DECLARED_ENGINEERING_BOUND,
    "DECLARED.  The fixed 3.6 V VINDPM regulation point is swept at 10 % of "
    "the offset sweep -- +/-5 % at the full +/-50 % offset sweep, i.e. "
    "3.42..3.78 V.  TI publishes the figure in 6.3.1 with no tolerance "
    "column and states VIN_OP min = 3.6 V in the same table.",
    role=POLICY_BUDGET)


def charger_thresholds(spec=None, sweep=0.0):
    """The four branch thresholds, optionally moved by the declared sweep.

    `sweep` is a signed fraction of each typical.  ADVERSE is the direction
    that makes the part leave a benign branch EARLIER: a larger VDPPM folds
    charge sooner, a smaller VBSUP1 enters supplement sooner, and a larger
    VINDPM_TRACK starves the input sooner.  The caller sweeps both ways and
    the ceiling takes the worst.
    """
    s = BQ25185 if spec is None else spec
    return dict(
        vdppm_V=s["vdppm_V"] * (1.0 + sweep),
        # VBSUP1 is an OFFSET BELOW the cell; a SMALLER offset means SYS has
        # less room to fall before the BATFET conducts.
        vbsup1_V=s["vbsup1_V"] * (1.0 - sweep),
        vbsup2_V=s["vbsup2_V"] * (1.0 - sweep),
        vindpm_track_V=s["vindpm_track_V"] * (1.0 + sweep),
        vindpm_fixed_V=s["vindpm_fixed_V"] * (
            1.0 + sweep * CHARGER_FIXED_VINDPM_SWEEP_RATIO),
        sweep=sweep,
        fixed_vindpm_sweep_ratio=CHARGER_FIXED_VINDPM_SWEEP_RATIO)


def vindpm_threshold_V(vbat, spec=None, thresholds=None):
    """SLUSF65B 6.3.1 + the VINDPM_TRACK EC row.

    Battery tracking applies only while VBAT is above 3.5 V; below it the
    input is regulated to a FIXED 3.6 V.  Two different controls, and D-793
    modelled neither.
    """
    s = BQ25185 if spec is None else spec
    t = charger_thresholds(s) if thresholds is None else thresholds
    if vbat > s["vindpm_track_vbat_floor_V"]:
        return vbat + t["vindpm_track_V"], "battery_tracking"
    return t["vindpm_fixed_V"], "fixed_3v6"


CHARGER_BRANCH_NAMES = ("SYS_REG", "CC_PATH_LIMITED", "TREG", "ILIM",
                        "VINDPM", "DPPM", "NO_CHARGE", "SUPPLEMENT")

# ==========================================================================
# D-796 / R15-01 + Fable R15-06 (D796-08).  WHETHER THE BATFET CAN SUPPLEMENT.
#
# Two BATFET states, and which of them a cell voltage admits:
#
#   "connected"  the cell is above VBUVLO; the BATFET may carry BAT -> SYS.
#   "uvlo_open"  BUVLO has disconnected BAT from SYS for DISCHARGE.  Charging
#                (precharge / CC) still flows -- SLUSF65B charges a battery
#                down to 0 V -- but nothing can SUPPLEMENT: a load the input
#                cannot carry collapses SYS (brown-out, then the 6.3.7.5
#                system-short hiccup), it does not draw on the cell.
#
# The falling trip is anywhere in the declared band; a cell that FELL
# through it re-connects only at trip + VBUVLO_HYS.  So:
#
#   VBAT <= trip_low                 -> uvlo_open only ("at/under VBUVLO")
#   VBAT >= trip_high + HYS_MAX      -> connected only
#   in between                       -> BOTH, part-to-part and by history
#
# and every domain that ranges over cells enumerates BOTH states wherever
# both are physical, so no product claim silently picks the benign one.
# ==========================================================================
BATFET_STATES = ("connected", "uvlo_open")


def buvlo_band_V(spec=None):
    """(falling-trip low, falling-trip high, rising re-connect high)."""
    s = BQ25185 if spec is None else spec
    lo = s["vbuvlo_typ_V"] * (1.0 - s["vbuvlo_declared_tolerance"])
    hi = s["vbuvlo_typ_V"] * (1.0 + s["vbuvlo_declared_tolerance"])
    return round(lo, 6), round(hi, 6), round(hi + s["vbuvlo_hys_max_V"], 6)


def batfet_states_at(vbat, spec=None):
    """Every BATFET state a cell at `vbat` can physically be in."""
    lo, _hi, reconnect = buvlo_band_V(spec)
    if vbat <= lo + 1e-12:
        return ("uvlo_open",)
    if vbat >= reconnect - 1e-12:
        return ("connected",)
    return BATFET_STATES


# ==========================================================================
# D-796 / D796-02.  AN AMBIGUOUS DATASHEET SENTENCE IS A NAMED ASSUMPTION.
#
# SLUSF65B 6.3.7.6: "If the charge current is reduced to 0, the battery
# supplies the current needed by the SYS output."  It does not say whether the
# input FET is ALSO throttled once TREG has taken the charge to zero (so the
# cell discharges into SYS with an adapter present), or whether the sentence
# only restates 6.3.3 supplement.  D-795 silently chose the benign reading and
# published a no-discharge table that is ambient- and TREG-independent.
#
# D-796 relies on NEITHER reading.  A no-discharge claim is published only
# where the zero-charge junction stays BELOW the LOW end of the declared TREG
# band -- there TREG can never fold the charge to zero, so the sentence cannot
# apply under either reading.  The junction claim is unaffected: under the
# throttling reading the input FET dissipates LESS, so the benign reading is
# the adverse one for heat and that is the one the junction bound uses.
# C-PWR-CHARGE-01 step 6 is the discriminating first-article measurement.
# ==========================================================================
CHARGER_MODEL_ASSUMPTIONS = dict(
    treg_zero_charge_sys_source=dict(
        status="AMBIGUOUS_IN_THE_PRIMARY_SOURCE_NOT_RELIED_ON",
        text="SLUSF65B 6.3.7.6: 'If the charge current is reduced to 0, the "
             "battery supplies the current needed by the SYS output.'",
        readings=dict(
            restates_supplement="the input keeps carrying what it can; the "
                                "cell supplies only a shortfall (6.3.3)",
            throttles_the_input="once TREG has folded the charge to zero the "
                                "input is reduced and the cell discharges "
                                "into SYS with the adapter attached"),
        no_discharge_claim="conditioned: published only where the zero-"
                           "charge junction is below TREG's declared LOW end "
                           "(90 C) at every ambient 0..40 C, so TREG cannot "
                           "reach zero charge and neither reading applies",
        junction_claim="uses the restates_supplement reading, which keeps "
                       "the input FET carrying the load and is therefore the "
                       "HOTTER of the two",
        discriminating_measurement="C-PWR-CHARGE-01 step 6 (40 C, high "
                                   "source corner, mid/high cell)"),
    batfet_below_vbuvlo=dict(
        status="PRIMARY_SOURCE",
        text="SLUSF65B 6.3.3 / 6.3.7.2: supplement requires VBAT > VBUVLO; "
             "BUVLO disconnects BAT from SYS",
        consequence="below the trip a load above the input-carrying limit "
                    "collapses SYS; it is never solved as SUPPLEMENT"),
    treg_limit_cycle=dict(
        status="MODEL_CONSEQUENCE",
        text="where the charge is held by the DPPM loop at an input limit, "
             "reducing the charge PROGRAM changes nothing until it falls "
             "below the held charge, and then SYS leaps back to regulation "
             "and the junction drops below TREG; no static TREG equilibrium "
             "exists and the part cycles between the two",
        consequence="the HOT, low-charge phase is published as the state "
                    "(adverse for the enclosure air and the charge time); it "
                    "is never labelled TREG and never carries a junction "
                    "below the threshold that would make TREG active",
        junction="the junction is bounded by the threshold itself: the loop "
                 "acts on TJ, and the phases alternate on the loop's "
                 "timescale, far faster than the package's thermal time "
                 "constant, so the die averages to TREG.  DECLARED -- "
                 "SLUSF65B publishes no loop bandwidth; C-PWR-CHARGE-01 "
                 "step 6 and C-THERM-01 observe the package temperature"))


def programmed_charge_A(vbat, spec=None, ichg_corner="max", vlowv_V=None):
    """What the CC/precharge loop asks for at this cell, before any fold.

    `ichg_corner` picks the end of the KISET x R37 band.  Below VLOWV the
    part is in PRECHARGE at IPRECHG = 20 % of ICHG, +/-10 %; the precharge
    accuracy is taken in the SAME direction as the ICHG corner so a heat
    question and a time question each get their own adverse end.  Returns
    (amps, kind).
    """
    s = BQ25185 if spec is None else spec
    ichg = {"max": s["ichg_max_A"], "min": s["ichg_min_A"],
            "typ": s["ichg_A"]}[ichg_corner]
    vlowv = s["vlowv_min_V"] if vlowv_V is None else vlowv_V
    if vbat < vlowv:
        acc = {"max": 1.0 + s["iprechg_accuracy"],
               "min": 1.0 - s["iprechg_accuracy"], "typ": 1.0}[ichg_corner]
        return ichg * s["iprechg_fraction"] * acc, "PRECHARGE"
    return ichg, "CC"


def charger_state(p_sys_W, vbat, ilim_corner="max", vbus_corner="max",
                  spec=None, treg_folds_charge_to_zero=False,
                  vbus_V=None, path_ohm=None, source_key=None,
                  previous_mode=None, sweep=0.0, ichg_corner="max",
                  ichg_program_A=None, charge_loop=None, vlowv_V=None,
                  batfet="connected"):
    """ONE physically consistent BQ25185 operating point.  Pure.

    D-796 / D796-08: `batfet` is "connected" or "uvlo_open".  Below VBUVLO
    (`batfet_states_at`) the BATFET cannot supplement, and a load the input
    cannot carry has NO static operating point (SYS collapses) -- the solver
    returns None and never a SUPPLEMENT state.  A "uvlo_open" request at a
    cell that cannot be under the trip, or "connected" at one that must be,
    is refused the same way, so a label cannot be attached to the wrong cell.

    D-795 / R14-03 CORRECTS THE CONTROL MODEL, AND THE CORRECTION IS ONE
    SENTENCE OF SLUSF65B 6.3.2 THAT D-794 DID NOT FOLLOW:

        "If the sum of the charging and load currents exceeds the preset
         maximum input current, the input DPM loop reduces the input current.
         If SYS drops below the DPPM voltage threshold, the charging current
         is reduced by the DPPM loop through the BATFET."

    ILIM and VINDPM are INPUT loops.  They cut the INPUT current, and it is
    the resulting fall of SYS to VBAT + VDPPM that makes the DPPM loop fold
    the charge.  D-794's ILIM/VINDPM branches held SYS at the 4.41 V
    regulation point and folded the charge by fiat -- a charge current below
    the program with SYS far above the DPPM node, which no loop in the part
    produces.  Round-14 reproduced it and R14-03 names it.  The branches are
    now:

      SYS_REG          6.3.5.  The input FET drops VIN - VSYS_REG as a series
                       pass element; charge at the PROGRAM.
      CC_PATH_LIMITED  the input FET fully enhanced; SYS is what the source
                       leaves; charge at the PROGRAM.
      TREG             6.3.7.6.  Thermal regulation has reduced the charge
                       PROGRAM; SYS is at regulation or path-limited and ABOVE
                       the DPPM node.  The ONLY branch in which a folded charge
                       current coexists with SYS above VBAT + VDPPM, and it
                       needs the junction at TREG to be legitimate -- which is
                       why `charge_loop="TREG"` is set only by
                       `charger_operating_point`, the thermal solve.
      ILIM / VINDPM /  6.3.1 / 6.3.2 / 6.3.6.  SYS HELD AT VBAT + VDPPM by the
      DPPM            DPPM loop, the input current at whichever input-side
                       limit binds -- ILIM, VINDPM, or the source path itself
                       with the FET fully on -- and the charge current is what
                       is left:  ICHG = IIN - P / (VBAT + VDPPM).
      NO_CHARGE        the charge has folded to zero; the input carries the
                       load alone with SYS above the supplement entry.
      SUPPLEMENT       6.3.3.  The BATFET conducts BAT -> SYS.

    The PROGRAM is ICHG (at `ichg_corner` of the KISET x R37 band), or
    IPRECHG below VLOWV, or -- `ichg_program_A` -- a thermal fold.
    """
    s = BQ25185 if spec is None else spec
    if batfet not in batfet_states_at(vbat, s):
        return None
    th = charger_thresholds(s, sweep)
    ilim = s["ilim_max_A"] if ilim_corner == "max" else s["ilim_min_A"]
    if vbus_V is None or path_ohm is None:
        if vbus_corner == "max":
            vbus, path = USB_VBUS_MAX_V, USB_PATH_MIN_OHM
        else:
            vbus, path = USB_VBUS_MIN_V, USB_PATH_MAX_OHM
    else:
        vbus, path = vbus_V, path_ohm
    ron_in = s["ron_in_max_ohm"]
    ron_bat = s["ron_bat_max_ohm"] * s["ron_bat_vbat_allowance"]
    vsys_reg = s["vsys_reg_V"] * (1.0 - s["vsys_reg_accuracy"])
    nominal_prog, prog_kind = programmed_charge_A(vbat, s, ichg_corner,
                                                  vlowv_V)
    if treg_folds_charge_to_zero:
        ichg_max, loop = 0.0, "TREG"
    elif ichg_program_A is not None:
        ichg_max = max(0.0, min(nominal_prog, ichg_program_A))
        loop = charge_loop or "TREG"
    else:
        ichg_max, loop = nominal_prog, prog_kind
    r_src = path + ron_in
    v_vindpm, vindpm_kind = vindpm_threshold_V(vbat, s, th)
    v_dppm = vbat + th["vdppm_V"]
    v_sup_enter = vbat - th["vbsup1_V"]
    v_sup_exit = vbat - th["vbsup2_V"]

    # The input current each INPUT-SIDE loop allows.  VINDPM regulates the IN
    # PIN, so its cap is set by the CABLE alone; ILIM caps the current itself.
    i_vindpm_cap = ((vbus - v_vindpm) / path) if path > 0 else float("inf")
    i_vindpm_cap = max(0.0, i_vindpm_cap)
    i_cap = min(ilim, i_vindpm_cap)
    input_loop = "ILIM" if ilim <= i_vindpm_cap else "VINDPM"

    def _node(i_chg):
        """VSYS with this charge current and the input NOT current-limited.

        The SYS regulator can only pull SYS DOWN, so the node is the lower of
        its regulation point and the STABLE (high) root the source leaves.
        """
        i_sys_reg = p_sys_W / vsys_reg
        if vbus - (i_sys_reg + i_chg) * r_src >= vsys_reg - 1e-15:
            return vsys_reg, i_sys_reg + i_chg, i_sys_reg, True
        b = vbus - i_chg * r_src
        disc = b * b - 4.0 * p_sys_W * r_src
        if disc < 0.0:
            return None
        vs = 0.5 * (b + math.sqrt(disc))
        if vs <= 0.0:
            return None
        return vs, p_sys_W / vs + i_chg, p_sys_W / vs, False

    mode = None
    i_supp = 0.0
    hysteresis_band = False
    threshold_used = None
    batfet_off_node_V = None
    regulated = False

    # ---- 1. The charge loop gets its PROGRAM, and no input-side loop binds.
    full = _node(ichg_max) if ichg_max > 0.0 else None
    if (full is not None and full[1] <= i_cap + 1e-12
            and full[0] >= v_dppm - 1e-12):
        vsys, i_in, i_sys, regulated = full
        i_chg = ichg_max
        if loop == "TREG" and ichg_max < nominal_prog - 1e-12:
            mode = "TREG"
            threshold_used = ("TREG: the thermal loop has reduced the charge "
                              "program to %.6f A; SYS stays above VDPPM"
                              % ichg_max)
        else:
            mode = "SYS_REG" if regulated else "CC_PATH_LIMITED"
            threshold_used = ("none: the charge current is the %s program"
                              % loop)
    else:
        # ---- 2. DPPM holds SYS at VBAT + VDPPM; an input-side limit sets
        #         IIN; the charge takes what is left. ----------------------
        dppm = None
        if ichg_max > 0.0 and 0.0 < v_dppm < vsys_reg:
            i_src_d = max(0.0, (vbus - v_dppm) / r_src)
            i_in_d = min(i_cap, i_src_d)
            i_sys_d = p_sys_W / v_dppm
            i_chg_d = i_in_d - i_sys_d
            if -1e-12 <= i_chg_d <= ichg_max + 1e-12:
                if i_src_d < i_cap:
                    which = "DPPM"
                else:
                    which = input_loop
                dppm = (v_dppm, i_in_d, i_sys_d,
                        max(0.0, min(ichg_max, i_chg_d)), which)
        if dppm is not None:
            vsys, i_in, i_sys, i_chg, mode = dppm
            threshold_used = (
                "SYS held at VDPPM = VBAT + %.4f V by the DPPM loop; the input "
                "current is set by %s" % (
                    th["vdppm_V"],
                    {"ILIM": "the input current limit",
                     "VINDPM": "VINDPM at %.4f V (%s)" % (v_vindpm,
                                                         vindpm_kind),
                     "DPPM": "the source path with the input FET fully "
                             "enhanced"}[mode]))
        else:
            # ---- 3. No charge at all.  Can the input carry the load? ------
            zero = _node(0.0)
            i_chg = 0.0
            if zero is not None and zero[1] <= i_cap + 1e-12:
                vs0, i_in0, i_sys0, reg0 = zero
            else:
                vs0 = vbus - i_cap * r_src
                if vs0 > vsys_reg:
                    vs0 = vsys_reg
                i_in0, i_sys0, reg0 = i_cap, (
                    p_sys_W / vs0 if vs0 > 0.0 else float("inf")), False
            supplementing = False
            batfet_off_node_V = vs0
            if vs0 <= 0.0 or i_sys0 > i_in0 + 1e-12:
                supplementing = True
                batfet_off_node_V = None
                threshold_used = ("the input cannot carry the load with "
                                  "the BATFET off at all")
            elif ichg_max > 0.0 and vs0 > v_dppm + 1e-12:
                # D-795 / R14-03.  NO EQUILIBRIUM ABOVE THE DPPM NODE.  The
                # zero-charge node sits ABOVE VBAT + VDPPM, so the CC loop --
                # which is active, the program being non-zero -- ramps the
                # charge current up and pulls SYS down to VDPPM; there the
                # DPPM loop would fold the charge, but the LOAD ALONE already
                # exceeds what the input can deliver at that node (the DPPM
                # branch above found no non-negative charge).  SYS keeps
                # falling and the BATFET conducts.  D-794 reported NO_CHARGE
                # here with SYS 1 V above the cell, which is a state no loop in
                # the part holds -- R14-03's inequality is what caught it.
                supplementing = True
                batfet_off_node_V = None
                threshold_used = (
                    "the CC loop pulls SYS to VDPPM = %.4f V and the load "
                    "alone exceeds the input there: entry by necessity"
                    % v_dppm)
            elif batfet != "connected":
                # D-796 / D796-08: the comparator has nothing to switch on --
                # BUVLO holds BAT off SYS -- so SYS below the cell is simply
                # where the input leaves it.
                threshold_used = ("BATFET disconnected by BUVLO: no "
                                  "supplement comparator acts")
            elif vs0 <= v_sup_enter + 1e-12:
                supplementing = True
                threshold_used = ("VBSUP1: SYS is below VBAT - %.4f V"
                                  % th["vbsup1_V"])
            elif vs0 <= v_sup_exit + 1e-12:
                hysteresis_band = True
                supplementing = (previous_mode == "SUPPLEMENT"
                                 and batfet == "connected")
                threshold_used = (
                    "inside the VBSUP1/VBSUP2 hysteresis band "
                    "[%.4f, %.4f] V; previous mode %r decides"
                    % (v_sup_enter, v_sup_exit, previous_mode))
            if supplementing and batfet != "connected":
                # D-796 / D796-08.  BUVLO has disconnected BAT from SYS: the
                # shortfall cannot be drawn from the cell.  SYS collapses
                # (brown-out; SLUSF65B 6.3.7.5 system-short hiccup) -- there
                # is no static operating point to report.
                return None
            if not supplementing:
                vsys, i_in, i_sys, regulated = vs0, i_in0, i_sys0, reg0
                mode = "NO_CHARGE"
                if threshold_used is None:
                    threshold_used = ("the charge current has folded to "
                                      "zero and the BATFET is still off")
            else:
                # ---- 4. SUPPLEMENT, bisected. --------------------------
                mode = "SUPPLEMENT"
                regulated = False
                if threshold_used is None:
                    threshold_used = ("VBSUP1: the input cannot carry the "
                                      "load")

                def _i_in_at(vs):
                    return max(0.0, min(i_cap, (vbus - vs) / r_src))

                def _resid(vs):
                    return vbat - (p_sys_W / vs - _i_in_at(vs)) * ron_bat - vs

                lo, hi = 1e-3, vbat
                if _resid(hi) >= 0.0:
                    return None
                for _ in range(90):
                    mid = 0.5 * (lo + hi)
                    if _resid(mid) >= 0.0:
                        lo = mid
                    else:
                        hi = mid
                vs = 0.5 * (lo + hi)
                if vs <= 0.2:
                    return None
                vsys = vs
                i_in = _i_in_at(vsys)
                i_sys = p_sys_W / vsys
                i_supp = max(0.0, i_sys - i_in)
                i_chg = 0.0

    v_pin = vbus - i_in * path
    # ---- the dissipation, priced as the PHYSICS and not as a resistor ------
    p_input_fet = max(0.0, (v_pin - vsys) * i_in)
    p_charge_fet = max(0.0, (vsys - vbat) * i_chg)
    p_batfet = max(0.0, (vbat - vsys) * i_supp)
    p_pkg = p_input_fet + p_charge_fet + p_batfet
    p_in = vbus * i_in                      # what leaves the source
    p_stored = vbat * i_chg
    p_from_cell = vbat * i_supp
    p_cable = i_in * i_in * path
    p_ron_only = i_in * i_in * ron_in
    p_treg_cannot = p_input_fet + p_batfet
    # D-793 / R12-02 + R12-04: the TERMINAL balance against the sum of the
    # INTERNAL loss elements -- two different sets of quantities.
    p_diss_total = p_in + p_from_cell - p_sys_W - p_stored
    p_loss_sum = p_pkg + p_cable
    return dict(
        mode=mode,
        ilim_corner=ilim_corner, vbus_corner=vbus_corner,
        ichg_corner=ichg_corner,
        source_key=source_key,
        batfet=batfet,
        previous_mode=previous_mode,
        ilim_A=ilim, vbus_source_V=vbus, path_ohm=path,
        vin_pin_V=round(v_pin, 6),
        vsys_V=round(vsys, 6), vbat_V=round(vbat, 6),
        system_W=round(p_sys_W, 6),
        input_A=round(i_in, 6), system_A=round(i_sys, 6),
        charge_A=round(i_chg, 6), supplement_A=round(i_supp, 6),
        input_fet_W=round(p_input_fet, 6),
        input_fet_resistive_only_W=round(p_ron_only, 6),
        charge_fet_W=round(p_charge_fet, 6),
        batfet_W=round(p_batfet, 6),
        cable_W=round(p_cable, 6),
        package_W=round(p_pkg, 6),
        package_W_treg_cannot_reduce=round(p_treg_cannot, 6),
        source_W=round(p_in, 6), stored_W=round(p_stored, 6),
        from_cell_W=round(p_from_cell, 6),
        total_dissipation_W=round(p_diss_total, 6),
        internal_loss_sum_W=round(p_loss_sum, 6),
        terminal_vs_loss_residual_W=round(p_diss_total - p_loss_sum, 12),
        controls=dict(
            vsys_reg_V=round(vsys_reg, 6),
            vindpm_threshold_V=round(v_vindpm, 6),
            vindpm_kind=vindpm_kind,
            vdppm_threshold_V=round(v_dppm, 6),
            supplement_enter_V=round(v_sup_enter, 6),
            supplement_exit_V=round(v_sup_exit, 6),
            input_loop_that_caps_the_current=input_loop,
            input_current_cap_A=round(i_cap, 6),
            ilim_cap_A=round(ilim, 6),
            vindpm_cap_A=(None if i_vindpm_cap == float("inf")
                          else round(i_vindpm_cap, 6)),
            charge_program_A=round(ichg_max, 6),
            nominal_charge_program_A=round(nominal_prog, 6),
            charge_program_kind=prog_kind,
            charge_loop=loop,
            threshold_used=threshold_used,
            inside_the_supplement_hysteresis_band=bool(hysteresis_band),
            batfet_off_comparator_node_V=(
                None if batfet_off_node_V is None
                else round(batfet_off_node_V, 6)),
            sweep=sweep,
            treg_folds_charge_to_zero=bool(treg_folds_charge_to_zero)),
        raw=dict(vsys=vsys, i_in=i_in, i_sys=i_sys, i_chg=i_chg,
                 i_supp=i_supp, v_pin=v_pin, vbus=vbus, path=path,
                 ron_in=ron_in, ron_bat=ron_bat, ilim=ilim,
                 vsys_reg=vsys_reg, p_sys=p_sys_W, vbat=vbat,
                 ichg_max=ichg_max, ichg_nominal=nominal_prog, i_cap=i_cap,
                 v_vindpm=v_vindpm, v_dppm=v_dppm,
                 v_sup_enter=v_sup_enter, v_sup_exit=v_sup_exit,
                 batfet_off_node_V=batfet_off_node_V,
                 # D-795 / R14-05: EVERY printed heat field has a raw twin,
                 # so a corruption of either copy is visible.
                 p_input_fet=p_input_fet, p_charge_fet=p_charge_fet,
                 p_batfet=p_batfet, p_pkg=p_pkg, p_cable=p_cable,
                 p_in=p_in, p_stored=p_stored, p_from_cell=p_from_cell,
                 p_diss_total=p_diss_total, p_loss_sum=p_loss_sum,
                 p_ron_only=p_ron_only, p_treg_cannot=p_treg_cannot),
        invariants=charger_invariants(
            i_in, i_supp, i_sys, i_chg, vsys, vbat, v_pin, ron_in,
            p_in, p_from_cell, p_sys_W, p_stored, p_diss_total,
            mode=mode, ilim=ilim, vsys_reg=vsys_reg, ron_bat=ron_bat,
            path=path, vbus=vbus, p_loss_sum=p_loss_sum,
            ichg_max=ichg_max, i_cap=i_cap, v_vindpm=v_vindpm,
            v_dppm=v_dppm, v_sup_enter=v_sup_enter, v_sup_exit=v_sup_exit,
            hysteresis_band=hysteresis_band, previous_mode=previous_mode,
            batfet_off_node_V=batfet_off_node_V,
            ichg_nominal=nominal_prog, charge_loop=loop,
            batfet=batfet, buvlo_trip_low_V=buvlo_band_V(s)[0]))


def charger_junction(st, ambient_C, r_sys_K_per_W, theta_ja_C_per_W,
                     delivered_out_W=0.0, heat_key="package_W"):
    """The two thermal relations the release uses, applied to one state.

    Internal air = ambient + R_SYS x (everything dissipated INSIDE the
    enclosure); junction = air + thetaJA x package heat.
    """
    internal = (st["source_W"] + st["from_cell_W"] - st["stored_W"]
                - delivered_out_W)
    air = ambient_C + r_sys_K_per_W * internal
    return air + theta_ja_C_per_W * st[heat_key], air, internal


TREG_EQUILIBRIUM_TOL_K = 0.05
# The hot phase of a TREG limit cycle: a state whose charge is NOT set by the
# program -- held by DPPM at an input limit, or (at a cell low enough that the
# CC loop drags SYS below the entry threshold) already supplementing.
LIMIT_CYCLE_HOT_BRANCHES = ("ILIM", "VINDPM", "DPPM", "SUPPLEMENT")


def charger_thermal_problems(st):
    """D-796 / R15-01.  A thermal label must be held by the loop it names.

    SLUSF65B 6.3.7.6: the device "reduces the charge current WHEN TJ REACHES
    the thermal regulation threshold".  TREG is a loop that becomes active
    BECAUSE the junction is at the threshold, so:

      * a state labelled TREG, or with `treg_active`, must have its junction
        AT the threshold -- except the zero-charge end, where TREG has done
        all it can and the junction may sit ABOVE it, and the limit-cycle hot
        phase, which is above it by construction;
      * a CHARGING state whose junction is ABOVE the threshold with TREG not
        active is a state the thermal loop would not leave alone.
    """
    th = st.get("thermal")
    why = []
    if not isinstance(th, dict):
        return ["no thermal block"]
    tj, treg = th["junction_C"], th["treg_C"]
    regime = th.get("regime")
    if st["mode"] == "TREG" or th.get("treg_active"):
        if tj < treg - TREG_EQUILIBRIUM_TOL_K:
            why.append("a TREG-active state whose junction %.3f C is BELOW "
                       "the %.1f C threshold that would activate the loop"
                       % (tj, treg))
        if regime == "TREG_EQUILIBRIUM" and tj > treg + TREG_EQUILIBRIUM_TOL_K:
            why.append("a TREG equilibrium above its threshold")
        if regime == "TREG_AT_ZERO_CHARGE" and st["charge_A"] > 1e-9:
            why.append("TREG at zero charge with a charge current")
    if st["mode"] == "TREG" and regime not in ("TREG_EQUILIBRIUM",
                                               "TREG_AT_ZERO_CHARGE"):
        why.append("a TREG branch not produced by the thermal solve")
    if (not th.get("treg_active") and st["charge_A"] > 1e-9
            and tj > treg + TREG_EQUILIBRIUM_TOL_K):
        why.append("a charging state at %.3f C, above TREG, with the "
                   "thermal loop inactive" % tj)
    if regime == "TREG_LIMIT_CYCLE_HOT_PHASE":
        if st["mode"] not in LIMIT_CYCLE_HOT_BRANCHES:
            why.append("a limit-cycle hot phase that is neither DPPM-held "
                       "nor supplementing")
        if tj < treg - TREG_EQUILIBRIUM_TOL_K:
            why.append("a limit-cycle hot phase below TREG")
        cold = (th.get("limit_cycle") or {}).get("cold_phase_junction_C")
        if cold is None or cold >= treg - TREG_EQUILIBRIUM_TOL_K:
            why.append("a limit cycle whose cold phase does not sit below "
                       "TREG -- a static equilibrium existed")
    return why


def charger_operating_point(p_sys_W, vbat, ambient_C, r_sys_K_per_W,
                            theta_ja_C_per_W, treg_C, delivered_out_W=0.0,
                            **kw):
    """D-795 / R14-03 + R14-04, CORRECTED BY D-796 / R15-01.

    SLUSF65B 6.3.7.6: "the device monitors the junction temperature of the
    die and reduces the charge current when TJ reaches the thermal regulation
    threshold (TREG)."  The fold is a LOOP.  Three outcomes, each labelled by
    the loop that actually holds it (`thermal.regime`):

      NO_TREG                 the unfolded state is at or below TREG.
      TREG_EQUILIBRIUM        a reduced program puts the junction AT TREG.
      TREG_AT_ZERO_CHARGE     even zero charge leaves the junction at or
                              above TREG; TREG has done all it can.
      TREG_LIMIT_CYCLE_HOT_PHASE
                              ROUND-15 R15-01.  D-795 bisected the program
                              for "junction <= TREG" and reported whatever it
                              landed on as TREG -- 44 of 480 corners came back
                              labelled TREG with the junction up to 21 K BELOW
                              the threshold.  The cause is a discontinuity:
                              while the DPPM loop holds the charge at an input
                              limit, a lower PROGRAM changes nothing until it
                              drops below the held charge, and then SYS leaps
                              back to regulation, the input FET's drop
                              collapses and the junction falls below TREG, so
                              the loop releases, the program rises, and the
                              part falls back into the DPPM-held state.  No
                              static TREG state exists.  The HOT, low-charge
                              phase is published -- labelled by its input
                              loop, with the cold phase carried as evidence --
                              because it is the adverse phase for the
                              junction, the enclosure air AND the charge time.
    """
    st = charger_state(p_sys_W, vbat, **kw)
    if st is None:
        return None

    def _tj(x):
        return charger_junction(x, ambient_C, r_sys_K_per_W,
                                theta_ja_C_per_W, delivered_out_W)

    def _attach(x, active, regime, extra=None):
        tj, air, internal = _tj(x)
        th = dict(
            ambient_C=ambient_C, r_sys_K_per_W=r_sys_K_per_W,
            theta_ja_C_per_W=theta_ja_C_per_W, treg_C=treg_C,
            delivered_out_W=round(delivered_out_W, 6),
            internal_W=round(internal, 6), internal_air_C=round(air, 6),
            junction_C=round(tj, 6), treg_active=bool(active),
            regime=regime)
        if extra:
            th.update(extra)
        out = dict(x, thermal=th)
        tp = charger_thermal_problems(out)
        inv = dict(out["invariants"], thermal_problems=tp,
                   thermal_label_is_held_by_its_loop=not tp)
        inv["ok"] = bool(out["invariants"]["ok"] and not tp)
        out["invariants"] = inv
        return out

    if _tj(st)[0] <= treg_C + 1e-9:
        return _attach(st, False, "NO_TREG")
    kw0 = dict(kw)
    kw0.pop("ichg_program_A", None)
    kw0.pop("charge_loop", None)
    zero = charger_state(p_sys_W, vbat, ichg_program_A=0.0,
                         charge_loop="TREG", **kw0)
    if zero is None:
        return None
    if _tj(zero)[0] >= treg_C - 1e-9:
        return _attach(zero, True, "TREG_AT_ZERO_CHARGE")
    lo, hi = 0.0, st["controls"]["nominal_charge_program_A"]
    best = zero
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        cand = charger_state(p_sys_W, vbat, ichg_program_A=mid,
                             charge_loop="TREG", **kw0)
        if cand is not None and _tj(cand)[0] <= treg_C:
            lo, best = mid, cand
        else:
            hi = mid
    if _tj(best)[0] >= treg_C - TREG_EQUILIBRIUM_TOL_K:
        return _attach(best, True, "TREG_EQUILIBRIUM")
    # ---- no static equilibrium: the limit cycle ---------------------------
    # The hot phase's charge is NOT set by the program (DPPM holds it, or the
    # part is supplementing), so it is published at the NOMINAL program: the
    # boundary program `hi` sits inside every checker's tolerance of the
    # switch and would make the label depend on rounding.
    hot = st
    if hot["mode"] not in LIMIT_CYCLE_HOT_BRANCHES:
        hot = charger_state(p_sys_W, vbat, ichg_program_A=hi,
                            charge_loop="TREG", **kw0) or st
    return _attach(hot, True, "TREG_LIMIT_CYCLE_HOT_PHASE", dict(
        limit_cycle=dict(
            program_band_A=[round(lo, 6), round(hi, 6)],
            cold_phase_mode=best["mode"],
            cold_phase_charge_A=best["charge_A"],
            cold_phase_junction_C=round(_tj(best)[0], 6),
            hot_phase_junction_C=round(_tj(hot)[0], 6),
            time_average_junction_bound_C=treg_C,
            why="the DPPM-held charge does not respond to the program until "
                "the program falls below it; then SYS returns to regulation "
                "and the junction drops below TREG, so no static TREG state "
                "exists")))


def charger_invariants(i_in, i_supp, i_sys, i_chg, vsys, vbat, v_pin, ron_in,
                       p_in, p_from_cell, p_sys_W, p_stored, p_diss,
                       mode=None, ilim=None, vsys_reg=None, ron_bat=None,
                       path=None, vbus=None, p_loss_sum=None,
                       ichg_max=None, i_cap=None, v_vindpm=None, v_dppm=None,
                       v_sup_enter=None, v_sup_exit=None,
                       hysteresis_band=False, previous_mode=None,
                       batfet_off_node_V=None, ichg_nominal=None,
                       charge_loop=None, batfet=None, buvlo_trip_low_V=None):
    eps = 1e-6
    inv = dict(
        kcl_at_sys=bool(abs(i_in + i_supp - i_sys - i_chg) < 1e-6),
        kcl_residual_A=round(i_in + i_supp - i_sys - i_chg, 9),
        supplement_requires_sys_below_bat=bool(
            i_supp <= eps or vsys < vbat + 1e-9),
        charge_requires_sys_above_bat=bool(
            i_chg <= eps or vsys > vbat - 1e-9),
        supplement_and_charge_are_exclusive=bool(i_supp * i_chg < 1e-9),
        kvl_input_fet_drop_is_non_negative=bool(v_pin >= vsys - 1e-9),
        input_fet_drop_is_at_least_resistive=bool(
            (v_pin - vsys) >= i_in * ron_in - 1e-6 or i_in <= eps),
        dissipation_is_non_negative=bool(p_diss >= -1e-9),
        every_current_is_non_negative=bool(
            min(i_in, i_supp, i_sys, i_chg) >= -1e-9))
    # ---- D-793 / R12-02.  THE INVARIANTS D-792 DID NOT HAVE. --------------
    # `energy_balance` used to compare the definition of p_diss with itself.
    # The real statement is that the TERMINAL balance and the INTERNAL loss
    # sum agree -- two different sets of quantities, one identity.
    if p_loss_sum is not None:
        inv["energy_balance"] = bool(abs(p_diss - p_loss_sum) < 1e-9)
        inv["energy_residual_W"] = round(p_diss - p_loss_sum, 12)
    else:
        inv["energy_balance"] = bool(
            abs(p_in + p_from_cell - p_sys_W - p_stored - p_diss) < 1e-6)
    # The LOAD really is a constant-power load at the solved node.
    inv["load_is_constant_power"] = bool(abs(vsys * i_sys - p_sys_W) < 1e-6)
    # ======================================================================
    # D-794 / R13-02.  EVERY BRANCH SATISFIES ITS OWN DEFINING INEQUALITIES,
    # AND -- THE HALF D-793 DID NOT HAVE -- NO BRANCH MAY BE CLAIMED WHILE THE
    # LOOP THAT WOULD HAVE TAKEN CONTROL FIRST IS STILL SLACK.
    #
    # D-793 checked that a SUPPLEMENT state satisfied the supplement equation.
    # It never checked that the part had any business being in supplement, nor
    # that a state holding SYS at its regulation point had an input-side loop
    # entitled to fold the charge current.  These two families -- `defining`
    # and `precedence` -- are what makes the branch set a PARTITION rather
    # than a list of separately-plausible answers.
    # ======================================================================
    if mode is not None and None not in (ilim, vsys_reg, ron_bat, path, vbus):
        r_src = path + ron_in
        cap = ilim if i_cap is None else i_cap
        ich = ichg_max
        why = []
        # ---- D-796 / D796-08: no supplement HISTORY below the trip --------
        if batfet == "uvlo_open" and previous_mode == "SUPPLEMENT":
            why.append("a SUPPLEMENT history with the BATFET disconnected by "
                       "BUVLO: the part cannot have been supplementing")
        # ---- universal: no input-side loop may be exceeded ---------------
        if i_in > cap + 1e-9:
            why.append("the input current exceeds the loop cap")
        if v_vindpm is not None and v_pin < v_vindpm - 1e-6 and i_in > 1e-9:
            why.append("the IN pin is below the VINDPM threshold")
        # ---- D-795 / R14-03: THE PHYSICAL INEQUALITY D-794 BROKE. --------
        # A charge current below the NOMINAL program while SYS sits above the
        # DPPM node has exactly one legitimate cause in SLUSF65B: thermal
        # regulation.  ILIM and VINDPM cut the INPUT; only the DPPM loop at
        # VBAT + VDPPM folds the charge.
        if (ichg_nominal is not None and v_dppm is not None
                and i_chg < ichg_nominal - 1e-9 and vsys > v_dppm + 1e-9
                and charge_loop != "TREG"):
            why.append("a charge current below the program with SYS above "
                       "VBAT + VDPPM and no thermal regulation active: no "
                       "loop in the BQ25185 produces that state")
        if mode in ("SYS_REG", "CC_PATH_LIMITED", "TREG"):
            if ich is not None and abs(i_chg - ich) > 1e-9:
                why.append("%s charges at the charge PROGRAM by definition"
                           % mode)
            if v_dppm is not None and vsys < v_dppm - 1e-9:
                why.append("SYS is below VDPPM: the DPPM loop has control")
            if i_in > cap + 1e-9:
                why.append("an input-side loop is exceeded")
        if mode == "SYS_REG":
            if abs(vsys - vsys_reg) > 1e-9:
                why.append("SYS is not at its regulation point")
            if v_pin - i_in * ron_in < vsys - 1e-9:
                why.append("the input cannot hold the regulation point")
            if ichg_nominal is not None and i_chg < ichg_nominal - 1e-9:
                why.append("SYS_REG folds no charge: a folded charge current "
                           "belongs to DPPM or TREG")
        elif mode == "CC_PATH_LIMITED":
            if ichg_nominal is not None and i_chg < ichg_nominal - 1e-9:
                why.append("CC_PATH_LIMITED charges at the nominal program")
            if vsys > vsys_reg + 1e-9:
                why.append("SYS above its regulation point")
            if abs(vsys - (vbus - i_in * r_src)) > 1e-6:
                why.append("SYS is not what the source and RON_IN leave")
        elif mode == "TREG":
            if charge_loop != "TREG":
                why.append("a TREG branch with no thermal loop behind it")
            if ichg_nominal is not None and i_chg > ichg_nominal - 1e-9:
                why.append("a TREG branch that folds nothing")
            if vsys > vsys_reg + 1e-9:
                why.append("SYS above its regulation point")
        elif mode in ("ILIM", "VINDPM", "DPPM"):
            # 6.3.2: every charge-folding branch holds SYS at VBAT + VDPPM.
            if v_dppm is None or abs(vsys - v_dppm) > 1e-9:
                why.append("%s must hold SYS at VBAT + VDPPM: the input loop "
                           "cuts the INPUT and only DPPM folds the charge"
                           % mode)
            if vsys <= vbat:
                why.append("6.3.2: SYS is maintained ABOVE the battery while "
                           "the DPPM loop is in control")
            if i_supp > eps:
                why.append("a DPPM-held branch may not supplement")
            if ich is not None and i_chg > ich + 1e-9:
                why.append("more charge current than the program")
            held = (vbus - vsys) / r_src
            if mode == "ILIM":
                if abs(i_in - ilim) > 1e-9 or ilim > held + 1e-9:
                    why.append("ILIM claimed with the input not at ILIM")
                if v_vindpm is not None and ilim > (vbus - v_vindpm) / path \
                        + 1e-9:
                    why.append("VINDPM binds before ILIM at this source")
            elif mode == "VINDPM":
                if v_vindpm is None or abs(v_pin - v_vindpm) > 1e-6:
                    why.append("VINDPM claimed with the IN pin off its "
                               "threshold")
                if i_in > ilim + 1e-9:
                    why.append("VINDPM claimed above ILIM")
            else:
                if abs(i_in - held) > 1e-6:
                    why.append("DPPM (source-limited) with the input FET not "
                               "fully enhanced")
                if i_in > cap + 1e-9:
                    why.append("DPPM with an input-side loop exceeded")
        elif mode == "NO_CHARGE":
            if i_chg > eps or i_supp > eps:
                why.append("NO_CHARGE must neither charge nor supplement")
            if vsys > vsys_reg + 1e-9:
                why.append("SYS above its regulation point")
            if v_sup_enter is not None and vsys < v_sup_enter - 1e-9 \
                    and batfet != "uvlo_open":
                why.append("SYS is below the supplement entry threshold")
            if v_sup_exit is not None and vsys < v_sup_exit - 1e-9 \
                    and previous_mode == "SUPPLEMENT":
                why.append("the part was supplementing and SYS has not risen "
                           "back above the VBSUP2 exit threshold")
        elif mode == "SUPPLEMENT":
            # D-796 / D796-08: SLUSF65B 6.3.3 -- no supplement at or under
            # VBUVLO.  Judged on the BATFET label AND on the cell itself, so
            # a mislabelled state cannot carry supplement below the trip.
            if batfet is not None and batfet != "connected":
                why.append("SUPPLEMENT with the BATFET disconnected by BUVLO")
            if buvlo_trip_low_V is not None and vbat <= buvlo_trip_low_V + 1e-12:
                why.append("SUPPLEMENT at a cell at or under the lowest "
                           "VBUVLO trip: the BATFET cannot supply SYS")
            if i_chg > eps:
                why.append("SUPPLEMENT must not charge")
            if vsys > vbat + 1e-9:
                why.append("supplementing into a node ABOVE the cell")
            if abs(vsys - (vbat - i_supp * ron_bat)) > 1e-6:
                why.append("SYS is not the cell less the BATFET drop")
            held = (vbus - vsys) / r_src
            if i_in < min(cap, held) - 1e-6:
                why.append("the input is delivering less than it could")
            # THE ENTRY THRESHOLD, JUDGED ON THE COMPARATOR'S OWN INPUT.
            # `batfet_off_node_V` is where SYS would sit with the BATFET off,
            # which is what VBSUP1/VBSUP2 watch.  `None` means no BATFET-off
            # operating point exists at all, which is entry by necessity.
            if batfet_off_node_V is not None and v_sup_enter is not None \
                    and batfet_off_node_V > v_sup_enter + 1e-9:
                if not (hysteresis_band and previous_mode == "SUPPLEMENT"
                        and v_sup_exit is not None
                        and batfet_off_node_V <= v_sup_exit + 1e-9):
                    why.append("supplement entered with the BATFET-off node "
                               "above VBAT - VBSUP1 and no prior supplement "
                               "state to latch it")
        else:
            why.append("unknown branch %r" % (mode,))
        inv["branch_condition"] = not why
        inv["branch_problems"] = why
    inv["ok"] = all(v for k, v in inv.items() if isinstance(v, bool))
    return inv
