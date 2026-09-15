r"""D-713 -- move /SX1262_DIO1 off U2's west column onto a FREE U3 channel.

D-710 measured that U2.9/U2.10/U2.11 -- three adjacent PCAL9535A pins in one
column -- share ONE conductor's worth of corridor.  D-712 spent D-711's channel
swap and closed /BQ25185_STAT1 with it, but the wall did not go away: it moved.
Measured on the promoted authority, evicting /TOUCH_INT_N lets /SX1262_DIO1
route and then /TOUCH_INT_N is NO_PATH, and the reverse.  The column holds
exactly TWO of {SX1262_DIO1, TOUCH_INT_N, SD_CARD_DETECT_N}.

U2 IS FULL -- all sixteen GPIO channels are assigned.  U3, the second
PCAL9535A on the same I2C bus and the same /WAKE_INT_N interrupt line, has
FOUR: P06 (pin 10), P07 (pin 11), P10 (pin 13) and P11 (pin 14).  A LoRa DIO1
interrupt does not care which expander it lands on.

Usage:  python3 evidence/d713-move-dio1-to-u3.py <board.kicad_pcb> [U3_PIN]
"""
import re
import sys
from pathlib import Path

B = Path(sys.argv[1])
U3PIN = sys.argv[2] if len(sys.argv) > 2 else "11"
s = B.read_text(encoding="utf-8")


def repad(ref, num, old, new):
    global s
    i = s.find('(property "Reference" "%s"' % ref)
    assert i > 0, ref
    j = s.find("\n\t(footprint ", i)
    j = j if j > 0 else len(s)
    blk = s[i:j]
    pat = re.compile(r'(\(pad "%s" smd roundrect\n(?:\t+\([^\n]*\n)*?\t+\(net ")%s("\))'
                     % (re.escape(num), re.escape(old)))
    blk, n = pat.subn(lambda m: m.group(1) + new + m.group(2), blk, count=1)
    assert n == 1, "%s.%s: expected exactly one %r" % (ref, num, old)
    s = s[:i] + blk + s[j:]
    print("%s.%-3s %-28s -> %s" % (ref, num, old, new))


repad("U2", "9", "/SX1262_DIO1", "unconnected-(U2-P05-Pad9)")
repad("U3", U3PIN, "unconnected-(U3-P%s-Pad%s)"
      % ({"10": "06", "11": "07", "13": "10", "14": "11"}[U3PIN], U3PIN),
      "/SX1262_DIO1")
B.write_text(s, encoding="utf-8")
print("wrote", B)
