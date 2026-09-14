#!/bin/bash
# D-710 -- rebuild the ACC_5V BOOST BASE from the promoted authority 4414da31.
#
# It holds EXACTLY the authority's 15 retained open edges over the same 10 nets
# and real refilled KiCad DRC is the inherited baseline (1 solder_mask_bridge,
# 199 lib_footprint_issues, 31 unconnected items) -- see
# evidence/d710-boost-base-drc.json and d710-boost-base-ledger.json.
#
# WHAT IT PROVES.  D-702(a) said U21.4 "has no ground" because the B GND fill
# stops 0.109 mm short, and D-703 spent five gate runs on the bond barrel that
# was supposed to give it one.  Neither was the problem: the blocker was the
# board's OWN `B /01_POWER_TREE/BQ25185_SYS POUR 2`.  Pull its east edge
# 60.000 -> 58.400 and B.Cu GND floods the pocket and reaches U21.4 directly,
# and the 6.3 mm "inert" GND chain out of U21.4 -- which D-703 could not remove
# because it was the converter's only return -- is then genuinely inert and
# comes out with the ledger UNCHANGED.  No bond barrel, and D-703's 0.025 mm
# bond-escape-versus-LX-neck conflict does not arise at all.
#
# Usage:  evidence/d710-build-boost-base.sh  [DEST]   (default /tmp/d710-boost)
set -e
MAN="$(cd "$(dirname "$0")/.." && pwd)"
W="${1:-/tmp/d710-boost}"
cd "$MAN"
rm -rf "$W"; mkdir -p "$W"

# 1. the pour narrowing -- a RESHAPE wholly inside its own former outline, the
#    shape verify_promotion --zone-reshaped was built for (D-703 section 6).
python3 evidence/d710-build-boost.py ../kicad/aqroot-demo "$W"

# 2. C65 +0.300 mm east.  D-703 said +0.350; +0.300 is the largest step that
#    swallows NO NEW barrel into C65.2's land (two GND vias are already under
#    it on the authority, at 61.900,41.000 and 62.400,40.600).
python3 evidence/d708-shiftloop.py "$W" "$W/x" C65 300000 0 0 \
    '/01_POWER_TREE/ACC_5V_RAW' 'GND' '+--allow-via-in-pad'
rm -rf "$W"/aqroot-Beta-v2.*; mv "$W/x"/aqroot-Beta-v2.* "$W"/; rmdir "$W/x"

# 3. the 6.3 mm GND chain out of U21.4, now that the plane reaches the land.
python3 evidence/d710-strip-objects.py "$W/aqroot-Beta-v2.kicad_pcb" \
    GND 58.5,37.8,61.3,39.6 B.Cu

echo "boost base at $W -- DRC must be the two inherited classes and 31 unconnected"
kicad-cli pcb drc --refill-zones --format json --units mm --severity-all \
    -o "$W/drc.json" "$W/aqroot-Beta-v2.kicad_pcb" >/dev/null 2>&1 || true
python3 - "$W/drc.json" <<'PY'
import collections, json, sys
d = json.load(open(sys.argv[1]))
print("  DRC", dict(collections.Counter(v["type"] for v in d["violations"])),
      "unconnected", len(d.get("unconnected_items", [])))
PY
