# FBV2-P2-002J — R80/R81 candidate poses

Each file is an `AQROOT_ECO_EXTRA` override: `{ref: [x, y, rotation, layer]}`,
applied on top of the committed 002F ECO so a candidate can be tested without
editing `place_p2_002f.py`.

Reproduce a screen with:

    AQROOT_ECO_002F=1 AQROOT_ECO_EXTRA=cand_002j/K6.json \
    AQROOT_PR43=1 AQROOT_LOCAL=R80 AQROOT_PROBE_PASS1=1 \
    AQROOT_PROBE_OUT=probe_K6.json AQROOT_SCRATCH=K6 AQROOT_WATCHDOG=60 \
    "<KICAD>/bin/python.exe" route_battery_block.py

Omit `AQROOT_LOCAL` and `AQROOT_PROBE_PASS1` for a full Phase A.

Measured results are in `../r80_screen_002j.json` (local screen) and
`../ledger_002j_K1.json` / `../ledger_002j_K6.json` (full Phase A).
**None of these poses is adopted** — see D-256.
