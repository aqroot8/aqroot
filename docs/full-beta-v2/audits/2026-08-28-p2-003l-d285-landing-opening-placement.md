# FBV2-P2-003L — D-285: the minimal landing-opening PLACEMENT ECO OPENS a legal southern BAT_PROTECTED_P landing — C36 rot 270 + south (own-GND blocker 0.0726 → 0.4750 mm) and the +3V3 decoupler C5 relocated west (the sole courtyard obstruction), clearing R68 by distance (0.0864 → 0.2941 mm); the proven D-275 south bridge now lays entry 4 / 1.40 mm F.Cu / exit 4 with ZERO east-landing DRC and NOTHING new added; PASS CANDIDATE for supervised Phase-A integration; no authoritative promotion; D-275 and D-277..D-283 preserved

**Date:** 2026-08-28 · **Task:** FBV2-P2-003L · **Starting HEAD:** `c413791`
**Owner decision this task ratifies:** **D-284** (Alpha, 2026-08-28) — agrees with the
CTO call and APPROVES the CTO-recommended placement fallback from D-283: open a legal
southern `BAT_PROTECTED_P` landing by a **bounded placement spread of the
C36/C25/U11/BQ25185_SYS neighbourhood** (landing-opening direction 1), not corridor
widening, not a broad refloorplan.
**Verdict:** **PASS CANDIDATE — the landing OPENS, measured and reproducible.** The
minimal placement ECO (`place_003l`, two footprints moved) opens the C36.1 landing so
the already-proven D-275 southern bridge lays end-to-end and legal; the DRC delta vs
the 003K board is EXACTLY the two landing clearance violations removed and NOTHING
added. This is a PASS candidate ready for the supervised Phase-A integration run; it is
**NOT an authoritative promotion** — full-board connectivity is proven only by the
supervised full run, which this bounded task does not start. No rule relaxed; the
0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED. D-275 + D-277..D-283
preserved. The authoritative PCB stays 0-track / 0-via and its placement is untouched
(C36/C5 at their home poses). **No routing % earned** — the blocker is resolved at
candidate level, awaiting the supervised gate.

---

## 1. The two blockers 003K measured, and why the fix is forced by geometry

003K (D-283) proved the disjoint southern LANE viable (≥ 1.20 mm, clears the taps) but
the only forced-south target-island pad, the far-east node cap **C36.1**, had NO legal
landing. Two INDEPENDENT clearance violations, exactly reproduced this task on the
sparse reconstructed board:

| # | violation | copper | fixed pad | actual |
|---|---|---|---|---|
| 1 | GND | B.Cu exit stub (SE via → landing) | **C36 pad 2 (own GND)**, 1.55 mm east of the landing pad | **0.0726 mm** |
| 2 | BAT_MAIN | F.Cu exit tie (centroid → NE via) | **R68 pad 1 (BQ25185_SYS)**, just north of the array | **0.0864 mm** |

- **Blocker 1 is invariant under any C36 TRANSLATION.** C36's GND pad sits 1.55 mm east
  of its BPP landing pad on the SAME footprint, so the whole {exit array + both pads}
  configuration translates rigidly — every mutual clearance is preserved. The ONLY lever
  is a C36 **rotation**. Rotating C36 to **270°** (vertical: BPP pad 1 NORTH, GND pad 2
  SOUTH) moves the GND pad 1.55 mm south of the north-poking exit array.
- **Blocker 2 is R68's fixed F.Cu pad** (R68 is `0R DNP` but KiCad-connected — the
  `BQ25185_SYS` net carries 16 pads). A vertical C36 is **3.05 mm tall**, so it cannot
  sit far enough south to clear R68 without colliding **C5**'s courtyard to the south.

## 2. The minimal ECO (`place_003l`, two footprints, nothing else)

| ref | from | to | displacement | why |
|---|---|---|---|---|
| **C36** (100 nF) | (63.750, 73.750, 0°) | **(63.750, 75.100, 270°)** | **1.35 mm S + rot** | rotation opens blocker 1; south shift clears blocker 2 by distance |
| **C5** (100 nF +3V3/GND) | (63.167, 75.649, 0°) | **(61.950, 75.150, 90°)** | **1.32 mm W + rot** | the SOLE courtyard obstruction to the vertical C36; a plane-net decoupler with routing latitude |

R68 is deliberately **NOT** moved: it carries a real 16-pad net and has no nearby legal
home, whereas the C36 south move clears it by distance. C5 was chosen over R68 because
its +3V3/GND decoupling role gives it routing latitude the 16-pad SYS net does not. Both
moves are STRICTLY NECESSARY and INSIDE the approved landing neighbourhood (C5 is 1.9 mm
from C36); they are recorded here, not taken silently (task discipline item 3).

## 3. The measurement (`bridge_probe_003l`, cheap, reproducible) — PASS

On the reconstructed sparse placed board (002F placement), after `place_003l.apply`
(courtyard/edge/rule-area audit passes) and the D-275 south bridge:

| clause | measurement | result |
|---|---|---|
| **A** LANE lays | land **C36.1**, traverse **1.40 mm** F.Cu, entry **4**, exit **4** | LAYS |
| **B** DISJOINT | western leg dips to **ywest = 82.40 mm** (> 74.7) | disjoint ✓ |
| **C** LANDING OPENS | **0** east-landing clearance violations; **C36.2 GND 0.4750 mm**, **R68.1 BAT_MAIN 0.2941 mm** | OPEN ✓ |
| **D** no new DRC item | clearance **4 → 2** (survivors = pre-existing WEST LTC issues), every other class identical | clean ✓ |
| **E** invariant / no promotion | D-275 constants reused; moves only C36/C5; no frozen part; authoritative 0/0, C36 at home | ✓ |

**Achieved landing clearances** (bridge copper → nearest GND/BAT_MAIN pad): R68.1
BAT_MAIN **0.2941** (was 0.0864), C5.2 GND **0.3003**, C36.2 GND **0.4750** (was
0.0726), R40.2 GND 0.975, C27.1 BAT_MAIN 1.164 — the **governing** clearance is
**0.2941 mm**, 47 % over the 0.200 mm floor. The bridge holds **1.40 mm** (≥ the
1.20 mm floor).

**DRC delta (ground truth, kicad-cli).** 003K board 228 violations → 003L board 226:
the only change is clearance 4 → 2. The two survivors are the pre-existing **western
LTC-block** issues (`R83`/`U18` GND 0.100 mm; `R80`/`U18` LTC_GATE 0.0088 mm) that are
independent of the landing and belong to the OTHER fallback direction (corridor
widening). `courtyards_overlap` stays **3** (the same western `U18`/`R80`/`R81`/`R83`
set — the C36/C5 moves add none), `silk_over_copper` 6, `solder_mask_bridge` 4,
`hole_clearance` 5, `shorting_items` 3, `lib_footprint_issues` 199, `via_dangling` 4 —
all unchanged. **No genuine DRC class or item is introduced, and none is absorbed.**

## 4. Why this is a CANDIDATE, not a promotion

The landing proof is on the reconstructed sparse board — a REAL board with REAL
kicad-cli DRC, not an analytical proxy — but it proves the LANDING, not the whole
board. Full-board connectivity with the moved C36/C5 and the early south bridge is a
property of the parent-supervised full route, which task discipline item 8 forbids
starting unsupervised. So the placement ECO is integrated **default-inert** and the
authoritative PCB is left untouched, exactly as every 003x task has: the ECO is a
proven candidate awaiting the supervised gate.

**Supervised follow-on (defined, NOT started):** the pinned D-271 recipe
(`AQROOT_SIXLAYER`, `AQROOT_D256=GSQ`, `AQROOT_Q3_POFV`, `AQROOT_D266`, `AQROOT_D267=F1`,
`AQROOT_TRUNK_LAST`, `AQROOT_U18_ORDER=6,10,7,1,3,2`, `AQROOT_D279=1`, `AQROOT_D280=1`)
plus `AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1` and
`AQROOT_ECO_EXTRA=hardware/beta-v2/checks/place_003l.json` (the existing 002J
override path merges the two moves into the 002F ECO and runs its collision audit — no
driver edit). The supervised run must (i) confirm the early south bridge lands legally
on the moved C36.1 at run scale, (ii) route the remaining nets around the reserved
bridge without reintroducing the 003I GND/BAT_MAIN/BAT_RAW corridor failures, and
(iii) close `BAT_PROTECTED_P` with no new DRC — only then does authoritative promotion
and a routing-% award apply.

## 5. Integration, suites, cleanliness, no false promotion

- **`place_003l.py`** — NEW. The two-move ECO with its own courtyard/edge/rule-area
  collision audit (mirroring `place_p2_002f`) and a FROZEN guard covering
  D9/U18/R75–R83/Q3/FETs/C58/U19/D10/**R68**. Applied on top of 002F.
- **`place_003l.json`** — NEW. The `AQROOT_ECO_EXTRA` file the supervised run consumes.
- **`bridge_probe_003l.py`** — NEW, the standing PASS record (A lane / B disjoint /
  C landing opens + named blockers clear / D no new DRC item / E invariant + no
  promotion). PASS.
- `bridge_probe_003k` (D-283), `bridge_probe_003i` (D-281), `bridge_probe_003j`
  (D-282) — intact, default south path unchanged. PASS.
- `bridge_probe_003c` (D-275 held fixed), `bridge_probe_003d` — PASS.
- `router_regression` G1–G11, `u19_escape_probe_003e/003f/003g/003h`
  (D-277/278/279/280) — PASS.

No existing code was modified — the three new files are additive, so every default path
is byte-identical and all prior suites pass unchanged.

**Authoritative PCB untouched:** `pcbnew` load reads **0 signal tracks, 0 signal vias**,
and C36 is at its home pose (63.75, 73.75, 0°). No KiCad source mutated, no authoritative
placement change, no rule relaxed; `phaseA_journal.json` untouched (the driver was never
invoked — the probe uses `apply_early_path` on a scratch board). Scratch `PROBE003L` is
gitignored. **Nothing frozen moved and nothing relaxed:** D9, U18, R75–R83, Q3, shunt,
FETs, C58, U19, D10, R84–R96/Q5–Q9, U11, **R68** frozen; only C36 and C5 moved, and only
inside the approved landing neighbourhood; `c3_00` NOT promoted; D-249..D-283 (incl.
**D-275/D-277..D-283**) untouched; no safety weakening; no topology/net/footprint/
polarity/value change; no six-layer/GND change; no netclass/width/clearance/hole-to-hole
relaxation; no authoritative promotion. Phase A NOT completed; Phase B NOT run. The
optional `BAT_SENSE TP20.1` (TEST) point is treated separately and is not a gate.
`JLCPCB_READINESS` not touched by this task.

## 6. The next task — FBV2-P2-003M (supervised Phase-A integration)

The route-scope candidates were exhausted at 003K; 003L delivers the OWNER-approved
placement fallback and PROVES it opens the landing. The one remaining step to close
`BAT_PROTECTED_P` and earn routing % is the **parent-supervised full Phase-A run** with
the 003L placement + the early south bridge (recipe in §4). Hold D-275/D-277..D-285
fixed; no netclass/width/clearance/hole-to-hole relaxation; authoritative promotion and
a routing-% award only if the full Phase-A gate passes with no new DRC and full
connectivity. If the supervised run reintroduces a corridor-capacity failure, the
fallback escalates to landing-opening direction 2 (corridor widening) — an OWNER call.
