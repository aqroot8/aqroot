# FBV2-P2-003D — transcript: the driver-integrated vacate + F.Cu bridge is a measured reproducible FAIL

**Date:** 2026-08-28 · **Starting HEAD:** `b3a7e65` (verified: `HEAD ==
origin/master`; worktree carried only the uncommitted 003D artifacts + the
`phaseA_journal.json` scratch churn). Full narrative in
[`audits/2026-08-28-p2-003d-d276-driver-bridge-fail.md`](../audits/2026-08-28-p2-003d-d276-driver-bridge-fail.md).

This transcript records the D-276 closeout: 003D integrated the proven 003C
vacate + F.Cu via-array bridge into the production Phase-A driver and drove it
through a full 2-pass route — and the full-driver route **reproducibly fails.**

## What was done, in order

1. **Recovered context** from the source of truth — `CTO_DECISIONS.md`
   D-269…D-275, the 003A/003B/003C audits, the routing harness
   (`route_battery_block.py`, the `bridge_*_003c` proven primitives), and the
   uncommitted 003D work (`bridge_eco_003d.py`, `bridge_gates_003d.py`,
   `bridge_probe_003d.py`, and the `phaseA_003d*` results/logs).

2. **Validated the ecoC / ecoD evidence without re-running Phase A.** The two
   full driver passes are not byte-identical — they differ only in per-net
   wall-clock `secs` jitter — but every decisive measurement is identical:
   Phase-A `fail = N_POL U19.3→(node) NO_LEGAL_ESCAPE` (blockers `board_edge ×23,
   U19.4 ×16, U19.2 ×12, U19.6 ×8`); `connections 68`; `skipped 91`; `ratsnest
   710`, `Δ −71`; DRC `hole_clearance 5 / lib_footprint_issues 199 /
   solder_mask_bridge 1 / unconnected_items 499`; and the bridge ECO
   `ok:false — no ≥ 1.20 mm F.Cu traverse corridor` (`vacated 6`, `existing_vias
   48`). Both logs end on the same `ECO ABORT` + `PHASE A: FAIL` lines. The base
   `phaseA_003d.json` (no ECO) shows the same U19.3 fail — the failure is upstream
   of the bridge ECO.

3. **Diagnosed the orchestration loss.** The ecoC/ecoD passes (PIDs 274901 /
   274902) were launched `nohup setsid … &` from a one-shot turn that then ended
   with a normal text response — no `sessions_yield`, no persistent waiter, no
   completion callback. The children finished at 04:31 UTC and wrote correct
   results, but a process exit cannot re-awaken an already-ended turn, and the
   finalize ACP session had ended at the wait boundary. Continuation/orchestration
   loss — not engineering, not OWNER. Repair discipline recorded: ACP owns
   foreground work and returns a completion event; CTO uses `sessions_yield` and
   resumes from it; no unregistered detached child batches.

4. **Restored / cleaned the worktree.** `phaseA_journal.json` scratch churn
   restored to HEAD. Audited `route_battery_block.py`: the only change is a
   single `AQROOT_BRIDGE_ECO`-guarded hook that is inert by default — kept, as it
   is what reproduces 003D. The incomplete `log_phaseA003d_ecoA.txt` / `ecoB.txt`
   (422 lines, no verdict, no result JSON — killed earlier passes) removed as
   scratch.

5. **Converted `bridge_probe_003d.py` into an honest FAIL-pinning regression.** As
   authored it presumed a passing driver gate (`bridge_gates_003d_*.json` with
   `pr40_eco == 111111111`) that never existed. Rewritten: A the hook is wired and
   ordered; B the ECO single-sources the D-275 primitives/constants from
   `bridge_route_003c`; C the vacate is cardinality-1 / control-role only; D each
   `phaseA_003d_eco*.json` records the measured FAIL (ECO abort + N_POL U19.3
   NO_LEGAL_ESCAPE) and **no false promotion**; E 2-pass determinism of the FAIL.
   **PASS.**

## The verdict

003D is a **measured reproducible FAIL** of production / full-driver promotion.
The proven 003C mechanism is not wrong; the production driver does not arrive at
the state where it applies — it fails earlier at **U19.3 pad escape**, and the
western F.Cu corridor is not open on the driver's own routed board. **003C /
D-275 is NOT invalidated** — its post-processed reproducible `BAT_PROTECTED_P`
closure stays the fixed proven solution for 003E. Not an owner decision.

## State

Authoritative PCB UNCHANGED — six copper layers, 0 signal tracks, 0 signal vias,
no KiCad source mutated. All suites PASS and unregressed: `router_regression`
G1–G11, `bridge_probe_003d` (rewritten), `bridge_probe_003c`, `via_array_probe`,
`d264/d266/d267/d269/d270_probe`, `dru_probe`, `netclass_probe`. `c3_00` NOT
promoted; D-249…D-275 untouched; no safety weakening, no topology/net change, no
authoritative promotion. U19.3 is the new named blocker; Phase A NOT passed;
Phase B NOT run. B-34 unchanged. **No progress earned: PCB routing stays 0 %,
overall stays 74 %.** Next: **FBV2-P2-003E** — a bounded investigation of the
U19.3 `N_POL` NO_LEGAL_ESCAPE (pad-escape geometry vs route-order/copper
obstruction vs minimum placement ECO), holding the proven 003C vacate + F.Cu
4-via bridge fixed.
