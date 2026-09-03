#!/usr/bin/env python3
"""Route and fully gate the fitted USB_VBUS_RAW front-side power tree."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "hardware/demo/kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).with_name("routing_ledger.py")
NET = "/01_POWER_TREE/USB_VBUS_RAW"
PADS = ("C20.1", "J3.A4", "J3.A9", "J3.B4", "J3.B9", "R35.1", "U10.5")
ACCEPTED = {"lib_footprint_issues", "hole_clearance", "solder_mask_bridge"}
sys.path.insert(0, str(ROOT / "hardware/beta-v2/checks"))
import incremental_router as ir  # noqa: E402
import qrouter as qr  # noqa: E402

WIDTH = 500_000
CLEARANCE = 200_000
POFV_DIAMETER = 350_000
POFV_DRILL = 200_000


def add_rule_area(raw, name, cx, cy):
    zone = pcbnew.ZONE(raw)
    zone.SetIsRuleArea(True)
    zone.SetZoneName(name)
    zone.SetLayerSet(pcbnew.LSET.AllCuMask(raw.GetCopperLayerCount()))
    zone.SetDoNotAllowTracks(False)
    zone.SetDoNotAllowVias(False)
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowZoneFills(False)
    zone.SetDoNotAllowFootprints(False)
    outline = zone.Outline()
    outline.NewOutline()
    # Keep the exception wholly inside the 0.60 x 1.15 mm connector land.
    for x, y in ((cx - 250_000, cy - 250_000),
                 (cx + 250_000, cy - 250_000),
                 (cx + 250_000, cy + 250_000),
                 (cx - 250_000, cy + 250_000)):
        outline.Append(x, y)
    raw.Add(zone)


def route_candidate(scratch, pads, c20_site=0, u10_site=0):
    raw = pcbnew.LoadBoard(str(scratch))
    for ref, name in (("J3.A9", "USB_VBUS_J3_A9_POFV"),
                      ("J3.A4", "USB_VBUS_J3_A4_POFV")):
        add_rule_area(raw, name, pads[ref]["x"], pads[ref]["y"])
    pcbnew.SaveBoard(str(scratch), raw)

    board = qr.QBoard(scratch)
    ir.inject_existing_via_obstacles(board)
    # Local load/decoupling branch stays on F.Cu.
    routes = [qr.connect_role(board, NET, pads["R35.1"], pads["C20.1"],
                              "F", WIDTH, CLEARANCE, CLEARANCE, G=25_000)]
    if not routes[-1].get("ok"):
        return board, routes

    # Escape the two non-connector endpoints with ordinary power vias.  The
    # connector islands themselves use only the two qualified in-land POFVs.
    c20 = qr.reserve_escape(board, NET, pads["C20.1"], WIDTH, CLEARANCE,
                            CLEARANCE, near="F", far="B", via_dia=800_000,
                            via_drill=400_000, target=(40_600_000, 146_380_000),
                            site_index=c20_site, site_separation=300_000)
    routes.append(c20)
    if not c20.get("ok"):
        return board, routes
    # U10.5 is a 0.60 mm-wide SOT-23 land.  Use the governed 0.35 mm
    # VBUS_CHG minimum only for its package neck; the B.Cu haul stays 0.50 mm.
    u10 = qr.reserve_escape(board, NET, pads["U10.5"], 350_000, CLEARANCE,
                            CLEARANCE, near="F", far="B", via_dia=800_000,
                            via_drill=400_000, target=(45_400_000, 146_380_000),
                            site_index=u10_site, site_separation=300_000)
    routes.append(u10)
    if not u10.get("ok"):
        return board, routes

    a9 = (pads["J3.A9"]["x"], pads["J3.A9"]["y"])
    a4 = (pads["J3.A4"]["x"], pads["J3.A4"]["y"])
    board.via(NET, *a9, POFV_DIAMETER, POFV_DRILL)
    board.via(NET, *a4, POFV_DIAMETER, POFV_DRILL)
    for left, right in ((c20["via"], a9), (a9, a4), (a4, u10["via"])):
        joined = qr.join_reserved(board, NET, left, right, WIDTH, CLEARANCE,
                                  CLEARANCE, layer="B")
        routes.append(joined)
        if not joined.get("ok"):
            return board, routes
    return board, routes


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper(board):
    result = Counter()
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--c20-site", type=int, default=0)
    parser.add_argument("--u10-site", type=int, default=0)
    args = parser.parse_args()
    before_sha = sha256(BOARD)
    baseline = copper(pcbnew.LoadBoard(str(BOARD)))
    with tempfile.TemporaryDirectory(prefix="aqroot-demo-usb-vbus-raw-") as temporary:
        work = Path(temporary)
        scratch = work / BOARD.name
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            scratch.with_suffix(suffix).write_bytes(BOARD.with_suffix(suffix).read_bytes())
        baseline_ledger_path = work / "baseline-ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(baseline_ledger_path)], check=True, stdout=subprocess.DEVNULL)
        baseline_ledger = json.loads(baseline_ledger_path.read_text())
        baseline_row = next(r for r in baseline_ledger["nets"] if r["net"] == NET)
        if baseline_row["open_edges"] == 0:
            print(json.dumps({"authoritative_board_sha256": before_sha,
                              "promotion_candidate": False,
                              "refusal": "target is already connected"}, indent=2))
            return 2
        seed = qr.QBoard(scratch)
        physical = ir.physical_net_pads(seed, NET)
        if {p["ref"] for p in physical} != set(PADS):
            raise RuntimeError(f"unexpected fitted pads: {sorted(p['ref'] for p in physical)}")
        pads = {p["ref"]: p for p in physical}
        board, routes = route_candidate(scratch, pads, args.c20_site, args.u10_site)
        board.save(scratch)
        drc = work / "drc.json"
        checked = subprocess.run([
            "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
            "--format", "json", "--units", "mm", "--severity-all",
            "--schematic-parity", "-o", str(drc), str(scratch),
        ], text=True, capture_output=True)
        violations = json.loads(drc.read_text()).get("violations", [])
        types = Counter(v.get("type", "unknown") for v in violations)
        attributable = [v for v in violations if v.get("type") not in ACCEPTED]
        after = copper(pcbnew.LoadBoard(str(scratch)))
        removed = baseline - after
        added = after - baseline
        wrong = [list(item) for item in added if item[0] != NET]
        ledger_path = work / "ledger.json"
        subprocess.run([sys.executable, str(LEDGER), "--board", str(scratch),
                        str(ledger_path)], check=True, stdout=subprocess.DEVNULL)
        ledger = json.loads(ledger_path.read_text())
        row = next(r for r in ledger["nets"] if r["net"] == NET)
        promotion = (len(routes) == len(BRANCHES) and all(r.get("ok") for r in routes)
                     and row["open_edges"] == 0 and not attributable
                     and not removed and not wrong)
        candidate = scratch.read_bytes()
        if args.candidate and promotion:
            args.candidate.write_bytes(candidate)
        if args.promote:
            if not promotion or sha256(BOARD) != before_sha:
                raise RuntimeError("refuse promotion: gate failed or authority changed")
            BOARD.write_bytes(candidate)
        report = {
            "schema": 1, "authoritative_board_sha256": before_sha,
            "authoritative_unchanged": sha256(BOARD) == before_sha,
            "baseline_open_edges": baseline_row["open_edges"], "routes": routes,
            "drc_exit": checked.returncode, "drc_types": dict(types),
            "attributable_drc": attributable,
            "removed_accepted_copper_items": sum(removed.values()),
            "added_items": sum(added.values()), "wrong_net_additions": wrong,
            "target_open_edges": row["open_edges"], "connectivity": ledger["connectivity"],
            "promotion_candidate": promotion,
            "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if promotion else 2


if __name__ == "__main__":
    raise SystemExit(main())
