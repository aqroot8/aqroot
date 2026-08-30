# FBV2-P2-003Z — D-300: the `AQROOT_LTCGATE` defer-to-congestion lever's full-authority gate CONFIRMED it is behaviourally identical to D-299 (gained 0 / lost 0, same `LTC_GATE U18.10→Q3.4` terminal wall, same D-249/D-269 rejections, identical DRC) — so the lever and its G15 WIP are REJECTED/RETIRED and the false-positive probe is retired; copper is NOT promoted, autonomy CONTINUES

**Date:** 2026-08-30
**Milestone:** FBV2-P2-003Z
**Decision:** D-300
**Class:** GOVERNED CTO FAIL / lever refutation + WIP retirement — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT). A normal Phase-A FAIL / a refuted bounded lever is not a stop reason.
**Starting HEAD:** `3ce5244` (D-299; pushed; `phaseA_journal.json` restored at HEAD) carrying three uncommitted WIP files: the OFF-by-default `AQROOT_LTCGATE` defer-to-congestion lever in `checks/route_battery_block.py` (+34/−1 lines), its **G15** contract in `checks/router_regression.py` (+30 lines), and the measured-record probe `checks/ltcgate_join_probe_003z.py` (untracked). No router process live.
**Final state:** the rejected source WIP is RETIRED via an **exact reverse patch** scoped to the two tracked files (`git diff -- … | git apply -R`); the false-positive probe is retired (untracked, never committed). Working tree clean; authoritative PCB byte-identical to HEAD. Docs committed. The full-authority gate artifact and scratch are gitignored (`checks/w/phaseA_003t_full_003z3_ltcgate.json`, `w/judge_003z.py`, `w/FULL003T_003z*_ltcgate/`, `w/TEST003Z_*/`).

---

## 1. What 003Z was asked to do

Execute the D-299 handoff (§5): build ONE bounded, env-gated (OFF-by-default) lever
that re-sites / re-orders / detours the `LTC_GATE U18.10→Q3.4` join corridor so its
path (a) stays clear of the `BAT_PROTECTED_P` 1.20 mm trunk region (preserving
**D-249**) and (b) opens the 0.300 mm `BAT_MAIN` clearance (preserving **D-269**),
within existing D-257/D-266 mechanics; then run the ~22-min full-authority gate with
`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1` (both accepted levers ON),
and judge by the full-run connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json`
(D-299) and `w/phaseA_003t_full_003w_u18bpp_i3.json` (D-297). Promote copper only on a
genuine full-authority Phase-A PASS (D-286). No DRU/rule change, no via below the
D-257 ladder, no D-290 re-auth, no D-249/D-269 relaxation, no topology/footprint/
outline change.

## 2. The lever that was built (`AQROOT_LTCGATE`, OFF → byte-identical)

A **pure re-order**: `route_battery_block.py` removed the `LTC_GATE U18.10→Q3.4`
branch from section `8b. LTC_GATE` (guarded on the flag AND the exact triple
`(LTC_GATE, U18.10, Q3.4)`) and re-queued it as the **last** functional item, a new
`13z` stage (after the closure stage and test points) at the ordinary SIG ladder
`LAD_SIG` / clearance. The theory (from the probe, §5): section 8b routes the join
**before** the western margin is fully occupied, so `connect_role` takes a short
central path that narrows to 0.20 mm inside the BPP trunk keep-region (D-249) and
grazes a `BAT_MAIN` path at 0.2803 mm (~20 µm short of D-269). Deferring it to full
congestion was supposed to force the router onto a clean west detour. OFF → the
branch stays in 8b, byte-identical to every prior run. Pinned OFF/ON + scoped by a
**G15** regression contract in `router_regression.py`.

## 3. The full-authority gate RAN and COMPLETED

The CTO completed the governing foreground run in a persistent terminal:

```
AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE=1 \
  bash w/run_003t_full.sh 003z3_ltcgate w/cand_003t/t_a_r77e15n10_r79e15n10.json
```

→ `checks/w/phaseA_003t_full_003z3_ltcgate.json` (secs **1497.0**, driver exited
clean); the shared `phaseA_journal.json` was restored **byte-identical to HEAD**
afterward and **no process remains**. A genuine full-authority artifact (not a proxy
— D-286), judged by `python3 w/judge_003z.py w/phaseA_003t_full_003z3_ltcgate.json`.

## 4. Verdict: BEHAVIOURALLY IDENTICAL TO D-299 — the lever does NOTHING

The gate output is **identical** to the D-299/003Y2 baseline in every judged metric:

| metric | 003Z (LTCGATE ON) | 003Y2 baseline (D-299) |
|---|---|---|
| terminal fail | `LTC_GATE U18.10→Q3.4` (SIG) | `LTC_GATE U18.10→Q3.4` (SIG) |
| new-DRC on the failing rung | `{track_width:1, clearance:1}` | `{track_width:1, clearance:1}` |
| connections / skipped | 72 / 101 | 72 / 101 |
| ratsnest / delta | 705 / −76 | 705 / −76 |
| journal len | 75 | 75 |
| final DRC histogram | `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}` | identical |
| **connected-set diff 003Z vs 003Y2** | **GAINED 0 / LOST 0** | — |

The failing rung's rejections are byte-for-byte the same two frozen owner rules:

```
track_width : rule 'BAT_PROTECTED_P high-current trunk width - D-249'
              min width 1.2000 mm; actual 0.2000 mm
clearance   : rule 'BAT_MAIN routed clearance - current path role - D-269'
              clearance 0.3000 mm; actual 0.2803 mm
```

`LTC_GATE U18.10 ↔ Q3.4` is NOT in the connected set; `LTC_GATE` is still the
terminal fail. No sub-0.50 non-fine via (run via diameters 0.35/0.60/0.65/0.80).
**Deferring the join to route last changed nothing** — the driver's `connect_role`
greedily re-takes the same geometrically-shortest central path even when the branch
is queued as the very last functional item, and that path violates the same two
rules. The re-order is not a real lever; it is a null operation on this wall.

## 5. Why the probe was a FALSE POSITIVE (the governing lesson, D-286 reaffirmed)

The measured-record probe `ltcgate_join_probe_003z.py` claimed the corridor was OPEN
and the wall was a pure ORDERING casualty: on the saved D-299 full-run routed board
`w/FULL003T_003y2_u19cap/aqroot-Beta-v2.kicad_pcb`, a post-hoc
`QR.connect_role(U18.10, Q3.4)` on B.Cu found a legal **10.475 mm west detour**
(out to x≈0.75) clear of both the BPP trunk region and the `BAT_MAIN` path, dropping
the board ratsnest 705→704 with ZERO new DRC classes. That measurement is real **but
it does not reproduce the driver's real in-run state.** The full run:

- routes the join with the reserved-lane keep-outs (U19CAP §C) already **lifted**
  before the closure stage, on a board that is **not** the post-hoc snapshot the
  probe measured;
- runs `connect_role` inside the driver's real per-pass / queue / obstacle state,
  where the shortest legal-looking central rung is still offered first and taken —
  the greedy path-cost model does not prefer the 10.5 mm west detour over the 0.20 mm
  central path unless the central lane is physically **blocked**, which re-ordering
  alone never does.

So the post-hoc probe on the final saved board is a **proxy that the full gate
overrides** (D-286: no focused vehicle / post-hoc measurement promotes copper — only
a genuine full-authority Phase-A PASS does, and here it FAILs identically). The probe
is retired so that **no artifact in the tree claims the lever works.**

## 6. Ruling (D-300)

- **REJECT / RETIRE** the `AQROOT_LTCGATE` defer-to-congestion lever and its **G15**
  production WIP. A pure re-order is a **null operation** on this wall — the join
  re-takes the identical rule-violating central path; gained 0 / lost 0 vs D-299.
- **RETIRE the false-positive probe** `ltcgate_join_probe_003z.py` (untracked, never
  committed) — its post-hoc measurement is a D-286 proxy that the full gate overrode;
  the negative finding is recorded here and in CTO_DECISIONS instead. No claim that
  the lever works survives anywhere in the tree.
- **Copper NOT promoted.** Full Phase-A still FAILs at the unchanged `LTC_GATE
  U18.10→Q3.4` wall; the authoritative board stays six layers / 0 tracks / 0 vias;
  readiness/progress UNCHANGED (D-286).
- **NOT an owner decision** — no floor relaxed, no frozen part moved, no DRU change,
  no D-249/D-269 relaxation; the wall remains a bounded, in-principle-reducible
  routing/geometry pinch within CTO scope. Autonomy CONTINUES.

**Retirement proof.** Exact reverse patch scoped to the two tracked WIP files
(`git diff -- route_battery_block.py router_regression.py | git apply -R`), NOT a
broad destructive reset. Post-revert `git hash-object` of each file equals its
`HEAD:` blob (`route_battery_block.py` `ebcafae…`, `router_regression.py`
`38eb3a8…`); `git grep` for `LTCGATE` / `AQROOT_LTCGATE` / `13z` /
`ltcgate_join_probe` over tracked Python source (excluding gitignored `checks/w/`)
returns **no match**; the untracked probe is removed; `git status` clean apart from
these docs. `router_regression.py` **ALL CHECKS PASS** (G12/G13/G14 intact; the G15
WIP correctly gone).

## 7. Bounded Opportunity & Simplification Scan (mandated at this milestone)

A deliberate scan for any product-capability / BOM / recoverability / testability /
manufacturing / firmware / UX / future-option opportunity around the LTC_GATE /
power-protection block, and for the next best *technical* lever, grounded in the
measured geometry above.

- **Product capability / architecture.** NONE justifies change. `LTC_GATE` is the
  LTC4368 gate-drive net; the wall is a **single internal control-net join**, not a
  capability gap. All other `LTC_GATE` segments are connected (`U18.10→R76.1` F.Cu
  FINE_ESC; `Q3.2→Q3.4`/`Q2.2→Q2.4`/`Q3.2→Q2.2` B.Cu). No architecture fork.
- **BOM.** NONE. No component add/remove/substitute closes a 20 µm routing pinch; the
  reverse-protection topology (LTC4368 + Q2/Q3 back-to-back FETs) is frozen and
  correct. No BOM opportunity, no cost lever.
- **Recoverability (D-049).** Unaffected. Low-current control net; no DNP/0 Ω/test
  point change is implicated. TP17 already sits on the `U18.10/R76.1` side.
- **Testability / manufacturing / firmware / UX.** All unaffected — a pure internal
  routing pinch with no footprint/outline/stackup/silk/firmware surface.
- **Future option.** The six-layer stack's bare inner signal layers In2/In3 remain
  spare capacity in this corridor (the D-297 lesson) — a preserved future vehicle if a
  west F.Cu/B.Cu detour proves congested. No option is foreclosed by deferring.
- **Cost classification.** No irreversible cost, no strategic fork, no opportunity
  loss. **Open owner decisions: NONE.**

**Next best technical lever (grounded, for FBV2-P2-004A).** The probe *did* find a
legal 10.475 mm west detour (B.Cu, w=0.20, 0 new DRC) — the corridor genuinely
exists; the driver simply will not take it while the shorter central lane is offered.
So the next lever is **path-shaping, not ordering**: an explicit local waypoint /
corridor reservation that *blocks* the rule-violating central lane for exactly this
join (a foreign keep-out over the central lane during the `U18.10→Q3.4` route, on the
proven `AQROOT_U19CAP` KO mechanism — lifted after), forcing `connect_role` onto the
west detour clear of the BPP 1.20 mm trunk region (D-249) and the `BAT_MAIN` path
(D-269, the miss is only ~19.7 µm). Env-gated OFF-by-default, within D-257/D-266
mechanics, no rule/DRU/topology change; judged only by the full gate. A **bounded
immediate-neighbor placement ECO** (nudging the offending `BAT_MAIN` path / Q3
cluster by ~20 µm to open the D-269 clearance on the natural central path) is the
**fallback** — larger blast radius, must be re-screened with real full-placement DRC
(D-286), reversible but touches placement, so it is second choice. Both preserve every
floor; neither is an owner decision.

## 8. Integrity

- Authoritative PCB byte-identical to HEAD (`sha256 2235e2736838…d642d7e`; six copper
  layers, 0 signal tracks, 0 signal vias, placement at home).
- No DRC absorbed — the LTC_GATE fail, the D-249/D-269 rejections and the lone scratch
  `via_dangling` live only on gitignored full-run scratch, never in the authoritative
  board. No promotion.
- `phaseA_journal.json` at HEAD (backed up / restored byte-identical around the run).
- No via below the D-257 ladder; D-269 (0.300 mm), ≥1.20 mm BPP (D-249), 0.60 mm
  BAT_MAIN ENFORCED; D-290 untouched.
- The accepted `AQROOT_U18BPP_JOIN` (D-297) and `AQROOT_U19CAP` (D-299, G14) levers,
  `place_003l` (D-285), the D-275/D-288 bridge, and D-275 and D-277..D-299 all
  preserved; frozen `beta-full-reference-v1` untouched.
- Gitignored evidence preserved: `checks/w/phaseA_003t_full_003z3_ltcgate.json`,
  `w/judge_003z.py`, `w/FULL003T_003z_ltcgate/`, `w/FULL003T_003z2_ltcgate/`,
  `w/FULL003T_003z3_ltcgate/`, `w/TEST003Z_EXPLORE/`, `w/TEST003Z_PROBE/`,
  `w/run_003z_ltcgate.log`.
- `router_regression.py` ALL CHECKS PASS (G12/G13/G14). `JLCPCB_READINESS` unchanged.

## 9. Next — FBV2-P2-004A

Build ONE bounded, env-gated (OFF-by-default) **path-shaping** lever for `LTC_GATE
U18.10→Q3.4`: an explicit local waypoint / central-lane keep-out (on the
`AQROOT_U19CAP` KO mechanism, lifted after the join) that forces `connect_role` onto
the proven ~10.5 mm west detour clear of the BPP 1.20 mm trunk region (D-249) and the
`BAT_MAIN` path (D-269) — NOT a re-order (refuted here). Keep `AQROOT_U18BPP_JOIN=I3`
+ `AQROOT_U19CAP=1` ON. Validate against `router_regression.py` (authoritative
byte-identical), then run the full-authority gate and judge by the connected-set diff
vs `w/phaseA_003t_full_003y2_u19cap.json` and `w/phaseA_003t_full_003w_u18bpp_i3.json`
— the run must close the `LTC_GATE` join for a real net gain with no new DRC class.
Promote copper only on a genuine full Phase-A PASS (D-286). The bounded
immediate-neighbor placement ECO is the fallback (re-screen full-placement DRC). No
DRU/rule change, no via below the D-257 ladder, no D-290 re-auth, no D-249/D-269
relaxation, no topology/footprint/outline change.

**NO PROGRESS EARNED (no copper promoted): PCB routing 0 %, overall 74 %, readiness ~77 %.**
