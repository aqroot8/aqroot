# FBV2-P2-003Y — D-299: the D-298 U19 CAPACITY lever's full-authority gate COMPLETED and it is a GENUINE **+2** capacity gain (NOT the D-296 swap) — so `AQROOT_U19CAP` is ACCEPTED and **COMMITTED** (banked OFF-by-default, G14); copper is NOT promoted because full Phase-A still FAILs, the terminal wall newly ADVANCING to `LTC_GATE U18.10→Q3.4` (candidate paths DRC-gate-rejected by the frozen D-249 BPP-trunk-width and D-269 BAT_MAIN-clearance rules), autonomy CONTINUES

**Date:** 2026-08-30
**Milestone:** FBV2-P2-003Y
**Decision:** D-299
**Class:** GOVERNED CTO ACCEPT + COMMIT (source lands) + overall-run FAIL + HANDOFF — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT). A normal Phase-A FAIL / newly-exposed bounded wall is not a stop reason.
**Starting HEAD:** `7a39430` (D-298; pushed after this task; `phaseA_journal.json` at HEAD) carrying the uncommitted OFF-by-default `AQROOT_U19CAP` lever WIP in `checks/route_battery_block.py` + the G14 contract in `checks/router_regression.py`.
**Final state:** source (`checks/route_battery_block.py`, `checks/router_regression.py`) **COMMITTED** (the full gate validated the lever as a genuine net gain — the deliberate promotion of the *source*, not of copper); docs committed. The full-authority gate artifact is gitignored scratch (`checks/w/phaseA_003t_full_003y2_u19cap.json`).

---

## 1. What 003Y was asked to do

Execute the D-298 handoff: run the **full-authority Phase-A gate** for the bounded
U19 CAPACITY lever (`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1`, direction-2 placement
`t_a_r77e15n10_r79e15n10`) — the only judge that promotes copper (D-286) — and rule
on whether closing `REC_BAT_LOW U19.7` **and** `N_BATDIV U19.6` is a **real net +2**
(promotable) or another **1-for-1 swap** (the D-296 refutation). The screen (D-298
§4) proved the U19 *mechanism* is DRC-clean and the pair *can* coexist; only the
~22-min full gate decides net gain vs swap and whether `LTC4368_FAULT_N` detours
cleanly under full congestion (D-298 §5). No DRU/rule change, no via below the
D-257 ladder, no D-290 re-auth, no topology/footprint/outline change.

## 2. The gate ran and COMPLETED (valid foreground full-authority run)

The CTO completed the governing run in a persistent terminal:

```
AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 \
  bash w/run_003t_full.sh 003y2_u19cap w/cand_003t/t_a_r77e15n10_r79e15n10.json
  -> checks/w/phaseA_003t_full_003y2_u19cap.json   (secs 1463.2, driver exited clean)
```

The **shared** `phaseA_journal.json` was backed up before and **restored
byte-identical to HEAD** after; **no process remains**. This is a genuine
full-authority artifact — not a proxy, focused vehicle, or partial run (D-286).
Judged by `checks/w/judge_003y2.py` (full-run connected-set / open-set diff vs the
D-297 003W baseline `w/phaseA_003t_full_003w_u18bpp_i3.json` and the committed
natural run `phaseA_003o_b1_r75rot_cto.json`).

## 3. The verdict — a GENUINE +2 capacity gain (NOT the D-296 swap)

| metric | 003O natural | 003W (D-297) | **003Y2 (D-298 U19CAP)** |
|---|---|---|---|
| connections | 67 | 70 | **72** |
| skipped | 99 | 99 | **101** |
| ratsnest / Δ | 708 / −73 | 707 / −74 | **705 / −76** |
| journal len | 69 | 73 | **75** |
| secs | 1776.5 | 1272.5 | **1463.2** |
| terminal fail | `REF_POL R87.2→(node)` NO_PATH | `REC_BAT_LOW U19.7→(node)` NO_LEGAL_ESCAPE | **`LTC_GATE U18.10→Q3.4`** (DRC-gate-rejected) |

**Connected-set diff 003Y2 vs 003W — GAINED 2, LOST 0:**

```
  + N_BATDIV     [R89.2, U19.6]   role=SIG layer=F vias=2 via_dia=0.6
  + REC_BAT_LOW  [(node), U19.7]  role=SIG layer=F vias=2 via_dia=0.6
  (LOST: none)
```

Both boxed U19 pins close **simultaneously** for a strict **+2** with **nothing
lost** — the categorical opposite of D-296's proven 1-for-1 swap (which gained
U19.7 only by losing `REF_POL U19.2`). The U19 field is genuinely *enlarged*, not
re-ordered. The screen's prediction (D-298) is confirmed by the full router,
though the escape geometry the full run actually chose differs slightly from the
probe's In3/In2 0.65/0.40 route: **both pins escape on F.Cu with the ordinary
board-legal 0.60/0.30 SIG via** (`U19.7` REC_BAT_LOW 15.621 mm, 2 vias;
`U19.6` N_BATDIV `R89.2→U19.6` 9.52 mm, 2 vias) — still board-legal, still +2,
via a route the full congestion permitted. (The +2 is the promotion metric; the
looser vs-003O diff is +7/−2, dominated by the direction-2 BAT_RAW/REF_POL gains
already banked upstream and by the natural run's different U19.7 target.)

**`LTC4368_FAULT_N` detours CLEANLY (the D-298 §5 risk is resolved).** All three
branches are connected on B.Cu and FAULT_N is **not** the terminal wall:
`U18.7→R81.2` 8.478 mm, `R81.2→R82.1` 2.719 mm, **`R82.1→Q9.1` 77.567 mm** — the
64 mm direct run detoured ~13 mm longer around the reserved U19 east lane and
still cleared the per-connection `gate()`. The probe's crude whole-net reroute
grazing BAT_MAIN was, as D-298 predicted, an artifact — the real driver routed
FAULT_N clean.

**No DRC regression.** The final DRC histogram is **identical** to 003W —
`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1,
track_width:1, unconnected_items:499}` — **no new class, no increased count**.
No sub-0.50 non-fine via (distinct via diameters in the run: 0.35, 0.60, 0.65,
0.80 — every one on or above the D-257 ladder). The U19 escapes added no DRC of
their own.

Verdict components (from `judge_003y2.py`): U19.7 closed **True**, U19.6 closed
**True**, net gain vs 003W (no loss) **True (+2/−0)**, is-a-swap **False**, no new
DRC class/increase **True**, FAULT_N-not-terminal **True** — and full-run PASS
**False** (the run FAILs at a new, further wall — see §4).

## 4. The new terminal wall — `LTC_GATE U18.10→Q3.4`, sharply characterized (no new route)

The +2 U19 closure moved the terminal wall **two connections forward**, past the
entire U19 field, to the LTC4368 gate-drive net:

```
fail: LTC_GATE U18.10->Q3.4 (SIG) : new DRC {track_width:1, clearance:1}
  track_width : rule 'BAT_PROTECTED_P high-current trunk width - D-249'
                min width 1.2000 mm; actual 0.2000 mm
  clearance   : rule 'BAT_MAIN routed clearance - current path role - D-269'
                clearance 0.3000 mm; actual 0.2803 mm
```

**This is NOT `NO_PATH` / `NO_LEGAL_ESCAPE`.** Candidate paths for the join *are
found*; the driver's per-connection `gate()` **rejects every candidate** because
each one violates one of **two FROZEN owner rules**:

- **`LTC_GATE`'s already-routed context (from the artifact journal).** The net's
  other segments are all connected: `U18.10→R76.1` on F.Cu (FINE_ESC_3, 0.20 mm,
  2× 0.35/0.20 fine vias at `[[5.9,64.8],[7.5,60.8]]`), and the gate-transistor
  chain `Q3.2→Q3.4`, `Q2.2→Q2.4`, `Q3.2→Q2.2` on B.Cu. The **failing** connection
  is the **JOIN that bridges the `U18.10` F.Cu escape cluster (north, y≈60–65) to
  the `Q3.4` gate cluster (B.Cu, y≈59)**.
- **Wall (1) — D-249 (`BAT_PROTECTED_P` high-current trunk, min 1.20 mm).** Every
  candidate join narrows to its natural 0.20 mm SIG width **where the
  `BAT_PROTECTED_P` 1.20 mm-trunk area rule applies** — i.e. the candidate path
  enters/overlaps the western-margin BPP trunk keep-region on that layer. D-249 is
  a hard current-path floor: the fix is to route the join *out of* the BPP trunk
  region, not to relax the rule.
- **Wall (2) — D-269 (`BAT_MAIN` routed clearance, current-path role, 0.300 mm).**
  The candidate comes within **0.2803 mm** of a `BAT_MAIN` current path — only
  **~19.7 µm short** of the 0.300 mm floor. A hair's-breadth miss, not a
  topological block.

**Class of wall.** This is the **same family** as the U18.8 and U19 walls that
preceded it — a **full-run-emergent congestion / corridor pinch on a flexible,
low-current control net** (`LTC_GATE` is gate drive; it has ample routing slack),
squeezed here between the `BAT_PROTECTED_P` trunk (D-249) and a `BAT_MAIN` current
path (D-269). It is **bounded and reducible in principle**: the join has slack, the
D-269 miss is ~20 µm, and a corridor detour / re-site / re-order of the
`U18.10→Q3.4` join that keeps it clear of the BPP trunk region and opens the
0.300 mm BAT_MAIN clearance should close it **within existing D-257/D-266
mechanics, preserving D-249 and D-269**. It is a routing/ordering lever, **not** an
owner decision and **not** a rule relaxation.

## 5. Ruling (D-299) — ACCEPT + COMMIT the U19CAP source; do NOT promote copper

1. **The D-298 U19 CAPACITY lever is a genuine +2 capacity gain, ACCEPTED.** The
   full-authority gate (the only promoting judge, D-286) closed `REC_BAT_LOW U19.7`
   **and** `N_BATDIV U19.6` for a strict +2 with **nothing lost**, board-legal
   0.60/0.30 vias, `LTC4368_FAULT_N` detouring clean, and **zero** new DRC — the
   categorical improvement over the refuted D-296 swap that D-298 designed for.
2. **COMMIT the source (this is where the change lands).** The two source files —
   the OFF-by-default `AQROOT_U19CAP` lever in `checks/route_battery_block.py` and
   the **G14** contract in `checks/router_regression.py` — are **retained and
   committed**, banked env-gated / **OFF by default** (byte-identical when unset).
   (D-298 deliberately left them uncommitted pending this gate; the gate passed the
   *net-gain* test, so the source now lands.)
3. **Do NOT promote copper.** Full Phase-A still **FAILs** — the terminal wall
   merely advanced past the whole U19 field to `LTC_GATE U18.10→Q3.4`. Per D-286
   copper promotes only on a genuine full-authority Phase-A **PASS**, so the
   authoritative board stays six layers / **0 signal tracks / 0 signal vias**,
   byte-identical to HEAD, and **readiness / progress are UNCHANGED**.
4. **Governance.** A governed CTO **ACCEPT + COMMIT + overall-run FAIL + HANDOFF**,
   **NOT an owner decision** — no floor relaxed, no frozen part moved, no DRU
   change; the new LTC_GATE wall is a bounded full-context routing/ordering/corridor
   wall reducible within CTO scope. `/home/aqroot8/.aqroot-autopilot-stop` ABSENT,
   autonomy CONTINUES.

## 6. Integrity

- **Authoritative PCB byte-identical to HEAD:** `sha256 2235e273…d642d7e`; six
  copper layers, **0 signal tracks, 0 signal vias**, placement at home
  (C36 63.75,73.75,0°; U18 3.0,72.4,90°). No copper promoted.
- **No DRC absorbed.** All routing/DRC lives on gitignored scratch (`checks/w/`);
  the LTC_GATE gate-rejection and the (now-closed) U19 walls are surfaced FAIL /
  gate evidence, never on the authoritative board.
- `phaseA_journal.json` **at HEAD** (backed up before the run and restored
  byte-identical after; `git diff --stat HEAD` empty for it). No process remains.
- **What lands in tracked source (D-299):** the OFF-by-default `AQROOT_U19CAP`
  U19 east-lane reservation + U19.7-first lever (byte-identical when unset) and
  the **G14** regression contract. **No copper, no placement, no rule/DRU, no
  floor, no topology/footprint/outline change; no via below the D-257 ladder.**
  D-269 (0.300 mm), ≥1.20 mm BPP (D-249), 0.60 mm BAT_MAIN ENFORCED; D-290
  untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297), `place_003l` (D-285), the
  D-275/D-288 bridge, D-275 and D-277..D-298 all preserved; frozen
  `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged.
- `python3 checks/router_regression.py` → **ALL CHECKS PASS**, incl. **G14**
  (lever OFF by default byte-identical; `AQROOT_U19CAP` activates; reserved-lane
  geometry spans U19.7/U19.6; hooks scoped to the U19 east lane +
  REC_BAT_LOW-before-N_BATDIV).
- **NO PROGRESS EARNED (no copper promoted):** PCB routing **0 %**, overall
  **74 %**, readiness **~77 %**.

## 7. Next — FBV2-P2-003Z (the LTC_GATE `U18.10→Q3.4` join lever)

Implement ONE narrowly-scoped, env-gated (**OFF by default**) bounded lever that
**re-sites / re-orders / detours the `LTC_GATE U18.10→Q3.4` join corridor** so its
candidate path (a) stays **clear of the `BAT_PROTECTED_P` 1.20 mm trunk region**
(preserving D-249 — route the join around the western-margin BPP trunk rather than
through it) and (b) opens the **0.300 mm `BAT_MAIN` clearance** (preserving D-269 —
the miss is only ~20 µm). `LTC_GATE` is a low-current gate-drive net with slack, so
a corridor detour / ordering change within existing **D-257/D-266 mechanics**
should close it. Keep `AQROOT_U18BPP_JOIN=I3` **and** `AQROOT_U19CAP=1` **ON**;
validate against `router_regression.py` (authoritative byte-identical) then run the
full-authority gate `AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 <lever env> bash
w/run_003t_full.sh 003z_ltcgate w/cand_003t/t_a_r77e15n10_r79e15n10.json`
(back up / restore the shared `phaseA_journal.json`), judged by the full-run
connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json` and
`w/phaseA_003t_full_003w_u18bpp_i3.json`. **No DRU/rule change, no via below the
D-257 ladder, no D-290 re-auth, no topology/footprint/outline change, no D-249/D-269
relaxation.** Promote copper only on a genuine full-authority Phase-A PASS (D-286).
