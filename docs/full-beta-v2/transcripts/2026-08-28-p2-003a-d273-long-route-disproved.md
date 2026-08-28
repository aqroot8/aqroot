# FBV2-P2-003A — transcript: disproving the long outer-B.Cu zero-via route

**Date:** 2026-08-28 · **Starting HEAD:** `1a82652` (verified: `HEAD ==
origin/master`, worktree carried only the uncommitted 003A artifacts + the
`phaseA_journal.json` scratch churn). Full narrative in
[`audits/2026-08-28-p2-003a-d273-long-route-disproved.md`](../audits/2026-08-28-p2-003a-d273-long-route-disproved.md).

This transcript records the independent validation behind D-273: the closeout of
the reservation-dependent LONG outer-B.Cu route that D-272 named as the next
technical step.

## The evidence, validated

1. **Recovered context** from the repository source of truth — `CTO_DECISIONS.md`
   D-270…D-272, the CHANGELOG/PROGRESS 002Z entries, and the D-272 audit — then
   read every uncommitted 003A artifact.

2. **Re-ran the c3 reproduction chain, confirmed internally consistent.** The
   parent board `w/c3repro003a_parent/aqroot-Beta-v2.kicad_pcb` is the AUTHORITATIVE
   placement + the pinned `c3_00.json` recipe driven through `run_prefix_002z.py`.
   `result_c3repro003a_parent.json` (`applied/asserted=true`, `mismatch=false`,
   `targets="111111101"`, `u18=8`, `u18_open=[]`, `sense_mm=13.811`, `returncode=0`)
   and `probe_c3repro003a_parent.json` (`BAT_PROTECTED_P R75.2->U11.2 = false`)
   match the D-272 `c3_e10n_r79` numbers exactly. The board 003A measures is the
   proven-8/8, trunk-open board — not a new placement.

3. **Validated the geometry / coverage argument** with the three read-only
   helpers (no routing, no copper):
   - `inspect_003a.py` — `R75.2` (2.800, 67.963); node copper one large B.Cu
     cluster x 38.48…66.40 (L≈89.6 mm); D9 reservation free end (10.800, 73.000);
     western BPP copper a separate small cluster x 0.60…5.22.
   - `occ_003a.py` — the B.Cu occupancy map shows `R75.2` embedded deep in the
     western copper mass and **exactly one connected central free channel**
     (x ≈ 13…38 mm) between the western margin and the node's west edge. The
     channel is not the discriminator; the escape latitude is. This is the basis
     for the four-family dedup: three thinnest latitudes (north/mid/south) + the
     D9 reservation's own exit.
   - `joins_003a.py` — the exact nearest node-copper join per channel exit.

4. **Re-ran the bounded probe** `long_corridor_003a_bounded.py` end-to-end and
   **reproduced `long_corridor_003a_bounded.json` byte-identically** (only the
   board-path string and wall-clock `dt` differ). Control `R75.2→D9.1`: @1.50
   NO_LEGAL_ESCAPE, @1.20 NO_PATH. F1/F2/F3/F4: **ALL FAIL both widths** — @1.50
   `R75.2` NO_LEGAL_ESCAPE (cannot leave its pad at 1.5 mm), @1.20 escapes ~2.7 mm
   then COARSE_BLOCKED; F4 COARSE_BLOCKED both. `bounded families with a legal
   B.Cu long corridor: NONE`.

5. **Corroborated the COARSE_BLOCKED verdict with the router's own primitive.** A
   0.25 mm coarse grid can over-block, so I did not accept COARSE_BLOCKED as
   proof on its own. `long_corridor_003a_corrob.py` runs the SAME `QR.connect_role`
   the router uses for the trunk, `R75.2` → four node-copper points, at the
   **default FULL budgets (ASTAR=500000, WAVE=3000)**, no coarse prefilter, 120 s
   per-trial cap. `long_corridor_003a_corrob.json` — **all 8 trials FAIL**: @1.50
   NO_LEGAL_ESCAPE (0.0 s, target-independent), @1.20 NO_PATH after a **48–62 s
   reachable-region exhaustion** (not a timeout). The long route is disproved by
   the router's own search, not just by a coarse gate. This is a legitimate
   measured FAIL — no analytic or virtual result is presented as a routed PASS.

## The deliverable set, and what was dropped

- **Kept, tracked:** `long_corridor_003a_bounded.py` (deliverable probe),
  `long_corridor_003a_corrob.py` (full-budget corroboration),
  `place_002z/{inspect,occ,joins}_003a.py` (read-only geometry evidence),
  `place_002z/long_corridor_003a_bounded.json`, `place_002z/long_corridor_003a_corrob.json`,
  `place_002z/manifest_003a.json`, and the parent reproduction triple
  `place_002z/{result,probe,log}_c3repro003a_parent.{json,txt}`.
- **Kept deliberately:** `long_corridor_003a.py`, the naive un-bounded first
  draft, as the documented rejected approach — it is what motivated the bounded
  redesign (its first east trial burned > 18 min, rc130) and is named by the two
  scripts that replace it. Repo convention keeps a rejected approach reproducible.
- **Restored:** `phaseA_journal.json` (parent scratch churn) to its HEAD state.
- **Not mutated:** no KiCad source; the authoritative PCB is byte-for-byte HEAD.

## Regression

`router_regression.py` **G11** pins the D-273 bounded-search contract on the
authoritative board (the c3 scratch board is not committed): a tiny budget must
BOUND the search (prompt NO_PATH, no copper, no raise); the probe budget
(ASTAR=60000 / WAVE=1200) must NOT fabricate a FAIL (still routes a routable
short trunk). Budgets saved/restored; no rule changed. **4/4 PASS.**

## Suites — exact outcomes

- `router_regression.py` — **ALL CHECKS PASS**, G1–G9 + G10 + **G11** (exit 0).
- `d264_probe` `d266_probe` `d267_probe` `d269_probe` `d270_probe` `dru_probe`
  `netclass_probe` — all **exit 0**.

## Result

The long outer-B.Cu zero-via route for `BAT_PROTECTED_P` is **disproved at target
1.50 mm and floor 1.20 mm** — a measured FAIL, corroborated at full budgets.
`c3_00` remains evidence only, not promoted. The authoritative PCB is unchanged.
This is **not an owner decision**; the next technical task is a **bounded
named-path F.Cu high-current via-bridge investigation** (evidence-based via-array
sizing + full safety / DRC / connectivity gates), which is not touched in 003A.
B-34 remains open; U19 / converters / Phase A / Phase B not started. No progress
earned: PCB routing stays 0 %, overall stays 74 %.
