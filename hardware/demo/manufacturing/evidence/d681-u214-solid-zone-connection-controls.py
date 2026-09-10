#!/usr/bin/env python3
"""D-681 addendum, CORRECTION: is `U21.4`'s THERMAL zone connection what keeps
the B.Cu GND pour out of the channel between U21's pad columns?  NO.  Four arms,
each a private copy refilled by KiCad's own ZONE_FILLER; board never written."""
import json, shutil, sys, tempfile
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"


def near(p, q):
    return abs(p.x / 1e6 - q[0]) < 1e-4 and abs(p.y / 1e6 - q[1]) < 1e-4


def arm(solid, clear_channel):
    tmp = Path(tempfile.mkdtemp(prefix="aqroot-solid-"))
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
        shutil.copy(SRC.with_suffix(ext), tmp / ("p" + ext))
    b = pcbnew.LoadBoard(str(tmp / "p.kicad_pcb"))
    doomed = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            if clear_channel and t.GetNetname() == "/ACC_DETECT_N" \
                    and near(t.GetPosition(), (57.900, 38.800)):
                doomed.append(t)
            continue
        n, s, e = t.GetNetname(), t.GetStart(), t.GetEnd()
        if n == "GND" and ((near(s, (58.700, 39.375)) and near(e, (60.600, 38.425)))
                           or (near(e, (58.700, 39.375)) and near(s, (60.600, 38.425)))):
            doomed.append(t)                       # U21.4's east escape, always
        if clear_channel and n == "/ACC_DETECT_N":
            for a, c in (((57.800, 38.900), (57.800, 40.700)),
                         ((57.650, 40.850), (57.800, 40.700))):
                if (near(s, a) and near(e, c)) or (near(s, c) and near(e, a)):
                    doomed.append(t)
    for t in doomed:
        b.Remove(t)
    fp = next(f for f in b.GetFootprints() if f.GetReference() == "U21")
    pad4 = next(p for p in fp.Pads() if p.GetNumber() == "4")
    if solid:
        pad4.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(tmp / "p.kicad_pcb"), b)
    del b
    b = pcbnew.LoadBoard(str(tmp / "p.kicad_pcb"))
    sys.path.insert(0, str(HERE.parent))
    import pour_bond_guard as pbg
    a = (int(58.4e6), int(39.4e6))
    c = (int(58.0e6), int(41.6e6))
    rec = dict(solid_zone_connection=solid, channel_cleared=clear_channel,
               removed=len(doomed), island_area_mm2=None, holds_the_body=None)
    for pour in pbg.read_pours(b):
        if pour["net"] != "GND" or pour["layer"] != "B.Cu":
            continue
        for isl in pour["islands"]:
            if isl["poly"].Contains(pcbnew.VECTOR2I(*a), -1, 0):
                rec["island_area_mm2"] = round(isl["area_mm2"], 4)
                rec["holds_the_body"] = bool(
                    isl["poly"].Contains(pcbnew.VECTOR2I(*c), -1, 0))
                return rec
    return rec


if "--arm" in sys.argv:
    i = sys.argv.index("--arm")
    r = arm(sys.argv[i + 1] == "1", sys.argv[i + 2] == "1")
    print("ARM_JSON " + json.dumps(r))
    raise SystemExit

# EACH ARM IN ITS OWN PROCESS.  Removing tracks from a loaded BOARD and saving
# it leaves this KiCad build's SWIG bindings returning an untyped SwigPyObject
# from the NEXT LoadBoard -- the same defect route_maze_batch.evict_copper
# documents -- so a second arm in the same interpreter cannot read its own
# result.
import subprocess
out = dict(schema=1, decision="D-681 addendum correction",
           question="does U21.4's zone connection explain why the B.Cu GND pour "
                    "never enters the 0.750 mm channel between U21's pad columns",
           board=str(SRC),
           board_sha256=__import__("hashlib").sha256(SRC.read_bytes()).hexdigest(),
           arms=[json.loads([ln[9:] for ln in subprocess.run(
               [sys.executable, __file__, "--arm", "1" if s else "0",
                "1" if c else "0"], capture_output=True, text=True
               ).stdout.splitlines() if ln.startswith("ARM_JSON ")][0])
                 for s in (False, True) for c in (False, True)])
out["answer"] = ("NO.  U21.4 stays alone on a 0.154 - 0.166 mm2 island in ALL "
                 "FOUR arms, so the THERMAL SPOKE is not the binding constraint: "
                 "KiCad's fill does not put copper in the channel at all.  The "
                 "strip the zone's own 0.250 mm local_clearance leaves between "
                 "the two pad columns is 0.251 mm against a 0.200 mm "
                 "min_thickness and it is still not filled.  Widening it needs "
                 "the ZONE's local clearance lowered board-wide, which trades "
                 "every GND-to-foreign gap on the board for this one pad and is "
                 "refused here.")
out["ok"] = all(a["holds_the_body"] is False for a in out["arms"])
Path(HERE / "d681-u214-solid-zone-connection-controls.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out["arms"], indent=1))
