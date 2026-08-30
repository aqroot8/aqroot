# FBV2-P2-011 / D-309 — Sixth rest-of-board incremental increment routed + PROMOTED (IR receiver local filtered supply `IR_RX_VS_LOCAL`) — display/touch group empirically disproved; shared live-fingerprint helper landed

**Date:** 2026-08-30
**Class:** Governed CTO ACCEPT + PROMOTE — routine rest-of-board routing within CTO authority. **No owner decision raised.**
**Starting HEAD:** `49528f2` (D-308; pushed; `origin/master` identical).
**Authoritative PCB:** `sha256 f4e95dec…8559e7ee` (527 trk / 58 via / 6 layers / 41 zones, ratsnest 690, journal 91) → **`sha256 5c5cae79465416c81f9d7b8dba5b2e3a3325bd9a0680b65103badf0e1a339f63`** (535 trk / 58 via / 6 layers / 41 zones, ratsnest 688, journal 93).

---

## Summary

The sixth rest-of-board increment is on the authoritative board. The same
`incremental_router.py` (baseline/route/gate/promote), with **zero new
mechanics**, loaded the D-308 promoted board and routed the **IR receiver (U6)
local filtered supply** `IR_RX_VS_LOCAL` WITHOUT touching a single strand of
accepted Phase-A / FRONT_RGB / ACC / DISP / IMU / FRONT_RGB_LED copper. A real
full-board gate proved a GENUINE no-casualty / no-new-DRC connectivity increment
(ratsnest 690→688, DRC unchanged, **no via ⇒ no plane re-pour ⇒ all 41 zones
byte-identical**) → **COPPER PROMOTED.** Autonomy continues; D-275 and D-277..D-308
preserved.

The pick was **earned on gate evidence, not defaulted to.** The task-preferred
coherent **display/touch control group** (`TOUCH_RST_N` + `TOUCH_INT_N`) and the
other bounded alternatives (`AMP_SD_MODE`, `SD_CARD_DETECT_N`) were each routed on
scratch (router said ALL OK) and then **FAILED the real full-board gate with new
`clearance` violations** — they are long cross-board hauls (33–68 mm) whose
cross-layer via lands in the **congested U2 B.Cu escape region beside the accepted
D-306 `DISP_RST_N` through-via.** `IR_RX_VS_LOCAL` — a pristine same-layer F.Cu
cluster — was the clean winner.

`IR_RX_VS_LOCAL` (07_IR) is the RC-filtered local supply of the IR demodulator
U6: series filter **R21.2** (F.Cu SMD) + decoupling **C11.1** (F.Cu SMD) → **U6.3**
supply pin (THT, on both faces). All three pads share the F.Cu outer layer (U6.3
is THT), so every MST edge is a **same-layer F.Cu run with NO via** — the cleanest
increment class (like D-307 `IMU_ADDR`, but on F.Cu). Noncritical low current, not
a bulk rail; a tight NE-corner cluster measured **pristine** (0 accepted copper
within bbox+2 mm).

---

## A — Candidate selection (3–5 measured on the current board; evidence, not geometry)

Baseline `f4e95dec…` (527/58/6, ratsnest 690, journal 91). The READ-ONLY screen
`w/screen_010.py` (re-run) plus a new READ-ONLY pad/netclass inspector
`w/inspect_011.py` measured the task-nominated candidates. All are **Default**
netclass (0.200/0.200, via 0.60/0.30 — no special pattern matches). **Four groups
were routed on scratch and put through the real full-board gate** (authoritative
untouched throughout):

| Group | Nets | Pads / geometry | `route` | **`gate`** | Why |
|---|---|---|---|---|---|
| **`IR_RX_VS`** | `IR_RX_VS_LOCAL` | C11.1 F, R21.2 F, U6.3 THT — NE-corner cluster span ~10×4 mm, **cu 0**, all F.Cu, **no via** | ALL OK (2/2, 3.113 + 9.291 mm) | **PASS (0 fails)** | **SELECTED** — pristine local coherent supply-filter; no via; cleanest class |
| `TOUCH_CTL` | `TOUCH_RST_N` + `TOUCH_INT_N` | J1.47/R12.1 F + U2.4 B; J1.46 F + U2.19 B — 33 & 38 mm cross-board, cu 21/24, 2 vias | ALL OK (3/3) | **FAIL — +3 `clearance`** | task-preferred display/touch group; **not clean** — via collides at U2 B.Cu escape beside D-306 `DISP_RST_N` via |
| `AMP_SD_MODE` | `AMP_SD_MODE` | R15.1/U5.4 F + U2.7 B — 57 mm haul, cu 57, 1 via | ALL OK (2/2) | **FAIL — +7 `clearance`** | same congested U2 escape |
| `SD_DETECT` | `SD_CARD_DETECT_N` | J2.10/R113.2 F + U2.11 B — 68 mm haul, cu 57, 1 via | ALL OK (2/2) | **FAIL — +2 `clearance`** | same congested U2 escape |

**Key negative-evidence finding — the U2 B.Cu escape wall.** `TOUCH_RST_N`,
`TOUCH_INT_N`, `AMP_SD_MODE`, `SD_CARD_DETECT_N` all target pins on **U2's B.Cu
edge** (U2.4/.7/.11/.19), immediately beside the accepted D-306 `DISP_RST_N`
through-via (U2.8). The router finds a geometric path (its clearance model differs
subtly from KiCad DRC around an existing through-via), but the real full-board DRC
reports the new via/track within 0.200 mm of the `DISP_RST_N` via barrel. This is
a **characterised wall** (like `U11_PROG`/`PWR_SENSE`), not a routing bug — it
needs a deliberate U2-escape corridor plan, **deferred to FBV2-P2-012**. The
failing candidate `GROUPS` entries are annotated with this result so they are not
naively retried. The "favor display/touch **if clean**" preference was honored:
it was tried first and empirically shown *not* clean.

`IR_RX_VS` is not merely a fallback — it is a genuinely coherent standalone
peripheral group (U6 supply filter), local and pristine, and it is the cleanest
increment class available (same-layer, no via, no plane re-pour). It won on the
gate.

## B — Route → gate → promote (one foreground experiment; authoritative untouched)

- **`route IR_RX_VS`** → ALL OK (2/2): `IR_RX_VS_LOCAL` C11.1↔R21.2 (3.113 mm,
  F.Cu) + R21.2↔U6.3 (9.291 mm, F.Cu); **8 segments, all 0.200 mm F.Cu, NO via**;
  no plane re-pour; scratch 535/58; AUTH sha UNCHANGED (`f4e95dec…`).
- **`gate IR_RX_VS`** = **PASS, every check**: no prior copper deleted/altered
  (D-308 527 trk + 58 via multiset is a SUBSET); 8 new items, all target-net;
  **all 41 zones byte-identical** (no via ⇒ no In1/In4 re-pour); `IR_RX_VS_LOCAL`
  fully connected (open edges 2→0); 0 prior requested pairs regressed; ratsnest
  690→688 EXACTLY −2; no new/worse DRC class; `unconnected_items` 499→499.
- **`promote IR_RX_VS`** re-ran the gate (PASS), re-verified the AUTH sha had not
  drifted (`f4e95dec…`), copied scratch→authoritative and merged the 2 route
  entries as `role=REST_INC`.

## C — What is promoted (integrity)

Authoritative `sha256 f4e95dec…8559e7ee` → **`5c5cae79…a339f63`**; tracks
**527→535** (+8 IR_RX_VS_LOCAL F.Cu); vias **58** (unchanged — no via); 6 layers /
41 zones unchanged; ratsnest **690→688** (−2); journal **91→93** (+2 `REST_INC`).
PCB file diff = **64 insertions / 0 deletions** (the cleanest class — tied with
D-307): all 8 additions are `(segment …)` F.Cu lines, **0 `segment`/`via`/
`footprint` deletions, 0 zone/`filled_polygon` changes** (no via ⇒ no plane
re-pour ⇒ every zone byte-identical). Real KiCad DRC **identical**
(`{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199,
unconnected_items:499}`; error-severity `kicad-cli` view = `solder_mask_bridge:1`
+ `hole_clearance:5`, unchanged). Every 432 Phase-A + 20 FRONT_RGB + 31 ACC + 11
DISP + 8 IMU + 25 FRONT_RGB_LED track and all 58 prior vias present
byte/geometry-identical; only new copper is the 8 `IR_RX_VS_LOCAL` F.Cu tracks. No
placement/DRU/netclass/footprint/value/polarity/outline/stackup change.

## D — Tests

New contract **G23** pins the increment (`IR_RX_VS_LOCAL` connected =
C11.1-R21.2-U6.3 one island; copper legal = 8 trk F.Cu 0.200 mm, **no via**;
ADD-ONLY = RGB_LED 25 + IMU 8 + DISP 11 + ACC 31 + RGB 20 + Phase-A 432/54).
G18–G22 stay green unchanged — their ADD-ONLY invariants exclude ALL
`role=REST_INC` nets generically and pin `phaseA_via`==54, so they auto-generalise.
`router_regression.py` = **ALL CHECKS PASS (G1–G23), 98 PASS lines, 0 failed**, run
twice, deterministic; G17 confirms 535 trk / 58 via / ratsnest 688 / 41 zones.

New focused probe `incremental_probe_011.py` (READ-ONLY: D-309 fingerprints;
pre-D-309 copper preserved exactly = 527 trk + 58 via; 8-track F.Cu increment, no
via; `IR_RX_VS_LOCAL` connected; no pair regressed; DRC unchanged) ALL PASS.
`incremental_probe_006/007/008/009/010.py` refreshed to the D-309 board (each still
proving its own net intact; the "pre-X copper" checks generalise to exclude
post-X increments) ALL PASS. `phaseB_bringup_probe_005.py` updated (535/58/93;
accepted-increment set + `IR_RX_VS_LOCAL`; 164 rest nets, **11 routed, 153
unrouted**) ALL PASS.

**Real-board DRC / connectivity re-run independently on the promoted board:**
`kicad-cli` error-severity DRC = `solder_mask_bridge:1` + `hole_clearance:5`,
`unconnected_items` 499; pcbnew ratsnest 688 — **no new `clearance` class from the
increment.**

**Phase-A DRU-synthesis probes (`d269_probe`, `d264_probe`, `dru_probe`) — NOT
part of the maintained increment regression, and NOT regressed by D-309.** Proven
by a board-swap A/B test: the committed D-308 board and the promoted D-309 board
give **byte-identical** probe verdicts — `d269_probe` FAIL(2) (C/D flaky borderline
BAT_RAW-divider synthetic clearance, per the D-308 finding), `d264_probe` FAIL(2)
(pre-existing path-role rule-emission reds, checks B/C), `dru_probe` FAIL(2)
(pre-existing). These probes analyze the **BAT_\*/LTC power-tree DRU rules**; the
`IR_RX_VS_LOCAL` increment is 8 F.Cu tracks in the NE corner ~60 mm away and cannot
affect them. No rule was touched or weakened; the flaky full-zone-re-pour proxy was
not mistaken for authoritative DRC (the real byte-stable board is DRC-clean).

## E — Opportunity & Simplification Scan (mandated) — shared live-fingerprint helper LANDED

The framework held with **zero new routing mechanics** (`IR_RX_VS` is the proven
same-layer no-via class; `connect_cross`/`refill_planes`/`qrouter.py` untouched).

**Acted-on simplification (the exact one D-308 §E pre-flagged):** the five
incremental probes plus `phaseB_bringup_probe_005` had each been declaring the
**same** five-line `EXPECT_{SHA,TRACKS,VIAS,JOURNAL,RATSNEST}` fingerprint pin,
hand-edited **identically (~25 edits) every increment** — pure repetitive
maintenance. This cycle introduced **`live_fingerprint.py`**, a single
source-of-truth `EXPECTED` dict (sha/tracks/vias/layers/zones/ratsnest/journal)
bumped **once** per promotion, and refactored all six probes to import it. This is
a **pure DRY consolidation that weakens no historical contract**: every probe still
asserts "live board == EXPECTED" exactly as before, and each keeps ALL of its own
increment-specific structural/connectivity/DRC checks inline. Verified: all six
probes PASS after the refactor; the per-increment probe edit is now "bump one dict
+ add one new probe + one new G-contract" instead of "touch 5–6 files identically".
It is bounded (mechanical constant→import swap), reversible, and does not touch the
G-contract regression (already generalised).

*Not acted on (bounded-scope discipline):* the failing candidate `GROUPS` entries
were **kept and annotated** (measured `clearance` counts + the U2-escape wall +
"deferred to FBV2-P2-012") rather than deleted, so the negative evidence is
self-documenting. No BOM/recoverability/testability/firmware/UX/mechanical change
forced; In2/In3 remain spare capacity. **Open owner decisions: NONE.**

## F — Integrity & rollback

Rollback = pre-promotion `sha256 f4e95dec…8559e7ee` (D-308; parent `49528f2`;
restored by `git checkout` of the PCB + journal; the D-302/D-304/D-305/D-306/D-307/
D-308 rollback points still stand). All locked invariants preserved: no
DRU/rule/clearance/stackup/topology/net/footprint/value/polarity/outline change;
no D-290 reauth; **no via at all** in this increment; D-249 (≥1.20 mm BPP), D-269
(0.300 mm), 0.300 BAT_MAIN, 0.60 mm BAT_MAIN, 0.200/0.150 signal, 0.25 hole-hole,
D-257/D-258/D-263/D-264/D-266, D-275/D-288 bridge, **In1/In4 GND roles** (untouched
— no via ⇒ no plane re-pour), USB/RF/mechanical reservations ENFORCED;
`AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO`
(D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), fixture split (G17), FRONT_RGB
(G18/D-304), ACC_3V3_CTL (G19/D-305), DISP_RST_N (G20/D-306), IMU_ADDR (G21/D-307),
FRONT_RGB_LED (G22/D-308), `place_003l` (D-285), D-275 and D-277..D-308 preserved;
frozen `beta-full-reference-v1` untouched; DEVICE_SPEC unchanged (no hardware fact
changed); shared journal authoritative (93 entries); no orphan process.

## G — Next: FBV2-P2-012

Continue rest-of-board routing via the same framework (**153 of 164 rest nets
unrouted**). Proven classes: same-layer (B.Cu/F.Cu, no via), single-via and
multi-via cross-layer, multi-terminal MST. Two live candidate directions:

1. **The U2 B.Cu escape corridor (characterised wall).** `TOUCH_RST_N`,
   `TOUCH_INT_N`, `AMP_SD_MODE`, `SD_CARD_DETECT_N` and other U2-edge control nets
   all fail because their via lands beside the D-306 `DISP_RST_N` via at U2's B.Cu
   escape. FBV2-P2-012 should measure whether a **deliberate escape-site offset**
   (route the via a few mm off U2's edge before the F↔B transition) or a
   short **B.Cu fan-out on U2's face** clears the 0.200 mm clearance to the
   `DISP_RST_N` barrel — the first increment that plans a via *site* rather than
   accepting the router's first legal one. This unlocks a whole coherent
   display/touch/SD/audio-strap family behind one wall.
2. **Another clean local no-via/single-via group** if (1) needs corridor
   analysis first — screen `w/screen_010.py` for short same-layer or one-via
   clusters (e.g. `RESERVED_SPARE` U23-local B.Cu 3-pad; `DIO2_TXEN` U8 intra-chip
   strap — verify it is a control strap, not RF matching).

**Still avoid** naive retry of `U11_PROG`/`PWR_SENSE` (hard walls) and the four
U2-escape candidates (now characterised) without the corridor plan;
RF/NFC/USB/crystals/community-header/rails/switching/class-D remain deferred. The
XGPIO0…9 bank is a real 10-net coherent target but a ~55 mm cross-board cross-layer
haul — screen its corridor before committing.

**PROGRESS EARNED (sixth rest-of-board increment promoted; cleanest class, no via; shared fingerprint helper landed; display/touch U2-escape wall characterised): PCB routing ~18 %→~18 %, overall ~76 %, readiness ~77 % (JLCPCB file unchanged — a small noncritical increment, not fab-readiness).**
