# FBV2-P2-003G — transcript: the dead-cell resistor-field congestion is an antisocial B.Cu detour; a route-time layer hop closes both named blockers net-positively and rotates one casualty (N_BATDIV C61.1) to 003H

**Date:** 2026-08-28 · **Starting HEAD:** `3fc55e4` (verified clean, `HEAD ==
origin/master` at start). Full narrative in
[`audits/2026-08-28-p2-003g-d279-deadcell-field-hop.md`](../audits/2026-08-28-p2-003g-d279-deadcell-field-hop.md).

This transcript records the D-279 closeout: a bounded A→B→C investigation of the
D-278 next blockers `VBRIDGE_TOP R85.1→D10.1` and `REF_HO R92.1↔R93.2`, a measured
minimum routing repair that closes both on a full production run, and the honest
tracking of the one functional casualty it rotates (`N_BATDIV C61.1` → 003H).

## What was done, in order

1. **Verified start state.** `HEAD == origin/master == 3fc55e4`, clean worktree.
   Read the source-of-truth docs (D-275/D-277/D-278 rows, the 003F audit, the
   memory) and the driver (`route_battery_block.py` `order_tight`/`run_once`,
   `qrouter.py` `escape`/`obstacles`/`connect_role`/`connect_hop`,
   `battery_route_plan.py` dead-cell plan).

2. **Cause (A) refuted — cheapest probe first.** Empty-board `qb.escape(...)`:
   R85.1 = 8, D10.1 = 7, R92.1 = 8, R93.2 = 8 ways at ≥ 0.150 mm. Intrinsic
   geometry is not the blocker.

3. **Ran the committed `AQROOT_LOCAL=DEADCELL` bounded prefix (no full run
   first).** It ROUTES both victims (R85.1, R93.2) — its `BAT_RAW` field taps
   fail for lack of any `BAT_RAW` copper (the west divider is skipped), so the
   field copper that boxes R85.1 is never laid. Conclusion: these two blockers,
   unlike D-278's U19.8, are **full-run emergent**; the bounded prefix cannot
   reproduce them.

4. **Attributed on the real routed baseline board.** Ran ONE full baseline
   (D-279 off), which reproduced `phaseA_003f_fix.json` exactly (68 conn,
   ratsnest 710/−71, identical DRC). Segment attribution: R85.1 `blocked by track
   ×49, R85.2 ×7, R86.1 ×7, R86.2 ×5` — the connection `N_POL R85.2→R86.1` routes
   6.23 mm for a 2.48 mm span (2.5×) as a B.Cu horseshoe boxing R85.1; R93.2
   `blocked by track ×46 …` — REC_GATE_N wrapping it plus the antisocial
   `REC_BAT_LOW Q7.1→R93.1` (23.1 mm / 3.1×). Remove-tests: deleting the N_POL box
   near R85.1 restores it 0 → 7; deleting REC_GATE_N + REC_BAT_LOW near R93.2
   restores it 0 → 8. On the empty board those same connections route DIRECT and
   are harmless (N_POL R85.2→R86.1 = 2.52 mm, R85.1 stays 7) — **the aggressor is
   the DETOUR**, the general case of D-278's single crossing pin.

5. **Implemented the minimum repair (D-279, env-gated).** In `run_once`, a
   dead-cell-class SIG B.Cu route whose copper came back > `D279_K` × its
   straight-line pad span AND > `D279_MIN_MM` (2.0 / 5.0 mm) is reverted and
   re-routed as an ordinary 0.35/0.20 through-via hop (D-257 preferred, no rule
   relaxed), inner signal layer (In2/In3) first so a local field detour leaves
   outer F.Cu clear, kept only if the hop is legal and strictly shorter. Scoped
   away from every wide/high-current net, TRUNK/TAP role, node target, and any
   route within 2× of its span. `AQROOT_D279` unset reproduces pre-003G exactly.

6. **Ran the full integrated production validation in the foreground (owned by
   this task).** Recipe = the pinned D-271 production recipe (SIXLAYER, c3_00
   asserted, D256=GSQ, Q3_POFV, D266, D267=F1, TRUNK_LAST, U18_ORDER=6,10,7,1,3,2,
   LOCAL empty, no BRIDGE_ECO) **plus `AQROOT_D279=1`**. Two connections hopped
   onto In2.Cu (`N_POL R85.2→R86.1` 6.2 → 4.5 mm, `REC_BAT_LOW Q7.1→R93.1`
   23.1 → 9.4 mm) and **both victims routed**: `VBRIDGE_TOP R85.1→D10.1` and
   `REF_HO R92.1→R93.2`. Aggregate: connections 68 → 69, ratsnest 710/−71 →
   709/−72 (one better), in-scope nets connected 23 → 24 of 29, DRC histogram
   identical to baseline, `bridge_eco null`. Exactly three nets changed.

7. **Tracked the casualty honestly.** The coupled field rotates ONE casualty onto
   `N_BATDIV C61.1→U19.6` — a functional bypass cap (not a test point), a
   pre-existing hyper-marginal 46 mm cross-board hop whose landing via co-locates
   with `U19.6→R89.2`'s via and survives baseline only by ~25 µm; robust across an
   F.Cu-first and the adopted inner-first hop variant (identical aggregate), so a
   genuine field coupling. Net +2 named functional closures − 1 functional
   casualty = +1. Deferred to 003H, not claimed closed.

8. **Regression + closeout.** New `u19_escape_probe_003g.py` (A/B/C/D/E) PASS;
   `u19_escape_probe_003f`/`003e` (D-278/D-277 intact) PASS; `router_regression`
   all checks G1–G11 PASS (D-279 off); `bridge_probe_003c` PASS (003C/D-275 held
   fixed); `bridge_probe_003d` PASS. Restored `phaseA_journal.json` scratch to
   HEAD; scratch `w/` dirs are gitignored.

## What was NOT done

- No authoritative copper, no placement ECO, no part moved, no topology/net/
  footprint/polarity/safety change, no six-layer/GND change, no netclass/width/
  clearance/hole-to-hole relaxation. `c3_00` NOT promoted. `bridge_probe_003c/003d`
  behaviour preserved. Phase A NOT passed (the held-fixed 003C BPP bridge and the
  C61.1 rotation remain); Phase B NOT run. `/home/aqroot8/.aqroot-progress.env`
  untouched — the CTO performs the readiness review after accepting this pushed
  milestone. The repair is **not regression-free** (it rotates C61.1); it is
  reported as a net-positive measured advance, not a clean close, and D-279 is
  kept env-gated (proven, part of the 003G recipe, not adopted into the default).

## Artifacts committed

- `route_battery_block.py` — the env-gated D-279 antisocial-detour layer hop in
  `run_once` plus its `AQROOT_D279` / `D279_K` / `D279_MIN_MM` config.
- `u19_escape_probe_003g.py` — the D-279 standing probe.
- `phaseA_003g_base.json` — the full baseline (D-279 off; reproduces 003F).
- `phaseA_003g_fix.json` — the full fix (D-279 on; both victims routed).
- Audit, CTO_DECISIONS D-279 row, CHANGELOG, PROGRESS, this transcript.
