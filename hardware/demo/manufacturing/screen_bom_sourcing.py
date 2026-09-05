#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- how much of the BOM sourcing gap does this repository ALREADY
know the answer to, and does the Demo's own board agree?

`checks/fab_package_contract.py` FAB7 measures the gap: of the fitted,
purchased, on-board references in the Demo assembly BOM, most carry neither a
manufacturer part number nor an LCSC code, and a line a supplier cannot quote
is not a finished BOM.  That is a number, not a plan.  This screen turns it
into a RULED work list.

Four prior authorities, all repo-local, none of them invented here:

  DEMO      the Demo schematic's own sourced lines.  If one 0603 100nF already
            names a part, the next one is not an open question.
  BETA-DM   `hardware/beta-dm/fab/jlcpcb/JLC-MATCH-AUDIT.csv` -- a per-line
            CTO audit of a JLCPCB match, carrying an APPROVED part number, a
            verdict and the reasoning, including explicit dielectric and
            voltage rulings.  This is the strongest prior the repository holds.
  LEDGER    `hardware/beta-dm/fab/BETA-DM-MPN-LEDGER.csv` -- the resolved
            manufacturer identity for the named parts of the same family.
  RULED     this project's OWN per-reference sourcing decisions, transcribed
            into `REFERENCE_RULINGS` below with their citation.  The only place
            a designator is the right key, and honoured only when the board's
            own footprint name corroborates the part.

**THE REFERENCE IS NOT THE IDENTITY; THE SPECIFICATION IS.**  The beta-dm
audit rows are keyed by designator, and three of them name a DIFFERENT VALUE
than the Demo carries at the same designator: `R70`-`R73` are 39R in beta-dm
and **33R** here, `R69` is 2.55R there and **1.87R** here, `R19`/`R20` are 4.7k
there and **2.2k** here -- because D-079 re-derived the backlight against the
real panel.  Grafting by designator would have put a 39 ohm part on a 33 ohm
land.  Nothing in this file ever matches on a designator.

**THE MATCH RULE IS BRITTLE FIRST AND REASONED SECOND.**  A candidate is
EXACT_PRIOR only when the value string and the footprint LEAF NAME are equal
character for character.  Anything looser must be RULED, and there is exactly
one ruling this file will make on its own: SPECIFICATION CONTAINMENT, where
the prior's part satisfies the Demo's stated requirement on every axis that
the requirement states --

    same land, EQUAL magnitude, prior tolerance <= demanded tolerance,
    prior voltage >= demanded voltage, prior dielectric class >= demanded
    class, prior power >= demanded power.

and every one of those axes is read off the APPROVED PART NUMBER, not off the
value string the prior was filed under -- see "READING THE PART, NOT THE LINE".

`10uF 10V X7R` and `10uF` are NOT interchangeable in that direction: the first
states a dielectric and a rating and the second states neither, so a 10uF part
of unknown dielectric can never be grafted onto a line that asks for X7R -- but
a 25 V X7R part CAN serve a line that asks for 10 V X7R.  Containment is
one-directional and it is checked, not assumed.

**EVERY CANDIDATE IS RE-CHECKED AGAINST THE DEMO'S OWN NETS.**  The beta-dm
audit notes reason about the net a part sits on in THAT board.  This board is
not that board: `C38`/`C67` sit on `ACC_5V_SW`, a 5 V net the prior audit never
saw against a line whose schematic value says 10 V.  Every capacitor candidate
is gated on the real Demo netlist read from the real board -- rating >= 2x the
node's operating maximum AND rating >= the node's absolute maximum -- and the
screen REFUSES any node whose voltage this repository has not established.

**THE PRIOR'S MANUFACTURER COLUMN IS NOT THE APPROVED PART'S MANUFACTURER.**
For a REJECTED audit row the `JLC Manufacturer` column describes the match that
was THROWN OUT, not the replacement the CTO approved.  Sixteen of the thirty-one
grafts are REJECTED rows, and taking that column would have stamped
`Samsung Electro-Mechanics` on Murata's `GRM31CR71E106KA12L`.  That is D-613's
`C26` defect -- one identity, two meanings -- rebuilt by machine.  The
manufacturer here is DERIVED from the approved MPN's own part-number family and
then CORROBORATED against the audit prose; a derivation with no corroboration is
reported UNRESOLVED and is not grafted.

**A VALUE THAT IS NOT FINAL IS NOT A SOURCING GAP.**  DEVICE_SPEC section 14
marks the NFC matching network TUNE / FIRST-ARTICLE TUNE -- values pending VNA
and the ST tool.  Those lines are reported as `TUNE_PENDING`, separately from
the lines that need a purchasing decision, because no part number can close
them and counting them as unfinished BOM misstates what is left.

Read-only.  It proposes; it changes nothing.  `apply_bom_sourcing.py` writes.

A candidate that survives all of that is still refused unless it also passes
the CURRENT gate on any 0 ohm link it lands on -- the one thing a voltage gate
cannot see, and the one the inherited audit had run on only three of this
board's eight links.

    python3 hardware/demo/manufacturing/screen_bom_sourcing.py \\
        [--package DIR] [--board PCB] [-o OUT] [--plan PLAN.json] \\
        [--worklist OPEN.csv]

Buckets: EXACT_PRIOR, CONTAINED_PRIOR, REFERENCE_RULING (all graftable),
REFUSED (a gate said no), NEAR_MISS, TUNE_PENDING, NO_CANDIDATE.
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

PACKAGE = ROOT / "hardware/demo/fab"
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
AUDIT = ROOT / "hardware/beta-dm/fab/jlcpcb/JLC-MATCH-AUDIT.csv"
LEDGER = ROOT / "hardware/beta-dm/fab/BETA-DM-MPN-LEDGER.csv"

# --------------------------------------------------------------------------
# The node voltages this repository has ESTABLISHED.  A node that is not here
# is not guessed: the candidate on it is reported UNRESOLVED_NET and refused.
#
#   operating  the highest DC the node reaches in normal service
#   absolute   the highest DC the node can reach at all, i.e. what a clamp,
#              an OVP or a supply's own abs-max permits.  Equal to
#              `operating` unless something on the node bounds a fault above it.
# --------------------------------------------------------------------------
NET_MAX_DC = {
    "GND": (0.0, 0.0, "board ground"),
    "+3V3": (3.3, 3.6, "U12 TPS63020 buck-boost +3V3 rail (DEVICE_SPEC s.11)"),
    "Net-(U1-EN)": (3.3, 3.6, "U1 EN, pulled to +3V3 through R1 10k"),
    "NFC_AGDC": (3.3, 3.6, "ST25R3916 AGD reference, supplied from NFC_SUPPLY"),
    "NFC_SUPPLY": (3.3, 3.6, "DEVICE_SPEC s.13: NFC runs from +3V3 via R106 FIT;"
                             " the 5 V PA boost branch is DNP"),
    "IR_RX_VS_LOCAL": (3.3, 3.6, "U6 TSOP38238 local supply, R21 100R from +3V3"),
    "USB_VBUS_RAW": (5.25, 5.5, "USB VBUS at J3; USB 2.0 source maximum 5.25 V"),
    "USB_VBUS_CHG": (5.25, 5.5, "USB VBUS through the R35 0R link"),
    "VBUS_PRESENT": (5.25, 5.5, "R104 150k / R105 220k divider off USB_VBUS_CHG"
                                " (operating ~3.1 V); bounded by its source"),
    "VREC_VCC": (5.25, 5.5, "U19 TLV7032 supply, R84 100R from USB_VBUS_CHG"),
    "BAT_PROTECTED_P": (4.2, 4.35, "single-cell Li-ion, charge termination 4.2 V;"
                                   " BQ25185 OVP bounds the fault"),
    "BAT_RAW": (4.2, 4.35, "single-cell Li-ion at the cell side of the protection"),
    "N_BATDIV": (4.2, 4.35, "R89 2.2M / R90 2.2M divider off BAT_RAW"
                            " (operating ~2.1 V); bounded by its source"),
    "BQ25185_SYS": (4.5, 5.5, "BQ25185 SYS; TI SLUSF65A 8.2.2.3 asks for 25 V"
                              " parts on IN/SYS, and SYS follows VBUS on adapter"),
    "ACC_3V3_SW": (3.3, 3.6, "switched 3.3 V accessory rail"),
    "ACC_5V_SW": (5.5, 5.5, "switched 5 V accessory rail from the U21 TPS61023 boost"),
    "LED_BOOST": (4.5, 38.0,
                  "U17 TPS61169 WLED boost output.  ARCHITECTURE D-079: the panel"
                  " backlight is SIX LEDs IN PARALLEL, one anode, 2.9-3.2 V, at"
                  " I_LED 109 mA typ -- so the node runs at Vf 3.2 V + 109 mA"
                  " through R70-R73 (4x33R = 8.25R, 0.90 V) + the R69 1.87R sense"
                  " (0.20 V) = 4.3 V.  The FAULT ceiling is the TPS61169 open-LED"
                  " OVP, and D8 NSR0240 is a 40 V catch diode."),
}

# Land -> the working voltage a chip part of that size is rated for.  Used only
# to state that no resistor on this board sits above its land's rating.
LAND_WORKING_V = {
    "0402": 50.0, "0603": 50.0, "0805": 150.0,
    "1206": 200.0, "1210": 200.0, "2512": 200.0,
}

# The highest DC any node on this board can reach.  Every node is fed from one
# of the supplies in NET_MAX_DC, and the highest of those is the TPS61169
# open-LED OVP ceiling; every other supply is at or below 5.5 V.  A node this
# screen has not established individually is still bounded by this number.
BOARD_MAX_DC = 38.0

# --------------------------------------------------------------------------
# A FOURTH AUTHORITY, AND THE ONE PLACE A DESIGNATOR IS THE RIGHT KEY.
#
# Everything above matches on a SPECIFICATION and never on a designator,
# because the beta-dm audit's designators name a different board.  But this
# project has also made per-reference sourcing decisions of its own, in
# `docs/full-beta-v2/assembly/SOURCING_LEDGER.md`, which is normative for the
# evidence behind an MPN, and DEVICE_SPEC s.16 lists `J8`'s missing MPN/LCSC
# property as a KNOWN OPEN ITEM.  The part was chosen at D-238; only the
# schematic property was never written.
#
# Such a ruling is only honoured when the BOARD corroborates it: the required
# substring must appear in the line's own footprint name, so a reference that
# has been re-landed since the decision cannot silently inherit it.
# --------------------------------------------------------------------------
REFERENCE_RULINGS = {
    "J8": dict(
        Manufacturer="JST", MPN="SM04B-SRSS-TB(LF)(SN)", LCSC="",
        corroborate_in_footprint="SM04B-SRSS-TB",
        basis="D-238, recorded in docs/full-beta-v2/assembly/SOURCING_LEDGER.md"
              " s.2 (JST SH, 1.0 mm, 4 circuit, side entry, SMT, 1.0 A,"
              " 50 V) and in DEVICE_SPEC s.10.2, which also lists the absent"
              " schematic property as an open item.  The plating-suffixed"
              " string is the one D-096 requires: the bare order code resolves"
              " to a zero-stock listing"),
}


# --------------------------------------------------------------------------
# THE ONE THING A LAND-VOLTAGE GATE CANNOT SEE: CURRENT.
#
# A 0 ohm link is the only chip resistor on this board that carries a supply,
# and the beta-dm audit closed its current gate against THREE references.  The
# Demo has EIGHT.  `R121`/`R122` sit in the speaker output and `R106` carries
# the whole NFC front end -- neither existed in the audited set.  A graft that
# adopted the audit's verdict would have adopted a gate that was never run on
# five of the eight parts, which is D-611's lesson exactly: a passing check may
# mean the question was never asked.
#
# So: every grafted 0 ohm reference must appear here with a number, or the line
# is refused.  Rating is the UNI-ROYAL ZW-series 0603 jumper the audit names --
# 1 A continuous, 2 A overload, under 50 mOhm.
# --------------------------------------------------------------------------
JUMPER_RATING_A = 1.0
ZERO_OHM_CURRENT = {
    "R32": (0.0, "J3 SHIELD to GND -- a shield bond, no continuous current"
                 " (beta-dm audit, verbatim)"),
    "R35": (0.500, "the only power-node jumper: USB_VBUS_RAW to USB_VBUS_CHG."
                   "  Worst case is the BQ25185 input current limit, and TI"
                   " SLUSF65A 8.2.2.1 gives 500 mA for R_ILIM/VSET = 18k --"
                   " the Demo's R36 IS 18k and its R37 IS 1k, so the audited"
                   " number still holds on this board"),
    "R42": (0.0, "U12 PS/SYNC strap to GND, signal level"
                 " (beta-dm audit, verbatim)"),
    "R106": (0.150, "NFC supply select link, +3V3 to NFC_SUPPLY, carrying the"
                    " whole ST25R3916 front end.  D-130 bounds the NFC field"
                    " current at 150 mA at 3.3 V.  NOT in the audited set."),
    "R109": (0.001, "DISP_BL_CTL to DISP_BL_CTL_STRAP, an MCU strap link"
                    " (DEVICE_SPEC s.14), signal level.  NOT in the audited set."),
    "R118": (0.001, "BMI270 SDO address strap to GND, signal level."
                    "  NOT in the audited set."),
    "R121": (0.292, "speaker output SPK_P.  U5 MAX98357A bridge-tied from"
                    " +3V3: peak differential 3.3 V, 2.33 Vrms into the 8 ohm"
                    " LS1, 0.68 W, I_rms 0.292 A -- above the speaker's own"
                    " 0.5 W rating (0.250 A), so the amplifier bounds it."
                    "  NOT in the audited set."),
    "R122": (0.292, "speaker output SPK_N, identical to R121."
                    "  NOT in the audited set."),
}


# --------------------------------------------------------------------------
# READING THE PART, NOT THE LINE.
#
# `1uF 10V X7R` is what the SCHEMATIC asks for.  The part the beta-dm audit
# approved for it is a 25 V YAGEO, because the audit deliberately bought
# margin.  A gate that derates the schematic's number instead of the part's
# rating is measuring the wrong object -- the same failure D-613 found four
# times over -- so every rating, dielectric, tolerance, capacitance and LAND
# used below is decoded FROM THE APPROVED PART NUMBER and then required to
# agree with the audit prose.  Two independent readings or the line is refused.
#
# Every code in these tables is corroborated by a note in this repository that
# states the same value in words.  An unknown code decodes to None; it is never
# guessed.
# --------------------------------------------------------------------------
MPN_FAMILY = (
    (r"^\d{4}W[AG]F.*T5E$", "UNI-ROYAL(Uniroyal Elec)", ("UNI-ROYAL", "UNIROYAL")),
    (r"^CC\d{4}[A-Z]{2}[A-Z0-9]", "YAGEO", ("YAGEO",)),
    (r"^CL\d{2}[A-Z]", "Samsung Electro-Mechanics", ("Samsung",)),
    (r"^GRM\d", "Murata Electronics", ("Murata",)),
    (r"^TCC\d", "CCTC", ("CCTC",)),
)

YAGEO_V = {"7BB": 16.0, "8BB": 25.0, "9BB": 50.0}
SAMSUNG_V = {"AQ": 25.0, "B8": 50.0, "BF": 50.0}
SAMSUNG_D = {"A": "X5R", "B": "X7R"}
MURATA_V = {"1A": 10.0, "1C": 16.0, "1E": 25.0, "1H": 50.0}
MURATA_D = {"R6": "X5R", "R7": "X7R"}
CL_LAND = {"05": "0402", "10": "0603", "21": "0805", "31": "1206"}
GRM_LAND = {"15": "0402", "18": "0603", "21": "0805", "31": "1206"}
UNIROYAL_TOL = {"F": 1.0, "D": 0.5, "B": 0.1, "J": 5.0}


def eia3(code):
    """`105` -> 1e-6 F, `226` -> 22e-6 F.  Three digits, picofarads."""
    if not re.fullmatch(r"\d{3}", code):
        return None
    return int(code[:2]) * (10 ** int(code[2])) * 1e-12


def ohms3(code):
    """`1002` -> 10000 R.  Four characters, the last a decade exponent."""
    if not re.fullmatch(r"\d{4}", code):
        return None
    return int(code[:3]) * (10 ** int(code[3]))


def decode_mpn(mpn):
    """The specification the PART NUMBER ITSELF states, or empty where it does
    not.  Also the land the part number is built for -- because one part number
    on two land patterns is exactly the defect D-613 found on `C26`."""
    out = dict(magnitude=None, voltage=None, dielectric=None, tolerance=None,
               land=None, power=None)
    m = re.match(r"^CC(\d{4})([A-Z])([A-Z])(C0G|NP0|X5R|X6S|X7R|X7S)"
                 r"(\d[A-Z]{2})(\d{3})$", mpn)
    if m:
        out.update(land=m.group(1), dielectric=m.group(4),
                   voltage=YAGEO_V.get(m.group(5)), magnitude=eia3(m.group(6)))
        return out
    m = re.match(r"^CL(\d{2})([A-Z])(\d{3})([A-Z])([A-Z0-9]{2})", mpn)
    if m:
        out.update(land=CL_LAND.get(m.group(1)),
                   dielectric=SAMSUNG_D.get(m.group(2)),
                   magnitude=eia3(m.group(3)),
                   voltage=SAMSUNG_V.get(m.group(5)))
        return out
    m = re.match(r"^GRM(\d{2})[A-Z]([A-Z]\d)(\d[A-Z])(\d{3})", mpn)
    if m:
        out.update(land=GRM_LAND.get(m.group(1)),
                   dielectric=MURATA_D.get(m.group(2)),
                   voltage=MURATA_V.get(m.group(3)),
                   magnitude=eia3(m.group(4)))
        return out
    m = re.match(r"^TCC(\d{4})(C0G|NP0|X5R|X7R)(\d{3})([A-Z])(\d{3})", mpn)
    if m:
        out.update(land=m.group(1), dielectric=m.group(2),
                   magnitude=eia3(m.group(3)),
                   voltage=int(m.group(5)[:2]) * (10 ** int(m.group(5)[2])))
        return out
    m = re.match(r"^(\d{4})W[A-Z]([A-Z])([0-9A-Z]{4})T5E$", mpn)
    if m:
        out.update(land=m.group(1), tolerance=UNIROYAL_TOL.get(m.group(2)),
                   magnitude=ohms3(m.group(3)))
        return out
    return out


RE_NOTE_CAP = re.compile(r"(\d+(?:\.\d+)?)\s*([pnu\u00b5m]?)F\s+(\d+(?:\.\d+)?)\s*V"
                         r"(?:\s+(C0G|NP0|X5R|X6S|X7R|X7S))?", re.I)
RE_NOTE_TOL = re.compile(r"(?:\+/-|\u00b1)\s*(\d+(?:\.\d+)?)\s*%")


def decode_note(note, magnitude, kind):
    """Everything the audit PROSE says about a part of this magnitude, as a
    LIST per axis.  A note argues -- it describes the match that was thrown out
    as well as the one that was approved ("JLC chose ... +/-0.1% ...;
    requirement is 1%") -- so the prose is used to CORROBORATE the part number,
    never to outvote it."""
    out = dict(voltage=[], dielectric=[], tolerance=[])
    if kind == "C":
        for m in RE_NOTE_CAP.finditer(note):
            value = float(m.group(1)) * CAP_PREFIX.get(
                m.group(2).lower().replace("\u00b5", "u"), 1.0)
            if same_magnitude(value, magnitude):
                out["voltage"].append(float(m.group(3)))
                if m.group(4):
                    out["dielectric"].append(m.group(4).upper())
    else:
        out["tolerance"] = [float(m.group(1)) for m in RE_NOTE_TOL.finditer(note)]
    return out


def part_spec(cand, prior_value, land):
    """The approved part's own specification, read twice and made to agree.

    Returns (spec, problems).  A disagreement between the part number and the
    prose is a problem, not a tie to be broken.
    """
    demanded = parse_spec(prior_value, land)
    mpn = decode_mpn(cand.get("mpn", "") or "")
    note = decode_note(cand.get("note", "") or "", demanded["magnitude"],
                       demanded["kind"])
    problems = []

    if mpn["land"] and land_size(land) and mpn["land"] != land_size(land):
        problems.append("part number is built for land %s, the line is %s"
                        % (mpn["land"], land_size(land)))
    if (mpn["magnitude"] is not None and demanded["magnitude"] is not None
            and abs(mpn["magnitude"] - demanded["magnitude"])
            > 1e-12 * max(1.0, abs(demanded["magnitude"]))):
        problems.append("part number decodes %r, the line asks %r"
                        % (mpn["magnitude"], demanded["magnitude"]))

    spec = dict(demanded)
    spec["source"] = {}
    for axis in ("voltage", "dielectric", "tolerance"):
        a, said = mpn.get(axis), note.get(axis) or []
        if a is not None:
            spec[axis] = a
            if said and a not in said:
                problems.append("%s: part number says %r, and the audit text"
                                " says only %r" % (axis, a, said))
            spec["source"][axis] = ("part number, corroborated by the note"
                                    if a in said else "part number")
        elif len(set(said)) == 1:
            spec[axis] = said[0]
            spec["source"][axis] = "audit note"
        elif said:
            problems.append("%s: the audit text offers %r and the part number"
                            " settles nothing" % (axis, sorted(set(said))))
    spec["magnitude"] = (mpn["magnitude"] if mpn["magnitude"] is not None
                         else demanded["magnitude"])
    spec["annotations"] = []
    spec["tune"] = False
    return spec, problems


DIELECTRIC_RANK = {"Y5V": 0, "X5R": 1, "X6S": 2, "X7S": 3, "X7R": 4,
                   "C0G": 5, "NP0": 5}
DIELECTRICS = set(DIELECTRIC_RANK)

# Value tokens that say something about STUFFING or about the land, not about
# the electrical specification.  `TUNE` is not here -- it says the value itself
# is not final, which is a different thing entirely.
ANNOTATIONS = {"FIT", "DNP"}

RE_CAP = re.compile(r"^(\d+(?:\.\d+)?)\s*([pnuµm]?)F$", re.I)
# `15mR` is fifteen MILLIohms and `1M` is one MEGohm; a pattern that reads only
# a single suffix letter silently drops the first and this board has one --
# `R75`, the 15 mOhm 1 W battery current sense.  It came back with no
# requirement at all until the screen was made to say so out loud.
RE_RES = re.compile(r"^(\d+(?:\.\d+)?)(mR|uR|\u00b5R|R|k|K|M|G)?$")
RE_RES_DP = re.compile(r"^(\d+)R(\d+)$")           # 1R1 = 1.1 ohm
RE_VOLT = re.compile(r"^(\d+(?:\.\d+)?)V$", re.I)
RE_TOL = re.compile(r"^(\d+(?:\.\d+)?)%$")
RE_PWR = re.compile(r"^(\d+(?:\.\d+)?)W$", re.I)
RE_LAND_SIZE = re.compile(r"_(\d{4})_")

CAP_PREFIX = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3}
RES_SUFFIX = {"mR": 1e-3, "uR": 1e-6, "\u00b5R": 1e-6, "R": 1.0,
              "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9, None: 1.0}


def rows(path):
    if not Path(path).exists():
        return []
    return list(csv.DictReader(Path(path).open(newline="",
                                               encoding="utf-8-sig")))


def leaf(footprint):
    """`Capacitor_SMD:C_0603_1608Metric` and `C_0603_1608Metric` are one land."""
    return footprint.strip().rsplit(":", 1)[-1]


def land_size(land):
    m = RE_LAND_SIZE.search(land)
    return m.group(1) if m else None


def loose(value):
    """The comparison a NEAR_MISS is allowed to make, and no more."""
    return " ".join(value.split()).casefold()


# --------------------------------------------------------------------------
# Specification parsing
# --------------------------------------------------------------------------

def parse_spec(value, land):
    """A value string as a SPECIFICATION, or `kind='OPAQUE'` if it is not one.

    Nothing here invents a requirement the string does not state.  An axis the
    string is silent about comes back `None`, and a `None` requirement is
    satisfied by anything -- which is exactly how the beta-dm audit reasoned
    ("Schematic states no dielectric, so X5R is permitted").
    """
    text = " ".join(value.split())
    spec = dict(raw=value, kind=None, magnitude=None, voltage=None,
                tolerance=None, dielectric=None, power=None,
                tune=False, annotations=[], unparsed=[])

    # Magnitude first, because it may carry a space (`100 nF`).
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([pnuµm]?)F\b", text, re.I)
    if m:
        spec["kind"] = "C"
        spec["magnitude"] = float(m.group(1)) * CAP_PREFIX.get(
            m.group(2).lower().replace("µ", "u"), 1.0)
        rest = text[m.end():].split()
    else:
        head, _, tail = text.partition(" ")
        m = RE_RES_DP.match(head)
        if m:
            spec["kind"] = "R"
            spec["magnitude"] = float("%s.%s" % (m.group(1), m.group(2)))
        else:
            m = RE_RES.match(head)
            if m and (m.group(2) or head.replace(".", "").isdigit()):
                spec["kind"] = "R"
                spec["magnitude"] = float(m.group(1)) * RES_SUFFIX[m.group(2)]
        rest = tail.split() if spec["kind"] else []

    if spec["kind"] is None:
        spec["kind"] = "OPAQUE"
        return spec

    size = land_size(land)
    for tok in rest:
        up = tok.upper()
        if up == "TUNE":
            spec["tune"] = True
        elif up in ANNOTATIONS or (size and up == size):
            spec["annotations"].append(up)
        elif up in DIELECTRICS:
            spec["dielectric"] = up
        elif RE_VOLT.match(tok):
            spec["voltage"] = float(RE_VOLT.match(tok).group(1))
        elif RE_TOL.match(tok):
            spec["tolerance"] = float(RE_TOL.match(tok).group(1))
        elif RE_PWR.match(tok):
            spec["power"] = float(RE_PWR.match(tok).group(1))
        else:
            spec["unparsed"].append(tok)
    return spec


def same_magnitude(a, b):
    """`100 * 1e-9` and `10 * 10**4 * 1e-12` are the same capacitor.  They are
    not the same float, and a BOM must not turn a rounding artefact into a
    different part."""
    if a is None or b is None:
        return a is b
    return abs(a - b) <= 1e-9 * max(abs(a), abs(b))


def contains(prior, demand):
    """Does the PRIOR's specification satisfy everything the DEMAND states?

    One-directional on purpose.  Returns (bool, reasons) so a refusal can be
    read rather than guessed at.
    """
    why = []
    if prior["kind"] != demand["kind"] or prior["kind"] == "OPAQUE":
        return False, ["different kind of part"]
    if prior["unparsed"] or demand["unparsed"]:
        return False, ["value carries a token this screen cannot read: %s"
                       % (prior["unparsed"] + demand["unparsed"])]
    if demand["tune"]:
        return False, ["the demanded value is not final (TUNE)"]
    if prior["tune"]:
        return False, ["the prior value is not final (TUNE)"]
    if not same_magnitude(prior["magnitude"], demand["magnitude"]):
        return False, ["magnitude %r != %r" % (prior["magnitude"],
                                               demand["magnitude"])]
    if demand["tolerance"] is not None:
        if prior["tolerance"] is None or prior["tolerance"] > demand["tolerance"]:
            return False, ["prior tolerance %r does not meet %r%%"
                           % (prior["tolerance"], demand["tolerance"])]
        why.append("tolerance %s%% meets %s%%" % (prior["tolerance"],
                                                  demand["tolerance"]))
    if demand["voltage"] is not None:
        if prior["voltage"] is None or prior["voltage"] < demand["voltage"]:
            return False, ["prior rating %r does not meet %rV"
                           % (prior["voltage"], demand["voltage"])]
        why.append("rating %sV meets %sV" % (prior["voltage"],
                                             demand["voltage"]))
    if demand["dielectric"] is not None:
        if (prior["dielectric"] is None
                or DIELECTRIC_RANK[prior["dielectric"]]
                < DIELECTRIC_RANK[demand["dielectric"]]):
            return False, ["prior dielectric %r does not meet %s"
                           % (prior["dielectric"], demand["dielectric"])]
        why.append("dielectric %s meets %s" % (prior["dielectric"],
                                               demand["dielectric"]))
    if demand["power"] is not None:
        if prior["power"] is None or prior["power"] < demand["power"]:
            return False, ["prior power %r does not meet %rW"
                           % (prior["power"], demand["power"])]
        why.append("power %sW meets %sW" % (prior["power"], demand["power"]))
    dropped = sorted(set(demand["annotations"]) - set(prior["annotations"]))
    if dropped:
        why.append("annotation %s is a stuffing/land note, not a "
                   "specification" % ",".join(dropped))
    return True, why or ["identical specification"]


# --------------------------------------------------------------------------
# Manufacturer: derived from the approved MPN, corroborated by the prose
# --------------------------------------------------------------------------

def manufacturer_for(mpn, corroborate):
    """The manufacturer the approved MPN's own family implies, if the audit
    text agrees.  `corroborate` is every string the row offers about the part.
    """
    for pattern, name, tokens in MPN_FAMILY:
        if re.match(pattern, mpn):
            hay = " ".join(corroborate).upper()
            if any(t.upper() in hay for t in tokens):
                return name, "derived from the %s part-number family and " \
                             "corroborated by the audit text" % name
            return None, "MPN family says %s but the audit text does not " \
                         "corroborate it" % name
    return None, "no known part-number family for %r" % mpn


# --------------------------------------------------------------------------
# Priors
# --------------------------------------------------------------------------

def priors(demo_bom):
    """(value, footprint-leaf) -> the candidates this repository already holds."""
    out = defaultdict(list)
    for row in demo_bom:
        mpn, lcsc = row.get("MPN", "").strip(), row.get("LCSC", "").strip()
        if mpn or lcsc:
            out[(row["Value"].strip(), leaf(row["Footprint"]))].append(dict(
                source="DEMO", mpn=mpn, lcsc=lcsc,
                manufacturer=row.get("Manufacturer", "").strip(),
                manufacturer_basis="the Demo schematic's own property",
                note="already sourced on this board: %s" % row["Refs"]))
    for row in rows(AUDIT):
        part = row.get("Approved JLCPCB Part #", "").strip()
        mpn = row.get("Approved MPN", "").strip()
        if not part and not mpn:
            continue
        verdict = row.get("JLC Auto-match Verdict", "").strip()
        note = row.get("Audit note", "").strip()
        accepted = verdict.upper().startswith("ACCEPTED")
        # For an ACCEPTED row the approved part IS the matched part, so the
        # match's own manufacturer column describes it.  For a REJECTED row it
        # describes the part that was thrown out and must not be adopted.
        corroborate = [note, row.get("Approved MPN", "")]
        if accepted:
            corroborate.append(row.get("JLC Manufacturer", ""))
        maker, basis = manufacturer_for(mpn, corroborate)
        out[(row["AQROOT Comment"].strip(),
             leaf(row["AQROOT Footprint"]))].append(dict(
                 source="BETA-DM", mpn=mpn, lcsc=part,
                 manufacturer=maker, manufacturer_basis=basis,
                 verdict=verdict,
                 rejected_match_manufacturer=(
                     None if accepted else row.get("JLC Manufacturer", "").strip()),
                 note=note))
    for row in rows(LEDGER):
        mpn = row.get("MPN", "").strip()
        if not mpn:
            continue
        out[(row["Value"].strip(), leaf(row["Footprint"]))].append(dict(
            source="LEDGER", mpn=mpn, lcsc="",
            manufacturer=row.get("Manufacturer", "").strip(),
            manufacturer_basis="the beta-dm MPN ledger's own column",
            note=row.get("Status", "").strip()))
    return out


# --------------------------------------------------------------------------
# The Demo's own nets
# --------------------------------------------------------------------------

def board_nets(path):
    """reference -> the non-ground net leaf names its pads sit on."""
    sys.stderr = open(os.devnull, "w")
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    sys.stderr = sys.__stderr__
    out = {}
    for fp in board.GetFootprints():
        nets = set()
        for pad in fp.Pads():
            name = pad.GetNetname().rsplit("/", 1)[-1]
            if name and name != "GND":
                nets.add(name)
        out[fp.GetReference()] = sorted(nets)
    return out


def net_gate(refs, nets, spec_v, land):
    """Does a part rated `spec_v` survive every node the Demo puts it on?

    Two limbs, and both must hold: the project's 2x derating rule against the
    node's OPERATING maximum, and plain survival against its ABSOLUTE maximum.
    A node this repository has not established individually is not guessed at
    -- for a part with a stated rating it is REFUSED, and for one without
    (a resistor) it falls back to `BOARD_MAX_DC`, which bounds every node on
    the board from above.
    """
    seen, unknown = [], []
    for ref in refs:
        for name in nets.get(ref, []):
            if name in NET_MAX_DC:
                seen.append((ref, name) + NET_MAX_DC[name])
            else:
                unknown.append("%s on %s" % (ref, name))
    nodes = sorted({s[1] for s in seen})
    operating = max([s[2] for s in seen], default=0.0)
    absolute = max([s[3] for s in seen], default=0.0)

    if spec_v is None:
        # A resistor: no rating to derate, so the claim is simply that the
        # land's working voltage is above anything the board can present.
        bound = max(absolute, BOARD_MAX_DC) if unknown else absolute
        working = LAND_WORKING_V.get(land_size(land))
        return dict(ok=bool(working) and working >= bound,
                    kind="land working voltage vs the highest node",
                    nodes=nodes, established_max_v=absolute,
                    bounded_max_v=bound, land_working_v=working,
                    nodes_not_individually_established=sorted(set(unknown)))
    if unknown:
        return dict(ok=False, kind="2x operating and survives absolute",
                    reason="node voltage not established",
                    nodes=nodes, unresolved=sorted(set(unknown)))
    return dict(ok=(spec_v >= 2 * operating and spec_v >= absolute),
                kind="2x operating and survives absolute",
                nodes=nodes, operating_max_v=operating,
                absolute_max_v=absolute, rating_v=spec_v,
                margin_x=round(spec_v / operating, 2) if operating else None)


def current_gate(refs, demand):
    """A 0 ohm link carries whatever the net carries.  Refuse any that has not
    been given a number."""
    if demand["kind"] != "R" or demand["magnitude"] != 0.0:
        return dict(ok=True, kind="not a zero-ohm link")
    missing = sorted(r for r in refs if r not in ZERO_OHM_CURRENT)
    if missing:
        return dict(ok=False, kind="zero-ohm link", reason=
                    "no current ruling for %s" % ", ".join(missing),
                    without_a_ruling=missing)
    worst = max((ZERO_OHM_CURRENT[r][0], r) for r in refs)
    return dict(ok=worst[0] <= JUMPER_RATING_A, kind="zero-ohm link",
                rating_a=JUMPER_RATING_A, worst_case_a=worst[0],
                worst_case_ref=worst[1],
                margin_x=(round(JUMPER_RATING_A / worst[0], 2)
                          if worst[0] else None),
                rulings={r: dict(amps=ZERO_OHM_CURRENT[r][0],
                                 basis=ZERO_OHM_CURRENT[r][1]) for r in refs})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=PACKAGE)
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--plan", type=Path,
                    help="write the graft plan apply_bom_sourcing.py consumes")
    ap.add_argument("--worklist", type=Path,
                    help="write the still-open lines as a purchasing brief")
    a = ap.parse_args()

    bom = rows(a.package / "aqroot-Demo-BOM-assembly.csv")
    if not bom:
        raise SystemExit("no assembly BOM at %s -- run export_fab_package.py"
                         % a.package)
    nets = board_nets(a.board)
    known = priors(bom)
    parsed_prior = {k: parse_spec(k[0], k[1]) for k in known}
    by_land = defaultdict(list)
    for key in known:
        by_land[key[1]].append(key)
    by_loose = defaultdict(list)
    for (value, land), cands in known.items():
        by_loose[(loose(value), land)].extend(
            dict(c, prior_value=value) for c in cands)

    exact, contained, near, tune, none_, refused = [], [], [], [], [], []
    for row in bom:
        if row.get("MPN", "").strip() or row.get("LCSC", "").strip():
            continue
        value, land = row["Value"].strip(), leaf(row["Footprint"])
        refs = [r for r in row["Refs"].split(",") if r]
        demand = parse_spec(value, land)
        line = dict(refs=refs, qty=len(refs), value=value, footprint=land,
                    spec=demand)

        if demand["tune"]:
            tune.append(dict(line, why="DEVICE_SPEC s.14 TUNE / FIRST-ARTICLE"
                                       " TUNE -- the VALUE is not final, so no"
                                       " part number can close this line"))
            continue

        ruled = REFERENCE_RULINGS.get(refs[0]) if len(refs) == 1 else None
        if ruled:
            want = ruled["corroborate_in_footprint"]
            if want not in row["Footprint"]:
                refused.append(dict(line, refused=(
                    "the per-reference ruling for %s names %r, which the"
                    " line's own footprint %r does not corroborate"
                    % (refs[0], want, land))))
            else:
                contained.append(dict(
                    line, how="REFERENCE_RULING",
                    ruling=[ruled["basis"]],
                    chosen=dict(source="SOURCING-LEDGER", mpn=ruled["MPN"],
                                lcsc=ruled["LCSC"],
                                manufacturer=ruled["Manufacturer"],
                                manufacturer_basis="named with the part in"
                                                   " SOURCING_LEDGER"),
                    part=demand, prior_value=refs[0],
                    net_gate=dict(ok=True, kind="not a chip passive"),
                    current_gate=dict(ok=True, kind="not a zero-ohm link")))
            continue

        # Every prior on this land, each read as the PART it approves rather
        # than as the value string it was filed under.
        offers = []
        for key in [(value, land)] + [k for k in by_land[land]
                                      if k != (value, land)]:
            for cand in known.get(key, []):
                spec, problems = part_spec(cand, key[0], land)
                ok, why = contains(spec, demand)
                offers.append(dict(
                    cand=cand, prior_value=key[0], part=spec,
                    exact=(key[0] == value), contains=ok, why=why,
                    problems=problems,
                    usable=(ok and not problems
                            and bool(cand.get("manufacturer")))))
        usable = [o for o in offers if o["usable"]]
        if not usable:
            blocked = [o for o in offers if o["contains"]]
            if blocked:
                refused.append(dict(line, offers=blocked[:4], refused=(
                    "; ".join(blocked[0]["problems"])
                    or "manufacturer unresolved: %s"
                    % blocked[0]["cand"].get("manufacturer_basis"))))
            elif by_loose.get((loose(value), land)):
                near.append(dict(line, candidates=by_loose[(loose(value), land)],
                                 why="matches only after case/whitespace folding"
                                     " and does not survive containment"))
            else:
                none_.append(dict(line, other_values_on_this_land=sorted(
                    {v for v, l in known if l == land})[:12],
                    nearest=[dict(prior_value=o["prior_value"],
                                  refused=o["why"]) for o in offers[:4]]))
            continue

        # An exact filing first, then the strongest prior; ties broken toward
        # the highest rating, because margin the audit already bought is
        # margin this board keeps.
        order = {"BETA-DM": 0, "DEMO": 1, "LEDGER": 2}
        pick = sorted(usable, key=lambda o: (
            not o["exact"], order.get(o["cand"]["source"], 9),
            -(o["part"]["voltage"] or 0)))[0]
        gate = net_gate(refs, nets, pick["part"]["voltage"], land)
        current = current_gate(refs, demand)
        entry = dict(line, how="EXACT_PRIOR" if pick["exact"]
                     else "CONTAINED_PRIOR",
                     ruling=pick["why"], chosen=pick["cand"],
                     part=pick["part"], prior_value=pick["prior_value"],
                     net_gate=gate, current_gate=current)
        if not gate["ok"] or not current["ok"]:
            entry["refused"] = (gate.get("reason", "node voltage gate")
                                if not gate["ok"] else current["reason"])
            refused.append(entry)
        elif pick["exact"]:
            exact.append(entry)
        else:
            contained.append(entry)

    def parts(bucket):
        return sum(row["qty"] for row in bucket)

    graftable = exact + contained
    doc = dict(
        schema=2,
        package=str(a.package), board=str(a.board),
        assembly_lines=len(bom),
        unsourced_lines=(len(graftable) + len(refused) + len(near)
                         + len(tune) + len(none_)),
        unsourced_parts=(parts(graftable) + parts(refused) + parts(near)
                         + parts(tune) + parts(none_)),
        summary={
            "EXACT_PRIOR": dict(lines=len(exact), parts=parts(exact)),
            "CONTAINED_PRIOR": dict(lines=len(contained),
                                    parts=parts(contained)),
            "REFUSED": dict(lines=len(refused), parts=parts(refused)),
            "NEAR_MISS": dict(lines=len(near), parts=parts(near)),
            "TUNE_PENDING": dict(lines=len(tune), parts=parts(tune)),
            "NO_CANDIDATE": dict(lines=len(none_), parts=parts(none_)),
        },
        graftable=dict(lines=len(graftable), parts=parts(graftable)),
        prior_sources=dict(
            DEMO=sum(1 for c in known.values() for x in c
                     if x["source"] == "DEMO"),
            BETA_DM=sum(1 for c in known.values() for x in c
                        if x["source"] == "BETA-DM"),
            LEDGER=sum(1 for c in known.values() for x in c
                       if x["source"] == "LEDGER"),
        ),
        unreadable=sorted(
            "%s | %s" % (r["value"], r["footprint"])
            for r in tune + none_ + near
            if r["spec"]["kind"] == "OPAQUE" or r["spec"]["unparsed"]),
        no_candidate_prefixes=dict(Counter(
            r.rstrip("0123456789") for row in none_ for r in row["refs"])),
        tune_refs=sorted(r for row in tune for r in row["refs"]),
        EXACT_PRIOR=exact, CONTAINED_PRIOR=contained, REFUSED=refused,
        NEAR_MISS=near, TUNE_PENDING=tune, NO_CANDIDATE=none_)

    text = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(text)
    if a.plan:
        plan = []
        for entry in graftable:
            pick = entry["chosen"]
            plan.append(dict(
                refs=entry["refs"], value=entry["value"],
                footprint=entry["footprint"], how=entry["how"],
                Manufacturer=pick["manufacturer"], MPN=pick["mpn"],
                LCSC=pick["lcsc"],
                basis=dict(source=pick["source"],
                           prior_value=entry["prior_value"],
                           verdict=pick.get("verdict"),
                           manufacturer_basis=pick["manufacturer_basis"],
                           part_rating_v=entry["part"].get("voltage"),
                           part_dielectric=entry["part"].get("dielectric"),
                           part_tolerance=entry["part"].get("tolerance"),
                           rating_read_from=entry["part"].get("source", {}),
                           ruling=entry["ruling"],
                           net_gate=entry["net_gate"],
                           current_gate=entry["current_gate"])))
        a.plan.write_text(json.dumps(
            dict(schema=1, board=str(a.board), lines=len(plan),
                 parts=sum(len(p["refs"]) for p in plan), graft=plan),
            indent=1, sort_keys=True, default=str) + "\n")
    if a.worklist:
        with a.worklist.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Bucket", "Refs", "Qty", "Value", "Footprint",
                        "Magnitude", "Tolerance_pct", "Voltage_V",
                        "Dielectric", "Power_W", "Demo_nets", "Note"])
            for bucket, note in (("TUNE_PENDING", "value not final --"
                                  " DEVICE_SPEC s.14 first-article tune"),
                                 ("NO_CANDIDATE", "no reviewed prior in this"
                                  " repository -- needs a new decision")):
                for row in doc[bucket]:
                    s = row["spec"]
                    seen = sorted({n for r in row["refs"]
                                   for n in nets.get(r, [])})
                    mag = s["magnitude"]
                    w.writerow([bucket, " ".join(row["refs"]), row["qty"],
                                row["value"], row["footprint"],
                                ("%.6g" % mag) if mag is not None else
                                "UNREADABLE",
                                s["tolerance"], s["voltage"],
                                s["dielectric"], s["power"],
                                " ".join(seen),
                                note + ("; VALUE STRING NOT UNDERSTOOD: %s"
                                        % s["unparsed"] if s["unparsed"]
                                        or s["kind"] == "OPAQUE" else "")])
    print(json.dumps({k: doc[k] for k in
                      ("assembly_lines", "unsourced_lines", "unsourced_parts",
                       "summary", "graftable", "prior_sources",
                       "unreadable", "no_candidate_prefixes")},
                     indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
