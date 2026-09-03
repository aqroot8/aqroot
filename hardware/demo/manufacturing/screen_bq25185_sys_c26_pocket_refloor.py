#!/usr/bin/env python3
"""Screen one-complete-net withdrawals around a boxed BQ25185 SYS land.

Despite the historical filename, ``--wall`` supports every governed SYS land
registered by the shared dogleg enumerator.
"""

import argparse, hashlib, itertools, json, math, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path
import pcbnew
import enumerate_bq25185_sys_dogleg_landings as landings

BOARD, DEFAULT_WALL, RADIUS = landings.BOARD, "C26.2", 5_000_000

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def last_json(output):
    decoder, records = json.JSONDecoder(), []
    for offset, char in enumerate(output):
        if char == "{":
            try:
                record, end = decoder.raw_decode(output[offset:])
                records.append((end, record))
            except json.JSONDecodeError:
                pass
    if not records: raise RuntimeError(f"subprocess emitted no JSON: {output!r}")
    return max(records, key=lambda row: row[0])[1]

def inventory(path, wall):
    board = pcbnew.LoadBoard(str(path))
    reference, pad_number = wall.split(".", 1)
    fp = board.FindFootprintByReference(reference)
    origin = next(p.GetPosition() for p in fp.Pads()
                  if p.GetNumber() == pad_number)
    rows = {}
    for item in board.GetTracks():
        points = [item.GetPosition()] if item.GetClass() == "PCB_VIA" else [item.GetStart(), item.GetEnd()]
        distance = min(math.hypot(p.x-origin.x, p.y-origin.y) for p in points)
        net = str(item.GetNetname())
        if distance <= RADIUS and net and net != landings.NET:
            row = rows.setdefault(net, {"nearby_objects": 0, "minimum_distance_mm": distance/1e6})
            row["nearby_objects"] += 1
            row["minimum_distance_mm"] = min(row["minimum_distance_mm"], distance/1e6)
    return dict(sorted(rows.items(), key=lambda pair: (pair[1]["minimum_distance_mm"], pair[0])))

def withdraw(path, net):
    board = pcbnew.LoadBoard(str(path))
    items = [item for item in list(board.GetTracks()) if str(item.GetNetname()) == net]
    layers = Counter("VIA" if item.GetClass() == "PCB_VIA" else item.GetLayerName() for item in items)
    for item in items: board.Remove(item)
    board.Save(str(path))
    return {"objects": len(items), "layers": dict(layers)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", type=Path)
    parser.add_argument("--net")
    parser.add_argument("--wall", choices=tuple(landings.CASES),
                        default=DEFAULT_WALL)
    parser.add_argument("--only-net", action="append",
                        help="screen only this inventoried net (repeatable)")
    parser.add_argument("--max-withdrawals", type=int, choices=(1, 2), default=1,
                        help="screen complete-net withdrawal sets up to this size")
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(withdraw(args.prepare, args.net)))
        return 0
    wall = args.wall
    before, nearby, cases = sha256(BOARD), inventory(BOARD, wall), []
    if args.only_net:
        unknown = sorted(set(args.only_net) - set(nearby))
        if unknown:
            parser.error(f"net is not in the {wall} pocket inventory: {unknown}")
        nearby = {net: nearby[net] for net in args.only_net}
    withdrawal_sets = [combo for size in range(1, args.max_withdrawals + 1)
                       for combo in itertools.combinations(nearby, size)]
    with tempfile.TemporaryDirectory(prefix=f"aqroot-demo-sys-{wall.lower().replace('.', '-')}-pocket-") as td:
        for index, nets in enumerate(withdrawal_sets):
            scratch = Path(td)/f"case-{index}.kicad_pcb"
            scratch.write_bytes(BOARD.read_bytes())
            removed = []
            for net in nets:
                prepared = subprocess.run([sys.executable, __file__, "--prepare",
                                           str(scratch), "--net", net], check=True,
                                          text=True, capture_output=True)
                removed.append({"net": net, **last_json(prepared.stdout)})
            run = subprocess.run([sys.executable, str(Path(landings.__file__)), "--board", str(scratch), "--pad", wall], check=True, text=True, capture_output=True)
            row = json.loads(run.stdout)["pads"][0]
            cases.append({"withdrawn_nets": list(nets), "withdrawn": removed,
                          "candidate_count": row["candidate_count"],
                          "first_candidates": row["candidates"][:4],
                          "blockers": row["blockers"]})
    winners = [case for case in cases if case["candidate_count"]]
    print(json.dumps({"schema": 1, "wall": wall, "authoritative_board_sha256": before,
        "authoritative_unchanged": sha256(BOARD) == before,
        "contract": {"radius_mm": RADIUS/1e6,
                     "withdrawal_scope": f"complete copper net sets of size 1..{args.max_withdrawals}",
                     "maximum_withdrawals": args.max_withdrawals,
                     "sys_width_mm": 0.5, "sys_clearance_mm": 0.25,
                     "power_via_mm": {"diameter": 0.9, "drill": 0.4},
                     "characterization_only": True,
                     "promotion_requires_complete_sys_tree_and_all_net_replay": True},
        "inventory": nearby, "cases_tested": len(cases),
        "winning_withdrawal_sets": winners, "cases": cases,
        "promotion_candidate": False}, indent=2, sort_keys=True))
    return 0 if winners else 2

if __name__ == "__main__": raise SystemExit(main())
