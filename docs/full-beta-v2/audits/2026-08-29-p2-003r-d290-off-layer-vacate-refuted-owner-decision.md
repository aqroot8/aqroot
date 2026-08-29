# FBV2-P2-003R / D-290 — the LAST bounded routing-only U18 co-closure lever (off-layer vacate of U18.7) is REFUTED on cheap non-vacuous evidence; the U18.7/U18.8/U18.9 3-into-one-corner contention is an irreducible placement-geometry mutual-exclusion at the 0.5 mm pad pitch vs the 0.300 mm current-path clearance floor, so a bounded LTC4368/R75 placement micro-ECO is now a genuine OWNER DECISION

- **Date:** 2026-08-29
- **Task:** FBV2-P2-003R (CTO scope) — the off-layer-vacate lever D-289 named as the last routing-only move to co-close U18.7/U18.8/U18.9
- **Decision:** D-290
- **Starting HEAD:** `9bd7aac` (FBV2-P2-003Q / D-289)
- **Ending HEAD:** this commit (docs + two cheap-screen evidence JSONs; **no source, no copper, no placement, no rule change** — the D-290 WIP lever is RETIRED)
- **Progress:** **NONE.** PCB routing stays 0 %, overall stays 74 %, JLCPCB readiness ~77 % (unchanged).
- **Authoritative PCB:** UNCHANGED — six copper layers, 0 signal tracks, 0 signal vias; placement untouched (C36 home 63.75,73.75,0°; U18 home 3.0,72.4,90°).
- **Owner decisions:** **ONE RAISED.** `/home/aqroot8/.aqroot-autopilot-stop` is now PRESENT (OWNER_DECISION). This is the first owner decision since D-284; it is raised strictly because 003R exhausted the last bounded routing-only lever the policy named (CURRENT_STATE §5/§8, D-289).

---

## 0. Summary

D-289 localized the residual U18.8 `BAT_PROTECTED_P` escape as a **3-into-one-corner
placement-geometry mutual-exclusion** and named exactly one bounded routing-only lever
left untried: **vacate the contended pin (U18.7 → R81.2) off the single shared B lane
onto an inner layer** so U18.8 can reserve the corner alone. FBV2-P2-003R implemented
that lever (the D-290 WIP: `AQROOT_VACATE=U18_7` forcing U18.7 onto In2/In3 via an
ordinary 0.35/0.20 through via, tried FIRST, coupled with `AQROOT_U18_FIRST=1`
reserving U18.8 alone) and screened it on the cheap non-vacuous `AQROOT_LOCAL=D256`
west-prefix vehicle.

The lever is **REFUTED**, and the refutation is not "one implementation failed" — it is
**geometric and exact**. The candidate REGRESSES (conn 34 vs baseline 35, −1). The
off-layer vacate makes the conflict WORSE, not better, for a reason that is arithmetic
in the pad pitch and the clearance floor, and the third pin (U18.9) is lost to an
independent blocker no via-size/layer/direction/ordering choice reopens. No concrete
legal routing-only site survives.

Therefore the D-290 WIP is **retired** and the exact fallback D-289 named — a bounded
**LTC4368/R75 placement micro-ECO** (D-284/285 class) to open a *second* U18.8 escape —
is now a genuine **OWNER DECISION** per the standing policy trigger.

## 1. Both cheap-screen metrics, independently verified

Both `AQROOT_LOCAL=D256` runs completed naturally (no router process remained;
`DRIVER_EXIT` clean). Metrics re-read from the committed result JSONs:

| run | conn | skipped | ratsnest (Δ) | U18.7 | U18.8 | U18.9 | terminal FAIL |
|---|---|---|---|---|---|---|---|
| baseline (`phaseA_003r_baseline.json`) | **35** | 55 | 740 (−41) | **CLOSED** B.Cu 9.728 mm | OPEN `NO_VIA_SITE` | **CLOSED** In2 north hop | `BAT_RAW R89.1→(node)` trunk width |
| lever (`phaseA_003r_lever.json`) | **34** | 54 | 741 (−40) | **GATE_REJECTED** 0.250<0.300 | CLOSED reserved+In2 join | **NO_LEGAL_ESCAPE** | `LTC4368_FAULT_N U18.7→(node)` clearance |

The lever env (from `w/log_003r_lever.txt`) carried BOTH `AQROOT_VACATE=U18_7` and
`AQROOT_U18_FIRST=1`, so the off-layer vacate genuinely fired. Final DRC histogram is
identical in both runs (`{hole_clearance:5, lib_footprint_issues:199,
solder_mask_bridge:1, track_width:1, unconnected_items:499}`) because the terminal
violation was SURFACED and reverted, never absorbed. The lever trades the baseline's two
closed pins (U18.7 + U18.9) for one (U18.8): a **−1 regression**, FAIL.

## 2. The vacate genuinely fired and was genuinely refuted (not skipped)

The D-290 branch in `route_battery_block.py:main()` fires when
`(r is None or not r.get('ok')) and VACATE and not node and (net,a,b_) in VACATE`. The
`VACATE_SETS['U18_7']` key `(N+'LTC4368_FAULT_N','U18.7','R81.2')` matches the plan
branch verbatim (`battery_route_plan.py:95`), and the `-> R81.2` branch is a pad pair
(`node=False`), so the guard is satisfied. The block calls `QR.connect_hop(... far='I2')`
across the full width ladder, then `far='I3'`, reverting each failed attempt; on total
failure `r=None` and the branch falls through to the ordinary B.Cu ladder. The lever log
shows U18.7 → R81.2 reaching `GATE_REJECTED` (the B.Cu-ladder result) with no surviving
inner route — i.e. **both In2 and In3 hops were attempted and reverted.**

## 3. Why the inner vacate fails — geometry, not a rule and not a plane

- **In2/In3 are free signal layers, not planes.** The positive baseline scratch board
  (`w/Q003R_baseline/aqroot-Beta-v2.kicad_pcb`) carries filled zone polygons on **In1.Cu
  and In4.Cu only** — those are the plane layers. In2.Cu and In3.Cu have zero zone fill;
  In2.Cu carries 6 signal segments (the BAT_SENSE north hop + the LTC_SHDN diagonal),
  In3.Cu carries none. So an inner hop is not structurally barred by a plane, and
  control nets were "never barred from the inner layers" (`battery_route_plan.py:640`).
- **The blocker is the pad-exit zone, not the corridor.** U18's west-edge pins are on
  B.Cu at a **0.5 mm pitch** (U18.6 y=66.25 / U18.7 65.75 / U18.8 65.25 / U18.9 64.75 /
  U18.10 64.25, all x=5.9; verified from the footprint + the log via anchors at x≈4.6).
  U18.8 (65.25) sits physically BETWEEN U18.7 (65.75, escaping SOUTH to R81.2 at y=73.0)
  and U18.9 (64.75, escaping NORTH to R75.1). U18.8 → R75.2 (y=66.5) must cross U18.7's
  south-escape latitude. Every escape — B.Cu neck, inner via, or via-in-pad — must exit
  through this zone where the adjacent pin's committed copper is 0.5 mm away.

The arithmetic (reproduced in `checks/w/run_003r*` context; recomputed this task):

| escape geometry vs U18.8's committed corner copper | edge-to-edge gap | vs 0.300 floor |
|---|---|---|
| U18.7 B.Cu neck (0.15 w) ↔ U18.8 reserve-via (0.35) | `0.5 − 0.075 − 0.175 = ` **0.250 mm** | FAIL (== the measured DRC) |
| U18.7 vacate-via (0.35) ↔ U18.8 reserve-via (0.35) | `0.5 − 0.175 − 0.175 = ` **0.150 mm** | FAIL WORSE (why I2/I3 revert) |

The off-layer vacate replaces U18.7's 0.15 mm B.Cu neck (0.250 mm from U18.8's via) with
a 0.35 mm through-via pad (**0.150 mm** from U18.8's via) — it moves the escape transition
*closer* to U18.8, not away. The vacate cannot get its via out of the pad-exit zone
without violating the current-path clearance (D-269, 0.300 mm) by a wider margin than the
neck it replaces. This is why In2 AND In3 both revert: the failure is at the pad exit,
where the layer is irrelevant (a through via occupies all layers at that x,y).

## 4. No via-size lever rescues it, and U18.9 is an independent casualty

- **Smaller via is barred and insufficient.** To reach 0.300 mm vs a 0.15 mm neck a via
  must be ≤ 0.25 mm dia (== the floor, zero margin); to let two *adjacent* pins both via
  you would need sub-0.20 mm vias, below the D-257 ladder (a DRU change — BARRED). And
  D-257's reserve via "answers a via-geometry question only … never [dropped] to buy a
  corridor a legal width could not have" (`route_battery_block.py:1099-1104`); using the
  0.25 reserve via to *buy clearance* is precisely the barred use.
- **U18.9 is lost independently.** In the lever U18.9 returns `NO_LEGAL_ESCAPE … blocked
  by U18.10 (×25), U18.7 (×17), track (×15)`. The dominant blocker is U18.10, which no
  U18.7 vacate touches; so even a hypothetically successful U18.7 vacate would not reopen
  U18.9's north escape while U18.8 holds the corner. The west margin physically holds two
  simultaneous escapes of {U18.7, U18.8, U18.9}; a third requires more room, not more
  routing cleverness.

**Conclusion:** the pad-exit zone at 0.5 mm pitch cannot host three escape transitions of
{U18.7, U18.8, U18.9} under the 0.300 mm current-path clearance floor. Ordering (D-289),
off-layer vacate (D-290) and via-size are all refuted or barred. No concrete legal
routing-only site exists. This is an irreducible **placement-geometry** mutual-exclusion.

## 5. Why this IS now an owner decision (the policy trigger fired)

CURRENT_STATE §5/§8 and D-289 set the standing trigger verbatim: *"A genuine OWNER
DECISION — a bounded LTC4368/R75 placement micro-ECO (D-284/285 class) to open a second
U18.8 escape, or direction-2 corridor widening — arises only if 003R also fails to
co-close U18.7+U18.8+U18.9 without relaxing a floor/rule or moving a frozen part."* 003R
has now failed exactly that way, and it exhausted the last bounded routing-only lever the
policy named. The remaining levers all move a part (placement) — outside CTO scope. The
trigger is self-executing; this is not "declaring owner decision because one
implementation failed" — the refutation is geometric (§3–§4) and the policy pre-committed
this outcome.

## 6. Retirement (clean, provable)

Reverted to HEAD `9bd7aac`: `battery_route_plan.py` (the D-290 `VACATE_SETS` +
`PLAN_D266_*_U18FIRST`), `route_battery_block.py` (the D-290 vacate branch + `U18_FIRST`
plan swap), `phaseA_journal.json` (driver scratch churn). Committed as evidence of record:
`checks/phaseA_003r_baseline.json`, `checks/phaseA_003r_lever.json` (the two cheap-screen
metrics). Gitignored scratch (facts preserved, not committed):
`w/log_003r_baseline.txt`, `w/log_003r_lever.txt`, `w/run_003r_cheap.sh`,
`w/run_003r_lever.sh`, `w/Q003R_baseline/`, `w/Q003R_lever/`.

## 7. Integrity

No source, copper, placement or rule change survives this task (the D-290 lever is
retired). No DRC absorbed — the U18.7 clearance reject and U18.9 no-escape ARE the FAIL
reasons. Rule floors ENFORCED: 0.200 mm clearance, 0.25 mm hole-to-hole, ≥1.20 mm BPP
trunk, 0.60 mm BAT_MAIN, **0.300 mm current-path clearance (D-269)**. `c3_00` not
promoted; `place_003l` (D-285) preserved; D-275 and D-277..D-289 preserved; optional
`BAT_SENSE TP20.1` separate; frozen `beta-full-reference-v1` untouched; six-layer stack /
GND / netclasses / footprints / polarity / safety set frozen; `.aqroot-progress.env` NOT
edited. **NO PROGRESS EARNED: PCB routing stays 0 %, overall stays 74 %, readiness
~77 %.**

## 8. The owner decision (see `/home/aqroot8/.aqroot-autopilot-stop`)

**Options, engineering consequences, CTO recommendation** are recorded in the stop file.
In brief: (A) authorize a bounded LTC4368/R75 placement micro-ECO (D-284/285 class) to
open a *second, independent* U18.8 escape corridor so all three west-edge sense/control
pins escape without the 0.5 mm-pitch pad-exit contention — **CTO-recommended**; (B)
accept the board as-is with U18.8 open (NOT fabricable — trunk one pad short); (C)
direction-2 corridor widening / broader refloorplan (larger mechanical blast radius).
Autonomy is HALTED pending the owner's direction.
