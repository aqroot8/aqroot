# FBV2-P2-003I — transcript: the route-order EARLY landing of the proven D-275 bridge is a MEASURED, REPRODUCIBLE FAIL — the bridge and the current-carrying corridor users (`LTC_GATE`/`BAT_RAW` tap, `GND` pour, `BAT_MAIN`) contend for one ~9 mm western corridor, so re-timing changes only WHICH high-current user fails, not WHETHER one fails; closed as FAIL, no authoritative promotion, D-275 and D-277..D-280 preserved, topology/capacity fix deferred to FBV2-P2-003J

**Date:** 2026-08-28 · **Starting HEAD:** `f4dfe3f` (verified clean, `HEAD ==
origin/master` at start). Full narrative in
[`audits/2026-08-28-p2-003i-d281-early-bridge-fail.md`](../audits/2026-08-28-p2-003i-d281-early-bridge-fail.md).

This transcript records the D-281 CLOSEOUT: validation of the parent-supervised
early-bridge full run as a MEASURED FAIL, the cheap reproduction of the decisive
resource-contention root cause, the honest rewrite of the standing probe, the
cleanup of the misleading incomplete scratch, the regression fleet, and the
definition of FBV2-P2-003J. No long full route was re-run — the parent CTO
supervised the definitive run to the point where the conflict became decisive and
stopped it as invalid.

## What was done, in order

1. **Verified start state.** `HEAD == origin/master == f4dfe3f`. Dirty worktree from
   the interrupted 003I work: `route_battery_block.py` (the env-gated
   `AQROOT_BRIDGE_EARLY` stage) and the clobbered per-run `phaseA_journal.json`
   modified; untracked `bridge_early_003i.py`, `bridge_probe_003i.py`; scratch
   `w/FIX003I` (the interrupted full run's partial board) and the clobbered journal.

2. **Read the source-of-truth.** CTO_DECISIONS D-275/D-277..D-280, the 003H
   transcript/audit, the driver diff, and both new modules. Confirmed the mechanism:
   `apply_early` lays the EXACT D-275 bridge (single-sourced from
   `bridge_route_003c`) at the first stage-8 item, in the proven-sparse window, then
   restores the driver's via-blind obstacle model.

3. **Reproduced the decisive conflict cheaply — no full rerun.** Ran the preflight
   probe: on the interrupted partial board (`FIX003I`) it read confusing FAILs (the
   board is an incomplete artifact, not a clean end-state). On the committed dense
   board (`FIX003H3`) the root cause is clean and reproducible: the western corridor
   carries 15 through-vias, the ≥ 1.20 mm via-AWARE traverse **NO_PATHs** while the
   copper-only traverse **PATHs** — the wall is via density in ONE shared corridor.
   The early bridge lays legally on a reconstructed sparse placed board (entry 4,
   traverse 1.50 mm, exit 4, no new DRC). The measured full-run figures from the
   parent (`GND` 0.0726, `BAT_MAIN` 0.125 vs 0.200; `BAT_RAW` NO_VIA_SITE) show the
   downstream corridor users fail once the bridge occupies the box first.

4. **Ruled it a MEASURED FAIL.** The early landing is necessary-but-not-sufficient:
   it lays, but it steals the corridor the taps need. This is the exact symmetric
   corollary of 003D's end-of-run abort — one corridor, two mutually-exclusive
   high-current users; route ORDER decides which fails, not whether one fails.
   Timing is not the lever; the corridor lacks CAPACITY for both. Closed 003I as
   FAIL, D-281, no authoritative promotion; D-275 and D-277..D-280 preserved.

5. **Cleaned the misleading incomplete scratch; restored the journal.** Removed
   `w/FIX003I` (the interrupted partial board — it honestly pins no result and was
   even being mis-read by the probe as a "completed board"). Restored
   `phaseA_journal.json` to HEAD (`git checkout`). Kept only honest evidence: the
   committed dense board `FIX003H3`, the reconstructed sparse-board reproduction the
   probe regenerates deterministically, and the recorded measured figures.

6. **Rewrote the standing probe honestly (`bridge_probe_003i.py`).** Replaced the
   earlier fix-advocacy framing with a MEASURED-FAIL RECORD (clauses A/B/C/E/F):
   A precondition met; B via-density root cause on `FIX003H3`; C D-275 invariant
   preserved; E early bridge lays on the sparse board (NECESSARY only); F the
   measured downstream FAIL, candidate REJECTED, and NO false promotion (no
   `phaseA_003i_fix.json` claims a clean/absorbed end-state; authoritative PCB
   0-track/0-via). Probe PASS.

7. **Ran the regression fleet (no long route).** `bridge_probe_003i` PASS;
   `router_regression` ALL CHECKS G1–G11 (D-280 off) PASS; `bridge_probe_003c` PASS
   (003C/D-275 held fixed); `bridge_probe_003d` PASS; `u19_escape_probe_003e` (D-277),
   `003f` (D-278), `003g` (D-279), `003h` (D-280) all PASS.

8. **Wrote the docs and defined the next task.** CTO_DECISIONS D-281 row, CHANGELOG,
   PROGRESS, the audit, and this transcript. Defined **FBV2-P2-003J** — a
   topology/capacity solution for the shared western corridor (widen/add a corridor,
   relocate the `LTC_GATE`/`BAT_RAW` taps out of the box, or re-plan so bridge and
   taps do not contend), preserving D-275 geometry and the D-277..D-280 closures
   without weakening clearance or any product/electrical requirement.

## What was NOT done

- No long full production route was re-run — the parent CTO supervised the
  definitive early-bridge run and stopped it once the two clearance violations +
  NO_VIA_SITE made it a decisive, invalid candidate. **The clearance violations were
  NOT absorbed/refreshed into the baseline** (that would waive real safety
  violations). No authoritative copper, no placement ECO, no part moved, no
  topology/net/footprint/polarity/safety change, no six-layer/GND change, no
  netclass/width/clearance/hole-to-hole relaxation (the 0.200 mm and 0.25 mm floors
  ENFORCED). `c3_00` NOT promoted. `bridge_probe_003c/003d` behaviour preserved.
  Phase A NOT passed (the D-275 BPP bridge is not integrated into the production
  run); Phase B NOT run. `/home/aqroot8/.aqroot-progress.env` untouched — a failed
  candidate earns no readiness; the CTO owns the readiness review. No OWNER decision
  exists or was made — 003I and 003J are engineering scope within CTO authority.

## Artifacts committed

- `route_battery_block.py` — the env-gated (`AQROOT_BRIDGE_EARLY`) EARLY route-order
  bridge stage (off by default; disables the `AQROOT_BRIDGE_ECO` end-of-run
  duplicate when set). Default behaviour byte-unchanged.
- `bridge_early_003i.py` — the EARLY route-order driver stage (the FAIL reproducer).
- `bridge_probe_003i.py` — the standing measured-FAIL record (A/B/C/E/F).
- Audit, CTO_DECISIONS D-281 row, CHANGELOG, PROGRESS, this transcript.
- Restored `phaseA_journal.json` to HEAD; removed the misleading `w/FIX003I` scratch.
