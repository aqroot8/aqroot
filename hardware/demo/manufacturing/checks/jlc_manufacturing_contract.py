#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the JLCPCB MANUFACTURING-READINESS contract (JLC1-JLC6), D-806.

WHY.  JLCPCB's engineering review of 2026-10-06 raised five CAM/DFA findings
on the D-805 package that no standing gate could see, because each one is a
VENDOR figure rather than a property this board's own rules ask about:

    JLC1  J2 microSD shell lands to the routed edge >= 0.25 mm (non-V-cut
          edge; HARD), D-806 target >= 0.30 mm.  Measured on the BOARD
          (land polygons vs the board outline) and on the GERBERS (F_Cu J2
          flashes vs an arc-aware read of Edge_Cuts).
    JLC2  U9 pre-CAM different-net copper gap >= 5.2 mil (HARD; JLCPCB: what
          holds 4.0 mil after their CAM), target >= 6.0 mil, measured on the
          BOARD over every copper layer inside U9's courtyard + 1.0 mm.
    JLC3  The same question asked of the GERBERS, independent of KiCad:
          U9 window minimum >= 5.2 mil HARD (>= 6.0 target), raw >= 4.0 mil
          HARD, modelled post-CAM (raw - 1.2 mil, JLCPCB's own 5.2 -> 4.0)
          >= 4.0 mil HARD, and BOARD-WIDE no different-net gap < 5.2 mil.
    JLC4  Via outer diameter >= hole + 0.20 mm.  POPULATION: every via on the
          board (KiCad `PCB_VIA`), and independently every Excellon PTH round
          hit that carries an F_Cu or B_Cu `ViaPad` flash.  Plated component
          holes are reported separately (all meet it today).
    JLC5  Reference-designator mapping: the package's reference index and
          locator drawings name EVERY fitted CPL reference exactly once, at the
          CPL coordinates, on the CPL side, matching the board footprint; no
          DNP reference is presented as fitted; each locator PDF carries every
          reference of its side, the release and the board sha256.
    JLC6  Profile identity: the board's Edge.Cuts primitives equal the declared
          profile (`board_profile_spec.json`), equal the frozen D-805 profile,
          are reproduced by the Edge_Cuts Gerber, and are what the packaged
          profile JSON states.

Every clause carries destructive controls: the frozen D-805 inputs (read from
git at the D-805 delivery commit) must FAIL JLC1-JLC4, and in-memory
mutations of the D-806 inputs must FAIL each clause.

    python3 checks/jlc_manufacturing_contract.py [--board B] [--package DIR]
        [--d805-ref COMMIT] [-o OUT.json]

Requires shapely (the same dependency as the independent Gerber extractor).
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, nearest_points
from shapely import affinity

HERE = Path(__file__).resolve().parent
MFG = HERE.parent
ROOT = HERE.parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
PACKAGE = ROOT / "hardware/demo/fab"
SPEC = MFG / "board_profile_spec.json"
D805_REF = "a8837f71667f2f737c69dab47b33dd410bdbd7e7"   # frozen D-805 delivery identity
MIL = 0.0254
J2_HARD, J2_TARGET = 0.25, 0.30
U9_HARD_MIL, U9_TARGET_MIL, POST_CAM_MIL, CAM_LOSS_MIL = 5.2, 6.0, 4.0, 1.2
VIA_RULE = 0.20
NM = 1e6
COPPER = [("F.Cu", "F_Cu"), ("In1.Cu", "In1_Cu"), ("In2.Cu", "In2_Cu"),
          ("In3.Cu", "In3_Cu"), ("In4.Cu", "In4_Cu"), ("B.Cu", "B_Cu")]


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _gcam():
    spec = importlib.util.spec_from_file_location(
        "gcam", MFG / "evidence/d804-gerber-cam-extract.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


GCAM = _gcam()


# --------------------------------------------------------------------------
# frozen D-805 inputs, from git
# --------------------------------------------------------------------------
def git_tree(ref, paths, dest):
    dest.mkdir(parents=True, exist_ok=True)
    for rel in paths:
        out = dest / Path(rel).name
        data = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (ref, rel)],
                              capture_output=True, check=True).stdout
        out.write_bytes(data)
    return dest


def d805_inputs(ref, tmp):
    proj = "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2"
    b = git_tree(ref, [proj + ".kicad_pcb", proj + ".kicad_pro", proj + ".kicad_dru"], tmp / "board")
    names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", ref,
                            "hardware/demo/fab/gerbers/"], capture_output=True, text=True,
                           check=True).stdout.split()
    g = git_tree(ref, [n for n in names if n.endswith((".gbr", ".drl"))], tmp / "gerbers")
    return b / "aqroot-Beta-v2.kicad_pcb", g


# --------------------------------------------------------------------------
# board geometry -> shapely
# --------------------------------------------------------------------------
def ps_to_shapely(ps):
    polys = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        shell = [(o.CPoint(k).x / NM, o.CPoint(k).y / NM) for k in range(o.PointCount())]
        holes = []
        for h in range(ps.HoleCount(i)):
            hc = ps.Hole(i, h)
            holes.append([(hc.CPoint(k).x / NM, hc.CPoint(k).y / NM) for k in range(hc.PointCount())])
        if len(shell) >= 3:
            polys.append(Polygon(shell, holes).buffer(0))
    return unary_union(polys) if polys else None


def item_poly(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, 0, 500, pcbnew.ERROR_OUTSIDE)
    return ps_to_shapely(ps)


def board_outline(board):
    ps = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ps, False)
    return ps_to_shapely(ps)


def copper_in_window(board, layer_name, win):
    """net -> union of copper inside `win` (shapely box, KiCad mm).  A pad with no
    net is its OWN island (an unconnected pin is a different conductor)."""
    lay = board.GetLayerID(layer_name)
    wb = pcbnew.BOX2I(pcbnew.VECTOR2I(int(win.bounds[0] * NM), int(win.bounds[1] * NM)),
                      pcbnew.VECTOR2L(int((win.bounds[2] - win.bounds[0]) * NM),
                                      int((win.bounds[3] - win.bounds[1]) * NM)))
    by = {}

    def put(key, g):
        if g is None or g.is_empty:
            return
        g = g.intersection(win.buffer(0.5))
        if not g.is_empty:
            by.setdefault(key, []).append(g)
    for f in board.GetFootprints():
        if not f.GetBoundingBox(False).Intersects(wb):
            continue
        for p in f.Pads():
            if p.IsOnLayer(lay) and p.GetBoundingBox().Intersects(wb):
                key = p.GetNetname() or "<nonet:%s.%s>" % (f.GetReference(), p.GetNumber())
                put(key, item_poly(p, lay))
    for t in board.GetTracks():
        if t.IsOnLayer(lay) and t.GetBoundingBox().Intersects(wb):
            put(t.GetNetname() or "<nonet:track>", item_poly(t, lay))
    for z in board.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lay) or not z.GetBoundingBox().Intersects(wb):
            continue
        put(z.GetNetname() or "<nonet:zone>", ps_to_shapely(z.GetFilledPolysList(lay)))
    return {k: unary_union(v) for k, v in by.items()}


def min_diff_net_gap(nets):
    names = sorted(nets)
    best = None
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = nets[a].distance(nets[b])
            if best is None or d < best[0]:
                p, q = nearest_points(nets[a], nets[b])
                best = (d, a, b, (round(p.x, 4), round(p.y, 4)))
    return best


def u9_window(board):
    f = board.FindFootprintByReference("U9")
    lay = pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd
    bb = f.GetCourtyard(lay).BBox()
    return box(bb.GetLeft() / NM - 1.0, bb.GetTop() / NM - 1.0,
               bb.GetRight() / NM + 1.0, bb.GetBottom() / NM + 1.0)


# --------------------------------------------------------------------------
# JLC1  J2 shell lands to the routed edge
# --------------------------------------------------------------------------
def jlc1_board(board):
    edge = board_outline(board).boundary
    f = board.FindFootprintByReference("J2")
    rows = []
    for p in f.Pads():
        if not p.IsOnLayer(pcbnew.F_Cu):
            continue
        g = item_poly(p, pcbnew.F_Cu)
        rows.append(dict(pad="J2.%s" % p.GetNumber(), net=p.GetNetname(),
                         at=[round(p.GetPosition().x / NM, 4), round(p.GetPosition().y / NM, 4)],
                         to_edge_mm=round(g.distance(edge), 4)))
    shell = [r for r in rows if r["pad"] == "J2.9"]
    m_shell = min(r["to_edge_mm"] for r in shell)
    m_all = min(r["to_edge_mm"] for r in rows)
    return dict(ok=m_shell >= J2_HARD - 1e-6 and m_all >= J2_HARD - 1e-6,
                target_met=m_shell >= J2_TARGET - 1e-6,
                shell_land_to_edge_min_mm=m_shell, any_j2_land_to_edge_min_mm=m_all,
                hard_mm=J2_HARD, target_mm=J2_TARGET,
                shell_lands=sorted(shell, key=lambda r: r["at"]))


def edge_gerber_geometry(path):
    """Arc-aware Edge_Cuts read: the profile as a list of centreline points."""
    x = y = 0.0
    mode = "G01"
    segs = []
    for raw in Path(path).read_text().splitlines():
        ln = raw.strip()
        for g in ("G01", "G02", "G03"):
            if ln.startswith(g):
                mode = g
                ln = ln[3:]
        m = re.match(r"^(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])\*$", ln)
        if not m:
            continue
        nx = int(m.group(1)) / 1e6 if m.group(1) else x
        ny = int(m.group(2)) / 1e6 if m.group(2) else y
        if m.group(5) == "1":
            if mode == "G01":
                segs.append(dict(kind="line", a=(x, y), b=(nx, ny), pts=[(x, y), (nx, ny)]))
            else:
                cx = x + (int(m.group(3)) / 1e6 if m.group(3) else 0.0)
                cy = y + (int(m.group(4)) / 1e6 if m.group(4) else 0.0)
                r = math.hypot(x - cx, y - cy)
                a0 = math.atan2(y - cy, x - cx)
                a1 = math.atan2(ny - cy, nx - cx)
                sw = (a1 - a0) % (2 * math.pi)
                if mode == "G02":                     # clockwise
                    sw = sw - 2 * math.pi if sw > 0 else sw
                pts = [(cx + r * math.cos(a0 + sw * k / 32), cy + r * math.sin(a0 + sw * k / 32))
                       for k in range(33)]
                segs.append(dict(kind="arc", a=(x, y), b=(nx, ny), centre=(cx, cy), radius=r, pts=pts))
        x, y = nx, ny
    return segs


def jlc1_gerber(gdir):
    edges = edge_gerber_geometry(next(Path(gdir).glob("*Edge_Cuts.gbr")))
    edge = unary_union([LineString(s["pts"]) for s in edges])
    g = GCAM.parse_gerber(next(Path(gdir).glob("*F_Cu.gbr")))
    # KiCad tags pads with %TO.P,REF,PIN only (no %TO.C), so the pin field names the part
    shell = [f for f in g["flashes"] if (f["pin"] or "").split(",")[:2] == ["J2", "9"]]
    allj2 = [f for f in g["flashes"] if (f["pin"] or "").split(",")[0] == "J2"]
    if not shell:
        return dict(ok=False, why="no J2 pin-9 flash in F_Cu")
    m_shell = min(f["geom"].distance(edge) for f in shell)
    m_all = min(f["geom"].distance(edge) for f in allj2)
    return dict(ok=m_shell >= J2_HARD - 1e-6 and m_all >= J2_HARD - 1e-6,
                target_met=m_shell >= J2_TARGET - 1e-6, shell_flashes=len(shell),
                shell_land_to_edge_min_mm=round(m_shell, 4),
                any_j2_flash_to_edge_min_mm=round(m_all, 4))


# --------------------------------------------------------------------------
# JLC2  U9 pre-CAM gap, board
# --------------------------------------------------------------------------
def jlc2(board):
    win = u9_window(board)
    rows, best = {}, None
    for lname, _ in COPPER:
        nets = copper_in_window(board, lname, win)
        b = min_diff_net_gap(nets)
        if b is None:
            continue
        rows[lname] = dict(min_gap_mm=round(b[0], 5), min_gap_mil=round(b[0] / MIL, 3),
                           nets=[b[1], b[2]], at=b[3])
        if best is None or b[0] < best[0]:
            best = (b[0], lname)
    mil = best[0] / MIL
    return dict(ok=mil >= U9_HARD_MIL - 1e-6, target_met=mil >= U9_TARGET_MIL - 1e-6,
                window_kicad_mm=[round(v, 3) for v in win.bounds],
                min_gap_mm=round(best[0], 5), min_gap_mil=round(mil, 3), min_layer=best[1],
                hard_mil=U9_HARD_MIL, target_mil=U9_TARGET_MIL, per_layer=rows)


# --------------------------------------------------------------------------
# JLC3  the same, from the Gerbers; plus the board-wide floor
# --------------------------------------------------------------------------
def gerber_nets(g, win=None):
    items = [(d["geom"], GCAM.nn(d["net"])) for d in g["draws"]]
    items += [(f["geom"], GCAM.nn(f["net"]), f) for f in g["flashes"]]
    items += [(r["geom"], GCAM.nn(r["net"])) for r in g["regions"]]
    by, k = {}, 0
    for it in items:
        geom, net = it[0], it[1]
        if win is not None:
            if not geom.intersects(win.buffer(0.5)):
                continue
            geom = geom.intersection(win.buffer(0.5))
        if net is None:
            comp = it[2]["comp"] if len(it) > 2 else None
            pin = it[2]["pin"] if len(it) > 2 else None
            net = "<nonet:%s:%s>" % (pin, k) if pin else "<nonet:%d>" % k
            k += 1
        by.setdefault(net, []).append(geom)
    return {n: unary_union(v) for n, v in by.items()}


def gerber_u9_min(gdir, board_win, mutate=None):
    win = affinity.scale(board_win, 1.0, -1.0, origin=(0, 0))       # KiCad -> Gerber frame
    best = None
    for _, gl in COPPER:
        g = GCAM.parse_gerber(next(Path(gdir).glob("*%s.gbr" % gl)))
        if mutate:
            mutate(gl, g)
        nets = gerber_nets(g, win)
        b = min_diff_net_gap(nets)
        if b and (best is None or b[0] < best[0]):
            best = (b[0], gl, b[1], b[2], (b[3][0], -b[3][1]))
    return best


def board_wide_gaps(gdir, mil):
    with tempfile.TemporaryDirectory(prefix="aqroot-jlc3-") as t:
        out = Path(t) / "cam.json"
        subprocess.run([sys.executable, str(MFG / "evidence/d804-gerber-cam-extract.py"), str(gdir),
                        "--gap-mil", str(mil), "--json", str(out)], capture_output=True, check=True)
        d = json.loads(out.read_text())
    gaps = [dict(layer=L, **q) for L, v in d["layers"].items() for q in v["gaps_below"]]
    shorts = sum(len(v["shorts"]) for v in d["layers"].values())
    opens = sum(len(v["open_ends"]) for v in d["layers"].values())
    return gaps, dict(shorts=shorts, open_ends=opens,
                      split_nets=d["netlist"]["split_nets"],
                      multi_net_components=d["netlist"]["multi_net_components"])


def jlc3(gdir, board_win):
    b = gerber_u9_min(gdir, board_win)
    raw = b[0] / MIL
    gaps, health = board_wide_gaps(gdir, U9_TARGET_MIL)
    below_hard = [g for g in gaps if g["gap_mil"] < U9_HARD_MIL - 1e-6]
    return dict(ok=(raw >= U9_HARD_MIL - 1e-6 and raw >= POST_CAM_MIL - 1e-6
                    and raw - CAM_LOSS_MIL >= POST_CAM_MIL - 1e-6 and not below_hard
                    and health["shorts"] == 0),
                target_met=raw >= U9_TARGET_MIL - 1e-6,
                u9_window_min_gap_mil=round(raw, 3), u9_window_min_gap_mm=round(b[0], 5),
                u9_layer=b[1], u9_nets=[b[2], b[3]], u9_at_kicad=[round(v, 4) for v in b[4]],
                modelled_post_cam_mil=round(raw - CAM_LOSS_MIL, 3),
                board_wide_gaps_below_5_2_mil=below_hard,
                board_wide_gaps_5_2_to_6_0_mil=len(gaps) - len(below_hard),
                board_wide_min_gap_mil=min((g["gap_mil"] for g in gaps), default=None),
                cam_health=health,
                note=("modelled post-CAM = raw - 1.2 mil, JLCPCB's own statement that "
                      ">= 5.2 mil pre-CAM is what holds >= 4.0 mil after their CAM"))


# --------------------------------------------------------------------------
# JLC4  via outer >= hole + 0.20 mm
# --------------------------------------------------------------------------
def jlc4_board(board):
    rows, bad = 0, []
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        rows += 1
        d, h = t.GetWidth(pcbnew.F_Cu) / NM, t.GetDrillValue() / NM
        if d - h < VIA_RULE - 1e-6:
            bad.append(dict(net=t.GetNetname(), at=[round(t.GetPosition().x / NM, 4),
                                                    round(t.GetPosition().y / NM, 4)],
                            dia=d, drill=h, outer_minus_hole=round(d - h, 4)))
    comp = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
                continue
            ds, sz = p.GetDrillSize(), p.GetSize(pcbnew.F_Cu)
            omh = min(sz.x, sz.y) / NM - min(ds.x, ds.y) / NM
            if omh < VIA_RULE - 1e-6:
                comp.append("%s.%s" % (f.GetReference(), p.GetNumber()))
    return dict(ok=not bad, population="every PCB_VIA on the board", vias=rows,
                below=len(bad), rows=bad,
                plated_component_holes_below=comp)


def jlc4_gerber(gdir):
    hits = GCAM.parse_drill(next(Path(gdir).glob("*-PTH.drl")))
    pads = []
    for gl in ("F_Cu", "B_Cu"):
        g = GCAM.parse_gerber(next(Path(gdir).glob("*%s.gbr" % gl)))
        pads += [(f["at"], f["geom"]) for f in g["flashes"] if f["func"].startswith("ViaPad")]
    idx = {}
    for at, geom in pads:
        idx.setdefault((round(at[0], 3), round(at[1], 3)), []).append(geom)
    n, bad = 0, []
    for h in hits:
        if h["a"] != h["b"]:
            continue
        key = (round(h["a"][0], 3), round(h["a"][1], 3))
        if key not in idx:
            continue
        n += 1
        outer = min(g.bounds[2] - g.bounds[0] for g in idx[key])
        if outer - h["d"] < VIA_RULE - 1e-6:
            bad.append(dict(at_kicad=[key[0], -key[1]], outer=round(outer, 4), hole=h["d"],
                            outer_minus_hole=round(outer - h["d"], 4)))
    return dict(ok=n > 0 and not bad, population="Excellon PTH round hits carrying an F_Cu/B_Cu ViaPad flash",
                via_hits=n, below=len(bad), rows=bad[:50])


# --------------------------------------------------------------------------
# JLC5  reference-designator mapping
# --------------------------------------------------------------------------
def pdf_text(p):
    x = subprocess.run(["pdftotext", "-raw", str(p), "-"], capture_output=True, text=True)
    return x.stdout if x.returncode == 0 else ""


def jlc5(board, pkg, manifest, index=None, texts=None):
    fit = list(csv.DictReader(open(pkg / "aqroot-Demo-pos-fitted.csv", newline="")))
    allr = list(csv.DictReader(open(pkg / "aqroot-Demo-pos-all.csv", newline="")))
    dnp = {r["Ref"] for r in allr} - {r["Ref"] for r in fit}
    if index is None:
        index = list(csv.DictReader(open(pkg / "aqroot-Demo-assembly-ref-index.csv", newline="")))
    vd = (manifest.get("vendor_drawings") or {}).get("locator") or {}
    files = vd.get("files") or {}
    if texts is None:
        texts = {s: pdf_text(pkg / files[s]["file"]) for s in ("top", "bottom") if s in files}
    problems = []
    seen = {}
    for r in index:
        seen[r["Ref"]] = seen.get(r["Ref"], 0) + 1
    dup = sorted(k for k, v in seen.items() if v > 1)
    if dup:
        problems.append("duplicated in index: %s" % dup)
    cpl = {r["Ref"]: r for r in fit}
    missing = sorted(set(cpl) - set(seen))
    extra = sorted(set(seen) - set(cpl))
    if missing:
        problems.append("fitted refs missing from index: %s" % missing)
    if extra:
        problems.append("index refs not in fitted CPL (DNP or unknown): %s" % extra)
    mism = []
    for r in index:
        c = cpl.get(r["Ref"])
        if not c:
            continue
        f = board.FindFootprintByReference(r["Ref"])
        bx, by = f.GetPosition().x / NM, f.GetPosition().y / NM
        side = "bottom" if f.IsFlipped() else "top"
        if (abs(float(r["CPL_X"]) - float(c["PosX"])) > 1e-6 or abs(float(r["CPL_Y"]) - float(c["PosY"])) > 1e-6
                or r["Side"] != c["Side"] or r["Side"] != side
                or abs(float(c["PosX"]) - bx) > 1e-4 or abs(-float(c["PosY"]) - by) > 1e-4):
            mism.append(r["Ref"])
    if mism:
        problems.append("index/CPL/board disagree for: %s" % mism)
    absent = {}
    for side in ("top", "bottom"):
        t = texts.get(side, "")
        toks = set(re.findall(r"(?<![A-Z0-9])[A-Z]{1,3}\d{1,3}(?![0-9])", t))
        want = [r["Ref"] for r in fit if r["Side"] == side]
        miss = [w for w in want if w not in toks]
        if miss:
            absent[side] = miss
        if manifest["source"]["board_sha256"][:32] not in t.replace("\n", ""):
            problems.append("%s locator does not carry the board sha256" % side)
    if absent:
        problems.append("refs absent from their side's locator PDF: %s" % absent)
    if not files:
        problems.append("MANIFEST names no vendor locator drawings")
    return dict(ok=not problems, fitted=len(fit), indexed=len(index), dnp=len(dnp),
                locator_files={s: files[s]["file"] for s in files} if files else None,
                problems=problems)


# --------------------------------------------------------------------------
# JLC6  profile identity
# --------------------------------------------------------------------------
def board_profile(board):
    sys.path[:0] = [str(MFG)]
    import jlc_drawings
    return jlc_drawings.outline_items(board)


def same_items(a, b, tol=1e-3):
    if len(a) != len(b):
        return False, "item count %d vs %d" % (len(a), len(b))

    def key(i):
        return (i["kind"], tuple(sorted([tuple(i["start"]), tuple(i["end"])])))
    A = sorted(a, key=key)
    B = sorted(b, key=key)
    for x, y in zip(A, B):
        if x["kind"] != y["kind"]:
            return False, "kind %s vs %s" % (x, y)
        ends_x = sorted([tuple(x["start"]), tuple(x["end"])])
        ends_y = sorted([tuple(y["start"]), tuple(y["end"])])
        if any(abs(p - q) > tol for u, v in zip(ends_x, ends_y) for p, q in zip(u, v)):
            return False, "ends %s vs %s" % (x, y)
        if x["kind"] == "arc" and (abs(x["radius"] - y["radius"]) > tol or
                                   any(abs(p - q) > tol for p, q in zip(x["centre"], y["centre"]))):
            return False, "arc %s vs %s" % (x, y)
    return True, None


def gerber_items(gdir):
    out = []
    for s in edge_gerber_geometry(next(Path(gdir).glob("*Edge_Cuts.gbr"))):
        it = dict(kind=s["kind"], start=[round(s["a"][0], 4), round(-s["a"][1], 4)],
                  end=[round(s["b"][0], 4), round(-s["b"][1], 4)])
        if s["kind"] == "arc":
            it.update(centre=[round(s["centre"][0], 4), round(-s["centre"][1], 4)], radius=round(s["radius"], 4))
        out.append(it)
    return out


def jlc6(board, d805_board, gdir, pkg, spec, items=None):
    items = board_profile(board) if items is None else items
    res = {}
    res["equals_declared_spec"], w1 = same_items(items, spec["items"])
    res["equals_frozen_d805"], w2 = same_items(items, board_profile(d805_board))
    res["reproduced_by_edge_cuts_gerber"], w3 = same_items(items, gerber_items(gdir))
    pj = pkg / "aqroot-Demo-board-profile.json"
    pdoc = json.loads(pj.read_text()) if pj.is_file() else {"items": []}
    res["packaged_profile_json_agrees"], w4 = same_items(items, pdoc["items"])
    counts = dict(lines=sum(i["kind"] == "line" for i in items), arcs=sum(i["kind"] == "arc" for i in items))
    radii = sorted({i["radius"] for i in items if i["kind"] == "arc"})
    return dict(ok=all(res.values()), **res, counts=counts, arc_radii=radii,
                why_not=[w for w in (w1, w2, w3, w4) if w])


# --------------------------------------------------------------------------
def controls(board, d805_board, d805_g, gdir, pkg, manifest, spec, win):
    c = {}
    # JLC1
    c["JLC1_frozen_D805_board_is_refused"] = not jlc1_board(d805_board)["ok"]
    c["JLC1_frozen_D805_gerbers_are_refused"] = not jlc1_gerber(d805_g)["ok"]
    j2 = board.FindFootprintByReference("J2")
    was = j2.GetPosition()
    j2.SetPosition(pcbnew.VECTOR2I(was.x, was.y + 120000))       # 0.120 mm back toward the edge
    r = jlc1_board(board)
    c["JLC1_J2_0_120_mm_outward_misses_target_or_hard"] = (not r["ok"]) or (not r["target_met"])
    j2.SetPosition(was)
    # JLC2
    c["JLC2_frozen_D805_board_is_refused"] = not jlc2(d805_board)["ok"]
    u9 = board.FindFootprintByReference("U9")
    p1 = next(p for p in u9.Pads() if p.GetNumber() == "1")
    sz, pos = p1.GetSize(pcbnew.F_Cu), p1.GetPosition()
    sz0, pos0 = pcbnew.VECTOR2I(int(sz.x), int(sz.y)), pcbnew.VECTOR2I(int(pos.x), int(pos.y))
    p32 = next(p for p in u9.Pads() if p.GetNumber() == "32")
    s32, q32 = p32.GetSize(pcbnew.F_Cu), p32.GetPosition()
    s32_0, q32_0 = pcbnew.VECTOR2I(int(s32.x), int(s32.y)), pcbnew.VECTOR2I(int(q32.x), int(q32.y))
    p1.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(750000, 300000))
    p1.SetPosition(pcbnew.VECTOR2I(pos0.x + 15000, pos0.y))
    p32.SetSize(pcbnew.F_Cu, pcbnew.VECTOR2I(300000, 750000))
    p32.SetPosition(pcbnew.VECTOR2I(q32_0.x, q32_0.y - 15000))
    c["JLC2_untrimmed_U9_corner_pair_is_refused"] = not jlc2(board)["ok"]
    p1.SetSize(pcbnew.F_Cu, sz0)
    p1.SetPosition(pos0)
    p32.SetSize(pcbnew.F_Cu, s32_0)
    p32.SetPosition(q32_0)
    # JLC3
    b = gerber_u9_min(d805_g, win)
    c["JLC3_frozen_D805_gerbers_fail_5_2_mil_and_post_cam"] = (
        b[0] / MIL < U9_HARD_MIL and b[0] / MIL - CAM_LOSS_MIL < POST_CAM_MIL)

    def squeeze(gl, g):
        if gl != "B_Cu":
            return
        for f in g["flashes"]:
            if (f["pin"] or "").split(",")[:2] == ["U9", "1"]:
                f["geom"] = affinity.translate(f["geom"], 0.06, -0.06)   # toward U9.32 (Gerber Y up)
    b = gerber_u9_min(gdir, win, squeeze)
    c["JLC3_U9_1_flash_pushed_into_its_corner_is_refused_below_4_mil"] = b[0] / MIL < POST_CAM_MIL
    # JLC4
    c["JLC4_frozen_D805_board_is_refused"] = jlc4_board(d805_board)["below"] == 35
    c["JLC4_frozen_D805_excellon_gerber_is_refused"] = jlc4_gerber(d805_g)["below"] >= 35
    v = next(t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T)
    d0 = v.GetWidth(pcbnew.F_Cu)
    v.SetWidth(pcbnew.F_Cu, v.GetDrillValue() + 150000)
    c["JLC4_one_via_at_hole_plus_0_15_is_refused"] = not jlc4_board(board)["ok"]
    v.SetWidth(pcbnew.F_Cu, d0)
    # JLC5
    index = list(csv.DictReader(open(pkg / "aqroot-Demo-assembly-ref-index.csv", newline="")))
    vd = manifest["vendor_drawings"]["locator"]["files"]
    texts = {s: pdf_text(pkg / vd[s]["file"]) for s in ("top", "bottom")}
    c["JLC5_index_missing_one_fitted_ref_is_refused"] = not jlc5(board, pkg, manifest, index[1:], texts)["ok"]
    moved = copy.deepcopy(index)
    moved[0]["CPL_X"] = "%.6f" % (float(moved[0]["CPL_X"]) + 0.5)
    c["JLC5_index_ref_0_5_mm_off_its_CPL_is_refused"] = not jlc5(board, pkg, manifest, moved, texts)["ok"]
    allr = list(csv.DictReader(open(pkg / "aqroot-Demo-pos-all.csv", newline="")))
    fitr = {r["Ref"] for r in csv.DictReader(open(pkg / "aqroot-Demo-pos-fitted.csv", newline=""))}
    d = next(r for r in allr if r["Ref"] not in fitr)
    plus = index + [dict(index[0], Ref=d["Ref"])]
    c["JLC5_a_DNP_ref_presented_as_fitted_is_refused"] = not jlc5(board, pkg, manifest, plus, texts)["ok"]
    victim = index[0]["Ref"]
    side = index[0]["Side"]
    t2 = dict(texts)
    t2[side] = re.sub(r"(?<![A-Z0-9])%s(?![0-9])" % victim, "XX", t2[side])
    c["JLC5_a_ref_missing_from_its_locator_pdf_is_refused"] = not jlc5(board, pkg, manifest, index, t2)["ok"]
    # JLC6
    items = board_profile(board)
    bad = copy.deepcopy(items)
    next(i for i in bad if i["kind"] == "arc")["radius"] += 0.1
    c["JLC6_one_fillet_radius_changed_is_refused"] = not jlc6(board, d805_board, gdir, pkg, spec, bad)["ok"]
    flat = [i for i in items if i["kind"] != "arc"]
    c["JLC6_tabs_straightened_arcs_removed_is_refused"] = not jlc6(board, d805_board, gdir, pkg, spec, flat)["ok"]
    return dict(ok=all(c.values()), controls=c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--package", type=Path, default=PACKAGE)
    ap.add_argument("--d805-ref", default=D805_REF)
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    board = pcbnew.LoadBoard(str(a.board))
    pkg = a.package
    gdir = pkg / "gerbers"
    manifest = json.loads((pkg / "MANIFEST.json").read_text())
    spec = json.loads(SPEC.read_text())
    with tempfile.TemporaryDirectory(prefix="aqroot-jlc-d805-") as t:
        d805_pcb, d805_g = d805_inputs(a.d805_ref, Path(t))
        d805_board = pcbnew.LoadBoard(str(d805_pcb))
        win = u9_window(board)
        checks = {
            "JLC1_J2_shell_land_to_routed_edge": dict(board=jlc1_board(board), gerber=jlc1_gerber(gdir)),
            "JLC2_U9_pre_cam_gap_board": jlc2(board),
            "JLC3_U9_gap_gerber_and_board_wide_floor": jlc3(gdir, win),
            "JLC4_via_outer_minus_hole": dict(board=jlc4_board(board), gerber=jlc4_gerber(gdir)),
            "JLC5_reference_designator_mapping": jlc5(board, pkg, manifest),
            "JLC6_profile_identity": jlc6(board, d805_board, gdir, pkg, spec),
        }
        for k in ("JLC1_J2_shell_land_to_routed_edge", "JLC4_via_outer_minus_hole"):
            checks[k]["ok"] = checks[k]["board"]["ok"] and checks[k]["gerber"]["ok"]
        checks["JLC1_J2_shell_land_to_routed_edge"]["target_met"] = (
            checks["JLC1_J2_shell_land_to_routed_edge"]["board"]["target_met"]
            and checks["JLC1_J2_shell_land_to_routed_edge"]["gerber"]["target_met"])
        checks["JLC_controls_not_vacuous"] = controls(board, d805_board, d805_g, gdir, pkg, manifest, spec, win)
    doc = dict(schema=1, decision="D-806", board=str(a.board), board_sha256=sha256(a.board),
               package=str(pkg), manifest_sha256=sha256(pkg / "MANIFEST.json"),
               d805_reference=a.d805_ref, spec_sha256=sha256(SPEC), checks=checks,
               targets_met={k: v.get("target_met") for k, v in checks.items() if "target_met" in v},
               all_pass=all(v["ok"] for v in checks.values()))
    text = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for k, v in sorted(checks.items()):
        print(" %-45s %s%s" % (k, "PASS" if v["ok"] else "FAIL",
                               "" if v.get("target_met") in (None, True) else "  (target missed)"),
              file=sys.stderr)
    print(json.dumps(dict(all_pass=doc["all_pass"], targets_met=doc["targets_met"]), indent=1))
    return 0 if doc["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
