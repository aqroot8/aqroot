#!/usr/bin/env python3
"""Stage and atomically gate the retained TCA4307 READY status tree."""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LOCAL = Path(__file__).with_name("route_local_two_pad.py")
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/09_COMMUNITY_HEADER/TCA4307_READY"
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
WIDTH = CLEARANCE = PAD_CLEARANCE = 200_000
# Explicit east/west and north/south spines turn an unbounded 74 mm search into
# a small reproducible family.  Values stay inside the 0..72 x 0..148 outline.
SPINE_X = tuple(range(4_000_000, 69_000_001, 4_000_000))
SPINE_Y = tuple(range(4_000_000, 145_000_001, 4_000_000))

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    blockers = []
    for shape in board.obstacles(layer, NET):
        margin = board.margin(shape, WIDTH, PAD_CLEARANCE, CLEARANCE)
        if qr.seg_shape_dist(a[0], a[1], b[0], b[1], shape) < margin:
            blockers.append(shape.tag)
    edge = qr.EDGE_CLR + WIDTH / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and
            max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and
            max(a[1], b[1]) <= board.ey1 - edge):
        blockers.append("board_edge")
    if blockers:
        return {"ok": False, "reason": "BLOCKED_FIXED_LEG",
                "blockers": sorted(set(blockers))[:10]}
    board.track(NET, layer, *a, *b, WIDTH)
    return {"ok": True, "mm": math.hypot(b[0] - a[0], b[1] - a[1]) / 1e6}


def join(board, a, b, layer, x, y):
    points = (a, (x, a[1]), (x, y), (b[0], y), b)
    legs = []
    for start, end in zip(points, points[1:]):
        leg = emit(board, layer, start, end)
        legs.append(leg)
        if not leg["ok"]:
            break
    ok = len(legs) == 4 and all(leg["ok"] for leg in legs)
    return {"ok": ok, "reason": "OK" if ok else legs[-1]["reason"],
            "spine_x_mm": x / 1e6, "spine_y_mm": y / 1e6, "legs": legs,
            "mm": sum(leg.get("mm", 0) for leg in legs)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_sha = sha256(BOARD); baseline = copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-ready-tree-") as temporary:
        work = Path(temporary); scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board)
        pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
        if set(pads) != {"U16.5", "R46.2", "TP44.1"}:
            raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
        attempts = []; long_route = None
        reservations = []
        for inner in ("I2", "I3"):
            reserve_mark = board.mark()
            a = qr.reserve_escape(board, NET, pads["R46.2"], WIDTH,
                PAD_CLEARANCE, CLEARANCE, near="B", far=inner,
                via_dia=600_000, via_drill=300_000,
                target=(pads["TP44.1"]["x"], pads["TP44.1"]["y"]), site_index=0,
                site_separation=300_000)
            b = {"ok": False, "reason": "NOT_ATTEMPTED"}
            if a.get("ok"):
                b = qr.reserve_escape(board, NET, pads["TP44.1"], WIDTH,
                    PAD_CLEARANCE, CLEARANCE, near="B", far=inner,
                    via_dia=600_000, via_drill=300_000,
                    target=(pads["R46.2"]["x"], pads["R46.2"]["y"]), site_index=0,
                    site_separation=300_000)
            reservations.append({"inner": inner, "a": a, "b": b})
            if b.get("ok"):
                for x in SPINE_X:
                    for y in SPINE_Y:
                        join_mark = board.mark()
                        joined = join(board, a["via"], b["via"], inner, x, y)
                        attempts.append({"inner": inner, "spine_x_mm": x / 1e6,
                                         "spine_y_mm": y / 1e6, "join": joined})
                        if joined.get("ok"):
                            long_route = {"ok": True, "inner": inner,
                                "spine_x_mm": x / 1e6, "spine_y_mm": y / 1e6,
                                "via_xy": a["via_xy"] + b["via_xy"], "vias": 2,
                                "mm": a["mm"] + b["mm"] + joined["mm"]}
                            break
                        board.revert(join_mark)
                    if long_route: break
            if not long_route:
                board.revert(reserve_mark)
            if long_route: break
        board.save(scratch)
        routes = [long_route or {"ok": False, "reason": "NO_STAGED_CORRIDOR"}]
        if long_route:
            run = subprocess.run([sys.executable, str(LOCAL),
                "TCA4307_READY_IC_PULLUP", "--route", str(scratch)],
                text=True, capture_output=True, check=True)
            routes.append(json.loads(run.stdout)["result"])
        drc = work / "drc.json"
        checked = subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones",
            "--save-board", "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch)],
            text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        after = copper(scratch); removed = baseline - after; added = after - baseline
        wrong = [list(item) for item in added if item[0] != NET]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        row = next(r for r in ledger["nets"] if r["net"] == NET)
        promotion = (len(routes) == 2 and all(r.get("ok") for r in routes)
                     and row["open_edges"] == 0 and not attributable
                     and not removed and not wrong)
        candidate = scratch.read_bytes()
        if args.candidate and promotion: args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
        report = {"schema": 1, "authoritative_board_sha256": before_sha,
            "authoritative_unchanged": sha256(BOARD) == before_sha,
            "routes": routes, "cases_tested": len(attempts),
            "reservations": reservations,
            "case_outcomes": dict(Counter(a["join"].get("reason", "UNKNOWN") for a in attempts)),
            "drc_exit": checked.returncode, "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": row["open_edges"], "connectivity": ledger["connectivity"],
            "promotion_candidate": promotion, "candidate_sha256": sha256(scratch)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
