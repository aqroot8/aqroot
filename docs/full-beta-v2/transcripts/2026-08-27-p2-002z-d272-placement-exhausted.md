# FBV2-P2-002Z — transcript: closing out the western-margin placement scope

**Date:** 2026-08-27 · **Starting HEAD:** `016aeee` (verified clean; no router
processes active). Full narrative in
[`audits/2026-08-27-p2-002z-d272-placement-exhausted.md`](../audits/2026-08-27-p2-002z-d272-placement-exhausted.md).

This transcript records the closeout validation of the parent-supervised
cardinality search behind D-272.

## The evidence, validated

1. **Read the closeout and all c1/c2/c3/c4 evidence** in
   `hardware/beta-v2/checks/place_002z/`. The cardinality ladder is internally
   consistent across aggregates, per-run result/log/probe triples, prefilter
   reports and `D272_closeout.json`:
   - **baseline** — `b1_u18ctrl` (U18 authoritative pose alone): U18 **6/8**,
     open `U18.7`+`U18.8`.
   - **c1** — `cardinality1_aggregate.json`, 6 poses, ceiling **7/8**
     (`b1_r75rot`); no single move lands all of {7,8,2}.
   - **c2** — `cardinality2_aggregate.json`, 5 supervised runs, ceiling **7/8**,
     target bit 8 (`BAT_PROTECTED_P R75.2→U11.2`) **FALSE in all five**. Analytic
     cross-check: `trunk_150=None` and `trunk_120=None` on all five poses, matching
     the real router's NO_LEGAL_ESCAPE / NO_PATH.
   - **c3** — `cardinality3_aggregate.json`, 4 supervised runs. `c3_e10n_r79`
     (`c3_00`) is the **first reproducible U18 8/8** (open none): `result_c3_e10n_r79.json`
     shows `u18=8`, `u18_open=[]`, `targets="111111101"`, `ledger="7/29"`,
     `sense_mm=13.811`, `applied/asserted=true`, `mismatch=false`, `returncode=0`;
     `probe_c3_e10n_r79.json` confirms `BAT_PROTECTED_P R75.2->U11.2 = false`. The
     other three runs are 7/8. Unique lever: e10n + R79 east widens the analytic
     B.Cu trunk 0.40 → 0.80 mm (`c3_prefilter_report.json`), still sub-floor.
   - **c4** — `c4_prefilter.json`: 705 poses swept (13 card-2 + 89 card-3 fan-8),
     102 fan-8 mech-clean rows, `best_overall_trunk_w=400000` (0.40 mm),
     `n_winners_ge_floor=0`. `c4_index.json` is `[]` by design (no ≥1.20 mm
     candidate → no real-router batch emitted).

2. **Confirmed the parent-supervised c2/c3 result/log/probe files are present and
   consistent** — 11 c1/c2 + 4 c3 = 15 each of `result_*.json`, `log_*.txt`,
   `probe_*.json`, matching the aggregates and `run_manifest_c3.json`.

## Suites (re-run at this commit)

    $ python3 router_regression.py
    router_regression: ALL CHECKS PASS        # G1–G9 and the new G10 (4/4)
      PASS G10 DRC transient path is process-unique and reclaimed
      PASS G10 concurrent same-tag DRC does not clobber the transient   rcs=[0, 0] both clean
      PASS G10 both concurrent runs read the authoritative baseline histogram
      PASS G10 no DRC transient left behind in shared WORK

    $ for p in d264 d266 d267 d269 d270 dru netclass; do python3 ${p}_probe.py; done
    d264_probe EXIT=0   d266_probe EXIT=0   d267_probe EXIT=0   d269_probe EXIT=0
    d270_probe EXIT=0   dru_probe  EXIT=0   netclass_probe EXIT=0

## Board state

    $ python3 -c 'import pcbnew; b=pcbnew.LoadBoard(".../aqroot-Beta-v2.kicad_pcb"); ...'
    copper_layers=6 signal_tracks=0 arcs=0 vias=0
    $ git diff --quiet -- hardware/beta-v2/kicad/  ->  kicad/ tree: UNMODIFIED vs HEAD

## Housekeeping

- **`phaseA_journal.json`** — restored to HEAD (`git checkout`); its diff was
  scratch churn (timing `secs` deltas + one scratch `RESERVE_RUN` entry) written by
  a search run, not evidence.
- **`run_*.out`** — dropped from `place_002z/`. They were transient driver stdout
  (`START <epoch>` markers for c2; duplicates of `result_*.json` for b1). No repo
  convention tracks `.out` files; the audit evidence is the result/log/probe triple.

## Verdict

PLACEMENT-SCOPE CLOSEOUT. No legal fan-8 placement makes the analytic western BPP
trunk reach even 0.80 mm or closes `BAT_PROTECTED_P R75.2→U11.2`; the west margin
is saturated in the plane, not along a length. `c3_00` is carried forward as
evidence only, not promoted. This supersedes D-271's owner-escalation framing:
bounded placement was CTO authority and is exhausted; the next technical task is a
long outer B.Cu route proof (reservation-dependent, zero current-carrying vias;
~2.29× resistance / ~18.9 mW at 1.5 A to verify), with the F.Cu high-current via
bridge a deferred, unauthorized fallback. Authoritative PCB untouched. B-34 open.
