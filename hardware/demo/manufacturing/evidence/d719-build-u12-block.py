#!/usr/bin/env python3
"""D-719 -- REBUILD THE TPS63020 BUCK-BOOST AS A REAL CONVERTER BLOCK.

FOUR MEASURED DEFECTS, NOT ONE.
  1. `/01_POWER_TREE/BQ25185_SYS` never reaches `U12.10`/`U12.11` -- the
     TPS63020's POWER `VIN` pins.  Only `VINA` (pin 1) is on the rail, so the
     3.3 V buck-boost has no power input and the product does not run.  The
     island is 0.7488 mm2 in a box whose only door is a 0.9 mm band against
     the WROOM antenna keep-out, and `EN` is standing in it.
  2. The switch node `Net-(L1-Pad1)` runs 13 mm -- out of `U12.8` east to
     x = 68.875, 8.4 mm SOUTH to y = 94.400, then west to `L1.1`.  That
     9.2 mm vertical of 0.400 mm switch node is 0.5 mm from the antenna
     keep-out AND it is the fence that walls `U12`'s whole east side off from
     the `SYS` pour body.
  3. There is NO output capacitance at the converter: C29/C30/C31/C32, the
     four 22 uF +3V3 bulk caps, are 46..60 mm away at y = 122.61.
  4. The feedback divider R39/R40 is 28 mm away at y ~ 72, so `V3V3_FB` -- a
     1 M / 180 k high-impedance node -- is run across the board on In2 and In3.
  Plus: R41 (PG pull-up) and R43 (EN pull-down) are 50-56 mm from the pins
  they serve, and their two-pad nets spend 103 mm and 103 mm of routed copper
  crossing the middle of the board to get there.

THE BLOCK.  `L1` rotates 90 degrees and moves east so both inductor terminals
face `U12`'s east column: the switch node becomes two ~1.1 mm stubs.  `U12`
moves into the space `L1` vacated plus the empty D-709 step, which opens a
4.7 mm south band for the `SYS` pour instead of a 0.9 mm one.  `C28` (100 nF)
lands 0.7 mm south of the VIN pins; `C31`/`C32` (2 x 22 uF) land north of the
VOUT pins; `R39`/`R40` land beside `FB`; `R41`/`R43` land beside the pins they
bias.  `TP6` leaves the channel.

WHAT IT BUYS.  `SYS` reaches `VIN` through the pour.  The switch node loses
11 mm.  Input, output and feedback loops become local.  And ~200 mm of routed
`Net-(SW9-A)` and `Net-(U12-PG)` copper comes out of the middle of the board.
"""
import json, subprocess, sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
MFG = Path(__file__).resolve().parents[2] / "hardware/demo/manufacturing"
BRD = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "cand1/aqroot-Beta-v2.kicad_pcb"
LOG = []


def ends(t):
    return frozenset({(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)})


# ---- 1. nets whose every pad moves or is re-sited: wiped and re-laid -------
WIPE = ["Net-(L1-Pad1)", "Net-(L1-Pad2)", "/01_POWER_TREE/V3V3_FB",
        "Net-(U12-PG)"]
# `Net-(SW9-A)` keeps ONLY the SW9.1 <-> TP13.1 chain; everything east of
# TP13 is the EN run that crossed U12's new footprint and the 0.9 mm band.
SW9_KEEP_TRK = {
    frozenset({(63950000, 89000000), (62700000, 87750000)}),
    frozenset({(65500000, 91950000), (62700000, 87750000)}),
    frozenset({(65500000, 93000000), (65500000, 91950000)}),
}
SW9_KEEP_VIA = {(62700000, 87750000), (65500000, 91950000)}
# `/BQ25185_STAT1`'s local detour through TP6 and across U12's new thermal pad
STAT1_KILL_TRK = {
    frozenset({(70400000, 97400000), (69600000, 96600000)}),
    frozenset({(69600000, 96600000), (70250000, 95500000)}),
    frozenset({(70250000, 95500000), (70250000, 96425000)}),
    frozenset({(70250000, 96425000), (70625000, 97900000)}),
    frozenset({(71300000, 99700000), (70400000, 97400000)}),
    frozenset({(70625000, 97900000), (76400000, 85525000)}),
}
STAT1_KILL_VIA = {(70400000, 97400000), (70625000, 97900000)}

# `+3V3` and `GND`: U12's own escape and its thermal-pad stitch are replaced
# wholesale, and pre-removing them keeps the move's --release closure from
# walking into SW2.2's ground tie, which shares the barrel under U12.15.
P3V3_BOX = (63.5e6, 95.5e6, 68.5e6, 100.6e6)
U12_GND_PADS = [(65.175e6, 100.610e6, 68.025e6, 102.190e6),   # U12.15 thermal
                (65.480e6, 99.700e6, 65.720e6, 100.300e6),    # U12.2
                (65.480e6, 102.500e6, 65.720e6, 103.100e6)]   # U12.13
# SW2.2's ground is tied to the planes TWICE: the barrel at (67.700,101.700)
# with its F.Cu stub, and the barrel at (67.800,100.900) with two B.Cu stubs.
# BOTH sit inside U12.15's old thermal pad.  The first is removed with the
# rest of the stitch -- it is the object whose release would otherwise have to
# walk into SW2.2 -- and the SECOND is kept, so the land keeps a tie.
# BOTH of SW2.2's ties stood inside U12.15's old thermal pad, so both come out
# -- placement PL5 measures a released land's copper as GONE -- and step 2 gives
# the land a fresh barrel at (68.600,101.250), inside its own pad and CLEAR of
# the old thermal box.
SW2_2_KEEP = set()
# C28's own ground stitch at its OLD site: four B.Cu stubs and two barrels
# that exist only to tie C28.2 to the planes.  C28 moves, so they are orphan
# stitch standing in the east channel the SYS pour needs.
C28_GND_TRK = {frozenset({(70175000, 93000000), (70700000, 92400000)}),
               frozenset({(70700000, 92500000), (70200000, 91650000)}),
               frozenset({(70700000, 92400000), (70500000, 92200000)}),
               frozenset({(69950000, 93245000), (70700000, 92500000)})}
C28_GND_VIA = {(70200000, 91650000), (70500000, 92200000),
               # R40.2's own stitch barrel: every track on it went with the
               # move's release, so it is a bare plane stitch standing on a
               # land that has left.  PL5/PL8 want the released land's copper
               # GONE, and In1/In4 keep their stitch through its neighbours.
               (61125000, 72600000)}
# U12's OLD thermal-pad stitch legs west of (65.1,100.7): their pad-side ends
# came out with the rest of the stitch, so they now serve nothing, and they sit
# in the middle of the band the SYS pour has to cross.
ORPHAN_BOX = (63.900e6, 99.300e6, 65.100e6, 101.600e6)
# R39.1's 0.400 mm +3V3 FEED.  Traced end to end it is a seven-segment branch
# whose ONLY pad is R39.1 and whose far end is the plane stitch at
# (70.650,67.550) -- so with R39 moved the WHOLE branch is orphan copper, and
# leaving any of it behind leaves a track_dangling the authority does not
# carry.  The barrel stays: it sits in both the F and In3 +3V3 fills.
P3V3_STUB = {frozenset({(65675000, 71750000), (66450000, 72500000)}),
             frozenset({(66450000, 72500000), (66650000, 73100000)}),
             frozenset({(66650000, 73100000), (67100000, 73450000)}),
             frozenset({(67100000, 73450000), (67500000, 73450000)}),
             frozenset({(67500000, 73450000), (67800000, 73300000)}),
             frozenset({(67800000, 73300000), (70650000, 69350000)}),
             frozenset({(70650000, 69350000), (70650000, 67550000)})}


def _in(box, p):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


b = pcbnew.LoadBoard(str(BRD))
n = sw = st = p3 = gn = 0
for t in list(b.GetTracks()):
    net = t.GetNetname()
    if net in WIPE:
        b.RemoveNative(t); n += 1
    elif net == "Net-(SW9-A)":
        if t.Type() == pcbnew.PCB_VIA_T:
            if (t.GetStart().x, t.GetStart().y) not in SW9_KEEP_VIA:
                b.RemoveNative(t); sw += 1
        elif ends(t) not in SW9_KEEP_TRK:
            b.RemoveNative(t); sw += 1
    elif net == "/BQ25185_STAT1":
        if t.Type() == pcbnew.PCB_VIA_T:
            if (t.GetStart().x, t.GetStart().y) in STAT1_KILL_VIA:
                b.RemoveNative(t); st += 1
        elif ends(t) in STAT1_KILL_TRK:
            b.RemoveNative(t); st += 1
    elif net == "+3V3":
        pts = [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
        if all(_in(P3V3_BOX, q) for q in pts) or ends(t) in P3V3_STUB:
            b.RemoveNative(t); p3 += 1
    elif net == "GND":
        if t.Type() == pcbnew.PCB_VIA_T \
                and ((t.GetStart().x, t.GetStart().y) in C28_GND_VIA
                     or _in(ORPHAN_BOX, (t.GetStart().x, t.GetStart().y))):
            b.RemoveNative(t); gn += 1
            continue
        pts = [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
        if any(any(_in(box, q) for box in U12_GND_PADS) for q in pts) \
                and not any(q in SW2_2_KEEP for q in pts):
            b.RemoveNative(t); gn += 1
        elif ends(t) in C28_GND_TRK:
            b.RemoveNative(t); gn += 1
        elif any(_in(ORPHAN_BOX, q) for q in pts):
            b.RemoveNative(t); gn += 1
b.Save(str(BRD))
LOG.append({"step": "wipe", "nets": WIPE, "removed": n,
            "sw9a_removed": sw, "stat1_local_removed": st,
            "p3v3_local_removed": p3, "gnd_stitch_removed": gn})
print("  -%d objects on %s" % (n, ", ".join(WIPE)))
print("  -%d Net-(SW9-A) (SW9.1<->TP13.1 chain kept)" % sw)
print("  -%d /BQ25185_STAT1 local detour objects" % st)
print("  -%d +3V3 local escape, -%d GND thermal stitch" % (p3, gn))

# ---- 2. the moves ---------------------------------------------------------
MOVES = [
    # ref,  x,      y,      rot, release-nets, release-points, bare-pads
    ("TP6",  75.000, 88.000,   0, ["/BQ25185_STAT1"], [], []),
    ("L1",   74.100, 97.600,  90, [], [], []),
    ("U12",  69.600, 97.600,   0, ["/01_POWER_TREE/BQ25185_SYS", "GND", "+3V3"],
     [], []),
    ("C28",  70.100,101.400, 270, ["/01_POWER_TREE/BQ25185_SYS", "GND"], [], []),
    ("C31",  69.700, 93.150,  90, ["+3V3", "GND"], [], []),
    ("C32",  72.400, 92.600,  90, ["+3V3", "GND"], [], []),
    ("R39",  67.400, 93.900,  90, ["+3V3"], [], []),
    # R40.2 sits on a GND stitch junction that also carries C5.2's tie; the
    # release takes it and step 3 gives C5.2 a new 0.37 mm tie to the same
    # mesh at (61.700,74.100).  C5.2 also sits IN the B GND PLANE fill.
    ("R40",  68.400, 89.200,  90, ["GND"], [], ["C5.2"]),
    ("R41",  73.000,102.600, 180, ["+3V3"], [], []),
    ("R43",  73.000,100.900,   0, ["GND"], [], []),
    # TP8 probes PG; with R41 at the IC it would otherwise owe a 35 mm run.
    ("TP8",  75.700,101.700,   0, ["Net-(U12-PG)"], [], []),
]
for ref, x, y, rot, nets, points, bare in MOVES:
    b = pcbnew.LoadBoard(str(BRD))
    f = b.FindFootprintByReference(ref)
    px, py = f.GetPosition().x, f.GetPosition().y
    dx, dy = int(round(x * 1e6)) - px, int(round(y * 1e6)) - py
    cmd = [sys.executable, str(MFG / "apply_part_shift.py"), "--board", str(BRD),
           "--ref", ref, "--dx-nm", str(dx), "--dy-nm", str(dy)]
    if rot:
        cmd += ["--rot-deg", str(rot)]
    if nets or points:
        cmd += ["--release"]
        for net in nets:
            cmd += ["--release-net", net]
        for pt in points:
            cmd += ["--release-point", pt]
        for bp in bare:
            cmd += ["--release-bare-pad", bp]
    rep = HERE / ("shift-%s.json" % ref.lower())
    cmd += ["--apply", "--report", str(rep)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        d = json.loads(rep.read_text())
    except Exception:
        print(r.stdout[-4000:]); print(r.stderr[-4000:]); sys.exit(1)
    LOG.append({"step": "move", "ref": ref, "to": [x, y, rot],
                "verdict": d.get("verdict"), "released": d.get("released_count", 0),
                "refusals": d.get("release_refusals", [])})
    print("  %-5s -> (%7.3f,%7.3f) rot %3d  %-5s released %s" %
          (ref, x, y, rot, d.get("verdict"), d.get("released_count", 0)))
    if r.returncode != 0:
        print(json.dumps({k: d[k] for k in
                          ("release_refusals", "vias_in_moved_pads",
                           "courtyard_overlaps_new", "endpoints_stranded")
                          if k in d}, indent=1)[:3000])
        (HERE / "build-log.json").write_text(json.dumps(LOG, indent=1))
        sys.exit(1)

# ---- 3. C5.2's replacement tie into the surviving stitch mesh -------------
b = pcbnew.LoadBoard(str(BRD))
net = b.FindNet("GND")
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(61950000, 74375000))
t.SetEnd(pcbnew.VECTOR2I(61700000, 74100000))
t.SetWidth(300000)
t.SetLayer(pcbnew.B_Cu)
t.SetNet(net)
b.Add(t)
b.Save(str(BRD))
LOG.append({"step": "c5_2_retie", "track_mm": [[61.950, 74.375], [61.700, 74.100]],
            "width_mm": 0.300, "layer": "B.Cu"})
print("  +1 GND tie C5.2 -> (61.700,74.100)")

b = pcbnew.LoadBoard(str(BRD))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BRD))
(HERE / "build-log.json").write_text(json.dumps(LOG, indent=1))
print("  refilled %d zones" % len(list(b.Zones())))
