#!/usr/bin/env python3
"""Qualify a coherent ordinary-via fanout set for the DISP_BL strap pocket."""

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
NET = "/02_MCU_CORE/DISP_BL_CTL_STRAP"
REFS = ("U1.16", "TP2.1", "R109.1")
WIDTH = CLEARANCE = 200_000

sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(board, a, b):
    for shape in board.obstacles("F", NET):
        if qr.seg_shape_dist(*a, *b, shape) < board.margin(
                shape, WIDTH, CLEARANCE, CLEARANCE):
            return False
    board.track(NET, "F", *a, *b, WIDTH)
    return True


def compact(points):
    return tuple(p for i, p in enumerate(points) if not i or p != points[i - 1])


def candidates(pad):
    """Bounded 0.25 mm perimeter shoulders and ordinary via sites."""
    px, py = pad["x"], pad["y"]
    result = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for reach in range(750_000, 2_251_000, 250_000):
            shoulder = (px + dx * reach, py + dy * reach)
            for offset in range(-1_000_000, 1_000_001, 250_000):
                via = ((shoulder[0], shoulder[1] + offset) if dx
                       else (shoulder[0] + offset, shoulder[1]))
                result.append((compact(((px, py), shoulder, via)), via))
    return result


def place(board, path, via):
    if not all(board.point_free(layer, NET, *via, 600_000,
                                CLEARANCE, CLEARANCE, 25_000)
               for layer in board.cu):
        return False
    if not all(emit(board, a, b) for a, b in zip(path, path[1:])):
        return False
    board.via(NET, *via, 600_000, 300_000)
    return True


def main():
    before = sha(BOARD)
    seed = qr.QBoard(BOARD)
    pads = {p["ref"]: p for p in ir.physical_net_pads(seed, NET)}
    qualified = {}
    for ref in REFS:
        rows = []
        board = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(board)
        for path, via in candidates(pads[ref]):
            mark = board.mark()
            if place(board, path, via):
                rows.append((path, via))
            board.revert(mark)
        qualified[ref] = rows

    tested_pairs = tested_triples = 0
    compatible_pairs = {"|".join(pair): 0 for pair in itertools.combinations(REFS, 2)}
    witnesses = []
    board = qr.QBoard(BOARD); ir.inject_existing_via_obstacles(board)
    for pair in itertools.combinations(REFS, 2):
        for left, right in itertools.product(qualified[pair[0]], qualified[pair[1]]):
            tested_pairs += 1
            mark = board.mark()
            if place(board, *left) and place(board, *right):
                compatible_pairs["|".join(pair)] += 1
            board.revert(mark)

    # Cap only after exhaustive individual/pair qualification. A triple witness
    # is sufficient to advance to the existing complete-tree atomic harness.
    for rows in itertools.product(*(qualified[ref] for ref in REFS)):
        tested_triples += 1
        mark = board.mark()
        if all(place(board, *row) for row in rows):
            witnesses.append({ref: {"via_mm": [row[1][0] / 1e6, row[1][1] / 1e6],
                                    "path_mm": [[x / 1e6, y / 1e6] for x, y in row[0]]}
                              for ref, row in zip(REFS, rows)})
            break
        board.revert(mark)
        if tested_triples >= 250_000:
            break

    print(json.dumps({
        "schema": 1, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"net": NET, "refs": REFS, "native_layer": "F.Cu",
                     "width_mm": 0.2, "clearance_mm": 0.2,
                     "via_mm": [0.6, 0.3], "characterization_only": True},
        "individual_candidates_tested": {ref: len(candidates(pads[ref])) for ref in REFS},
        "individual_legal_fanouts": {ref: len(qualified[ref]) for ref in REFS},
        "pair_combinations_tested": tested_pairs,
        "compatible_pairs": compatible_pairs,
        "triple_combinations_tested": tested_triples,
        "triple_search_capped": tested_triples >= 250_000 and not witnesses,
        "coherent_witness": witnesses[0] if witnesses else None,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0 if witnesses else 2


if __name__ == "__main__":
    raise SystemExit(main())
