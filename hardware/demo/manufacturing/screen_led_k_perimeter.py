#!/usr/bin/env python3
"""Bound explicit current-width perimeter corridors for the LED_K tree."""

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
NET = "/03_SPI_A_DISPLAY_SD/LED_K"
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
WIDTH = CLEARANCE = 300_000

# Reserve the connector launch first, move the long haul to a signal inner
# layer, and return near the driver.  This deliberately screens both sides of
# the FPC row and several west-perimeter lanes without moving components or
# disturbing accepted copper.
FAMILIES = tuple(
    (layer, launch_y, west_x, return_y, return_x)
    for layer in ("I2", "I3")
    for launch_y in (94_750_000, 95_000_000, 95_250_000,
                     96_750_000, 97_000_000, 97_250_000)
    for west_x in (4_000_000, 5_000_000, 6_000_000, 8_000_000)
    for return_y in (119_500_000, 120_500_000, 121_500_000, 122_500_000)
    for return_x in (3_750_000, 4_500_000, 5_250_000)
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


def segment_free(board, layer, left, right):
    distance = math.hypot(right[0] - left[0], right[1] - left[1])
    samples = max(1, math.ceil(distance / 25_000))
    return all(board.point_free(
        layer, NET,
        round(left[0] + (right[0] - left[0]) * step / samples),
        round(left[1] + (right[1] - left[1]) * step / samples),
        WIDTH, CLEARANCE, CLEARANCE, G=0)
        for step in range(samples + 1))


def route_family(path, family):
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import incremental_router as ir
    import qrouter as qr

    layer, launch_y, west_x, return_y, return_x = family
    board = qr.QBoard(str(path)); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    j = (pads["J1.2"]["x"], pads["J1.2"]["y"])
    u = (pads["U17.3"]["x"], pads["U17.3"]["y"])
    launch = (j[0], launch_y); landing = (return_x, return_y)
    nodes = ((j, launch, "F"),
             (launch, (west_x, launch_y), layer),
             ((west_x, launch_y), (west_x, return_y), layer),
             ((west_x, return_y), landing, layer),
             (landing, u, "B"))
    legs = []
    for left, right, route_layer in nodes:
        ok = segment_free(board, route_layer, left, right)
        legs.append({"layer": route_layer, "ok": ok,
                     "mm": math.hypot(right[0] - left[0], right[1] - left[1]) / 1e6})
        if not ok:
            return {"ok": False, "legs": legs}
        board.track(NET, route_layer, *left, *right, WIDTH)
    board.via(NET, *launch, 600_000, 300_000)
    board.via(NET, *landing, 600_000, 300_000)
    board.save(str(path))
    return {"ok": True, "legs": legs}


def launch_sites(path):
    """Prove the required connector-to-inner precondition before long hauls."""
    sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
    import incremental_router as ir
    import qrouter as qr

    board = qr.QBoard(str(path)); ir.inject_existing_via_obstacles(board)
    pads = {p["ref"]: p for p in ir.physical_net_pads(board, NET)}
    result = {}
    for ref in ("J1.2", "J1.3"):
        for far in ("I2", "I3"):
            sites = board.via_sites(
                "F", far, NET, pads[ref], WIDTH, 600_000,
                CLEARANCE, CLEARANCE, 50_000, span=3_000_000,
                via_drill=300_000, hole_clr=250_000, limit=64)
            result[f"{ref}:F:{far}"] = [[x / 1e6, y / 1e6] for x, y in sites]
    return result


def main():
    before_sha = sha256(BOARD); baseline = copper(BOARD)
    sites = launch_sites(BOARD)
    if not any(sites.values()):
        print(json.dumps({"schema": 1, "authoritative_board_sha256": before_sha,
                          "authoritative_unchanged": sha256(BOARD) == before_sha,
                          "launch_site_counts": {key: len(value) for key, value in sites.items()},
                          "families": len(FAMILIES), "families_reached": 0,
                          "precondition_failure": "NO_0P30_CLEAR_J1_LED_K_VIA_SITE",
                          "candidates": [], "cases": []}, indent=2, sort_keys=True))
        return 2
    cases = []; candidates = []
    for index, family in enumerate(FAMILIES):
        with tempfile.TemporaryDirectory(prefix="aqroot-demo-led-k-perimeter-") as tmp:
            scratch = Path(tmp) / "candidate.kicad_pcb"
            for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
                scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
            haul = route_family(scratch, family)
            local = None
            if haul["ok"]:
                run = subprocess.run([sys.executable, str(LOCAL), "LED_K_DRIVER_SENSE",
                                      "--route", str(scratch)], text=True, capture_output=True)
                if run.returncode not in (0, 2):
                    raise RuntimeError(run.stderr or run.stdout)
                local = json.loads(run.stdout)
            row = {"index": index, "family": [family[0], *[x / 1e6 for x in family[1:]]],
                   "haul_ok": haul["ok"], "failed_leg": next(
                       (i for i, leg in enumerate(haul["legs"]) if not leg["ok"]), None),
                   "local_ok": bool(local and local["result"].get("ok"))}
            if row["haul_ok"] and row["local_ok"]:
                # J1.3 is the duplicate fitted LED_K contact beside J1.2.
                board = pcbnew.LoadBoard(str(scratch)); net = board.FindNet(NET)
                points = sorted((p.GetPosition() for f in board.GetFootprints()
                                 if f.GetReference() == "J1" for p in f.Pads()
                                 if p.GetNumber() in ("2", "3")), key=lambda p: p.x)
                track = pcbnew.PCB_TRACK(board); track.SetNet(net); track.SetLayer(pcbnew.F_Cu)
                track.SetWidth(WIDTH); track.SetStart(points[0]); track.SetEnd(points[1]); board.Add(track)
                pcbnew.SaveBoard(str(scratch), board)
                drc = scratch.with_suffix(".drc.json")
                subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                                "--format", "json", "--units", "mm", "--severity-all",
                                "--schematic-parity", "-o", str(drc), str(scratch)],
                               text=True, capture_output=True)
                violations = json.loads(drc.read_text()).get("violations", [])
                types = Counter(v.get("type", "unknown") for v in violations)
                attributable = [v for v in violations if v.get("type") not in ACCEPTED]
                ledger_path = scratch.with_suffix(".ledger.json")
                subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                                str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
                ledger = json.loads(ledger_path.read_text())
                target = next(x for x in ledger["nets"] if x["net"] == NET)
                after = copper(scratch); added = after - baseline; removed = baseline - after
                row.update({"drc_types": dict(types), "attributable_drc": len(attributable),
                            "open_edges": target["open_edges"], "added_items": sum(added.values()),
                            "removed_items": sum(removed.values())})
                if not attributable and target["open_edges"] == 0 and not removed and all(
                        item[0] == NET for item in added):
                    candidate = Path(tempfile.gettempdir()) / f"aqroot-led-k-{index}.kicad_pcb"
                    candidate.write_bytes(scratch.read_bytes())
                    row.update({"candidate": str(candidate), "candidate_sha256": sha256(candidate)})
                    candidates.append(row)
            cases.append(row)
    print(json.dumps({"schema": 1, "authoritative_board_sha256": before_sha,
                      "authoritative_unchanged": sha256(BOARD) == before_sha,
                      "families": len(FAMILIES), "candidates": candidates,
                      "cases": cases}, indent=2, sort_keys=True))
    return 0 if candidates else 2


if __name__ == "__main__":
    raise SystemExit(main())
