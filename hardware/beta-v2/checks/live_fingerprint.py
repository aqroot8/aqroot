# -*- coding: utf-8 -*-
"""FBV2-P2-011 / D-309 -- SINGLE SOURCE OF TRUTH for the CURRENT authoritative
board fingerprint.

Every incremental read-only probe (incremental_probe_006..NNN,
phaseB_bringup_probe_005) and the G-contract regression pin the SAME live
authoritative board: its sha256, track / via / copper-layer / zone counts, the
ratsnest and the journal length.  Before D-309 these five constants were
declared IDENTICALLY inside each probe and had to be hand-edited (~25 identical
edits) on every promoted increment -- pure repetitive maintenance that the
Opportunity & Simplification Scan flagged.

This module centralises that pin to ONE place, bumped ONCE per promotion.  It is
a pure DRY consolidation and weakens NO historical contract: every probe still
asserts "live board == EXPECTED", exactly as before -- only the literal now lives
here instead of being copied into each file.  Each probe keeps ALL of its own
increment-specific structural / connectivity / DRC checks inline.

Bump procedure on each promoted increment: update the EXPECTED dict below to the
new authoritative sha / counts (the values `incremental_router.py baseline`
prints, or the promote summary).  Nothing else changes.
"""

# The authoritative board fingerprint after the most recently promoted increment.
EXPECTED = dict(
    decision='D-320',                 # FBV2-P2-022: IR transmit carrier CONTROL leg IR_TX_GPIO16 (U1.9 ESP32 GPIO16 -> R22.1 series-drive resistor), dedicated 2-pad point-to-point net, SAME-LAYER F.Cu MST, NO via -- the cleanest class (no plane re-pour); the low-current MCU control GPIO, isolated by series R22 from the IR_GATE switch node and the IR_LED_A/K emitter power (both excluded switching/emitter nets); in an OPEN region 35.2 mm clear of BAT_PROTECTED_P (zero D-269 involvement); away from the west-XGPIO corridor / U11 power-tree wall / RF-NFC-USB-crystal-switching-rail-community mass
    sha256='4e706490389655cb8b68f8c15249a813072f36a9ea9e6ffaeb1fdd2194c0bf34',
    tracks=729,                       # 716 (D-319) + 13 IR_TX_GPIO16 (single same-layer F.Cu MST run, detoured 13 segments around the GND pinch)
    vias=67,                          # unchanged (no via -- both pads on F.Cu)
    copper_layers=6,
    zones=41,                         # unchanged (no via -> no plane re-pour; zone COUNT + FILL constant)
    ratsnest=671,                     # 672 (D-319) - 1 (IR_TX_GPIO16 2-pad net fully connected)
    journal=110,                      # 109 (D-319) + 1 IR_TX_GPIO16 REST_INC edge
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
