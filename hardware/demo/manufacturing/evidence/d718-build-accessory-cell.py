#!/usr/bin/env python3
"""D-718 -- relocate the ACCESSORY 5 V POWER CELL to the east pocket beside the
BQ25185 SYS pour and the PCAL expander.

WHY.  D-717 addendum 2 priced the SYS feed to the boost where it stands: BASE
NO_PATH at 0.500 mm, no single net opens it, and the minimal five-net cut buys a
169.4 mm switched-mode INPUT rail with nine barrels.  The cell is at y ~ 36..43
and every one of its supplies and controls is elsewhere: BQ25185_SYS's body is
at y >= 72, C28 (its only bulk on that rail) is at (69.175, 93.245), and the
five accessory control lines all originate on U3 at y 75.7..79.0.  The cell is
in the wrong place, not badly routed.

THE POCKET.  x 67.3..76.4, y 76.4..92.3 on B.Cu is the least congested region on
the board: 17 B.Cu track objects, and between y 81.5 and 90.8 only ONE (a GND
stitch barrel at (68.000, 82.400)).  SW9 is F.Cu and only its two NPTH pegs
reach through; J8 is F.Cu SMD; the D-709 east step gave x 72..77 between
y 70.5 and 104 and nothing but R36 uses it.

WHAT MOVES.  U21 (TPS61023), L4 (WE-MAPI 4030), C65/C66 (2 x 22 uF RAW bulk),
R99/R100 (FB divider), TP28, U22 (TPS22950C load switch) and R101 (its ILIM
resistor, which sat 46 mm from the pin it sets).

WHAT IT BUYS.  L4.1 and U21.3 land inside the BQ25185_SYS B.Cu pour; ACC_5V_LX,
ACC_5V_RAW, ACC_5V_FB and ACC_5V_ILIM all become cell-local; ACC_5V_BOOST_EN,
ACC_POWER_FAULT_N and ACC_5V_SW_EN all get SHORTER (their far ends are on U3);
and only ONE conductor -- ACC_5V_SW, 0.40/0.60 mm, 0.7 A -- has to cross to
J5.24 at (65.900, 68.420), which is J5's own southern end.

Usage: python3 w/d718/build_cand1.py
"""
import json
import subprocess
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
MFG = HERE.parents[1]
BRD = (Path(sys.argv[1]) if len(sys.argv) > 1
       else HERE / "cand1" / "aqroot-Beta-v2.kicad_pcb")
LOG = []

# ---- 1. the three cell-local nets whose EVERY pad moves --------------------
# `Net-(U11-TS_MR)` joins them: BOTH its pads move relative to each other --
# `R38`, the BQ25185's 10 k TS/MR bias resistor, sat at (9.525, 85.985), SIXTY
# MILLIMETRES from `U11.6`, and its 22 objects meander 88.84 mm straight
# through the corridor `/ACC_5V_SW` needs to reach `J5.24`.  A high-impedance
# thermistor-bias node does not belong on a 60 mm antenna and the corridor does
# not belong to it; the resistor comes home and the net is re-routed.
WIPE = ["/01_POWER_TREE/ACC_5V_RAW", "/01_POWER_TREE/ACC_5V_FB",
        "/01_POWER_TREE/ACC_5V_ILIM", "Net-(U11-TS_MR)"]
b = pcbnew.LoadBoard(str(BRD))
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() in WIPE:
        b.RemoveNative(t); n += 1
# ---- 1b. U21.2's own ACC_5V_BOOST_EN stub, and the F.Cu hop it feeds ------
# The rest of that tree -- a 140 mm tour east to x = 70, back west to x = 48,
# south to y = 74 and into U3.16 -- SURVIVES and still holds R102, TP30 and
# U3.16 together.  Only the seven B.Cu stub segments from U21.2, the barrel at
# (56.500, 41.100) they climb, the F.Cu hop to (58.400, 43.000) and ITS barrel
# come out, so nothing is left dangling on either side.
def ends(t):
    return {(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)}


STUB = [
    {(56850000, 39900000), (56700000, 39900000)},
    {(56700000, 39900000), (56500000, 40050000)},
    {(56500000, 40050000), (56425000, 40200000)},
    {(56425000, 40200000), (56425000, 40625000)},
    {(56425000, 40625000), (56525000, 40775000)},
    {(56525000, 40775000), (56600000, 40900000)},
    {(56500000, 41100000), (56600000, 40900000)},
    {(58400000, 43000000), (56500000, 41100000)},
]
BARRELS = [(56500000, 41100000), (58400000, 43000000)]
m = 0
for t in list(b.GetTracks()):
    if t.GetNetname() != "/ACC_5V_BOOST_EN":
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        if (t.GetStart().x, t.GetStart().y) in BARRELS:
            b.RemoveNative(t); m += 1
    elif ends(t) in STUB:
        b.RemoveNative(t); m += 1
assert m == 10, m
b.Save(str(BRD))
LOG.append({"step": "wipe_local_nets", "nets": WIPE, "removed": n,
            "boost_en_stub_removed": m})
print("  -%d objects on %s" % (n, ", ".join(WIPE)))
print("  -%d ACC_5V_BOOST_EN stub objects at U21.2" % m)

# ---- 2. the moves ---------------------------------------------------------
MOVES = [
    # ref,   x_mm,   y_mm,  rot, release nets, extra release points
    ("U22",  74.300, 80.250, 180,
     ["/ACC_5V_SW_EN", "GND", "/ACC_5V_SW", "/ACC_POWER_FAULT_N"],
     ["/ACC_POWER_FAULT_N:55.375,44.7"]),
    ("R101", 73.000, 77.200, 180, ["GND"], []),
    ("R38",  72.800, 73.200,   0, ["GND"], []),
    ("U21",  71.000, 89.300,   0,
     ["/01_POWER_TREE/BQ25185_SYS", "GND"], []),
    ("L4",   70.200, 84.600,   0, ["/01_POWER_TREE/BQ25185_SYS"], []),
    ("C65",  74.300, 84.000, 180, ["GND"], []),
    ("C66",  74.300, 86.500, 180, ["GND"], []),
    ("R99",  74.300, 88.800, 180, [], []),
    ("R100", 73.000, 91.300,   0, ["GND"], []),
    ("TP28", 75.500, 93.600,   0, [], []),
]
for ref, x, y, rot, nets, points in MOVES:
    b = pcbnew.LoadBoard(str(BRD))
    f = b.FindFootprintByReference(ref)
    px, py = f.GetPosition().x, f.GetPosition().y
    dx, dy = int(round(x * 1e6)) - px, int(round(y * 1e6)) - py
    cmd = [sys.executable, str(MFG / "apply_part_shift.py"),
           "--board", str(BRD), "--ref", ref,
           "--dx-nm", str(dx), "--dy-nm", str(dy)]
    if rot:
        cmd += ["--rot-deg", str(rot)]
    if nets or points:
        cmd += ["--release"]
    for net in nets:
        cmd += ["--release-net", net]
    for p in points:
        cmd += ["--release-point", p]
    cmd += ["--apply", "--report", str(HERE / ("shift-%s.json" % ref.lower()))]
    r = subprocess.run(cmd, capture_output=True, text=True)
    rep = json.loads((HERE / ("shift-%s.json" % ref.lower())).read_text())
    LOG.append({"step": "move", "ref": ref, "to": [x, y, rot],
                "verdict": rep["verdict"], "released": rep.get("released_count", 0),
                "refusals": rep.get("release_refusals", [])})
    print("  %-5s -> (%7.3f,%7.3f) rot %3d   %s  released %d  refusals %d"
          % (ref, x, y, rot, rep["verdict"], rep.get("released_count", 0),
             len(rep.get("release_refusals", []))))
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        (HERE / "build-log.json").write_text(json.dumps(LOG, indent=1))
        sys.exit(1)

# ---- 3. the small BQ25185_SYS pour the cell has left behind ---------------
# `B /01_POWER_TREE/BQ25185_SYS POUR 2`, the rectangle (55,33)-(60,42), existed
# ONLY to join L4.1 to U21.3 and holds no pad of its net once they move.  It is
# REMOVED, and the removal is a CLAIM the promotion states:
# `verify_promotion.py --zone-removed` and `pour_partition_contract.py
# --pour-removed` both take it by name.  Leaving it in place is not the safer
# choice -- a zone with nothing to connect to is two `isolated_copper` DRC
# findings, measured, which is a NEW DRC class this board does not carry.
b = pcbnew.LoadBoard(str(BRD))
doomed = [z for z in b.Zones()
          if z.GetZoneName() == "B /01_POWER_TREE/BQ25185_SYS POUR 2"]
assert len(doomed) == 1, [z.GetZoneName() for z in b.Zones()]
for z in doomed:
    b.RemoveNative(z)
b.Save(str(BRD))
LOG.append({"step": "drop_orphan_sys_pour",
            "zone": "B /01_POWER_TREE/BQ25185_SYS POUR 2"})
print("  -1 zone 'B /01_POWER_TREE/BQ25185_SYS POUR 2' (no pad of its net left)")

# ---- 4. refill ------------------------------------------------------------
b = pcbnew.LoadBoard(str(BRD))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
print("  refilled %d zones" % len(list(b.Zones())))
(HERE / "build-log.json").write_text(json.dumps(LOG, indent=1))
