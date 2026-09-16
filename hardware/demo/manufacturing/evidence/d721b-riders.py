#!/usr/bin/env python3
"""Three measured, edge-neutral, DRC-clean board repairs that ride with an
edge-closing route.

  1. `B /01_POWER_TREE/BQ25185_SYS POUR 1` west edge 58.500 -> 61.000 mm.
     The rail's pour was a 12.5 x 36.5 mm rectangle laid over `U2`'s and
     `U3`'s east fan-out, and EVERY new B.Cu route there fragments it: it is
     why D-721's `EXT_SCL_BUF` re-lay and this decision's `STAT2` route both
     regressed `BQ25185_SYS`.  No SYS land and no SYS track lies west of
     x = 61.725 inside it, so the 2.5 mm the pour gives up is copper the rail
     never used -- and the B.Cu GND plane takes it back, which is the
     reference those expander signals should have had all along.
  2. `B /01_POWER_TREE/BQ25185_SYS POUR 2` 5.0 x 9.0 mm rectangle ->
     2.1 x 6.2 mm strip, for the same reason at the boost end.
  3. `MK1` gains `allow_soldermask_bridges`.  The inherited
     `solder_mask_bridge` is the `DMM-4026-B-I2S`'s ACOUSTIC PORT: a 1.05 mm
     NPTH with no net, concentric inside the microphone's own 1.65 mm GND
     land, sharing one mask aperture with it BY DESIGN.  KiCad's footprint
     attribute exists for exactly that, and with it set the board's real DRC
     carries ZERO violations that are not the headless CLI's missing
     footprint-library warnings.
"""
import sys, json
import pcbnew

BRD = sys.argv[1]
NEW1 = [(61.00, 72.00), (71.00, 72.00), (71.00, 108.50), (61.00, 108.50)]
NEW2 = [(56.30, 34.00), (58.40, 34.00), (58.40, 40.20), (56.30, 40.20)]
LOG = {}
b = pcbnew.LoadBoard(BRD)
for z in list(b.Zones()):
    n = z.GetZoneName()
    pts = NEW1 if n == "B /01_POWER_TREE/BQ25185_SYS POUR 1" else (
          NEW2 if n == "B /01_POWER_TREE/BQ25185_SYS POUR 2" else None)
    if pts is None:
        continue
    o = z.Outline().Outline(0)
    was = [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6) for i in range(o.PointCount())]
    if [(round(x, 3), round(y, 3)) for x, y in was] == [(round(x, 3), round(y, 3)) for x, y in pts]:
        LOG[n] = "already reshaped"
        continue
    sp = pcbnew.SHAPE_POLY_SET(); sp.NewOutline()
    for x, y in pts: sp.Append(int(round(x * 1e6)), int(round(y * 1e6)))
    z.SetOutline(sp)
    LOG[n] = {"was": was, "now": pts}
f = b.FindFootprintByReference("MK1")
LOG["MK1_allow_soldermask_bridges"] = {"was": bool(f.AllowSolderMaskBridges())}
f.SetAllowSolderMaskBridges(True)
LOG["MK1_allow_soldermask_bridges"]["now"] = True
b.Save(BRD)
for _ in range(2):
    b = pcbnew.LoadBoard(BRD); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(BRD)
print(json.dumps(LOG, indent=1))
