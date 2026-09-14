#!/bin/bash
# D-708 -- rebuild the gated finalist (run r9) from the authority.
#
#   37 -> 15 retained open edges against an authority of 16
#   failed_nets [], nets_regressed [], refused_clauses [] (all fifteen true)
#   DRC = {solder_mask_bridge: 1, lib_footprint_issues: 199}, attributable []
#   PP1-PP4 true against its own base; promotion_candidate TRUE
#
# It is held out of promotion by ONE clause measured HEAD -> candidate:
# pour_partition PP2 prices the GND fragment {C36.2, C5.2, C7.2, R37.2, R40.2}
# at 2.295 A against a 3.125 A BAT_MAIN neighbour bar, because C5.2 reaches the
# pocket's ONLY legal 0.500 mm barrel through 4.383 mm of widest path.  See
# d708-bond-at-controls.json: that is a geometry fact, not a routing one.
#
# Usage:  evidence/d708-build-finalist.sh  [WORKDIR]   (default /tmp/d708)
set -e
MAN="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$MAN/../kicad/aqroot-demo"
W="${1:-/tmp/d708}"
cd "$MAN"

rm -rf "$W"; mkdir -p "$W/base"
# 1. the owner-authorized outline: x 72 -> 77 between y 70.500 and y 104.005,
#    with all five full-board planes grown to it (D-703 option 2, D-707).
python3 evidence/d708-expand-outline.py "$SRC/aqroot-Beta-v2.kicad_pcb" "$W/base" 77 70.5 104.005
# 2. three keep-outs, because qrouter takes its extents from a bounding box and
#    would otherwise lay copper in the notch a stepped outline leaves.
python3 evidence/d708-add-step-keepouts.py "$W/base/aqroot-Beta-v2.kicad_pcb"
# 3. the two I2C lines are stripped rather than released: a --release closure
#    stops AT a via and leaves it connected on one layer, and each --release-via
#    exposes the next (see the D-708 addendum).
cp -r "$W/base" "$W/t0"
python3 evidence/d696-strip.py "$W/t0/aqroot-Beta-v2.kicad_pcb" "$W/t0/aqroot-Beta-v2.kicad_pcb" \
    '/09_COMMUNITY_HEADER/EXT_SDA' '/09_COMMUNITY_HEADER/EXT_SCL'
# 4. J8 +5.000 mm east so the Qwiic port stays ON the new right wall (D-707).
python3 evidence/d708-shiftloop.py "$W/t0" "$W/t1" J8 5000000 0 0 'GND' '/ACC_3V3_SW'
# 5. R36 into the new area -- the one part move that gives /01_POWER_TREE/
#    ILIM_VSET a via-free run to U11.7 and frees the via column ISET needs.
python3 evidence/d708-shiftloop.py "$W/t1" "$W/t2" R36 4750000 -5250000 0 \
    '/01_POWER_TREE/ILIM_VSET' 'GND' \
    '+--release-via' '+/01_POWER_TREE/ILIM_VSET:68.6,80.25' \
    '+--release-via' '+/01_POWER_TREE/ILIM_VSET:69.25,76.45'
# 6. USB_VBUS_CHG's In3 leg is redundant once its U11 end is evicted, and it is
#    one series chain, so it cannot be partly evicted without dangling.
cp -r "$W/t2" "$W/t3"
python3 evidence/d708-strip-layer.py "$W/t3/aqroot-Beta-v2.kicad_pcb" "$W/t3/aqroot-Beta-v2.kicad_pcb" \
    '/01_POWER_TREE/USB_VBUS_CHG' In3.Cu
# 7. and /ACC_POWER_FAULT_N, which r9 re-routes (it does NOT move C5.2's price:
#    that was measured and is why this decision promoted no copper).
cp -r "$W/t3" "$W/t6"
python3 evidence/d696-strip.py "$W/t6/aqroot-Beta-v2.kicad_pcb" "$W/t6/aqroot-Beta-v2.kicad_pcb" \
    '/ACC_POWER_FAULT_N'

echo "base built at $W/t6 -- real DRC must be the two inherited classes ALONE"
kicad-cli pcb drc --refill-zones --format json --units mm --severity-all \
    -o "$W/base-drc.json" "$W/t6/aqroot-Beta-v2.kicad_pcb" >/dev/null 2>&1 || true
python3 - "$W/base-drc.json" <<'PY'
import collections, json, sys
d = json.load(open(sys.argv[1]))
print("  base DRC", dict(collections.Counter(v["type"] for v in d["violations"])))
PY

AQROOT_OFFCENTRE_LAUNCH=1 python3 route_maze_batch.py \
  --board "$W/t6/aqroot-Beta-v2.kicad_pcb" \
  --grid 25000 --partial --join-max-mm 0 --trunk-floor --escape-floor --neck \
  --maze-via 500000:250000 --repair-planes \
  --evict /BQ25185_STAT1 --evict /01_POWER_TREE/ILIM_VSET \
  --evict /01_POWER_TREE/USB_VBUS_CHG --evict /01_POWER_TREE/ISET \
  --evict-window 58.5,70.0,77.0,85.5 \
  --bond-pad J8.1 --bond-pad C23.1 --bond-pad C63.2 --bond-pad C5.2 \
  --bond-via 500000:250000 \
  --tap --tap-first --tap-max-mm 4 --guard "$MAN/evidence/d708-npth-guard.json" \
  --work "$W/r9" --out "$W/r9.json" \
  /BQ25185_STAT1 /01_POWER_TREE/ILIM_VSET /01_POWER_TREE/USB_VBUS_CHG \
  /01_POWER_TREE/ISET /ACC_POWER_FAULT_N /ACC_3V3_SW \
  /09_COMMUNITY_HEADER/EXT_SDA /09_COMMUNITY_HEADER/EXT_SCL
