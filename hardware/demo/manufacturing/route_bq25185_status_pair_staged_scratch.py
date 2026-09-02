#!/usr/bin/env python3
"""Atomically stage distinct U2 fanouts and complete both BQ25185 status trees."""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
STATUS = {
    "STAT1": {"net": "/BQ25185_STAT1", "u2": "U2.9", "pullup": "R127.2",
              "replay": ("BQ25185_STAT1_PULLUP_CHARGER", "BQ25185_STAT1_PULLUP_TP")},
    "STAT2": {"net": "/BQ25185_STAT2", "u2": "U2.10", "pullup": "R128.2",
              "replay": ("BQ25185_STAT2_PULLUP_CHARGER", "BQ25185_STAT2_PULLUP_TP")},
}
LANE_X = tuple(range(3_000_000, 70_000_001, 4_000_000))
LANE_Y = tuple(range(3_000_000, 146_000_001, 4_000_000))
SPINE_X = tuple(range(10_000_000, 66_000_001, 4_000_000))
SPINE_Y = tuple(range(10_000_000, 142_000_001, 4_000_000))

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition(); key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def emit(board, net, layer, a, b):
    for shape in board.obstacles(layer, net):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, WIDTH, CLEARANCE, CLEARANCE): return False
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and max(a[1], b[1]) <= board.ey1 - edge): return False
    board.track(net, layer, *a, *b, WIDTH); return True

def corridors(a, b):
    yield from ((a, (a[0], y), (b[0], y), b) for y in LANE_Y)
    yield from ((a, (x, a[1]), (x, b[1]), b) for x in LANE_X)
    yield from ((a, (x, a[1]), (x, y), (b[0], y), b) for x in SPINE_X for y in SPINE_Y)

def staged_join(board, net, layer, a, b):
    tested = 0
    for points in corridors(a, b):
        tested += 1; mark = board.mark()
        if all(emit(board, net, layer, p, q) for p, q in zip(points, points[1:])):
            return {"ok": True, "tested": tested, "waypoints_mm": [[x/1e6, y/1e6] for x, y in points[1:-1]],
                    "mm": sum(math.hypot(q[0]-p[0], q[1]-p[1]) for p, q in zip(points, points[1:]))/1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR", "tested": tested}

def run_case(work, layers, u2_sites, pullup_site, order, baseline):
    scratch = work / f"{order[0]}-{layers['STAT1']}-{u2_sites['STAT1']}-{u2_sites['STAT2']}-{pullup_site}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board); routes = []; reserved = {}
    # Reserve both adjacent U2 package launches before either long join so the
    # pair cannot win by consuming the other status land's only escape.
    for name in order:
        spec = STATUS[name]; pads = {p["ref"]: p for p in ir.physical_net_pads(board, spec["net"])}
        a = qr.reserve_escape(board, spec["net"], pads[spec["u2"]], WIDTH, CLEARANCE, CLEARANCE,
            near="B", far=layers[name], via_dia=600_000, via_drill=300_000,
            target=(pads[spec["pullup"]]["x"], pads[spec["pullup"]]["y"]), site_index=u2_sites[name], site_separation=300_000)
        routes.append({"status": name, "role": "u2_reserve", "result": a})
        if not a.get("ok"): return finish(scratch, board, routes, baseline, False)
        reserved[name] = {"u2": a, "pads": pads}
    for name in order:
        spec = STATUS[name]; pads = reserved[name]["pads"]
        b = qr.reserve_escape(board, spec["net"], pads[spec["pullup"]], WIDTH, CLEARANCE, CLEARANCE,
            near="B", far=layers[name], via_dia=600_000, via_drill=300_000,
            target=(pads[spec["u2"]]["x"], pads[spec["u2"]]["y"]), site_index=pullup_site, site_separation=300_000)
        routes.append({"status": name, "role": "pullup_reserve", "result": b})
        if not b.get("ok"): return finish(scratch, board, routes, baseline, False)
        join = staged_join(board, spec["net"], layers[name], reserved[name]["u2"]["via"], b["via"])
        routes.append({"status": name, "role": "staged_join", "result": join})
        if not join.get("ok"): return finish(scratch, board, routes, baseline, False)
    board.save(scratch)
    for name in order:
        for leg in STATUS[name]["replay"]:
            run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)], text=True, capture_output=True, check=True)
            result = json.loads(run.stdout); routes.append({"status": name, "role": leg, "result": result["result"]})
            if not result["result"].get("ok"): return finish(scratch, qr.QBoard(scratch), routes, baseline, False)
    return finish(scratch, qr.QBoard(scratch), routes, baseline, True)

def finish(scratch, board, routes, baseline, complete):
    board.save(scratch)
    if not complete: return {"routes": routes, "promotion_candidate": False, "reason": "INCOMPLETE_PAIR", "path": scratch}
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json", "--units", "mm",
        "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)], text=True, capture_output=True, check=True)
    types = Counter(v.get("type", "unknown") for v in json.loads(drc.read_text()).get("violations", []))
    report = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(report)], check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(report.read_text()); nets = {s["net"] for s in STATUS.values()}
    targets = {n["net"]: n["open_edges"] for n in ledger["nets"] if n["net"] in nets}
    after = copper(scratch); removed = baseline-after; added = after-baseline
    attributable = sum(n for t, n in types.items() if t not in ACCEPTED)
    ok = targets == {"/BQ25185_STAT1": 0, "/BQ25185_STAT2": 0} and not attributable and not removed and not any(k[0] not in nets for k in added)
    return {"routes": routes, "drc_types": dict(types), "attributable_drc_count": attributable,
        "target_open_edges": targets, "connectivity": ledger["connectivity"], "added_items": sum(added.values()),
        "removed_accepted_copper_items": sum(removed.values()), "promotion_candidate": ok,
        "candidate_sha256": sha(scratch), "path": scratch}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true"); args = ap.parse_args()
    before = sha(BOARD); baseline = copper(BOARD); cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-bq25185-status-staged-") as td:
        for layer_order, a, b, pullup_site, order in itertools.product(itertools.permutations(("I2", "I3")), range(4), range(4), range(2), itertools.permutations(STATUS)):
            layers = {"STAT1": layer_order[0], "STAT2": layer_order[1]}; sites = {"STAT1": a, "STAT2": b}
            case = run_case(Path(td), layers, sites, pullup_site, order, baseline); case.update(layers=layers, u2_sites=sites, pullup_site=pullup_site, order=order); cases.append(case)
            if case.get("promotion_candidate"): break
        winners = [c for c in cases if c.get("promotion_candidate")]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases: case.pop("path", None)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before, "authoritative_unchanged": sha(BOARD) == before,
        "cases": cases, "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
