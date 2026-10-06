#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- D-806 JLCPCB manufacturing-readiness corrections.

Three local geometry corrections answering the JLCPCB engineering review of
2026-10-06, and nothing else:

  G1  J2 (Molex 5025700893) translated by (0, J2_DY) -- inward.  Every track
      end that lies on a J2 land moves with that land, so each J2 connection
      is the same track, shortened.  The outline is NOT touched: the D-805
      J2 tab, its fillets and the tab-to-wall gap stay exactly as drawn.
  G2  U9 (ST25R3916, VFQFPN32) corner-land HEEL trim: the eight lands that
      meet another land at a package corner (1, 8, 9, 16, 17, 24, 25, 32)
      are shortened by HEEL_TRIM at the end that faces the package centre.
      Toe, width, pitch, every other land and the footprint pose are
      unchanged.  The library master carries the same trim
      (`libraries/AQROOT_Beta.pretty/ST25R3916_AQET.kicad_mod`).
  G3  Every via whose outer diameter is less than its hole + 0.20 mm grows to
      hole + 0.20 mm.  Drills do not change.

Zones are then filled until a further fill changes nothing.

    python3 apply_d806_jlc_corrections.py IN.kicad_pcb OUT.kicad_pcb [-o REPORT.json]

Never run this against the live project directory (pcbnew.SaveBoard rewrites
the sibling .kicad_pro): build in a scratch copy of the WHOLE project and copy
back only the .kicad_pcb.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew

MM = 1_000_000
J2_DY = -0.150                     # mm, KiCad +Y is down: negative = inward
HEEL_TRIM = 0.030                  # mm per corner land
U9_CORNER_LANDS = ("1", "8", "9", "16", "17", "24", "25", "32")
JLC_OUTER_MINUS_HOLE = 0.200       # mm


def nm(v):
    return int(round(v * MM))


def mm(v):
    return v / MM


def j2_move(board, rep):
    fp = board.FindFootprintByReference("J2")
    pads = list(fp.Pads())
    d = pcbnew.VECTOR2I(0, nm(J2_DY))
    moved = []
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_TRACE_T:
            continue
        for which in ("start", "end"):
            _pt = t.GetStart() if which == "start" else t.GetEnd()
            pt = pcbnew.VECTOR2I(int(_pt.x), int(_pt.y))
            hit = [p for p in pads if p.IsOnLayer(t.GetLayer()) and p.HitTest(pt)]
            if not hit:
                continue
            new = pcbnew.VECTOR2I(pt.x + d.x, pt.y + d.y)
            (t.SetStart if which == "start" else t.SetEnd)(new)
            moved.append({"net": t.GetNetname(), "layer": t.GetLayerName(),
                          "pad": f"J2.{hit[0].GetNumber()}", "end": which,
                          "from": [round(mm(pt.x), 4), round(mm(pt.y), 4)],
                          "to": [round(mm(new.x), 4), round(mm(new.y), 4)]})
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and any(p.HitTest(t.GetPosition()) for p in pads):
            raise SystemExit("J2 land carries a via; G1 assumes none")
    _old = fp.GetPosition()
    old = pcbnew.VECTOR2I(int(_old.x), int(_old.y))
    fp.SetPosition(pcbnew.VECTOR2I(old.x + d.x, old.y + d.y))
    rep["G1_j2"] = {"delta_mm": [0.0, J2_DY],
                    "from": [mm(old.x), mm(old.y)],
                    "to": [mm(fp.GetPosition().x), mm(fp.GetPosition().y)],
                    "rotation_deg": fp.GetOrientationDegrees(),
                    "track_ends_moved": moved}


def u9_trim(board, rep):
    fp = board.FindFootprintByReference("U9")
    c = fp.GetPosition()
    out = []
    for p in fp.Pads():
        if p.GetNumber() not in U9_CORNER_LANDS:
            continue
        L = pcbnew.F_Cu
        _sz = p.GetSize(L)
        sz = pcbnew.VECTOR2I(int(_sz.x), int(_sz.y))     # a copy: GetSize is live
        _pos = p.GetPosition()
        pos = pcbnew.VECTOR2I(int(_pos.x), int(_pos.y))
        horiz = sz.x > sz.y
        long_ = sz.x if horiz else sz.y
        if abs(mm(long_) - 0.75) > 1e-6:
            raise SystemExit(f"U9.{p.GetNumber()} long side {mm(long_)} != 0.75")
        new_long = long_ - nm(HEEL_TRIM)
        # the heel is the end toward the package centre: shift the centre AWAY
        if horiz:
            sgn = 1 if pos.x > c.x else -1
            npos = pcbnew.VECTOR2I(pos.x + sgn * nm(HEEL_TRIM / 2), pos.y)
            nsz = pcbnew.VECTOR2I(new_long, sz.y)
        else:
            sgn = 1 if pos.y > c.y else -1
            npos = pcbnew.VECTOR2I(pos.x, pos.y + sgn * nm(HEEL_TRIM / 2))
            nsz = pcbnew.VECTOR2I(sz.x, new_long)
        p.SetSize(L, nsz)
        p.SetPosition(npos)
        out.append({"pad": f"U9.{p.GetNumber()}", "net": p.GetNetname(),
                    "size_from": [mm(sz.x), mm(sz.y)], "size_to": [mm(nsz.x), mm(nsz.y)],
                    "centre_from": [round(mm(pos.x), 4), round(mm(pos.y), 4)],
                    "centre_to": [round(mm(npos.x), 4), round(mm(npos.y), 4)]})
    if len(out) != 8:
        raise SystemExit(f"expected 8 U9 corner lands, trimmed {len(out)}")
    rep["G2_u9"] = {"heel_trim_mm": HEEL_TRIM, "lands": out}


def via_grow(board, rep):
    out = []
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        d, h = t.GetWidth(pcbnew.F_Cu), t.GetDrillValue()
        want = h + nm(JLC_OUTER_MINUS_HOLE)
        if d < want:
            t.SetWidth(pcbnew.F_Cu, want)
            out.append({"net": t.GetNetname(),
                        "at": [round(mm(t.GetPosition().x), 4), round(mm(t.GetPosition().y), 4)],
                        "dia_from": mm(d), "dia_to": mm(want), "drill": mm(h)})
    rep["G3_vias"] = {"rule": "outer >= hole + 0.200 mm", "grown": out, "count": len(out)}


def fill_to_fixed_point(board, path, rep):
    filler = pcbnew.ZONE_FILLER(board)
    digests = []
    for i in range(6):
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(path, board)
        digests.append(hashlib.sha256(Path(path).read_bytes()).hexdigest())
        if len(digests) >= 2 and digests[-1] == digests[-2]:
            break
    else:
        raise SystemExit("zone fill did not reach a fixed point")
    rep["fill"] = {"passes": len(digests), "fixed_point_sha256": digests[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(a.src)
    rep = {"decision": "D-806", "src_sha256": hashlib.sha256(Path(a.src).read_bytes()).hexdigest()}
    j2_move(board, rep)
    u9_trim(board, rep)
    via_grow(board, rep)
    fill_to_fixed_point(board, a.dst, rep)
    rep["dst_sha256"] = hashlib.sha256(Path(a.dst).read_bytes()).hexdigest()
    txt = json.dumps(rep, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(txt + "\n")
    print(json.dumps({k: (v if k != "G3_vias" else v["count"]) for k, v in rep.items()
                      if k not in ("G1_j2", "G2_u9")}, indent=1))


if __name__ == "__main__":
    main()
