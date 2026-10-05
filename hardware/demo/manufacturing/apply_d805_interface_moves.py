#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-805 interface moves: J3 / J2 / SW9 to `interface_datums.json`.

Stage 1 of D-805 (the route is stage 2, `route_maze_batch.py` + hand copper):

    * J3, J2 and SW9 are put at the datum-file position and rotation;
    * the two J3 VBUS POFV rule areas follow their pads (A4 / A9);
    * Edge.Cuts gets the two declared bottom tabs to Y 151 (concave fillet
      r 1.0, convex corner r 0.5), nothing else of the outline changes;
    * copper of the moved parts' nets is ripped ONLY inside each part's local
      window (old courtyard U new courtyard, inflated), and dangling remnants
      inside the same window are swept until none is left.  Nothing outside a
      window is touched.

    python3 apply_d805_interface_moves.py IN.kicad_pcb OUT.kicad_pcb [-o REPORT.json]

Never run this against the live project directory (pcbnew.Save rewrites the
sibling .kicad_pro): build in a scratch copy and cp only the .kicad_pcb.
"""
import argparse
import json
import math
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
DATUMS = HERE / "interface_datums.json"
MM = 1_000_000


def nm(v):
    return int(round(v * MM))


def V(x, y):
    return pcbnew.VECTOR2I(nm(x), nm(y))


# rip windows (mm, x0 y0 x1 y1) -- old courtyard U new courtyard, + ~1 mm
WINDOWS = {
    "J3": (35.0, 137.5, 52.0, 151.0),
    "J2": (6.3, 127.0, 23.7, 151.0),
    "SW9": (63.3, 83.3, 64.6, 89.7),      # the old land row only: two pad stubs
}
# nets whose whole copper is J3-local (connector <-> one passive / ESD part)
J3_LOCAL_NETS = ("Net-(J3-CC1)", "Net-(J3-CC2)", "/01_POWER_TREE/USB_D_CONN_P",
                 "/01_POWER_TREE/USB_D_CONN_N", "Net-(J3-SHIELD)")


def inside(w, p):
    return w[0] <= p.x / MM <= w[2] and w[1] <= p.y / MM <= w[3]


def outline(board, tabs, main_y=148.0, east=72.0):
    """Replace the single bottom edge line with the tabbed polyline."""
    bottom = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts
              and d.GetShape() == pcbnew.SHAPE_T_SEGMENT
              and abs(d.GetStart().y / MM - main_y) < 1e-6 and abs(d.GetEnd().y / MM - main_y) < 1e-6]
    assert len(bottom) == 1, bottom
    width = bottom[0].GetWidth()
    board.Delete(bottom[0])

    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(width)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        board.Add(s)

    def arc(c, a, b):          # centre, start, end (90 deg, KiCad picks the minor arc via mid)
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(width)
        r = math.hypot(a[0] - c[0], a[1] - c[1])
        ma = math.atan2(a[1] - c[1], a[0] - c[0])
        mb = math.atan2(b[1] - c[1], b[0] - c[0])
        d = (mb - ma + math.pi) % (2 * math.pi) - math.pi
        m = ma + d / 2
        s.SetArcGeometry(V(*a), V(c[0] + r * math.cos(m), c[1] + r * math.sin(m)), V(*b))
        board.Add(s)

    x = 0.0
    for t in sorted(tabs, key=lambda t: t["x"][0]):
        x0, x1, y = t["x"][0], t["x"][1], t["edge_y"]
        rf, rc = t["concave_fillet_r"], t["convex_corner_r"]
        seg((x, main_y), (x0 - rf, main_y))
        arc((x0 - rf, main_y + rf), (x0 - rf, main_y), (x0, main_y + rf))
        seg((x0, main_y + rf), (x0, y - rc))
        arc((x0 + rc, y - rc), (x0, y - rc), (x0 + rc, y))
        seg((x0 + rc, y), (x1 - rc, y))
        arc((x1 - rc, y - rc), (x1 - rc, y), (x1, y - rc))
        seg((x1, y - rc), (x1, main_y + rf))
        arc((x1 + rf, main_y + rf), (x1, main_y + rf), (x1 + rf, main_y))
        x = x1 + rf
    seg((x, main_y), (east, main_y))


PLANE_NETS = ("GND", "+3V3")


def rip(board, ref, nets, report):
    """Plane nets lose only their F.Cu track in the window: their stitching
    barrels stay (DRC names any barrel the moved land now lands on)."""
    w = WINDOWS[ref]
    gone = []
    for t in list(board.GetTracks()):
        if t.GetNetname() not in nets:
            continue
        if t.GetNetname() in PLANE_NETS and (t.GetClass() == "PCB_VIA" or t.GetLayer() != pcbnew.F_Cu):
            continue
        local = t.GetNetname() in J3_LOCAL_NETS
        if t.GetClass() == "PCB_VIA":
            hit = local or inside(w, t.GetPosition())
        else:
            hit = local or inside(w, t.GetStart()) or inside(w, t.GetEnd())
        if hit:
            gone.append(t)
    for t in gone:
        board.Delete(t)
    report.setdefault("ripped", {})[ref] = len(gone)
    return len(gone)


INTRUDER_CLEARANCE = 250_000


def intruders(board, report):
    """Foreign copper the moved lands / holes now land on: removed, and its
    bbox (+1 mm) returned so the dangling sweep may follow the cut."""
    moved = [board.FindFootprintByReference(r) for r in ("J3", "J2", "SW9")]
    pads = [p for f in moved for p in f.Pads()]
    gone, wins = [], []
    for t in list(board.GetTracks()):
        n = t.GetNetCode()
        for p in pads:
            if p.GetNetCode() == n and n > 0:
                continue
            hit = False
            for L in t.GetLayerSet().CuStack():
                if p.IsOnLayer(L) and t.GetEffectiveShape(L).Collide(p.GetEffectiveShape(L), INTRUDER_CLEARANCE):
                    hit = True
                    break
            if not hit and p.HasHole():
                hit = any(t.GetEffectiveShape(L).Collide(p.GetEffectiveHoleShape(), INTRUDER_CLEARANCE)
                          for L in t.GetLayerSet().CuStack())
            if hit:
                gone.append(t)
                break
    for t in gone:
        bb = t.GetBoundingBox()
        wins.append((bb.GetX() / MM - 1, bb.GetY() / MM - 1, bb.GetRight() / MM + 1, bb.GetBottom() / MM + 1))
        report.setdefault("intruders", []).append(
            [t.GetClass(), t.GetNetname(), board.GetLayerName(t.GetLayer()),
             round(bb.GetCenter().x / MM, 3), round(bb.GetCenter().y / MM, 3)])
        board.Delete(t)
    return wins


def sweep_dangling(board, windows, report):
    """Remove track ends inside a window that touch nothing of their own net."""
    total = 0
    while True:
        pads = {}
        for p in board.GetPads():
            pads.setdefault(p.GetNetCode(), []).append(p)
        vias = {}
        ends = {}
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                vias.setdefault(t.GetNetCode(), []).append(t)
            else:
                for q in (t.GetStart(), t.GetEnd()):
                    ends.setdefault((t.GetNetCode(), t.GetLayer(), q.x, q.y), []).append(t)
        dead = []
        for t in board.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            n, L = t.GetNetCode(), t.GetLayer()
            for q in (t.GetStart(), t.GetEnd()):
                if not any(inside(w, q) for w in windows):
                    continue
                if len(ends[(n, L, q.x, q.y)]) > 1:
                    continue
                if any(v.GetPosition().x == q.x and v.GetPosition().y == q.y or
                       (v.GetPosition() - q).EuclideanNorm() <= v.GetWidth(L) // 2 for v in vias.get(n, [])):
                    continue
                if any(p.IsOnLayer(L) and p.HitTest(q) for p in pads.get(n, [])):
                    continue
                # a T onto the middle of another segment of the same net
                if any(o.m_Uuid.AsString() != t.m_Uuid.AsString() and o.GetClass() == "PCB_TRACK" and o.GetLayer() == L
                       and o.GetNetCode() == n and o.HitTest(q, 1000) for o in board.GetTracks()):
                    continue
                dead.append(t)
                break
        # vias in a window that no longer touch any track/pad of their net
        for v in [v for vs in vias.values() for v in vs]:
            if not any(inside(w, v.GetPosition()) for w in windows):
                continue
            n = v.GetNetCode()
            tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetNetCode() == n
                      and t.HitTest(v.GetPosition(), v.GetWidth(pcbnew.F_Cu) // 2)]
            if not tracks and not any(p.HitTest(v.GetPosition()) for p in pads.get(n, [])):
                if not any(z.GetNetCode() == n and not z.GetIsRuleArea() for z in board.Zones()):
                    dead.append(v)
        if not dead:
            break
        for t in {t.m_Uuid.AsString(): t for t in dead}.values():
            board.Delete(t)
            total += 1
    report["swept_dangling"] = total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("-o", "--report", type=Path)
    a = ap.parse_args()
    datums = json.loads(DATUMS.read_text())
    board = pcbnew.LoadBoard(str(a.inp))
    rep = {"moves": {}}
    nets = {}
    for ref in ("J3", "J2", "SW9"):
        f = board.FindFootprintByReference(ref)
        nets[ref] = {p.GetNetname() for p in f.Pads() if p.GetNetname()}
        spec = datums["interfaces"][ref]
        was = (f.GetPosition().x / MM, f.GetPosition().y / MM, f.GetOrientationDegrees())
        f.SetOrientationDegrees(spec["rotation"])
        f.SetPosition(V(*spec["position"]))
        rep["moves"][ref] = dict(before=was, after=(spec["position"][0], spec["position"][1], spec["rotation"]))
    # POFV rule areas follow their pads
    j3 = board.FindFootprintByReference("J3")
    for z in board.Zones():
        nm_ = z.GetZoneName()
        if nm_ in ("USB_VBUS_J3_A4_POFV", "USB_VBUS_J3_A9_POFV"):
            pad = [p for p in j3.Pads() if p.GetNumber() == nm_.split("_")[3]][0]
            c = z.Outline().BBox().Centre()
            z.Move(pad.GetPosition() - c)
    outline(board, datums["outline"]["tabs"])
    # J3: GND copper is ripped only on F.Cu under the OLD body (planes keep their stitching)
    rip(board, "J3", nets["J3"] - {"GND"}, rep)
    old_j3 = (37.6, 138.4, 48.4, 147.6)
    for t in list(board.GetTracks()):
        if (t.GetNetname() == "GND" and t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu
                and (inside(old_j3, t.GetStart()) or inside(old_j3, t.GetEnd()))):
            board.Delete(t)
    rip(board, "J2", nets["J2"], rep)
    rip(board, "SW9", nets["SW9"], rep)
    extra = intruders(board, rep)
    sweep_dangling(board, list(WINDOWS.values()) + extra, rep)
    # the D-531 in-land VBUS POFV barrels move with their lands (0.35 / 0.20)
    for pad in [p for p in board.FindFootprintByReference("J3").Pads() if p.GetNumber() in ("A4", "A9")]:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pad.GetPosition())
        v.SetWidth(350_000)
        v.SetDrill(200_000)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(pad.GetNet())
        board.Add(v)
        rep.setdefault("pofv", []).append([pad.GetNumber(), pad.GetPosition().x / MM, pad.GetPosition().y / MM])
    board.Save(str(a.out))
    text = json.dumps(rep, indent=1)
    if a.report:
        a.report.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
