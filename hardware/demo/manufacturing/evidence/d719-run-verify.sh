timeout 1200 python3 hardware/demo/manufacturing/verify_promotion.py --ref HEAD \
  --nets 'Net-(L1-Pad1),Net-(L1-Pad2),/01_POWER_TREE/V3V3_FB,Net-(SW9-A),Net-(U12-PG),/BQ25185_STAT1,+3V3,GND,/01_POWER_TREE/BQ25185_SYS' \
  --track-width 200000 --via-drill 300000 --annular 150000 \
  --evicted 'Net-(L1-Pad1)' --evicted 'Net-(L1-Pad2)' --evicted '/01_POWER_TREE/V3V3_FB' \
  --evicted 'Net-(U12-PG)' --evicted 'Net-(SW9-A)' --evicted '/BQ25185_STAT1' \
  --evicted '+3V3' --evicted 'GND' \
  --moved U12 --moved L1 --moved C28 --moved C31 --moved C32 --moved R39 --moved R40 \
  --moved R41 --moved R43 --moved TP6 --moved TP8 \
  --out w/d719/d719-verify-promotion.json
