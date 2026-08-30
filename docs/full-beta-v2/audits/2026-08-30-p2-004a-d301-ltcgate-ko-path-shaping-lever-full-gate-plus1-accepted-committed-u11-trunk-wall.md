# FBV2-P2-004A — D-301: the `AQROOT_LTCGATE_KO` path-shaping lever's full-authority gate CONFIRMED a GENUINE +1 (closes `LTC_GATE U18.10→Q3.4`, LOST 0, no new DRC) — so the minimum OFF-by-default lever + G15 are ACCEPTED and COMMITTED; copper is NOT promoted (full Phase-A still FAILs at the newly-exposed `U11.2` BPP trunk wall), autonomy CONTINUES

**Date:** 2026-08-30
**Milestone:** FBV2-P2-004A
**Decision:** D-301
**Class:** GOVERNED CTO ACCEPT + COMMIT + overall-run FAIL — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT). A normal Phase-A FAIL (a new terminal wall) is not a stop reason; the accepted lever is a bounded, reversible, OFF-by-default routing capacity gain within CTO authority.
**Starting HEAD:** `060a313` (D-300; pushed; `phaseA_journal.json` restored byte-identical at HEAD) carrying two uncommitted WIP files: the OFF-by-default `AQROOT_LTCGATE_KO` path-shaping lever in `checks/route_battery_block.py` (a `LTCGATE_KO` env-parse block + a scoped install/lift hook, plus a bulky in-run characterization probe `_ltcgate_probe` / `AQROOT_LTCGATE_PROBE`) and its **G15** contract in `checks/router_regression.py`. No router process live.
**Final state:** the bulky in-run probe (`_ltcgate_probe`, ~118 lines, and its `AQROOT_LTCGATE_PROBE` hook) is **pruned** — production WIP is reduced to the narrow accepted lever (the `LTCGATE_KO` parse + the scoped install/lift hook) + the G15 regression; both tracked files are **committed**. Lever **OFF by default → byte-identical** (G15). Authoritative PCB byte-identical to HEAD (`sha256 2235e273…d642d7e`, six layers, 0 tracks, 0 vias). The full-authority gate artifact, judge and scratch are gitignored (`checks/w/phaseA_003t_full_004a_ltcgate1.json`, `w/judge_004a.py`, `w/FULL003T_004a_ltcgate1/`, `w/TEST004A_*/`, `w/run_004a_*.log`).

---

## 1. What 004A was asked to do

Execute the D-300 handoff (§5): build ONE bounded, env-gated (OFF-by-default)
**path-shaping** lever (NOT a re-order — D-300 refuted ordering) that installs a
foreign keep-out over the rule-violating central lane of the `LTC_GATE U18.10→Q3.4`
join for exactly that one join (laid before the item, lifted right after, on the
proven `AQROOT_U19CAP` KO mechanism), forcing `connect_hop` onto the proven clean
west detour; then run the ~22-min full-authority gate with `AQROOT_U18BPP_JOIN=I3
AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1` (both prior accepted levers ON), and judge by
the full-run connected-set diff vs `w/phaseA_003t_full_003y2_u19cap.json` (D-299) and
`w/phaseA_003t_full_003w_u18bpp_i3.json` (D-297). Promote copper only on a genuine
full-authority Phase-A PASS (D-286). No DRU/rule change, no via below the D-257
ladder, no D-290 re-auth, no D-249/D-269 relaxation, no topology/footprint/outline
change.

## 2. The lever that was built and ACCEPTED (`AQROOT_LTCGATE_KO`, OFF → byte-identical)

A **path-shaping keep-out**, not an ordering change. `route_battery_block.py` parses
`AQROOT_LTCGATE_KO` into `LTCGATE_KO` — a list of `(layer, (x0,y0,x1,y1,hw))` keep-out
capsules in nm (`=1`/`AUTO`/`DEFAULT` → the validated default; an explicit
`LAYER:x0,y0,x1,y1,hw;…` string in mm overrides). Unset → `LTCGATE_KO == []`, no
keep-out installed, **byte-identical to every prior run**. In the section-8b queue
loop, guarded on `LTCGATE_KO` being non-empty AND the exact triple `(LTC_GATE,
U18.10, Q3.4)`, the capsules are installed as net-foreign `QR.SEG(...,'KO')` shapes
immediately before the join is routed and **lifted immediately after** — nothing else
on the board ever sees them.

**The validated default** seals the squeeze-gap just north of the `BAT_SENSE` 1.0 mm
current-path track `(2.8,62.05)-(5.4,62.05)` on **each far run layer** F/I2/I3 at
`(2.6,62.5)-(5.5,62.5)`, half-width 0.4 mm. The noKO `connect_hop` far run is the
diagonal `(5.15,64.75)→(5.15,63.6)→(2.25,60.7)→(1.9,60.7)`, which grazes that
`BAT_SENSE` track at ~`(3.59,62.04)` — the real `gate()` rejects it on **D-269 alone**
(clearance 0.2803 vs 0.300 mm, ~19.7 µm short; FINE_ESC legalises the D-257 via, so
there is **no** D-249 track_width violation in the real path — the audit's earlier
"0.20 mm D-249" was a raw-`connect_hop` probe artifact that bypassed FINE_ESC). With
the capsules, the hop is forced to cross **west** of the track's x=2.8 end and the
join routes F.Cu `(5.15,64.75)→(4.0,64.75)→(1.9,62.65)→(1.9,60.7)`, **8.556 mm**, with
`gate()` PASS and no new DRC.

Pinned OFF/ON + scoped by a **G15** regression contract in `router_regression.py`:
OFF by default (`LTCGATE_KO == []`, byte-identical); `=1` arms the validated default
(3 capsules on F/I2/I3 at the y=62.5 latitude spanning the BAT_SENSE x-extent);
an explicit `LAYER:x0,y0,x1,y1,hw` string parses; the lever is scoped to exactly
`LTC_GATE U18.10→Q3.4` with the KO lifted after the join.

**Pruning (per CTO ruling).** The 004A WIP also carried a ~118-line in-run
characterization probe `_ltcgate_probe` (+ its `AQROOT_LTCGATE_PROBE` hook) that
reproduced the real `connect_hop`/`run()`/`gate()` ladder with/without the KO at the
8b point. That was engineering evidence, not production routing; its findings are
recorded here and in the artifacts. It has been **removed** from tracked source — the
committed lever is the narrow `LTCGATE_KO` parse + the scoped install/lift hook only
(net WIP reduced from +242 to +124 lines across the two files).

## 3. The full-authority gate RAN and COMPLETED

The CTO completed the governing foreground run in a persistent terminal:

```
AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 \
  bash w/run_003t_full.sh 004a_ltcgate1 w/cand_003t/t_a_r77e15n10_r79e15n10.json
```

(direction-2 placement, both prior accepted levers ON) → `checks/w/phaseA_003t_full_004a_ltcgate1.json`
(secs **1500.2**, driver exited clean); the shared `phaseA_journal.json` was restored
**byte-identical to HEAD** afterward and **no process remains**. A genuine
full-authority artifact (not a proxy — D-286), judged by
`python3 w/judge_004a.py w/phaseA_003t_full_004a_ltcgate1.json`.

## 4. Verdict: a GENUINE +1 — `LTC_GATE U18.10→Q3.4` CLOSES, nothing lost

| metric | 004A (`LTCGATE_KO=1`) | 003Y2 baseline (D-299) |
|---|---|---|
| terminal fail | `U11.2 escape: none exists` | `LTC_GATE U18.10→Q3.4` (SIG) |
| connections | **73** | 72 |
| skipped-already-connected | 101 | 101 |
| ratsnest | **704 / −77** | 705 / −76 |
| journal length | **76** | 75 |
| final DRC | `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499}` | identical |

**Connected-set diff (004A vs 003Y2): GAINED 1, LOST 0** — exactly `LTC_GATE Q3.4↔U18.10`
(role SIG, layer F, 2 vias, `via_dia 0.35`, 8.556 mm). **Not a swap.** vs the 003W
(D-297) baseline: GAINED 3 (`LTC_GATE`, plus the two D-299 U19 pins `N_BATDIV
R89.2↔U19.6` and `REC_BAT_LOW (node)↔U19.7`), LOST 0 — so the accepted U18.8 / U19CAP
gains are **preserved** and the LTC_GATE close is purely additive.

- **LTC_GATE closed:** `U18.10→Q3.4` in the connected set = **True**; `LTC_GATE` is no
  longer in the terminal fail. The join routes on F.Cu with two 0.35/0.20 FINE_ESC
  vias (D-257 fine corridor applies) — no sub-0.50 non-fine via anywhere in the run
  (distinct via diameters 0.35/0.60/0.65/0.80).
- **No new DRC:** the final histogram is **identical** to 003Y2 (no new class, no
  increased count). D-249 and D-269 held; no rule relaxed.

The lever does exactly what it was designed to do, and the full gate — not a proxy —
confirms it. Per the D-286 discipline this is the promotable class of evidence, so the
lever is **ACCEPTED and COMMITTED** (banked env-gated / OFF-by-default, byte-identical
when unset, pinned by G15).

## 5. Why copper is NOT promoted — full Phase-A still FAILs at a NEW terminal wall

Copper promotes only on a **full-authority Phase-A PASS** (D-286). 004A is the **first
run in the whole arc to close every upstream wall** (west/BAT_RAW, U18.8 In3-join
D-297, the saturated U19 dead-cell field D-299, and now `LTC_GATE` D-301) and
therefore the **first to reach the final `u11_escape()` step**. That step now FAILs:

```
PHASE A: FAIL -- U11.2 escape: none exists
```

so the run FAILs and no copper is promoted. This is genuine forward progress — the
terminal wall advanced past the entire LTC_GATE field — but it is a FAIL, so
**readiness/progress are UNCHANGED** and the authoritative board stays six layers /
0 tracks / 0 vias.

## 6. The new terminal wall characterized sharply (`U11.2 escape: none exists`)

Measured from `checks/w/phaseA_003t_full_004a_ltcgate1.json`, `w/run_004a_full.log`,
the journal, and the authoritative board geometry — **no new long route was run.**

- **What fails:** `u11_escape()` (`route_battery_block.py:2149`) — the routine that lays
  the **U11.2 end of the `BAT_PROTECTED_P` high-current trunk**. It runs **LAST**, after
  all 73 queue connections. It escapes `D9.1` at `W_TRUNK_BPP = 1.50 mm`, flares `U11.2`
  (1.50 mm trunk → 0.20 mm SENSE neck), then `connect_role(launch → D9.1)` at 1.50 mm
  then 1.20 mm, then `gate()`. Any failure → revert → return False. Because the queue
  is drained and `u11_escape()` returns False, the no-progress check reports
  `U11.2 escape: none exists`.
- **The geometry (authoritative board):** `U11.2` pad = **(66.400, 78.200)** — inside
  the **east** `BAT_PROTECTED_P` node cluster (x 38–66, y 65–93); `D9.1` pad =
  **(11.350, 72.500)** — in the **west** control-copper mass. So `u11_escape()` is
  trying to lay a dedicated **~55 mm cross-board ≥1.20 mm B.Cu trunk** between the east
  node and the far-west D9.1 pad.
- **The rest of the BPP backbone is already connected** on the 004A board: `R75.2 →
  (stage)` TRUNK 14.458 mm F.Cu; the EARLY SOUTH BRIDGE lands at `C36.1`
  (traverse 70.925 mm, w 1.30); `C58.1 → D9.1` TAP 5.092 mm; and `C36.1 / C25.1 /
  C58.1 / D9.1` are all reported **"already joined via R75.2."** `U11.2` itself already
  has its thin **0.20 mm SENSE** escape into the node (5.525 mm, a Kelvin/sense tie,
  **not** a current path). What has **no legal path** is the dedicated **≥1.20 mm
  current trunk** from `U11.2`.
- **Why it fails:** the single central west↔east channel holds ≤~1.30 mm on the dense
  board (D-273/D-274 class), and it is **already occupied** by the south bridge
  (ywest 82.40) and the R75.2 trunk. A **second** parallel cross-board 1.50 mm trunk
  `U11.2 → D9.1` does not fit. This is **NOT** a ~20 µm DRC-rule pinch (unlike
  LTC_GATE); it is a genuine **≥1.20 mm-trunk NO_LEGAL_PATH** — the deepest, structural
  BPP trunk-width wall (the D-273/274/281/282/283 class), now exposed as the last
  Phase-A blocker.
- **The reducible observation (for 004B):** `U11.2` is **in** the east node, which is
  already on-net with `D9.1` via the bridge/R75.2 backbone. Forcing a fresh cross-board
  1.50 mm trunk to the **distant** `D9.1` is the expensive framing; the U11.2 current
  path can instead be a **short wide tap into the nearest already-connected ≥1.20 mm
  BPP node copper** (e.g. `C36.1` at (63.75,73.75), ~2.9 mm east), while D9.1↔node
  continuity is already carried by the bridge. That is the natural, bounded, CTO-scope
  next lever (§8).

## 7. Opportunity & Simplification Scan (D-301, LTC_GATE close / BPP trunk milestone)

Path-shaping is essentially **free, reversible, and BOM-neutral**; the scan checks
manufacturing / test / recovery / future-option impacts of the accepted lever and the
newly-exposed U11.2 wall.

- **A. Nearly-free capability added.** The accepted `AQROOT_LTCGATE_KO` lever closes the
  LTC4368 gate-drive join with **zero BOM/placement/rule impact**, OFF-by-default,
  byte-identical when unset. It banks a proven +1 in source that turns on for the
  eventual promotion run.
- **B. Complexity removed.** The bulky in-run probe was pruned from production source —
  evidence lives in the audit/artifacts, not the router.
- **C. Better implementation than the obvious one.** For the U11.2 wall, the obvious
  implementation (force a second cross-board 1.50 mm trunk) is what fails; the better
  implementation is a **short local tap** into the already-connected east node (§8).
- **D. BOM.** No opportunity — the LTC4368 + Q2/Q3 back-to-back-FET reverse-protection
  topology is frozen and correct; no add/remove/substitute closes a routing pinch.
- **E. Recoverability / testability / manufacturing / firmware / UX.** All unaffected by
  the accepted lever — a low-current internal control-net join with no
  footprint/outline/stackup/silk/firmware surface; `TP17` already covers the
  U18.10/R76.1 side. The U11.2 trunk is a **high-current safety-relevant net**, so 004B
  must preserve the ≥1.20 mm current path (no width waiver) — a whole-product
  (power/protection) constraint, not a free lever.
- **F. Future option (preserved).** The six-layer stack's bare inner signal layers
  In2/In3 remain spare capacity (the D-297 lesson) — a preserved vehicle if the U11.2
  tap corridor proves congested. Nothing is foreclosed.
- **Conclusion.** No product-capability or BOM opportunity justifies changing
  architecture; no irreversible cost, no strategic fork, no opportunity loss. **Open
  owner decisions: NONE.** The only deferred item is the *technical* 004B lever below,
  pursued under CTO autonomy.

## 8. Next task — FBV2-P2-004B (the `U11.2` BPP trunk-endpoint retarget lever)

Build ONE bounded, env-gated (OFF-by-default) lever that closes the `U11.2` end of the
`BAT_PROTECTED_P` high-current trunk **as a short wide tap into the nearest
already-connected ≥1.20 mm BPP node copper** (candidate: `C36.1` (63.75,73.75) or the
bridge landing / east-node trunk), instead of forcing the cross-board 1.50 mm
`u11_escape()` run to the distant `D9.1`. The tap must remain a legal **≥1.20 mm**
current path (D-249 / D-269 / 0.60 mm BAT_MAIN floors ENFORCED — no width waiver; this
is a high-current safety-relevant net). Keep the accepted `AQROOT_U18BPP_JOIN=I3`,
`AQROOT_U19CAP=1`, `AQROOT_LTCGATE_KO=1` levers ON. **Judge by the full-run
connected-set diff** vs `w/phaseA_003t_full_004a_ltcgate1.json`: the run must close the
`U11.2` trunk endpoint for a real net gain with no new DRC class and no lost
connection — and, critically, **verify the retarget preserves a valid high-current
path** (U11 load current still reaches the bulk-cap / protection output at ≥1.20 mm; a
short tap that leaves U11 fed only through the thin cap-via tie would be a functional
regression, not a gain). Do **not** trust a focused/post-hoc probe (the D-300 lesson).
Promote copper only on a genuine full-authority Phase-A PASS (D-286). **Fallback** (only
if no legal on-net tap sites the ≥1.20 mm path): a bounded immediate-neighbour placement
ECO to open a ≥1.20 mm `U11.2` corridor, re-screened with real full-placement DRC. If
the ≥1.20 mm trunk truly cannot be closed within CTO-scope routing/tap/bounded-ECO —
i.e. the D-281/282/283 western-corridor wall genuinely re-surfaces as unsolvable
without a topology/mechanical change — that would re-raise an OWNER decision; 004B must
first exhaust the bounded retarget within CTO authority.

## 9. Integrity / preservation

- Authoritative PCB **byte-identical to HEAD** (`sha256 2235e273…d642d7e`; six copper
  layers, 0 signal tracks, 0 signal vias; placement untouched). **No copper promoted;
  no DRC absorbed** — the U11.2 open is surfaced FAIL evidence on gitignored scratch,
  never in the authoritative board.
- `phaseA_journal.json` restored **byte-identical to HEAD**; **no process remains**.
- `router_regression.py` **ALL CHECKS PASS** (G9–G15; G15 verifies OFF-by-default
  byte-identical, the armed default, the explicit override parse, and the scoped
  install/lift).
- No via below the D-257 ladder; **D-269 (0.300 mm), ≥1.20 mm BPP trunk (D-249),
  0.60 mm BAT_MAIN** all ENFORCED; D-290 untouched; `place_003l` (D-285) and the
  D-275/D-288 bridge preserved; **D-275 and D-277..D-300 preserved**; frozen
  `beta-full-reference-v1` untouched.
- JLCPCB readiness **~77 %** unchanged (no copper promotion). Repo progress unchanged.
- Gitignored evidence preserved: `checks/w/phaseA_003t_full_004a_ltcgate1.json`,
  `w/judge_004a.py`, `w/FULL003T_004a_ltcgate1/`, `w/TEST004A_base/`, `w/TEST004A_ko1/`,
  `w/run_004a_base.log`, `w/run_004a_ko1.log`, `w/run_004a_full.log`,
  `w/run_004a_probe.sh`.
