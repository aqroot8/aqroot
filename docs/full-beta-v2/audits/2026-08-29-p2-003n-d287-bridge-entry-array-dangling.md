# FBV2-P2-003N — D-287: the full bounded direction-1 placement screen is EXHAUSTED (27/27), only three candidates pass the D-286 zero-copper hard gates, and a cheap CTO-authorized bridge-connectivity probe REFUTES all three at the SAME genuine electrical fault — the D-275 south-bridge ENTRY array (R75.2 POFV) is bussed on F.Cu with NO symmetric B.Cu tie-stub, so its vias dangle on one layer regardless of placement; this is a BRIDGE-IMPLEMENTATION defect independent of placement (a narrower CTO lever), NOT a placement wall, so direction-2 is NOT yet the sole remaining option and this is NOT an OWNER decision

**Date:** 2026-08-29 · **Task:** FBV2-P2-003N · **Starting HEAD:** `64a0c67`
**Verdict:** **DIRECTION-1 CANDIDATE SPACE EXHAUSTED (27/27 fail) + THE THREE HARD-GATE
SURVIVORS FAIL BRIDGE INTEGRATION ON A PLACEMENT-INDEPENDENT ENTRY-ARRAY DANGLING-VIA
DEFECT — CTO ENGINEERING FAIL, NO OWNER DECISION, NO PROMOTION.**

No copper and no placement are promoted. The authoritative PCB stays **six copper
layers, 0 signal tracks, 0 signal vias**, placement untouched. Every rule floor
(0.200 mm clearance, 0.25 mm hole-to-hole, ≥1.20 mm BPP trunk) is ENFORCED, not
relaxed — the FAIL is precisely a refusal to accept dangling vias as connectivity.
D-275 and D-277..D-286 are preserved. **No routing % earned** (PCB routing stays 0 %,
overall 74 %, JLCPCB readiness ~77 %).

---

## 1. What 003N was asked to do

D-286 corrected the gate baseline and MEASURED the designated candidate `c3_00` invalid.
003N (CTO scope) was to re-screen the **complete bounded direction-1 LTC-block placement
candidate space** with the corrected **D-286 post-placement baseline DRC** — rejecting
any candidate whose bare placement shorts different nets, breaches a clearance/hole
floor, overlaps a courtyard, or boxes an LTC sense pin — then take the first genuinely
short-free, routable survivor into a `place_003l` + proven-south-bridge full Phase-A run.

## 2. The instrument — `checks/screen_003n.py` (deliverable)

For every candidate the screen builds a **REAL scratch board at the exact D-286
pre-copper boundary** (002F ECO + `AQROOT_ECO_EXTRA = place_003l` + the candidate moves
→ BuildConnectivity → zone fill → save) and runs the **real** `kicad-cli pcb drc
--severity-all` plus the **real** QBoard pad-escape solver (`qb.escape`, the same one the
router uses). A candidate is REJECTED if, versus the `place_003l`-only CLEAN reference,
it introduces a different-net pad short, a sub-0.200 mm clearance, a net-agnostic hole
breach, a courtyard overlap, or leaves any required U18 pin un-escapable. This is the
instrument D-286 mandates: real full-placement DRC, NOT the analytic "mech-clean"
prefilter that once graded the invalid `c3_00` as rank-1.

`screen_003n.py --validate` is the screen regression: it asserts `c3_00` is REJECT with
≥1 new `shorting_items` and that the `place_003l` reference is CLEAN. **PASS** (this run:
`c3_00` REJECT `shorting_items +3`; reference clean).

## 3. The 27-candidate screen result (Stage-1 hard gates)

The complete bounded direction-1 space is 27 candidates: `b1` family (6, single R75/Q3/
U18 rotations off the AUTHORITATIVE home), `c3` family (4, card-3 U18+R79+R75),
`cand_00..11` (12, card-2 U18+R81), `c2` family (5, card-2 east/west spreads).

**Only three candidates pass every zero-copper hard gate AND every required U18 escape:**

| candidate | move | verdict | why |
|---|---|---|---|
| **b1_r75rot**  | R75→(2.8, 65.0, 270°, B.Cu) | **PASS** | clean, all U18 escape |
| **b1_r75rotN** | R75→(2.8, 64.5, 270°, B.Cu) | **PASS** | clean, all U18 escape |
| **b1_q3rot**   | Q3→(3.8, 56.8, 270°, B.Cu)  | **PASS** | clean, all U18 escape |
| b1_r75rotE2 / b1_r75rotNE | R75 rot+east | REJECT | `courtyards_overlap +1` |
| b1_u18ctrl | U18 ctrl-rot | REJECT | shorts +4, clr +1, courtyard +3, U18.2/3 unescapable |
| c3_00..03 | U18+R79+R75 | REJECT | shorts 2–6, clr 1–2, courtyard 3, LTC pins unescapable |
| cand_00..11 | U18+R81 | REJECT | shorts/clr/courtyard and/or U18.1/2 unescapable |
| c2_e10n/e10/e05/w05/E2r | east/west spread | REJECT | shorts 2–7, clr 1–2, courtyard 3, LTC pins unescapable |

24 candidates are REJECTED at the bare placement; three survive. Full table in
`checks/w/screen_003n/results.json`.

## 4. The three survivors ALL fail bridge integration — same genuine fault

### 4.1 b1_r75rot (parent-supervised full run — prior 003N evidence)

The primary survivor was taken into a full parent-supervised Phase-A run
(`AQROOT_BRIDGE_EARLY=1 AQROOT_BRIDGE_SOUTH=1`, `place_003l`, `AQROOT_PLACE_JSON=
b1_r75rot.json`). The early southern bridge reported a **geometric** success:

```
EARLY BRIDGE SOUTH OK land=C36.1 traverse=72.786mm w=1.40 entry=4 exit=4 ywest=82.40
```

— a full-width, disjoint (ywest 82.40 > 75) lane laid to a legal C36.1 landing. But
**immediately after**, every subsequent routing gate rejected on an identical brand-new
DRC class: `via_dangling +4` ("Via is not connected or connected on only one layer") —
20 unrelated post-bridge gates (LTC_GATE, LTC_GATE_RC, BAT_RAW …) each rejected for the
same four dangling vias, the ladder walked all the way down with no recovery, and the
persistent CTO stopped the proven-poisoned cascade (`DRIVER_EXIT=143`). The bridge left
its four vias electrically dangling. **A geometric bridge is NOT electrical
connectivity.** Log: `checks/w/log_003n_b1_r75rot.txt`.

### 4.2 The cheap discriminating probe (CTO-authorized, added to `screen_003n.py`)

Before spending an expensive full run on each remaining survivor, 003N runs a **cheap
focused bridge-connectivity probe** (`screen_003n.py --bridge`) that reproduces the EXACT
early southern D-275 bridge (`bridge_early_003i.apply_early(south=True)` — the same stage
the driver fires at its first `8*` item) in ISOLATION on each candidate's D-286 placed
board, fills, saves, and runs the real DRC. KiCad's `via_dangling` is the authoritative
≥2-layer-connected test; **a via connected on only one layer is a genuine electrical
fault and MUST fail** — never absorbed. Each dangling via is attributed to its nearest
pad, so entry(R75.2) vs exit(C36.1) is identifiable. A candidate is CONNECTED only if the
bridge laid AND `via_dangling == 0` AND entry ≥ 3 AND exit ≥ 3 AND disjoint ywest > 75 AND
traverse w ≥ 1.20 mm.

The probe is **validated against the b1_r75rot control**: it reproduces `via_dangling +4`
exactly (`screen_003n.py --bridge --validate` asserts b1_r75rot FAIL with ≥1 dangling —
PASS), matching the full-run cascade. It is now a **standing bridge integration
regression**.

### 4.3 All three survivors — probe result (`checks/w/screen_003n/bridge_probe.json`)

| candidate | land | traverse | entry | exit | ywest | dangling | verdict |
|---|---|---|---|---|---|---|---|
| **b1_r75rot**  | C36.1 | 72.786 mm @ 1.40 | 4 | 4 | 82.40 ✓ | **4** | **FAIL** |
| **b1_r75rotN** | C36.1 | 73.286 mm @ 1.40 | 4 | 4 | 82.40 ✓ | **4** | **FAIL** |
| **b1_q3rot**   | C36.1 | 76.103 mm @ 1.50 | 4 | 4 | 61.04 ✗ | **2** | **FAIL** (also NOT disjoint) |

Every dangling via is attributed to the **ENTRY array on R75.2** — whether R75 is moved
(r75rot/N → 4 dangling) or held at its authoritative home (q3rot → 2 dangling). b1_q3rot
fails a second way too: with R75 home the forced-south wall does not push the western leg
below the tap band, so ywest = 61.04 < 75 (not disjoint). **0/3 truly connected.**

## 5. Root cause — an ASYMMETRIC, placement-independent bridge-implementation defect

Direct geometry (probe scratch board, b1_r75rot):

```
R75.2 pad  : center (2.800, 67.963), net BAT_PROTECTED_P, layer B.Cu only,
             bbox y ∈ [67.350, 68.575]
entry vias : (2.087, 66.188) (3.487, 66.188) (2.788, 66.188) (2.413, 66.812)
             — all ~0.5–1.15 mm NORTH of the R75.2 B.Cu pad's north edge
```

The four entry vias land **north of R75.2's B.Cu pad**, over bare substrate. On F.Cu they
are tied together by the `apply_early` bus track; on B.Cu they touch **nothing** — so
each via has copper on exactly one layer → `via_dangling`. The **exit** array does not
dangle because `bridge_early_003i._lay_landing` lays an explicit **B.Cu tie-stub** from
each exit via to its landing pad (`qb.track(NET,'B', x,y, npx,npy)`) in addition to the
F.Cu track — a symmetric two-layer tie. **The entry array has no such B.Cu tie-stub**: it
relies on the POFV vias physically overlapping R75.2's pad, which does not hold at this
placement (or the home placement). The defect is in `bridge_early_003i.apply_early` /
`bridge_route_003c.scan_entry_sites` — it is **structural to the bridge code and present
in every placement**, modulated (4 vs 2 dangling) only by how many entry sites happen to
clip the pad.

This also RE-QUALIFIES the earlier "the D-275 south bridge PASSED" claims (003K/003L/
003M): those were **geometric** passes (array laid, traverse full-width, disjoint) that
were never electrically gated — c3_00 failed on the placement short first, so the entry
dangling was masked. 003N is the first run to gate the bridge **electrically** end-to-end,
and it fails. Consistent with the D-286 binding constraint: surface the fault, do not
absorb it.

## 6. Verdict and why this is NOT an owner decision

- The **entire bounded direction-1 candidate space is exhausted**: 24 rejected at bare
  placement, 3 survivors refuted at bridge integration.
- BUT the three survivors do **not** fail on a placement wall — they fail on a **bridge
  connectivity implementation defect independent of placement** (the missing entry-array
  B.Cu tie-stub). This is exactly the case the 003N charter names as a **narrower CTO
  technical lever**: fixing it does not require moving any LTC-block footprint and is
  independent of the placement search.
- Therefore **direction-2 (broad LTC4368 refloorplan / corridor widening, OWNER/
  mechanical) is NOT yet the sole remaining option**, and this is **NOT an OWNER
  decision**. `/home/aqroot8/.aqroot-autopilot-stop` stays ABSENT; open owner decisions
  remain NONE.

## 7. The next bounded task — FBV2-P2-003O (CTO scope)

**Fix the D-275 south-bridge ENTRY-array two-layer tie so the entry vias are electrically
connected (zero `via_dangling`), symmetric to the proven exit array.** Concretely, in
`bridge_early_003i.apply_early` / `bridge_route_003c`: after laying the entry vias and the
F.Cu bus, add an explicit **B.Cu tie-stub from each entry via to R75.2's pad centre**
(mirroring `_lay_landing`'s exit stub) and/or constrain `scan_entry_sites` to sites that
truly sit inside R75.2's B.Cu pad copper — with NO rule/floor/topology/footprint change
and NO absorption. Verify with `screen_003n.py --bridge` that the fixed bridge reports
`via_dangling == 0`, entry ≥ 3, exit ≥ 3, disjoint ywest > 75, traverse ≥ 1.20 mm on the
best survivor **b1_r75rot** (disjoint 82.40, cleanest geometry). Only when the probe is
GREEN, take b1_r75rot into a parent-supervised full Phase-A run; then close
`BAT_PROTECTED_P` and re-measure connectivity/ratsnest. If — and only if — the entry tie
proves un-fixable without relaxing a floor or moving a frozen part does direction-2
become a genuine OWNER decision.

## 8. Integrity

- **Only new file:** `checks/screen_003n.py` (the D-286 screen + the bridge-connectivity
  probe/regression). No driver, router, DRU, footprint, netclass, or rule source mutated.
- Authoritative PCB UNCHANGED: six layers, 0 tracks, 0 vias, placement untouched.
- `phaseA_journal.json` restored to committed HEAD state (driver never authoritatively
  invoked; scratch churn discarded).
- All scratch under `checks/w/screen_003n/` (gitignored).
- Regressions GREEN: `screen_003n.py --validate` (c3_00 REJECT +3, reference clean);
  `screen_003n.py --bridge --validate` (b1_r75rot FAIL, via_dangling +4).
- No DRC absorbed; a `via_dangling` item IS the FAIL reason. `c3_00` not promoted;
  `place_003l` (D-285) preserved and clean; optional `BAT_SENSE TP20.1` separate; frozen
  `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged.
- **NO PROGRESS EARNED:** PCB routing 0 %, overall 74 %, readiness ~77 %.
