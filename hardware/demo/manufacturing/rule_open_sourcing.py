#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- rule the OPEN purchasing lines against a LIVE record.

D-614 closed 122 of the 247 fitted references by grafting identities this
repository had already audited.  What it could not close is the residue: BOM
lines for which no prior decision exists anywhere in the repo.  D-614's own
next-task note is exact about why it stopped -- **D-096 binds**: a part number
configured from an ordering scheme is a hypothesis until a distributor record
confirms lifecycle and stock, and that session had none to read.

This tool reads one.  `jlc_live.py` fetches and ARCHIVES the record; this
module decides, and it decides the same way the rest of this repository does --
by measuring the CONSEQUENCE rather than pattern-matching a string:

  LAND        the distributor's own package field must equal the land the
              board actually has.  This is the direct `C26` guard (D-613):
              one part number on two land patterns is how that defect happened.
  MAGNITUDE   the record's own Capacitance / Resistance attribute, parsed.
  TOLERANCE   the record's tolerance must be at or inside what the value
              string demands.  Silence in the demand is satisfied by anything.
  DIELECTRIC  ranked, never string-equal, so C0G satisfies an X7R demand and
              X5R does not.  A capacitor whose demand is SILENT still has to
              reach X5R -- the beta-dm audit's own reasoning, written down.
  VOLTAGE     `screen_bom_sourcing.net_gate`, unchanged: 2x the node's
              OPERATING maximum and survival of its ABSOLUTE maximum, using
              the rating READ OFF THE PART.
  POWER       new here, and built in net_gate's image: 2x the operating
              dissipation AND survival of the single-fault dissipation.  A
              line whose dissipation cannot be bounded is REFUSED, not passed.
  BRAND       D-206's lesson: *a loose keyword search returns a plausible
              WRONG part more often than it returns nothing*.  An unrecognised
              vendor is not written into a locked BOM.
  STOCK       D-096's actual demand -- lifecycle and stock, from the record,
              with the date it was read.

    python3 rule_open_sourcing.py [--refresh] [-o REPORT.json] [--plan PLAN.json]

`--refresh` re-reads every query live; without it the archived record is
replayed, so a ruling is reproducible byte for byte.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import screen_bom_sourcing as S            # noqa: E402
from jlc_live import fetch                 # noqa: E402

FIRST_FIVE = 5          # boards in the first build (FIRST_FIVE_ASSEMBLY_PLAN)
STOCK_FACTOR = 10       # ... and the liquidity a line must show beyond it
STOCK_FLOOR = 500

# --------------------------------------------------------------------------
# WHAT THE BOARD ACTUALLY DRAWS THROUGH A RESISTOR.
#
# A land-voltage gate cannot see current, and an over-bound built from node
# voltage (V^2/R with the whole node across the part) is only honest for a
# HIGH-value part.  On 12 ohm it says one watt, which is nonsense, and on R95
# it UNDERSTATES the answer, because the single-fault case puts a reversed
# cell IN SERIES with VBUS and the difference across the part exceeds either
# node's bound.  So the low-value lines carry a number, each one taken from
# this repository's own recorded derivation:
#
#     operating_a   the worst-case current in normal service
#     fault_a       the highest current any single fault can present
#     duty          the fraction of time the current flows, for a part that
#                   is pulsed rather than DC.  1.0 unless stated.
# --------------------------------------------------------------------------
RESISTOR_WORST_CASE = {
    "R24": (0.150, 0.170, 1.0 / 3.0,
            "IR LED current limit, FBV2-S1-007 and the R24 symbol note:"
            " 150 mA first-build peak, 170 mA worst case high (rail +2 %,"
            " VF 1.35 V, R -1 %).  The 38 kHz carrier runs at ONE THIRD duty"
            " (the C12 note derives its ripple from D = 0.333), so the"
            " dissipation is I^2 R D and not I^2 R."),
    "R69": (0.109, 0.109, 1.0,
            "backlight sense.  D-079: the panel is SIX LEDs IN PARALLEL at"
            " I_LED 109 mA typ, and R69 1.87R develops the 0.20 V the"
            " TPS61169 regulates to.  The current is REGULATED, so a shorted"
            " string raises the node voltage and not the current."),
    "R70": (0.02725, 0.03633, 1.0, "one of FOUR parallel 33R backlight"
            " ballasts carrying 109 mA between them (D-079): 27.25 mA each,"
            " and 36.33 mA each if ONE of the four is open."),
    "R95": (0.0089, 0.0166, 1.0,
            "dead-cell recovery limit, P-20 / D-105 and the sheet-01 block-B"
            " text: 8.4 mA nominal at VBUS 5.0 V into a 0 V pack, 7.9-8.9 mA"
            " over 4.75-5.25 V, and a SINGLE-FAULT ceiling into a reversed"
            " cell of 15.9 mA nominal / 16.6 mA worst case.  NOTE: the R95"
            " SYMBOL note says 13.1 mA where the sheet text says 16.6 mA;"
            " the larger number is used."),
    "R125": (0.00103, 0.00132, 1.0,
             "D13 green channel current set, FBV2-S1-008: 1.03 mA nominal,"
             " 1.32 mA high corner."),
    "R126": (0.00167, 0.00217, 1.0,
             "D13 blue channel current set, FBV2-S1-008: 1.67 mA nominal,"
             " 2.17 mA high corner."),
    "R75": (3.33, 3.33, 1.0,
            "battery current sense.  The R75 symbol note states the design's"
            " own ceiling: I_OC,FWD = 50 mV / 15 mR = 3.33 A, the LTC4368-1"
            " forward trip.  Nothing below it is interrupted, so it IS the"
            " continuous current the part must survive."),
}
for _r in ("R71", "R72", "R73"):
    RESISTOR_WORST_CASE[_r] = RESISTOR_WORST_CASE["R70"]

# --------------------------------------------------------------------------
# A PART CLASS, NOT JUST A NUMBER.
#
# `15mR 1% 1W` is satisfied on paper by a thick-film chip at +/-1500 ppm/degC.
# Across -40..+85 degC that part moves 19 % -- on the shunt the fuel gauge and
# the LTC4368 trip point both read.  A current sense is an ALLOY / metal-strip
# part and the tempco is the thing that makes it one.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# WHEN THE SYMBOL'S OWN NOTE ASKS FOR MORE THAN ITS VALUE STRING SAYS.
#
# D-613's `C26` and D-614's four findings are all one failure: reading the
# LINE instead of reading the thing the line describes.  Two of these open
# lines carry a recorded derivation that is STRICTER than the value string a
# BOM exporter sees, and a gate that trusted the string alone would buy a part
# the design has already rejected in writing.
# --------------------------------------------------------------------------
NOTE_TIGHTER = {
    "R24": dict(tolerance=1.0,
                why="the R24 symbol note and the sheet-07 text both read"
                    " `12R 1 percent 0805`, and the 150 mA derivation prices"
                    " the worst-case-high corner at `R -1 %`.  The Value"
                    " string says only `12R`, so a 5 % part satisfies the"
                    " STRING and contradicts the DERIVATION."),
    "C12": dict(dielectric="X7R", voltage=16.0,
                why="the C12 symbol note is explicit: `the requirement is at"
                    " least 15 uF EFFECTIVE at 3.3 V DC bias, which is why the"
                    " part is specified X7R 16 V in 1210 rather than a heavily"
                    " derated 6.3 V 0805`.  The Value string says only `22uF`."),
}

RESISTOR_CLASS = {
    "R75": dict(max_tempco_ppm=100,
                types=("Current Sense Resistor", "Alloy Resistor",
                       "Metal Foil Resistor", "Shunt Resistor"),
                why="R75 is the battery current sense: the LTC4368-1 +/-50 mV"
                    " trip and every current the gauge reports are derived"
                    " from its value.  A +/-1500 ppm/degC thick film moves"
                    " ~19 % over -40..+85 degC and would move the 3.33 A trip"
                    " with temperature; an alloy/current-sense part at"
                    " <=100 ppm/degC moves ~1.3 %."),
}

# --------------------------------------------------------------------------
# D-206, VERBATIM: *a loose keyword search returns a plausible WRONG part more
# often than it returns nothing*.  A distributor catalogue is full of houses
# whose only appearance in this programme would be this line.  The allow-list
# is every passive vendor this repository has ALREADY accepted a part from,
# plus the majors whose chip-passive data is public and auditable.
# --------------------------------------------------------------------------
ACCEPTED_BRANDS = {
    # already accepted in this repository (beta-dm audit / D-206 / D-614)
    "YAGEO", "Samsung Electro-Mechanics", "Murata Electronics", "CCTC",
    "UNI-ROYAL(Uniroyal Elec)", "FH(Guangdong Fenghua)",
    # majors
    "TDK", "Taiyo Yuden", "KEMET", "Vishay Intertech", "VISHAY",
    "PANASONIC", "KOA Speer", "KOA", "Bourns", "ROHM", "Susumu",
    "Walsin Tech Corp", "Kyocera AVX", "AVX", "Viking Tech",
    "Samsung Electro-Mechanics(Samsung)", "Nichicon",
    # current-sense / alloy specialists
    "RALEC", "TA-I Tech", "Ever Ohms Tech", "Uniroyal Elec",
}
BRAND_TIER = {"Murata Electronics": 3, "Samsung Electro-Mechanics": 3,
              "TDK": 3, "Taiyo Yuden": 3, "KEMET": 3, "YAGEO": 3,
              "UNI-ROYAL(Uniroyal Elec)": 2, "Vishay Intertech": 3,
              "PANASONIC": 3, "KOA Speer": 3, "Bourns": 3, "ROHM": 3}

def _fold(name):
    """`FH(Guangdong Fenghua)` and `FH (Guangdong Fenghua Advanced Tech)` are
    one vendor.  The catalogue is not consistent about spacing or about how
    much of the legal name it prints."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


_ACCEPTED_FOLDED = None


def accepted(brand):
    global _ACCEPTED_FOLDED
    if _ACCEPTED_FOLDED is None:
        _ACCEPTED_FOLDED = sorted(_fold(b) for b in ACCEPTED_BRANDS)
    f = _fold(brand)
    return bool(f) and any(f.startswith(a) or a.startswith(f)
                           for a in _ACCEPTED_FOLDED)


RE_NUM = re.compile(r"(-?\d+(?:\.\d+)?)")
OHM = {"": 1.0, "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
FARAD = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "": 1.0}
WATT = {"m": 1e-3, "": 1.0, "u": 1e-6, "µ": 1e-6}


def _num(text):
    m = RE_NUM.search(text or "")
    return float(m.group(1)) if m else None


def _scaled(text, table):
    """`2.2kΩ` -> 2200.0, `100mW` -> 0.1, `22uF` -> 2.2e-5."""
    if not text or text.strip() in ("-", ""):
        return None
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*([pnumµkKMG]?)", text)
    if not m:
        return None
    return float(m.group(1)) * table.get(m.group(2), 1.0)


def decode(rec):
    """The live record read as a PART, with nothing inferred from its name."""
    at = {a["attribute_name_en"]: a["attribute_value_name"]
          for a in (rec.get("attributes") or [])}
    out = dict(code=rec.get("componentCode"), mpn=rec.get("componentModelEn"),
               brand=(rec.get("componentBrandEn") or "").strip(),
               library=rec.get("componentLibraryType"),
               stock=rec.get("stockCount") or 0,
               land=(rec.get("componentSpecificationEn") or "").strip(),
               rohs=rec.get("rohsFlag"), buyable=rec.get("isBuyComponent"),
               no_buy=rec.get("noBuyReason"),
               datasheet=rec.get("dataManualUrl"),
               attributes=at, kind=None, magnitude=None, voltage=None,
               tolerance=None, dielectric=None, power=None, tempco_ppm=None,
               rtype=at.get("Type"))
    prices = rec.get("componentPrices") or []
    out["price_1"] = next((p["productPrice"] for p in prices
                           if p.get("startNumber") == 1), None)
    if at.get("Capacitance"):
        out["kind"] = "C"
        out["magnitude"] = _scaled(at["Capacitance"], FARAD)
        out["voltage"] = _num(at.get("Voltage Rating"))
        d = (at.get("Temperature Coefficient") or "").upper().strip()
        out["dielectric"] = d if d in S.DIELECTRICS else None
    elif at.get("Resistance"):
        out["kind"] = "R"
        out["magnitude"] = _scaled(at["Resistance"], OHM)
        out["power"] = _scaled(at.get("Power(Watts)"), WATT)
        out["voltage"] = None
        out["working_v"] = _num(at.get("Voltage-Supply(Max)")
                                or at.get("Voltage Rating"))
        tc = at.get("Temperature Coefficient") or ""
        nums = [abs(float(x)) for x in RE_NUM.findall(tc)] if "ppm" in tc else []
        out["tempco_ppm"] = max(nums) if nums else None
    tol = at.get("Tolerance")
    if tol and "%" in tol:
        out["tolerance"] = abs(_num(tol) or 0.0)
    return out


def power_gate(refs, demand, part):
    """`net_gate` in the current domain: 2x operating AND survives fault."""
    if demand["kind"] != "R":
        return dict(ok=True, kind="not a resistor")
    r = demand["magnitude"]
    rating = part.get("power")
    if rating is None:
        return dict(ok=False, kind="dissipation",
                    reason="the record states no power rating")
    if r == 0.0:
        return dict(ok=True, kind="zero-ohm link -- current_gate owns this")

    ruled = [RESISTOR_WORST_CASE[x] for x in refs if x in RESISTOR_WORST_CASE]
    if ruled:
        if len(ruled) != len(refs):
            return dict(ok=False, kind="dissipation", reason=(
                "a ruling exists for some of %s but not all" % ", ".join(refs)))
        op = max(x[0] for x in ruled)
        flt = max(x[1] for x in ruled)
        duty = max(x[2] for x in ruled)
        p_op, p_flt = op * op * r * duty, flt * flt * r * duty
        return dict(ok=(rating >= 2 * p_op and rating >= p_flt),
                    kind="2x operating and survives single fault",
                    basis="current ruling", rating_w=rating,
                    operating_a=op, fault_a=flt, duty=duty,
                    operating_w=round(p_op, 6), fault_w=round(p_flt, 6),
                    margin_x=round(rating / p_op, 2) if p_op else None,
                    ruling=sorted({x[3] for x in ruled}))

    # No ruling.  The caller falls back to the strict over-bound, which is
    # only honest when EVERY node the part touches is established.
    return dict(ok=None, kind="dissipation", basis="over-bound pending")


def over_bound(refs, nets, r):
    """Highest DC the board can put ACROSS a part, and the P it implies."""
    unknown, absolute = [], 0.0
    for ref in refs:
        for name in nets.get(ref, []):
            if name in S.NET_MAX_DC:
                absolute = max(absolute, S.NET_MAX_DC[name][1])
            else:
                unknown.append("%s on %s" % (ref, name))
    if unknown:
        return None, sorted(set(unknown))
    return (absolute * absolute / r if r else 0.0), []


def keywords(demand, land):
    """Every way this repository knows to ASK for the part."""
    size = S.land_size(land) or ""
    mag = demand["magnitude"]
    out = []
    if demand["kind"] == "R":
        if mag >= 1e6:
            v = "%gM" % (mag / 1e6)
        elif mag >= 1e3:
            v = "%gK" % (mag / 1e3)
        elif mag >= 1:
            v = "%gR" % mag
        else:
            v = "%gR" % mag
        out.append("%s %s resistor" % (v, size))
        # UNI-ROYAL's 1 % chip family is JLCPCB BASIC across most of E96 and
        # this repository already decodes it (`0603WAF...T5E`).  A code built
        # from the ordering scheme is a HYPOTHESIS (D-096); asking for it by
        # name is how the hypothesis gets confirmed or dropped.
        for dec in range(-2, 8):
            scaled = mag / (10 ** dec)
            if 100 <= round(scaled) < 1000:
                out.append("%sWAF%03d%dT5E" % (size, round(scaled), dec))
                break
    else:
        if mag >= 1e-6:
            v = "%guF" % (mag * 1e6)
        elif mag >= 1e-9:
            v = "%gnF" % (mag * 1e9)
        else:
            v = "%gpF" % (mag * 1e12)
        die = demand["dielectric"] or ""
        out.append(("%s %s %s capacitor" % (v, size, die)).replace("  ", " "))
        if die:
            out.append("%s %s capacitor" % (v, size))
        for brand in ("Murata", "Samsung", "YAGEO", "TDK"):
            out.append("%s %s %s %s" % (v, size, die, brand))
    return out


def rank(cand):
    part = cand["part"]
    tier = next((v for k, v in BRAND_TIER.items()
                 if _fold(k) == _fold(part["brand"])), 1)
    # Below the comfort floor, STOCK decides -- a thin line is a schedule risk
    # and 91 pieces beat 51 whoever made them.  Above it, stock stops mattering
    # and the maker does.
    return (0 if part["library"] == "base" else 1,
            -min(part["stock"], STOCK_FLOOR),
            -tier,
            -(cand.get("margin") or 0),
            -min(part["stock"], 10 ** 7))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, default=S.PACKAGE)
    ap.add_argument("--board", type=Path, default=S.BOARD)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--include-tune", action="store_true",
                    help="also rule the DEVICE_SPEC s.14 TUNE lines at their"
                         " FIRST-ARTICLE value -- see the note in the source")
    a = ap.parse_args()

    bom = S.rows(a.package / "aqroot-Demo-BOM-assembly.csv")
    if not bom:
        raise SystemExit("no assembly BOM -- run export_fab_package.py")
    nets = S.board_nets(a.board)

    ruled, refused, tune, queries = [], [], [], []
    for row in bom:
        if row.get("MPN", "").strip() or row.get("LCSC", "").strip():
            continue
        value, land = row["Value"].strip(), S.leaf(row["Footprint"])
        refs = [r for r in row["Refs"].split(",") if r]
        demand = S.parse_spec(value, land)
        line = dict(refs=refs, qty=len(refs), value=value, footprint=land,
                    spec=demand,
                    demo_nets=sorted({n for r in refs for n in nets.get(r, [])}))
        if demand["tune"] and not a.include_tune:
            tune.append(dict(line, why="DEVICE_SPEC s.14 -- the VALUE is not"
                                       " final; no part number can close it"))
            continue
        if demand["kind"] == "OPAQUE" or demand["unparsed"]:
            refused.append(dict(line, refused="value string not understood:"
                                              " %s" % demand["unparsed"]))
            continue

        size = S.land_size(land)
        need = len(refs) * FIRST_FIVE
        floor = max(need * STOCK_FACTOR, STOCK_FLOOR)
        seen, offers = {}, []
        for kw in keywords(demand, land):
            doc = fetch(kw, pages=a.pages, refresh=a.refresh, quiet=True)
            queries.append(dict(line=value + " | " + land, keyword=kw,
                                fetched_utc=doc["fetched_utc"],
                                returned=doc["returned"]))
            for rec in doc["records"]:
                if rec["componentCode"] in seen:
                    continue
                seen[rec["componentCode"]] = True
                part = decode(rec)
                why = []
                if part["kind"] != demand["kind"]:
                    continue
                if part["land"] != size:
                    continue
                if not S.same_magnitude(part["magnitude"], demand["magnitude"]):
                    continue
                # Past this point the part IS the right value on the right
                # land, so every remaining refusal is worth reading.
                if not accepted(part["brand"]):
                    why.append("vendor %r is not on the accepted list (D-206)"
                               % part["brand"])
                tight = next((NOTE_TIGHTER[r] for r in refs
                              if r in NOTE_TIGHTER), {})
                want_tol = min([x for x in (demand["tolerance"],
                                            tight.get("tolerance"))
                                if x is not None], default=None)
                if want_tol is not None and (
                        part["tolerance"] is None
                        or part["tolerance"] > want_tol + 1e-9):
                    why.append("tolerance %s vs the demanded %s%%"
                               % (part["tolerance"], want_tol))
                if demand["kind"] == "C":
                    want = (tight.get("dielectric") or demand["dielectric"]
                            or "X5R")
                    floor_v = tight.get("voltage")
                    if floor_v and (part["voltage"] or 0) < floor_v:
                        why.append("rating %s V under the %s V the symbol note"
                                   " requires" % (part["voltage"], floor_v))
                    have = part["dielectric"]
                    if (have is None
                            or S.DIELECTRIC_RANK[have] < S.DIELECTRIC_RANK[want]):
                        why.append("dielectric %s does not reach %s"
                                   % (have, want))
                if demand["tune"]:
                    # THE NFC TANK NODE VOLTAGE IS NOT ESTABLISHED HERE, and
                    # inventing one to feed a derating rule would be worse than
                    # saying so.  What IS established is the sheet's own
                    # ruling -- these lines are specified 50 V C0G -- so the
                    # gate is the value string's stated rating, and the
                    # unestablished node is carried as an open item rather
                    # than silently derated against a made-up number.
                    nv = dict(ok=(demand["voltage"] is None
                                  or (part["voltage"] or 0)
                                  >= demand["voltage"]),
                              kind="the value string's own stated rating",
                              basis="DEVICE_SPEC s.14 -- the ST25R3916 tank"
                                    " node voltage is NOT established in this"
                                    " repository; the sheet's own 50 V C0G"
                                    " specification is the ruling this gate"
                                    " enforces",
                              demanded_v=demand["voltage"],
                              rating_v=part["voltage"],
                              node_voltage_established=False)
                else:
                    nv = S.net_gate(refs, nets, part["voltage"], land)
                if not nv["ok"]:
                    why.append("node voltage gate: %s"
                               % nv.get("reason", "refused"))
                pw = power_gate(refs, demand, part)
                if demand["tune"] and pw.get("ok") is None:
                    # Same honesty as the voltage limb.  The ST25R3916 tank
                    # current is not established in this repository, so no
                    # dissipation number can be asserted; the ranker is left
                    # to take the HIGHEST-RATED part that fits the land, and
                    # the measurement is carried as an open item.
                    pw = dict(ok=part["power"] is not None,
                              kind="not established -- first-article"
                                   " measurement",
                              basis="DEVICE_SPEC s.14: the NFC tank current is"
                                    " NOT established here, so this line takes"
                                    " the highest-rated part its land offers"
                                    " and the dissipation is measured on the"
                                    " first article",
                              rating_w=part["power"])
                if pw.get("ok") is None:
                    bound, unknown = over_bound(refs, nets, demand["magnitude"])
                    if bound is None:
                        pw = dict(ok=False, kind="dissipation", basis=
                                  "over-bound", reason="node voltage not"
                                  " established", unresolved=unknown)
                    else:
                        pw = dict(ok=(part["power"] or 0) >= 2 * bound,
                                  kind="2x the strict over-bound",
                                  basis="over-bound: the whole node voltage"
                                        " across the part",
                                  rating_w=part["power"],
                                  over_bound_w=round(bound, 6),
                                  margin_x=(round(part["power"] / bound, 2)
                                            if bound and part["power"] else None))
                if not pw["ok"]:
                    why.append("dissipation gate: %s"
                               % (pw.get("reason") or
                                  "rating %s W against %s W"
                                  % (pw.get("rating_w"),
                                     pw.get("operating_w")
                                     or pw.get("over_bound_w"))))
                klass = next((RESISTOR_CLASS[r] for r in refs
                              if r in RESISTOR_CLASS), None)
                if klass:
                    if part.get("tempco_ppm") is None or \
                            part["tempco_ppm"] > klass["max_tempco_ppm"]:
                        why.append("tempco %s ppm/degC against a %s ppm limit"
                                   % (part.get("tempco_ppm"),
                                      klass["max_tempco_ppm"]))
                    if part.get("rtype") not in klass["types"]:
                        why.append("part type %r is not a current-sense class"
                                   % part.get("rtype"))
                # Two limbs, because they are two different questions.  The
                # HARD one is whether the first build can be bought at all.
                # The comfort floor is a PURCHASING judgement, so it is
                # flagged and carried, never used to refuse a part that has
                # ten times what the build needs.
                if part["stock"] < need * STOCK_FACTOR:
                    why.append("stock %s under %s -- %s parts x %s boards x %s"
                               " liquidity" % (part["stock"],
                                               need * STOCK_FACTOR, len(refs),
                                               FIRST_FIVE, STOCK_FACTOR))
                thin = part["stock"] < STOCK_FLOOR
                if str(part["rohs"]) != "1":
                    why.append("not flagged RoHS")
                # `noBuyReason` is where the catalogue states LIFECYCLE --
                # "This product is no longer manufactured." -- which is half
                # of exactly what D-096 asks to see.
                if str(part["buyable"]) != "1":
                    why.append("JLCPCB will not sell it: %s"
                               % (part["no_buy"] or "isBuyComponent != 1"))
                margin = None
                if demand["kind"] == "C" and part["voltage"]:
                    margin = part["voltage"]
                elif part.get("power"):
                    margin = part["power"] * 1000
                offers.append(dict(part=part, refused=why, ok=not why,
                                   margin=margin, net_gate=nv, power_gate=pw,
                                   thin_stock=thin))

        usable = sorted([o for o in offers if o["ok"]], key=rank)
        entry = dict(line, candidates_examined=len(offers),
                     stock_floor=floor,
                     nearest=[dict(mpn=o["part"]["mpn"], lcsc=o["part"]["code"],
                                   brand=o["part"]["brand"],
                                   refused=o["refused"])
                              for o in offers[:6]])
        if not usable:
            refused.append(dict(entry, refused=(
                "no candidate on this land survived every gate"
                if offers else "no candidate of the right value on this land")))
            continue
        pick = usable[0]
        ruled.append(dict(entry, chosen=pick["part"], net_gate=pick["net_gate"],
                          power_gate=pick["power_gate"],
                          thin_stock=pick["thin_stock"],
                          note_tighter=next((NOTE_TIGHTER[r] for r in refs
                                             if r in NOTE_TIGHTER), None),
                          runners_up=[dict(mpn=o["part"]["mpn"],
                                           lcsc=o["part"]["code"],
                                           library=o["part"]["library"],
                                           stock=o["part"]["stock"])
                                      for o in usable[1:4]]))

    def parts(bucket):
        return sum(r["qty"] for r in bucket)

    doc = dict(schema=1, package=str(a.package), board=str(a.board),
               first_five_boards=FIRST_FIVE, stock_factor=STOCK_FACTOR,
               stock_floor=STOCK_FLOOR,
               summary={"RULED": dict(lines=len(ruled), parts=parts(ruled)),
                        "REFUSED": dict(lines=len(refused),
                                        parts=parts(refused)),
                        "TUNE_PENDING": dict(lines=len(tune),
                                             parts=parts(tune))},
               jlc_basic=sum(1 for r in ruled
                             if r["chosen"]["library"] == "base"),
               thin_stock_lines=sorted(" ".join(r["refs"]) for r in ruled
                                       if r["thin_stock"]),
               brands=dict(Counter(r["chosen"]["brand"] for r in ruled)),
               queries=queries, RULED=ruled, REFUSED=refused,
               TUNE_PENDING=tune)
    text = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        a.out.write_text(text)
    if a.plan:
        graft = []
        for e in ruled:
            p = e["chosen"]
            graft.append(dict(
                refs=e["refs"], value=e["value"], footprint=e["footprint"],
                how=("FIRST_ARTICLE_VALUE" if e["spec"]["tune"]
                     else "LIVE_RECORD"),
                Manufacturer=p["brand"], MPN=p["mpn"],
                LCSC=p["code"],
                note=(("FIRST-ARTICLE VALUE ONLY -- DEVICE_SPEC s.14 requires"
                       " this position to be RE-TUNED against a VNA and the"
                       " ST tool with the board in hand, so this part number"
                       " buys the first article and is EXPECTED TO CHANGE. "
                       if e["spec"]["tune"] else "")
                      + "SOURCING D-615 LIVE_RECORD. JLCPCB record read %s:"
                      " %s library, stock %s, land %s, %s. Gates: %s; %s."
                      % (next((q["fetched_utc"] for q in queries), "?"),
                         p["library"], p["stock"], p["land"],
                         "; ".join("%s %s" % (k, v) for k, v in
                                   sorted(p["attributes"].items())),
                         e["net_gate"]["kind"], e["power_gate"]["kind"])),
                basis=dict(source="JLCPCB-LIVE", prior_value=e["value"],
                           verdict="RULED", manufacturer_basis=
                           "the distributor record's own brand field",
                           part_rating_v=p["voltage"],
                           part_dielectric=p["dielectric"],
                           part_tolerance=p["tolerance"],
                           part_power_w=p["power"],
                           stock=p["stock"], library=p["library"],
                           net_gate=e["net_gate"],
                           power_gate=e["power_gate"], ruling=[])))
        a.plan.write_text(json.dumps(
            dict(schema=1, decision="D-615", board=str(a.board),
                 lines=len(graft),
                 parts=sum(len(g["refs"]) for g in graft), graft=graft),
            indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: doc[k] for k in
                      ("summary", "jlc_basic", "brands")},
                     indent=1, sort_keys=True))
    for e in ruled:
        p = e["chosen"]
        print("  RULED   %-28s %-7s %-11s %-24s %-26s stock=%s"
              % (" ".join(e["refs"])[:28], p["library"], p["code"],
                 p["brand"][:24], (p["mpn"] or "")[:26], p["stock"]))
    for e in refused:
        print("  REFUSED %-28s %s" % (" ".join(e["refs"])[:28], e["refused"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
