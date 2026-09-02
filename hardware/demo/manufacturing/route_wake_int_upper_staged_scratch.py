#!/usr/bin/env python3
"""Broaden only the final WAKE_INT_N branch after the D-512 witness.

Every case reserves the qualified U3.1 fanout, replays the proven
U2.1->Q10.3->U1.23 middle chain, then co-searches ordinary U1.23/R3.1
escapes and bounded north/interior staged corridors.  Partial trees are never
promotion candidates.
"""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/WAKE_INT_N"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                   item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out


def emit(board, layer, a, b):
    for shape in board.obstacles(layer, NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and
            max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and
            max(a[1], b[1]) <= board.ey1 - edge):
        return False
    board.track(NET, layer, *a, *b, WIDTH)
    return True


def path(board, layer, points):
    mark = board.mark()
    for a, b in zip(points, points[1:]):
        if a != b and not emit(board, layer, a, b):
            board.revert(mark); return None
    return sum(math.hypot(b[0]-a[0], b[1]-a[1])
               for a, b in zip(points, points[1:])) / 1e6


def staged_join(board, layer, a, b):
    families = []
    families += [("direct", (a, b)),
                 ("x_then_y", (a, (b[0], a[1]), b)),
                 ("y_then_x", (a, (a[0], b[1]), b))]
    # The final branch lives in the north MCU region.  Sweep the unused top
    # perimeter densely, then a bounded set of vertical and horizontal spines
    # spanning and flanking both endpoints.
    for y in range(132_000_000, 146_500_001, 250_000):
        families.append(("north_y", (a, (a[0], y), (b[0], y), b)))
    for x in range(38_000_000, 61_000_001, 250_000):
        families.append(("vertical_x", (a, (x, a[1]), (x, b[1]), b)))
    for x, y in itertools.product(range(38_000_000, 61_000_001, 1_000_000),
                                  range(132_000_000, 146_000_001, 1_000_000)):
        families.append(("two_spine", (a, (x, a[1]), (x, y), (b[0], y), b)))
        families.append(("two_spine_rev", (a, (a[0], y), (x, y), (x, b[1]), b)))
    for tested, (family, points) in enumerate(families, 1):
        length = path(board, layer, points)
        if length is not None:
            return {"ok": True, "family": family, "tested": tested,
                    "mm": length,
                    "waypoints_mm": [[x/1e6, y/1e6] for x, y in points[1:-1]]}
    return {"ok": False, "reason": "NO_STAGED_UPPER_CORRIDOR",
            "tested": len(families)}


def seed_tree(target):
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        target.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    board = qr.QBoard(target); ir.inject_existing_via_obstacles(board)
    pad = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}["U3.1"]
    points = ((pad["x"], pad["y"]), (53_750_000, pad["y"]), (53_750_000, 83_000_000))
    if not all(emit(board, "B", a, b) for a, b in zip(points, points[1:])):
        raise RuntimeError("D-512 qualified U3 fanout no longer legal")
    lower_start = (53_750_000, 83_000_000)
    board.via(NET, *lower_start, 600_000, 300_000)
    u2 = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}["U2.1"]
    lower = None
    for layer, site in itertools.product(("I2", "I3"), range(8)):
        mark = board.mark()
        escape = qr.reserve_escape(board, NET, u2, WIDTH, CLEARANCE, CLEARANCE,
            near="B", far=layer, via_dia=600_000, via_drill=300_000,
            target=lower_start, site_index=site, site_separation=250_000)
        if escape.get("ok"):
            end = escape["via"]
            candidates = [(lower_start, end),
                (lower_start, (end[0], lower_start[1]), end),
                (lower_start, (lower_start[0], end[1]), end)]
            for x in range(48_000_000, 59_000_001, 250_000):
                candidates.append((lower_start, (x, lower_start[1]), (x, end[1]), end))
            for points2 in candidates:
                length = path(board, layer, points2)
                if length is not None:
                    lower = {"ok": True, "layer": layer, "site": site,
                             "escape": escape, "mm": length}; break
        if lower: break
        board.revert(mark)
    if not lower:
        board.save(target)
        return [{"leg": "WAKE_INT_U3_U2_STAGED", "result": {"ok": False,
                 "reason": "NO_LOWER_JOIN_AFTER_D512_FANOUT"}}]
    board.save(target)
    routes = [{"leg": "WAKE_INT_U3_U2_STAGED", "result": lower}]
    for leg in ("WAKE_INT_U2_Q10", "WAKE_INT_Q10_U1"):
        run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(target)],
                             text=True, capture_output=True, check=True)
        result = json.loads(run.stdout)["result"]
        routes.append({"leg": leg, "result": result})
        if not result.get("ok"): break
    return routes


def run_case(work, seeded, seed_routes, layer, u1_site, r3_site, baseline):
    scratch = work / f"{layer}-{u1_site}-{r3_site}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(seeded.with_suffix(suffix).read_bytes())
    routes = seed_routes
    if len(routes) != 3 or not all(r["result"].get("ok") for r in routes):
        return {"layer": layer, "u1_site": u1_site, "r3_site": r3_site,
                "routes": routes, "reason": "QUALIFIED_LOWER_TREE_REGRESSED",
                "promotion_candidate": False, "path": scratch}
    board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    reserved = []
    endpoints = []
    for ref, site, target in (("U1.23", u1_site, pads["R3.1"]),
                              ("R3.1", r3_site, pads["U1.23"])):
        result = qr.reserve_escape(board, NET, pads[ref], WIDTH, CLEARANCE, CLEARANCE,
            near="F", far=layer, via_dia=600_000, via_drill=300_000,
            target=(target["x"], target["y"]), site_index=site,
            site_separation=250_000)
        reserved.append({"ref": ref, "result": result})
        if not result.get("ok"):
            return {"layer": layer, "u1_site": u1_site, "r3_site": r3_site,
                    "routes": routes, "reserved": reserved,
                    "reason": "ENDPOINT_ESCAPE_FAILED", "promotion_candidate": False,
                    "path": scratch}
        endpoints.append(result["via"])
    joined = staged_join(board, layer, *endpoints); board.save(scratch)
    if not joined["ok"]:
        return {"layer": layer, "u1_site": u1_site, "r3_site": r3_site,
                "routes": routes, "reserved": reserved, "join": joined,
                "reason": joined["reason"], "promotion_candidate": False,
                "path": scratch}
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity",
        "-o", str(drc), str(scratch)], check=True, text=True, capture_output=True)
    violations = json.loads(drc.read_text()).get("violations", [])
    types = Counter(v.get("type", "unknown") for v in violations)
    attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    report = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(report)],
                   check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(report.read_text()); row = next(r for r in ledger["nets"] if r["net"] == NET)
    after = copper(scratch); removed = baseline-after; added = after-baseline
    promotion = (row["open_edges"] == 0 and not attributable and not removed and
                 not any(key[0] != NET for key in added))
    return {"layer": layer, "u1_site": u1_site, "r3_site": r3_site,
            "routes": routes, "reserved": reserved, "join": joined,
            "drc_types": dict(types), "attributable_drc_count": len(attributable),
            "target_open_edges": row["open_edges"], "connectivity": ledger["connectivity"],
            "added_items": sum(added.values()), "removed_accepted_copper_items": sum(removed.values()),
            "wrong_net_additions": sum(n for key,n in added.items() if key[0] != NET),
            "promotion_candidate": promotion, "candidate_sha256": sha(scratch), "path": scratch}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--candidate",type=Path); ap.add_argument("--promote",action="store_true")
    ap.add_argument("--case-start",type=int,default=0); ap.add_argument("--case-count",type=int,default=16); args=ap.parse_args()
    before=sha(BOARD); baseline=copper(BOARD); cases=[]
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-wake-upper-") as td:
        work=Path(td)
        seeded=work/"seeded.kicad_pcb"; seed_routes=seed_tree(seeded)
        universe=list(itertools.product(("I2","I3"),range(8),range(8)))
        selected=universe[args.case_start:args.case_start+args.case_count]
        for layer,u1,r3 in selected:
            case=run_case(work,seeded,seed_routes,layer,u1,r3,baseline); cases.append(case)
            if case.get("promotion_candidate"): break
        winners=[c for c in cases if c.get("promotion_candidate")]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD)!=before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for c in cases: c.pop("path",None)
    print(json.dumps({"schema":1,"authoritative_board_sha256":before,
        "authoritative_unchanged":sha(BOARD)==before,"cases_tested":len(cases),
        "case_start":args.case_start,"case_stop":args.case_start+len(cases),"case_universe":len(universe),
        "cases":cases,"promotion_candidates":len(winners)},indent=2,sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__": raise SystemExit(main())
