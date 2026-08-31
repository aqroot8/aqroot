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
    decision='D-323',                 # FBV2-P2-025: accelerometer/add-on presence-detect ACC_DETECT_N (R64.1 divider F.Cu / R129.2 series B.Cu / U3.17 PCAL expander GPIO B.Cu), a 3-pad cross-layer net = ONE 0.60/0.30 through via (R64.1<->R129.2, In1/In4 re-poured) + ONE same-layer B.Cu run (R129.2<->U3.17); a genuine functional low-speed CMOS detect input, PROMOTED after the cleaner-class candidate DISP_BL_CTL_STRAP (display backlight-control strap U1.16/TP2.1/R108.1/R109.1) hit a characterized local wall (ALL three MST edges NO_PATH at 0.200 mm even on the fine grid -- the dense MCU/backlight pad pocket, congestion 185, boxes every terminal; the MCU_EN_RC lesson) and after BTN_B_N (button SW7.1/R9.2/U2.18) FAILED the gate on connectivity (SW7 is a 4-pin tact switch whose two terminals share pad "1" 7.96 mm apart -> the per-ref MST leaves the second terminal unconnected; a framework limit of the whole button family, NOT a copper casualty); the via landed in the OPEN north 34.16 mm from every barrel and the realized copper clears BAT_PROTECTED_P by 3.88 mm (zero D-269 involvement); away from the west-XGPIO corridor / U11 power-tree wall / RF-NFC-USB-crystal-switching-rail-community mass
    sha256='a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626',
    tracks=781,                       # 759 (D-322) + 22 ACC_DETECT_N (3 F.Cu + 19 B.Cu 0.200 mm runs: R64.1->via short F.Cu leg + via->R129.2->U3.17 B.Cu detour)
    vias=68,                          # 67 (D-322) + 1 ACC_DETECT_N 0.60/0.30 through via at (57.900,38.800)
    copper_layers=6,
    zones=41,                         # unchanged (via -> only the In1/In4 GND reference planes re-poured for the anti-pad; zone COUNT constant)
    ratsnest=665,                     # 667 (D-322) - 2 (ACC_DETECT_N 3-pad net fully connected: 2 MST edges closed)
    journal=116,                      # 114 (D-322) + 2 ACC_DETECT_N REST_INC edges
)

# Convenience aliases (the names the existing probes already use for these pins).
SHA = EXPECTED['sha256']
TRACKS = EXPECTED['tracks']
VIAS = EXPECTED['vias']
COPPER_LAYERS = EXPECTED['copper_layers']
ZONES = EXPECTED['zones']
RATSNEST = EXPECTED['ratsnest']
JOURNAL_LEN = EXPECTED['journal']
