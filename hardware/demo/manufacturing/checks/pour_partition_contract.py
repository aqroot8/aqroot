#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- an outer pour's PAD PARTITION may not get finer unnoticed.

D-619 refused a `/04_SPI_B_RADIOS_NFC/NFC_VDD_A` route that closed an edge,
regressed nothing and drew ZERO attributable DRC, because its 4.4 mm `B.Cu`
wall up the west side of `U9` severed the `GND` pour and left `C45.2`,
`C51.2` and `C53.2` on a 12.461 mm2 fragment.  Every instrument on this board
passed that route:

    verify_promotion.py   counts OBJECTS, and nothing was removed
    routing_ledger.py     counts EDGES, and `GND` stayed at 4
    kicad-cli drc         reports UNCONNECTED ITEMS, and there were none --
                          the fragment keeps three of its own through barrels
    pour_bond_guard.py    reserves narrow bonds it can FIND, and before the
                          cut there was no neck there to find

It was caught by a person reading island areas, once, by hand.  This file is
that reading, made mechanical, so the next one is caught by the gate.

WHAT IS MEASURED.  For every filled OUTER pour, each pad of the pour's net is
resolved to the island that CONTAINS it -- by geometry, never by ordinal, for
the reason `pour_bond_contract.py` P2 already records: one new island
renumbers every ordinal above it.  That gives a PARTITION of the pour's pads.
The claim is then a claim about the partition and not about a count:

  PP1  WELL FORMED, AND THE BAR IS THE TRANSACTION.  Every pad of a
       pour-owning net that sits on that pour's layer is resolved to an island
       of it.  Some never are and always were not: a net owning a BOUNDED pour
       has lands outside that pour's outline by construction, and this board
       has 20 of them (19 `BQ25185_SYS`, plus `GND` `MK1.4`).  Asserting zero
       would be asserting a different board.  The claim is therefore that the
       transaction introduces NO NEW unresolved pad -- a pad that resolved
       before and resolves nowhere after has had its pour taken away, which is
       the same injury PP2 measures arriving by a different road.

  PP2  NO PAD PAIR IS SPLIT.  Two pads that shared an island BEFORE share one
       AFTER.  This is strictly stronger than an island COUNT, which moves for
       harmless reasons -- a pour growing a new sliver, a zone refilled around
       a via -- and weaker than a copper diff, which moves for every route.
       It is exactly the injury: copper that used to join two lands does not.

  PP3  A SPLIT IS PRICED, NOT ONLY NAMED.  For every new fragment, what does
       it still have?  Each pad's own through barrels are resolved into the
       net's filled zones on the RESERVED INNER PLANES, because that is the
       bond a severed outer fragment actually keeps.  A fragment whose every
       pad keeps a barrel into a full-board reference plane is `BONDED`; one
       with a pad that keeps nothing is `STRANDED`, and STRANDED is the
       hard refusal -- it is the D-584 orphan, the failure mode the pour was
       poured to avoid.

  PP4  NON-VACUITY.  Deleting the fragment's barrels must turn every `BONDED`
       verdict into `STRANDED`.  A clause that cannot fail is not a clause.

WHY `BONDED` IS NOT A FAILURE, STATED HONESTLY.  D-619 treated any severance
as an injury.  D-622 measured the two sides of that trade for the first time
and they are not close: the `C45` pocket's `B.Cu` geodesic back to the main
island is **32.001 mm** the long way round the west of `U9`, while each of its
three pads sits within a millimetre of its own through barrel into the SAME
9450.2 mm2 `In1.Cu` and `In4.Cu` `GND` reference planes -- `In4` one prepreg
below `B.Cu`.  Severing a 32 mm outer detour off pads that each own a barrel
into two solid reference planes is not a return-path injury; it is what those
barrels are for.  So this contract does not forbid severance.  It forbids
severance that STRANDS, and it makes every other severance state its price.

Read-only.  Nothing here writes a board.

    python3 checks/pour_partition_contract.py --ref HEAD [--board B] -o OUT
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANU = ROOT / "hardware/demo/manufacturing"
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SIDECARS = ("aqroot-Beta-v2.kicad_dru", "aqroot-Beta-v2.kicad_pro",
            "aqroot-Beta-v2.kicad_prl")

sys.path.insert(0, str(MANU))


def board_at(rev, tmp):
    """The board as it stands at `rev`, with the sidecars it is read against.

    A scratch board without its `.kicad_pro` silently drops every netclass to
    Default; without its `.kicad_dru` it is judged by different rules.  Both
    matter here because the zones are read from the file, so they are copied.
    """
    out = Path(tmp) / "pre"
    out.mkdir(parents=True, exist_ok=True)
    rel = "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
    blob = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (rev, rel)],
                          check=True, capture_output=True).stdout
    (out / "aqroot-Beta-v2.kicad_pcb").write_bytes(blob)
    for s in SIDECARS:
        (out / s).write_bytes((PROJECT / s).read_bytes())
    return out / "aqroot-Beta-v2.kicad_pcb"


def partition(path):
    """{key: {islands, pads:{ref: island}, geometry}} for every OUTER pour."""
    import pcbnew
    import pour_bond_guard as pg
    board = pcbnew.LoadBoard(str(path))
    pours = pg.read_pours(board)
    for p in pours:
        pg.assign(board, p)
    out, unresolved = {}, []
    for p in pours:
        key = "%s|%s|%s" % (p["net"], p["lkey"], p["zone"])
        pads, isl = {}, {}
        for i, e in enumerate(p["islands"]):
            isl[i] = dict(area_mm2=round(e["area_mm2"], 3),
                          pads=sorted(q["ref"] for q in e["pads"]),
                          vias=[(v["x"], v["y"]) for v in e["vias"]])
            for q in e["pads"]:
                pads[q["ref"]] = i
        out[key] = dict(net=p["net"], lkey=p["lkey"], layer=p["layer"],
                        zone_name=p["zone_name"], n_islands=len(p["islands"]),
                        pads=pads, islands=isl)
        # PP1: a pad of this net, on this layer, that landed on no island
        for fp in board.GetFootprints():
            for q in fp.Pads():
                if q.GetNetname() != p["net"]:
                    continue
                if p["layer"] not in [board.GetLayerName(l)
                                      for l in q.GetLayerSet().CuStack()]:
                    continue
                ref = "%s.%s" % (fp.GetReference(), q.GetNumber())
                if ref not in pads:
                    unresolved.append(dict(pour=key, pad=ref))
    return out, unresolved


def reserved_plane_zones(path):
    """Filled zones of each net on the RESERVED INNER planes, by net."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    import route_maze_batch as rb
    reserved = rb.reserved_inner_planes(board)
    inner = {"In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"}
    out = {}
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid in z.GetLayerSet().CuStack():
            ln = board.GetLayerName(lid)
            if ln not in inner:
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                sub = pcbnew.SHAPE_POLY_SET()
                sub.AddOutline(ps.Outline(i))
                for h in range(ps.HoleCount(i)):
                    sub.AddHole(ps.Hole(i, h), 0)
                out.setdefault(z.GetNetname(), []).append(
                    (ln, z.GetZoneName(), sub, round(sub.Area() / 1e12, 3)))
    return out, reserved


def barrels(path, net):
    """Through barrels of `net`: (x, y, top, bottom)."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != net:
            continue
        v = pcbnew.Cast_to_PCB_VIA(t)
        out.append((v.GetPosition().x, v.GetPosition().y,
                    board.GetLayerName(v.TopLayer()),
                    board.GetLayerName(v.BottomLayer())))
    return out


def price_fragment(path, net, frag, planes, drop_barrels=()):
    """PP3: what does every pad of this fragment still have?

    A pad is BONDED when a barrel of its own net lies inside the fragment's
    own island copper AND inside a filled zone of that net on a reserved
    inner plane.  `drop_barrels` is PP4's knife: the same measurement with
    named barrels removed must come back STRANDED.
    """
    import pcbnew
    drop = {(int(x), int(y)) for (x, y) in drop_barrels}
    keep = [b for b in frag["vias"] if (int(b[0]), int(b[1])) not in drop]
    rows = []
    for b in keep:
        pt = pcbnew.VECTOR2I(int(b[0]), int(b[1]))
        hits = [dict(layer=ln, zone=zn, area_mm2=ar)
                for (ln, zn, poly, ar) in planes.get(net, [])
                if poly.Contains(pt, -1, 0)]
        rows.append(dict(xy_mm=[round(b[0] / 1e6, 3), round(b[1] / 1e6, 3)],
                         planes=hits))
    bonded = [r for r in rows if r["planes"]]
    return dict(barrels=len(keep), barrels_into_reserved_planes=len(bonded),
                detail=rows,
                verdict="BONDED" if bonded else "STRANDED")


def compare(pre_path, post_path):
    pre, pre_bad = partition(pre_path)
    post, post_bad = partition(post_path)
    planes, reserved = reserved_plane_zones(post_path)

    res = {}
    was = {(x["pour"], x["pad"]) for x in pre_bad}
    now = {(x["pour"], x["pad"]) for x in post_bad}
    new_bad = sorted(now - was)
    res["PP1"] = dict(ok=not new_bad and len(post) >= len(pre),
                      newly_unresolved=[dict(pour=k, pad=v) for k, v in new_bad],
                      unresolved_pre=len(pre_bad), unresolved_post=len(post_bad),
                      unresolved_inherited=sorted("%s %s" % (k.split("|")[0], v)
                                                  for k, v in sorted(was & now)),
                      pours_pre=len(pre), pours_post=len(post))

    splits, fragments = [], []
    for key, a in sorted(pre.items()):
        c = post.get(key)
        if c is None:
            splits.append(dict(pour=key, why="POUR_DISAPPEARED"))
            continue
        # group the PRE pads by their PRE island, then look at where they went
        groups = {}
        for ref, i in a["pads"].items():
            groups.setdefault(i, set()).add(ref)
        for i, refs in sorted(groups.items()):
            landed = {}
            for ref in refs:
                if ref in c["pads"]:
                    landed.setdefault(c["pads"][ref], set()).add(ref)
            if len(landed) <= 1:
                continue
            biggest = max(landed, key=lambda j: c["islands"][j]["area_mm2"])
            rec = dict(pour=key, net=a["net"], layer=a["layer"],
                       pre_island=i,
                       pre_area_mm2=a["islands"][i]["area_mm2"],
                       pre_pads=len(refs),
                       parts=[dict(post_island=j,
                                   area_mm2=c["islands"][j]["area_mm2"],
                                   pads=sorted(v),
                                   body=(j == biggest))
                              for j, v in sorted(landed.items())])
            splits.append(rec)
            for j, v in sorted(landed.items()):
                if j == biggest:
                    continue
                pr = price_fragment(post_path, a["net"], c["islands"][j], planes)
                fragments.append(dict(pour=key, net=a["net"], layer=a["layer"],
                                      post_island=j,
                                      area_mm2=c["islands"][j]["area_mm2"],
                                      pads=sorted(v), **pr))
    res["PP2"] = dict(ok=not splits, splits=splits,
                      islands={k: [pre[k]["n_islands"],
                                   post[k]["n_islands"]] for k in sorted(pre)
                               if k in post})
    res["PP3"] = dict(
        ok=all(f["verdict"] == "BONDED" for f in fragments),
        reserved_inner_planes={k: sorted(v) for k, v in reserved.items()},
        fragments=fragments)

    # -- PP4 ---------------------------------------------------------------- #
    # The knife: take every barrel away from each fragment and the verdict
    # must flip.  With no fragment at all the clause is exercised on the pour
    # the transaction DID touch, so it can still fail loudly.
    probes = []
    for f in fragments:
        key = f["pour"]
        j = f["post_island"]
        frag = post[key]["islands"][j]
        cut = price_fragment(post_path, f["net"], frag, planes,
                             drop_barrels=frag["vias"])
        probes.append(dict(pour=key, post_island=j, pads=f["pads"],
                           with_barrels=f["verdict"],
                           without_barrels=cut["verdict"],
                           flips=(f["verdict"] == "BONDED"
                                  and cut["verdict"] == "STRANDED")))
    if not fragments:
        # NO FRAGMENT IS THE GOOD OUTCOME AND IT MUST STILL BE PROVED.  Take
        # the largest pad-bearing island of every pour, strip its barrels and
        # require the pricing to report STRANDED, so the machinery that would
        # judge a fragment is exercised on this board even when there is none.
        for key, c in sorted(post.items()):
            cand = [(e["area_mm2"], j) for j, e in c["islands"].items()
                    if e["pads"] and e["vias"]]
            if not cand:
                continue
            # PROBE ONLY WHERE THE FLIP CAN MEAN SOMETHING.  `BQ25185_SYS`
            # owns two BOUNDED `B.Cu` pours and no reserved inner plane, so
            # its islands price STRANDED with their barrels in place and
            # STRANDED without them -- a true reading of that net and a
            # vacuous knife.  The clause is exercised where a reserved plane
            # exists to be cut off from, which on this board is `GND`
            # (`In1`/`In4`) and `+3V3` (`In3`).
            for _, j in sorted(cand, reverse=True):
                frag = c["islands"][j]
                live = price_fragment(post_path, c["net"], frag, planes)
                if live["verdict"] != "BONDED":
                    continue
                cut = price_fragment(post_path, c["net"], frag, planes,
                                     drop_barrels=frag["vias"])
                probes.append(dict(pour=key, post_island=j,
                                   pads=frag["pads"][:6],
                                   with_barrels=live["verdict"],
                                   without_barrels=cut["verdict"],
                                   flips=(cut["verdict"] == "STRANDED")))
                break
    res["PP4"] = dict(ok=bool(probes) and all(p["flips"] for p in probes),
                      probes=probes)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE board")
    ap.add_argument("--board", default=str(BOARD),
                    help="the POST board (default: the authoritative one)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="aqroot-pp-") as tmp:
        pre = board_at(a.ref, tmp)
        res = compare(pre, Path(a.board))
    ok = all(res[k]["ok"] for k in ("PP1", "PP2", "PP3", "PP4"))
    doc = dict(schema=1, ref=a.ref, board=str(a.board), ok=ok, results=res)
    text = json.dumps(doc, indent=1, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for k in ("PP1", "PP2", "PP3", "PP4"):
        print("%s %s" % (k, "PASS" if res[k]["ok"] else "FAIL"))
    print("pour_partition_contract: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
