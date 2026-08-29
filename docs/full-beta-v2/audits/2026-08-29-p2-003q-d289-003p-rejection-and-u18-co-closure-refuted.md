# FBV2-P2-003Q / D-289 — the rejected 003P WIP is retired with NO PROGRESS, and the bounded U18.7/U18.8 co-closure lever (reservation ordering) is REFUTED on cheap non-vacuous evidence; the REF_POL/R89 wall is characterized as F.Cu routing capacity with a named narrowest lawful lever (no closure claimed)

- **Date:** 2026-08-29
- **Task:** FBV2-P2-003Q (CTO scope) — autonomous continuation after the persistent CTO rejected the FBV2-P2-003P WIP
- **Decision:** D-289
- **Starting HEAD:** `bc1088d` (FBV2-P2-003O / D-288)
- **Ending HEAD:** this commit (docs + gitignored scratch only; **no source, no copper, no placement, no rule change**)
- **Progress:** **NONE.** PCB routing stays 0 %, overall stays 74 %, JLCPCB readiness ~77 % (unchanged).
- **Authoritative PCB:** UNCHANGED — six copper layers, 0 signal tracks, 0 signal vias; placement untouched (C36 home 63.75,73.75,0°; U18 home 3.0,72.4,90°).
- **Owner decisions:** NONE raised (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT). One bounded CTO routing lever remains untried before any owner decision (see §5).

---

## 0. Summary

The persistent CTO rejected the uncommitted FBV2-P2-003P patch set (D-289/D-290/D-291
as informal code-comment labels — never committed to this ledger). This task (a)
**independently verified** that rejection, (b) **cleanly retired** the rejected WIP
(tree restored to the 003O tip), and (c) continued with the next bounded CTO
engineering task, producing two governed engineering findings — a **refuted**
co-closure lever and a **characterized** capacity wall — neither of which earns
progress. The governed record here is the evidence and the exact next lever, not any
accepted code.

The three informal 003P labels are **VOID and refuted**; this committed **D-289** is
the 003Q governed ruling that supersedes them. They are described below by their
mechanism (divider-tap width / Kelvin sense-pair clearance / test-via role), not by
those labels, to avoid confusing a reader who never saw the retired code.

## 1. Independent verification of the 003P rejection (CONFIRMED)

The rejected 003P WIP consisted of five tracked source edits + six untracked
artifacts, all provably in the D-289/D-290/D-291 chain (explicit markers in every
diff and probe header). Its natural-authority full run
`phaseA_003p_b1_r75rot_cto.json` was compared against the committed 003O evidence of
record `phaseA_003o_b1_r75rot_cto.json`:

| field | 003O (committed) | 003P (rejected) | verdict |
|---|---|---|---|
| connections | 67 | 67 | SAME |
| skipped | 99 | 99 | SAME |
| ratsnest / delta | 708 / −73 | 708 / −73 | SAME |
| final DRC | `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}` | identical | SAME |
| terminal fail | `REF_POL R87.2→(node) NO_PATH @ 0.150 mm` | identical | SAME |

The only delta is the *pre-run baseline* `via_dangling` (2 vs 4) — placement-baseline
measurement noise, not board state. **003P is aggregate-equivalent to 003O.**

**D-290 is a lateral swap (CONFIRMED from the scratch logs, not just the JSON).**
- 003O: `LTC4368_FAULT_N U18.7→R81.2` **CLOSED** (routed 9.728 mm); `BAT_PROTECTED_P U18.8→R75.2` OPEN (reservation gate-rejected on `BAT_MAIN routed clearance`, then `NO_VIA_SITE`).
- 003P: `U18.8→R75.2` **CLOSED** (D-290 relaxed the pair clearance → JOINED 1.245 mm inner-I2); `U18.7→R81.2` now **OPEN** — `NO_LEGAL_ESCAPE … blocked by U18.8 (x25)`. U18.8's copper physically took U18.7's escape. Connections stay 67 — zero-sum.

**The divider-tap-width hypothesis is the wrong lever (CONFIRMED).** In the 003P full
run `BAT_RAW R86.2→(node)` is still `GATE_REJECTED (BAT_MAIN minimum width)` on
**other-branch** 0.20 mm copper (`enclosedByArea` needs the whole track inside the
per-branch corridor, so a merged/extended track is never covered), and
`BAT_RAW R89.1→(node)` is a **true `NO_PATH` at 0.200 mm** — no F corridor exists for
a width allowance to widen. TAP_4/TAP_5 corridors never materialize.

**The test-via-role hypothesis only cured a focused-vehicle artifact (CONFIRMED).**
`LTC_GATE TP17.1` CLOSES anyway in the full run (routed 4.654 mm); the test-via change
only fixed a `phaseA_003p_u19*` focused-vehicle stub-cap/via-site artifact that does
not exist at full authority.

**Conclusion:** the rejection is sound. 003P earned NO PROGRESS.

## 2. Retirement (clean, provable, complete)

- **Reverted to HEAD (`git checkout HEAD --`):** `battery_route_plan.py`,
  `d269_probe.py`, `path_role_dru.py`, `route_battery_block.py`,
  `phaseA_journal.json` (a regenerated run-output artifact; restored to committed).
- **Removed (untracked, all D-289/290/291-marked):** `d289_probe.py`,
  `d290_probe.py`, `d291_probe.py`, `phaseA_003p_b1_r75rot_cto.json`,
  `phaseA_003p_u19.json`, `phaseA_003p_u19_d291.json`.
- **Preserved:** the completed 003P full-run evidence facts live on in the gitignored
  scratch `w/log_003p_b1_r75rot_cto.txt` (like `w/log_003o_…`), and their aggregate is
  recorded in §1 above. The committed 003O evidence of record is untouched.
- **Tree:** clean at `bc1088d`; no rejected clutter, no unrelated/user work disturbed.

## 3. Task 2 — closing BOTH U18.7 and U18.8 via bounded reservation ordering: REFUTED

**Method (cheap, non-vacuous).** The `AQROOT_LOCAL=D256` west-margin prefix vehicle
(U18 field + D-266 reservations + bridge + trip, before the dead-cell/testpoints)
faithfully reproduces the U18.8 reservation clash — it is NOT vacuous for the U18 pin
field (the vacuity caveat applies to the dead-cell/REF_POL nets, not here). Baseline
matched 003O exactly: U18.9 reserves first, U18.8 both attempts `GATE_REJECTED` on
`BAT_MAIN routed clearance`, U18.7→R81.2 CLOSED 9.728 mm.

**The lever tested.** `PLAN_D266_RESERVE` reserves the Kelvin pair in a fixed order —
`BAT_SENSE U18.9→R75.1` first, `BAT_PROTECTED_P U18.8→R75.2` second. The bounded
reservation-ordering lever the task names is to reserve the trunk-critical U18.8 FIRST
(no clearance relaxation, no geometry change), so its scored B exit is picked before
U18.9's copper exists to gate-reject it.

**Result (b1_r75rot + place_003l, D256 vehicle):**

| run | conn | ratsnest | U18.7 | U18.8 | U18.9 | terminal fail |
|---|---|---|---|---|---|---|
| baseline (U18.9-first) | **35** | 740 (−41) | ✓ CLOSED | OPEN | ✓ JOINED | BAT_RAW R89.1 (past U18) |
| reorder (U18.8-first) | **34** | 741 (−40) | ✗ `GATE_REJECTED` clr 0.25<0.30 | ✓ JOINED | ✗ `NO_LEGAL_ESCAPE` | U18.7 (new casualty) |

Reserving U18.8 first **trades one casualty for two** (−1 connection). U18.8 closes but
U18.7 is persistently gate-rejected (its escape sits 0.25 mm from U18.8's new
reservation copper, below the D-269 0.30 mm `BAT_MAIN routed clearance`) and U18.9 can
no longer reserve (its fallback exit terminates into R75.1 copper that the BAT_SENSE
`Q3.6→R75.1` current path already connected, which the inverted reservation gate
forbids) nor escape in the main pass (blocked by U18.10 x25 / U18.7 x17).

**Root cause (geometry, not order).** `U18.8→R75.2` must escape **NORTH**
(U18.8 y≈65.25 → R75.2 y≈66.50) into the **single** escape lane `U18.7→R81.2` also
needs, and U18.8 has **no alternative B via-site** (`NO_VIA_SITE` at 0.65 mm and
0.35 mm on B). `U18.9→R75.1` escapes SOUTH (away), which is why the baseline order
keeps U18.7 but loses U18.8. This is a genuine **3-into-one-corner contention**
(U18.7 / U18.8 / U18.9 + the R75 pads) at the b1_r75rot + place_003l placement.
Reservation ordering only *selects the casualty* — exactly the CTO's lateral-swap
diagnosis and the standing D-266 lesson ("permuting whole-branch order only chooses a
different casualty"). The reservation-**geometry** sub-lever (`D266_INNER` far layer)
cannot help either: the conflict is the B-side neck (`near='B'`), which is layer-
independent.

**Verdict: the reservation-ordering / reservation-geometry lever is REFUTED for
co-closure.** No permutation within that lever class closes U18.7 + U18.8 + U18.9.

## 4. Task 3 — the REF_POL/R89 F.Cu wall: characterized as routing CAPACITY (no closure claimed)

Measured on the **actual congested** routed 003O board
(`w/FIX003O_b1_r75rot_CTO/aqroot-Beta-v2.kicad_pcb`, not a focused vehicle) with
`w/refpol_wall_003q.py`:

- The REF_POL node component is `{TP24.1, U19.2, R88.1}` (all CLOSED). **R87.2**
  (the REF_POL divider tap, at 9.65,25.03) is **isolated** — `R87.2→(node)` and
  `R88.1→R87.2` are `NO_PATH` (no F corridor at 0.150 mm). This is the terminal fail.
- Corridor tally between R87.2 and the nearest node copper (B.Cu, 2.479 mm away):
  **F.Cu is saturated by `N_POL` 6.36 mm** (the `R86.1→TP23.1` 23.7 mm antisocial run)
  **+ `VREF_TOP` 1.45 mm**; B.Cu is blocked by `BAT_RAW` 11.20 mm + `N_BATDIV` 3.91 mm.
- `BAT_RAW R89.1→(node)` is likewise a **true `NO_PATH`** — a width/clearance/via rule
  cannot manufacture an F corridor where the routing graph finds none.

**The wall is F.Cu routing capacity / congestion, NOT any DRU rule.** The narrowest
lawful capacity lever (NOT another DRU exception) is a **D-279-class inner-layer
offload of the `N_POL` F.Cu aggressor** — send `N_POL R86.1→TP23.1` to In2/In3, freeing
the F.Cu corridor for `R87.2→node`. (D-279 today reverts only antisocial *B.Cu*
detours, so this F.Cu run escapes it — extending the offload to the F.Cu aggressor is
the precise bounded change.) A scarce-pad-first ordering for `R87.2→node` is the
secondary candidate. **No closure is claimed:** both levers route these nets in an
uncongested focused vehicle (vacuous) and can only be validated on a full authority
run.

## 5. Next task and owner-decision assessment

- **FBV2-P2-003R (CTO scope), the exact next lever:** vacate the contended pin off the
  single north B escape lane so U18.8 can reserve it — force `U18.7→R81.2` (and, if
  needed, resolve `U18.9→R75.1` as a main-pass hop to the already-connected R75.1 node)
  onto an inner layer (D-278/D-279-class `hop_first`), **coupled** with reserving U18.8
  first; and, in parallel, extend the D-279 offload to the `N_POL` F.Cu run to open the
  REF_POL R87.2 corridor. Both require full-authority validation (the U18 field is
  cheaply screenable; the REF_POL corridor is not). No floor/rule relaxation, no
  frozen-part move, no DRC absorption.
- **Owner-decision boundary (not yet reached).** The reservation-ordering lever is
  refuted, but the off-layer-vacate lever (003R) is untried, so this is a bounded CTO
  engineering result, **not** an owner decision. A genuine OWNER DECISION (a bounded
  LTC4368/R75 placement micro-ECO in the D-284/285 class to open a *second* U18.8
  escape, or direction-2 corridor widening) arises only if 003R also fails to close
  U18.7 + U18.8 + U18.9 without relaxing a floor or moving a frozen part — the 3-way
  north-corner contention makes a placement lever the robust fallback.

## 6. Integrity

- No source, no authoritative copper, no placement, no rule/floor change; no DRC
  absorbed (the 003P blockers and the refuted 003Q reorder are the FAIL reasons).
- Rule floors ENFORCED: 0.200 mm clearance, 0.25 mm hole-to-hole, ≥1.20 mm BPP trunk
  (D-249), 0.60 mm BAT_MAIN minimum width. Six-layer stack, GND, netclasses,
  footprints, polarity, safety — frozen. `beta-full-reference-v1` untouched.
- `c3_00` not promoted; `place_003l` (D-285) preserved; D-275 and D-277..D-288
  preserved. `phaseA_journal.json` restored to HEAD.
- Scratch evidence (gitignored `checks/w/`): `log_003q_baseline.txt`,
  `log_003q_u18first.txt`, `run_003q_cheap.sh`, `refpol_wall_003q.py`,
  `log_003p_b1_r75rot_cto.txt`.
- `.aqroot-progress.env` NOT edited. `JLCPCB_READINESS` unchanged.
