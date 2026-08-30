# FBV2-P2-003T / D-294 — Direction-2 (D-293) executed: a focused minimum candidate exists, but the governing full authority gate FAILs; no candidate is promotable

**Date:** 2026-08-30
**Task:** FBV2-P2-003T
**Decision:** D-294
**Starting HEAD:** `9c708f3` (clean; `phaseA_journal.json` at HEAD)
**Class:** GOVERNED EVIDENCE / NO-PROGRESS milestone — autonomy CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).
**Result:** The owner-approved (D-293) bounded direction-2 lever — relocate the minimum escape-target set so `BAT_RAW` and `BAT_PROTECTED_P` leave U18 through independent corridors — was screened cheaply and then run under **full CTO authority**. A **focused minimum candidate genuinely exists** (`t_a_r77e15n10_r79e15n10`: R77/R79 +1.5 mm east +1.0 mm north with U18 north +1.25 mm → focused conn 20, `fail=None`, DRC clean, U18.8 **and** U18.9 both JOIN). But the **governing full authority gate FAILs**: at full congestion U18.8's `R75.2` join has **no I2 corridor at 0.200 mm between the two reserved vias** (fallback `NO_VIA_SITE`, no 0.65 mm B via site), U18.9 joins but U18.8 stays open, and a **NEW governing wall** surfaces at `REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`. Direction-2 is **partially productive** (+2 connections vs the 003O baseline, the old `REF_POL R87.2` wall is now past) but **incomplete**; **no candidate is promotable.** No source/copper/placement/rule change, no DRC absorbed, no promotion. D-269 enforced at 0.300 mm, D-290 remains closed, D-275/D-288 and all floors preserved.

---

## A — What D-293 authorized, and what 003T did

D-293 (Alpha, 2026-08-29 22:34 UTC) approved **direction 2**: relocate the *minimum necessary*
escape targets — R77/R79 east and/or R80/R81 north as measured evidence dictates — so the two
opposite-edge current-path nets D-292 identified (`BAT_RAW` U18.1 east, `BAT_PROTECTED_P` U18.8
west) leave U18 through **independent corridors**. The authorization explicitly does **not** relax
D-269 (0.300 mm current-path) or any floor, does not accept U18.8 open, and does not re-authorize
the D-290 routing lever.

003T built a bounded direction-2 candidate grid (`w/mkcands_003t.py`, `w/batch_003t.sh`), screened
each on a cheap focused vehicle, then took the single `fail=None` survivor into a full authority run.
The ACP wrapper failed on the long run; **the CTO completed the decisive full-authority run
directly** (`FULL003T_e15n10cto`, `w/phaseA_003t_full_e15n10cto.json`, secs 1313.8).

## B — The bounded direction-2 candidate table (focused vehicle; cheap, non-authoritative)

| candidate JSON | move | conn | skip | ratsnest (Δ) | DRC added vs base | verdict |
|---|---|---:|---:|---|---|---|
| `phaseA_003t_t_n125` | U18 north +1.25 only | 17 | 2 | 763 (−18) | clearance +1 | FAIL `LTC_UV U18.2→R79.2` new DRC clearance 1 |
| `phaseA_003t_t_a_r77e10_r79e10` | R77/R79 +1.0 E | 19 | 2 | 761 (−20) | clearance +1 | FAIL `LTC_OV U18.3→R77.2` new DRC clearance 6 |
| **`phaseA_003t_t_a_r77e15n10_r79e15n10`** | **R77/R79 +1.5 E +1.0 N, U18 n+1.25** | **20** | **2** | **760 (−21)** | **none** | **PHASE A COMPLETE (`fail=None`)** |
| `phaseA_003t_t_a_r77e20_r79e20` | R77/R79 +2.0 E | 19 | 2 | 761 (−20) | clearance +1 | FAIL `LTC_OV U18.3→R77.2` new DRC clearance 6 |
| `phaseA_003t_t_b_n075_r80n10_r81n10` | R80/R81 +1.0 N, U18 n+0.75 | 18 | 2 | 762 (−19) | clearance +1 | FAIL `LTC_UV U18.2→R79.2` NO_LEGAL_ESCAPE |

**Reading of the table.** East-only moves (`e10`, `e20`) leave the east `LTC_OV U18.3→R77.2` current
pin gate-rejected (a too-small east move keeps the corridor tight; a too-large one, `e20`, re-breaches
against the moved neighbor) — the window is narrow. North-only (`n125`) breaches `LTC_UV U18.2→R79.2`.
The R80/R81-north variant (`t_b`) leaves `LTC_UV` with no legal escape. **Exactly one** combined move —
R77/R79 +1.5 mm east **and** +1.0 mm north with U18 north +1.25 mm — clears every east pin **and** every
west pin with **zero added DRC**: the focused vehicle's `fail=None`, conn 20, U18.8 JOIN ok and U18.9
JOIN ok (`w/phaseA_003t_t_a_r77e15n10_r79e15n10.json`, journal). This is the **focused minimum
direction-2 candidate**, and it is the one the CTO advanced to the full gate.

## C — The governing full authority run (`t_a_r77e15n10_r79e15n10`, U18 n+1.25)

`w/phaseA_003t_full_e15n10cto.json` (the authoritative decision artifact):

| metric | 003O baseline (evidence of record) | 003T full authority | Δ |
|---|---|---|---|
| source JSON | `checks/phaseA_003o_b1_r75rot_cto.json` | `checks/w/phaseA_003t_full_e15n10cto.json` | — |
| connections | **67** | **69** | **+2** |
| skipped-already-connected | 99 | 98 | −1 |
| ratsnest | 781 → **708 (−73)** | 781 → **708 (−73)** | identical |
| PHASE A | FAIL | FAIL | wall MOVED |
| terminal wall | `REF_POL R87.2→(node) NO_PATH` (no F corridor @0.150 mm) | **`REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`** | new wall |
| U18.8 (`BAT_PROTECTED_P` west) | OPEN (`NO_VIA_SITE`) | **OPEN** (`R75.2` join `NO_PATH` → `NO_VIA_SITE`) | still open |
| U18.9 (`BAT_SENSE` Kelvin) | — | **JOINED** (In2, `BAT_SENSE_KELVIN`) | — |
| final DRC | `{hc:5, lfi:199, smb:1, tw:1, uc:499}` | `{hc:5, lfi:199, smb:1, tw:1, uc:499, via_dangling:1}` | +1 dangling (scratch, surfaced) |

**The two full-context walls, exactly as measured:**

1. **U18.8 `BAT_PROTECTED_P` west (open, non-terminal).** In the full run U18.8→R75.2 reserves on I2
   (`RESERVE_PAIR` ok, journal) but the **JOIN fails `NO_PATH`: "no I2 corridor at 0.200 mm between
   reserved vias"** — the U18.9-Kelvin reserve via and the U18.8-`BAT_PROTECTED_P` reserve via, both on
   the same inner layer, pinch the join corridor below the 0.200 mm general clearance floor under full
   congestion; the B fallback then hits `NO_VIA_SITE` (no 0.65 mm B via site reachable). U18.9 joins;
   U18.8 is left open and the run continues.
2. **`REC_BAT_LOW U19.7→(node)` (the PHASE A terminal FAIL).** `NO_LEGAL_ESCAPE` at ≥0.150 mm, blocked
   by **U19.8 (×26), U19.6 (×13), U19.5 (×7), track (×6)** — U19.7's escape zone is boxed by its own
   package neighbors' **already-committed escapes** (U19.8's `VREC_VCC→C60.1` and U19.5's `REF_HO→R91.2`
   both route earlier in the journal) plus six committed track segments. This is an **escape-ordering /
   corridor-reservation** wall (the neighbors escaped first and consumed U19.7's corridor), NOT a DRU
   rule and NOT a placement short.

## D — D-293 VERDICT: focused minimum exists, governing gate fails → nothing promotable

**Direction-2 is genuinely productive but incomplete.** Relocating R77/R79 east opened the independent
`BAT_RAW` east corridor D-292 required (U18.1→R77.1, U18.3→R77.2, U18.2→R79.2 all connect in the full
journal), routing **+2** more nets than 003O and clearing the old `REF_POL R87.2` terminal wall.

**But the focused closure is vacuous against the congested full run** — the documented Phase-A pattern
(a focused vehicle omits the surrounding congestion, so its `fail=None` does not transfer). The full
gate is the governing gate, and it FAILs on two full-context walls that the cheap vehicle cannot see:
the U18.8 I2 join corridor pinches between the two reserved vias, and a new `U19.7 NO_LEGAL_ESCAPE`
surfaces. **A candidate that closes only in the focused vehicle is NOT promotable**; per D-286 no
proxy evidence promotes copper. No 003T candidate passes the full authority gate → **no promotion.**

This is a **governed CTO FAIL, not an owner decision.** Direction-2 was authorized and remains a valid
direction; 003T did not exhaust it (the failures are bounded, full-context routing/ordering walls with
no floor relaxed and no frozen part moved). Autonomy continues.

## E — Next lever (CTO authority; no D-290 reauth, no D-269 weakening, no owner decision)

**FBV2-P2-003U — a bounded full-context reservation-and-ordering corridor study of the two named
003T walls, at the D-293 direction-2 placement, with every floor enforced.**

- **(1) PRIMARY — `REC_BAT_LOW U19.7` escape ordering (the terminal FAIL).** U19.7 has no legal escape
  only because its own neighbors (U19.8/U19.5) and six tracks escaped first and consumed the corridor.
  Study reserving U19.7's escape **before** its neighbor pins (a path-ordering / escape-reservation
  lever, in the family the D-289 characterization named for capacity walls), and/or re-routing the six
  blocking tracks off U19.7's exit — within existing reservation mechanics, **no DRU change**.
- **(2) SECONDARY — U18.8 I2 join corridor.** The full-run failure is "no I2 corridor at 0.200 mm
  between reserved vias." Study the reserve-via **siting/ordering** on I2 (D-257/D-266 reservation
  mechanics) at the direction-2 placement to open a ≥0.200 mm `BAT_PROTECTED_P` join corridor between
  the U18.8 and U18.9 reserve vias without dropping any via below the D-257 ladder (that would be a DRU
  change, BARRED) and without the D-290 off-layer vacate (BARRED). If evidence shows the corridor
  cannot open under the direction-2 placement without relaxing a floor, that is reported as a bounded
  finding — it does not by itself re-raise an owner decision.

All floors (0.200 mm clearance, 0.25 mm hole-to-hole, **0.300 mm D-269 current-path**, ≥1.20 mm BPP
trunk, 0.60 mm BAT_MAIN) ENFORCED; D-290 stays closed; topology/net/footprint/outline/polarity frozen;
no candidate promoted without full-authority connectivity + DRC + regression evidence.

## F — Integrity

- **Authoritative PCB byte-identical to HEAD** (`sha256 2235e273…d642d7e`): six copper layers, **0
  signal segments, 0 signal vias, 0 arcs**; placement at home. All 003T copper lived only in gitignored
  scratch (`checks/w/`).
- **`phaseA_journal.json` at HEAD** (driver never authoritatively invoked; scratch churn discarded).
- **No DRC absorbed** — the U18.8 open, the U19.7 no-escape, and the single scratch `via_dangling` are
  the surfaced FAIL evidence, on throwaway scratch, never in the authoritative board.
- **No promotion.** `place_003l` (D-285) preserved; D-275/D-288 bridge preserved; D-275 and D-277..D-293
  preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged.
- **Stop file:** `/home/aqroot8/.aqroot-autopilot-stop` **ABSENT** — a normal Phase-A FAIL is not a
  stop reason; the persistent CTO resumes one-Claude-at-a-time engineering with FBV2-P2-003U.
- **Scratch evidence (gitignored under `checks/w/`):** `phaseA_003t_full_e15n10cto.json`,
  `FULL003T_e15n10cto/` (scratch PCB + sources), the focused candidate set
  `phaseA_003t_t_*.json` + `log_003t_*.txt`, the earlier full attempts
  `FULL003T_e15n10{,r}/` + `log_003t_full_e15n10{,r}.txt`, per-candidate `Q003T_*/`,
  `cand_003t/`, `mkcands_003t.py`, `batch_003t.sh`.

**NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.**
