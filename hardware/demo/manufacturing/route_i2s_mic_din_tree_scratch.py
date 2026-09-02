#!/usr/bin/env python3
"""Atomically screen the fitted microphone I2S data tree."""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/I2S_MIC_DIN"
LEGS = ("I2S_MIC_DIN_MCU_PULLDOWN", "I2S_MIC_DIN_MCU_MIC")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

WIDTH = CLEARANCE = 200_000
PERIMETER_Y = tuple(range(143_000_000, 146_000_001, 500_000))
PERIMETER_X = tuple(range(3_000_000, 8_000_001, 1_000_000))
SPINE_X = tuple(range(10_000_000, 66_000_001, 4_000_000))
SPINE_Y = tuple(range(102_000_000, 142_000_001, 4_000_000))

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def copper(path):
    out = Counter()
    for item in pcbnew.LoadBoard(str(path)).GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y), (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        out[key] += 1
    return out

def coalesce_exact_hub_vias(path):
    """Remove only byte-for-byte-equivalent target-net vias emitted by two legs."""
    board = pcbnew.LoadBoard(str(path)); seen = set(); removed = 0
    for item in list(board.GetTracks()):
        if item.GetClass() != "PCB_VIA" or item.GetNetname() != NET: continue
        p = item.GetPosition()
        key = (p.x, p.y, item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(),
               item.TopLayer(), item.BottomLayer())
        if key in seen:
            board.Remove(item); removed += 1
        else:
            seen.add(key)
    if removed: board.Save(str(path))
    del board
    return removed

def emit(board, a, b, layer):
    blockers = []
    for shape in board.obstacles(layer, NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, WIDTH, CLEARANCE, CLEARANCE):
            blockers.append(shape.tag)
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and max(a[1], b[1]) <= board.ey1 - edge):
        blockers.append("board_edge")
    if blockers:
        return False
    board.track(NET, layer, *a, *b, WIDTH)
    return True

def staged_join(board, a, b, layer):
    families = []
    families.extend(("north_perimeter", (a, (a[0], y), (b[0], y), b)) for y in PERIMETER_Y)
    families.extend(("west_perimeter", (a, (x, a[1]), (x, b[1]), b)) for x in PERIMETER_X)
    families.extend(("two_spine", (a, (x, a[1]), (x, y), (b[0], y), b))
                    for x in SPINE_X for y in SPINE_Y)
    for tested, (family, points) in enumerate(families, 1):
        mark = board.mark()
        if all(emit(board, p, q, layer) for p, q in zip(points, points[1:])):
            return {"ok": True, "family": family, "tested": tested,
                    "waypoints_mm": [[x / 1e6, y / 1e6] for x, y in points[1:-1]],
                    "mm": sum(math.hypot(q[0]-p[0], q[1]-p[1]) for p, q in zip(points, points[1:])) / 1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR", "tested": len(families)}

def route_staged_mic_leg(path):
    board = qr.QBoard(path); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    attempts = []
    for inner in ("I2", "I3"):
        for r_site in range(4):
            for mk_site in range(4):
                mark = board.mark()
                a = qr.reserve_escape(board, NET, pads["R120.1"], WIDTH, CLEARANCE, CLEARANCE,
                    near="F", far=inner, via_dia=600_000, via_drill=300_000,
                    target=(pads["MK1.7"]["x"], pads["MK1.7"]["y"]), site_index=r_site,
                    site_separation=300_000)
                b = {"ok": False, "reason": "NOT_ATTEMPTED"}; joined = b
                if a.get("ok"):
                    b = qr.reserve_escape(board, NET, pads["MK1.7"], WIDTH, CLEARANCE, CLEARANCE,
                        near="B", far=inner, via_dia=600_000, via_drill=300_000,
                        target=(pads["R120.1"]["x"], pads["R120.1"]["y"]), site_index=mk_site,
                        site_separation=300_000)
                if b.get("ok"):
                    joined = staged_join(board, a["via"], b["via"], inner)
                attempts.append({"inner": inner, "r120_site": r_site, "mk1_site": mk_site,
                                 "a": a, "b": b, "join": joined})
                if joined.get("ok"):
                    board.save(path)
                    return {"ok": True, "attempt": "staged-perimeter", "inner": inner,
                            "r120_site": r_site, "mk1_site": mk_site, "reserve_a": a,
                            "reserve_b": b, "join": joined, "cases": len(attempts)}
                board.revert(mark)
    return {"ok": False, "attempt": "staged-perimeter", "reason": "NO_PATH",
            "cases": len(attempts), "last": attempts[-1]}

def run_case(work, order, baseline):
    scratch = work / ("-".join(order) + ".kicad_pcb")
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    routes = []
    for leg in order:
        if leg == "I2S_MIC_DIN_MCU_MIC":
            routes.append({"name": leg, "result": route_staged_mic_leg(scratch)})
        else:
            run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                                 text=True, capture_output=True, check=True)
            routes.append(json.loads(run.stdout))
        if not routes[-1]["result"].get("ok"): break
    coalesced_hub_vias = coalesce_exact_hub_vias(scratch)
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
                    "--units", "mm", "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)],
                   text=True, capture_output=True, check=True)
    violations = json.loads(drc.read_text()).get("violations", [])
    types = Counter(v.get("type", "unknown") for v in violations)
    attributable = [v for v in violations if v.get("type") not in ACCEPTED]
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)],
                   check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    target = next(row for row in ledger["nets"] if row["net"] == NET)
    after = copper(scratch); removed = baseline - after; added = after - baseline
    wrong = [list(item) for item in added if item[0] != NET]
    ok = (len(routes) == len(LEGS) and all(r["result"].get("ok") for r in routes)
          and target["open_edges"] == 0 and not attributable and not removed and not wrong)
    return {"order": order, "routes": routes, "drc_types": dict(types),
            "coalesced_exact_hub_vias": coalesced_hub_vias,
            "attributable_drc_count": len(attributable), "target_open_edges": target["open_edges"],
            "connectivity": ledger["connectivity"], "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "promotion_candidate": ok, "candidate_sha256": sha(scratch), "path": scratch}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true")
    args = ap.parse_args(); before = sha(BOARD); baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-i2s-mic-din-") as td:
        cases = [run_case(Path(td), order, baseline) for order in itertools.permutations(LEGS)]
        winners = [case for case in cases if case["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases: case.pop("path", None)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "cases": cases,
        "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
