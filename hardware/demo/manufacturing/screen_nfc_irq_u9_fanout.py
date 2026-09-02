#!/usr/bin/env python3
"""Bound package-specific F.Cu fanouts from the fitted U9.27 NFC IRQ land."""

import hashlib, itertools, json, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET, REF = "/NFC_IRQ", "U9.27"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge",
            "track_dangling", "via_dangling"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir
import qrouter as qr


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(board, a, b):
    for shape in board.obstacles("F", NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(NET, "F", *a, *b, WIDTH)
    return True


def main():
    before = sha(BOARD)
    seed = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(seed)
    pad = {p["ref"]: p for p in ir.physical_net_pads(seed, NET)}[REF]
    # U9.27 is on the south-east QFN edge. Sweep outward shoulders below and
    # east of the package, then stagger ordinary vias across the free pocket.
    shapes = []
    for sy, vx, vy in itertools.product(
            range(33_000_000, 35_001_000, 1_000_000),
            range(34_000_000, 38_001_000, 1_000_000),
            range(33_000_000, 37_001_000, 1_000_000)):
        paths = [((pad["x"], pad["y"]), (pad["x"], sy), (vx, sy), (vx, vy))]
        for path in paths:
            if len(set(path)) != len(path): continue
            shapes.append(path)
    legal = []
    board = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(board)
    for path in shapes:
        mark = board.mark()
        via = path[-1]
        if (all(board.point_free(layer, NET, *via, 600_000,
                                 CLEARANCE, CLEARANCE, 25_000)
                for layer in board.cu)
                and all(emit(board, a, b) for a, b in zip(path, path[1:]))):
            legal.append(path)
        board.revert(mark)
    clean = None; drc_cases = []
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-nfc-irq-u9-") as td:
        for index, path in enumerate(legal[:16]):
            candidate = Path(td) / f"candidate-{index}.kicad_pcb"
            board = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(board)
            if not all(emit(board, a, b) for a, b in zip(path, path[1:])): continue
            board.via(NET, *path[-1], 600_000, 300_000); board.save(candidate)
            candidate.with_suffix(".kicad_dru").write_bytes(BOARD.with_suffix(".kicad_dru").read_bytes())
            report = candidate.with_suffix(".drc.json")
            subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all", "--schematic-parity",
                "-o", str(report), str(candidate)], check=True, capture_output=True, text=True)
            types = Counter(v.get("type", "unknown") for v in json.loads(report.read_text()).get("violations", []))
            attributable = sum(n for t, n in types.items() if t not in ACCEPTED)
            drc_cases.append({"index": index, "drc_types": dict(types),
                              "attributable_drc_count": attributable})
            if not attributable:
                clean = path; break
    def mm(path): return [[x / 1e6, y / 1e6] for x, y in path]
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before, "shapes_tested": len(shapes),
        "legal_fanout_count": len(legal), "clean_witness": mm(clean) if clean else None,
        "real_drc_cases": drc_cases, "promotion_candidate": False}, indent=2, sort_keys=True))
    return 0 if clean else 2


if __name__ == "__main__": raise SystemExit(main())
