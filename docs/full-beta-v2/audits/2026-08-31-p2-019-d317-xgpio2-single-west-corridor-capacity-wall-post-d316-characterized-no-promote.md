# FBV2-P2-019 / D-317 — the SINGLE west XGPIO net `XGPIO2` is now a MEASURED CORRIDOR-CAPACITY WALL on the live D-316 board (the D-316 `XGPIO3` haul spent the one corridor the D-315 study proved it admits); NO PROMOTE; clean characterization boundary; FBV2-P2-020 defined

**Date:** 2026-08-31
**Starting HEAD:** `6410e1faef21acd77a7bfad5d4cadb185a6151be` (D-316; pushed; `origin/master` identical)
**Authoritative PCB (UNTOUCHED this task):** `sha256 d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d` — 691 tracks / 67 vias / 6 layers / 41 zones / ratsnest 676 / journal 105
**Result:** GOVERNED CTO CHARACTERIZATION — the named candidate (the single west XGPIO net `XGPIO2`) does **NOT** promote on the live D-316 board; the authoritative board is **byte-identical to committed D-316** (zero copper change); autonomy CONTINUES; **no owner decision.**

---

## Summary

FBV2-P2-018 / D-316 routed and promoted a *single* west XGPIO net, `XGPIO3` (R54.1 F.Cu → U3.7 B.Cu),
at the 0.200 mm Default clearance, and named `XGPIO2` (R53.1 F.Cu → U3.6 B.Cu) as the next single-net
candidate — with the explicit caution that its pre-D-316 0.6859 mm BPP margin (measured on the D-314
board) **must not be assumed to survive** the addition of the XGPIO3 copper/via, and that its via-exv to
the XGPIO1 barrel was already tight (0.256 mm). Screened faithfully on the **live D-316 board**, `XGPIO2`
alone at the 0.200 mm Default **does not route**: it fails **NO_FAR_RUN** — the long ~116 mm F.Cu haul
from R53.1 down to the U3 via region has **no legal 0.200 mm corridor**. The single authorized bounded
site alternative (the existing D-310 `via_offset` transition relocation, no new router logic) **also
fails NO_FAR_RUN**, proving the wall is the **haul corridor**, not the via site.

This is the **D-315 corridor-capacity wall now realized.** D-315 measured that the west F.Cu corridor,
congested by the D-313/D-314 XGPIO increments, **admits ONE 116 mm haul, not two parallel ones** (the
XGPIO2+XGPIO3 pair failed NO_FAR_RUN in every order). D-316 spent that one corridor slot on the
`XGPIO3` haul (now REAL laid copper). `XGPIO2` (R53, U3.6), the immediately-adjacent second parallel
haul from R53.1, is therefore now blocked — exactly as D-315 predicted. On the D-314 board (before
XGPIO3) `XGPIO2` alone routed (D-315: via (55.300, 78.150), 116.42 mm, haul→BPP 0.6859 mm); that old via
site is now 0.450 mm centre-to-centre from the D-316 `XGPIO3` barrel at (55.300, 77.700) — a hole-hole
of 0.150 mm < 0.25, i.e. a collision — so the router (which correctly injects the 67 existing barrels as
obstacles) cannot reuse it, and no alternative site opens the far-run corridor. **The 0.6859 mm margin
did not survive, as the task required verifying.**

Every experiment ran on throw-away scratch copies (`checks/w/…`, gitignored); the authoritative project
was never mutated (`sha256 d730c74d…` verified before **and** after both screens; `route`/`gate`/`promote`
were never invoked on this board).

---

## A — Topology (read-only, live D-316 board, `w/screen_019.py`)

`XGPIO2` = net `/XGPIO2`, a 2-pad cross-layer net (one MST edge, one F↔B through via):

| pad | ref | layer | x (mm) | y (mm) | role |
|-----|-----|-------|--------|--------|------|
| series R | **R53.1** | F.Cu | 54.9629 | 26.3957 | 100 Ω series resistor (north resistor pack) |
| expander | **U3.6** | B.Cu | 54.1375 | 78.3250 | PCAL9535A GPIO pin (west edge, **flanked middle pin**: U3.5 south, U3.7 north) |

The route is the same structure as every accepted XGPIO increment: a long F.Cu haul from the north
resistor pack down to a cross-layer through via that transitions to the B.Cu U3 pin. The corridor for
this haul is the same y≈73–82 west band the D-313/D-314/D-316 XGPIO hauls already occupy.

---

## B — Screen: `XGPIO2` alone at the 0.200 mm Default (`w/screen_019.py`, one managed foreground process)

Routed through the exact faithful router path the gate would use — `IR.connect_cross` with
`IR.inject_existing_via_obstacles` (so all **67** existing barrels, including the D-316 `XGPIO3` via at
(55.300, 77.700), are obstacles), no `via_offset`, `clr_pad = clr_trk = 0.200 mm`:

| net @ clearance | result | detail |
|-----------------|--------|--------|
| `XGPIO2` @ 0.200 | **FAIL NO_FAR_RUN** | escape + via site found, but **no legal 0.200 mm corridor from R53.1 to the via** (tried 0.05 mm then 0.025 mm grid) |

The failure is the **far run** — the long ~116 mm F.Cu haul from R53.1. The escape from U3.6 succeeded
(the via-site step is not the blocker here), so this is not the D-315 *pad-escape box* at 0.300 mm; it is
a genuine **corridor** failure at the 0.200 mm Default, caused by the now-laid `XGPIO3` haul occupying
the one corridor.

Authoritative `sha256 d730c74d…` unchanged during the screen; only gitignored `w/SGL019_2` scratch written.

---

## C — The one authorized bounded alternative: existing `via_offset` site relocation (`w/screen_019_offset.py`)

The task authorizes **one** bounded site/path alternative for a newly-blocked route. The correct one
here is the **existing** D-310/D-311 `via_offset` mechanism (`IR._offset_via_site`, **zero new router
logic**), which walks the F↔B transition a bounded distance off the nearest congesting barrel (the
`XGPIO3` via). Tried at the proven 2.5 mm bound:

| net @ clearance + alternative | result | detail |
|-------------------------------|--------|--------|
| `XGPIO2` @ 0.200 + `via_offset` 2.5 mm | **FAIL NO_FAR_RUN** | same far-run corridor failure |

`via_offset` relocates the via **site**; it cannot open a new 116 mm **haul corridor**. That it changes
nothing confirms the wall is **corridor capacity**, not via placement (exactly the D-315 reasoning:
"`via_offset` relocates the via SITE after escape and does nothing for a parallel-haul corridor
conflict"). **The one bounded alternative is spent.** A per-region `clr_pad`/`clr_trk` split was already
spent by D-315 for this pair (fixes escape, still NO_FAR_RUN), and a spatially-varying clearance is
out-of-bounds new logic the task forbids — and unnecessary, because no site change unblocks the haul.

---

## D — Why NOT promote, and why no rule/logic change

* The named candidate is the single net `XGPIO2`. On the **live D-316 board** it is walled two
  independent ways (Default 0.200 mm: NO_FAR_RUN; bounded `via_offset`: NO_FAR_RUN). The route does not
  complete, so there is nothing to gate — and the pre-D-316 0.6859 mm BPP margin is moot (measured on a
  board state that no longer exists).
* This is the **D-315 corridor-capacity wall realized**: the west F.Cu corridor admits ONE 116 mm haul;
  D-316 spent it on `XGPIO3`; `XGPIO2` is the blocked second parallel haul. Not an ordering artifact —
  `XGPIO3` is committed copper, and `XGPIO2` alone cannot route past it at 0.200 mm.
* **No rule weakening, no logic change:** 0.200 mm is the Default netclass; nothing below any floor was
  accepted; `incremental_router.py` / `qrouter.py` are untouched (the only source touched is the
  gitignored `w/screen_019*.py` scratch). No `GROUPS['XGPIO2']` entry is registered (there is no viable
  route to register).

---

## E — Integrity: authoritative board proven PRISTINE

`sha256` before and after the entire investigation: **`d730c74d186ebcc7d2f0aa513776778ce1cb9c9659029a2fffd5e2261e3ac97d`**
(byte-identical to committed D-316). No `route`/`gate`/`promote` ran on the authoritative project; only
gitignored `checks/w/{SGL019_2, SGL019O_2}` scratch copies were written; no orphan process; git working
tree clean (only gitignored `w/` scratch present).

* **`router_regression.py` — ALL CHECKS PASS (G1–G29), run twice, identical (deterministic).**
* `incremental_probe_006 … 017` — **all PASS**; `phaseB_bringup_probe_005` — **PASS**
  (691/67/105; **20 routed rest nets, 144 unrouted**). `live_fingerprint.py` single SoT still at D-316.
* **Independent DRC** (`kicad-cli pcb drc`, outside the framework helper): 205 violations =
  `{solder_mask_bridge:1, hole_clearance:5, lib_footprint_issues:199}`, `unconnected_items:499`,
  **`clearance` = 0** — matches the D-316 gate exactly.
* **D-269 / D-264 / DRU board-swap A/B:** the current board **is** committed D-316 (same bytes), so any
  swap is trivially byte-identical — **no regression is possible** (nothing mutated). Recorded honestly
  on the live board: `d269` FAIL(2) (the synthetic BAT_RAW-TAP-injection flake D-316 characterized),
  `d264` 2 failed (the D-314-characterized intrinsic non-determinism on an unrelated U18 sense item),
  `dru` FAIL(2) (pre-existing reds identical at D-316) — all known, none a regression.

## F — Opportunity & Simplification Scan (bounded to the XGPIO west bank)

* **A (the wall is now structural for west F.Cu single hauls):** D-315 proved the west F.Cu corridor
  admits ONE 116 mm haul; D-316 spent it on `XGPIO3`. So the remaining west members `XGPIO2` / `XGPIO4`
  / `XGPIO5` / `XGPIO6` / `XGPIO7` all contend for the **same now-spent corridor** as *second* F.Cu
  hauls — `XGPIO4/5/6/7` are the *northern* pins the D-314/D-315 scans flagged as even more congested.
  **Do not keep retrying single west XGPIO F.Cu hauls** — the corridor is saturated, not ordering-sensitive.
* **B (the deferred structural option is now concretely justified):** the D-315/D-316 scans repeatedly
  flagged the In2/In3 inner **signal** layers as fully available (the F/B-only framework never routes
  them) and an inner-layer XGPIO haul as the deferred option "if the F.Cu corridor saturates further."
  The corridor **has** saturated for the west bank — this is the concrete hard blocker that would
  separately justify the inner-layer route. It is a **larger framework change** (F/B-only today), out of
  the bounded scope of a single-net increment, and is defined as a **separate future task**, not started
  here.
* **C (productive near-term path):** 144 of 164 rest nets remain unrouted, many in **open, uncongested
  regions** away from the west F.Cu corridor. The zero-new-mechanism momentum continues by routing the
  next clean single-net (or small coherent group) increment **outside** the saturated west XGPIO band.
* No BOM / footprint / value / polarity / mechanical / firmware / UX change; DEVICE_SPEC unchanged.

## G — Locked invariants preserved

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change;
no D-290 reauth; D-249 ≥1.20 BPP, D-269 0.300 / 0.60 BAT_MAIN, general 0.200 / applicable 0.150 signals,
≥0.25 hole-hole (D-257), D-275/D-288 bridge, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical
reservations, every accepted increment (D-304…D-316) — all preserved (the board is byte-identical D-316).
Frozen `beta-full-reference-v1` untouched. Shared journal authoritative (105); no orphan process.

## H — NEXT: FBV2-P2-020

Route the next clean rest-of-board increment in an **open, uncongested region** — a single net or small
coherent local group **outside** the saturated west XGPIO F.Cu corridor — at its netclass Default under
the D-286 real full-board gate, zero router-logic change; add `incremental_probe_018.py` + `G30` on
promote. **Do NOT** retry single west XGPIO F.Cu hauls (`XGPIO2` / `XGPIO4` / `XGPIO5` / `XGPIO6` /
`XGPIO7` — corridor-capacity walled as second hauls), the `XGPIO2`+`XGPIO3` PAIR (D-315 wall), or
`U11_PROG` / `PWR_SENSE` (hard walls). Hold the **inner-layer (In2/In3) west-XGPIO haul** as the now
concretely-justified deferred **framework** task for when the open regions are exhausted. **144 of 164
rest nets remain unrouted.**

**Rollback:** none needed — no authoritative change. HEAD advances by documentation only.
