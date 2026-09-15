"""D-712 -- the PCB half of D-711's U2 channel ECO.

Exchanges the NET ASSIGNMENT of two PAIRS of PCAL9535A (U2) pads so the four
signals sit on the side of the TSSOP-24 their partners are on:

    pad 9  (P05, WEST)  /BQ25185_STAT1  <->  pad 20 (P17, EAST) /SX1262_DIO1
    pad 10 (P06, WEST)  /BQ25185_STAT2  <->  pad 19 (P16, EAST) /TOUCH_INT_N

This is the exact counterpart of evidence/d711-eco-u2-channel-swap.py on the
schematic; the two must be applied TOGETHER or schematic/PCB parity breaks.

Usage:  python3 evidence/d712-apply-pcb-pad-swap.py  <board.kicad_pcb>
"""
import re, sys
from pathlib import Path

B = Path(sys.argv[1])
s = B.read_text(encoding="utf-8")

SWAP = {"9": ("/BQ25185_STAT1", "/SX1262_DIO1"),
        "10": ("/BQ25185_STAT2", "/TOUCH_INT_N"),
        "19": ("/TOUCH_INT_N", "/BQ25185_STAT2"),
        "20": ("/SX1262_DIO1", "/BQ25185_STAT1")}

# U2's footprint block, located by its reference property.
i = s.find('(property "Reference" "U2"')
assert i > 0, "U2 reference property not found"
j = s.find('\n\t(footprint ', i)          # start of the NEXT footprint
if j < 0:
    j = len(s)
blk = s[i:j]

for num, (old, new) in SWAP.items():
    pat = re.compile(r'(\(pad "%s" smd roundrect\n(?:\t+\([^\n]*\n)*?\t+\(net ")%s("\))'
                     % (re.escape(num), re.escape(old)))
    blk, n = pat.subn(lambda m: m.group(1) + new + m.group(2), blk, count=1)
    assert n == 1, "pad %s: expected exactly one %r, matched %d" % (num, old, n)
    print("U2.%-3s %-16s -> %s" % (num, old, new))

s = s[:i] + blk + s[j:]
B.write_text(s, encoding="utf-8")
print("wrote", B)
