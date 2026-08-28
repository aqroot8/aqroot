# FBV2-P2-003B — transcript: disproving the bounded F.Cu high-current via bridge

**Date:** 2026-08-28 · **Starting HEAD:** `624f085` (verified: `HEAD ==
origin/master`; worktree carried only the uncommitted 003B artifacts + the
`phaseA_journal.json` scratch churn). Full narrative in
[`audits/2026-08-28-p2-003b-d274-fcu-bridge-disproved.md`](../audits/2026-08-28-p2-003b-d274-fcu-bridge-disproved.md).

This transcript records the investigation behind D-274: the bounded named-path
F.Cu high-current via bridge that D-273 named as the next technical step.

## What was done, in order

1. **Recovered context** from the repository source of truth — `CTO_DECISIONS.md`
   D-249/D-264/D-267/D-269/D-270/D-273, the 002Z and 003A audits, the routing
   harness (`route_battery_block.py`, `qrouter.py`, `path_role_dru.py`,
   `battery_route_plan.py`), the c3_00 recipe and the D9 reservation mechanism.

2. **Reproduced the pinned c3_00 prefix.** `run_prefix_002z.py
   place_002z/c3_00.json c3repro003b` → `result_c3repro003b.json`:
   `applied/asserted=true`, `mismatch=false`, `targets="111111101"`, `u18=8`,
   `u18_open=[]`, `ledger="7/29"`, `sense_mm=13.811`, `returncode=0` —
   byte-consistent with D-273. The D9.1 current-escape reservation (F1 staging,
   B end (10.800, 73.000), 0 via) and the U18.8/U18.9 Kelvin joins are present as
   recorded. The one open connection is bit 8 `BAT_PROTECTED_P R75.2→U11.2`.

3. **Established the exact islands** with KiCad `GetConnectedItems`: the TARGET
   island is `{D9.1, C25.1, C36.1, U11.2}` (D9.1 already tied to U11.2 through the
   C25/C36 F.Cu cap copper by two SINGLE 0.80/0.40 vias at (11.35, 71.3) and
   (60.6, 65.0)); the SOURCE island is `{R75.2, U18.8}` — a 1.14 mm B.Cu stub at
   x = 2.80. Bit 8 is open only because these two islands are ~8 mm apart. The
   original `NO_VIA_SITE` on `R75.2→(stage)` was a full-trunk-width B.Cu escape
   failure, not an absence of via room.

4. **Derived the via-array sizing** (`via_array_003b.py` → `via_array_003b.json`)
   from the board's own IPC-2221B method, calibrated by reproducing the DRU's
   BAT_MAIN outer 0.525 mm exactly. A 0.40/25 µm through-via barrel as an internal
   FR4 conductor carries 1.055 A at a 10 K rise (conservative — no plane-cooling
   credit). For the 1.75 A validation case: ideal-sharing needs 2, the
   fault-tolerant floor is 3 (3.17 A; lose one open via → 2.11 A > 1.75 A), the
   design target is 4 (hottest via +6.5 K under 2:1 imbalance). Flagged UNVERIFIED:
   the 25 µm plating (JLC typical, not a fab traveller).

5. **Measured the three bridge pieces** (`bridge_geom_003b.py`,
   `bridge_feasibility_003b.py` → `bridge_feasibility_003b.json`; QBoard models a
   through via as copper on every layer with GND pours auto-antipadded):
   - **ENTRY feasible** — a 4-via array fits on R75.2's 1.225 × 3.35 mm B.Cu pad
     at 0.9 mm pitch, all copper layers clear; F.Cu is empty within 3.5 mm.
     Via-in-pad on a sense-resistor pad → plated-over-filled vias (D-258 POFV).
   - **EXIT feasible** — 4-via arrays land on the node (527 free sites at x = 38.5;
     855 at x = 45) and a 3-via array on the D9 reservation stub.
   - **TRAVERSE impossible at ≥ 1.20 mm** — an F.Cu full-width flood from R75.2
     dies at x = 4.80 mm (@1.50 4.65, @1.00 4.95, @0.80 11.6; island west edge
     x = 10.05), and a full-budget A* (the router's own `QBoard.search`)
     R75.2 → node returns NO_PATH at both 1.20 and 1.50 mm, by exhausting the
     small reachable F.Cu region in 0.5–0.6 s. The blocker is the western
     control-net F.Cu congestion: the LTC_GATE x = 5.75 vertical, the
     BAT_PROT_SHDN_CTL diagonal, and the BAT_RAW y = 72.45 run, in the
     x 4.8…11 / y 66…73 window. The 0.80 mm escape is recorded, not used — it is
     below the mandatory 1.20 mm trunk floor, which this task may not waive.

6. **Added a generalized regression** — `via_array_probe.py` pins the via-array
   sizing contract and REJECTS undersized (single-/two-via) transitions (the
   electrical half of the bridge guard); the overbroad/bounding-box/foreign-net
   geometric half is already carried by `dru_probe`'s `corridor_checks`. **PASS.**

## The verdict

The bridge is disproved at the F.Cu traverse: the two via arrays exist, but no
≥ 1.20 mm F.Cu corridor joins them. Combined with D-273, the western margin
cannot host a ≥ 1.20 mm high-current trunk on either outer layer — the saturation
is in the plane, on both faces. The CTO recommendation is a bounded
western-corridor control-net vacate ECO (CTO/engineering scope, the D-270 class),
not an owner call.

## State

Authoritative PCB UNCHANGED — six copper layers, 0 signal tracks, 0 signal vias,
no KiCad source mutated. All suites PASS and unregressed: `router_regression`
G1–G11, `via_array_probe` (new), `d264/d266/d267/d269/d270_probe`, `dru_probe`,
`netclass_probe`. `phaseA_journal.json` scratch churn restored. `c3_00` NOT
promoted. D-249, D-264, D-266, D-267, D-269, D-270, D-271, D-272, D-273 untouched.
U19 NOT searched; Phase A/B NOT run. B-34 REMAINS OPEN. No progress earned: PCB
routing stays 0 %, overall stays 74 %.
