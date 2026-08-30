# FBV2-P2-003U / D-295 — The two D-294 walls are FULL-RUN-EMERGENT ordering/congestion casualties (no cheap vehicle judges either at the direction-2 placement); the PRIMARY (U19.7) is REDUCIBLE-in-principle with an exact mechanism and a bounded escape-reservation lever, but the governing ~22-min full gate cannot run foreground here → precise CTO handoff, no promotion

**Date:** 2026-08-30
**Task:** FBV2-P2-003U
**Decision:** D-295
**Starting HEAD:** `36662db` (D-294; clean, `phaseA_journal.json` at HEAD)
**Class:** GOVERNED CHARACTERIZATION / NO-PROGRESS + HANDOFF milestone — autonomy CONTINUES (a normal Phase-A FAIL is not a stop reason; no owner decision is raised).
**Result:** The bounded full-context reservation/ordering corridor study D-294 defined was executed. Both 003T walls are proven **full-run-emergent ordering/congestion casualties** at the D-293 direction-2 placement, and **no cheap vehicle judges either one** (the U19 dead-cell field is placement-independent for cheap vehicles, so it cannot reproduce the direction-2-induced layer flip that boxes U19.7; the R80 focused vehicle reported `fail=None` / U18.8 JOIN ok — i.e. vacuous — where the full run FAILs). The **PRIMARY** wall (`REC_BAT_LOW U19.7`) is now diagnosed EXACTLY and shown **reducible in principle** — U19.7 escaped cleanly in the committed 003O baseline; direction-2's +2-connection congestion swapped `VREC_VCC U19.8`'s pad-escape from B.Cu onto F.Cu, consuming the F corridor U19.7 needs, so U19.7 (a greedy-tightest-first casualty and, as a `(node)` join, ineligible for the D-278 inner hop) is left open. The **SECONDARY** wall (U18.8 I2 join corridor) is a full-congestion I2 pinch between the two placed reserve vias. Both bounded levers (escape-reservation for U19.7; reserve-via siting/ordering on I2 for U18.8) require the **~22-min governing full authority gate** to judge, and that gate cannot be run foreground under the ACP 10-min single-call cap with no backgrounding permitted. Per the 003U operating discipline this is delivered as a **precise CTO handoff**: exact diagnosis, exact lever design with code hooks, and the exact ready-to-run full-authority command. No source/copper/placement/rule change; no DRC absorbed; no promotion. Authoritative PCB byte-identical to HEAD (`sha256 2235e273…d642d7e`); `phaseA_journal.json` at HEAD; D-269 enforced at 0.300 mm; D-290 closed; D-275/D-288 and all floors preserved.

---

## A — What D-294 asked, and the hard environment constraint that shaped 003U

D-294 (§5 / CURRENT_STATE §5) defined FBV2-P2-003U as a bounded full-context
reservation-and-ordering corridor study of the two 003T walls at the D-293
direction-2 placement (`t_a_r77e15n10_r79e15n10`): **(1, PRIMARY)** reserve
`REC_BAT_LOW U19.7`'s escape before its neighbor pins U19.8/U19.5 and/or re-route
the six blocking tracks (escape-ordering, no DRU change); **(2, SECONDARY)** study
the U18.8/U18.9 I2 reserve-via siting/ordering to open a ≥0.200 mm join corridor
within D-257/D-266 mechanics — without re-authorizing D-290, dropping any via below
the D-257 ladder, weakening D-269, or changing topology/footprint/outline; and
judge advancement/promotion **only** by the complete full-authority run.

**The binding constraint.** Prior full Phase-A runs take ~1300–1780 s (003T full =
1313.8 s, 003O = 1776.5 s). The ACP exec wrapper has a 10-minute single-call cap,
and 003U's operating discipline BARS `&`/`nohup`/detached/tracked jobs, `Monitor`,
and scheduled wakeups — foreground-owned work only. Therefore the governing full
gate cannot be run inside this task. The discipline anticipates exactly this: do
the cheap bounded characterization first, and if a full route must be run, STOP
before launching it and deliver a precise ready-to-run handoff. That is this
milestone.

## B — The decisive cheap evidence: the connected-set diff 003O → 003T (no long re-run)

Judging Phase-A changes by the full-run connected-set diff (memory
`fbv2-p2-focused-vehicle-vacuity`) needs no new long run — the two committed/scratch
full-run journals already carry it. Diffing `checks/phaseA_003o_b1_r75rot_cto.json`
(003O baseline, conn 67) against `checks/w/phaseA_003t_full_e15n10cto.json` (003T
direction-2, conn 69) at U19 is decisive:

| U19 pin (net) | 003O escape | 003T escape |
|---|---|---|
| U19.1 `REC_POL_OK`→Q6.1 | B.Cu 11.148 | B.Cu 11.148 |
| U19.2 `REF_POL`←TP24.1 | F 8.61 | F 8.727 |
| U19.3 `N_POL`←TP23.1 | **B.Cu** 6.118 | **I2** 6.118 |
| U19.5 `REF_HO`←R91.2 | **F** 12.269 | **I2** 12.05 |
| U19.6 `N_BATDIV`←R89.2 | **B.Cu 10.151 (escaped)** | **— (not via this route)** |
| U19.7 `REC_BAT_LOW`→Q7.1 | **F 14.907 (ESCAPED)** | **OPEN — `NO_LEGAL_ESCAPE`** |
| U19.8 `VREC_VCC`→C60.1 | **B.Cu 2.689, 0 vias** | **F 3.857, 2 vias** |

**In 003O all seven U19 pins escaped, U19.7 among them** (`REC_BAT_LOW U19.7→Q7.1`,
14.907 mm on F.Cu). Direction-2 moves nothing near U19 (U19 @ 2.695,28.255,0°;
Q7/R93 unmoved), so **U19's escape geometry is identical between 003O and 003T** —
the wall is not geometric. What changed is the **global routing order/layer
assignment** the +2-connection congestion produced:

- **The exact trigger — a VREC_VCC layer swap.** `VREC_VCC` has two segments,
  `U19.8→C60.1` (the pad escape) and `C60.1→R84.2`. In 003O they are B.Cu(0 via) /
  F(2 via); in 003T they **swap** to F(2 via) / B.Cu(0 via). So in 003T U19.8's
  pad-escape occupies the F.Cu lane immediately south of U19.7, which in 003O was
  free and carried U19.7→Q7.1. `U19.8` (×26) is duly the dominant blocker the FAIL
  names, with `U19.6` (×13), `U19.5` (×7) and track (×6).
- **U19.7 is then a greedy-tightest-first casualty.** The driver already re-measures
  `order_tight` before **every** fine-pitch pin (`route_battery_block.py:2169-2181`,
  PR-32), so this is NOT a stale-slack-table bug. It is the inherent limit of
  tightest-first: at the head of the U19 pass U19.7 has a WIDE escape (its neighbors
  are unrouted), so it sorts LATE; its neighbors route first and consume its lane;
  when its turn comes it is re-measured with **no** legal escape. `REC_BAT_LOW` then
  routes `Q7.1→R93.1` first (journal step 51) and U19.7 falls through to the closure
  stage as `U19.7→(node)` (PR-24), which FAILs.
- **The D-278 inner hop cannot rescue it.** `hop_first`/D-278 (`route_battery_block.py:1039`)
  is guarded by `and not node`, so a `(node)` join — which is what U19.7 becomes —
  is ineligible for the off-layer escape that would sidestep the box.

**This is a reducible, ordering-class wall** (U19.7 demonstrably escapes when the
order/layer assignment leaves the F lane free, as 003O proves), NOT a
placement-geometry mutual-exclusion in the D-289/D-290/D-292 class.

## C — Why NO cheap vehicle judges the U19.7 lever (vacuity, proven not assumed)

- `AQROOT_LOCAL=DEADCELL` (~2 min) routes only the dead-cell network and **omits
  the west prefix / BAT_RAW divider field** whose +2-connection congestion is the
  entire cause of the VREC_VCC layer swap (memory `fbv2-p2-focused-vehicle-vacuity`).
  It is also **placement-independent** (direction-2 moves nothing DEADCELL routes),
  so it produces the same result at home / 003O / 003T and structurally **cannot**
  reproduce the direction-2-induced box.
- `AQROOT_LOCAL=U19` keeps the whole prefix + dead-cell field (it can reproduce the
  emergent dead-cell blockers) but **lays the whole prefix**, so it is ~15–20 min —
  over the 10-min foreground cap.
- `AQROOT_LOCAL=R80`/`D256` are west-margin-only and never route U19.

So the only faithful judge of the U19.7 lever is the full authority gate. There is
**no sub-10-min faithful vehicle**; a DEADCELL run would be a vacuous smoke test.

## D — The SECONDARY wall: U18.8 I2 join corridor (full-congestion pinch, also vacuous cheaply)

At the direction-2 placement (U18 north +1.25 → 8.0,66.5,180°) the west-3-corner is
resolved and **both** inner reserve vias place on I2 (003T journal): step 5
`BAT_SENSE U18.9→R75.1 RESERVE_PAIR` ok, step 6 `BAT_PROTECTED_P U18.8→R75.2
RESERVE_PAIR` ok, and step 26 `BAT_SENSE U18.9→R75.1 JOIN` ok — **U18.9 joins**. But
`U18.8→R75.2` JOIN FAILs `NO_PATH` ("no I2 corridor at 0.200 mm between the two
reserved vias") then fallback `NO_VIA_SITE` (no 0.65 mm B via). Measured reserve vias
on the routed board (`w/FULL003T_e15n10cto/…kicad_pcb`): `BAT_PROTECTED_P` 0.35/0.20
at (2.8,66.8) & (7.2,66.5); `BAT_SENSE` 0.35/0.20 at (4.25,63.5) & (4.6,66.0). The
failure is not the via **centres** touching (nearest reserve-via pair ≈1.97 mm) but
that the U18.8→R75.2 **join track** cannot thread a ≥0.200 mm lane on I2 between the
U18.9-Kelvin reserve stub, the U18.8-BPP reserve stub and the surrounding
full-congestion I2 copper.

**Vacuity, proven.** The 003T R80 focused screen reported `t_a_r77e15n10_r79e15n10`
conn 20, `fail=None`, **U18.8 JOIN ok** — the very candidate that FAILs U18.8 on the
full run. The focused vehicle omits the congestion that pinches I2, so it cannot
judge this wall either. Bounded lever: reserve-via **siting/ordering** on I2 (D-257/
D-266 mechanics) to open ≥0.200 mm — without dropping any via below the D-257 ladder
(a DRU change, BARRED), without the D-290 off-layer vacate (BARRED), without
weakening D-269 or changing topology/footprint/outline. Full-gate-only to judge; if
the corridor cannot open at this placement without relaxing a floor, that is a
bounded finding (it does not, by itself, re-raise an owner decision).

## E — VERDICT: bounded, reducible, full-gate-only → handoff, not promotion, not owner decision

Both walls are **bounded full-context routing/ordering casualties** — no floor
relaxed, no frozen part moved, D-290 untouched, D-269 enforced. The PRIMARY is
reducible in principle with an exact mechanism (§B) and a bounded escape-reservation
lever (§F); the SECONDARY is a reserve-via-siting question (§D). Neither is judgeable
by any cheap vehicle at the direction-2 placement, and the governing ~22-min full
gate cannot run foreground here. Per D-286 no proxy evidence promotes copper, so
**nothing is promoted**; per the 003U discipline this is a **governed CTO
characterization / NO-PROGRESS + HANDOFF**, NOT an owner decision (direction-2
remains authorized and is not exhausted). Autonomy CONTINUES; the stop file stays
ABSENT.

## F — Handoff to FBV2-P2-003V (CTO authority; implement the bounded lever, then run the full gate)

The next task implements ONE narrowly-scoped, env-gated (OFF by default), bounded
lever and validates it against `router_regression.py` (authoritative behavior must
stay byte-identical), then runs the FULL authority gate — the only faithful judge.

- **PRIMARY lever (U19.7 escape reservation).** Reserve `REC_BAT_LOW U19.7`'s escape
  **before** its east-row neighbors route, so the F lane it needs to reach `Q7.1` is
  not consumed by `VREC_VCC U19.8`'s pad-escape. Concrete hooks: (i) add a bounded
  U19-pin escape-reservation pass in the reserve_escape family
  (`route_battery_block.py:647-729`), scoped to the dead-cell `tight='U19'` group, so
  the SOT-23-8 pins reserve their pad exits before the field routes (mirror of the
  D-266 Kelvin reservation for a fine-pitch pin field); and/or (ii) relax the D-278
  `and not node` guard (`:1039`) for the `tight='U19'` group so a boxed U19 pin whose
  connection retargets to `(node)` can still take the ordinary 0.35/0.20 inner hop
  (D-257 preferred, no rule relaxed) instead of horse-shoeing/failing; and/or
  (iii) hold `VREC_VCC U19.8`'s pad-escape on B.Cu (its 003O layer) so U19.7 keeps
  the F corridor. All are escape-ordering/reservation levers within existing
  reservation mechanics — **no DRU change**.
- **SECONDARY lever (U18.8 I2 reserve-via siting).** Re-site/re-order the U18.8 and
  U18.9 I2 reserve vias so the U18.8→R75.2 join has a ≥0.200 mm I2 lane, within
  D-257/D-266 mechanics — no via below the D-257 ladder, no D-290 vacate, no D-269/
  topology/footprint/outline change.
- **The exact governing full-authority run (CTO executes in a persistent terminal):**
  ```bash
  cd /home/aqroot8/aqroot/hardware/beta-v2/checks
  cp phaseA_journal.json /tmp/phaseA_journal.HEAD.json      # back up the SHARED journal
  export AQROOT_U19_RESV=1        # (the 003V lever env gate, once implemented)
  bash w/run_003t_full.sh 003v_u19resv w/cand_003t/t_a_r77e15n10_r79e15n10.json
  #   -> writes w/phaseA_003t_full_003v_u19resv.json  (~22 min, DRIVER_EXIT=0)
  cp /tmp/phaseA_journal.HEAD.json phaseA_journal.json      # restore the SHARED journal
  ```
  `w/run_003t_full.sh` already carries the full governed recipe (SIXLAYER, ECO_002F,
  D256=GSQ, Q3_POFV, D266, D267=F1, TRUNK_LAST, U18_ORDER=6,10,7,1,3,2, D279, D280,
  D270=BRIDGES, BRIDGE_EARLY, BRIDGE_SOUTH, ECO_EXTRA=place_003l.json, PLACE_JSON=the
  direction-2 candidate, LOCAL unset = full authority). **Judge by the full-run
  connected-set diff vs `phaseA_003o_b1_r75rot_cto.json` and
  `w/phaseA_003t_full_e15n10cto.json`**: the lever advances only if U19.7 joins (and,
  for the secondary, U18.8 joins) with connections up and no new DRC class. Promote
  copper only on a genuine full-authority PASS (D-286).

## G — Integrity

- **Authoritative PCB byte-identical to HEAD** (`sha256 2235e273…d642d7e`): six copper
  layers, 0 signal tracks, 0 signal vias; placement at home (C36 63.75,73.75,0°; U18
  3.0,72.4,90°). No copper promoted.
- **No source/copper/placement/rule change.** `route_battery_block.py`,
  `battery_route_plan.py`, `phaseA_journal.json` and all driver/DRU/footprint/netclass
  source are byte-identical to HEAD (`git diff --stat HEAD` empty for these). The two
  003V levers are DESIGNED here, not implemented — the tree stays clean; only docs and
  this audit change.
- **`phaseA_journal.json` at HEAD** (driver never invoked this task; the 003T scratch
  full run was read-only for the connected-set diff).
- **No DRC absorbed** — the U18.8 open, the U19.7 no-escape and the lone scratch
  `via_dangling:1` are surfaced FAIL evidence on gitignored scratch, never in the
  authoritative board. **No promotion.** `place_003l` (D-285), the D-275/D-288 bridge,
  D-275 and D-277..D-294 all preserved; frozen `beta-full-reference-v1` untouched;
  `JLCPCB_READINESS` unchanged. D-269 enforced at 0.300 mm; D-290 stays closed;
  0.200 mm / 0.25 mm / ≥1.20 mm BPP / 0.60 mm BAT_MAIN floors ENFORCED.
- **Stop file** `/home/aqroot8/.aqroot-autopilot-stop` **ABSENT** — a bounded
  full-context routing/ordering FAIL is not a stop reason; the persistent CTO resumes
  one-Claude-at-a-time engineering with FBV2-P2-003V (run the handoff).
- **Evidence read (no new long run):** committed `checks/phaseA_003o_b1_r75rot_cto.json`;
  gitignored scratch `checks/w/phaseA_003t_full_e15n10cto.json`,
  `w/FULL003T_e15n10cto/aqroot-Beta-v2.kicad_pcb`, `w/cand_003t/t_a_r77e15n10_r79e15n10.json`,
  `w/run_003t_full.sh`.

**NO PROGRESS EARNED: PCB routing 0 %, overall 74 %, readiness ~77 %.**
