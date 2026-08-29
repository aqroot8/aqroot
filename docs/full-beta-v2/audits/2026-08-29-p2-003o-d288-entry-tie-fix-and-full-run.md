# FBV2-P2-003O — D-288: the D-275 south-bridge ENTRY-array two-layer tie is FIXED (rotation-aware in-pad POFV scan + symmetric B.Cu tie-stub) and proven `via_dangling`-clean by a non-vacuous regression AND a natural-completion CTO full run — but the full Phase-A run still FAILs on genuinely NEW downstream blockers (U18.8 BAT_PROTECTED_P escape + a terminal REF_POL/R87 corridor), so the bridge-code fix is accepted/committed with NO routing/overall progress and NO readiness change

**Date:** 2026-08-29 · **Task:** FBV2-P2-003O · **Starting HEAD:** `9172470`
**Verdict:** **BRIDGE ENTRY-TIE FIX = ACCEPTED & COMMITTED (the D-287 dangling defect is
resolved; entry array electrically tied on two layers, `via_dangling == 0`). OVERALL
PHASE-A RUN = FAIL on NEW downstream blockers. CTO ENGINEERING FAIL, NO OWNER DECISION,
NO AUTHORITATIVE PROMOTION.**

A successful **bridge-implementation fix** is distinct from an **overall Phase-A pass**.
003O closed the exact D-287 lever (the entry array dangled on one layer); the natural-run
proves it — the D-287 `via_dangling` cascade is GONE, the south bridge now passes
BOTH geometrically AND electrically, and the `BAT_PROTECTED_P` island closes R75.2 through
seven pads. But the full run still FAILs, now on **new, downstream, genuinely-different**
blockers the entry dangling had shadowed. No copper and no placement are promoted. The
authoritative PCB stays **six copper layers, 0 signal tracks, 0 signal vias**, placement
untouched. Every rule floor (0.200 mm clearance, 0.25 mm hole-to-hole, ≥1.20 mm BPP trunk,
0.60 mm BAT_MAIN) is ENFORCED, not relaxed; no DRC absorbed. D-275 and D-277..D-287 are
preserved. **No routing % earned** (PCB routing stays 0 %, overall 74 %, JLCPCB readiness
~77 %) — only scratch evidence and tooling improved.

---

## 1. What 003O was asked to do

D-287 exhausted the bounded direction-1 placement space (27/27) and refuted all three
hard-gate survivors at ONE placement-independent electrical fault: the D-275 south-bridge
**ENTRY array on R75.2** was bussed on F.Cu with **no symmetric B.Cu tie-stub**, so its
vias landed ~0.5–1.15 mm NORTH of R75.2's B.Cu pad and dangled on one layer
(`via_dangling 4/4/2`). 003O (CTO scope) was to **fix the entry-array two-layer tie** so
the entry vias are electrically connected (`via_dangling == 0`), symmetric to the proven
exit array — with **no rule/floor/topology/footprint/net change and no absorption** —
verify with `screen_003n.py --bridge`, then take the best survivor `b1_r75rot` into a
parent-supervised full Phase-A run and close `BAT_PROTECTED_P`.

## 2. The fix — minimal, two parts, both in the bridge code

**(A) Root-cause: a rotation-aware, in-pad POFV entry scan (`bridge_route_003c.scan_entry_sites`).**
The prior scan windowed on the pad's **UNROTATED** `hx/hy` half-sizes and accepted any
`point_free` site, then sorted "south-first". R75 is rotated −90°, so the raw `hx/hy`
window was the WRONG shape (tall-narrow instead of wide-short) and the "south-first" sort
actually picked the **NORTHERNMOST** sites — off the pad, over bare substrate. The fix
adds `_in_pad(shp, x, y, margin)`, which transforms `(x,y)` into the pad's **own rotated
frame** and requires the site centre to sit inside the pad rectangle inset by
`IN_PAD_MARGIN = 0.20 mm`; the scan now walks the pad's **rotation-aware AABB**
(`shp.bbox`) and sorts **centre-out**. `point_free` (clearance to FOREIGN copper) and
`hole_clear` still apply unchanged. Result: every entry via barrel genuinely overlaps
R75.2's B.Cu pad copper.

**(B) A symmetric B.Cu tie-stub (`stage_bridge` + `bridge_early_003i.apply_early`).**
After laying the entry vias and the F.Cu bus, each entry via now also gets an explicit
**B.Cu tie-stub from the via to R75.2's pad centre** (`qb.track(NET,'B', x,y, rpx,rpy,
W_LAND)`) — the exact mirror of the exit array's `_lay_landing` B.Cu stub. So each entry
via is tied on **two layers**: the F.Cu bus unites the via tops into the trunk, the B.Cu
stub joins the via bottom to R75.2's pad copper. Belt-and-suspenders with (A): even if a
site sits near the pad edge, the B.Cu stub guarantees the ≥2-layer connection.

No rule, floor, topology, net, footprint, width, or layer-stack change; no driver/router/
DRU mutation.

## 3. The D-288 regression is NON-VACUOUS (`screen_003n.py --bridge --validate`, GREEN)

`entry_tie_regression` pins the fix with two controls on the same `b1_r75rot` D-286
placed board:

- **NEGATIVE control** — reproduce the D-287 asymmetric entry array (4 vias at the
  MEASURED off-pad sites `LEGACY_ENTRY_SITES` + an F.Cu bus, **NO** B.Cu stub). It **MUST
  dangle**: measured **`via_dangling +4`** — proving the defect is real and KiCad's
  connectivity test genuinely catches it. The fix therefore cannot pass vacuously.
- **POSITIVE control** — the real fixed bridge (`bridge_probe` → `apply_early`: in-pad
  POFV entry vias + F.Cu bus + explicit B.Cu tie-stubs): **CONNECTED, `via_dangling == 0`,
  entry 4, exit 4, ywest 82.4, traverse w 1.30 mm**; the geometric floors hold.
- **NO-ABSORPTION delta** — vs the IDENTICAL no-bridge placed board, the fixed bridge adds
  **ZERO** new hard-class DRC (shorting/clearance/hole/courtyard delta 0). The bridge
  introduces no genuine violations that could have been swept under a baseline.

`screen_003n.py --bridge --validate` exits **0** (all three assertions GREEN). This
replaces the D-287 `--validate` (which asserted `b1_r75rot` FAIL with dangling) — the same
DRC that used to flag the defect now clears the fixed bridge and still flags the legacy
array.

## 4. The natural-completion CTO full run (`b1_r75rot`, `DRIVER_EXIT=0`)

Recipe: the governed parent-supervised full Phase-A run on `b1_r75rot` (`place_003l` +
`AQROOT_BRIDGE_EARLY/SOUTH`, corrected D-286 harness), ran SYNCHRONOUSLY to natural
completion under the persistent CTO. Evidence of record (pinned, committed):
`checks/phaseA_003o_b1_r75rot_cto.json`; scratch log `checks/w/log_003o_b1_r75rot_cto.txt`
(gitignored). `DRIVER_EXIT=0`, **secs 1776.5**, PHASE A **FAIL**, connections **67**,
skipped-already-connected **99**, ratsnest **781 → 708 (−73)**.

### 4.1 The bridge now passes BOTH geometrically AND electrically — the D-287 cascade is GONE

```
bridge_early: land C36.1, traverse 70.925 mm @ 1.30 mm, entry 4 @ y=67.95, exit 4,
              ywest 82.40, ok=true, bridge_eco null
```

The four **entry vias now sit at y = 67.95 mm — genuinely INSIDE the rotated R75.2 B.Cu
pad** (pad centre ≈ 2.800, 67.963; bbox y ∈ [67.35, 68.58]), versus the D-287 y ≈ 66.19–
66.81 (north of the pad). There is **NO `via_dangling` cascade** anywhere in the run — the
20-gate poisoning that forced the D-287 `DRIVER_EXIT=143` stop is gone. The fix is proven
end-to-end at full-run scale, not merely in the isolated probe.

### 4.2 BAT_PROTECTED_P island closes seven pads — but U18.8 stays open (NEW blocker)

The main trunk lays (`R75.2 → (stage)` 14.634 mm @ 1.50 mm F.Cu + 2 vias) and the
`BAT_PROTECTED_P` island closes **R75.2 through C36 / C25 / C58 / D9 / U11 / U14 / TP15**
(all "already joined via R75.2"). **`U18.8` remains OPEN**: its reservation was first
`GATE_REJECTED` on a genuine `clearance +1` (`rule 'BAT_MAIN routed clearance'`), then the
main pass reports **`NO_VIA_SITE` — "no via site of 0.65 mm reachable on B"** (pass-1) and
**"no 0.35 mm via site reachable on B"** (pass-2). So `BAT_PROTECTED_P` is **not fully
closed across all required pads** — `U18.8` is the one open trunk pad, blocked by a via-
landing/clearance geometry, not by the bridge.

### 4.3 Terminal Phase-A fail — a NEW, different net (REF_POL), plus BAT_RAW divider width

The driver's selected terminal fail is **`REF_POL R87.2 → (node)` : NO_PATH — no F
corridor at 0.150 mm** (also `R88.1 → R87.2` NO_PATH at 0.150 mm). Independently,
**`BAT_RAW R89.1 → (node)` NO_PATH at 0.600 mm**, and **`R86.2`** walks the width ladder
1.00 → 0.20 mm and is then `GATE_REJECTED` on **`track_width +4`** because four 0.20 mm
`BAT_RAW` **divider taps** violate the **`BAT_MAIN minimum width` 0.60 mm** rule. This is a
**rule-conformance rejection** (the router refusing to lay a route that would breach
BAT_MAIN) — **attributed, not absorbed**: the final board carries no such `track_width +4`.
These are downstream nets the D-287 entry dangling had shadowed.

### 4.4 Final DRC (re-verified with `kicad-cli pcb drc --severity-all` on the final scratch board)

`{hole_clearance: 5, lib_footprint_issues: 199, solder_mask_bridge: 1, track_width: 1,
unconnected_items: 499}` — reproduces the JSON exactly. Bounded stub exceptions present
(`stubs`): `BAT_RAW_DIVIDER_TAP_1/2/3` (0.2 mm, D-269 microamp tap corridor), `BAT_STUB_3`
(BAT_PROTECTED_P, 1.0 mm shunt), `BAT_STUB_4` (BAT_SENSE, 0.2 mm).

**The single `track_width` item, stated truthfully:** a **`BAT_PROTECTED_P` track on
B.Cu, length 2.4749 mm @ (65.5, 76.05), actual width 0.2000 mm**, violating rule
**`BAT_PROTECTED_P high-current trunk width - D-249` (min 1.2000 mm)** — i.e. one thin
0.20 mm **sense/Kelvin sub-branch** of the high-current trunk net (a bounded sense tap),
a genuine-but-benign copper item **SURFACED not absorbed** (identical in class to the lone
`track_width +1` D-286/003M surfaced). It is NOT a fabrication blocker.

## 5. Verdict — a successful bridge fix ≠ an overall Phase-A pass

- The **D-287 lever is closed.** The entry array is electrically tied on two layers; the
  regression is non-vacuous (legacy `+4` dangling / fixed `0` dangling / no absorption);
  the full run confirms it (no `via_dangling` cascade, island closes seven pads).
- **BUT the full Phase-A run FAILs** on new downstream blockers the entry dangling had
  shadowed: (1) `U18.8`'s `BAT_PROTECTED_P` escape (`NO_VIA_SITE` on B + a BAT_MAIN routed-
  clearance reservation reject) leaves the trunk one pad short of full closure; (2) the
  terminal `REF_POL R87.2 / R88.1→R87.2` F-corridor NO_PATH at 0.150 mm; (3) the `BAT_RAW`
  `R89.1/R86.2` divider-tap width vs the BAT_MAIN 0.60 mm rule.
- These are **bounded technical blockers**, not a placement wall and not un-fixable
  without relaxing a floor or moving a frozen part. So **direction-2 (broad LTC4368
  refloorplan / corridor widening, OWNER/mechanical) is NOT the sole remaining option, and
  this is NOT an OWNER decision.** `/home/aqroot8/.aqroot-autopilot-stop` stays ABSENT;
  open owner decisions remain NONE.

## 6. The next bounded task — FBV2-P2-003P (CTO scope), in true fabrication-blocker order

With the bridge entry tie proven, the remaining `BAT_PROTECTED_P`/Phase-A blockers, in
priority order, **without relaxing any floor/rule or moving a frozen part**:

1. **U18.8 `BAT_PROTECTED_P` escape (the last open trunk pad).** Investigate/close its
   via-site + reservation — it reports `NO_VIA_SITE` at 0.65 mm and 0.35 mm on B and an
   earlier reservation `GATE_REJECTED` on a `BAT_MAIN routed clearance` item. Find a legal
   B-layer via site / escape for U18.8 that keeps the 0.200 mm clearance floor and the
   ≥1.20 mm trunk width; this closes `BAT_PROTECTED_P` across all required pads.
2. **Terminal REF_POL R87.2 / R88.1→R87.2 corridor.** NO_PATH at 0.150 mm — investigate
   the F.Cu corridor to the REF_POL node (a signal net); determine whether it is a
   congestion/ordering problem or a genuine geometric wall.
3. **BAT_RAW R89.1 / R86.2 divider-tap width.** The four 0.20 mm divider taps trip the
   BAT_MAIN 0.60 mm rule (`track_width +4`, gate-rejected). Attribute correctly — decide
   whether these taps are legitimately bounded microamp exceptions (like the D-269
   `BAT_RAW_DIVIDER_TAP_*` corridor already in the `stubs` list) or genuine width failures
   — **without relaxing BAT_MAIN**.

If any of these proves un-fixable without relaxing a floor/rule or moving a frozen part,
THAT becomes a genuine OWNER decision. Until then autonomy continues (no autopilot stop).

## 7. Integrity

- **Source changes (all in the bridge code / regression, NOT the driver):**
  `bridge_route_003c.py` (rotation-aware in-pad `scan_entry_sites` via `_in_pad` +
  `IN_PAD_MARGIN`, centre-out sort; entry B.Cu tie-stub in `stage_bridge`),
  `bridge_early_003i.py` (entry B.Cu tie-stub in `apply_early`), `screen_003n.py` (the
  D-288 `entry_tie_regression`: negative + positive + no-absorption controls, replacing the
  D-287 dangling-control `--validate`). No driver/router/DRU/footprint/netclass/rule
  source mutated.
- **No rule/floor relaxed** (0.200 mm clearance, 0.25 mm hole-to-hole, ≥1.20 mm BPP trunk,
  0.60 mm BAT_MAIN all ENFORCED); **no DRC absorbed** (U18.8 `NO_VIA_SITE`, the REF_POL
  NO_PATH, and the BAT_RAW `track_width +4` are the FAIL/reject reasons, not swept).
- **No authoritative promotion:** board stays six copper layers, 0 signal tracks, 0 signal
  vias, placement at home (C36 63.75,73.75,0°; U18 3.0,72.4,90°). All 003O copper lived in
  gitignored scratch (`checks/w/`). `phaseA_journal.json` restored to committed HEAD.
- **Evidence of record pinned:** `checks/phaseA_003o_b1_r75rot_cto.json` (the natural-
  completion CTO full-run result) is committed; the log stays gitignored scratch.
- Regressions GREEN: `screen_003n.py --bridge --validate` (negative `+4`, positive `0` /
  no-absorption); the focused D-288 regression and router regression G1–G12 passed in the
  prior work. `c3_00` not promoted; `place_003l` (D-285) preserved; optional
  `BAT_SENSE TP20.1` separate; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS`
  unchanged.
- **NO PROGRESS EARNED:** PCB routing 0 %, overall 74 %, readiness ~77 % — only scratch
  evidence and tooling improved.
