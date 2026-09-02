#!/usr/bin/env python3
"""Route and fully gate the retained three-pad ACC_PWR_EN control tree."""

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
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/ACC_PWR_EN"
PADS = ("R17.1", "U16.1", "U3.20")
BRANCHES = (("R17.1", "U16.1"), ("U16.1", "U3.20"))
EAST_INNER_WAYPOINT_X = (64_000_000, 65_000_000, 66_000_000,
                         67_000_000, 68_000_000)
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            p = item.GetPosition()
            key = (item.GetNetname(), "VIA", item.GetWidth(pcbnew.F_Cu),
                   item.GetDrillValue(), p.x, p.y)
        else:
            ends = sorted(((item.GetStart().x, item.GetStart().y),
                           (item.GetEnd().x, item.GetEnd().y)))
            key = (item.GetNetname(), item.GetLayerName(), item.GetWidth(), *ends)
        result[key] += 1
    return result


def emit_clear_segment(board, layer, a, b, width=200_000,
                       clr_pad=200_000, clr_trk=200_000):
    """Emit one fixed corridor leg only when exact obstacle geometry permits."""
    blockers = []
    for shape in board.obstacles(layer, NET):
        margin = board.margin(shape, width, clr_pad, clr_trk)
        if qr.seg_shape_dist(a[0], a[1], b[0], b[1], shape) < margin:
            blockers.append(shape.tag)
    edge = qr.EDGE_CLR + width / 2
    if not (board.ex0 + edge <= min(a[0], b[0]) and
            max(a[0], b[0]) <= board.ex1 - edge and
            board.ey0 + edge <= min(a[1], b[1]) and
            max(a[1], b[1]) <= board.ey1 - edge):
        blockers.append("board_edge")
    if blockers:
        return {"ok": False, "reason": "BLOCKED_FIXED_LEG",
                "blockers": sorted(set(blockers))[:8]}
    board.track(NET, layer, a[0], a[1], b[0], b[1], width)
    return {"ok": True, "reason": "OK",
            "mm": math.hypot(b[0] - a[0], b[1] - a[1]) / 1e6}


def join_via_waypoints(board, va, vb, layer, x):
    """Join reserved barrels through a fixed east-side inner-layer corridor."""
    points = (va, (x, va[1]), (x, vb[1]), vb)
    legs = []
    for left, right in zip(points, points[1:]):
        leg = emit_clear_segment(board, layer, left, right)
        legs.append(leg)
        if not leg["ok"]:
            break
    return {
        "ok": len(legs) == 3 and all(leg.get("ok") for leg in legs),
        "reason": "OK" if len(legs) == 3 and all(leg.get("ok") for leg in legs)
        else legs[-1].get("reason", "NO_PATH"),
        "waypoint_x_mm": x / 1e6, "legs": legs,
        "mm": sum(leg.get("mm", 0) for leg in legs),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-acc-pwr-en-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        board = qr.QBoard(scratch)
        ir.inject_existing_via_obstacles(board)
        pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
        if set(pads) != set(PADS):
            raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")
        routes = []
        attempts = []
        for inner in ("I2", "I3"):
            for waypoint_x in EAST_INNER_WAYPOINT_X:
              for u16_site in range(4):
                for u3_site in range(4):
                    mark = board.mark()
                    a = qr.reserve_escape(
                        board, NET, pads["U16.1"], 200_000, 200_000, 200_000,
                        near="B", far=inner, via_dia=600_000,
                        via_drill=300_000, target=(pads["U3.20"]["x"], pads["U3.20"]["y"]),
                        site_index=u16_site, site_separation=300_000,
                    )
                    b = {"ok": False, "reason": "NOT_ATTEMPTED"}
                    joined = {"ok": False, "reason": "NOT_ATTEMPTED"}
                    if a.get("ok"):
                        b = qr.reserve_escape(
                            board, NET, pads["U3.20"], 200_000, 200_000, 200_000,
                            near="B", far=inner, via_dia=600_000,
                            via_drill=300_000,
                            target=(pads["U16.1"]["x"], pads["U16.1"]["y"]),
                            site_index=u3_site, site_separation=300_000,
                        )
                    if b.get("ok"):
                        joined = join_via_waypoints(
                            board, a["via"], b["via"], inner, waypoint_x)
                    attempts.append({"inner": inner, "u16_site": u16_site,
                                     "u3_site": u3_site,
                                     "waypoint_x_mm": waypoint_x / 1e6,
                                     "a": a, "b": b,
                                     "join": joined})
                    if joined.get("ok"):
                        routes = [dict(joined, ok=True, inner=inner,
                                       attempt="reserved-site-enumeration",
                                       vias=2, via_xy=a["via_xy"] + b["via_xy"],
                                       mm=a["mm"] + b["mm"] + joined["mm"])]
                        break
                    board.revert(mark)
                if routes:
                    break
              if routes:
                break
            if routes:
                break
        if not routes:
            routes = [{"ok": False, "attempt": "reserved-site-enumeration",
                       "waypoint_x_mm": [x / 1e6 for x in EAST_INNER_WAYPOINT_X],
                       "cases": len(attempts), "last": attempts[-1]}]
        if routes[-1].get("ok"):
            routes.append(qr.connect_role(
                board, NET, pads["R17.1"], pads["U16.1"], "B",
                200_000, 200_000, 200_000, G=25_000,
            ))
        board.save(scratch)
        drc = work / "drc.json"
        checked = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        after = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] != NET]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        row = next(r for r in ledger["nets"] if r["net"] == NET)
        promotion = (len(routes) == len(BRANCHES)
                     and all(r.get("ok") for r in routes)
                     and row["open_edges"] == 0 and not attributable
                     and not removed and not wrong)
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
        report = {
            "schema": 1, "authoritative_board_sha256": before_sha,
            "authoritative_unchanged": sha256(BOARD) == before_sha,
            "routes": routes, "reserved_site_cases": len(attempts),
            "reserved_site_outcomes": dict(Counter(
                attempt["join"].get("reason", "OK")
                if attempt["join"].get("ok") is not True else "OK"
                for attempt in attempts
            )),
            "drc_exit": checked.returncode,
            "drc_types": dict(types), "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": row["open_edges"],
            "connectivity": ledger["connectivity"],
            "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
