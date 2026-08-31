# FBV2-P2-017 / D-315 — XGPIO2+XGPIO3 south-west adjacent pair: measured CORRIDOR-CAPACITY WALL at the D-269 clearance; NO PROMOTE; clean characterization boundary; FBV2-P2-018 sharply defined

**Date:** 2026-08-31
**Starting HEAD:** `8de847b97d03af1221c737c6718bf1d5e0eeb861` (D-314; pushed; `origin/master` identical)
**Authoritative PCB (UNTOUCHED this task):** `sha256 95bc07be30598df44e5096fd3c51729aa61cdbefd9c9855297e3737ea0b3a605` — 669 tracks / 66 vias / 6 layers / 41 zones / ratsnest 677 / journal 104
**Result:** GOVERNED CTO CHARACTERIZATION — the named candidate (the XGPIO2+XGPIO3 adjacent pair) does **NOT** promote; the authoritative board is **byte-identical to committed D-314** (zero copper change); autonomy CONTINUES; **no owner decision.**

---

## Summary

FBV2-P2-016 / D-314 promoted the two SOUTHERNMOST west XGPIO members (`XGPIO0`+`XGPIO1`,
U3.4/U3.5) and predicted the same "XGPIO-lower-first self-separates" recipe would carry the
next south-west pair `XGPIO2`+`XGPIO3` (U3.6/U3.7). The task correctly framed that recipe as a
**hypothesis to revalidate on the live D-314 board, not an automatic truth.** Revalidated, it is
**disproved for this pair.** Both route orders fail, and the single bounded evidence-backed
alternative (a per-region clr_pad/clr_trk split) also fails. The pair is a genuine
**F.Cu corridor-capacity wall at the D-269 0.300 mm clearance**, not an ordering artifact.

The investigation also produced the decisive positive lead for the next task: **a SINGLE west
XGPIO net routes cleanly at the 0.200 mm Default clearance and keeps the D-269 0.300 mm floor to
BAT_PROTECTED_P with measured margin** (XGPIO2 haul→BPP **0.686 mm**, XGPIO3 **0.474 mm**). The
wall is specifically the attempt to place **two parallel 116 mm hauls at once** in the now
D-313+D-314-congested corridor, plus the flanked middle-pin U3.6 escape box at 0.300 mm pad
clearance — not the routability of either net alone.

Every experiment ran on throw-away scratch copies (`checks/w/…`, gitignored); the authoritative
project was never mutated (sha `95bc07be…` verified before and after; `route`/`gate`/`promote`
were never invoked on this board).

---

## A — Geometry (read-only, live D-314 board, `w/xgpio23_study_017.py`)

The west U3 GPIO column is at **x = 54.138**, pin pitch 0.65 mm, index increasing NORTH:

| net | U3 pin | pad y (mm) | series R (F.Cu) |
|-----|--------|-----------|-----------------|
| XGPIO0 | U3.4 | 79.625 (southmost) | R51.1 |
| XGPIO1 | U3.5 | 78.975 | R52.1 |
| **XGPIO2** | **U3.6** | **78.325** | **R53.1** (54.96, 26.40) |
| **XGPIO3** | **U3.7** | **77.675** | **R54.1** (55.11, 28.80) |
| XGPIO4 | U3.8 | 77.025 | R55.1 |

Accepted D-314 west vias: `XGPIO1 @ (55.400, 79.000)`, `XGPIO0 @ (52.750, 78.350)`.
XGPIO2 (U3.6) is a **flanked middle pin** — U3.5 to its south, U3.7 to its north — unlike the
southmost XGPIO0 (open south) or XGPIO1 (only one occupied neighbour) that D-314 promoted.
Legal 0.300 mm-clear B.Cu via cells DO exist (2983 within 3 mm of U3.6, nearest `(55.488,78.075)`
d=1.373 EAST; 3428 for U3.7) — the wall is **reachability/escape and long-haul corridor**, not
via-site availability.

---

## B — Screen: both pair orders at the D-269 0.300 mm floor (`w/screen_016_one.py`, live D-314 board)

The durable one-order recovery mechanism (D-314), re-run one managed foreground process at a time,
each row persisted to `screen_016_recovery.json`:

| tag | order | verdict | detail |
|-----|-------|---------|--------|
| `2_3_0` | XGPIO2→XGPIO3 | **A-FAIL** | XGPIO2 **U3.6 NO LEGAL ESCAPE** at ≥0.200 mm (blocked by U3.7 ×27, U3.4 ×16, track ×9, **via ×8**); XGPIO3 far-run blocked |
| `3_2_1` | XGPIO3→XGPIO2 | **A-FAIL** | XGPIO3 **no legal corridor** R54.1→via at 0.05/0.025 mm; XGPIO2 **U3.6 NO LEGAL ESCAPE** (same box) |

Both fail **regardless of order** — the failures are intrinsic to the D-314 board (in each order
the first net lays nothing before the other's failure, so neither failure is caused by the sibling).
`qb.escape` explores all 8 directions (ordered by preference, not limited to a cone), so U3.6's
failure is a genuine pad-escape box at 0.300 mm pad clearance, aggravated by the 8 via obstacles
(now including the accepted XGPIO0/XGPIO1 barrels consuming the pocket).

---

## C — Per-clearance wall isolation (`w/xgpio23_clr_017.py`, each net ALONE, live D-314 board)

| net @ clearance | result | via | haul mm | BPP (via) | exv cu |
|-----------------|--------|-----|---------|-----------|--------|
| XGPIO2 @ 0.200 | **OK** | (55.300, 78.150) | 116.42 | 2.279 | 0.256 |
| XGPIO2 @ 0.300 | **FAIL NO_LEGAL_ESCAPE** | — | — | — | — |
| XGPIO3 @ 0.200 | **OK** | (55.300, 77.700) | 118.26 | 1.836 | 0.704 |
| XGPIO3 @ 0.300 | **FAIL NO_FAR_RUN** | — | — | — | — |

At the **0.200 mm Default** clearance each net routes; at the **0.300 mm** blanket clearance the
flanked pin U3.6 cannot escape (pad-limited) and R54.1→via cannot complete (track-limited). The
0.300 mm blanket is a *proxy* for "keep 0.300 from BPP" but it over-constrains the **entire** haul
to clear 0.300 mm from **all** copper, which is exactly what the congested corridor cannot give.

## D — The single bounded evidence-backed alternative: per-region clr_pad/clr_trk split

D-269's 0.300 mm governs clearance to **BAT_PROTECTED_P**. Verified: **every** BAT_PROTECTED_P pad
is on **B.Cu and ≥9 mm** from the via/escape pocket; the only BPP copper near the F.Cu haul is the
**F.Cu trunk (tracks → clr_trk)**. The U3 pin-pocket escape is limited by **pad** clearance
(clr_pad). So `clr_pad = 0.200` (the true Default floor at the U3 pins, where no BPP copper exists)
+ `clr_trk = 0.300` (preserve the D-269 track clearance to the BPP trunk) is the correct-per-region
clearance and **not** rule weakening (the real full-board gate, D-269-aware, remains the arbiter).

`w/xgpio23_split_017.py` (both orders, live D-314 board):

| order | XGPIO2 | XGPIO3 |
|-------|--------|--------|
| XGPIO2-first | **FAIL NO_FAR_RUN** | FAIL NO_FAR_RUN |
| XGPIO3-first | FAIL NO_FAR_RUN | **FAIL NO_FAR_RUN** |

The split **fixes the escape** (U3.6 no longer NO_LEGAL_ESCAPE) but the 116 mm haul **cannot route
at clr_trk = 0.300** — the corridor down the D-313+D-314-congested board admits **one** 0.300 mm-
clearance haul, not two. This is the definitive result: the pair is a corridor-capacity wall.
**The one bounded alternative is spent.**

## E — Pair vs single at 0.200 mm (`w/xgpio23_pair200_017.py`, `w/xgpio23_single200_017.py`)

* **PAIR @ 0.200 mm uniform, both orders:** FAIL — the first net routes (116 mm), the second's
  far-run is **NO_FAR_RUN** (the two nearly-parallel hauls from adjacent resistors R53/R54 to
  adjacent vias contend for one corridor). Corridor conflict, independent of BPP.
* **SINGLE net @ 0.200 mm uniform (full-haul → BPP measured):**
  * XGPIO2 → via (55.300, 78.150), **haul→BPP min copper 0.6859 mm ≥ 0.300 → D-269 OK**
  * XGPIO3 → via (55.300, 77.700), **haul→BPP min copper 0.4739 mm ≥ 0.300 → D-269 OK**

So a **single** west XGPIO net at the 0.200 mm Default clearance is geometrically clean and keeps
the D-269 floor with margin (0.47–0.69 mm), unlike the D-313 EAST pilot whose 0.200 mm haul pinched
BPP to 0.244–0.281 mm (path-specific — the west haul does not approach BPP as closely).

---

## F — Why NOT promote, and why no rule/logic change

* The named candidate is the **XGPIO2+XGPIO3 pair.** It is walled three independent ways
  (0.300 mm: escape + far-run; 0.200 mm: parallel-haul conflict; split: haul NO_FAR_RUN at 0.300 mm
  clr_trk). No **stagger/offset** helps: `via_offset` (D-310) relocates the via SITE *after* escape
  and does nothing for a pad-escape box or a parallel-haul corridor conflict.
* A per-region **spatially-varying** clearance (0.200 mm except within X mm of BPP) would be
  substantial new `qrouter`/`connect_role` logic — **out of the bounded scope** the task authorises,
  and unnecessary because the single-net path avoids the conflict entirely. No genuinely-new blocker
  forces a generic fix here.
* **No rule weakening:** 0.200 mm is the Default netclass; D-269 (0.300 mm to BPP) is *satisfied* by
  the single-net path (measured 0.47–0.69 mm). Nothing below any floor was accepted.

## G — Integrity: authoritative board proven PRISTINE

`sha256` before and after the entire investigation: **`95bc07be…`** (byte-identical to committed
D-314). No `route`/`gate`/`promote` ran on the authoritative project; only gitignored
`checks/w/{SCR16,CLR17,SW200,SWSP,SGL200}_*` scratch copies were written; no orphan process.

* `router_regression.py` — **ALL CHECKS PASS (G1–G28), run twice, identical** (deterministic).
* `incremental_probe_006 … 016` — **all PASS**; `phaseB_bringup_probe_005` — **PASS**
  (669/66/104; 19 routed rest nets, 145 unrouted).
* Real-board DRC histogram unchanged: `{solder_mask_bridge:1, hole_clearance:5,
  lib_footprint_issues:199, unconnected_items:499}` — `clearance` stays 0.
* **D-269 / D-264 / DRU board-swap:** the current board **is** committed D-314 (same bytes), so the
  swap is trivially byte-identical — **no regression is possible** (nothing mutated). The D-314
  characterization of `d264` as intrinsically non-deterministic (unrelated U18 sense item) stands.

## H — Opportunity & Simplification Scan (bounded to the XGPIO west bank)

* **A (near-free capability):** one more community-GPIO net is connectable now — as a **single-net**
  0.200 mm increment. → FBV2-P2-018.
* **B (remove unnecessary constraint):** the blanket `clr_trk = clr_pad = 0.300` XGPIO recipe is
  **over-conservative** for west members whose haul naturally clears BPP by ≥0.47 mm. The correct
  clearance is the **0.200 mm Default with the real D-269-aware gate arbitrating** — simpler and it
  unblocks the corridor. The 0.300 mm blanket should be reserved for paths that actually approach BPP
  (as the east pilot did).
* **C (better implementation):** **do not force adjacent PAIRS** for the congested northern west
  members — the two parallel 116 mm hauls are the wall. Route the remaining west members
  **one net at a time**; the corridor holds one 0.300 mm-clearance haul or (better) one 0.200 mm haul.
* **E/F (recoverability / capacity):** `In2`/`In3` inner **signal** layers remain fully available; if
  the F.Cu corridor saturates further, routing XGPIO hauls on an inner layer is a future option — but
  that is a larger framework change (F/B-only today), deliberately **deferred, not forgotten.**
* No BOM / footprint / value / polarity / mechanical / firmware / UX change; DEVICE_SPEC unchanged
  (no product/hardware fact changed).

## I — Locked invariants preserved

No DRU / rule / clearance / stackup / topology / net / footprint / value / polarity / outline change;
no D-290 reauth; D-249 ≥1.20 BPP, D-269 0.300 / 0.60 BAT_MAIN, general 0.200 / applicable 0.150
signals, ≥0.25 hole-hole, D-275/D-288 bridge, In1/In4 GND roles, In2/In3 capacity, RF/USB/mechanical
reservations, every accepted increment (D-304…D-314) — all preserved (the board is byte-identical
D-314). Frozen `beta-full-reference-v1` untouched. Shared journal authoritative (104); no orphan
process.

## J — NEXT: FBV2-P2-018 (sharply defined)

**Route a SINGLE west XGPIO net at the 0.200 mm Default clearance** — recommended **XGPIO3** (via
(55.300, 77.700), haul→BPP **0.474 mm ≥ 0.300**, via exv 0.704 mm most-separated) or **XGPIO2**
(more BPP margin 0.686 mm, but via exv 0.256 mm to the XGPIO1 barrel — tighter). Register a
single-net GROUP at `clr_pad=clr_trk=200000` (NOT the 0.300 mm blanket — the haul clears BPP
naturally), `route`→`gate`→`promote` under the standard D-286 real full-board gate; the gate's
D-269-aware KiCad DRC is the arbiter of the BPP clearance. On promote add `incremental_probe_017.py`
+ `G29` (assert the net connected, copper legal, D-269 ≥0.300 to BPP by real DRC, ADD-ONLY). Do
**not** re-attempt the XGPIO2+XGPIO3 PAIR, and do **not** re-attempt `U11_PROG`/`PWR_SENSE` (hard
walls). 145 of 164 rest nets remain unrouted.

**Rollback:** none needed — no authoritative change. HEAD advances by documentation only.
