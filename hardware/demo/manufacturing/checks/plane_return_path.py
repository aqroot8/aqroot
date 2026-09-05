#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- RP1..RP6: what does a SIGNAL SLOT on a RESERVED GND PLANE
cost the RETURN PATH of every trace that references that plane?

THE GAP THIS CLOSES.  `PP2` (D-628) prices a POUR severance in amperes.  It
has never been able to price a PLANE severance, because a reference plane is
not carrying the current that matters -- it is carrying somebody ELSE's return
current, and the cost of cutting it is paid by traces the cut never touches.
D-628's own record calls this "the one OPEN modelling gap in `PP2`", D-632,
D-633, D-634 and D-635 each carried it forward unclosed, and D-635 ended by
naming it the ONLY thing standing between a measured closure at the full
netclass trunk width and copper.  This is that clause.

WHAT A SLOT ACTUALLY COSTS, AND WHY IT IS GEOMETRY.  Return current does not
choose the shortest path; above a few tens of kilohertz it chooses the path of
LEAST INDUCTANCE, which is the plane copper directly beneath its own outbound
trace.  Cut a slot across that copper and the return has nowhere to go but
AROUND, and the loop that opens is the area between where the current wanted to
flow and where the copper let it.  Every term in that sentence is measurable
from the board:

  * WHICH traces pay -- the ones whose NEAREST reference is this plane, i.e.
    the copper layers immediately above and below it in the board's own
    stack-up.  Read from `GetEnabledLayers().CuStack()`, never transcribed:
    `.kicad_dru` section 2b states the intent ("L2 (In1) references the F.Cu
    side, L5 (In4) references the B.Cu side") and the board states the fact.
  * WHICH of them pay -- the ones that CROSS.  A trace that runs alongside a
    slot, or ends beside it, keeps a continuous return; only a trace whose
    copper spans the void from one side to the other has to detour.
  * HOW MUCH -- exactly.  The return follows the void's own boundary, so the
    detour is (the shorter boundary arc between where the trace enters the void
    and where it leaves) minus (the straight chord it wanted).  Both are
    computed on the real void outline, not estimated.

RP1  PLANE SURVIVES.  The plane's filled polygon, minus the haul stroked at
     the ZONE's OWN clearance and minus an anti-pad at every new barrel, is
     ONE outline, and every same-net via and land that was on the plane is
     still on its main body.  This is `screen_plane_slot.py`'s question asked
     of the REAL path at the REAL clearance with the REAL barrels, rather than
     of the worst-case straight cut at the netclass clearance.
RP2  REFERENCE INVENTORY.  Every foreign track on a layer this plane
     references is classified CROSS / GRAZE / CLEAR.  An empty CROSS list is
     the only free slot there is, and this clause is what proves the list.
RP3  CLASS REFUSAL.  No CROSS may belong to a REFERENCE-CRITICAL netclass.
     The list is not this file's opinion: each entry cites a live
     `.kicad_dru` rule by its exact name, and the clause FAILS if the cited
     rule is not present in the `.kicad_dru` beside the board -- so retiring
     or renaming a rule breaks this check loudly instead of silently widening
     it.  `USB_D` is the sharp case: the board's own rule is named "USB 2.0
     differential pair geometry (90 ohm on F.Cu over In1)", which NAMES `In1`
     as the pair's reference plane, so a slot in `In1` under that pair is
     refused by the board's authored intent and not by a judgement call.
RP4  DETOUR BUDGET.  Every admitted CROSS must detour less than
     `rise_length / 20`, where `rise_length = edge_ns * c / sqrt(epsilon_r)`
     and `epsilon_r` is read from the BOARD's own stack-up.  `--edge-ns` has
     NO DEFAULT and the clause refuses to run without it: the edge rate of a
     given net is not something this repository publishes, and D-633's LL-C
     already ruled that inventing an unpublished electrical figure is not
     something a clause may do.  Stating it on the command line puts it in the
     artifact, where it can be argued with.
RP5  THE HAUL'S OWN RETURN.  The haul is a coplanar strip inside its own slot:
     its return is the plane copper flanking it.  Both flanks, sampled at
     every vertex, must lie in the SAME outline of the cut plane -- otherwise
     the "return path" beside the signal is a different piece of copper.  And
     the haul's own netclass may not itself be reference-critical.
RP6  RETURN TRANSFER AT THE BARRELS.  Where a signal changes reference domain
     -- an `F.Cu` end referenced to `In1` hauling on `In4` -- its return
     current must change plane too, and the only thing that carries it is a
     GND through barrel near the signal barrel.  The distance to the nearest
     one is MEASURED at every barrel and budgeted the same way as RP4.  A haul
     on the plane its own ends already reference needs no transfer at all, and
     the clause says so rather than charging it: this is the term that makes
     `In1` and `In4` different prices for identical copper.

    python3 checks/plane_return_path.py --haul ART.json --edge-ns F
        [--layer In4] [--board B] [-o OUT]
    python3 checks/plane_return_path.py --layer In4 --seg X0,Y0,X1,Y1 ...
        --barrel X,Y,DIA --width NM --edge-ns F [-o OUT]

READ-ONLY.  No zone is refilled and the board is not written; the promotion
gate's `pour_partition` and `pour_bond` remain the only things that certify a
fill.  A PASS here is a PRICE, not a licence.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"

C_MM_NS = 299.792458          # speed of light, mm/ns

# ---------------------------------------------------------------------------
# RP3.  REFERENCE-CRITICAL NETCLASSES, EACH WITH THE LIVE RULE THAT SAYS SO.
#
# Every entry is a netclass this board's own `.kicad_dru` already constrains
# for a reason that a reference-plane cut would defeat -- controlled impedance,
# differential symmetry, an RF path pinned to one layer, or a switching edge
# whose loop must stay small.  The `cite` string is matched against the live
# `.kicad_dru` and a miss is an RP3 FAILURE, not a warning: this table is a
# pointer into the rules, never a second copy of them.
# ---------------------------------------------------------------------------
REFERENCE_CRITICAL = {
    "USB_D": ("USB 2.0 differential pair geometry (90 ohm on F.Cu over In1)",
              "impedance-controlled differential pair whose reference plane "
              "the rule NAMES"),
    "NFC_RF": ("NFC transmit arm minimum width - equal both arms",
               "differential transmit arms whose symmetry a return-path "
               "asymmetry defeats"),
    "NFC_RX": ("NFC receive path stays on B.Cu",
               "an RF receive path pinned to one layer by rule"),
    "NFC_OSC": ("NFC crystal nets stay on B.Cu",
                "a 27.12 MHz crystal net pinned to one layer by rule"),
    "SWITCH_NODE": ("SWITCH_NODE: low impedance, minimum width 0.40 mm",
                    "a switching node whose return loop is the radiator"),
    "LED_BOOST": ("LED_BOOST routed clearance - backlight string runs above "
                  "20 V",
                  "a boost output whose loop carries the fastest edges on "
                  "this board"),
    "SPK_OUT": ("SPK_OUT is outer-layer only - Class-D edges do not belong "
                "on In2",
                "a Class-D output already confined by rule for its edges"),
}


# ------------------------------------------------------------------ geometry
def seg_int(p, p2, q, q2):
    """Proper intersection point of two segments, or None."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p, p2, q, q2
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if d == 0:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / d
    if not (0.0 <= t <= 1.0 and 0.0 <= u <= 1.0):
        return None
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1), t)


def ring_walk(ring, i, ti, j, tj):
    """Length along `ring` from point (edge i, fraction ti) to (edge j, tj),
    walking forward with wrap-around.  `ring` is a closed list of points."""
    n = len(ring)

    def pt(k, t):
        a, b = ring[k], ring[(k + 1) % n]
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))

    total, k, t = 0.0, i, ti
    cur = pt(i, ti)
    guard = 0
    while True:
        guard += 1
        if guard > 4 * n + 8:
            return None
        nxt_i = (k + 1) % n
        end = ring[nxt_i]
        if k == j and tj >= t:
            e = pt(j, tj)
            return total + math.dist(cur, e)
        total += math.dist(cur, end)
        cur, k, t = end, nxt_i, 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--haul", type=Path,
                    help="a screen_plane_haul.py artifact")
    ap.add_argument("--layer", default="",
                    help="plane layer short name; taken from --haul if absent")
    ap.add_argument("--plane-net", default="GND")
    ap.add_argument("--seg", action="append", default=[],
                    help="X0,Y0,X1,Y1 in mm (instead of --haul)")
    ap.add_argument("--barrel", action="append", default=[],
                    help="X,Y,DIA in mm (instead of --haul)")
    ap.add_argument("--width", type=int, default=0, help="haul width, nm")
    ap.add_argument("--netclass", default="",
                    help="the haul's netclass, for RP5; from --haul if absent")
    ap.add_argument("--edge-ns", type=float, required=True,
                    help="RP4/RP6.  The FASTEST edge, in ns, that any admitted "
                         "crossing net carries.  No default by design")
    ap.add_argument("--fraction", type=float, default=20.0,
                    help="RP4/RP6 budget = rise_length / FRACTION")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    import pcbnew

    sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    dru_path = a.board.with_suffix(".kicad_dru")
    dru = dru_path.read_text(encoding="utf-8")
    b = pcbnew.LoadBoard(str(a.board))

    # ---------------------------------------------------------- the proposal
    segs, barrels, width, klass = [], [], a.width, a.netclass
    haul_doc = None
    if a.haul:
        haul_doc = json.loads(a.haul.read_text(encoding="utf-8"))
        if not haul_doc.get("ok"):
            raise SystemExit("%s did not close; nothing to price" % a.haul)
        if haul_doc.get("board_sha256") != sha:
            raise SystemExit("%s was measured on a different board (%s vs %s)"
                             % (a.haul, haul_doc.get("board_sha256")[:12],
                                sha[:12]))
        klass = klass or haul_doc.get("netclass", "")
        lay = a.layer
        if not lay:
            names = {t["layer"] for t in haul_doc["tracks"]}
            inner = sorted(n for n in names if n.startswith("In"))
            if len(inner) != 1:
                raise SystemExit("--layer: the haul touches %s" % sorted(names))
            lay = inner[0].split(".")[0]
        a.layer = lay
        want = a.layer + ".Cu"
        for t in haul_doc["tracks"]:
            if t["layer"] != want:
                continue
            segs.append((t["x0_mm"], t["y0_mm"], t["x1_mm"], t["y1_mm"]))
            width = width or t["width_nm"]
        for v in haul_doc["barrels"]:
            barrels.append((v["x_mm"], v["y_mm"], v["dia_nm"] / 1e6))
    for s in a.seg:
        segs.append(tuple(float(v) for v in s.split(",")))
    for s in a.barrel:
        barrels.append(tuple(float(v) for v in s.split(",")))
    if not segs:
        raise SystemExit("no plane segments: give --haul or --seg")
    if not a.layer:
        raise SystemExit("--layer is required without --haul")
    if not width:
        raise SystemExit("--width is required without --haul")

    lid = b.GetLayerID(a.layer + ".Cu")

    # ------------------------------------------------- the board's own facts
    stack = [l for l in b.GetEnabledLayers().CuStack()]
    names = [b.GetLayerName(l) for l in stack]
    if (a.layer + ".Cu") not in names:
        raise SystemExit("%s is not an enabled copper layer" % a.layer)
    k = names.index(a.layer + ".Cu")
    referenced = [names[i] for i in (k - 1, k + 1) if 0 <= i < len(names)]

    # epsilon_r comes off the BOARD's stack-up.  The worst (largest) value is
    # the slowest propagation and therefore the SHORTEST rise length and the
    # TIGHTEST budget, which is the side to err on.
    eps = []
    for line in a.board.read_text(encoding="utf-8", errors="replace").split(
            "\n"):
        t = line.strip()
        if t.startswith("(epsilon_r "):
            try:
                eps.append(float(t.split()[1].rstrip(")")))
            except ValueError:
                pass
    if not eps:
        raise SystemExit("the board publishes no epsilon_r; RP4 cannot run")
    eps_r = max(eps)
    velocity = C_MM_NS / math.sqrt(eps_r)
    rise_len = a.edge_ns * velocity
    budget = rise_len / a.fraction

    zones = [z for z in b.Zones()
             if not z.GetIsRuleArea() and z.GetNetname() == a.plane_net
             and z.IsOnLayer(lid)]
    if len(zones) != 1:
        raise SystemExit("expected exactly one %s zone on %s, found %d"
                         % (a.plane_net, a.layer, len(zones)))
    zone = zones[0]
    zclr = zone.GetLocalClearance()
    half = width / 2.0 + zclr

    # ------------------------------------------------------------- the void
    def disc(cx, cy, r, n=96):
        ps = pcbnew.SHAPE_POLY_SET()
        ch = pcbnew.VECTOR_VECTOR2I()
        for i in range(n):
            th = 2 * math.pi * i / n
            ch.append(pcbnew.VECTOR2I(int(round(cx + r * math.cos(th))),
                                      int(round(cy + r * math.sin(th)))))
        ps.AddOutline(pcbnew.SHAPE_LINE_CHAIN(ch, True))
        return ps

    void = pcbnew.SHAPE_POLY_SET()
    for (x0, y0, x1, y1) in segs:
        X0, Y0 = x0 * 1e6, y0 * 1e6
        X1, Y1 = x1 * 1e6, y1 * 1e6
        dx, dy = X1 - X0, Y1 - Y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln * half, dx / ln * half
        rect = pcbnew.SHAPE_POLY_SET()
        ch = pcbnew.VECTOR_VECTOR2I()
        for px, py in ((X0 + nx, Y0 + ny), (X1 + nx, Y1 + ny),
                       (X1 - nx, Y1 - ny), (X0 - nx, Y0 - ny)):
            ch.append(pcbnew.VECTOR2I(int(round(px)), int(round(py))))
        rect.AddOutline(pcbnew.SHAPE_LINE_CHAIN(ch, True))
        void.BooleanAdd(rect)
        void.BooleanAdd(disc(X0, Y0, half))
        void.BooleanAdd(disc(X1, Y1, half))
    for (bx, by, bd) in barrels:
        void.BooleanAdd(disc(bx * 1e6, by * 1e6, bd / 2.0 * 1e6 + zclr))

    rings = []
    for i in range(void.OutlineCount()):
        o = void.Outline(i)
        rings.append([(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6)
                      for j in range(o.PointCount())])

    # ------------------------------------------------------- RP1: severance
    poly = pcbnew.SHAPE_POLY_SET(zone.GetFilledPolysList(lid))

    def outline_of(ps, x_nm, y_nm):
        pt = pcbnew.VECTOR2I(int(x_nm), int(y_nm))
        for i in range(ps.OutlineCount()):
            sub = pcbnew.SHAPE_POLY_SET()
            sub.AddOutline(ps.Outline(i))
            for h in range(ps.HoleCount(i)):
                sub.AddHole(ps.Hole(i, h), 0)
            if sub.Collide(pt, 0):
                return i
        return None

    def areas(ps):
        out = []
        for i in range(ps.OutlineCount()):
            sub = pcbnew.SHAPE_POLY_SET()
            sub.AddOutline(ps.Outline(i))
            for h in range(ps.HoleCount(i)):
                sub.AddHole(ps.Hole(i, h), 0)
            out.append((i, sub.Area() / 1e12))
        return sorted(out, key=lambda t: -t[1])

    before = areas(poly)
    anchors = []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA" or t.GetNetname() != a.plane_net:
            continue
        p = t.GetPosition()
        i = outline_of(poly, p.x, p.y)
        if i is not None:
            anchors.append(dict(kind="via", tag="via@%.3f,%.3f"
                                % (p.x / 1e6, p.y / 1e6),
                                x=p.x, y=p.y, before=i))
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetNetname() != a.plane_net or not pad.IsOnLayer(lid):
                continue
            p = pad.GetPosition()
            i = outline_of(poly, p.x, p.y)
            if i is not None:
                anchors.append(dict(kind="pad",
                                    tag=f.GetReference() + "." +
                                        pad.GetNumber(),
                                    x=p.x, y=p.y, before=i))
    poly.BooleanSubtract(void)
    after = areas(poly)
    main = after[0][0] if after else None
    off_body = []
    for an in anchors:
        i = outline_of(poly, an["x"], an["y"])
        an["after"] = i
        if i is None or i != main:
            off_body.append(an)
    rp1 = dict(clause="RP1", name="PLANE SURVIVES",
               zone_clearance_nm=zclr, void_half_width_nm=int(half),
               outlines_before=len(before), outlines_after=len(after),
               area_before_mm2=round(sum(x[1] for x in before), 3),
               area_after_mm2=round(sum(x[1] for x in after), 3),
               anchors=len(anchors), anchors_off_body=len(off_body),
               off_body=off_body[:20],
               ok=(not off_body and len(after) <= len(before)))
    rp1["area_lost_mm2"] = round(rp1["area_before_mm2"]
                                 - rp1["area_after_mm2"], 3)

    # -------------------------------------- RP2/RP4: who crosses, and by how
    haul_pts = []
    for (x0, y0, x1, y1) in segs:
        if not haul_pts:
            haul_pts.append((x0, y0))
        haul_pts.append((x1, y1))

    def inside_void(x, y):
        return void.Collide(pcbnew.VECTOR2I(int(round(x * 1e6)),
                                            int(round(y * 1e6))), 0)

    crossings, grazes = [], []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        lname = b.GetLayerName(t.GetLayer())
        if lname not in referenced:
            continue
        s, e = t.GetStart(), t.GetEnd()
        p0 = (s.x / 1e6, s.y / 1e6)
        p1 = (e.x / 1e6, e.y / 1e6)
        hw = t.GetWidth() / 2e6
        # does the CENTRELINE cross the haul itself?
        cuts = []
        for i in range(len(haul_pts) - 1):
            r = seg_int(p0, p1, haul_pts[i], haul_pts[i + 1])
            if r:
                cuts.append(r)
        touch = any(inside_void(p0[0] + (p1[0] - p0[0]) * i / 40.0,
                                p0[1] + (p1[1] - p0[1]) * i / 40.0)
                    for i in range(41))
        if not cuts:
            if touch or inside_void(*p0) or inside_void(*p1):
                grazes.append(dict(net=t.GetNetname(),
                                   netclass=t.GetNetClassName(),
                                   layer=lname, width_mm=round(hw * 2, 4),
                                   a=[round(v, 4) for v in p0],
                                   b=[round(v, 4) for v in p1],
                                   mm=round(math.dist(p0, p1), 4),
                                   verdict="GRAZE"))
            continue
        # ENTRY AND EXIT ON THE VOID'S OWN BOUNDARY.
        #
        # KiCad stores a trace as INDEPENDENT segments, so the segment that
        # crosses the haul very often begins or ends INSIDE the void -- at a
        # corner, or at a via that sits in the slot region -- and then it hits
        # the void boundary ONCE and the arc is undefined.  Asking the segment
        # alone was this clause's first defect and it left four crossings
        # unpriced.  What is asked instead is the crossing segment's OWN LINE,
        # extended past both ends: the nearest boundary hit on each side of the
        # crossing point.  That is EXACT for a trace running straight through
        # the void -- which is what a trace crossing a 0.7 mm slot does -- and
        # everywhere else it is the trace's own direction of travel rather than
        # an assumed one.  A crossing that still cannot be resolved is reported
        # as such and FAILS RP4; it is never silently dropped.
        cx, cy = cuts[0][0], cuts[0][1]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy) or 1.0
        ux, uy = dx / ln, dy / ln
        REACH = 60.0
        far0 = (cx - ux * REACH, cy - uy * REACH)
        far1 = (cx + ux * REACH, cy + uy * REACH)
        best = None
        for ri, ring in enumerate(rings):
            n = len(ring)
            back, fwd = [], []
            for j in range(n):
                r = seg_int(far0, far1, ring[j], ring[(j + 1) % n])
                if not r:
                    continue
                # signed distance of the hit from the crossing point
                sd = (r[0] - cx) * ux + (r[1] - cy) * uy
                (fwd if sd >= 0 else back).append((abs(sd), j, r[0], r[1]))
            if not back or not fwd:
                continue
            back.sort()
            fwd.sort()
            (_, ja, xa, ya), (_, jb, xb, yb) = back[0], fwd[0]

            def frac(j, x, y):
                A, B = ring[j], ring[(j + 1) % n]
                L = math.dist(A, B) or 1.0
                return max(0.0, min(1.0, math.dist(A, (x, y)) / L))

            fa, fb = frac(ja, xa, ya), frac(jb, xb, yb)
            f = ring_walk(ring, ja, fa, jb, fb)
            g = ring_walk(ring, jb, fb, ja, fa)
            if f is None or g is None:
                continue
            chord = math.dist((xa, ya), (xb, yb))
            arc = min(f, g)
            cand = dict(ring=ri, chord_mm=round(chord, 4),
                        arc_mm=round(arc, 4),
                        detour_mm=round(arc - chord, 4),
                        entry=[round(xa, 4), round(ya, 4)],
                        exit=[round(xb, 4), round(yb, 4)])
            if best is None or cand["detour_mm"] > best["detour_mm"]:
                best = cand
        kls = t.GetNetClassName()
        rec = dict(net=t.GetNetname(), netclass=kls, layer=lname,
                   width_mm=round(hw * 2, 4),
                   a=[round(v, 4) for v in p0], b=[round(v, 4) for v in p1],
                   mm=round(math.dist(p0, p1), 4), verdict="CROSS",
                   reference_critical=kls in REFERENCE_CRITICAL)
        rec.update(best or dict(detour_mm=None,
                                why="the centreline crosses the haul but not "
                                    "the void boundary twice"))
        crossings.append(rec)

    # merge crossings that are the same net on the same layer: a polyline
    # crossing a slot is one crossing, however many segments KiCad stores it in
    rp2 = dict(clause="RP2", name="REFERENCE INVENTORY",
               plane=a.layer + ".Cu", references=referenced,
               crossings=len(crossings), grazes=len(grazes),
               crossing_nets=sorted({c["net"] for c in crossings}),
               grazing_nets=sorted({g["net"] for g in grazes}),
               detail=sorted(crossings, key=lambda c: (c["net"], c["a"])),
               graze_detail=sorted(grazes, key=lambda g: (g["net"], g["a"])),
               ok=True)

    refused = [c for c in crossings if c["reference_critical"]]
    missing_cites = sorted(
        k for k, (cite, _w) in REFERENCE_CRITICAL.items() if cite not in dru)
    board_classes = set()
    for t in b.GetTracks():
        board_classes.add(t.GetNetClassName())
    unknown = sorted(k for k in REFERENCE_CRITICAL if k not in board_classes)
    rp3 = dict(clause="RP3", name="CLASS REFUSAL",
               reference_critical_classes=sorted(REFERENCE_CRITICAL),
               citations={k: v[0] for k, v in REFERENCE_CRITICAL.items()},
               citations_missing_from_dru=missing_cites,
               classes_absent_from_board=unknown,
               refused=[dict(net=c["net"], netclass=c["netclass"],
                             layer=c["layer"], detour_mm=c["detour_mm"],
                             why=REFERENCE_CRITICAL[c["netclass"]][1])
                        for c in refused],
               ok=(not refused and not missing_cites))

    over = [c for c in crossings
            if not c["reference_critical"]
            and (c["detour_mm"] is None or c["detour_mm"] > budget)]
    rp4 = dict(clause="RP4", name="DETOUR BUDGET",
               epsilon_r=eps_r, velocity_mm_per_ns=round(velocity, 3),
               edge_ns=a.edge_ns, fraction=a.fraction,
               rise_length_mm=round(rise_len, 3),
               budget_mm=round(budget, 3),
               worst_admitted_detour_mm=max(
                   [c["detour_mm"] for c in crossings
                    if not c["reference_critical"]
                    and c["detour_mm"] is not None] or [0.0]),
               over_budget=[dict(net=c["net"], layer=c["layer"],
                                 detour_mm=c["detour_mm"]) for c in over],
               ok=not over)

    # ------------------------------------------------- RP5: the haul's own
    # THE FLANK IS FOUND, NOT ASSUMED.  Sampling one fixed offset either side
    # was this clause's second defect: it reported `outline: null` -- no plane
    # copper at that point -- as a SPLIT, when the two are opposite findings.
    # A haul running through a region where the plane already has no copper
    # cuts nothing there and owes nothing; a haul with copper on both sides
    # that belongs to two DIFFERENT outlines is the real fault, because then
    # the "return path" beside the signal is not the same conductor.  So each
    # side is walked outward on a ladder and the FIRST copper found is the
    # flank, with three honest outcomes instead of one.
    LADDER = [0.02, 0.05, 0.10, 0.20, 0.40, 0.80, 1.20, 1.60, 2.00]
    flanks, flank_bad = [], []
    for i in range(len(haul_pts) - 1):
        (x0, y0), (x1, y1) = haul_pts[i], haul_pts[i + 1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        base = half / 1e6
        pair = []
        for sgn in (1, -1):
            found = None
            for frac_t in (0.25, 0.5, 0.75):
                mx = x0 + (x1 - x0) * frac_t
                my = y0 + (y1 - y0) * frac_t
                for step in LADDER:
                    px = mx + nx * (base + step) * sgn
                    py = my + ny * (base + step) * sgn
                    oi = outline_of(poly, px * 1e6, py * 1e6)
                    if oi is not None:
                        found = dict(x=round(px, 4), y=round(py, 4),
                                     outline=oi, at_mm=round(step, 3))
                        break
                if found:
                    break
            pair.append(found)
        both = pair[0] is not None and pair[1] is not None
        if both:
            state = ("BONDED" if pair[0]["outline"] == pair[1]["outline"]
                     == main else "SPLIT")
        elif pair[0] is None and pair[1] is None:
            state = "NO_FLANK"
        else:
            side = pair[0] or pair[1]
            state = "ONE_SIDED" if side["outline"] == main else "SPLIT"
        rec = dict(seg=i, state=state, flanks=pair)
        flanks.append(rec)
        if state == "SPLIT":
            flank_bad.append(rec)
    rp5 = dict(clause="RP5", name="THE HAUL'S OWN RETURN",
               haul_netclass=klass,
               haul_reference_critical=klass in REFERENCE_CRITICAL,
               flank_ladder_mm=LADDER,
               states={s: sum(1 for f in flanks if f["state"] == s)
                       for s in ("BONDED", "ONE_SIDED", "NO_FLANK", "SPLIT")},
               flanks=flanks, flanks_split=len(flank_bad),
               ok=(klass not in REFERENCE_CRITICAL and not flank_bad))

    # ---------------------------------------- RP6: transfer at the barrels
    # Which plane does each OUTER end of the haul reference?  The layer
    # adjacent to it in the stack -- the same rule RP2 uses, applied the other
    # way round.
    outer_layers = sorted({t["layer"] for t in (haul_doc or {}).get(
        "tracks", []) if not t["layer"].startswith("In")})
    end_refs = []
    for lname in outer_layers:
        i = names.index(lname)
        end_refs += [names[j] for j in (i - 1, i + 1) if 0 <= j < len(names)]
    end_refs = sorted(set(end_refs) & {n for n in names
                                       if n.startswith("In")})
    transfer_needed = bool(end_refs) and (a.layer + ".Cu") not in end_refs
    bar = []
    for (bx, by, bd) in barrels:
        best = None
        for t in b.GetTracks():
            if t.GetClass() != "PCB_VIA" or t.GetNetname() != a.plane_net:
                continue
            p = t.GetPosition()
            d = math.hypot(p.x / 1e6 - bx, p.y / 1e6 - by)
            if best is None or d < best[0]:
                best = (d, round(p.x / 1e6, 4), round(p.y / 1e6, 4))
        bar.append(dict(x=bx, y=by, dia_mm=bd,
                        nearest_gnd_via_mm=round(best[0], 4) if best else None,
                        nearest_gnd_via=[best[1], best[2]] if best else None,
                        within_budget=(best is not None
                                       and best[0] <= budget)))
    rp6 = dict(clause="RP6", name="RETURN TRANSFER AT THE BARRELS",
               outer_layers=outer_layers, ends_reference=end_refs,
               transfer_needed=transfer_needed, budget_mm=round(budget, 3),
               barrels=bar,
               ok=((not transfer_needed)
                   or all(x["within_budget"] for x in bar)))

    clauses = [rp1, rp2, rp3, rp4, rp5, rp6]
    ok = all(c["ok"] for c in clauses)
    after_sha = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(schema=1, board=str(a.board), board_sha256=sha,
               authoritative_unchanged=(sha == after_sha),
               question=("what does a signal SLOT on a reserved GND plane "
                         "cost the RETURN PATH of every trace that references "
                         "that plane"),
               method=("read-only.  The layers a plane references are the "
                       "copper layers adjacent to it in the board's own "
                       "stack-up; the void is the haul stroked at the ZONE's "
                       "own clearance plus an anti-pad at every barrel; a "
                       "CROSS is a centreline that cuts the haul, and its "
                       "detour is the shorter void-boundary arc between entry "
                       "and exit minus the chord.  epsilon_r is read from the "
                       "board stack-up; the edge rate is stated by the caller "
                       "and never defaulted"),
               haul=str(a.haul) if a.haul else None,
               layer=a.layer, plane_net=a.plane_net,
               haul_netclass=klass, haul_width_nm=width,
               plane_references=referenced,
               segments=[[round(v, 4) for v in s] for s in segs],
               barrels=[[round(v, 4) for v in x] for x in barrels],
               clauses=clauses, verdict="PASS" if ok else "FAIL")
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    for c in clauses:
        print("  %-4s %-32s %s" % (c["clause"], c["name"],
                                   "PASS" if c["ok"] else "FAIL"),
              file=sys.stderr)
    print(" %s slot on %s: %d CROSS, %d GRAZE, worst admitted detour "
          "%.3f mm against a %.3f mm budget -> %s"
          % (klass or "?", a.layer, len(crossings), len(grazes),
             rp4["worst_admitted_detour_mm"], budget,
             doc["verdict"]), file=sys.stderr, flush=True)
    for c in rp3["refused"]:
        print("   REFUSED %-28s %-10s %s" % (c["net"], c["netclass"],
                                             c["why"]), file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
