# FBV2-P2-003K — D-283: the DISJOINT-SUB-BOX southern BAT_PROTECTED_P bridge (candidate c) LAYS its lane but has NO LEGAL LANDING — the only forced-south target-island pad (the far-east node cap C36.1) is boxed by GND and BAT_MAIN, so the exit array lands 0.0726 mm from GND and 0.0864 mm from BAT_MAIN; the ungated early bridge then poisons every subsequent gate and the full run cascades (140 rejections across 26 nets); candidate (c) is EXHAUSTED and the remaining lever is the OWNER/mechanical placement-spread fallback; no authoritative promotion; D-275 and D-277..D-282 preserved

**Date:** 2026-08-28 · **Task:** FBV2-P2-003K · **Starting HEAD:** `453ab4e`
**Verdict:** **MEASURED FAIL — candidate (c) EXHAUSTED.** The env-gated
(`AQROOT_BRIDGE_SOUTH`, default inert) disjoint-sub-box southern bridge reserves the
exact D-275 mechanism in the sparse southern band and forces the western leg below
the tap band (`south_ywest = 81.85 mm`, well south of the taps at y < 74.7) — the
**disjoint LANE half of candidate (c) is confirmed viable, at ≥ 1.20 mm**. But the
only target-island BPP pad reachable when the leg is forced south is the far-east
node cap **C36.1** (no target-island pad exists between D9.1 at x = 11 and C25/C36 at
x = 62, and the OPEN node copper that D-275 landed on does not exist early), and its
neighbourhood cannot clear a ≥ 0.200 mm exit array: the bridge exit copper lands
**0.0726 mm** from C36's own GND pad and **0.0864 mm** from R6/R68's BAT_MAIN
(`BQ25185_SYS`) pad — the exact 003I clearance class (identical GND 0.0726 mm).
Because the early stage lays the bridge UNGATED, that fixed violation pair is then
read as `new DRC {clearance:2}` by every subsequent per-connection gate and rejects
it: **140 gate rejections across 26 nets** on the parent-supervised full run. The run
is INVALID as a Phase-A candidate; the two clearance violations are GENUINE and are
NOT absorbed. With (b) refuted (D-282), (d) the 003I FAIL (D-281) and (a) an
envelope/OWNER change, the remaining lever is the FALLBACK — a placement spread of
the LTC4368 block (OWNER/mechanical) — **NOT attempted here**. No rule relaxed; the
0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED. The authoritative
PCB stays 0-track / 0-via; D-275 + D-277..D-282 are preserved. **NO routing progress
earned.**

---

## 1. What 003K implements (the minimal env-gated candidate c)

003J (D-282) measured that the shared western corridor (y 65–75) cannot host both the
≥ 1.20 mm bridge and the `LTC_GATE`/`BAT_RAW` taps by any via-relocation, and
localised the one spare ≥ 1.20 mm F.Cu lane to a SOUTHERN band **disjoint** from the
tap cluster (taps y < 74.7; the spare copper-only detour uses y > 75). 003K
implements the minimal env-gated candidate that reserves the bridge in that band:

- **`AQROOT_BRIDGE_SOUTH`** (`route_battery_block.py`, default inert; implies the
  `AQROOT_BRIDGE_EARLY` 003I stage so the bridge is still laid exactly once, at the
  stage-8 boundary). No effect unless set.
- **`bridge_early_003i.apply_early(..., south=True)`** — the SAME proven D-275
  mechanism (cardinality-1 `BAT_PROT_SHDN_CTL` vacate, 4× R75.2 entry array,
  ≥ 1.20 mm F.Cu traverse rule, 4× exit array, ≥ 3 fault-tolerant floor,
  single-sourced VERBATIM from `bridge_route_003c`) with two south-only additions:
  1. a TEMPORARY net-foreign obstacle wall over the corridor-north box
     (x 4.6–30 mm, y 55–74.7 mm) that forces the western leg BELOW the tap band —
     removed with the injected via phantoms, so it shapes ONLY the bridge's own
     search and never obstructs a real net (the disjoint-sub-box discipline);
  2. `LAND_REFS_SOUTH = [C36.1, U11.2, C25.1]` — the far-east node caps, because the
     forced-south leg cannot return to the corridor pads.

The bridge copper (net `BAT_PROTECTED_P`) then stands as an obstacle every later net
routes around — the reservation that forces the western LTC block into the
complement (D-266/D-267 early-reservation discipline reused).

## 2. The measurement (`bridge_probe_003k.py`, cheap, reproducible)

On the reconstructed sparse placed board (fresh scratch, `reconstruct_placed` = the
c3_00 placement, six-layer, no routed nets — the sparsest corridor state):

| clause | measurement | result |
|---|---|---|
| **A** LANE holds | entry 4, traverse **1.20 mm**, exit 3, land **C36.1** | LAYS |
| **B** DISJOINT | western leg dips to **ywest = 81.85 mm** (> 74.7) | disjoint ✓ |
| **C** NO LANDING | C36.1 exit copper vs **GND 0.0726 mm**, **BAT_MAIN 0.0864 mm** | **FAIL** |

Clause C reproduces on the sparse board because the offending neighbours are fixed
PADS, present from board load: C36's GND pad 2 at (64.525, 73.750) and R6/R68's
BAT_MAIN pad at (63.459, 71.606). The 1.20 mm exit copper at the traverse endpoint
(62.975, 72.850) and the exit-via B.Cu stub (63.425, 73.300) simply have no 0.200 mm
room there.

## 3. The full run — the FAIL, measured (parent-supervised)

Recipe = the pinned D-271 production recipe (`AQROOT_SIXLAYER`, c3_00 placement
[fingerprint `R75@2.800,65.000/-90 U18@4.000,72.900/90 …`, identical to the 003H
reference], `AQROOT_D256=GSQ`, `AQROOT_Q3_POFV`, `AQROOT_D266`, `AQROOT_D267=F1`,
`AQROOT_TRUNK_LAST`, `AQROOT_U18_ORDER=6,10,7,1,3,2`, `AQROOT_D279=1`,
`AQROOT_D280=1`) **plus `AQROOT_BRIDGE_EARLY=1` and `AQROOT_BRIDGE_SOUTH=1`**;
scratch `FIX003K`.

The early stage laid the south bridge at the stage-8 boundary —
`EARLY BRIDGE SOUTH OK land=C36.1 traverse=70.377mm w=1.20 entry=4 exit=3
ywest=81.85` — and then the ungated landing violation (GND 0.0726 mm / BAT_MAIN
0.0864 mm) was seen as `new DRC {"clearance": 2}` by EVERY subsequent per-connection
gate, which correctly REJECTED it rather than absorbing it. The result: **140 gate
rejections carrying the identical fixed pair, across 26 distinct nets**
(`BAT_RAW`, `LTC_GATE`, `LTC_GATE_RC`, `REF_POL`, `N_BATDIV`, `REC_*`, …). The
parent stopped the run once the cascade was decisive — exactly as the 003I parent
stopped its run — so no `phaseA_003k_fix.json` was written and no partial board
masquerades as a result. The two clearance violations are GENUINE safety-clearance
violations and are NOT refreshed into any baseline (the 003I ruling).

**Why every gate rejects.** `gate()` fails a connection when the board's DRC gains a
class vs the pre-route baseline. The early bridge is laid UNGATED, so its fixed
`clearance:2` pair is present on the board for the whole remainder of the route;
every later gate therefore sees `+2 clearance` and rejects its connection — the
landing violation poisons the entire gate model. This is a property of the ungated
early stage meeting an illegal landing; it is not a per-connection local clash (the
identical 0.0726/0.0864 figures across geographically distant nets confirm one fixed
source).

## 4. Conclusion — candidate (c) is exhausted at the LANDING, not the lane

003J's disjoint-band hypothesis had two halves. 003K measures both:

- **The disjoint LANE is viable** — the western leg holds ≥ 1.20 mm below the tap
  band (ywest 81.85), so the taps + GND/BAT_MAIN keep the corridor. This is the part
  003J could not prove on the already-dense board (there the lane capped at ≤ 1.30 mm);
  the sparse-window reservation does open it.
- **The LANDING is not viable** — the only target-island pad the forced-south leg can
  reach, the far-east node cap C36.1, is boxed by GND and BAT_MAIN and cannot host a
  legal ≥ 0.200 mm exit array. D-275's own bridge avoided this by landing on OPEN node
  COPPER at (40.67, 70.71); that copper does not exist at the early reservation point,
  so the early bridge is forced onto a congested PAD.

So the smallest sufficient change is NOT a route-scope reservation. With candidate
(b) refuted (D-282), (d) the 003I FAIL (D-281), and (a) an envelope change (OWNER),
the only remaining lever is the **fallback: a placement spread of the LTC4368 block
that either (i) opens an OPEN landing region for the forced-south bridge, or (ii)
widens the western corridor so the D-275 corridor bridge and the taps both fit** —
an OWNER/mechanical decision, per the 003J ruling. **NOT attempted here.**

## 5. Suites, cleanliness, no false promotion

- `bridge_probe_003k` — NEW, the standing measured-FAIL record. A (lane lays),
  B (disjoint, ywest 81.85), C (decisive: C36.1 landing violates GND + BAT_MAIN),
  D (D-275 invariant reused; vacate cardinality-1; current-carrying nets refused),
  E (no false promotion; authoritative 0/0). PASS.
- `bridge_probe_003i` (D-281), `bridge_probe_003j` (D-282) — intact. PASS.
- `bridge_probe_003c` (D-275 held fixed), `bridge_probe_003d` — PASS.
- `router_regression` G1–G11 (D-280 off) — PASS.
- `u19_escape_probe_003e/003f/003g/003h` (D-277/278/279/280) — PASS.

The south variant is default-inert: with `AQROOT_BRIDGE_SOUTH` unset, `apply_early`'s
`south=False` path is byte-for-byte the 003I corridor stage (same land_refs, no wall),
so all of the above pass unchanged.

**Authoritative PCB untouched:** `pcbnew` load of the product board reads **0 signal
tracks, 0 signal vias**. No KiCad source mutated, no placement ECO, no rule relaxed;
`phaseA_journal.json` restored to HEAD (the driver rewrote it during the run); scratch
`FIX003K` is gitignored. **Nothing moved and nothing relaxed:** D9, U18, R75–R83, Q3,
shunt, FETs, C58, C36, U11, U19, D10 and the whole R84–R96/Q5–Q9 field frozen;
`c3_00` NOT promoted; D-249..D-282 (incl. **D-275/D-277..D-282**) untouched; the proven
003C bridge geometry held fixed; no safety weakening; no topology/net/footprint/
polarity change; no six-layer/GND change; no netclass/width/clearance/hole-to-hole
relaxation; no authoritative promotion. Phase A NOT completed (the D-275 BPP bridge is
still not integrated); Phase B NOT run. The optional `BAT_SENSE TP20.1` (TEST) point
is treated separately and is not a gate. No OWNER decision made — 003K exhausts the
route-scope candidate; the OWNER/mechanical fallback is defined, not taken.

## 6. The next task — FBV2-P2-003L (OWNER/mechanical, defined)

The route-scope candidates for closing `BAT_PROTECTED_P` on the full board are now
exhausted: (b) tap relocation (D-282, refuted), (d) early corridor bridge (D-281,
FAIL), (c) disjoint southern sub-box (D-283, FAIL — no legal landing). **The one
remaining lever is a placement spread of the LTC4368 block — an OWNER/mechanical
decision.** Two concrete sub-directions for the OWNER to weigh:

1. **Open the landing.** Spread C36/C25/U11 (and/or the BQ25185 SYS pad neighbourhood)
   so the forced-south bridge has a ≥ 0.200 mm-clear landing region — the disjoint
   LANE already holds ≥ 1.20 mm; only the landing is blocked.
2. **Widen the corridor.** Spread the LTC4368 block eastward so the D-275 corridor
   bridge and the `LTC_GATE`/`BAT_RAW` taps + GND/BAT_MAIN both fit the western
   corridor (the D-281 capacity wall).

Either changes placement/topology and is outside route scope; it requires an OWNER
decision and, if it grows the outline, an envelope review. No long full run without
CTO supervision; hold D-275/D-277..D-283 fixed; no netclass/width/clearance/
hole-to-hole relaxation; no authoritative promotion unless the full Phase-A gate
passes.
