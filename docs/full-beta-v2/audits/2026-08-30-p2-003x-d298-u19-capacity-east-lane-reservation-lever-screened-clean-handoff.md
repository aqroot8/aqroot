# FBV2-P2-003X — D-298: the bounded U19 CAPACITY lever (reserve the shared EAST escape lane so `LTC4368_FAULT_N` detours, and close the tighter pin `REC_BAT_LOW U19.7` before `N_BATDIV U19.6`) is IMPLEMENTED env-gated/OFF-by-default and SCREENED DRC-CLEAN on the real full-run board — both boxed U19 pins escape SIMULTANEOUSLY onto bare inner layers with the only board-legal via; copper is NOT promoted (the net +2-vs-swap verdict and FAULT_N's clean detour are the ~22-min full gate's job), autonomy CONTINUES

**Date:** 2026-08-30
**Milestone:** FBV2-P2-003X
**Decision:** D-298
**Class:** GOVERNED CTO IMPLEMENT + SCREEN + HANDOFF — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT). A normal Phase-A FAIL / full-gate-pending is not a stop reason.
**Starting HEAD:** `46b582f` (D-297; pushed; `phaseA_journal.json` at HEAD) with the accepted OFF-by-default `AQROOT_U18BPP_JOIN` lever + G13 already banked.
**Final state:** source (`route_battery_block.py`, `router_regression.py`) + probe (`checks/w/u19cap_probe_003x.py`, gitignored scratch) **UNCOMMITTED** per the 003X discipline (a full-authority PASS is a separate, deliberate promotion step); docs committed.

---

## 1. What 003X was asked to do

Close the sole remaining Phase-A blocker by creating **simultaneous** legal escape
capacity for **BOTH** `REC_BAT_LOW U19.7` **and** `N_BATDIV U19.6` in the saturated
U19 dead-cell field. D-296 proved a single-pin reservation only **swaps** the
casualty, so the lever had to **enlarge** the field, not re-order it — one
minimum-delta env-gated OFF-by-default capacity lever, default byte-identical,
`AQROOT_U18BPP_JOIN=I3` (D-297) kept on in any full-gate recipe, within all floors
and **no DRU/rule/clearance change, no via below the D-257 ladder, no D-290
re-auth, no topology/footprint/outline change.**

## 2. Ground truth measured on the real 003W full-run board

Vehicle: the actual full-congestion board `w/FULL003T_003w_u18bpp_i3/aqroot-Beta-v2.kicad_pcb`
(D-297 lever ON; terminal wall `REC_BAT_LOW U19.7 → (node) NO_LEGAL_ESCAPE`,
`N_BATDIV U19.6` next). Probes: `checks/w/explore_u19_003x.py`,
`dir_escape_003x.py`, `corridor_003x.py`, `remove_faultn_003x.py`,
`pofv_u19_003x.py`, and the record probe `u19cap_probe_003x.py`.

- **U19 is a BOTTOM (B.Cu) SOT-23-8.** East row (x=3.833) N→S: `U19.8` (y29.23),
  `U19.7` (y28.58), `U19.6` (y27.93), `U19.5` (y27.28). All pins escape on B.Cu.
- **U19.7 and U19.6 are pad-boxed on 6 of 8 directions by their NEIGHBOUR PADS**
  (N/S/diagonals) — placement-fixed, and no placement/footprint change is in
  scope. Only **E / W** are non-pad.
- **The EAST lane is walled for BOTH pins by the SAME control track:**
  `LTC4368_FAULT_N` (the `R82.1 → Q9.1` 64 mm cross-board run, `PLAN_2_CHAIN`,
  routed at stage 2-5). Its direct B.Cu path grazes the U19 east column; its
  endpoint `(4.85,28.95)` sits **30 µm** off U19.7's east ray (`d=0.245`,
  margin 0.275). The WEST lane is walled by the west-row pins' own escapes
  (`REF_POL` for U19.7, `N_POL` for U19.6).
- **POFV (via-in-pad) is DRU-BARRED.** The `.kicad_dru` grants the fine
  0.35/0.20 via (annular 0.075) only to **specifically-named** escapes — and
  `U19.2 (REF_POL)`, `U19.3 (N_POL)`, `U19.5 (REF_HO)` each have a D-257 fine-via
  exception, but **`U19.6 (N_BATDIV)` and `U19.7 (REC_BAT_LOW)` do NOT**. The
  only *globally*-legal via is **0.65/0.40** (annular 0.125, hole 0.40), which is
  too big for the 0.25 mm-tall pad's in-pad drop and adds `via_diameter` /
  `annular_width` DRC if forced fine. So the escape must be a lateral B.Cu stub +
  a **general 0.65/0.40** via — which needs a **clear lateral lane**.

## 3. The lever (D-298) — reserve the shared east lane + close the tighter pin first

Two coupled mechanics, one env gate `AQROOT_U19CAP`, OFF by default:

1. **Reserve the U19.7/U19.6 shared east escape lane** with a foreign keep-out
   (B.Cu, x≈4.70, y 27.55→28.95) installed before routing and **lifted just before
   the closure stage** (`'12b'`). While it is up, the `LTC4368_FAULT_N` cross-board
   run (a low-current control net with ample slack) **DETOURS around it** on B.Cu;
   when it is lifted, both pins escape east into the freed lane and hop to a **bare
   inner layer** (`U19.7 → REC_BAT_LOW` on **In3**, `U19.6 → N_BATDIV` on **In2**).
2. **Close the tighter pin first:** at closure `REC_BAT_LOW U19.7` is ordered
   **before** `N_BATDIV U19.6` (the DEADCELL default lists N_BATDIV first, which
   routes U19.6 first and its 0.65 via re-boxes U19.7 — an **intra-pair swap**;
   U19.7-first lets both fit).

This is a **capacity ADD, not the D-296 swap:** it uses the *bare* inner signal
layers (In2/In3, the D-297 lesson) and forces the *flexible* 64 mm control run off
the shared lane — it does not steal a lane a boxed neighbour needs.

**Implementation** (`route_battery_block.py`, all env-gated on `U19CAP`, OFF →
byte-identical): the `AQROOT_U19CAP` flag + `U19CAP_KO` geometry (§ top); install
the keep-out before the pass loop; lift it at the first `'12b'` item; reorder
`CLOSE_NETS` so `REC_BAT_LOW` precedes `N_BATDIV`. The keep-out lives only in the
obstacle model (`qb.shapes['B']`), never becomes copper.

## 4. Measured evidence (`u19cap_probe_003x.py`, real board + real KiCad DRC)

| check | result |
|---|---|
| A `U19.7` boxed on the 003W board (`NO_LEGAL_ESCAPE`) | PASS |
| A `U19.6` boxed on the 003W board (`NO_LEGAL_ESCAPE`) | PASS |
| B `LTC4368_FAULT_N` reroutes on B.Cu AROUND the reserved lane | PASS (detours, still connected) |
| C `U19.7` escapes FIRST onto a bare inner layer (0.65/0.40 via) | PASS — **In3, 13.2 mm, 2 vias** |
| C `U19.6` escapes AFTER U19.7 and they COEXIST (net +2) | PASS — **In2, 9.6 mm, 2 vias** |
| D `U19` escapes are DRC-clean (real KiCad DRC, zone-refilled) | **PASS — ZERO new violation involving `REC_BAT_LOW`/`N_BATDIV`** |

The `U19.7` and `U19.6` escapes with the only board-legal 0.65/0.40 via, once the
GND zones are refilled to carve their antipads, add **no** new DRC class of their
own. The two adjacent boxed pins **coexist** (U19.7-first) — a genuine **+2** in
principle. (A first probe run mis-read `hole_clearance` from un-refilled zones;
`ZONE_FILLER` before DRC clears it, exactly as the D-297 probe does.)

## 5. What the probe does NOT prove — and what the full gate must judge (D-286)

- **FAULT_N's CLEAN detour.** The probe forces FAULT_N with a crude *whole-net*
  `connect_role`, which grazes `BAT_PROTECTED_P` up north (3 `clearance`, plus one
  marginal near Q9) — artifacts of the naive reroute, **not** of the U19 escapes.
  In the real run the driver routes FAULT_N through `run_once` with a
  **per-connection `gate()`** that rejects any DRC-adding path, so it either finds
  a clean detour (the original path needs only a ~30 µm local nudge to clear
  U19.7) or leaves FAULT_N on a clean route. Whether a clean detour exists under
  full congestion is a **full-gate** question.
- **Net +2 vs a swap.** Per D-286 no proxy promotes copper: only the ~22-min
  full-authority connected-set diff decides whether closing U19.7+U19.6 is a real
  net gain or trades FAULT_N / another net. This screen proves the U19 *mechanism*
  is DRC-clean and the pair *can* coexist — the categorical improvement over
  D-296 (which was a proven 1-for-1 swap) — but the verdict is the gate's.

## 6. Ruling (D-298) — implement + bank OFF-by-default; do NOT promote copper

The bounded U19 capacity lever is **implemented, regression-pinned (G14), and
screened DRC-clean** for the decisive question (do both boxed pins escape
simultaneously onto bare inner layers with a legal via?). It is retained
env-gated / **OFF by default** in tracked source (byte-identical when unset). It
is a **capacity add** aligned with the D-297 lesson, categorically distinct from
the refuted D-296 swap. **Copper is NOT promoted:** the full run has not been
executed (the ~22-min gate exceeds the ACP 10-min single-call cap and may not be
backgrounded in this task), so per D-286 nothing promotes and readiness/progress
are unchanged. A governed CTO IMPLEMENT + SCREEN + HANDOFF — not an owner
decision (no floor relaxed, no frozen part moved, no DRU change, direction-2 not
exhausted).

## 7. The exact governing full-authority run (CTO executes in a persistent terminal)

```bash
cd /home/aqroot8/aqroot/hardware/beta-v2/checks
cp phaseA_journal.json /tmp/phaseA_journal.HEAD.json            # back up the SHARED journal
AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 \
  bash w/run_003t_full.sh 003x_u19cap w/cand_003t/t_a_r77e15n10_r79e15n10.json
#   -> writes w/phaseA_003t_full_003x_u19cap.json  (~22 min, DRIVER_EXIT=0)
cp /tmp/phaseA_journal.HEAD.json phaseA_journal.json            # restore the SHARED journal
```

`run_003t_full.sh` carries the full governed recipe and now passes
`AQROOT_U19CAP` through (gitignored scratch script). **Keep `AQROOT_U18BPP_JOIN=I3`
ON** (accepted D-297); **do NOT** combine with the refuted `AQROOT_U19_RESV`
(D-296). **Judge by the full-run connected-set diff** vs
`phaseA_003o_b1_r75rot_cto.json` and `w/phaseA_003t_full_003w_u18bpp_i3.json`: the
run advances only if `U19.7` **AND** `U19.6` close for a real net gain (a swap is
NOT a gain — D-296) with no new DRC class. **Promote copper only on a genuine
full-authority Phase-A PASS** (D-286).

## 8. If the full gate shows FAULT_N cannot detour cleanly (the next sharp lever)

The single sharpest alternative, should the reservation prove insufficient, is a
**DRU fine-via escape exception for `REC_BAT_LOW U19.7` and `N_BATDIV U19.6`**,
mirroring the EXISTING D-257 exceptions already granted to the other three U19
pins (`REF_POL U19.2`, `N_POL U19.3`, `REF_HO U19.5`). A 0.35/0.20 fine via fits
the dense field where the 0.65 via is marginal. **That is a DRU change** — barred
by the 003X constraints — so it is a **CTO/owner re-authorization** question, not
a routing lever, and belongs to a follow-up that lifts the DRU freeze for this
specific, precedented exception. It is named here so the path forward is explicit.

## 9. Integrity

- **Authoritative PCB byte-identical to HEAD:** `sha256 2235e273…d642d7e`; six
  copper layers, **0 signal tracks, 0 signal vias**, placement at home. No copper
  promoted.
- **No DRC absorbed:** all routing/DRC lives on gitignored scratch (`checks/w/`);
  the U19 no-escape walls are surfaced FAIL evidence, never on the authoritative
  board.
- `phaseA_journal.json` **at HEAD** (the driver was never authoritatively
  invoked; the DEADCELL smoke run backed up and restored the shared journal, and
  it was force-restored from git HEAD after this task).
- **What survives in tracked source:** the OFF-by-default `AQROOT_U19CAP` lever
  (byte-identical when unset), the **G14** regression contract, and (gitignored)
  the `u19cap_probe_003x.py` record probe + the exploration probes. **No copper,
  no placement, no rule/DRU, no floor, no topology/footprint/outline change; no
  via below the D-257 ladder.** D-269 (0.300 mm), ≥1.20 mm BPP, 0.60 mm BAT_MAIN
  ENFORCED; D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297),
  `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-297 all
  preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS`
  unchanged.
- `python3 router_regression.py` → **ALL CHECKS PASS**, incl. new **G14**
  (lever OFF by default byte-identical; `AQROOT_U19CAP` activates; reserved-lane
  geometry spans U19.7/U19.6; hooks scoped to the U19 east lane +
  REC_BAT_LOW-before-N_BATDIV). `python3 w/u19cap_probe_003x.py` → **ALL CHECKS
  PASS**.
- **NO PROGRESS EARNED (no copper promoted):** PCB routing 0 %, overall 74 %,
  readiness ~77 %.

## 10. Next — FBV2-P2-003Y

Execute the D-298 handoff: run the full-authority gate (§7) with
`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1`, judge by the connected-set diff. On a
genuine Phase-A PASS (U19.7 + U19.6 closed, no new DRC class), promote the copper
(the first Phase-A completion). If FAULT_N cannot detour cleanly / the run swaps,
that is a governed FAIL and the next lever is the §8 DRU fine-via exception
(owner-scope re-authorization).
