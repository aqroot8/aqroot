#!/usr/bin/env python3
"""D-681 ADDENDUM, MEASURED: why the TPS61023's GND pin cannot be grounded at
this placement.  Read-only; every number below is produced here, not copied."""
import json, subprocess, sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent
MANU = HERE.parent
BOARD = MANU.parent / "kicad/aqroot-demo/aqroot-Beta-v2.kicad_pcb"
b = pcbnew.LoadBoard(str(BOARD))

fp = next(f for f in b.GetFootprints() if f.GetReference() == "U21")
pads = {p.GetNumber(): (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                        p.GetSize().x / 1e6, p.GetSize().y / 1e6,
                        p.GetNetname()) for p in fp.Pads()}
zone = next(z for z in b.Zones()
            if not z.GetIsRuleArea() and z.GetNetname() == "GND"
            and b.GetLayerName(list(z.GetLayerSet().CuStack())[0]) == "B.Cu")

# 1. the channel between U21's two pad columns, in numbers
west = pads["3"][0] + pads["3"][2] / 2.0          # U21.3 land east edge
east = pads["4"][0] - pads["4"][2] / 2.0          # U21.4 land west edge
clr = zone.GetLocalClearance() / 1e6
chan = dict(west_land_edge_mm=round(west, 4), east_land_edge_mm=round(east, 4),
            channel_mm=round(east - west, 4),
            zone_local_clearance_mm=clr,
            zone_min_thickness_mm=zone.GetMinThickness() / 1e6,
            zone_thermal_gap_mm=zone.GetThermalReliefGap() / 1e6,
            zone_thermal_spoke_mm=zone.GetThermalReliefSpokeWidth() / 1e6,
            pad_connection=int(zone.GetPadConnection()),
            pour_strip_mm=round((east - clr) - (west + clr), 4),
            u21_4_land_height_mm=pads["4"][3])
chan["why_no_spoke"] = (
    "the zone connects pads by THERMAL RELIEF (pad_connection %d): the fill is "
    "held %.3f mm off the land and reaches it only through spokes %.3f mm wide, "
    "and U21.4's land is %.3f mm TALL -- a spoke of that width cannot be cut "
    "into a pad shorter than itself, so the west channel can never reach it "
    "however clear it is" % (chan["pad_connection"], chan["zone_thermal_gap_mm"],
                             chan["zone_thermal_spoke_mm"],
                             chan["u21_4_land_height_mm"]))

# 2. every foreign object that crosses U21's own footprint, by layer
box = (56.6, 38.0, 60.7, 43.2)
crossers = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        continue
    lay = b.GetLayerName(t.GetLayer())
    s, e = t.GetStart(), t.GetEnd()
    for k in range(41):
        x = (s.x + (e.x - s.x) * k / 40) / 1e6
        y = (s.y + (e.y - s.y) * k / 40) / 1e6
        if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
            crossers.setdefault(lay, set()).add(t.GetNetname())
            break
PROTECTED = ("/XGPIO4", "/XGPIO5", "/ACC_3V3_SW", "/ACC_5V_SW_EN")
out = dict(
    schema=1, decision="D-681 addendum",
    question="why can U21.4, the TPS61023 accessory boost's GND pin, not be "
             "grounded at this placement",
    board=str(BOARD),
    board_sha256=__import__("hashlib").sha256(BOARD.read_bytes()).hexdigest(),
    u21_pads={k: dict(xy_mm=[v[0], v[1]], size_mm=[v[2], v[3]], net=v[4])
              for k, v in sorted(pads.items())},
    inter_column_channel=chan,
    foreign_copper_over_the_footprint={
        k: dict(nets=sorted(v),
                protected=[n for n in sorted(v)
                           if any(n.endswith(p.split("/")[-1]) for p in PROTECTED)])
        for k, v in sorted(crossers.items())},
    window_mm=list(box),
)
Path(HERE / "d681-u21-ground-addendum.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(dict(channel=chan["channel_mm"], strip=chan["pour_strip_mm"],
                      spoke=chan["zone_thermal_spoke_mm"],
                      land_height=chan["u21_4_land_height_mm"],
                      layers={k: v["nets"] for k, v in
                              out["foreign_copper_over_the_footprint"].items()}),
                 indent=1))
