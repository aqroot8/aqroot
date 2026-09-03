#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- read-only screen for a pour that is expected to close edges
BY ITSELF, with no stitch track and no stitch barrel.

`screen_inner_plane.py` answers "does a pour FILL, and how close does it come
to each pad".  That is the right question for a net that owns NO copper, where
every pad must still be planted by `maze3d.stitch_net`.  It is the wrong
question for a net that ALREADY owns copper, because there the pour can close
an edge three ways the fill-and-reach measurement cannot see:

  * `connect_pads yes` bonds the pour directly to every same-net pad it
    overlaps on its own layer -- no via, no track, no escape;
  * an EXISTING through barrel that was planted for another plane passes
    through the new layer too, so the new pour inherits it;
  * two islands of an existing pour on a different layer become one net once
    barrels on both of them land in a single island of the new pour.

None of those is a proposal the router makes, so none of them is visible until
the real KiCad fill engine has run and the fitted-pad ledger has been recounted.
This module runs exactly that experiment on a scratch copy and reports the
connectivity delta, the DRC delta and the fill geometry.  It writes nothing to
`hardware/demo/kicad/aqroot-demo/` and proposes no copper.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from screen_inner_plane import insert_zone, zone_sexpr, measure

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
LEDGER = Path(__file__).resolve().parent / "routing_ledger.py"

# Same inherited-class pins as the promotion gate, so a screen and a gate
# cannot disagree about what "attributable" means.
INHERITED = {"lib_footprint_issues": 199, "hole_clearance": 5,
             "solder_mask_bridge": 1}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ledger(board, out):
    subprocess.run([sys.executable, str(LEDGER), "--board", str(board),
                    str(out)], check=True, capture_output=True, text=True)
    return json.loads(Path(out).read_text())


def screen(net, layer, work, clearance=0.25, islands=0):
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
        (work / BOARD.name).with_suffix(suffix).write_bytes(
            BOARD.with_suffix(suffix).read_bytes())
    scratch = work / BOARD.name
    name = "%s %s PLANE" % (layer.split(".")[0], net)
    insert_zone(scratch, zone_sexpr(net, layer, name, clearance=clearance,
                                    islands=islands))

    drc_json = work / "drc.json"
    done = subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(drc_json), str(scratch),
    ], text=True, capture_output=True)
    report = json.loads(drc_json.read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    attributable = [v for v in report.get("violations", [])
                    if v.get("type") not in INHERITED]

    base = ledger(BOARD, work / "ledger-before.json")
    after = ledger(scratch, work / "ledger-after.json")
    b = {r["net"]: r["open_edges"] for r in base["nets"]}
    a = {r["net"]: r["open_edges"] for r in after["nets"]}
    geom = measure(scratch, net, layer)
    return dict(
        net=net, layer=layer, zone_name=name, zone_clearance_mm=clearance,
        island_removal_mode=islands,
        drc_exit=done.returncode, drc_types=counts,
        attributable_drc=attributable,
        inherited_within_baseline=all(counts.get(k, 0) <= n
                                      for k, n in INHERITED.items()),
        filled_area_mm2=geom["filled_area_mm2"], fill_islands=geom["islands"],
        island_area_mm2=geom["island_area_mm2"],
        retained_open_edges_before=base["connectivity"]["retained_open_edges"],
        retained_open_edges_after=after["connectivity"]["retained_open_edges"],
        open_retained_nets_before=base["connectivity"]["open_retained_nets"],
        open_retained_nets_after=after["connectivity"]["open_retained_nets"],
        net_open_edges_before=b.get(net), net_open_edges_after=a.get(net),
        nets_improved=sorted(n for n in b if a.get(n, 0) < b[n]),
        nets_regressed=sorted(n for n, v in a.items() if v > b.get(n, v)),
        candidate_sha256=sha256(scratch),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", required=True)
    ap.add_argument("--layers", required=True,
                    help="comma-separated, screened independently")
    ap.add_argument("--work", required=True)
    ap.add_argument("--clearance", type=float, default=0.25)
    ap.add_argument("--islands", type=int, default=0,
                    help="island_removal_mode for the new pour (0 = remove)")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    before = sha256(BOARD)
    cases = []
    for layer in a.layers.split(","):
        cell = Path(a.work) / ("%s_%s" % (a.net.strip("/+").replace("/", "_"),
                                          layer.replace(".", "_")))
        c = screen(a.net, layer, cell, a.clearance, a.islands)
        cases.append(c)
        print("  %-7s area %8.1f mm2  islands %3d  edges %d -> %d  "
              "attributable DRC %d"
              % (layer, c["filled_area_mm2"], c["fill_islands"],
                 c["retained_open_edges_before"],
                 c["retained_open_edges_after"], len(c["attributable_drc"])),
              file=sys.stderr, flush=True)
    out = dict(schema=1, net=a.net, authoritative_board_sha256=before,
               authoritative_unchanged=(before == sha256(BOARD)), cases=cases)
    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
