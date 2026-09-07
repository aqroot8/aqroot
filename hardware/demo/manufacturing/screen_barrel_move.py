#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- READ-ONLY: WHERE MUST THIS BARREL GO FOR THE POUR TO CLOSE?

D-658.  `screen_pour_cut_blame.py` (D-657) answers *which foreign objects cut
this pour*.  On `+3V3` the answer was TWO 0.600/0.300 barrels of
`Net-(U11-TS_MR)` at (64.700, 70.500) and (66.600, 70.900) -- the `BQ25185`'s
TS/MR strap, two pads, microamps, UNPROTECTED -- and `evidence/d657-barrel-shrink.json`
then closed the SHRINK arm: at 0.500/0.250, 0.450/0.200 and the D-257 `FINE_ESC`
0.350/0.200 the plane stays cut, and removing them outright frees the plane by
STRANDING the strap.  What is left is the arm neither screen can ask:

    MOVE them.  Which rigid offsets let KiCad's own filler pour the severed
    cluster back onto the body, leave every moved net in ONE piece, and
    survive the board's own DRC?

THE MOVE IS OF A NEIGHBOURHOOD, NOT OF A VIA.  A barrel is the junction of the
tracks that land on it; translating the via alone would leave those ends in
mid-air, and a screen that measured THAT would be measuring a board no
transaction could ever build.  So every track end that coincides EXACTLY with a
named site, on any layer that site's barrel spans, translates with it.  That is
the ideal a `--detour-spec` relay approximates, and it is the right thing to
measure first: if the ideal does not free the pour, no relay of it will.

WHAT IS MEASURED, NOT ASSUMED

  * KiCad's OWN FILLER decides the pour.  Every rung runs `pcbnew.ZONE_FILLER`
    over the whole board and reads the partition off `GetConnectivity`, exactly
    as D-657 does -- and for the same reason in TWO processes, because removing
    or editing copper and filling in ONE interpreter segfaults KiCad 10.0.5.
  * KiCad's OWN DRC decides legality.  `--drc` runs `kicad-cli pcb drc
    --refill-zones` per rung and reports the error profile BY TYPE against the
    unmoved board's, so a rung that frees the pour by planting a barrel in
    somebody else's clearance cannot read as a win.
  * THE MOVED NET IS WATCHED AS CLOSELY AS THE POUR.  A rung that frees the
    plane by severing the strap is a rung that traded one open edge for
    another; `intact` is reported per moved net, from the same partition.
  * THE AUTHORITATIVE BOARD IS NEVER WRITTEN.  Every rung is a private copy;
    the authority's sha256 is taken before and after and reported.

    python3 screen_barrel_move.py --barrel NET@X,Y:DIA/DRILL [--barrel ...]
                                  --free NET:REF.PAD [--free ...]
                                  [--offset DX,DY]... [--drc] [-o OUT.json]

`--free NET:REF.PAD` is the CLAIM: this pad is severed from the largest cluster
of NET today and the rung must join it.  Offsets default to the six D-657
records: +-0.5, +-1.0 north/south and +-1.0 east/west.
"""

import argparse
import hashlib
import itertools
import math
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))


# --------------------------------------------------------------------------- #
# CHILDREN
# --------------------------------------------------------------------------- #
# One `LoadBoard` per process, and the EDIT and the FILL in different processes.
# Both limits are D-657's, recorded there in the same words and paid for with a
# segfault and an unwrapped `SwigPyObject` respectively.
# --------------------------------------------------------------------------- #

def _move_child():
    """argv: --move BOARD MOVE.json -- translate the barrels + their ends, SAVE.

    `MOVE.json` is `{"sites": [{"net","x_nm","y_nm","dia_nm","drill_nm",
    "dx_nm","dy_nm"}, ...]}`.  EACH SITE CARRIES ITS OWN DELTA, because the
    first ladder this screen ran moved both barrels rigidly and every rung that
    freed the pour landed one of them inside `/ACC_3V3_SW`'s clearance -- the
    switched accessory rail `AQROOT_DEMO_SCOPE` requires.  Two barrels that cut
    the same neck do not have to leave it in the same direction.  Resolution is EXACT and UNIQUE per site: a site that
    matches a number of vias other than ONE is a description of a board that is
    not this one, and the child stops rather than guessing -- the same contract
    `route_maze_batch.resolve_barrel` holds itself to.
    """
    import pcbnew
    board, spec = sys.argv[2], Path(sys.argv[3])
    doc = json.loads(spec.read_text())
    b = pcbnew.LoadBoard(board)

    moved_vias, moved_ends, report = [], [], []
    for s in doc["sites"]:
        dx, dy = int(s["dx_nm"]), int(s["dy_nm"])
        hits = []
        for t in b.GetTracks():
            if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != s["net"]:
                continue
            v = pcbnew.Cast_to_PCB_VIA(t)
            p = v.GetPosition()
            if (p.x, p.y) != (int(s["x_nm"]), int(s["y_nm"])):
                continue
            if int(v.GetWidth()) != int(s["dia_nm"]):
                continue
            if int(v.GetDrillValue()) != int(s["drill_nm"]):
                continue
            hits.append(v)
        if len(hits) != 1:
            (spec.parent / "moved.json").write_text(json.dumps(dict(
                error="site %s matches %d vias, not 1" % (s, len(hits)))))
            return 2
        v = hits[0]
        # D-658.  A MOVE MAY ALSO BE A SHRINK, and the two levers were only
        # ever refuted SEPARATELY.  `evidence/d657-barrel-shrink.json` shrank
        # these barrels in place down to the D-257 `FINE_ESC` 0.350/0.200 and
        # the plane stayed cut; this screen's first ladder moved them at full
        # 0.600/0.300 and every rung that freed the plane landed inside
        # `/ACC_3V3_SW`'s 0.250 mm rule clearance.  The antipad a barrel
        # subtracts and the clearance it demands are the SAME radius, so the
        # combination is a different question from either arm.
        if s.get("to_dia_nm"):
            v.SetWidth(int(s["to_dia_nm"]))
        if s.get("to_drill_nm"):
            v.SetDrill(int(s["to_drill_nm"]))
        # THE LAYER STACK IS NOT THE LAYER NUMBERING, and this cost a whole
        # ladder to find.  KiCad 10 numbers copper `F_Cu 0, B_Cu 2, In1 4,
        # In2 6, In3 8, In4 10`, so `range(TopLayer, BottomLayer+1)` on a
        # through via yields {0,1,2} -- F, B and nothing else.  The first run
        # of this screen dragged 2 of the 4 ends for exactly that reason and
        # reported every offset as SEVERING the strap, because the `In2` hop
        # between the two barrels was left standing at the old sites.  The
        # span is a slice of the STACK, in stack order.
        stack = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                 pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
        i, j = stack.index(v.TopLayer()), stack.index(v.BottomLayer())
        span = set(stack[min(i, j):max(i, j) + 1])
        ends = 0
        for t in b.GetTracks():
            if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != s["net"]:
                continue
            if t.GetLayer() not in span:
                continue
            for get, put in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                p = get()
                if (p.x, p.y) == (int(s["x_nm"]), int(s["y_nm"])):
                    put(pcbnew.VECTOR2I(p.x + dx, p.y + dy))
                    ends += 1
        p = v.GetPosition()
        v.SetPosition(pcbnew.VECTOR2I(p.x + dx, p.y + dy))
        moved_vias.append(s["net"])
        moved_ends.append(ends)
        report.append(dict(net=s["net"],
                           was_mm=[s["x_nm"] / 1e6, s["y_nm"] / 1e6],
                           now_mm=[(s["x_nm"] + dx) / 1e6,
                                   (s["y_nm"] + dy) / 1e6],
                           geometry_mm=[int(v.GetWidth()) / 1e6,
                                        int(v.GetDrillValue()) / 1e6],
                           track_ends_dragged=ends))
    b.Save(board)
    (spec.parent / "moved.json").write_text(json.dumps(dict(
        vias=len(moved_vias), ends=sum(moved_ends), sites=report)))
    return 0


def _fill_child():
    """argv: --fill BOARD OUT.json NET [NET ...] -- refill, then partition."""
    import pcbnew
    board, out, nets = sys.argv[2], Path(sys.argv[3]), sys.argv[4:]
    b = pcbnew.LoadBoard(board)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    conn = b.GetConnectivity()
    doc = {}
    for net in nets:
        pads = {}
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == net and p.GetNumber():
                    pads[f.GetReference() + "." + p.GetNumber()] = p
        seen, parts = set(), []
        for k, p in pads.items():
            if k in seen:
                continue
            grp = sorted({i.GetParentFootprint().GetReference() + "."
                          + i.GetNumber()
                          for i in conn.GetConnectedItems(p)
                          if i.GetClass() == "PAD"} | {k})
            grp = [g for g in grp if g in pads]
            seen |= set(grp)
            parts.append(sorted(grp))
        doc[net] = sorted(parts)
    out.write_text(json.dumps(doc))
    return 0


def _strip_child():
    """argv: --strip BOARD SPEC.json -- remove the named barrels and SAVE."""
    import pcbnew
    board, spec = sys.argv[2], Path(sys.argv[3])
    doc = json.loads(spec.read_text())
    b = pcbnew.LoadBoard(board)
    gone = 0
    for s in doc["sites"]:
        for t in list(b.GetTracks()):
            if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != s["net"]:
                continue
            v = pcbnew.Cast_to_PCB_VIA(t)
            p = v.GetPosition()
            if (p.x, p.y) == (int(s["x_nm"]), int(s["y_nm"])) \
                    and int(v.GetWidth()) == int(s["dia_nm"]) \
                    and int(v.GetDrillValue()) == int(s["drill_nm"]):
                b.Remove(t)
                gone += 1
    b.Save(board)
    return 0 if gone == len(doc["sites"]) else 3


if len(sys.argv) > 1 and sys.argv[1] == "--strip":
    raise SystemExit(_strip_child())
if len(sys.argv) > 1 and sys.argv[1] == "--move":
    raise SystemExit(_move_child())
if len(sys.argv) > 1 and sys.argv[1] == "--fill":
    raise SystemExit(_fill_child())


# --------------------------------------------------------------------------- #
# DRIVER
# --------------------------------------------------------------------------- #

def parse_barrel(s):
    """`NET@X,Y:DIA/DRILL` in millimetres -> the child's nanometre record."""
    net, rest = s.rsplit("@", 1)
    at, geom = rest.split(":", 1)
    x, y = [float(v) for v in at.split(",")]
    dia, drill = [float(v) for v in geom.split("/", 1)]
    return dict(net=net, x_nm=int(round(x * 1e6)), y_nm=int(round(y * 1e6)),
                dia_nm=int(round(dia * 1e6)), drill_nm=int(round(drill * 1e6)))


def bonded(partition, pad):
    """Is `pad` in the LARGEST cluster of this partition?  And how big is its own?"""
    own = next((c for c in partition if pad in c), None)
    if own is None:
        return None, 0, 0
    big = max((len(c) for c in partition), default=0)
    return (len(own) == big and big > 1), len(own), len(partition)


def drc_profile(brd, out):
    """`kicad-cli pcb drc --refill-zones` -> {type: count}, or the failure."""
    r = subprocess.run(
        ["kicad-cli", "pcb", "drc", "--refill-zones", "--format", "json",
         "--severity-error", "-o", str(out), str(brd)],
        capture_output=True, text=True)
    if not out.exists():
        return dict(error=(r.stderr or r.stdout)[-400:], exit=r.returncode)
    doc = json.loads(out.read_text())
    prof = {}
    for v in doc.get("violations", ()):
        prof[v["type"]] = prof.get(v["type"], 0) + 1
    return dict(exit=r.returncode, by_type=prof,
                total=sum(prof.values()),
                unconnected=len(doc.get("unconnected_items", ())))


SWEEP = None


def sweep_plan(a, sites):
    """Legal barrel sites for EACH named barrel, crossed into rungs.

    THE OBSTACLE MODEL IS THE ROUTER'S OWN, not a re-derivation.
    `maze3d._via_free_everywhere` is the same predicate `_hop_sites` uses to
    decide `NO_VIA_SITE` and the same one `verify_laid` re-proves afterwards:
    copper clearance on EVERY layer of the stack plus drilled-hole clearance
    against every hole on the board.  Same-net copper is not an obstacle to it,
    which is why the sweep runs on a copy with the OLD BARRELS ALREADY GONE --
    otherwise every site within a hole-clearance of the barrel being moved
    would report itself unavailable to its own replacement.

    Ranking is by DISPLACEMENT, smallest first.  A barrel that has to move is
    a barrel whose neighbours have to be re-laid to follow it, and every tenth
    of a millimetre of that move is copper some relay owes the board.
    """
    global SWEEP
    import shutil as _sh
    import qrouter as qr
    import maze3d as mz
    import incremental_router as ir

    d = (a.work or Path("/tmp")) / "sweep"
    d.mkdir(parents=True, exist_ok=True)
    for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        src = a.board.with_suffix(suf)
        if src.exists():
            _sh.copy(src, (d / a.board.name).with_suffix(suf))
    brd = d / a.board.name
    spec = d / "strip.json"
    spec.write_text(json.dumps(dict(sites=[dict(s, dx_nm=0, dy_nm=0)
                                           for s in sites], strip=True)))
    subprocess.run([sys.executable, __file__, "--strip", str(brd), str(spec)],
                   capture_output=True, text=True, check=True)

    qb = qr.QBoard(str(brd))
    ir.inject_existing_via_obstacles(qb)
    per = []
    for s in sites:
        dia, drill = s["dia_nm"], s["drill_nm"]
        if a.shrink:
            dia, drill = [int(round(float(v) * 1e6))
                          for v in a.shrink.split("/")]
        # THE SWEEP'S CLEARANCE IS THE CALLER'S, because the router's Field
        # carries ONE clearance and the board's `.kicad_dru` does not.  This
        # pocket is bounded by `/ACC_3V3_SW`, whose `ACC_3V3 routed clearance`
        # rule is 0.250 mm, not the 0.200 mm Default -- so a sweep run at
        # 0.200 offers sites real DRC then refuses, which is how the first
        # shrink ladder came back with two clearance violations it had already
        # been told about.
        clr = int(round(a.sweep_clr * 1e6))
        field = mz.Field(qb, s["net"], 200000, clr, clr,
                         dia, drill, G=a.sweep_grid)
        R = int(round(a.sweep * 1e6))
        step = int(round(a.sweep_step * 1e6))
        lo = int(round(a.sweep_min * 1e6))
        found = []
        n = int(R // step)
        for iy in range(-n, n + 1):
            for ix in range(-n, n + 1):
                dx, dy = ix * step, iy * step
                r = math.hypot(dx, dy)
                if r < lo or r > R:
                    continue
                x, y = s["x_nm"] + dx, s["y_nm"] + dy
                if mz._via_free_everywhere(qb, field, x, y, dia, drill,
                                           a.sweep_grid):
                    found.append((round(r / 1e6, 4), round(dx / 1e6, 4),
                                  round(dy / 1e6, 4)))
        found.sort()
        per.append(found)
        print("sweep %s @ %.3f,%.3f : %d legal sites, nearest %s"
              % (s["net"], s["x_nm"] / 1e6, s["y_nm"] / 1e6, len(found),
                 found[:3]), file=sys.stderr, flush=True)

    SWEEP = dict(radius_mm=a.sweep, step_mm=a.sweep_step, shrink=a.shrink,
                 clearance_mm=a.sweep_clr,
                 min_mm=a.sweep_min, grid_nm=a.sweep_grid,
                 predicate="maze3d._via_free_everywhere on a copy with the "
                           "named barrels removed",
                 legal_sites=[len(f) for f in per],
                 nearest=[f[:8] for f in per])
    if a.sweep_only:
        print(json.dumps(dict(schema=1, decision="D-658", sweep=SWEEP,
                              board_sha256=hashlib.sha256(
                                  a.board.read_bytes()).hexdigest(),
                              all_sites=[[list(v) for v in f] for f in per]),
                         indent=1, sort_keys=True))
        if a.out:
            a.out.write_text(json.dumps(
                dict(schema=1, decision="D-658", sweep=SWEEP,
                     all_sites=[[list(v) for v in f] for f in per]),
                indent=1, sort_keys=True) + "\n")
        raise SystemExit(0)
    tops = [f[:a.sweep_top] for f in per]
    plan, seen = [], set()
    for combo in itertools.product(*tops):
        key = tuple((c[1], c[2]) for c in combo)
        if key in seen:
            continue
        seen.add(key)
        # A PAIR OF BARRELS IS A HOP, AND A HOP HAS A LENGTH.  Two sites the
        # relay has to span on ONE inner layer are not free of each other; a
        # bound here is the caller saying how long an `In2` hop this
        # transaction is willing to own.
        if a.sweep_near:
            pts = [(sites[i]["x_nm"] / 1e6 + c[0],
                    sites[i]["y_nm"] / 1e6 + c[1])
                   for i, c in enumerate(key)]
            if max(math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                   for p1 in pts for p2 in pts) > a.sweep_near:
                continue
        plan.append(key)
    plan.sort(key=lambda k: (max(math.hypot(*v) for v in k),
                             sum(math.hypot(*v) for v in k)))
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--barrel", action="append", required=True,
                    metavar="NET@X,Y:DIA/DRILL")
    ap.add_argument("--free", action="append", default=[],
                    metavar="NET:REF.PAD",
                    help="the pad this move must join to its net's body")
    ap.add_argument("--offset", action="append", default=[], metavar="DX,DY")
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--work", type=Path, default=None)
    ap.add_argument("--drc", action="store_true")
    ap.add_argument("--sweep", type=float, default=0.0, metavar="R_MM",
                    help="search each site's own legal barrel sites within "
                         "R_MM instead of trying rigid --offset arms")
    ap.add_argument("--sweep-step", type=float, default=0.1)
    ap.add_argument("--sweep-min", type=float, default=0.35,
                    help="a site nearer than this to the old one is not a MOVE")
    ap.add_argument("--sweep-top", type=int, default=4,
                    help="candidates per site to cross-product into rungs")
    ap.add_argument("--sweep-grid", type=int, default=25000)
    ap.add_argument("--sweep-clr", type=float, default=0.20,
                    help="clearance the sweep holds every neighbour to, in mm")
    ap.add_argument("--rung", action="append", default=[],
                    metavar="DX,DY;DX,DY",
                    help="ONE explicit rung: a delta PER named barrel, in the "
                         "order they were named (repeatable)")
    ap.add_argument("--shrink", default=None, metavar="DIA/DRILL",
                    help="the geometry the moved barrels take, in mm; below "
                         "the board via floor this needs a .kicad_dru licence "
                         "and the gate's clause 6 will say so")
    ap.add_argument("--sweep-only", action="store_true",
                    help="report each barrel's legal sites and stop; no fill")
    ap.add_argument("--sweep-near", type=float, default=0.0,
                    help="a PAIR whose two sites are further apart than this "
                         "is not offered as a rung (0 = no bound)")
    ap.add_argument("--stop-after", type=int, default=0,
                    help="stop once this many rungs have passed")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    sites = [parse_barrel(s) for s in a.barrel]
    free = []
    for f in a.free:
        net, pad = f.rsplit(":", 1)
        free.append((net, pad))
    offsets = [tuple(float(v) for v in o.split(",")) for o in a.offset] or [
        (0.0, 0.5), (0.0, -0.5), (0.0, 1.0), (0.0, -1.0),
        (1.0, 0.0), (-1.0, 0.0)]

    before = hashlib.sha256(a.board.read_bytes()).hexdigest()
    tag = hashlib.sha256(("%s|%s|%s" % (before, a.barrel, a.free))
                         .encode()).hexdigest()[:12]
    work = a.work or Path("/tmp/barrel_move_%s" % tag)
    work.mkdir(parents=True, exist_ok=True)

    watched = sorted({n for n, _ in free} | {s["net"] for s in sites})

    def rung(name, deltas, shrink=None):
        """`deltas` is one (dx_mm, dy_mm) PER SITE, in the order named.

        `shrink` is withheld from the as-built baseline on purpose: the rung
        every other rung is compared against must be THE BOARD, geometry and
        all, or the delta is measured against a board nobody proposed.
        """
        d = work / name
        d.mkdir(parents=True, exist_ok=True)
        for suf in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            src = a.board.with_suffix(suf)
            if src.exists():
                shutil.copy(src, (d / a.board.name).with_suffix(suf))
        brd = d / a.board.name
        rec = dict(rung=name, deltas_mm=[list(v) for v in deltas],
                   to_mm=[[round(s["x_nm"] / 1e6 + dx, 4),
                           round(s["y_nm"] / 1e6 + dy, 4)]
                          for s, (dx, dy) in zip(sites, deltas)])
        rec["shrink_mm"] = shrink
        if shrink or any(v != (0.0, 0.0) for v in deltas):
            spec = d / "move.json"
            to = ([int(round(float(v) * 1e6)) for v in shrink.split("/")]
                  if shrink else [0, 0])
            spec.write_text(json.dumps(dict(sites=[
                dict(s, dx_nm=int(round(dx * 1e6)),
                     dy_nm=int(round(dy * 1e6)),
                     to_dia_nm=to[0], to_drill_nm=to[1])
                for s, (dx, dy) in zip(sites, deltas)])))
            r = subprocess.run([sys.executable, __file__, "--move", str(brd),
                                str(spec)], capture_output=True, text=True)
            moved = json.loads((d / "moved.json").read_text())
            if r.returncode or "error" in moved:
                rec.update(ok=False, move=moved)
                return rec
            rec["move"] = moved
        res = d / "partition.json"
        r = subprocess.run([sys.executable, __file__, "--fill", str(brd),
                            str(res)] + watched,
                           capture_output=True, text=True)
        if not res.exists():
            rec.update(ok=False, fill_error=(r.stderr or r.stdout)[-400:])
            return rec
        part = json.loads(res.read_text())
        rec["clusters"] = {n: len(part[n]) for n in watched}
        rec["freed"] = {}
        for net, pad in free:
            ok, own, n = bonded(part[net], pad)
            rec["freed"]["%s:%s" % (net, pad)] = dict(
                bonded=ok, own_cluster=own, clusters=n)
        rec["intact"] = {s["net"]: len(part[s["net"]]) == 1
                         for s in sites}
        if a.drc:
            rec["drc"] = drc_profile(brd, d / "drc.json")
        rec["ok"] = (all(v["bonded"] for v in rec["freed"].values())
                     and all(rec["intact"].values()))
        return rec

    t0 = time.time()
    if a.rung:
        plan = [tuple(tuple(float(v) for v in part.split(","))
                      for part in r.split(";")) for r in a.rung]
        for k in plan:
            if len(k) != len(sites):
                raise SystemExit("--rung names %d deltas for %d barrels"
                                 % (len(k), len(sites)))
    elif a.sweep:
        plan = sweep_plan(a, sites)
    else:
        plan = [tuple((dx, dy) for _ in sites) for (dx, dy) in offsets]
    rungs = [rung("r00-as-built", tuple((0.0, 0.0) for _ in sites))]
    for i, deltas in enumerate(plan):
        rungs.append(rung("r%02d-%s%s" % (i + 1,
                                          "_".join("%+.2f%+.2f" % v
                                                   for v in deltas),
                                          "@" + a.shrink if a.shrink else ""),
                          deltas, a.shrink))
        if a.stop_after and len([r for r in rungs if r.get("ok")]) >= a.stop_after:
            break

    base = rungs[0].get("drc", {}).get("by_type") if a.drc else None
    for r in rungs[1:]:
        if base is not None and "by_type" in r.get("drc", {}):
            got = r["drc"]["by_type"]
            r["drc"]["delta_by_type"] = {
                k: got.get(k, 0) - base.get(k, 0)
                for k in sorted(set(got) | set(base))
                if got.get(k, 0) != base.get(k, 0)}

    after = hashlib.sha256(a.board.read_bytes()).hexdigest()
    doc = dict(
        schema=1, decision="D-658", board=str(a.board),
        board_sha256=before, authoritative_unchanged=(before == after),
        question=("which rigid offsets of these barrels -- and of the track "
                  "ends that land on them -- let KiCad's own filler pour the "
                  "named pads back onto their body, leave every moved net in "
                  "one piece, and keep the DRC profile?"),
        method=("pcbnew.ZONE_FILLER per rung on a private copy; the barrel and "
                "every coincident track end on the layers it spans translate "
                "together; partitions read off GetConnectivity; --drc reruns "
                "kicad-cli pcb drc --refill-zones and reports the delta BY TYPE"),
        sites=[dict(net=s["net"], at_mm=[s["x_nm"] / 1e6, s["y_nm"] / 1e6],
                    dia_mm=s["dia_nm"] / 1e6, drill_mm=s["drill_nm"] / 1e6)
               for s in sites],
        free=["%s:%s" % f for f in free],
        sweep=SWEEP,
        rungs=rungs,
        winners=[r["rung"] for r in rungs[1:] if r.get("ok")],
        seconds=round(time.time() - t0, 1))
    txt = json.dumps(doc, indent=1, sort_keys=True)
    if a.out:
        a.out.write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
