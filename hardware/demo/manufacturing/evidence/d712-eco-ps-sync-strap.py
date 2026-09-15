r"""D-712 ECO -- tie the TPS63020's PS/SYNC pin to GND AT THE PIN.

WHY.  R42 is a 0R tying U12.13 (PS/SYNC) to GND, and on the PCB it sits at
(16.665, 120.335) -- FIFTY MILLIMETRES west of the pin it straps -- with TP14
at (40.500, 124.500) on the way.  Thirty-three objects of B.Cu haul cross the
board for it, and its last two segments lie in the C24/C26 gate, which D-649
measured as a SINGLE-FILE corridor that the /01_POWER_TREE/BQ25185_SYS pour
and this net cannot share.  That is why C26.2 -- a 10 uF bulk capacitor on the
system rail -- is an ISLAND on the authority board.

U12 sits 0.505 mm north of the WROOM ANTENNA KEEP-OUT, so its whole south pad
row has 0.900 mm of board to escape into, and that band cannot hold U12.12's
EN escape, a PS/SYNC escape AND the SYS pour's path at the same time.

A 0R to GND and a direct tie to GND are the SAME CIRCUIT.  TPS63020 PS/SYNC
low = power-save mode, which is what a 0R to GND selects and what a
battery-powered device wants; the resistor only ever existed as a
depopulate-to-choose option, and AQROOT Demo does not exercise it.

THE EDIT, on 01_power_tree.kicad_sch:
  * delete R42 (0R) and TP14 (test point)
  * delete the four wires that served them
  * MOVE the GND power symbol #PWR0146 from R42's pin 1 to U12 pin 13 and
    shorten the pin-13 wire to meet it

The PCB half is evidence/d712-build-b3.py: U12.13's pad joins GND and a
0.610 mm B.Cu track ties it to U12.15, U12's own thermal ground pad.

Usage:  python3 evidence/d712-eco-ps-sync-strap.py [01_power_tree.kicad_sch]
"""
import re
import sys
from pathlib import Path

SCH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "../kicad/aqroot-demo/01_power_tree.kicad_sch")
s = SCH.read_text(encoding="utf-8")
orig = s


def symbol_block(ref):
    for m in re.finditer(r"\n\t\(symbol\n", s):
        j = m.start()
        k = s.find("\n\t(symbol\n", j + 5)
        k = k if k > 0 else len(s)
        blk = s[j:k]
        if re.search(r'\(property "Reference" "%s"' % re.escape(ref), blk):
            return blk
    raise SystemExit("no symbol %r" % ref)


for ref in ("R42", "TP14"):
    blk = symbol_block(ref)
    assert s.count(blk) == 1
    s = s.replace(blk, "", 1)
    print("deleted symbol", ref)

WIRES = [((204.47, 76.20), (205.74, 76.20)),      # GND -> R42.1
         ((213.36, 76.20), (213.36, 72.39)),      # R42.2 -> PS/SYNC net
         ((224.79, 90.17), (219.71, 90.17)),      # TP14 -> PS/SYNC net
         ((219.71, 90.17), (219.71, 72.39))]
for a, b in WIRES:
    pat = re.compile(
        r"\t\(wire\n\t\t\(pts\n\t\t\t\(xy %g %g\) \(xy %g %g\)\n\t\t\)\n"
        r"\t\t\(stroke\n\t\t\t\(width 0\)\n\t\t\t\(type default\)\n\t\t\)\n"
        r'\t\t\(uuid "[0-9a-f-]+"\)\n\t\)\n' % (a[0], a[1], b[0], b[1]))
    s, n = pat.subn("", s, count=1)
    assert n == 1, "wire %s -> %s not found exactly once" % (a, b)
    print("deleted wire (%.2f,%.2f)->(%.2f,%.2f)" % (a + b))

# the surviving pin-13 wire now runs from the new GND symbol instead of the bus
old = "(xy 213.36 72.39) (xy 228.6 72.39)"
new = "(xy 223.52 72.39) (xy 228.6 72.39)"
assert s.count(old) == 1
s = s.replace(old, new, 1)
print("shortened U12.13 wire to (223.52,72.39)->(228.60,72.39)")

# #PWR0146 moves from R42's pin 1 to U12 pin 13.  Same symbol, same reference,
# same UUID -- only its position and its text anchors move.
blk = symbol_block("#PWR0146")
moved = (blk.replace("(at 204.47 76.2 270)", "(at 223.52 72.39 270)")
            .replace("(at 198.12 76.2 0)", "(at 217.17 72.39 0)")
            .replace("(at 203.2 74.422 90)", "(at 222.25 70.612 90)")
            .replace("(at 204.47 76.2 0)", "(at 223.52 72.39 0)"))
assert moved != blk
s = s.replace(blk, moved, 1)
print("moved GND symbol #PWR0146 to U12.13 at (223.52,72.39)")

assert s != orig
SCH.write_text(s, encoding="utf-8")
print("wrote", SCH)
