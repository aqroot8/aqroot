# FBV2-P2-003W — D-297: the SECONDARY U18.8 I2-join lever completes `BAT_PROTECTED_P U18.8→R75.2` on In3 for a GENUINE +1 connected-set gain (no swap, no new DRC, `via_dangling` cleared); ACCEPTED and retained OFF-by-default in tracked source, but copper is NOT promoted — the full run still FAILs on the saturated U19 field

**Date:** 2026-08-30
**Milestone:** FBV2-P2-003W
**Decision:** D-297
**Class:** GOVERNED ACCEPT / SECONDARY-lever net gain banked in source — **NOT an owner decision.** Autonomy continues (`/home/aqroot8/.aqroot-autopilot-stop` ABSENT).
**Starting HEAD:** `27f9790` (pushed; `phaseA_journal.json` at HEAD) with one uncommitted WIP file `checks/route_battery_block.py` (+25/−1 lines, the env-gated `AQROOT_U18BPP_JOIN` lever the D-295/D-296 handoff called for) plus a G13 regression contract in `checks/router_regression.py` and the measured-record probe `checks/u18_i3_join_probe_003w.py`.
**Final HEAD:** source + docs + probe commit on `master` (this milestone).

---

## 1. What 003W was asked to do

D-296 (003V) refuted the PRIMARY U19.7 escape-reservation family (it fires and closes U19.7 but only swaps the casualty inside the capacity-saturated U19 field) and handed off the **SECONDARY** D-295 lever: at the D-293 direction-2 placement `t_a_r77e15n10_r79e15n10`, open a **≥0.200 mm join lane** for `BAT_PROTECTED_P U18.8 → R75.2` within existing **D-257/D-266** corridor mechanics — full-authority-gate judged, **without** any D-290 re-authorization, DRU/rule change, via below the D-257 ladder, or topology/footprint/outline change.

003W implemented ONE narrowly-scoped, env-gated (**OFF by default**) lever, pinned it with a regression contract (G13) and a measured-record probe, and the CTO ran the FULL authority gate (the only judge that promotes copper — D-286).

---

## 2. The wall (D-294 / D-295)

At the direction-2 placement the `BAT_PROTECTED_P` reserve pair places two ordinary **0.35/0.20 THROUGH vias** at `R75.2` (2.800, 66.800) and `U18.8` (7.200, 66.500) on **In2** (via the nearest-legal-exit fallback; the join-minimising scored exit is rejected on `BAT_MAIN` routed clearance). Their **In2 JOIN is `NO_PATH`**: a `BAT_RAW` 0.600 mm **current-path wall** runs vertically on In2 at x ≈ 6.4 → 6.65 (y 50.45 → 70.40), severing the west→east lane between the two vias. U18.8 is left open (non-fatal); the terminal fatal wall in 003T was the PRIMARY `REC_BAT_LOW U19.7` (refuted separately by D-296).

---

## 3. The lever (D-297) — join the ONE branch on In3, not In2

**Premise.** The reserve vias are **THROUGH vias** — copper on every layer — so the join is electrically identical on In2 or In3. **In3.Cu is a routable six-layer signal layer** (`qrouter.ROUTABLE[6] = ('F','B','I2','I3')`) that is **EMPTY across the whole corridor** on the real full-run board (only 2 In3 tracks board-wide, NONE in the corridor; no In3 copper pour — the only inner pours are the In1/In4 GND planes). So the same branch joins cleanly on In3 with **NO new via, NO DRU/floor change, NO topology change.**

**Implementation** (`route_battery_block.py`, `main()` join site). A single env flag names the join layer for **exactly one branch**; unset → the join stays on `va[2]` (In2), byte-identical to every prior run:

```python
jl = va[2]
if (U18BPP_JOIN in ('I2', 'I3')
        and net == N + 'BAT_PROTECTED_P'
        and a == 'U18.8' and b_ == 'R75.2'):
    jl = U18BPP_JOIN
r = QR.join_reserved(qb, net, va[:2], vb[:2], w, CP, ct, layer=jl)
```

`AQROOT_U18BPP_JOIN` (`'I2'`/`'I3'`, `.upper()`-normalised; any other value never activates the lever). The override is guarded on the env flag **and** the exact net/pad pair — nothing wider.

---

## 4. Measured evidence

### 4a. Probe on the most faithful affordable vehicle (`u18_i3_join_probe_003w.py`)

Run on the actual full-run routed board `w/FULL003T_e15n10cto/aqroot-Beta-v2.kicad_pcb` (the real full congestion, not a focused vehicle whose In2 join would pass vacuously), on a throwaway copy so the preserved evidence board is never mutated:

| check | result |
|---|---|
| In2 and In3 are routable six-layer signal layers | PASS (`ROUTABLE[6]=('F','B','I2','I3')`) |
| **A** In2 join is `NO_PATH` (the D-294 wall reproduces) | PASS |
| **A** In3 join is ok (the lever opens the lane) | PASS — **ok 4.410 mm**, grid 0.025 |
| **B** In3 join adds ZERO new DRC classes (real KiCad DRC) | PASS — `new=NONE` |
| **B** In3 join clears the dangling reserve via | PASS — **`via_dangling` 1 → 0** |

### 4b. Full-authority gate (`w/phaseA_003t_full_003w_u18bpp_i3.json`, secs 1272.5)

Judged by the full-run connected-set diff vs the D-294 governing baseline `w/phaseA_003t_full_e15n10cto.json`:

| metric | D-294 baseline (003T) | **003W (`AQROOT_U18BPP_JOIN=I3`)** |
|---|---|---|
| connections (routed) | 69 | **70** (+1) |
| skipped-already-connected | 98 | **99** (+1 — see §5) |
| ratsnest / delta | 708 / −73 | **707 / −74** (one more edge cleared) |
| journal length | 72 | **73** (+1: the U18.8→R75.2 In3 JOIN) |
| DRC | `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, track_width:1, unconnected_items:499, via_dangling:1}` | **`{…same…, unconnected_items:499}` — `via_dangling` 1 → 0, no new class** |
| terminal fatal wall | `REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE` (U19.8 ×26, U19.6 ×13, U19.5 ×7, track ×6) | **identical** |

The journal records the reserve/join two-step exactly:
- step 6 `RESERVE_PAIR` `BAT_PROTECTED_P U18.8↔R75.2`, layer **I2**, 2 vias (through);
- step 27 `JOIN` `BAT_PROTECTED_P U18.8→R75.2`, layer **I3**, **4.410 mm, 0 vias**, ok.

**The decisive connected-set diff (D-294 → 003W) is a STRICT PURE GAIN.** The entire journal delta is **exactly one added entry** — the `U18.8→R75.2 JOIN` on In3 — with **nothing lost** (no entry removed, no entry flipped to unconnected). This is the categorical opposite of D-296's 1-for-1 swap (which gained `REC_BAT_LOW U19.7→Q7.1` only by losing `REF_POL TP24.1→U19.2`). The In3 join takes routing capacity from **no other net** (In3 is unused in the corridor), so no casualty is possible — and none occurs.

---

## 5. Why `skipped-already-connected` also rises 98 → 99 (a positive sign, not a loss)

`skipped` counts pads **skipped because they are ALREADY joined to their net's copper** (`route_battery_block.py` `state['skipped']`), i.e. it is *skipped-already-connected*, not *skipped-failed*. Closing `U18.8→R75.2` extends the `BAT_PROTECTED_P` connected component, so one downstream `BAT_PROTECTED_P` pad that the driver reaches later is now found already-joined and is (correctly) skipped rather than re-routed. The +1 skipped is therefore a **consequence of the successful join**, confirmed by the ratsnest falling one further edge (−73 → −74) and the total requested set being conserved. It is progress, not regression.

---

## 6. Ruling (D-297) — ACCEPT the lever; bank the gain in source; do NOT promote copper

**The SECONDARY U18.8 I2-join lever is a genuine, board-legal, verified net gain and is ACCEPTED.** Unlike the D-296 PRIMARY family (rejected/retired), this lever earns a real +1 connected-set connection (`U18.8→R75.2` on In3, 4.410 mm), clears the lone `via_dangling`, adds zero new DRC classes, adds no via, relaxes no floor, and changes no topology/footprint/outline/rule. It is retained in tracked source as an **env-gated, OFF-by-default** lever (`AQROOT_U18BPP_JOIN`), byte-identical to every prior run when unset, and pinned by the **G13** regression contract and the `u18_i3_join_probe_003w.py` measured-record probe.

**But copper is NOT promoted, and progress does NOT move.** Phase-A copper promotes to the authoritative board only on a full-authority **PASS** (D-286); the 003W full run still **FAILs** on the unchanged saturated U19 field — terminal `REC_BAT_LOW U19.7→(node) NO_LEGAL_ESCAPE`, with `N_BATDIV U19.6` the next-in-line wall (D-296). D-297 therefore **banks** the U18.8 closure in the source: once the U19 field is separately enlarged, this lever (set ON) yields the U18.8 join for free — no new via, no new DRC. Until then the authoritative board stays six layers / 0 tracks / 0 vias and readiness/progress are unchanged.

This is a governed CTO ACCEPT of a productive SECONDARY lever + a governed **FAIL of the overall Phase-A run** — NOT an owner decision (no floor relaxed, no frozen part moved, direction-2 not exhausted, the U19 field remains bounded CTO-scope work).

---

## 7. Integrity

- **Authoritative PCB byte-identical to HEAD:** `sha256 2235e2736838b1182a1e97821d1b4a3a473316f679fdf99c4fed7acb8d642d7e` (`hardware/beta-v2/kicad/aqroot-beta-v2/aqroot-Beta-v2.kicad_pcb`); six copper layers, **0 signal tracks, 0 signal vias**, placement at home. `git status` clean for the PCB.
- **No DRC absorbed:** the `via_dangling` clear and the +1 connection live only on the gitignored full-run scratch board; the U18.8 In3 join, the U19.7/U19.6 no-escape and the run's DRC are surfaced FAIL/gain evidence on scratch, never in the authoritative board.
- `phaseA_journal.json` at HEAD (the shared journal was backed up and restored around the full run).
- **What survives in tracked source:** the OFF-by-default `AQROOT_U18BPP_JOIN` lever (byte-identical when unset), the G13 contract, and the probe. No copper, no placement, no rule, no floor, no topology/footprint/outline change; no via below the D-257 ladder; D-269 (0.300 mm current-path), ≥1.20 mm BPP, 0.60 mm BAT_MAIN ENFORCED; D-290 untouched; `place_003l` (D-285) and the D-275/D-288 bridge preserved; D-275 and D-277..D-296 preserved; frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` unchanged.
- Gitignored evidence **preserved**: `checks/w/phaseA_003t_full_003w_u18bpp_i3.json`, `checks/w/FULL003T_e15n10cto/`, `checks/w/TEST003W_PROBE/`.
- **NO PROGRESS EARNED (no copper promoted):** PCB routing 0 %, overall 74 %, readiness ~77 %.

---

## 8. Tests

- `python3 u18_i3_join_probe_003w.py` → **ALL CHECKS PASS** (In2 `NO_PATH`, In3 ok 4.410 mm, zero new DRC classes, `via_dangling` 1→0).
- `python3 router_regression.py` → **ALL CHECKS PASS**, incl. new **G13**: In3 is a routable six-layer signal layer; the lever is **OFF by default** (join layer = `va[2]`, byte-identical); `AQROOT_U18BPP_JOIN=I3` activates the In3 join; a non-I2/I3 value never activates it; the override is scoped to exactly `BAT_PROTECTED_P U18.8→R75.2`. (G1–G12 unchanged.)

---

## 9. Next — FBV2-P2-003X

The last Phase-A fabrication blocker is now the **simultaneous `REC_BAT_LOW U19.7` + `N_BATDIV U19.6` closure** in the capacity-saturated U19 dead-cell field. D-296 proved a single-pin reservation only **swaps** the casualty, so the next lever must **enlarge** the field, not re-order it. The D-297 insight points the way: **the inner signal layers In2/In3 are bare and routable in this corridor.** 003X should implement ONE bounded, env-gated (OFF-by-default) **U19 capacity** lever that offloads one or more saturating escapes off the jammed F.Cu/B.Cu field onto a bare inner layer (e.g. the direction-2-induced `VREC_VCC U19.8` F.Cu pad-escape and/or a boxed U19 escape), within D-257/D-266 mechanics — **no via below the D-257 ladder, no D-290 re-auth, no DRU/rule/topology/footprint/outline change** — and judge it by the full-authority connected-set diff: it must close **U19.7 AND U19.6 together for a real net gain** (a 1-for-1 swap is NOT a gain — D-296). Promote copper only on a genuine full-authority Phase-A PASS. Keep the direction-2 placement `t_a_r77e15n10_r79e15n10` and the accepted D-297 U18.8 lever ON in that run.
