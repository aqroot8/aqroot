#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- re-prove a promotion from the two board files ALONE.

`route_maze_batch.py` gates its own candidate before it writes it.  That is
necessary but it is not independent: the same process that proposed the copper
decided it was legal.  This module re-derives every promotion property a second
time, from the committed board and the promoted board, without reading the
driver's scratch tree, its ledger or its evidence JSON:

  * NO pre-existing track or via was moved or removed;
  * every ADDED object lies on one of the nets the promotion claimed;
  * every added track meets the width the caller asserts, and every added via
    meets the drill and annular-ring floors it asserts;
  * the zone inventory changed by exactly the pours the caller asserts, and no
    surviving zone's net, layer, outline or fill parameters changed;
  * real KiCad `--refill-zones --save-board --severity-all --schematic-parity`
    DRC on the promoted board reports only the inherited classes, with ZERO
    attributable violations and ZERO schematic-parity errors;
  * the promoted board is fill-stable -- a second refill changes nothing;
  * the retained safety rules are still live text in the `.kicad_dru`.

It is read-only with respect to `hardware/demo/kicad/aqroot-demo/`: both boards
it inspects are copies in a temporary directory.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"
SUFFIXES = (".kicad_pcb", ".kicad_dru", ".kicad_pro")

# The three report classes this board has carried since long before the maze
# router existed; they are inherited, not attributable to any promotion.
INHERITED = {"lib_footprint_issues": 199, "hole_clearance": 5,
             "solder_mask_bridge": 1}

# Retained contracts that must still be LIVE RULE TEXT, not merely believed.
DRU_CONTRACTS = {
    "D-269_bat_main_routed_clearance": "BAT_MAIN routed clearance",
    "D-186_bat_main_class": "BAT_MAIN",
    "annular_ring_floor": "annular_width (min 0.125mm)",
    "power_via_drill_floor": "POWER-class vias use the 0.40 mm drill",
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def objects(path):
    """Every track and via as a geometry signature, independent of its UUID."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = set()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            out.add(("via", t.GetNetname(), t.GetStart().x, t.GetStart().y,
                     t.GetWidth(), t.GetDrill()))
        else:
            out.add(("trk", t.GetNetname(), board.GetLayerName(t.GetLayer()),
                     t.GetStart().x, t.GetStart().y,
                     t.GetEnd().x, t.GetEnd().y, t.GetWidth()))
    return out


def zone_sigs(path):
    """Every non-rule-area pour's net, layers, name, fill parameters, outline."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    out = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        o = z.Outline().Outline(0)
        out.append((z.GetNetname(),
                    tuple(board.GetLayerName(l) for l in z.GetLayerSet().Seq()),
                    z.GetZoneName(), z.GetMinThickness(), z.GetLocalClearance(),
                    int(z.GetIslandRemovalMode()), int(z.GetPadConnection()),
                    tuple((o.CPoint(i).x, o.CPoint(i).y)
                          for i in range(o.PointCount()))))
    return sorted(out)


def drc(path, out):
    """Real KiCad DRC, refilling and saving the copy it is handed."""
    subprocess.run([
        "kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
        "--format", "json", "--units", "mm", "--severity-all",
        "--schematic-parity", "-o", str(out), str(path),
    ], text=True, capture_output=True)
    report = json.loads(Path(out).read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v["type"]] = counts.get(v["type"], 0) + 1
    return dict(
        counts=counts,
        attributable=[v for v in report.get("violations", [])
                      if v["type"] not in INHERITED],
        schematic_parity_errors=len(report.get("schematic_parity", [])),
        unconnected_items=len(report.get("unconnected_items", [])))


def stage(rev, work):
    """A project-faithful copy of the board at `rev` (or of the worktree)."""
    cell = Path(work)
    cell.mkdir(parents=True, exist_ok=True)
    for suffix in SUFFIXES:
        target = (cell / BOARD.name).with_suffix(suffix)
        if rev is None:
            shutil.copyfile(BOARD.with_suffix(suffix), target)
        else:
            src = BOARD.with_suffix(suffix).relative_to(ROOT)
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "show", "%s:%s" % (rev, src)],
                capture_output=True, check=True).stdout
            target.write_bytes(blob)
    return cell / BOARD.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD",
                    help="git revision holding the PRE-promotion board")
    ap.add_argument("--nets", required=True,
                    help="comma-separated nets the promotion claimed")
    ap.add_argument("--plane", action="append", default=[],
                    help="NET:LAYER pour the promotion claims to have ADDED; "
                         "repeatable, omit when no pour was added")
    ap.add_argument("--track-width", type=int, default=0,
                    help="nm floor every added track must meet")
    ap.add_argument("--via-drill", type=int, default=0,
                    help="nm floor every added via drill must meet")
    ap.add_argument("--annular", type=int, default=125000,
                    help="nm floor every added via's annular ring must meet")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    nets = [n for n in a.nets.split(",") if n]
    planes = sorted(tuple(p.split(":", 1)) for p in a.plane)

    tmp = Path(tempfile.mkdtemp(prefix="aqroot-demo-verify-"))
    pre, post = stage(a.ref, tmp / "pre"), stage(None, tmp / "post")

    before, after = objects(pre), objects(post)
    removed = sorted(str(x) for x in (before - after))
    added = sorted(after - before)
    added_nets = sorted({x[1] for x in added})
    tracks = [x for x in added if x[0] == "trk"]
    vias = [x for x in added if x[0] == "via"]

    zpre, zpost = zone_sigs(pre), zone_sigs(post)
    zadded = [z for z in zpost if z not in zpre]
    zlost = [z for z in zpre if z not in zpost]
    zclaim = sorted((z[0], z[1][0]) for z in zadded)

    first = drc(post, tmp / "drc-1.json")
    refilled = sha256_file(post)
    second = drc(post, tmp / "drc-2.json")
    fill_stable = refilled == sha256_file(post)

    dru = (post.with_suffix(".kicad_dru")).read_text(encoding="utf-8")
    contracts = {k: (v in dru) for k, v in DRU_CONTRACTS.items()}

    widths = sorted({x[7] for x in tracks})
    layers = sorted({x[2] for x in tracks})
    vdims = sorted({(x[4], x[5]) for x in vias})

    checks = dict(
        nothing_removed=not removed,
        added_only_on_claimed_nets=set(added_nets) <= set(nets),
        zone_inventory_as_claimed=(not zlost and zclaim == planes),
        track_width_floor_met=(not a.track_width
                               or all(w >= a.track_width for w in widths)),
        via_drill_floor_met=(not a.via_drill
                             or all(d >= a.via_drill for _dia, d in vdims)),
        annular_floor_met=all((dia - d) / 2 >= a.annular for dia, d in vdims),
        drc_zero_attributable=not first["attributable"],
        drc_inherited_within_baseline=all(
            first["counts"].get(k, 0) <= n for k, n in INHERITED.items()),
        schematic_parity_clean=first["schematic_parity_errors"] == 0,
        fill_stable=fill_stable,
        dru_contracts_live=all(contracts.values()),
        beta_v2_untouched=not subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "hardware/beta-v2"],
            capture_output=True, text=True).stdout.strip(),
    )

    report = dict(
        schema=1, ref=a.ref, claimed_nets=nets, claimed_planes=planes,
        pre_board_sha256=sha256_file(pre),
        promoted_board_sha256=sha256_file(BOARD),
        objects_removed=len(removed), removed_sample=removed[:8],
        objects_added=len(added), added_object_nets=added_nets,
        added_tracks=len(tracks), added_vias=len(vias),
        added_track_widths_nm=widths, added_track_layers=layers,
        added_via_dia_drill_nm=[list(v) for v in vdims],
        zones_added=zadded, zones_removed=zlost,
        drc=first, drc_second_pass=second, dru_contracts=contracts,
        checks=checks, verdict="PASS" if all(checks.values()) else "FAIL",
    )
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
