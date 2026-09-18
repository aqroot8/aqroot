#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY, ABSOLUTE: can each POWER RAIL's actual copper
carry the current the design asks of it, ALONG THE PATH THE CURRENT TAKES?

WHY THIS EXISTS AND WHY IT IS NOT `audit_bond_ampacity.py`.  Every ampacity
instrument on this board so far is a DIFF: it takes an authority and a
candidate and rules on the copper the candidate ADDED.  That answers "did this
transaction make anything worse", which is the wrong question at release.
D-742 asked the right one -- "is the `USB_VBUS_CHG` conductor big enough for
the current the charger is programmed to draw" -- and no instrument here could
answer it, because the answer needs three things a diff does not have:

  1. AN ABSOLUTE DESIGN CURRENT per rail, not a delta.
  2. THE PATH.  A power net is not uniformly a power conductor.
     `/01_POWER_TREE/USB_VBUS_CHG` has ELEVEN pads on it and nine of them are
     telemetry: two dividers, two Schottky steering diodes, a gate resistor and
     a 1 M pull.  Those branches carry microamps and are 200 mm long.  Judging
     the net by its narrowest track anywhere condemns copper that carries
     nothing, and -- far worse -- a rail whose CARRYING path is starved can
     hide behind a wide telemetry stub.  So the rail is declared as
     SOURCE pads -> SINK pads and only the copper BETWEEN them is judged.
  3. dT, NOT PASS/FAIL.  IPC-2221B is stated as "the width for a 10 K rise".
     A 0.10 mm neck inside a package courtyard and a 33 mm haul are not the
     same object even at the same width, and a floor that says only
     "0.35 mm min" cannot tell them apart.  This reports the rise each segment
     actually runs at, its length, and its share of the path's series drop.

METHOD.  IPC-2221B, the same form `audit_bond_ampacity.py` uses and the same
form `.kicad_dru` section 5 published years earlier:

    I = k * dT^0.44 * A^0.725     A in mil^2, I in amperes
    k = 0.048 outer, 0.024 inner

so, inverted for the rise a known current produces in a known conductor,

    dT = (I / (k * A^0.725)) ** (1/0.44)

SELF-CHECK FIRST.  The run re-derives `.kicad_dru` section 5's own published
width table before it rules on anything.  A method that cannot reproduce the
board's own numbers has no business condemning the board's own copper; the
residual is reported in `method_selfcheck` and a miss is a FAIL of this tool,
not of the board.

THE PATH IS THE WIDEST BOTTLENECK, NOT THE SHORTEST ROUTE.  Real current
divides among every parallel path, so the honest conservative bound is the
single best path available to it: a maximin (widest-bottleneck) search over the
copper graph.  If THAT path has a segment too narrow, no division of current
saves it.  Parallel paths only ever help, so this under-states the board.

    python3 audit_rail_ampacity.py [--board B] [-o OUT.json]
"""
import argparse, json, math, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import pcbnew

BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

# This board's stackup, transcribed from the fab notes it is ordered against
# and identical to the constants `audit_bond_ampacity.py` already uses.
OUTER_MM = 0.0348               # 1 oz finished outer copper
INNER_MM = 0.0174               # 0.5 oz finished inner copper
PLATING_MM = 0.025              # JLCPCB plated barrel wall, minimum
MIL2_PER_MM2 = 1.0 / 0.00064516
K_EXT, K_INT = 0.048, 0.024
RHO_CU = 1.72e-5                # ohm-mm at 20 C
OUTER = {"F.Cu", "B.Cu"}
DT_REF = 10.0                   # the rise every published floor is stated at

# --------------------------------------------------------------------------
# THE RAIL TABLE.  `amps` is the ENFORCED maximum the design permits, not a
# typical -- the same convention `.kicad_dru` section 5 uses when it writes
# "0.70 A ILIM" and "0.5 A (ILIM500)".  Every entry cites what sets it.
# --------------------------------------------------------------------------
RAILS = (
    dict(name="USB_VBUS_CHG", net="/01_POWER_TREE/USB_VBUS_CHG",
         src=("R35.2",), snk=("U11.10",), amps=1.10,
         basis="BQ25185 ILIM/VSET = 13 kOhm -> ILIM1100 (SLUSF65B table 6-1); "
               "D-742 raised it from ILIM500 so ICHG can reach 800 mA inside "
               "the 360 min tMAXCHG safety timer"),
    dict(name="USB_VBUS_RAW", net="/01_POWER_TREE/USB_VBUS_RAW",
         src=("J3.A4", "J3.B4", "J3.A9", "J3.B9"), snk=("R35.1",), amps=1.10,
         basis="same charger input current, upstream of the R35 0 R link"),
    dict(name="BAT_PROTECTED_P", net="/01_POWER_TREE/BAT_PROTECTED_P",
         src=("R75.2", "R75.4"), snk=("U11.2",), amps=1.50,
         basis="BAT_MAIN 1.5 A sustained design current (.kicad_dru section 5); "
               "IBAT_OCP 3.125 A is a fault trip, not a routing current"),
    dict(name="BQ25185_SYS", net="/01_POWER_TREE/BQ25185_SYS",
         src=("U11.1",), snk=("U12.1",), amps=1.00,
         basis="SYS_MAIN 1.0 A (.kicad_dru section 5)"),
)


def ampacity(area_mm2, dT, external):
    a = area_mm2 * MIL2_PER_MM2
    return (K_EXT if external else K_INT) * (dT ** 0.44) * (a ** 0.725)


def rise(area_mm2, amps, external):
    """The IPC-2221B temperature rise this conductor runs at, inverted."""
    a = area_mm2 * MIL2_PER_MM2
    k = K_EXT if external else K_INT
    denom = k * (a ** 0.725)
    if denom <= 0:
        return float("inf")
    return (amps / denom) ** (1.0 / 0.44)


def width_for(amps, dT, external):
    """IPC-2221B width in mm for this current at this rise, this board's copper."""
    k = K_EXT if external else K_INT
    a_mil2 = (amps / (k * dT ** 0.44)) ** (1.0 / 0.725)
    return a_mil2 / MIL2_PER_MM2 / (OUTER_MM if external else INNER_MM)


def selfcheck():
    """Re-derive `.kicad_dru` section 5's published table before ruling."""
    published = (
        ("BAT_MAIN", 1.5, 0.525, 2.734), ("SYS_MAIN", 1.0, 0.300, 1.563),
        ("P3V3", 1.0, 0.300, 1.563), ("ACC_3V3", 0.40, 0.085, 0.443),
        ("ACC_5V", 0.70, 0.184, 0.958), ("VBUS_CHG", 0.5, 0.115, 0.601),
        ("SPK_OUT", 0.29, 0.070, 0.365),
    )
    rows, worst = [], 0.0
    for name, amps, outer, inner in published:
        o, i = width_for(amps, DT_REF, True), width_for(amps, DT_REF, False)
        rows.append(dict(rail=name, amps=amps,
                         dru_outer_mm=outer, derived_outer_mm=round(o, 4),
                         dru_inner_mm=inner, derived_inner_mm=round(i, 4)))
        worst = max(worst, abs(o - outer), abs(i - inner))
    return dict(rows=rows, worst_residual_mm=round(worst, 4), ok=worst <= 0.005)


def pad_key(pad):
    p = pad.GetPosition()
    return ("PAD", pad.GetParentFootprint().GetReference(), pad.GetNumber(),
            p.x, p.y)


def build_graph(board, net):
    """Nodes are copper endpoints; edges are the conductors between them.

    A track is an edge of its own width and length.  A via is an edge whose
    conductor is the plated barrel wall -- an annulus of the drill diameter and
    the plating thickness -- because a barrel is a conductor too and on this
    board it has repeatedly been the bottleneck.  A pad is joined to every
    track endpoint that lands inside it.
    """
    nodes, edges = set(), []
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                pads.append(pad)
                nodes.add(pad_key(pad))

    def node_at(x, y, layer):
        return ("PT", x, y, layer)

    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            lys = [board.GetLayerName(l) for l in range(pcbnew.PCB_LAYER_ID_COUNT)
                   if t.IsOnLayer(l) and pcbnew.IsCopperLayer(l)]
            drill = t.GetDrillValue() / 1e6
            area = math.pi * ((drill / 2 + PLATING_MM) ** 2 - (drill / 2) ** 2)
            # A barrel's wall is plated copper on every layer it spans; treat
            # it as an OUTER conductor (it is in free air at both ends) and as
            # 1.6 mm long, the full stack.
            for a in lys:
                for b in lys:
                    if a < b:
                        na, nb = node_at(pos.x, pos.y, a), node_at(pos.x, pos.y, b)
                        nodes.add(na); nodes.add(nb)
                        edges.append(dict(kind="via", a=na, b=nb, area_mm2=area,
                                          external=True, length_mm=1.6,
                                          width_mm=None, drill_mm=round(drill, 3),
                                          layer="%s-%s" % (a, b),
                                          x=round(pos.x / 1e6, 3), y=round(pos.y / 1e6, 3)))
            continue
        if t.GetClass() != "PCB_TRACK":
            continue
        ly = board.GetLayerName(t.GetLayer())
        s, e = t.GetStart(), t.GetEnd()
        na, nb = node_at(s.x, s.y, ly), node_at(e.x, e.y, ly)
        nodes.add(na); nodes.add(nb)
        w = t.GetWidth() / 1e6
        th = OUTER_MM if ly in OUTER else INNER_MM
        edges.append(dict(kind="track", a=na, b=nb, area_mm2=w * th,
                          external=ly in OUTER, length_mm=t.GetLength() / 1e6,
                          width_mm=round(w, 3), drill_mm=None, layer=ly,
                          x=round(s.x / 1e6, 3), y=round(s.y / 1e6, 3),
                          x2=round(e.x / 1e6, 3), y2=round(e.y / 1e6, 3)))

    # Bond every pad to the track endpoints that land on it.  A pad is a large
    # conductor; the edge is free.
    endpoints = [n for n in nodes if n[0] == "PT"]
    for pad in pads:
        pk = pad_key(pad)
        for n in endpoints:
            _, x, y, ly = n
            if pad.IsOnLayer(board.GetLayerID(ly)) and pad.HitTest(pcbnew.VECTOR2I(x, y)):
                edges.append(dict(kind="pad", a=pk, b=n, area_mm2=float("inf"),
                                  external=True, length_mm=0.0, width_mm=None,
                                  drill_mm=None, layer=ly,
                                  x=round(x / 1e6, 3), y=round(y / 1e6, 3)))
    return nodes, edges


def widest_bottleneck(nodes, edges, sources, sinks, amps):
    """Maximin search: the path whose WORST conductor is the best available."""
    adj = defaultdict(list)
    for ed in edges:
        adj[ed["a"]].append((ed["b"], ed))
        adj[ed["b"]].append((ed["a"], ed))

    def cap(ed):
        if ed["kind"] == "pad":
            return float("inf")
        return ampacity(ed["area_mm2"], DT_REF, ed["external"])

    best = {n: 0.0 for n in nodes}
    prev = {}
    import heapq
    heap = []
    for s in sources:
        best[s] = float("inf")
        heapq.heappush(heap, (-float("inf"), id(s), s))
    seen = set()
    while heap:
        negc, _, n = heapq.heappop(heap)
        if n in seen:
            continue
        seen.add(n)
        for m, ed in adj[n]:
            c = min(best[n], cap(ed))
            if c > best.get(m, 0.0):
                best[m] = c
                prev[m] = (n, ed)
                heapq.heappush(heap, (-c, id(m), m))
    reached = [k for k in sinks if best.get(k, 0.0) > 0.0]
    if not reached:
        return None, None
    tgt = max(reached, key=lambda k: best[k])
    path, cur = [], tgt
    while cur in prev:
        n, ed = prev[cur]
        path.append(ed)
        cur = n
    path.reverse()
    return path, best[tgt]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--dt-limit", type=float, default=20.0,
                    help="rise above which a segment is reported HOT")
    ap.add_argument("-o", type=Path)
    args = ap.parse_args()

    board = pcbnew.LoadBoard(str(args.board.resolve()))
    board.BuildConnectivity()
    check = selfcheck()

    pad_index = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            pad_index["%s.%s" % (fp.GetReference(), pad.GetNumber())] = pad

    out = []
    for rail in RAILS:
        nodes, edges = build_graph(board, rail["net"])
        srcs = [pad_key(pad_index[r]) for r in rail["src"] if r in pad_index]
        snks = [pad_key(pad_index[r]) for r in rail["snk"] if r in pad_index]
        missing = [r for r in rail["src"] + rail["snk"] if r not in pad_index]
        path, bottleneck = widest_bottleneck(nodes, edges, srcs, snks, rail["amps"])
        row = dict(rail=rail["name"], net=rail["net"], design_amps=rail["amps"],
                   basis=rail["basis"], source=list(rail["src"]),
                   sink=list(rail["snk"]), pads_not_on_board=missing)
        if path is None:
            row.update(connected=False, verdict="NO_PATH")
            out.append(row)
            continue
        segs, drop, hot = [], 0.0, []
        for ed in path:
            if ed["kind"] == "pad":
                continue
            dT = rise(ed["area_mm2"], rail["amps"], ed["external"])
            r = RHO_CU * ed["length_mm"] / ed["area_mm2"] if ed["area_mm2"] else 0.0
            drop += r * rail["amps"]
            seg = dict(kind=ed["kind"], layer=ed["layer"],
                       width_mm=ed["width_mm"], drill_mm=ed["drill_mm"],
                       length_mm=round(ed["length_mm"], 3),
                       area_mm2=round(ed["area_mm2"], 6),
                       rise_K=round(dT, 1),
                       required_mm_at_10K=round(
                           width_for(rail["amps"], DT_REF, ed["external"]), 3)
                       if ed["kind"] == "track" else None,
                       at=[ed.get("x"), ed.get("y")])
            segs.append(seg)
            if dT > args.dt_limit:
                hot.append(seg)
        segs_sorted = sorted(segs, key=lambda s: -s["rise_K"])
        row.update(connected=True,
                   path_segments=len(segs),
                   path_length_mm=round(sum(s["length_mm"] for s in segs), 3),
                   series_resistance_mohm=round(
                       sum(RHO_CU * s["length_mm"] / s["area_mm2"] for s in segs) * 1000, 3),
                   ir_drop_mV=round(drop * 1000, 2),
                   bottleneck_amps_at_10K=round(bottleneck, 3),
                   worst_rise_K=segs_sorted[0]["rise_K"] if segs else None,
                   hot_segments=hot,
                   worst_three=segs_sorted[:3],
                   verdict="OK" if not hot else "HOT")
        out.append(row)

    report = dict(schema=1, board=str(args.board), dt_limit_K=args.dt_limit,
                  method_selfcheck=check, rails=out,
                  all_ok=check["ok"] and all(r.get("verdict") == "OK" for r in out))
    text = json.dumps(report, indent=1, sort_keys=True)
    if args.o:
        args.o.write_text(text + "\n", encoding="utf-8")
    print(text)
    for r in out:
        print("  %-16s %-8s worst rise %-7s bottleneck %s A" % (
            r["rail"], r.get("verdict"), r.get("worst_rise_K"),
            r.get("bottleneck_amps_at_10K")), file=sys.stderr)
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
