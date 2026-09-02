#!/usr/bin/env python3
"""Screen a shared staggered U2.9/U2.10 status breakout in scratch.

The ordinary escape enumerator proved each adjacent land can escape alone but
cannot reserve two nearby vias.  This package-specific screen first carries
both nets west on B.Cu, then staggers their vias on a 0.25 mm grid.  It is
characterization-only: a complete status-tree transaction remains the only
promotion vehicle.
"""

import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
WIDTH = CLEARANCE = 200_000
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge",
            "via_dangling"}

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(board, net, a, b):
    for shape in board.obstacles("B", net):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(net, "B", *a, *b, WIDTH)
    return True


def path_points(pad, via, launch):
    """Two package-specific doglegs; deduplicate zero-length legs."""
    points = [(pad["x"], pad["y"]), (pad["x"] - launch, pad["y"]),
              (via[0], pad["y"]), via]
    return [p for i, p in enumerate(points) if not i or p != points[i - 1]]


def main():
    before = sha(BOARD)
    rows = []
    max_real_drc_cases = 2
    # West of the left-hand TSSOP lands.  The ranges deliberately stagger in
    # both axes and extend beyond the isolated ordinary-via search envelope.
    xs = tuple(reversed(range(50_750_000, 53_251_000, 250_000)))
    ys1 = range(85_750_000, 87_251_000, 250_000)
    ys2 = range(84_750_000, 86_251_000, 250_000)
    launches = (250_000, 500_000, 750_000)
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-status-shared-fanout-") as td:
        work = Path(td)
        seed = qr.QBoard(BOARD)
        pads1 = {p["ref"]: p for p in ir.physical_net_pads(seed, "/BQ25185_STAT1")}
        pads2 = {p["ref"]: p for p in ir.physical_net_pads(seed, "/BQ25185_STAT2")}
        specs = (("/BQ25185_STAT1", pads1["U2.9"]),
                 ("/BQ25185_STAT2", pads2["U2.10"]))
        # Qualify each proposed fanout against the authoritative geometry first.
        # Iterating the raw Cartesian product behind a case cap biases the search
        # toward the first x/y tuple and can incorrectly report a pair-level wall
        # before most individual shapes have even been visited.
        individual = []
        for net, pad, ys in ((specs[0][0], specs[0][1], ys1),
                             (specs[1][0], specs[1][1], ys2)):
            legal = []
            qb = qr.QBoard(BOARD)
            ir.inject_existing_via_obstacles(qb)
            for x, y, launch in itertools.product(xs, ys, launches):
                mark = qb.mark()
                via = (x, y)
                path = path_points(pad, via, launch)
                if (all(qb.point_free(layer, net, *via, 600_000,
                                      CLEARANCE, CLEARANCE, 25_000)
                        for layer in qb.cu)
                        and all(emit(qb, net, a, b)
                                for a, b in zip(path, path[1:]))):
                    legal.append((via, launch, path))
                qb.revert(mark)
            individual.append(legal)
        tested = 0
        geometric = 0
        for first, second, order in itertools.product(
                individual[0], individual[1], ((0, 1), (1, 0))):
            tested += 1
            (x1, y1), launch1, path1 = first
            (x2, y2), launch2, path2 = second
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 < 900_000 ** 2:
                continue
            qb = qr.QBoard(BOARD)
            ir.inject_existing_via_obstacles(qb)
            mark = qb.mark()
            vias = ((x1, y1), (x2, y2))
            ok = True
            paths = [path1, path2]
            for i in order:
                net = specs[i][0]
                if not all(qb.point_free(layer, net, *vias[i], 600_000,
                                         CLEARANCE, CLEARANCE, 25_000)
                           for layer in qb.cu):
                    ok = False
                    break
                if not all(emit(qb, net, a, b)
                           for a, b in zip(paths[i], paths[i][1:])):
                    ok = False
                    break
                qb.via(net, *vias[i], 600_000, 300_000)
            if not ok:
                qb.revert(mark)
                continue
            geometric += 1
            candidate = work / f"candidate-{tested}.kicad_pcb"
            qb.save(candidate)
            qb.revert(mark)
            candidate.with_suffix(".kicad_dru").write_bytes(
                BOARD.with_suffix(".kicad_dru").read_bytes())
            drc = candidate.with_suffix(".drc.json")
            subprocess.run([
                "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                "--format", "json", "--units", "mm", "--severity-all",
                "--schematic-parity", "-o", str(drc), str(candidate),
            ], check=True, text=True, capture_output=True)
            violations = json.loads(drc.read_text()).get("violations", [])
            types = Counter(v.get("type", "unknown") for v in violations)
            attributable = [v for v in violations if v.get("type") not in ACCEPTED]
            row = {
                "order": ["STAT1" if i == 0 else "STAT2" for i in order],
                "vias_mm": [[x1 / 1e6, y1 / 1e6], [x2 / 1e6, y2 / 1e6]],
                "launches_mm": [launch1 / 1e6, launch2 / 1e6],
                "paths_mm": [[[x / 1e6, y / 1e6] for x, y in path]
                             for path in paths],
                "drc_types": dict(types),
                "attributable_drc_count": len(attributable),
            }
            rows.append(row)
            if not attributable or len(rows) >= max_real_drc_cases:
                break
        winner = next((r for r in rows if not r["attributable_drc_count"]), None)
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"layer": "B.Cu", "width_mm": 0.2,
                     "clearance_mm": 0.2, "via_mm": [0.6, 0.3],
                     "characterization_only": True},
        "individual_shapes_tested": [len(xs) * len(ys1) * len(launches),
                                      len(xs) * len(ys2) * len(launches)],
        "legal_individual_fanouts": [len(x) for x in individual],
        "pair_orders_tested": tested,
        "geometric_pairs": geometric,
        "real_drc_cases": rows,
        "real_drc_case_limit": max_real_drc_cases,
        "clean_pair_found": winner is not None,
        "winner": winner,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if winner else 2


if __name__ == "__main__":
    raise SystemExit(main())
