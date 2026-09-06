#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHICH crossing track should the transaction cut?

D-639 promoted the first rip-up-and-relay this board has ever taken and closed
with a ranked list whose first item was *"re-take `screen_segment_evict` on the
promoted board and gate `GND U9.16`"*.  Re-taking it reproduces the same answer
on the promoted board -- `GND U9.16` is `SEGMENT_OPENS`, on ONE named cut, and
that cut is `/04_SPI_B_RADIOS_NFC/NFC_RFO2`.

AND THAT CUT IS NOT FREE, BECAUSE THE BOARD ALREADY OWNS A CONTRACT ABOUT IT.
`NFC_RFO2` is the LONGER of the two 13.56 MHz transmit arms -- 8.9446 mm
against `NFC_RFO1`'s 6.0744 mm, a 2.8702 mm mismatch that is PM-3, an OPEN
recorded placement defect -- and `checks/rf_symmetry_contract.py` RF2 bounds
the GROWTH of exactly that mismatch by a budget which **defaults to zero**.
The relay measured for this land is 2.6872 -> 3.0997 mm, so the transaction
D-639 left ready would have grown the recorded defect by 0.4125 mm and the
standing contract would have refused it AFTER the gate run was spent.

SO THE QUESTION THIS SCREEN ASKS IS ONE NOBODY HAS ASKED.
`screen_segment_evict` walks its candidate tracks NEAREST-FIRST and stops at
the FIRST one whose single cut opens the land (its "QUESTION 2"), and every
instrument downstream -- `relay_price`, `screen_relay_transaction`,
`--plan-out`, the gate -- inherits that one choice without ever learning
whether there was another.  Distance to the land is not a price.  What a cut
costs is what the RELAY costs, and what the relay costs is decided by whose
track it is.

    For a land that opens, enumerate EVERY candidate track, cut each ALONE,
    and report every one that opens the barrel site -- with the citation
    each cut net carries in this repository's own contracts.

Nothing here is invented.  The lattice is `screen_segment_evict.land_field`,
which is that screen's own construction lifted out unchanged, so a cut this
screen calls an opener is an opener in exactly the sense QUESTION 2 means.
The candidate list is `screen_segment_evict.candidates`, in its own order and
under its own `--cap`.  The verdict per cut is `screen_segment_evict.try_island`
under `screen_segment_evict.Cuts`, which is QUESTION 2's own body.

THE CITATIONS ARE READ, NEVER LISTED.  A hand-maintained "sensitive nets" table
is a second copy of the truth and would be wrong the day a contract changed.
This screen greps the contracts THEMSELVES -- every `checks/*.py`, the
promotion verifier, the protected-copper regex and the board's own
`.kicad_dru` -- for each cut net's literal name and its netclass, and reports
the files and rule names that mention them.  A cut net with no citation
anywhere is a cut nothing in this repository has an opinion about; a cut net
with citations is one whose relay has to be judged against them BEFORE a gate
run is spent, which is the whole point.

A POSITIVE CONTROL RIDES ALONG.  `screen_segment_evict`'s own chosen cut must
appear in this screen's opener list, or the two instruments disagree about the
same land and this one is wrong.  It is reported as `reproduces_evidence_cut`
and a run where it is false is a run whose ranking means nothing.

NOTHING IS WRITTEN.  The authoritative board is opened once, read, and its
sha256 is re-checked at exit.  Every cut lives in the in-memory obstacle model
and is restored.
"""

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
DRU = BOARD.with_suffix(".kicad_dru")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))

from screen_segment_evict import (Cuts, candidates, land_field, seg_record,
                                  try_island, window_cuts)

# The files that are allowed to have an opinion about a net.  Every one of them
# is a contract this repository already runs; nothing is added to this list to
# make a particular answer come out, and a file that stops existing simply
# stops being cited.
# The board's catch-all netclass.  A net that carries it carries no class-level
# constraint, so a match on the literal name is noise and never a citation.
NULL_CLASS = "Default"

CONTRACT_FILES = sorted(
    [p for p in (HERE / "checks").glob("*.py") if p.name != "__init__.py"]
    + [HERE / "verify_promotion.py", HERE / "protected_copper.py"])


def net_copper(qb, net):
    """This net's routed copper today: length, layers, barrels.

    The figure a length contract measures is the whole net, so that is what a
    relay's delta has to be read against.  Taken off the obstacle model, which
    is the same geometry every other instrument here uses.
    """
    import qrouter as qr
    mm, layers, vias = 0.0, set(), set()
    for L in qb.cu:
        for s in qb.shapes[L]:
            if s.net != net:
                continue
            if isinstance(s, qr.SEG) and s.tag == 'track':
                mm += math.hypot(s.x1 - s.x0, s.y1 - s.y0) / 1e6
                layers.add(L)
            elif getattr(s, "tag", None) == 'via':
                vias.add((s.cx, s.cy))
    return dict(mm=round(mm, 4), layers=sorted(layers), vias=len(vias))


def citations(net, netclass, texts):
    """Every contract file and `.kicad_dru` rule that names this net or class.

    The net name is matched WHOLE -- a bare `NFC_RFO1` must not answer for
    `NFC_RFO10` -- and the sheet-path prefix is stripped for the search because
    contracts spell these nets both ways.
    """
    leaf = net.rsplit("/", 1)[-1]
    pats = [re.compile(r"(?<![\w/])%s(?![\w])" % re.escape(x))
            for x in {net, leaf} if x]
    out = []
    for (name, text) in texts:
        hits = sorted({m.group(0) for p in pats for m in p.finditer(text)})
        if hits:
            out.append(dict(where=name, matched=hits, kind="net"))
    # `Default` IS NOT A CITATION.  It is this board's catch-all class, and
    # the literal word appears in every argparse call and half the comments in
    # these files, so matching it reports an opinion nobody holds.  `GND
    # J3.A12/B1` is the case that forced this: its sole opener `Net-(J3-CC2)`
    # came back with three "citations" and two `.kicad_dru` rules, and every
    # one of them was the string `Default` inside a block about something else.
    # A class that constrains nothing may not make a net look constrained.
    if netclass and netclass != NULL_CLASS:
        p = re.compile(r"(?<![\w])%s(?![\w])" % re.escape(netclass))
        for (name, text) in texts:
            if p.search(text):
                out.append(dict(where=name, matched=[netclass],
                                kind="netclass"))
    return out


def dru_rules(net, netclass, dru_text):
    """The `.kicad_dru` rules whose body names this net or its netclass."""
    leaf = net.rsplit("/", 1)[-1]
    if not netclass or netclass == NULL_CLASS:
        netclass = None
    want = re.compile(r"(?<![\w/])(%s|%s)(?![\w])"
                      % (re.escape(leaf), re.escape(netclass or "\x00")))
    out, name = [], None
    for block in re.split(r"(?m)^\(rule\s", dru_text):
        m = re.match(r'\s*"([^"]+)"', block)
        if not m:
            continue
        name = m.group(1)
        if want.search(block):
            out.append(name)
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--evidence", type=Path, required=True,
                    help="a screen_segment_evict.py artifact taken on THIS "
                         "board; the land, the island and the cut this screen "
                         "ranks against are the ones that screen measured")
    ap.add_argument("--land", action="append", default=[], metavar="NET:REF",
                    help="only this land, e.g. 'GND:U9.16'.  Repeatable")
    ap.add_argument("--grid", type=int, default=100000)
    ap.add_argument("--max-mm", type=float, default=8.0)
    ap.add_argument("--rung", choices=("floor", "relief"), default="floor")
    ap.add_argument("--cap", type=int, default=20)
    ap.add_argument("--guard", type=Path)
    ap.add_argument("--body-landing", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import qrouter as qr
    import incremental_router as ir
    import maze3d as mz
    from route_maze_batch import reserved_inner_planes, load_guard

    board_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    ev = json.loads(a.evidence.read_text(encoding="utf-8"))
    if ev.get("board_sha256") != board_sha:
        print("REFUSED: the evidence was taken on board %s and this board is "
              "%s" % (ev.get("board_sha256", "?")[:16], board_sha[:16]),
              file=sys.stderr)
        return 2

    texts = [(str(p.relative_to(ROOT)), p.read_text(encoding="utf-8",
                                                    errors="replace"))
             for p in CONTRACT_FILES if p.exists()]
    dru_text = DRU.read_text(encoding="utf-8") if DRU.exists() else ""

    spec = load_guard(a.guard)
    qb = qr.QBoard(str(a.board))
    ir.inject_existing_via_obstacles(qb)
    neck = mz.neck_rule(qb)
    reserved = reserved_inner_planes(qb.b)
    want = set(a.land)

    out = []
    for rec in ev["nets"]:
        net = rec["net"]
        lf = None
        for l in rec["lands"]:
            if not l.get("verdict", "").startswith("SEGMENT_") \
                    or "cuts" not in l:
                continue
            key = "%s:%s" % (net, l["land"][0])
            if want and key not in want:
                continue
            if lf is None:
                lf = land_field(qb, net, a.grid, a.rung, neck, reserved, spec,
                                a.body_landing)
                islands = mz.net_islands(qb, net)
                body = max(islands, key=len) if islands else None
            field, land_ok = lf["field"], lf["land_ok"]
            refs = set(l["land"])
            island = None
            for isl in islands:
                if isl is body:
                    continue
                if refs & {p["ref"] for p in isl}:
                    island = [p for p in isl if p["ref"] in refs]
                    break
            if not island:
                out.append(dict(land=key, error="the land's pads are no "
                                                "longer an island of this net"))
                continue

            chosen, vias = candidates(qb, field, island, a.max_mm, a.cap)
            evidence_cut = {(c["net"], c["layer"],
                             tuple(c["a_mm"]), tuple(c["b_mm"]))
                            for c in l["cuts"]}
            openers, refused = [], []
            for (L, s) in chosen:
                with Cuts(qb, field, window_cuts([(L, s)], island, a.max_mm)):
                    r = try_island(qb, field, island, a.max_mm, land_ok)
                sr = seg_record(L, s)
                nc = None
                try:
                    from route_maze_batch import net_contract
                    nc = net_contract(qb.b, s.net)["netclass"]
                except Exception:
                    nc = None
                row = dict(cut=sr, netclass=nc,
                           is_evidence_cut=bool(
                               (sr["net"], sr["layer"],
                                tuple(sr["a_mm"]), tuple(sr["b_mm"]))
                               in evidence_cut))
                if r and r.get("ok"):
                    row.update(opens=True, stitch_mm=r.get("mm"),
                               via_xy=list(r.get("via_xy") or ()),
                               net_copper=net_copper(qb, s.net),
                               citations=citations(s.net, nc, texts),
                               dru_rules=dru_rules(s.net, nc, dru_text))
                    openers.append(row)
                else:
                    row.update(opens=False,
                               reason=(r or {}).get("reason"))
                    refused.append(row)

            # UNCITED MEANS NOTHING NAMES THIS NET.  A class-level hit is
            # reported but does not make an opener cited: the question a cut
            # has to answer is what THIS net owes, and a netclass shared with
            # eighty others cannot answer it.
            uncited = [o for o in openers
                       if not [c for c in o["citations"]
                               if c["kind"] == "net"]
                       and not o["dru_rules"]]
            out.append(dict(
                land=key, net=net, netclass=rec.get("netclass"),
                rung=lf["rung"], island=[p["ref"] for p in island],
                candidates=len(chosen), foreign_vias=len(vias),
                openers=openers, refused=refused,
                opener_nets=sorted({o["cut"]["net"] for o in openers}),
                reproduces_evidence_cut=any(o["is_evidence_cut"]
                                            for o in openers),
                uncited_openers=[o["cut"]["net"] for o in uncited],
                verdict=("SOLE_CUT" if len(openers) == 1 else
                         "CHOICE" if openers else "NO_SINGLE_CUT")))
            print("  %-16s %2d candidates -> %d opener(s): %s"
                  % (key, len(chosen), len(openers),
                     ", ".join(sorted({o["cut"]["net"] for o in openers}))
                     or "none"),
                  file=sys.stderr, flush=True)

    doc = dict(
        schema=1, board=str(a.board), board_sha256=board_sha,
        evidence=str(a.evidence),
        evidence_sha256=hashlib.sha256(
            a.evidence.read_bytes()).hexdigest(),
        grid=a.grid, max_mm=a.max_mm, rung=a.rung, cap=a.cap,
        body_landing=bool(a.body_landing),
        contract_files=[n for (n, _t) in texts],
        question="screen_segment_evict stops at the FIRST candidate track "
                 "whose single cut opens a plane land, nearest-first, and "
                 "every instrument downstream inherits that choice.  Which "
                 "OTHER single cuts open the same land, and what does this "
                 "repository's own contracts say about each cut net?",
        method="read-only; screen_segment_evict.land_field builds the lattice, "
               "screen_segment_evict.candidates the list, and "
               "screen_segment_evict.try_island under Cuts is QUESTION 2's own "
               "body -- every trial reverted.  Citations are grepped out of "
               "checks/*.py, verify_promotion.py, protected_copper.py and the "
               "board's .kicad_dru, never listed here",
        lands=out,
        authoritative_unchanged=(
            hashlib.sha256(a.board.read_bytes()).hexdigest() == board_sha))
    if a.out:
        a.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    print(json.dumps({d["land"]: d.get("verdict") or d.get("error")
                      for d in out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
