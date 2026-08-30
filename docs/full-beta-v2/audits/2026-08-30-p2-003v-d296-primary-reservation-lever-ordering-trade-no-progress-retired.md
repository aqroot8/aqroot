# FBV2-P2-003V — D-296: the PRIMARY U19.7 escape-reservation lever is a bounded ordering trade with NO connected-set progress; the source WIP is retired

**Date:** 2026-08-30
**Milestone:** FBV2-P2-003V
**Decision:** D-296
**Class:** GOVERNED FAIL / primary-family refutation — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT).
**Starting HEAD:** `a2e27fc` (pushed; `phaseA_journal.json` at HEAD) with one uncommitted WIP file `checks/route_battery_block.py` (+65 lines, the `AQROOT_U19_RESV` lever the D-295 handoff called for).
**Final HEAD:** docs-only evidence commit on `master` (this milestone).

---

## 1. What 003V was asked to do

D-295 (003U) handed off the PRIMARY direction-2 wall — `REC_BAT_LOW U19.7 → (node) NO_LEGAL_ESCAPE` at the D-293 placement (`t_a_r77e15n10_r79e15n10`) — with an exact lever design: **reserve U19.7's B.Cu escape (one neck + one through via, scored toward Q7.1 to preserve the 003O escape direction) BEFORE the `tight='U19'` pin field runs and consumes it.** OFF by default; env-gated on `AQROOT_U19_RESV`; a failed reservation non-fatal (falls through to the ordinary path). 003V implemented that lever and ran the FULL authority gate twice — the only judge that promotes copper (D-286).

Two full runs were completed under CTO authority (no new run in this closeout — the two artifacts already existed):

- **`w/phaseA_003t_full_003v_u19resv.json`** — first attempt, reservation via at the D-257 preferred **0.35/0.20** rung.
- **`w/phaseA_003t_full_003v_u19resv2.json`** — corrected attempt, reservation via at the smallest **board-legal 0.60/0.30** rung (the corridor-less reservation has no FINE_ESC override, so the sub-minimum 0.35/0.20 via is rejected on `via_diameter` + `annular_width`).

Both are judged by the full-run connected-set diff against the D-294 governing baseline `w/phaseA_003t_full_e15n10cto.json` and the committed 003O baseline.

---

## 2. RESV (0.35/0.20) — the illegal reservation is rejected; run is behaviourally identical to D-294

The corridor-less reservation cannot legalise a sub-minimum via, so `reserve_escape` returns not-ok, the (non-fatal) reservation is dropped, and the run falls through to the ordinary path unchanged.

| metric | D-294 baseline | RESV (0.35/0.20) |
|---|---|---|
| connections | 69 | 69 |
| skipped | 98 | 98 |
| ratsnest / delta | 708 / −73 | 708 / −73 |
| journal length | 72 | 72 (**no RESERVE entry laid**) |
| DRC | `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499, via_dangling:1}` | identical |
| terminal fail | `REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE` (U19.8 ×26, U19.6 ×13, U19.5 ×7, track ×6) | **identical** |

**Connected-set diff D-294 → RESV: EMPTY in both directions.** RESV is byte-equivalent in behaviour to D-294 — exactly the "unset reproduces the run" property the lever promised. No progress, no regression.

---

## 3. RESV2 (0.60/0.30) — the reservation FIRES, U19.7 closes, but the casualty merely moves

The board-legal reservation is laid (journal gains one `RESERVE` step `REC_BAT_LOW U19.7 → Q7.1`, 1 via), and U19.7's own SIG edge then completes from the reserved lane. **U19.7 routes.** But the saturated U19 pin field is not enlarged — it is merely re-ordered, so a *different* pin becomes the casualty.

| metric | D-294 baseline | RESV2 (0.60/0.30) |
|---|---|---|
| connections | 69 | **69** |
| skipped | 98 | **98** |
| ratsnest / delta | 708 / −73 | **708 / −73** |
| journal length | 72 | 73 (**+1: the U19.7 RESERVE step**) |
| DRC | as above | **identical histogram** |
| terminal fail | `REC_BAT_LOW U19.7→(node)` | **`N_BATDIV U19.6→(node) NO_LEGAL_ESCAPE`** (blocked by U19.7 ×22, U19.5 ×20, track ×6, C60.2 ×5) |

**Connected-set diff D-294 → RESV2 (the decisive evidence):**

- **GAINED:** `REC_BAT_LOW U19.7 → Q7.1 (SIG)` — the reservation worked; U19.7 escapes.
- **LOST:** `REF_POL TP24.1 → U19.2 (SIG)` — U19.2, previously connected in D-294, is now open.

Net connected-set (requested-connected count): **68 in D-294, 68 in RESV2** — a strict **1-for-1 swap**. The reported terminal wall also moves *within the same package*: from U19.7 to U19.6 (with U19.2 also left open). The reservation reserved copper for U19.7 by taking it away from the equally-saturated neighbours, so the greedy-tightest-first race simply walls on a different U19 pin.

---

## 4. Ruling (D-296)

**The reservation MECHANISM is real and the diagnosis is confirmed:** with a board-legal via the lever fires, U19.7 escapes exactly as D-295 predicted, and the run stays fully board-legal (DRC histogram unchanged, no rule relaxed, no via below the D-257 ladder — the corridor-less rung self-corrects to the ordinary Default 0.60/0.30). This is a genuine positive finding — U19.7 is closable in principle.

**But the lever earns NO connected-set progress.** The U19 dead-cell pin field is saturated on F.Cu/B.Cu capacity, not on ordering priority for one pin: reserving U19.7's lane simply chooses *which* pin among the saturated field is abandoned (U19.7 ⇄ U19.2, wall U19.7 → U19.6). Total connected count is unchanged at every measure (conn 69, skip 98, ratsnest 708/−73). Per D-286 no proxy — and here not even a genuine full-authority run — promotes copper without a real net gain. **REJECTED for production. The `AQROOT_U19_RESV` source WIP is retired.** This refutes the PRIMARY reservation family from the D-295 handoff; it is a governed FAIL, not an owner decision (the SECONDARY U18.8/U18.9 I2 reserve-via lever remains open, and no floor/rule/placement was touched).

---

## 5. Retirement proof

The WIP was retired with an **exact reverse patch** (not a destructive broad reset): `git diff -- checks/route_battery_block.py > /tmp/003v_u19resv_wip.patch; git apply -R` — scoped to exactly the WIP hunks, touching nothing else.

- `git diff --stat` for `checks/route_battery_block.py`: **empty** (identical to HEAD).
- Worktree blob `git hash-object` = `bba62d35efd5de9451dbd12ec85cee89e608e912` = `HEAD:checks/route_battery_block.py` blob — **byte-identical**.
- `git grep U19_RESV` over tracked source (excluding gitignored `checks/w/`): **no match** — no `AQROOT_U19_RESV` code remains in tracked source.
- Working tree after retirement: **clean** (the docs commit is the only change).

The gitignored evidence is **preserved**: `checks/w/phaseA_003t_full_003v_u19resv.json`, `checks/w/phaseA_003t_full_003v_u19resv2.json`, `checks/w/FULL003T_003v_u19resv*/`, `checks/w/TEST003V_U19RESV/`.

---

## 6. Integrity

- **Authoritative PCB byte-identical to HEAD:** `sha256 2235e2736838b1182a1e97821d1b4a3a473316f679fdf99c4fed7acb8d642d7e` (`hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb`); six copper layers, 0 signal tracks, 0 signal vias, placement at home. `git status` clean for the PCB.
- **No DRC absorbed:** the U18.8 open, the U19.6/U19.7/U19.2 no-escape and the lone scratch `via_dangling:1` are surfaced FAIL evidence on gitignored scratch, never in the authoritative board.
- `phaseA_journal.json` at HEAD (clean).
- No source/copper/placement/rule change survives; no via below the D-257 ladder; D-269 (0.300 mm current-path), ≥1.20 mm BPP, 0.60 mm BAT_MAIN floors ENFORCED; D-290 untouched; `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-295 preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged.
- **NO PROGRESS EARNED:** PCB routing 0 %, overall 74 %, readiness ~77 %.

---

## 7. Next — FBV2-P2-003W

Execute the **SECONDARY** D-295 lever: a bounded **U18.8/U18.9 I2 reserve-via siting/ordering** study to open a **≥0.200 mm join lane** for `U18.8 → R75.2` within the existing **D-257/D-266 corridor mechanics** — full-authority-gate judged (connected-set diff vs `phaseA_003o_b1_r75rot_cto.json` and `w/phaseA_003t_full_e15n10cto.json`), **without** any D-290 re-authorization, DRU/rule change, via below the D-257 ladder, or topology/footprint/outline change. Promote copper only on a genuine full-authority net gain.
