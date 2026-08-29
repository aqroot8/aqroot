# FBV2-P2-003M — D-286: the DRC/ratsnest baseline was measured BEFORE the candidate placement (latent since 002L), so the c3_00 placement's own items poisoned every gate; the harness now measures the baseline on the ACTUAL complete pre-copper placement, and with that correction the definitive full run SURFACES that candidate c3_00 is electrically invalid — U18 (LTC4368) collides with R83 and R80, three genuine different-net pad shorts and two sub-0.200 mm clearances with ZERO copper, and the LTC sense pins are un-escapable; harness fix + G12 regression COMMITTED, c3_00 recipe MEASURED FAIL, no authoritative promotion, D-275 and D-277..D-285 preserved

**Date:** 2026-08-29 · **Task:** FBV2-P2-003M · **Starting HEAD:** `77e0cb0`
**Verdict:** **HARNESS CORRECTION PASS + c3_00 RECIPE MEASURED FAIL.** Two distinct
results, neither of which promotes any copper or placement:

1. **The harness correction is a real, verified fix (D-286).** `route_battery_block.py`
   computed the DRC/ratsnest gate baseline right after the 002F ECO
   (+`AQROOT_ECO_EXTRA`) but **before** `AQROOT_PLACE_JSON` moved the candidate
   footprints, so a candidate placement's own placement-derived DRC was never in the
   comparison baseline. Every routing gate then read those placement items as brand-new
   copper violations and rejected unrelated nets. Latent since 002L; the 003M placement
   combination made it decisive (the first parent-supervised 003M attempt: **43
   `GATE_REJECTED`, `DRIVER_EXIT=143`**, the persistent CTO stopping a proven-poisoned
   cascade). The baseline is now measured on the ACTUAL complete pre-copper placement
   (002F ECO + `AQROOT_ECO_EXTRA` + `AQROOT_PLACE_JSON`, connectivity rebuilt, zones
   filled, saved, DRU written, fingerprint asserted) — before any QBoard copper. New
   regression **G12** reproduces the defect, pins the corrected order, and proves a
   post-baseline (copper) violation is still surfaced. All preflight PASS.

2. **With the corrected harness the definitive full run reveals the truth the old order
   was HIDING: candidate placement `c3_00` is electrically invalid.** c3_00 moves
   **U18 (the LTC4368 protection IC)** to (4.0, 72.9, 90°), driving its pad field on top
   of **R83** and **R80** (which c3_00 does not move). On the zero-copper placement,
   kicad-cli DRC reports **three genuine different-net pad shorts** and **two sub-0.200 mm
   clearances**, and the router independently finds the LTC sense pins un-escapable. This
   is a genuine placement fault, **not** a harness artifact — it must be **surfaced, not
   baselined away** (binding constraint). The c3_00 recipe is therefore a MEASURED FAIL.

**No authoritative promotion. No copper. No placement promoted.** The authoritative PCB
stays six copper layers, **0 signal tracks, 0 signal vias**, placement untouched. The
0.200 mm clearance and 0.25 mm hole-to-hole floors are ENFORCED, not relaxed — the FAIL
is precisely a refusal to accept a placement that breaches them. D-275 and D-277..D-285
are preserved. `place_003l` (D-285) is fully vindicated (see §4). **No routing % earned.**

---

## 1. The defect, exactly

`route_battery_block.py` (pre-003M) sequenced the scratch build as:

```
apply 002F ECO (+AQROOT_ECO_EXTRA)      # C36/C5 landing ECO
save + DRU.write
base = drc(pcb) ; base_rn = ratsnest(pcb)     # <-- BASELINE TAKEN HERE
apply AQROOT_PLACE_JSON (candidate placement) # c3_00: moves U18/R75/R79
  BuildConnectivity ; ZONE_FILLER.Fill ; save
fingerprint / assert
QBoard routing  (gates: after - base, excluding unconnected_items)
```

The baseline was captured one step too early. Every gate delta `after - base` therefore
carried the candidate placement's **own** DRC as if the router had just laid it. In the
003M log this shows as a FIXED offset repeated verbatim across unrelated nets, before
and after the bridge:

```
Q2_CS   Q2.1->Q2.3   GATE_REJECTED  new DRC {"solder_mask_bridge":3,"courtyards_overlap":3,"shorting_items":3,...}
Q3_CS   Q3.3->Q3.1   GATE_REJECTED  new DRC {"solder_mask_bridge":3,"courtyards_overlap":3,"clearance":...}
BAT_SENSE  ...        GATE_REJECTED  new DRC {"solder_mask_bridge":3,"courtyards_overlap":3,"shorting_items":3,...}
BAT_RAW  R77.1->R79.1 GATE_REJECTED  new DRC {"solder_mask_bridge":3,"courtyards_overlap":3,"shorting_i...
```

The **early south bridge itself PASSED** at full-run scale in that attempt —
`EARLY BRIDGE SOUTH OK land=C36.1 traverse=72.786mm w=1.40 entry=4 exit=4 ywest=82.40` —
which is why the defect was in the gate baseline, not the bridge. 43 `GATE_REJECTED`
events, `DRIVER_EXIT=143` (SIGTERM — the persistent CTO stopping the cascade). No design
FAIL could be claimed from that invalidated run.

### The fix

The baseline is relocated to AFTER the full candidate placement is applied,
connectivity is rebuilt, zones are filled, the board is saved, the DRU is written and
the placement fingerprint is asserted — but BEFORE any QBoard copper:

```
apply 002F ECO (+AQROOT_ECO_EXTRA)
save + DRU.write
apply AQROOT_PLACE_JSON  (BuildConnectivity ; ZONE_FILLER.Fill ; save)
fingerprint / assert
base = drc(pcb) ; base_rn = ratsnest(pcb)     # <-- BASELINE NOW HERE
QBoard routing
```

Default behaviour is preserved: when no `AQROOT_PLACE_JSON` is supplied the on-disk
board at the new baseline point is byte-identical to the board at the old point (the
placement block is skipped and the fingerprint block only reads), so every default path
result is unchanged. `DRU.write` writes a separate `.kicad_dru` sidecar, so the
placement `Save` does not clobber it and the DRC still runs against the real rules.

---

## 2. Do NOT blindly absorb — measure and attribute the post-placement, pre-copper items

The corrected baseline on the 003M candidate is:

```
{'clearance':2, 'courtyards_overlap':3, 'hole_clearance':5, 'lib_footprint_issues':199,
 'shorting_items':3, 'silk_over_copper':6, 'solder_mask_bridge':4, 'unconnected_items':499}
```

Rather than accept that as a baseline, each item was measured on independent throwaway
zero-copper boards (`w/baseline_003m_audit.py`, `w/attrib_003m.py`) and attributed:

| placement | histogram (non-cosmetic classes) | verdict |
|---|---|---|
| AUTHORITATIVE (home) | `hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1` | governed baseline (long accepted) |
| 002F ECO only | identical to authoritative | clean |
| **`place_003l` only (D-285)** | **identical to authoritative** | **CLEAN — introduces nothing** |
| **`c3_00` only** | **+clearance:2, +courtyards_overlap:3, +shorting_items:3, +silk_over_copper:6, solder_mask_bridge 1→4** | **c3_00 is the SOLE cause** |
| `c3_00` + `place_003l` | same as c3_00 only | c3_00 dominates |

`hole_clearance:5` and `lib_footprint_issues:199` are the pre-existing authoritative
placement/library items, governed since the pre-placement audit. `place_003l` adds
nothing. **Everything else is c3_00.**

---

## 3. What c3_00 actually does — three genuine different-net pad shorts

c3_00 (`002Z-c3_e10n_r79`, prefilter rank 1) moves three parts: **U18 → (4.0, 72.9, 90°)**,
R75 → (2.8, 65, 270°), R79 → (9.825, 67.825, 0°). It does NOT move R83 or R80. At U18's
new pose its pad field lands on top of R83 and R80:

| DRC item | nets | colliding pads (measured) |
|---|---|---|
| shorting_items | `BAT_PROT_SHDN_CTL` ↔ `LTC_OV` | **R83.1** on **U18.3** @ (4.0, 75.0) |
| shorting_items | `BAT_PROT_SHDN_CTL` ↔ `LTC_UV` | **R83.1** on **U18.2** @ (4.5, 75.0) |
| shorting_items | `BAT_RAW` ↔ `LTC_GATE` | **R80.1** on **U18.10** @ (5.0, 70.8) |
| clearance (GND 0.200→**0.100 mm**) | `GND` | U18.4 (GND) / R83.1 cluster @ (3.5, 75.0) |
| clearance (Default 0.200→**0.0088 mm**) | `LTC_SHDN` / `LTC_GATE` | R80.2 / U18.10 cluster @ (5.0, 70.8) |

These are hard **pad-on-pad different-net shorts with ZERO routed copper** — no router
action can remove them, because they are inherent to the footprint positions. The
router's own escape analysis in the definitive full run names the identical culprits:

```
U18.10 LTC_GATE  NO_LEGAL_ESCAPE  blocked by R80.1 (x71)
U18.3  LTC_OV    NO_LEGAL_ESCAPE  blocked by R83.1 (x68)
U18.2  LTC_UV    NO_LEGAL_ESCAPE  blocked by R83.1 (x71)
```

Two fully independent instruments — kicad-cli DRC on the bare placement and the router's
geometric escape solver — agree on the exact colliding pads. c3_00 is electrically
invalid.

The c3 prefilter graded these candidates "mech-clean," but its screen was analytic and
never ran a real full-placement DRC — the same class of gap the D-286 harness fix
closes. Re-screening candidates with the corrected post-placement baseline DRC is the
right next step.

---

## 3a. The definitive full run with the corrected harness — DRIVER_EXIT=0, PHASE A FAIL

With the D-286 fix, the exact D-285 recipe (`w/run_003m.sh`: SIXLAYER + D256 GSQ +
Q3_POFV + D266/D267/TRUNK_LAST + U18_ORDER + D279 + D280 + `BRIDGE_EARLY` +
`BRIDGE_SOUTH` + `ECO_EXTRA=place_003l.json` + `PLACE_JSON=c3_00.json`) was run
synchronously to natural completion — **`DRIVER_EXIT=0`, not a SIGTERM** — because the
gate poison is gone. Measured end-state:

- **PHASE A: FAIL** — `BAT_PROT_SHDN_CTL R83.1 -> (node) : NO_NODE` (no legal copper node;
  R83.1 is shorted onto U18). connections **64**, skipped-already-connected **89**,
  ratsnest **713 (−68)**.
- **Early south bridge PASSED at full width** — `land C36.1`, traverse **72.994 mm @
  w = 1.50 mm**, entry **4** / exit **4**, disjoint south (`ywest 82.4 mm`), landing
  `(63.75, 74.325)`, `bridge_eco null`. So the D-275 bridge + `place_003l` landing is
  itself sound; the run does not fail on the bridge.
- **Gate discipline held.** The ONLY class increased vs the (corrected) baseline is
  `track_width +1` — a single `BAT_PROTECTED_P` bounded-stub segment at 0.2 mm vs the
  D-249 1.2 mm trunk rule, a genuine copper item on an already-failed scratch board,
  correctly SURFACED (not absorbed). No placement class ever appeared as a spurious gate
  delta — `shorting_items:3` and `clearance:2` sit identically in baseline AND final,
  proving they are placement-state, not route-introduced, and were neither poisoning
  gates nor being hidden. A fresh kicad-cli DRC on the routed board confirms the same
  histogram.
- **Every terminal casualty is a c3_00 collision.** `LTC_GATE U18.10` (blocked by R80.1),
  `LTC_OV U18.3` and `LTC_UV U18.2/R79.2` (blocked by R83.1), `BAT_PROT_SHDN_CTL
  Q4.1/R83.1` (NO_NODE), `BAT_SENSE U18.9` / `LTC4368_FAULT_N U18.7` (NO_VIA_SITE) — the
  entire LTC4368 control cluster, unroutable because U18 sits on R83/R80.

Two independent gates — the router's connectivity result and the placement DRC audit —
agree: the c3_00 placement is invalid. The result JSON (`phaseA_003m_fix.json`, scratch)
is NOT promoted; following the 003K precedent no failed-candidate result is committed.

---

## 4. `place_003l` (D-285) is preserved and vindicated

Measured alone on the six-layer zero-copper board, `place_003l` reproduces the
authoritative baseline exactly — it adds no clearance, no short, no courtyard overlap.
D-285's landing-opening ECO is clean; the 003M FAIL is entirely c3_00's placement of the
LTC4368 block, a different concern from the C36.1 landing D-285 solved.

---

## 5. Regression G12 (router_regression) — fails the old order, pins the new one

`router_regression.py` gains **G12** (all of G1–G11 unchanged and still PASS). On a real
scratch board it induces a placement-derived DRC delta (stack C5 on C36), then:

- **G12 candidate placement induces a placement-derived DRC delta** — `{solder_mask_bridge:1, courtyards_overlap:1, shorting_items:1, silk_overlap:2}` (the same class family as 003M), so which baseline is used matters.
- **G12 OLD pre-placement order FALSELY flags the placement (the bug)** — old-order delta == the induced items.
- **G12 NEW post-placement order yields ZERO spurious delta** — the gate is now relative to the actual routed starting geometry.
- **G12 a post-baseline copper violation is STILL surfaced** — a synthetic `+clearance` after the baseline boundary is detected; nothing is hidden.
- **G12 driver source order** — asserts `base = RU.drc(pcb, "Abase"...)` is textually AFTER the `AQROOT_PLACE_JSON` apply and the fingerprint assertion and BEFORE `QBoard`; the pre-placement ordering fails this the moment it returns.

---

## 6. Preflight (all PASS, after the correction)

`router_regression` G1–G12 · `bridge_probe_003c` · `bridge_probe_003d` ·
`bridge_probe_003i` · `bridge_probe_003j` · `bridge_probe_003k` · `bridge_probe_003l` ·
`u19_escape_probe_003e` · `u19_escape_probe_003f` · `u19_escape_probe_003g` ·
`u19_escape_probe_003h`.

---

## 7. Integrity

- Authoritative PCB UNCHANGED: six copper layers, **0 signal tracks, 0 signal vias**,
  placement untouched (C36/C5/U18/R75/R79/R80/R83 all at home poses on the authoritative
  board; c3_00 and place_003l live only in scratch/override files).
- `phaseA_journal.json` restored to its committed state after the (FAIL) run.
- Only source change: the baseline relocation in `route_battery_block.py` and the
  additive G12 in `router_regression.py`. No netclass / width / topology / net /
  footprint / value / polarity / six-layer / GND / safety change. No DRC absorbed — a
  genuine placement short is surfaced as the FAIL reason, not hidden.
- `c3_00` NOT promoted. Optional `BAT_SENSE TP20.1` remains separate. Frozen
  `beta-full-reference-v1` untouched.
- `JLCPCB_READINESS` unchanged: no committed change to authoritative fabrication
  readiness (a harness-correctness fix + a measured candidate rejection do not move the
  board closer to fab). Repo progress unchanged.

---

## 8. Next task — FBV2-P2-003N (CTO scope, not an owner decision)

Route-scope western-corridor fixes are exhausted (003I/J/K). The bounded landing ECO
(`place_003l`, D-284 direction 1) is proven clean but only opens the C36.1 landing; it
does not place the LTC4368 block. The designated candidate placement `c3_00` is now
measured invalid. Other cardinality-3 / cardinality-1 candidates exist
(`c3_01/02/03`, `cand_00..11`, the c2 family) and have NOT been screened with a real
full-placement DRC. **003N: re-screen the LTC-block placement candidates with the
corrected D-286 post-placement baseline DRC (reject any with a bare-placement short or an
un-escapable LTC sense pin), and integrate the first genuinely short-free, routable
candidate with `place_003l` + the proven south bridge on a parent-supervised full run.**
This stays inside CTO authority (bounded placement/routing experiments). Only if that
re-screen proves the entire bounded direction-1 candidate space cannot yield a
short-free, routable LTC-block placement — leaving a broad LTC4368 refloorplan /
corridor-widening (direction 2) as the SOLE remaining option — does it escalate to a
genuine OWNER DECISION.
