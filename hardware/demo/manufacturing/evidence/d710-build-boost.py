"""D-710 -- build the ACC_5V boost candidate base from the authority.

  1. narrow `B /01_POWER_TREE/BQ25185_SYS POUR 2`'s east edge 60.000 -> 58.400
     so the B.Cu GND plane floods the pocket and reaches U21.4 (D-703 s2)
  2. C65 +0.350 mm east, which takes the U21.4-land / C65.1-land gap
     0.7345 -> 1.0845 mm against the 0.900 mm a 0.600 mm SWITCH_NODE owes

Usage: d710-build-boost.py SRC_DIR DEST_DIR
"""
import re, shutil, sys
from pathlib import Path
SRC, DEST = Path(sys.argv[1]), Path(sys.argv[2])
DEST.mkdir(parents=True, exist_ok=True)
for f in SRC.glob("aqroot-Beta-v2.*"):
    shutil.copy(f, DEST / f.name)
bd = DEST / "aqroot-Beta-v2.kicad_pcb"
s = bd.read_text(encoding="utf-8")

old = "(xy 55 33) (xy 60 33) (xy 60 42) (xy 55 42)"
new = "(xy 55 33) (xy 58.4 33) (xy 58.4 42) (xy 55 42)"
n = s.count(old)
assert n == 1, "POUR 2 outline found %d times" % n
s = s.replace(old, new, 1)
bd.write_text(s, encoding="utf-8")
print("POUR 2 east edge 60.000 -> 58.400")
