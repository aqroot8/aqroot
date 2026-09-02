#!/usr/bin/env python3
"""Atomically refloor BTN_B_N and route the fitted SX1262 DIO1 link.

The accepted BTN_B_N tree is the minimum D-502 withdrawal boundary needed for
the U2.20 launch.  Every candidate withdraws that complete tree, reserves the
qualified U2.20 fanout, completes DIO1, then replays all four physical BTN_B
lands.  Neither net can be promoted alone.
"""

import argparse, hashlib, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
DIO = "/SX1262_DIO1"
BTN = "/08_BUTTONS_EXPANDERS/BTN_B_N"
WIDTH = CLEARANCE = 200_000
U2_VIA = (56_000_000, 87_750_000)
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


def withdraw_btn(path):
    board = pcbnew.LoadBoard(str(path)); removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() == BTN:
            board.Remove(item); removed += 1
    board.Save(str(path))
    return removed


def emit(board, a, b, layer):
    for shape in board.obstacles(layer, DIO):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(DIO, layer, *a, *b, WIDTH)
    return True


def corridors(a, b):
    for y in range(90_000_000, 146_000_001, 500_000):
        yield "horizontal", (a, (a[0], y), (b[0], y), b)
    for x in range(4_000_000, 56_000_001, 500_000):
        yield "vertical", (a, (x, a[1]), (x, b[1]), b)
    for x in range(4_000_000, 56_000_001, 1_000_000):
        for y in range(92_000_000, 146_000_001, 2_000_000):
            yield "two_spine", (a, (x, a[1]), (x, y), (b[0], y), b)


def join(board, a, b, layer):
    tested = 0
    for family, points in corridors(a, b):
        tested += 1; mark = board.mark()
        if all(emit(board, p, q, layer) for p, q in zip(points, points[1:])):
            return {"ok": True, "family": family, "tested": tested,
                    "waypoints_mm": [[x / 1e6, y / 1e6] for x, y in points[1:-1]],
                    "mm": sum(math.hypot(q[0]-p[0], q[1]-p[1])
                              for p, q in zip(points, points[1:])) / 1e6}
        board.revert(mark)
    return {"ok": False, "reason": "NO_STAGED_CORRIDOR", "tested": tested}


def compact(points):
    return tuple(point for index, point in enumerate(points)
                 if not index or point != points[index - 1])


def leg_paths(a, b):
    """Small deterministic family for either side of a transition via."""
    yield "direct", compact((a, b))
    yield "x_then_y", compact((a, (b[0], a[1]), b))
    yield "y_then_x", compact((a, (a[0], b[1]), b))


def mixed_join(board, a, b, first):
    """Join through one ordinary via, changing between In2 and In3 once."""
    second = "I3" if first == "I2" else "I2"
    tested_sites = tested_paths = 0
    # A deterministic 1 mm screening lattice bounds this family to 3,021
    # ordinary through-via sites per layer order.
    sites = ((x, y) for x in range(4_000_000, 56_000_001, 1_000_000)
             for y in range(90_000_000, 146_000_001, 1_000_000))
    for via in sites:
        tested_sites += 1
        if not all(board.point_free(layer, DIO, *via, 600_000,
                                    CLEARANCE, CLEARANCE, 25_000)
                   for layer in board.cu):
            continue
        for left_name, left in leg_paths(a, via):
            for right_name, right in leg_paths(via, b):
                tested_paths += 1; mark = board.mark()
                left_ok = all(emit(board, p, q, first)
                              for p, q in zip(left, left[1:]))
                if left_ok:
                    board.via(DIO, *via, 600_000, 300_000)
                right_ok = left_ok and all(emit(board, p, q, second)
                                           for p, q in zip(right, right[1:]))
                if right_ok:
                    return {"ok": True, "family": "mixed_one_via",
                            "layer_order": [first, second],
                            "leg_families": [left_name, right_name],
                            "transition_via_mm": [via[0] / 1e6, via[1] / 1e6],
                            "tested_sites": tested_sites,
                            "tested_paths": tested_paths,
                            "mm": (sum(math.hypot(q[0]-p[0], q[1]-p[1])
                                       for p, q in zip(left, left[1:])) +
                                   sum(math.hypot(q[0]-p[0], q[1]-p[1])
                                       for p, q in zip(right, right[1:]))) / 1e6}
                board.revert(mark)
    return {"ok": False, "reason": "NO_MIXED_ONE_VIA_CORRIDOR",
            "layer_order": [first, second], "tested_sites": tested_sites,
            "tested_paths": tested_paths}


def replay_btn(board):
    group = ir.GROUPS["BTN_B_N"]
    pads = ir.physical_net_pads(board, BTN)
    pads.sort(key=lambda p: (p["ref"], p["x"], p["y"]))
    rows = []
    for i, j in ir.mst_edges(pads):
        pa, pb = pads[i], pads[j]
        layer, kind = ir.edge_plan(pa, pb, group)
        result = (qr.connect_role(board, BTN, pa, pb, layer, WIDTH,
                                  CLEARANCE, CLEARANCE) if kind == "same"
                  else ir.connect_cross(board, BTN, pa, pb, group))
        rows.append({"a": pa["ref"], "b": pb["ref"], "kind": kind,
                     "ok": bool(result.get("ok")),
                     "reason": result.get("reason"), "detail": result})
        if not result.get("ok"): break
    return rows


def run_case(work, inner, u8_site, baseline, mixed):
    scratch = work / f"{'mixed' if mixed else 'single'}-{inner}-{u8_site}.kicad_pcb"
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
    prep = subprocess.run([sys.executable, __file__, "--prepare", str(scratch)],
                          check=True, text=True, capture_output=True)
    withdrawn = int(prep.stdout.splitlines()[0])
    board = qr.QBoard(scratch); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, DIO)}
    u2_path = ((pads["U2.20"]["x"], pads["U2.20"]["y"]),
               (56_750_000, pads["U2.20"]["y"]),
               (56_750_000, 87_750_000), U2_VIA)
    u2_ok = (all(board.point_free(layer, DIO, *U2_VIA, 600_000,
                                  CLEARANCE, CLEARANCE, 25_000)
                 for layer in board.cu)
             and all(emit(board, a, b, "B") for a, b in zip(u2_path, u2_path[1:])))
    if u2_ok: board.via(DIO, *U2_VIA, 600_000, 300_000)
    u8 = {"ok": False, "reason": "NOT_ATTEMPTED"}; haul = u8; btn = []
    if u2_ok:
        u8 = qr.reserve_escape(board, DIO, pads["U8.13"], WIDTH, CLEARANCE,
                               CLEARANCE, near="B", far=inner,
                               via_dia=600_000, via_drill=300_000,
                               target=U2_VIA, site_index=u8_site,
                               site_separation=300_000)
    if u8.get("ok"):
        haul = (mixed_join(board, U2_VIA, u8["via"], inner) if mixed
                else join(board, U2_VIA, u8["via"], inner))
    if haul.get("ok"): btn = replay_btn(board)
    if btn and all(row["ok"] for row in btn):
        ir.refill_planes(board.b); board.save(scratch)
    result = {"mode": "mixed_one_via" if mixed else "single_layer",
              "inner": inner, "u8_site": u8_site, "withdrawn_btn_items": withdrawn,
              "u2_fanout": u2_ok, "u8_escape": u8, "haul": haul,
              "btn_replay": btn, "promotion_candidate": False, "path": scratch}
    if not (btn and all(row["ok"] for row in btn)): return result
    drc = scratch.with_suffix(".drc.json")
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "--schematic-parity", "-o", str(drc), str(scratch)],
                   check=True, text=True, capture_output=True)
    types = Counter(v.get("type", "unknown") for v in json.loads(drc.read_text()).get("violations", []))
    ledger_path = scratch.with_suffix(".ledger.json")
    subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch), str(ledger_path)],
                   check=True, stdout=subprocess.DEVNULL)
    ledger = json.loads(ledger_path.read_text())
    targets = {n["net"]: n["open_edges"] for n in ledger["nets"] if n["net"] in (DIO, BTN)}
    after = copper(scratch); removed, added = baseline - after, after - baseline
    wrong_removed = sum(n for k, n in removed.items() if k[0] != BTN)
    wrong_added = sum(n for k, n in added.items() if k[0] not in (DIO, BTN))
    attributable = sum(n for t, n in types.items() if t not in ACCEPTED)
    result.update({"drc_types": dict(types), "attributable_drc_count": attributable,
                   "target_open_edges": targets, "connectivity": ledger["connectivity"],
                   "removed_items": sum(removed.values()), "wrong_net_removals": wrong_removed,
                   "added_items": sum(added.values()), "wrong_net_additions": wrong_added,
                   "candidate_sha256": sha(scratch)})
    result["promotion_candidate"] = (not attributable and not wrong_removed and
        not wrong_added and targets == {DIO: 0, BTN: 0})
    return result


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--candidate", type=Path); ap.add_argument("--promote", action="store_true")
    ap.add_argument("--single-layer", action="store_true",
                    help="reproduce the exhausted D-503 family")
    ap.add_argument("--prepare", type=Path)
    args = ap.parse_args()
    if args.prepare:
        print(withdraw_btn(args.prepare)); return 0
    before, baseline = sha(BOARD), copper(BOARD)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-dio1-btn-refloor-") as td:
        matrix = (("I3", 0),) if args.promote else tuple((layer, site) for layer in ("I2", "I3") for site in range(8))
        cases = [run_case(Path(td), layer, site, baseline,
                          mixed=not args.single_layer)
                 for layer, site in matrix]
        winners = [row for row in cases if row["promotion_candidate"]]
        if winners and args.candidate: args.candidate.write_bytes(winners[0]["path"].read_bytes())
        if args.promote:
            if not winners or sha(BOARD) != before: raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(winners[0]["path"].read_bytes())
        for row in cases: row.pop("path", None)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "cases": cases,
        "promotion_candidates": len(winners)}, indent=2, sort_keys=True))
    return 0 if winners else 2


if __name__ == "__main__": raise SystemExit(main())
