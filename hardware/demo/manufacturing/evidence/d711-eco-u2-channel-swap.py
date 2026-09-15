"""D-710 ECO -- swap two PAIRS of PCAL9535A (U2) GPIO channels so that four
signals sit on the side of the package their partners are on.

    P05 (pin 9)  BQ25185_STAT1  <->  P17 (pin 20) SX1262_DIO1
    P06 (pin 10) BQ25185_STAT2  <->  P16 (pin 19) TOUCH_INT_N

WHY.  U2 is a TSSOP-24 with pins 1-12 on its WEST column and 13-24 on its EAST
column.  /BQ25185_STAT1 and /BQ25185_STAT2 come from U11 and TP6/TP7 in the
EAST (x 62.7 .. 70.3) and were landed on the WEST column, while /SX1262_DIO1
(U8.13 at x 3.000) and /TOUCH_INT_N (J1.46 at x 22.410) come from the WEST and
were landed on the EAST column.  All four therefore CROSS the package, and the
crossing is why U2.9/U2.10/U2.11 share one conductor's worth of corridor.

IT COSTS NOTHING.  All four channels are INPUTS and all four targets are
already configured as inputs (06h = E0h, 07h = FFh are UNCHANGED), every
PCAL9535A channel is interrupt-capable, no part moves, no net is added or
removed and no footprint changes.  What changes is the bit position firmware
reads -- and the interrupt mask policy moves with the nets.

THE EDIT, on 08_buttons_expanders.kicad_sch:
  * delete the wire joining P05's pin stub to R127's pull-up chain
  * delete the wire joining P06's pin stub to R128's pull-up chain
  * move the SX1262_DIO1 hierarchical label from P17's stub to P05's
  * move the TOUCH_INT_N hierarchical label from P16's stub to P06's
  * add a local BQ25185_STAT1 label on P17's stub and a local BQ25185_STAT2
    label on P16's, which join R127's and R128's chains BY NAME -- each net
    keeps exactly ONE hierarchical label, so the sheet's ports are unchanged
"""
import re, sys
from pathlib import Path

SCH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "../kicad/aqroot-demo/08_buttons_expanders.kicad_sch")
s = SCH.read_text(encoding="utf-8")
orig = s

WIRE = ('\t(wire\n\t\t(pts\n\t\t\t(xy %s) (xy %s)\n\t\t)\n\t\t(stroke\n'
        '\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n')
for a, b, u in (("101.6 67.31", "113.03 67.31",
                 "fb080108-0801-4b08-9b08-000000000001"),
                ("101.6 69.85", "129.54 69.85",
                 "fb080108-0801-4b08-9b08-00000000000a")):
    w = WIRE % (a, b, u)
    assert s.count(w) == 1, "wire %s -> %s not found exactly once" % (a, b)
    s = s.replace(w, "", 1)
    print("deleted wire (%s) -> (%s)" % (a, b))

for name, old_at, new_at in (("SX1262_DIO1", "101.6 95.25 0", "101.6 67.31 0"),
                             ("TOUCH_INT_N", "101.6 92.71 0", "101.6 69.85 0")):
    pat = '(hierarchical_label "%s"\n\t\t(shape input)\n\t\t(at %s)' % (
        name, old_at)
    assert s.count(pat) == 1, "hier label %s not found exactly once" % name
    s = s.replace(pat, pat.replace("(at %s)" % old_at, "(at %s)" % new_at), 1)
    print("moved hierarchical_label %-14s %s -> %s" % (name, old_at, new_at))

LABEL = ('\t(label "%s"\n\t\t(at %s 0)\n\t\t(effects\n\t\t\t(font\n'
         '\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n'
         '\t\t)\n\t\t(uuid "%s")\n\t)\n')
anchor = '\t(hierarchical_label "SX1262_DIO1"'
assert s.count(anchor) == 1
add = "".join(LABEL % (n, at, u) for n, at, u in (
    ("BQ25185_STAT1", "101.6 95.25", "d7100108-0801-4b08-9b08-000000000101"),
    ("BQ25185_STAT2", "101.6 92.71", "d7100108-0801-4b08-9b08-000000000102")))
s = s.replace(anchor, add + anchor, 1)
print("added local labels BQ25185_STAT1 @101.6,95.25 and "
      "BQ25185_STAT2 @101.6,92.71")

assert s != orig
SCH.write_text(s, encoding="utf-8")
print("wrote", SCH)
