#!/usr/bin/env python3
"""Atomically route and gate the fitted CC1101 GDO0 control link.

Reuses the D-500-qualified U7.15 B.Cu shoulder/via and screens distinct MCU
escapes plus direct and staged In2/In3 joins.  Failed cases remain scratch-only.
"""

import argparse, hashlib, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/CC1101_GDO0"
WIDTH = CLEARANCE = 200_000
U7_VIA = (18_500_000, 140_750_000)
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


def emit(board, a, b, layer):
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


def corridors(a, b):
    for y in range(120_000_000, 146_000_001, 500_000):
        yield "north_lane", (a, (a[0], y), (b[0], y), b)
    for x in range(3_000_000, 67_000_001, 1_000_000):
        yield "vertical_lane", (a, (x, a[1]), (x, b[1]), b)
    for x in range(6_000_000, 66_000_001, 2_000_000):
        for y in range(120_000_000, 146_000_001, 2_000_000):
            yield "two_spine", (a, (x, a[1]), (x, y), (b[0], y), b)


def staged_join(board, a, b, layer):
    tested = 0
    for family, points in corridors(a, b):
        tested += 1
        mark = board.mark()
        if all(emit(board, p, q, layer) for p, q in zip(points, points[1:])):
            return {"ok": True, "family": family, "tested": tested,
                    "waypoints_mm": [[x / 1e6, y / 1e6]
                                     for x, y in points[1:-1]],
                    "mm": sum(math.hypot(q[0] - p[0], q[1] - p[1])
                              for p, q in zip(points, points[1:])) / 1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR", "tested": tested}


def run_case(work, inner, u1_site, baseline):
    scratch = work / f"{inner}-{u1_site}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    board = qr.QBoard(scratch)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    if set(pads) != {"U1.8", "U7.15"}:
        raise RuntimeError(f"unexpected fitted pads: {sorted(pads)}")

    u7_path = ((pads["U7.15"]["x"], pads["U7.15"]["y"]),
               (18_500_000, pads["U7.15"]["y"]), U7_VIA)
    fanout_ok = (all(board.point_free(layer, NET, *U7_VIA, 600_000,
                                      CLEARANCE, CLEARANCE, 25_000)
                     for layer in board.cu)
                 and all(emit(board, a, b, "B")
                         for a, b in zip(u7_path, u7_path[1:])))
    if fanout_ok:
        board.via(NET, *U7_VIA, 600_000, 300_000)
    u1 = {"ok": False, "reason": "NOT_ATTEMPTED"}
    joined = u1
    if fanout_ok:
        u1 = qr.reserve_escape(
            board, NET, pads["U1.8"], WIDTH, CLEARANCE, CLEARANCE,
            near="F", far=inner, via_dia=600_000, via_drill=300_000,
            target=U7_VIA, site_index=u1_site, site_separation=300_000)
    if u1.get("ok"):
        joined = qr.join_reserved(board, NET, u1["via"], U7_VIA,
                                  WIDTH, CLEARANCE, CLEARANCE, layer=inner)
        if not joined.get("ok"):
            joined = staged_join(board, u1["via"], U7_VIA, inner)
    if joined.get("ok"):
        board.save(scratch)

    result = {"inner": inner, "u1_site": u1_site,
              "qualified_u7_fanout": fanout_ok, "reserve_u1": u1,
              "join": joined, "promotion_candidate": False, "path": scratch}
    if not joined.get("ok"):
        return result

    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "--schematic-parity", "-o", str(drc), str(scratch)],
                   check=True, text=True, capture_output=True)
    types = Counter(v.get("type", "unknown")
                    for v in json.loads(drc.read_text()).get("violations", []))
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                    str(ledger_path)], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    target = next(n for n in ledger["nets"] if n["net"] == NET)
    after = copper(scratch)
    removed, added = baseline - after, after - baseline
    attributable = sum(n for t, n in types.items() if t not in ACCEPTED)
    result.update({"drc_types": dict(types),
                   "attributable_drc_count": attributable,
                   "target_open_edges": target["open_edges"],
                   "connectivity": ledger["connectivity"],
                   "removed_accepted_copper_items": sum(removed.values()),
                   "added_items": sum(added.values()),
                   "wrong_net_additions": sum(n for k, n in added.items()
                                              if k[0] != NET),
                   "candidate_sha256": sha(scratch)})
    result["promotion_candidate"] = (not attributable and not removed and
        not result["wrong_net_additions"] and target["open_edges"] == 0)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path)
    ap.add_argument("--promote", action="store_true")
    args = ap.parse_args()
    before, baseline = sha(BOARD), copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-cc1101-gdo0-") as td:
        matrix = (("I3", 0),) if args.promote else (
            tuple((inner, site) for inner in ("I2", "I3") for site in range(8)))
        cases = [run_case(Path(td), inner, site, baseline)
                 for inner, site in matrix]
        winners = [case for case in cases if case["promotion_candidate"]]
        if winners and args.candidate:
            args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for case in cases:
            case.pop("path", None)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "cases": cases,
        "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__":
    raise SystemExit(main())
