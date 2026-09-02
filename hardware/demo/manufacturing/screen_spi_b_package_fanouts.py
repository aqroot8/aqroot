#!/usr/bin/env python3
"""Bound coherent ordinary-via fanouts for the adjacent SPI-B package lands.

This is deliberately a package-reservation screen, not a partial router.  It
first qualifies each land in isolation, then exhaustively tests the compact
qualified cross-product while reserving every land in a package group before
any long haul is attempted.
"""

import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

WIDTH = CLEARANCE = 200_000
SITE_INDICES = range(8)
LAYERS = ("I2", "I3")
GROUPS = {
    "U1": (
        ("/SPI_B_SCK", "U1.4", "U7.18"),
        ("/SPI_B_MOSI", "U1.5", "U7.17"),
        ("/SPI_B_MISO", "U1.6", "U7.16"),
    ),
    "U9": (
        ("/SPI_B_SCK", "U9.30", "U1.4"),
        ("/SPI_B_MOSI", "U9.31", "U1.5"),
        ("/SPI_B_MISO", "U9.32", "U1.6"),
    ),
    "U7": (
        ("/SPI_B_MOSI", "U7.17", "U1.5"),
        ("/SPI_B_MISO", "U7.16", "U1.6"),
    ),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reserve(board, spec, layer, site):
    net, ref, target_ref = spec
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, net)}
    pad, target = pads[ref], pads[target_ref]
    near = "F" if ref.startswith("U1.") else "B"
    return qr.reserve_escape(
        board, net, pad, WIDTH, CLEARANCE, CLEARANCE,
        near=near, far=layer, via_dia=600_000, via_drill=300_000,
        target=(target["x"], target["y"]), site_index=site,
        site_separation=300_000,
    )


def qualify(spec):
    choices = []
    failures = {}
    for layer, site in itertools.product(LAYERS, SITE_INDICES):
        board = qr.QBoard(BOARD)
        ir.inject_existing_via_obstacles(board)
        result = reserve(board, spec, layer, site)
        if result.get("ok"):
            choices.append((layer, site))
        else:
            reason = result.get("reason", "UNKNOWN")
            failures[reason] = failures.get(reason, 0) + 1
    return choices, failures


def screen_group(name, specs):
    qualified = {}
    failures = {}
    for spec in specs:
        choices, failed = qualify(spec)
        qualified[spec[1]] = choices
        failures[spec[1]] = failed
    cases = 0
    winners = []
    if all(qualified[spec[1]] for spec in specs):
        for order in itertools.permutations(specs):
            pools = [qualified[spec[1]] for spec in order]
            for selections in itertools.product(*pools):
                cases += 1
                board = qr.QBoard(BOARD)
                ir.inject_existing_via_obstacles(board)
                results = []
                for spec, (layer, site) in zip(order, selections):
                    result = reserve(board, spec, layer, site)
                    results.append({"pad": spec[1], "layer": layer,
                                    "site_index": site, "result": result})
                    if not result.get("ok"):
                        break
                if len(results) == len(specs) and all(r["result"].get("ok") for r in results):
                    winners.append({"order": [spec[1] for spec in order],
                                    "reservations": results})
                    # One coexistence witness is sufficient; all individual
                    # alternatives remain recorded for the complete-tree replay.
                    break
            if winners:
                break
    return {
        "group": name,
        "individual_qualified": {
            ref: [{"layer": layer, "site_index": site} for layer, site in choices]
            for ref, choices in qualified.items()
        },
        "individual_failures": failures,
        "coexistence_cases_tested": cases,
        "coexistence_witness": winners[0] if winners else None,
    }


def main():
    before = sha(BOARD)
    groups = [screen_group(name, specs) for name, specs in GROUPS.items()]
    report = {
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": sha(BOARD) == before,
        "contract": {"width_mm": 0.2, "clearance_mm": 0.2,
                     "via_mm": [0.6, 0.3], "characterization_only": True},
        "groups": groups,
        "all_groups_have_coexistence": all(g["coexistence_witness"] for g in groups),
        "promotion_candidate": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_groups_have_coexistence"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
