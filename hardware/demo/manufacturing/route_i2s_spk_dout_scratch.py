#!/usr/bin/env python3
"""Atomically screen broader staged corridors for fitted I2S speaker data."""

import argparse, hashlib, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/I2S_SPK_DOUT"
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

def emit(board, a, b, layer):
    for shape in board.obstacles(layer, NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and max(a[1], b[1]) <= board.ey1 - edge):
        return False
    board.track(NET, layer, *a, *b, WIDTH)
    return True

def corridor_families(a, b):
    yield from (("north_perimeter", (a, (a[0], y), (b[0], y), b)) for y in PERIMETER_Y)
    yield from (("west_perimeter", (a, (x, a[1]), (x, b[1]), b)) for x in PERIMETER_X)
    yield from (("two_spine", (a, (x, a[1]), (x, y), (b[0], y), b))
                for x in SPINE_X for y in SPINE_Y)
    yield from (("three_spine", (a, (x1, a[1]), (x1, y), (x2, y), (x2, b[1]), b))
                for x1 in PERIMETER_X for x2 in SPINE_X for y in SPINE_Y)

def staged_join(board, a, b, layer):
    families = list(corridor_families(a, b))
    for tested, (family, points) in enumerate(families, 1):
        mark = board.mark()
        if all(emit(board, p, q, layer) for p, q in zip(points, points[1:])):
            return {"ok": True, "family": family, "tested": tested,
                    "waypoints_mm": [[x / 1e6, y / 1e6] for x, y in points[1:-1]],
                    "mm": sum(math.hypot(q[0]-p[0], q[1]-p[1]) for p, q in zip(points, points[1:])) / 1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR", "tested": len(families)}

def route_case(path, inner, u1_site, u5_site):
    board = qr.QBoard(path); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    a = qr.reserve_escape(board, NET, pads["U1.34"], WIDTH, CLEARANCE, CLEARANCE,
        near="F", far=inner, via_dia=600_000, via_drill=300_000,
        target=(pads["U5.1"]["x"], pads["U5.1"]["y"]), site_index=u1_site, site_separation=300_000)
    b = {"ok": False, "reason": "NOT_ATTEMPTED"}; joined = b
    if a.get("ok"):
        b = qr.reserve_escape(board, NET, pads["U5.1"], WIDTH, CLEARANCE, CLEARANCE,
            near="F", far=inner, via_dia=600_000, via_drill=300_000,
            target=(pads["U1.34"]["x"], pads["U1.34"]["y"]), site_index=u5_site, site_separation=300_000)
    if b.get("ok"): joined = staged_join(board, a["via"], b["via"], inner)
    if joined.get("ok"): board.save(path)
    return {"ok": joined.get("ok", False), "inner": inner, "u1_site": u1_site,
            "u5_site": u5_site, "reserve_a": a, "reserve_b": b, "join": joined}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true")
    args = ap.parse_args(); before = sha(BOARD); baseline = copper(BOARD); cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-i2s-spk-dout-") as td:
        work = Path(td)
        for inner in ("I2", "I3"):
            for u1_site in range(4):
                for u5_site in range(4):
                    scratch = work / f"{inner}-{u1_site}-{u5_site}.kicad_pcb"
                    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
                    result = route_case(scratch, inner, u1_site, u5_site)
                    if result["ok"]:
                        drc = scratch.with_suffix(".drc.json")
                        subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board", "--format", "json",
                            "--units", "mm", "--severity-all", "--schematic-parity", "-o", str(drc), str(scratch)],
                            check=True, text=True, capture_output=True)
                        types = Counter(v.get("type", "unknown") for v in json.loads(drc.read_text()).get("violations", []))
                        ledger = scratch.with_suffix(".ledger.json")
                        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger)], check=True,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        target = next(n for n in json.loads(ledger.read_text())["nets"] if n["net"] == NET)
                        after = copper(scratch); removed = baseline - after; added = after - baseline
                        attributable = sum(n for t, n in types.items() if t not in ACCEPTED)
                        result.update({"drc_types": dict(types), "attributable_drc_count": attributable,
                            "target_open_edges": target["open_edges"], "removed_accepted_copper_items": sum(removed.values()),
                            "added_items": sum(added.values()), "wrong_net_additions": sum(n for k, n in added.items() if k[0] != NET)})
                        result["promotion_candidate"] = (not attributable and not removed and
                            not result["wrong_net_additions"] and target["open_edges"] == 0)
                    else: result["promotion_candidate"] = False
                    result["path"] = scratch; cases.append(result)
        winners = [c for c in cases if c["promotion_candidate"]]
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
