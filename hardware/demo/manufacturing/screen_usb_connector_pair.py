#!/usr/bin/env python3
"""Exhaustively screen the F.Cu-only USB-C connector-side pair trees."""

import hashlib
import itertools
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
import sys
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

PAIR = {
    "N": ("/01_POWER_TREE/USB_D_CONN_N", ("J3.A7", "J3.B7", "U10.1")),
    "P": ("/01_POWER_TREE/USB_D_CONN_P", ("J3.A6", "J3.B6", "U10.3")),
}
WIDTH = 230_000
CLEARANCE = 200_000
GRID = 25_000


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def route_tree(board, polarity, order):
    net, expected = PAIR[polarity]
    pads = {pad["ref"]: pad for pad in ir.physical_net_pads(board, net)}
    if set(pads) != set(expected):
        raise RuntimeError(f"{net}: unexpected pads {sorted(pads)}")
    results = []
    root = order[0]
    for target in order[1:]:
        result = qr.connect_role(board, net, pads[root], pads[target], "F",
                                 WIDTH, CLEARANCE, CLEARANCE, G=GRID)
        results.append({"from": root, "to": target, "result": result})
        if not result.get("ok"):
            break
    return results


def run_case(source, work, pair_order, n_order, p_order):
    tag = "".join(pair_order) + "-" + "_".join(n_order) + "-" + "_".join(p_order)
    scratch = work / f"usb-conn-{tag}.kicad_pcb"
    scratch.write_bytes(source.read_bytes())
    board = qr.QBoard(scratch)
    ir.inject_existing_via_obstacles(board)
    orders = {"N": n_order, "P": p_order}
    routes = {}
    for polarity in pair_order:
        routes[polarity] = route_tree(board, polarity, orders[polarity])
        if len(routes[polarity]) != 2 or not all(
                leg["result"].get("ok") for leg in routes[polarity]):
            break
    complete = set(routes) == {"N", "P"} and all(
        len(legs) == 2 and all(leg["result"].get("ok") for leg in legs)
        for legs in routes.values())
    return {"pair_order": list(pair_order), "node_orders": {
                "N": list(n_order), "P": list(p_order)},
            "routes": routes, "complete": complete}


def main():
    before = sha256(BOARD)
    permutations = {key: list(itertools.permutations(value[1]))
                    for key, value in PAIR.items()}
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-connector-") as temporary:
        work = Path(temporary)
        cases = [run_case(BOARD, work, pair_order, n_order, p_order)
                 for pair_order in (("N", "P"), ("P", "N"))
                 for n_order in permutations["N"]
                 for p_order in permutations["P"]]
    complete = [case for case in cases if case["complete"]]
    failure_summary = {}
    first_tree_complete = {"N": 0, "P": 0}
    for case in cases:
        if case["complete"]:
            continue
        failed = False
        for stage, polarity in enumerate(case["pair_order"], start=1):
            legs = case["routes"].get(polarity, [])
            if len(legs) == 2 and all(leg["result"].get("ok") for leg in legs):
                if stage == 1:
                    first_tree_complete[polarity] += 1
                continue
            reason = next((leg["result"].get("reason", "UNKNOWN") for leg in legs
                           if not leg["result"].get("ok")), "NOT_ATTEMPTED")
            key = f"stage{stage}:{polarity}:{reason}"
            failure_summary[key] = failure_summary.get(key, 0) + 1
            failed = True
            break
        if not failed:
            raise RuntimeError("incomplete case has no failed stage")
    print(json.dumps({
        "schema": 1,
        "authoritative_board_sha256": before,
        "authoritative_unchanged": before == sha256(BOARD),
        "contract": "both three-pad USB-C trees; F.Cu only; 0.23 mm width; 0.20 mm clearance; zero vias",
        "cases_tested": len(cases),
        "complete_case_count": len(complete),
        "first_tree_complete_cases": first_tree_complete,
        "failure_summary": failure_summary,
        "complete_cases": complete,
        "promotion_candidate": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
