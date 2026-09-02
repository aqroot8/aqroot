#!/usr/bin/env python3
"""Bound explicit F.Cu perimeter feeds for the retained LED_A tree."""

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
NET = "/03_SPI_A_DISPLAY_SD/LED_A"
SPINE = ("LED_A_R73_R70", "LED_A_R70_R72", "LED_A_R72_R71")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}

# J1.1 must leave perpendicular to the 0.5 mm FPC row.  These bounded
# corridors reserve that launch first, then approach the ballast spine from
# below, above, or around its east perimeter without changing the locked
# 0.30 mm LED-current width.
FAMILIES = tuple(
    ((44_910_000, launch_y), (turn_x, launch_y), (turn_x, spine_y))
    for launch_y in (94_750_000, 95_000_000, 95_250_000)
    for turn_x in (41_500_000, 42_500_000, 43_500_000, 45_500_000, 46_000_000)
    for spine_y in (92_000_000, 92_500_000, 93_000_000, 93_500_000)
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(path):
    result = Counter()
    board = pcbnew.LoadBoard(str(path))
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


def route_feed(path, waypoints):
    # Reuse the qualified obstacle model and connector directly, but keep this
    # current-path-specific family out of the generic low-speed route catalog.
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import qrouter as qr
    import incremental_router as ir

    board = qr.QBoard(path)
    ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    nodes = [(pads["J1.1"]["x"], pads["J1.1"]["y"]), *waypoints,
             (pads["R71.2"]["x"], pads["R71.2"]["y"])]
    legs = []
    for left, right in zip(nodes, nodes[1:]):
        distance = math.hypot(right[0] - left[0], right[1] - left[1])
        samples = max(1, math.ceil(distance / 25_000))
        clear = all(board.point_free(
            "F", NET,
            round(left[0] + (right[0] - left[0]) * step / samples),
            round(left[1] + (right[1] - left[1]) * step / samples),
            300_000, 200_000, 200_000, G=0)
            for step in range(samples + 1))
        leg = {"ok": clear, "reason": None if clear else "BLOCKED_SEGMENT",
               "mm": distance / 1e6}
        legs.append(leg)
        if not clear:
            break
        board.track(NET, "F", *left, *right, 300_000)
    board.save(path)
    return {"ok": len(legs) == len(nodes) - 1 and all(x.get("ok") for x in legs),
            "legs": legs}


def main():
    before_sha = sha256(BOARD)
    baseline = copper(BOARD)
    cases = []
    candidates = []
    for index, family in enumerate(FAMILIES):
        with tempfile.TemporaryDirectory(prefix="aqroot-demo-led-a-perimeter-") as tmp:
            scratch = Path(tmp) / "candidate.kicad_pcb"
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
            feed = route_feed(scratch, family)
            spine = []
            if feed["ok"]:
                for leg in SPINE:
                    run = subprocess.run([sys.executable, str(LOCAL), leg, "--route", str(scratch)],
                                         text=True, capture_output=True)
                    if run.returncode not in (0, 2):
                        raise RuntimeError(run.stderr or run.stdout)
                    spine.append(json.loads(run.stdout))
                    if not spine[-1]["result"].get("ok"):
                        break
            row = {"index": index, "waypoints_mm": [[x / 1e6, y / 1e6] for x, y in family],
                   "feed_ok": feed["ok"], "feed_reason":
                   next((x.get("reason") for x in feed["legs"] if not x.get("ok")), None),
                   "feed_failed_leg": next((i for i, x in enumerate(feed["legs"])
                                             if not x.get("ok")), None),
                   "spine_ok": len(spine) == len(SPINE) and
                   all(x["result"].get("ok") for x in spine)}
            if row["feed_ok"] and row["spine_ok"]:
                drc = scratch.with_suffix(".drc.json")
                subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                                "--format", "json", "--units", "mm", "--severity-all",
                                "--schematic-parity", "-o", str(drc), str(scratch)],
                               check=True, text=True, capture_output=True)
                violations = json.loads(drc.read_text()).get("violations", [])
                types = Counter(v.get("type", "unknown") for v in violations)
                attributable = [v for v in violations if v.get("type") not in ACCEPTED]
                ledger_path = scratch.with_suffix(".ledger.json")
                subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                                str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
                ledger = json.loads(ledger_path.read_text())
                target = next(x for x in ledger["nets"] if x["net"] == NET)
                added = copper(scratch) - baseline
                removed = baseline - copper(scratch)
                row.update({"drc_types": dict(types), "attributable_drc": len(attributable),
                            "open_edges": target["open_edges"], "added_items": sum(added.values()),
                            "removed_items": sum(removed.values())})
                if not attributable and target["open_edges"] == 0 and not removed and all(
                        item[0] == NET and item[1] != "VIA" for item in added):
                    candidate = Path(tempfile.gettempdir()) / f"aqroot-led-a-{index}.kicad_pcb"
                    candidate.write_bytes(scratch.read_bytes())
                    row["candidate"] = str(candidate)
                    row["candidate_sha256"] = sha256(candidate)
                    candidates.append(row)
            cases.append(row)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before_sha,
                      "authoritative_unchanged": sha256(BOARD) == before_sha,
                      "families": len(FAMILIES), "candidates": candidates,
                      "cases": cases}, indent=2, sort_keys=True))
    return 0 if candidates else 2


if __name__ == "__main__":
    raise SystemExit(main())
