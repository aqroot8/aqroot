# FBV2-P2-002Y — transcript: resolving the 002W reproduction gap

**Date:** 2026-08-27 · **Starting HEAD:** `8725eea` (verified clean).

This transcript records the measurements behind D-271. Full narrative in
[`audits/2026-08-27-p2-002y-reproduction.md`](../audits/2026-08-27-p2-002y-reproduction.md).

## The investigation, step by step

1. **Confirmed the reported drift.** Ran the D-266/D-267 recipe at HEAD; `U18.8`
   reserved at **(3.000, 71.600)** "shortest" (scored, no retry), `U18.7`
   NO_LEGAL_ESCAPE — as FBV2-P2-002X reported. But my first run used
   `AQROOT_ECO_002F=1` and put `U18.8`'s via at (7.200, 65.250) — a wholly
   different board.

2. **Found the placement trap.** `placement_fingerprint.py` on the on-disk 002X
   board `w/X0`: `U18@3.000,72.400`, **"vs AUTHORITATIVE MATCH"**. On the scratch
   the ECO run left: `U18@8.000,65.250`, **"vs ECO_002F MATCH"**. The two differ
   in nine parts (`U18`, `R76..R83`). `RU.fresh` copies AUTHORITATIVE;
   `AQROOT_ECO_002F` silently swaps it. Re-ran WITHOUT `ECO_002F`:
   `U18.8` → **(3.000, 71.600)**, matching `w/X0`'s reserved via read straight
   from the board with pcbnew. Reproduction achieved.

3. **Ruled out D-269 as the cause.** Ran the same recipe at commit `6ebb009`
   (002U) and `798d0ae` (002T, dropping `D267`): `U18.8` → **(3.000, 71.600)** at
   both. The pre-D-269 code selects the same site. `git diff 798d0ae..HEAD`
   shows `reserve_escape` byte-identical; `PLAN_D266_RESERVE` byte-identical
   across all four commits. Not a clearance interaction; not tie-break; not state
   leakage (`fresh` rebuilds from AUTHORITATIVE each run).

4. **Swept every stage-0 flag** (`Q3_POFV` on/off, `D267` on/F1/F2, `KELVIN_FIRST`):
   `U18.8` stays **(3.000, 71.600)** in every case. The site is robust.

5. **Forced (3.750, 71.600).** `free=True`, but the reservation is GATE_REJECTED —
   `{"solder_mask_bridge":1,"shorting_items":1,"clearance":1}` — and `U18.7` stays
   blocked. The historical site is DRC-illegal on this board.

6. **Instrumented sibling sealing (`SEAL-DBG`).** `U18.8` has exactly ONE via
   candidate, (3.000, 71.600), and it **seals no sibling at reservation time**.
   `U18.7` is sealed later, cumulatively.

7. **Traced the copper.** `BAT_SENSE Q3.6→R75.1` routes **18.200 mm** (vs the 002T
   audit's 13.532 mm), an east-bulging **diagonal wall (6.75,62.45)→(2.80,66.40)**
   — the current-carrying path 002X named. `R75.2`'s reserved via lands at
   (2.800, 63.200) here vs the 002T audit's (1.200, 65.700). Two different
   margins; the committed code reproduces the 18.200 mm one at every commit.

## The pinned deterministic result

    PLACEMENT ASSERTED: AUTHORITATIVE   (U18@3.000,72.400)
    RESERVED BAT_SENSE       U18.9 -> R75.1   shortest vias I2 @ U18.9(3.500,69.000)
    RESERVED BAT_PROTECTED_P U18.8 -> R75.2   shortest vias I2 @ U18.8(3.000,71.600)
    TRUNK    BAT_SENSE       Q3.6  -> R75.1   18.200 mm  w=1.00  B.Cu
    PR-40 PROBE  targets 111010111  U18 6/8   open U18 pins: U18.7, U18.8

Pinned in `hardware/beta-v2/checks/prefix_002w.py` (`RECIPE` +
`AQROOT_EXPECT_PLACEMENT=AUTHORITATIVE`) and `prefix_002w_manifest.json`.

## Verdict

DECISION STOP. The prefix is deterministic and self-describing; the governed 8/8
board is not reconstructible from committed code; the western margin is
oversubscribed at the current-carrying `BAT_SENSE` role, one pad west of the
trunk. No routing code or rule changed; authoritative PCB untouched. Owner
decision required (protection architecture, or a placement change).
