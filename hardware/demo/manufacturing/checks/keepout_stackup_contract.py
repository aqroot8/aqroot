#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AQROOT Demo -- the KEEP-OUT STACKUP contract (KO1-KO5).

A keep-out is a statement about PHYSICS.  An antenna needs its clearance
volume; a moulded boss needs its retention volume; an acoustic port needs its
hole.  None of those stop at layer two.

KiCad stores a rule area's layers as an explicit SET, and it clamps the
shorthand `*.Cu` to the stackup that exists AT THE MOMENT THE AREA IS CREATED.
Grow the stackup later and the area does not grow with it.  What is left is a
keep-out that looks right in the editor, is honoured EXACTLY as written by DRC,
and silently protects fewer layers than the part requires -- so there is no
violation to report and no way to notice except to ask.

This board carried FIVE of them, every one clamped to `F.Cu / B.Cu / In1.Cu /
In2.Cu` while the board has six copper layers: `U1`'s footprint-embedded
ESP32-S3-WROOM-1 antenna area, a BOARD-LEVEL DUPLICATE of the same region with
its own uuid, both M2 mounting-boss retention keep-outs and `MK1`'s acoustic
port.  D-616 found ONE of them, because it asked a footprint's zones and
`pcbnew.BOARD.Zones()` does not return those -- nor does a footprint's return
the board's.  D-617 closed all five and this file is why they cannot come back.

    KO1  EVERY rule area that forbids copper -- footprint-embedded or
         board-level -- claims EVERY enabled copper layer of this board
    KO2  and holds no copper on any of them: zero filled pour, zero track
         endpoints, zero via barrels inside the on-board part of the region
    KO3  KiCad's own DRC agrees: zero `items_not_allowed`
    KO4  the screen is NOT VACUOUS -- it must see rule areas in BOTH scopes,
         and a synthetic area narrowed by one layer must be caught
    KO5  the two GND reference planes are the SAME COPPER.  `In1.Cu` and
         `In4.Cu` carry no tracks; they are solid GND references cut only by
         holes, pads and keep-outs, so once every keep-out claims both of them
         the two fills are identical BY CONSTRUCTION.  Before D-617 they
         differed by 335.555 mm2 -- exactly the copper the four clamped
         keep-outs should never have let `In4.Cu` keep.  This clause states
         that identity as a measurement, so a keep-out that loses a layer
         again shows up as two planes that stopped matching.

    python3 hardware/demo/manufacturing/checks/keepout_stackup_contract.py \
        [--board B.kicad_pcb] [-o REPORT.json] [--skip-drc]
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MANUF = ROOT / "hardware/demo/manufacturing"
PROJECT = ROOT / "hardware/demo/kicad/aqroot-demo"
BOARD = PROJECT / "aqroot-Beta-v2.kicad_pcb"

sys.path.insert(0, str(MANUF))

# The two layers KO5 asserts are the same copper, and why they may be:
# `qrouter.ROUTABLE` has never called either of them routable and no track has
# ever been laid on one.  The clause re-measures that premise rather than
# trusting it -- a track on In1 or In4 would make the identity meaningless, so
# a non-zero track count is itself the failure.
MIRROR = ("In1.Cu", "In4.Cu")


PERTURB_CHILD = """
import sys
import pcbnew
path, uuid, drop = sys.argv[1], sys.argv[2], sys.argv[3]
b = pcbnew.LoadBoard(path)
zones = list(b.Zones()) + [z for f in b.GetFootprints() for z in f.Zones()]
hit = [z for z in zones if str(z.m_Uuid.AsString()) == uuid]
if len(hit) != 1:
    raise SystemExit("KO4: %d rule areas with uuid %s" % (len(hit), uuid))
ls = hit[0].GetLayerSet()
if not ls.Contains(b.GetLayerID(drop)):
    raise SystemExit("KO4: %s does not claim %s to begin with" % (uuid, drop))
ls.removeLayer(b.GetLayerID(drop))
hit[0].SetLayerSet(ls)
pcbnew.SaveBoard(path, b)
"""


def survey(board_path, perturb=None):
    """Run the screen against `board_path`, optionally narrowing one area.

    `perturb` is (uuid, layer) -- the negative control: strip one enabled
    copper layer from one rule area and require KO1 to catch it.  It is done on
    a COPY, never on the board handed in.
    """
    out = Path(tempfile.mkdtemp(prefix="aqroot-ko-contract-")) / "ko.json"
    target = board_path
    if perturb:
        cell = out.parent / "perturbed"
        cell.mkdir()
        for suffix in (".kicad_pcb", ".kicad_dru", ".kicad_pro"):
            src = board_path.with_suffix(suffix)
            if src.exists():
                (cell / src.name).write_bytes(src.read_bytes())
        target = cell / board_path.name
        # The perturbation is made by `pcbnew` in a CHILD, never by text and
        # never in this process: a rule area written `(layers "*.Cu")` has no
        # layer line to name, and `SaveBoard` in-process leaves this KiCad
        # build's bindings returning untyped objects from the next `LoadBoard`
        # -- the same lesson `route_maze_batch.detour_apply` records.
        subprocess.run([sys.executable, "-c", PERTURB_CHILD, str(target),
                        perturb[0], perturb[1]], check=True,
                       capture_output=True, text=True)
    subprocess.run([sys.executable, str(MANUF / "screen_footprint_keepouts.py"),
                    "--board", str(target), "-o", str(out)],
                   check=True, capture_output=True, text=True)
    return json.loads(out.read_text())


def kicad_drc(board_path):
    cell = Path(tempfile.mkdtemp(prefix="aqroot-ko-drc-"))
    import verify_promotion as V
    staged = V.stage(None, cell)
    if board_path != BOARD:
        staged.write_bytes(board_path.read_bytes())
    out = cell / "drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--refill-zones", "--save-board",
                    "--format", "json", "--units", "mm", "--severity-all",
                    "-o", str(out), str(staged)], capture_output=True,
                   text=True)
    report = json.loads(out.read_text())
    counts = {}
    for v in report.get("violations", []):
        counts[v.get("type", "unknown")] = counts.get(v.get("type"), 0) + 1
    return counts, [v for v in report.get("violations", [])
                    if v.get("type") == "items_not_allowed"]


def mirror_planes(board_path):
    """Filled area and track count of the two solid GND reference planes."""
    import pcbnew
    b = pcbnew.LoadBoard(str(board_path))
    out = {}
    for name in MIRROR:
        lid = b.GetLayerID(name)
        area = 0.0
        for z in b.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(lid):
                continue
            area += z.GetFilledPolysList(lid).Area() / 1e12
        tracks = sum(1 for t in b.GetTracks()
                     if t.GetClass() == "PCB_TRACK" and t.GetLayer() == lid)
        out[name] = dict(area_mm2=round(area, 6), tracks=tracks,
                         net=sorted({z.GetNetname() for z in b.Zones()
                                     if not z.GetIsRuleArea()
                                     and z.IsOnLayer(lid)}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", type=Path, default=BOARD)
    ap.add_argument("--skip-drc", action="store_true")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()

    report = survey(a.board)
    areas = report["areas"]
    forbidding = [x for x in areas
                  if x["keepout"]["tracks"] or x["keepout"]["vias"]
                  or x["keepout"]["copperpour"]]
    under = [dict(scope=x["scope"], ref=x["ref"], identity=x["identity"],
                  uuid=x["uuid"], unprotected=x["unprotected_board_layers"])
             for x in forbidding if x["unprotected_board_layers"]]
    holding = []
    for x in forbidding:
        for layer, d in sorted(x["per_layer"].items()):
            if d["pour_mm2"] > 0 or d["tracks"] or d["vias"]:
                holding.append(dict(uuid=x["uuid"], identity=x["identity"],
                                    layer=layer, **{k: d[k] for k in
                                                    ("pour_mm2", "tracks",
                                                     "vias", "nets")}))
    scopes = {x["scope"] for x in forbidding}

    control_uuid = sorted(x["uuid"] for x in forbidding)[0]
    control = survey(a.board, perturb=(control_uuid,
                                       report["board_copper_layers"][-1]))
    control_caught = any(
        x["uuid"] == control_uuid and x["unprotected_board_layers"]
        for x in control["areas"])

    drc_counts, not_allowed = ({}, []) if a.skip_drc else kicad_drc(a.board)
    planes = mirror_planes(a.board)
    mirror_ok = (planes[MIRROR[0]]["tracks"] == 0
                 and planes[MIRROR[1]]["tracks"] == 0
                 and planes[MIRROR[0]]["net"] == planes[MIRROR[1]]["net"]
                 and abs(planes[MIRROR[0]]["area_mm2"]
                         - planes[MIRROR[1]]["area_mm2"]) < 1e-6)

    checks = {
        "KO1_every_keepout_claims_the_stackup": not under,
        "KO2_no_keepout_holds_copper": not holding,
        "KO3_kicad_reports_no_items_not_allowed":
            a.skip_drc or drc_counts.get("items_not_allowed", 0) == 0,
        "KO4_screen_is_not_vacuous": bool(scopes == {"board", "footprint"}
                                          and control_caught),
        "KO5_gnd_reference_planes_are_the_same_copper": mirror_ok,
    }
    out = dict(schema=1, board=str(a.board),
               board_copper_layers=report["board_copper_layers"],
               rule_areas=report["rule_areas"],
               forbidding_copper=len(forbidding),
               scopes=sorted(scopes),
               under_declared=under, holding_copper=holding,
               control=dict(uuid=control_uuid,
                            layer=report["board_copper_layers"][-1],
                            caught=control_caught),
               drc_counts=drc_counts,
               items_not_allowed=not_allowed,
               reference_planes=planes,
               checks=checks, ok=all(checks.values()))
    text = json.dumps(out, indent=2, sort_keys=True, default=str)
    if a.out:
        a.out.write_text(text + "\n", encoding="utf-8")
    for k, v in sorted(checks.items()):
        print("%-46s %s" % (k, "PASS" if v else "FAIL"))
    print(json.dumps({k: out[k] for k in
                      ("rule_areas", "forbidding_copper", "scopes",
                       "under_declared", "holding_copper", "reference_planes")},
                     indent=1, default=str))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
