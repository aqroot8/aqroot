#!/bin/bash
cd /home/aqroot8/aqroot-demo
D=w/d696
python3 $D/strip.py $D/base.kicad_pcb /tmp/c1.kicad_pcb "Net-(SW9-A)" "Net-(U12-PG)" "Net-(U12-PS_SYNC)" "Net-(L1-Pad1)" "Net-(L1-Pad2)" 2>/dev/null
python3 $D/delvia.py /tmp/c1.kicad_pcb /tmp/c2.kicad_pcb 65.2,98.8 70.2,91.65 67.8,100.9 67.7,101.7 64.1,99.7 64.3,101.0 64.4,100.3 2>/dev/null
python3 $D/deltrk.py /tmp/c2.kicad_pcb $D/k0.kicad_pcb 66.1,100.0 2>/dev/null
cp $D/base.kicad_dru $D/k0.kicad_dru; cp $D/base.kicad_pro $D/k0.kicad_pro
cd hardware/demo/manufacturing
B=../../../$D/k0.kicad_pcb
mv(){ python3 apply_part_shift.py --board $B "$@" --apply --report /tmp/s.json >/dev/null 2>&1 || true
 python3 -c "
import json;d=json.load(open('/tmp/s.json'))
print('%-6s %-4s %s rot %s rel %d courts %s'%(d['ref'],d['verdict'],d['position_now_mm'],d['orientation_now_deg'],d['released_count'],d.get('courtyard_overlaps_new')))
for r in d['release_refusals'][:3]: print('   REFUSE',r)"; }
ch(){ APPLY=1 python3 ../../../$D/chain2.py $B "$@" | tail -2; }
ch TP6 -50000 -6900000 '/BQ25185_STAT1'
ch R127 7950000 -21750000 '/BQ25185_STAT1|+3V3' 180
ch TP13 4700000 -1800000 'Net-(SW9-A)|GND'
mv --ref C28  --dx-nm 1825000 --dy-nm 7255000 --release --release-net "/01_POWER_TREE/BQ25185_SYS" --release-net GND
mv --ref L1   --dy-nm -3850000 --rot-deg 180
mv --ref C28  --dx-nm -800000 --dy-nm -5400000 --rot-deg 90 --release --release-net "/01_POWER_TREE/BQ25185_SYS" --release-net GND
ch U12 0 -4200000 '+3V3|GND|/01_POWER_TREE/BQ25185_SYS' 90
ch TP14 24600000 -21600000 'Net-(U12-PS_SYNC)|GND'
ch TP8 29300000 -21600000 'Net-(U12-PG)|GND'
ch R43 50185000 -22735000 'GND|Net-(SW9-A)' 0
ch R42 53535000 -20935000 'GND|Net-(U12-PS_SYNC)' 180
ch R41 56885000 -19135000 '+3V3|Net-(U12-PG)' 180
