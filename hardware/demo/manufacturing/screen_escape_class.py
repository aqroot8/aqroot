#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: "UNLAUNCHABLE" is THREE walls wearing one name.

Every escape refusal this board has recorded arrives as one sentence -- `NO
LEGAL ESCAPE at >= W mm` -- and every one of them has been read as the same
kind of fact.  They are not the same kind of fact, and the arithmetic that
tells them apart has been sitting in `screen_land_escape_margin.py` since D-620
without ever being asked the question.

That screen already reports TWO numbers per land: the MARGIN at the width the
net's contract asks for, and the WIDEST track the land can physically launch.
D-626's `no_lattice_at_any_pitch` reads only the first, collapses `margin < 0`
and `margin == 0` into one predicate, and hands both to the same prose --
"land licence, placement or route_local_two_pad".  That prose is true and it is
not actionable: it names three instruments and never says which.  D-629's
ladder then spent seven rungs and 295.8 M cells on `/BQ25185_STAT1`'s `U11.9`
learning by hand what the second number says for free.

READ BOTH NUMBERS AND THE ONE WALL BECOMES FOUR CLASSES, EACH WITH ITS OWN
INSTRUMENT:

    margin > 0                       CLEAR.  Not a land wall at all; if the
                                     router still refuses, the blocker is
                                     ROUTED COPPER and the answer is eviction,
                                     a corridor or placement (D-621 reached
                                     this conclusion for `NFC_VDD_RF` by hand).

    margin == 0                      LATTICE_EXACT.  KiCad's DRC passes this
                                     land -- the promoted `NFC_RFO1`/`RFO2`
                                     arms are this case -- but `maze3d`
                                     rasterises with a 0.75-cell guard band on
                                     top of the clearance, so at EVERY pitch
                                     the required figure strictly exceeds the
                                     available one.  No ladder will ever
                                     propose it.  `route_local_two_pad` works
                                     in exact geometry and is the ONLY
                                     instrument.  Laddering it is provably
                                     wasted search.

    margin < 0, widest >= licensed   WIDTH_NECKABLE.  The land cannot launch
    neck, land inside a courtyard    its contract width and CAN launch copper
    the board's own necking rule     this board already licenses by name.  The
    names                            instrument is a WIDTH licence -- `--neck`
                                     where the confined courtyard search can
                                     reach a full-width goal cell, and the
                                     D-610 `PAD_ESCAPE_RUN_<REF>_<PIN>` /
                                     `enclosedByArea` rectangle where it
                                     cannot.  NOT a finer pitch.

    margin < 0, widest >= board      WIDTH_UNLICENSED.  Same geometry, but the
    min_track_width, no courtyard    board has never granted this footprint a
    licence                          necking allowance.  The instrument is a
                                     DRU edit authored BEFORE the router runs.

    widest < board min_track_width   TRUE_WALL.  No copper this board can
                                     fabricate leaves this land.  Placement,
                                     or a different part.  There is nothing to
                                     route and nothing to license.

AND EVERY WIDTH VERDICT IS PRICED IN AMPERES, BECAUSE A NARROW ESCAPE IS A
CURRENT DECISION WEARING A CONNECTIVITY DECISION'S CLOTHES.  D-610 promoted a
0.200 mm neck on `U12.4` carrying the WHOLE `+3V3` rail and ruled on it in
amperes, in prose, once; D-628 made the same arithmetic a CONTRACT for pour
severance.  This screen spends it a third time and by reusing both files
unchanged: `audit_bond_ampacity.ampacity` for IPC-2221B at this board's own
copper, and `pour_partition_contract.published_rail_currents` for the design
current `.kicad_dru` section 5 publishes for that net's class.  A class the
table does not price is reported `NET_CARRIES_NO_PUBLISHED_CURRENT` and
REFUSED, exactly as `PP2` refuses one -- which is how `/01_POWER_TREE/ACC_5V_LX`
stops being a routing question: `SWITCH_NODE` carries the `U21` boost
inductor's 2.19 A peak and its widest legal escape is 0.250 mm, or 0.872 A.

AND THE CONTRACT WIDTH IS COMPARED WITH THE FLOOR THE DRU ACTUALLY PUBLISHES,
because that gap is a documented defect class on this board and not a
hypothesis.  `route_maze_batch.DRU_CLASS` carries a `width_cap` for exactly one
class, `NFC_RF`, with the reason written out at length: the netclass in the
`.kicad_pcb` asks for the DRU's `opt` figure, `net_contract` takes `max()` of
the two, "and `max()` made this class UNLAUNCHABLE FROM THE PART IT SERVES".
`U9` is a UFQFPN-32 at 0.500 mm pitch and it hosts more than one class.  This
screen prints `contract_mm`, `dru_floor_mm` and `widest_mm` side by side for
every open net, so a class routed at its `opt` when its `min` would launch is
visible without anyone having to remember that `NFC_RF` once was.

SOUND ON THE EXCLUSION SIDE, AND THAT IS THE SIDE THAT MATTERS.  The obstacles
this measures are PADS -- the land pattern's own arithmetic, a property of the
PACKAGE that does not move when copper moves.  A `CLEAR` verdict therefore says
"this package can launch this width", never "this net will route today", and
the classes above are about what is BUILDABLE, not about what is currently free.

Read-only.  Writes JSON; changes nothing.

    python3 screen_escape_class.py [--board B] [--net N] [-o OUT]
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "checks"))

import maze3d as mz
import audit_bond_ampacity as ab
from pour_partition_contract import published_rail_currents, decide, DT_K
from route_maze_batch import BOARD, DRU_CLASS
from routing_ledger import generate as ledger_build
from screen_land_escape_margin import screen as margin_screen

NM = 1e6
AMP_TOL = 1e-9                  # the tolerance `PP2.decide` itself uses


def classify(margin_mm, widest_mm, in_courtyard, neck_mm, board_min_mm):
    """The verdict, in ONE place, so the controls drive what the report does.

    `widest_mm` is None when no direction admits any track at all.
    """
    if margin_mm is None:
        return "UNMEASURED", "no margin was measured for this land"
    if margin_mm > 0:
        return "CLEAR", ("this package can launch the contract width; a router "
                         "refusal here is ROUTED COPPER, not the land")
    if margin_mm == 0:
        return "LATTICE_EXACT", ("DRC-legal and rasterisable at NO pitch -- "
                                 "maze3d's 0.75-cell guard band strictly "
                                 "exceeds the room at every lattice; "
                                 "route_local_two_pad is the only instrument")
    w = 0.0 if widest_mm is None else widest_mm
    if w < board_min_mm:
        return "TRUE_WALL", ("widest legal escape %.4f mm is below this board's "
                             "own min_track_width %.3f mm -- no copper it can "
                             "fabricate leaves this land" % (w, board_min_mm))
    if neck_mm is not None and in_courtyard and w + 1e-9 >= neck_mm:
        return "WIDTH_NECKABLE", ("cannot launch the contract width, CAN launch "
                                  "%.4f mm >= the %.3f mm this board's own "
                                  ".kicad_dru licenses inside this courtyard"
                                  % (w, neck_mm))
    return "WIDTH_UNLICENSED", ("cannot launch the contract width, CAN launch "
                                "%.4f mm >= min_track_width %.3f mm, but this "
                                "land holds no necking licence"
                                % (w, board_min_mm))


def price(width_mm, required_amps):
    """IPC-2221B at this board's copper, judged the way `PP2` judges a bond."""
    if width_mm is None or width_mm <= 0:
        return None, False, "NO_CONDUCTOR_TO_PRICE"
    amps = round(ab.ampacity(ab.track_area(width_mm), DT_K), 3)
    ok, why = decide("BONDED", amps, required_amps)
    return amps, ok, why


def dru_class_width_rules(dru_path):
    """Every `track_width (min ...)` the `.kicad_dru` enforces per NETCLASS.

    The lever `--escape-floor` descends to is `DRU_CLASS`, a table in
    `route_maze_batch.py`.  A table is a transcription, and a transcription can
    drift from the file it transcribes -- which on this board would mean a
    router proposing copper its own DRC refuses.  So the rule text is parsed
    and the two are COMPARED, and the comparison is a control rather than a
    note.  Only `A.hasNetclass('X')` conditions are read; a rule with any other
    term is ignored rather than guessed at.
    """
    import re
    try:
        txt = Path(dru_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out = {}
    q = "'"                     # the `.kicad_dru` quotes class names this way
    pat = re.compile(
        r'\(rule\s+"[^"]*"\s*(?:\(layer\s+[^)]*\)\s*)?'
        r'\(constraint\s+track_width\s*\(min\s+([0-9.]+)mm\)'
        r'(?:\s*\(opt\s+([0-9.]+)mm\))?\s*\)\s*'
        r'\(condition\s+"A\.hasNetclass\(' + q + r'([A-Z0-9_]+)' + q +
        r'\)"\)', re.S)
    for mn, opt, cls in pat.findall(txt):
        mm = float(mn)
        if cls not in out or mm < out[cls]["min_mm"]:
            out[cls] = dict(min_mm=mm, opt_mm=(float(opt) if opt else None))
    return out


def floor_controls(dru_rules):
    """The floor this lever uses is never below what the board's DRC enforces.

    `--escape-floor` can only ever be as good as `DRU_CLASS`, so the one thing
    that must be checked before it is trusted is that `DRU_CLASS` does not
    undercut the `.kicad_dru`.  Each class is checked in the direction that
    matters: the table may be STRICTER than the rule and may never be looser.
    """
    rows, ok_all = [], True
    for cls, ov in sorted(DRU_CLASS.items()):
        w = ov.get("width")
        if w is None:
            continue                       # unpriced: the lever does not move
        rule = dru_rules.get(cls)
        if rule is None:
            rows.append(dict(netclass=cls, table_mm=w / NM, rule_mm=None,
                             ok=True,
                             why="no per-class track_width rule; the table is "
                                 "the only floor and cannot undercut one"))
            continue
        good = w / NM + 1e-9 >= rule["min_mm"]
        ok_all &= good
        rows.append(dict(netclass=cls, table_mm=w / NM,
                         rule_mm=rule["min_mm"], rule_opt_mm=rule["opt_mm"],
                         ok=good,
                         why=("table floor is at or above the rule KiCad "
                              "enforces" if good else
                              "TABLE UNDERCUTS THE DRC RULE -- the lever would "
                              "propose copper the board refuses")))
    return ok_all, rows


def controls(neck_mm, board_min_mm):
    """Non-vacuity: this screen must not be able to call everything a neck.

    Every probe drives the SAME `classify()` / `price()` the verdict does, so a
    control that misbehaves is a report that misbehaves.
    """
    cases = [
        # (name, margin, widest, in_courtyard, expected)
        ("positive_margin_is_not_a_wall", 0.25, 1.0, True, "CLEAR"),
        ("zero_margin_is_never_a_neck", 0.0, 1.0, True, "LATTICE_EXACT"),
        ("nothing_launchable_is_a_true_wall", -0.2, 0.0, True, "TRUE_WALL"),
        ("below_board_minimum_is_a_true_wall", -0.2, board_min_mm / 2.0, True,
         "TRUE_WALL"),
        ("neckable_only_inside_a_named_courtyard", -0.2, neck_mm, False,
         "WIDTH_UNLICENSED"),
        ("neckable_inside_a_named_courtyard", -0.2, neck_mm, True,
         "WIDTH_NECKABLE"),
        ("just_under_the_licensed_neck_is_unlicensed", -0.2,
         neck_mm - 0.001, True, "WIDTH_UNLICENSED"),
    ]
    rows, ok_all = [], True
    for name, m, w, cy, want in cases:
        got, _ = classify(m, w, cy, neck_mm, board_min_mm)
        rows.append(dict(control=name, margin_mm=m, widest_mm=w,
                         in_courtyard=cy, expected=want, got=got,
                         ok=(got == want)))
        ok_all &= (got == want)
    # THE PRICE BAR SITS EXACTLY WHERE IT CLAIMS.  The discriminating step is
    # ONE MILLIAMP and not one part per million, because `price()` rounds to
    # 3 dp before it compares -- the same rounding `PP2`'s `bond_price` applies
    # so that a report prints the figure the decision used.  Probing a
    # part-per-million perturbation would test the ROUNDING and call it the
    # bar; this probes the bar, and names the quantum it probes it at.
    bar = 1.0
    exact_w = (bar / (0.048 * DT_K ** 0.44)) ** (1.0 / 0.725) * 0.00064516 / ab.OZ_MM
    a_at, ok_at, _ = price(exact_w, bar)
    w_un = exact_w
    while price(w_un, bar)[0] >= bar:
        w_un *= 0.999
    a_un, ok_un, why_un = price(w_un, bar)
    rows.append(dict(control="priced_at_the_bar_is_admitted", amps=a_at,
                     required=bar, expected=True, got=ok_at, ok=ok_at))
    rows.append(dict(control="one_rounding_quantum_below_the_bar_is_refused",
                     amps=a_un, required=bar, width_mm=round(w_un, 6),
                     quantum_a=0.001, expected=False, got=ok_un, why=why_un,
                     ok=(not ok_un)))
    ok_all &= ok_at and not ok_un
    # AND A CLASS THE TABLE DOES NOT PRICE IS REFUSED, NOT GUESSED.
    _, ok_np, why_np = price(1.0, None)
    rows.append(dict(control="unpriced_class_is_refused", expected=False,
                     got=ok_np, why=why_np, ok=(not ok_np)))
    ok_all &= not ok_np
    return ok_all, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=str(BOARD))
    ap.add_argument("--net", action="append", default=[],
                    help="restrict to these nets; default is every OPEN net")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()

    board = Path(a.board)
    dru = board.with_suffix(".kicad_dru")
    table, prov = published_rail_currents(dru)

    qb = mz.qr.QBoard(str(board))
    neck = mz.neck_rule(qb)
    neck_mm = None if neck is None else neck.min_w / NM
    board_min_mm = qb.b.GetDesignSettings().m_TrackMinWidth / NM
    pad_xy = {}
    for fp in qb.b.GetFootprints():
        for p in fp.Pads():
            c = p.GetPosition()
            pad_xy["%s.%s" % (fp.GetReference(), p.GetNumber())] = (c.x, c.y)

    led = ledger_build(board)
    open_nets = [e for e in led["nets"] if e["open_edges"] > 0]
    if a.net:
        want = set(a.net)
        open_nets = [e for e in open_nets if e["net"] in want]
    open_nets.sort(key=lambda e: (-e["open_edges"], e["net"]))

    nets_out, lands_out = [], []
    for e in open_nets:
        doc = margin_screen(board, [e["net"]], set())
        cls = doc["pads"][0]["netclass"] if doc["pads"] else None
        contract_mm = doc["pads"][0]["width_mm"] if doc["pads"] else None
        floor_nm = DRU_CLASS.get(cls, {}).get("width")
        required = (table.get(cls) or {}).get("amps")
        rows = []
        for r in doc["pads"]:
            widest = max((d["widest_mm"] or 0.0)
                         for d in r["directions"].values()) or None
            xy = pad_xy.get(r["pad"])
            inside = bool(neck is not None and xy is not None
                          and neck.contains(xy[0], xy[1]))
            verdict, why = classify(r["best_margin_mm"], widest, inside,
                                    neck_mm, board_min_mm)
            row = dict(pad=r["pad"], net=e["net"], netclass=cls,
                       contract_mm=r["width_mm"],
                       best_margin_mm=r["best_margin_mm"],
                       widest_mm=widest, in_licensed_courtyard=inside,
                       licensed_neck_mm=neck_mm, verdict=verdict, why=why)
            if verdict in ("WIDTH_NECKABLE", "WIDTH_UNLICENSED"):
                # PRICE BOTH CONDUCTORS A LICENCE COULD ACTUALLY BUY: the
                # widest the land admits, and the narrowest the board licenses.
                for key, w in (("at_widest", widest),
                               ("at_licensed_neck",
                                neck_mm if verdict == "WIDTH_NECKABLE" else None)):
                    if w is None:
                        continue
                    amps, ok, pw = price(w, required)
                    row["price_%s" % key] = dict(
                        width_mm=round(w, 4), amps=amps,
                        required_amps=required, admitted=ok, why=pw)
            rows.append(row)
            lands_out.append(row)
        counts = {}
        for r in rows:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        nets_out.append(dict(
            net=e["net"], sheet=e["sheet"], netclass=cls,
            open_edges=e["open_edges"], pads=e["pads"],
            contract_mm=contract_mm,
            dru_floor_mm=(None if floor_nm is None else floor_nm / NM),
            # THE `opt`-vs-`min` GAP, STATED RATHER THAN REMEMBERED.
            routed_above_dru_floor=bool(
                floor_nm is not None and contract_mm is not None
                and contract_mm > floor_nm / NM + 1e-9),
            published_amps=required,
            verdicts=counts,
            blocked_lands=[r["pad"] for r in rows
                           if r["verdict"] not in ("CLEAR",)]))

    ctl_ok, ctl_rows = controls(neck_mm or 0.2, board_min_mm)
    dru_rules = dru_class_width_rules(dru)
    floor_ok, floor_rows = floor_controls(dru_rules)
    ctl_ok = ctl_ok and floor_ok
    summary = {}
    for r in lands_out:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1

    out = dict(
        schema=1, board=str(board),
        board_sha256=led.get("board_sha256"),
        what="D-630 -- every open net's lands, classified by WHICH instrument "
             "answers them.  `no_lattice_at_any_pitch` collapses margin<0 and "
             "margin==0 into one predicate and hands both to prose naming "
             "three instruments; reading the WIDEST legal escape beside the "
             "margin separates them, and every width verdict is PRICED in "
             "amperes against .kicad_dru section 5 the way PP2 prices a bond.",
        licensed_neck_mm=neck_mm,
        licensed_courtyards=(None if neck is None else sorted(neck.refs)),
        board_min_track_mm=board_min_mm,
        published_currents=prov,
        controls_ok=ctl_ok, controls=ctl_rows,
        dru_class_width_rules=dru_rules,
        escape_floor_controls_ok=floor_ok, escape_floor_controls=floor_rows,
        land_verdicts=summary,
        open_nets=len(nets_out),
        open_edges=sum(n["open_edges"] for n in nets_out),
        nets=nets_out, lands=lands_out)
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

    print("controls: %s (%d classification/price probes, %d escape-floor "
          "probes)" % ("PASS" if ctl_ok else "FAIL", len(ctl_rows),
                       len(floor_rows)))
    print("licensed neck %.3f mm inside %s; board min track %.3f mm\n"
          % (neck_mm or 0.0, ",".join(sorted(neck.refs)) if neck else "-",
             board_min_mm))
    print("%-10s %-34s %-11s %-6s %-8s %-7s %-17s %s"
          % ("pad", "net", "class", "contr", "margin", "widest", "verdict",
             "priced"))
    for r in lands_out:
        if r["verdict"] == "CLEAR":
            continue
        p = r.get("price_at_licensed_neck") or r.get("price_at_widest") or {}
        pr = ("" if not p else
              "%.3f A vs %s A %s" % (p["amps"],
                                     p["required_amps"], p["why"]))
        print("%-10s %-34s %-11s %-6.3f %-8.4f %-7s %-17s %s"
              % (r["pad"], r["net"][:34], r["netclass"], r["contract_mm"],
                 r["best_margin_mm"],
                 "-" if r["widest_mm"] is None else "%.4f" % r["widest_mm"],
                 r["verdict"], pr))
    print("\n%s" % json.dumps(summary, sort_keys=True))
    gaps = [n for n in nets_out if n["routed_above_dru_floor"]]
    if gaps:
        print("\nrouted ABOVE the .kicad_dru floor (the NFC_RF width_cap "
              "lesson), %d net(s):" % len(gaps))
        for n in gaps:
            print("  %-34s %-11s contract %.3f mm vs DRU floor %.3f mm"
                  % (n["net"][:34], n["netclass"], n["contract_mm"],
                     n["dru_floor_mm"]))
    return 0 if ctl_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
