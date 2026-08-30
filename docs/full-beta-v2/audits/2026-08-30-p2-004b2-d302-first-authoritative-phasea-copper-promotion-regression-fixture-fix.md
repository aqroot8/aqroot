# FBV2-P2-004B2 / D-302 — First authoritative Phase-A copper promotion + router-regression fixture-compatibility fix

**Date:** 2026-08-30
**Decision:** D-302 (see `CTO_DECISIONS.md`)
**Start HEAD:** `56d0ebe` (D-301; pushed)
**Result:** COMMITTED — the verified `U11_RETARGET`→`C36.1` full-run board becomes the authoritative PCB; the router-regression harness is made compatible with a routed authoritative board; `router_regression.py` = ALL 79 CHECKS PASS (G1–G17). **Phase-A battery-block copper ONLY — the board is NOT fully routed.**

---

## 1. What was promoted

The working tree carried a verified promotion, byte-identical to the gitignored scratch `checks/w/FULL003T_004b2_u11retarget/`, produced by the full run
`AQROOT_U18BPP_JOIN=I3 AQROOT_U19CAP=1 AQROOT_LTCGATE_KO=1 AQROOT_U11_RETARGET=1 … 004b2_u11retarget`
(`checks/w/run_004b2_full.log`, `DRIVER_EXIT=0`, **PHASE A COMPLETE**).

It closes the D-301 terminal wall (`U11.2 escape: none exists`): `u11_escape()` retargets the `BAT_PROTECTED_P` high-current trunk far endpoint from the impossible ~55 mm cross-board `D9.1` run to a SHORT wide tap into the nearest already-on-net ≥1.20 mm BPP node copper **`C36.1` (63.750,74.325)** — B.Cu **7.905 mm** at 1.50 mm min trunk width. Per the 004B2 no-casualty refinement (D-301 §H → D-302) the U11.2 0.20 mm SENSE tie is KEPT, so U11.2 is already on-net with C36.1 and the tap is a **current-path reinforcement** judged by `reserve_gate(state['rn'], allow_dangle=False)` (ratsnest EXACTLY unchanged), not a new `gate()` connection; its journal entry carries `reinforcement:True` and is not counted as a made connection.

Run outcome: routed **74** / skipped-already-connected **101** / **ratsnest 704 (−77)**.

### Board stats (authoritative == artifact)

| metric | value | vs scratch artifact |
|---|---|---|
| PCB sha256 | `63a9bc54…f87d6ba9` | byte-identical |
| DRU sha256 | `2617cf9b…5eab268c` | byte-identical |
| tracks / vias | 432 / 54 | == |
| copper layers | 6 | == |
| placement | direction-2 (fingerprint `397dffe1f77e4d10`) | == |
| zones | 41 (2 GND copper + 4 authored keep-outs + 35 routing-annotation rule areas) | == |
| ratsnest (unconnected) | 704 | == |
| `phaseA_journal.json` | 77 entries (incl. `U11.2→C36.1` `reinforcement:True`) | == |

### Real KiCad DRC on the authoritative board

`{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, unconnected_items:499}`

**ZERO new copper DRC classes** from the promotion. Note the D-301 failing-scratch `track_width:1` is GONE: the regenerated D-249 high-current-trunk-width rule plus the real routed geometry resolve it. The remaining items are all pre-existing / not-yet-routed (hole_clearance, library footprint metadata, one solder-mask bridge, and the 499 still-open connections that Phase B and the rest of the board will address).

---

## 2. The DRU is the accepted rule set, not a relaxation

The authoritative DRU was regenerated (67 → 119 rules, byte-identical to the scratch). It **adds** the per-net escape / tap / stub / trunk / clearance rules that the routed copper requires and **renames** three generic rules to their specific accepted forms:

| family | count | what it authorises |
|---|---|---|
| D-249 | 11 | BPP high-current trunk width; U11/U14/U18 BAT-pin & fuel-gauge/test taps; BAT_SENSE Kelvin tap; bounded shunt stubs (0.20/0.40/1.00 mm) |
| D-257 | 39 | fine-pitch escape via / hole / annular-ring families for the named LTC/U19/Q3/REF/VREC escapes |
| D-258 | 2 | (escape family) |
| D-263 | 6 | BAT_RAW escape vias (D12.1→R77.1, R80.1→Q2.7) |
| D-264 | 2 | BAT_MAIN outer-layer split (never on In2 / In3) |
| D-266 | 6 | BAT_PROTECTED_P / BAT_SENSE Kelvin reservation vias |
| D-269 | 1 | BAT_MAIN current-path routed clearance |

Renames: `BAT_PROTECTED_P trunk width — local override, D-245` → `high-current trunk width — D-249`; `BAT_MAIN is outer-layer only` → In2 / In3 (D-264); `BAT_MAIN routed clearance` → current-path role (D-269).

**Why the old HEAD DRU is stale and cannot accompany the routed board.** The accepted route lays fine-pitch escape vias, bounded shunt stubs, Kelvin reservation vias and a ≥1.20 mm trunk that are each authorised by a *named, region-bounded* rule. Without those rules the routed geometry is measured against the generic netclass rules and KiCad DRC would spuriously flag legal, CTO-accepted copper (e.g. a 0.20 mm bounded stub under the generic ≥1.20 mm BPP floor). No rule floor is relaxed: D-249 ≥1.20 mm BPP, D-269 0.300 mm, the D-257 via ladder and the 0.60 mm BAT_MAIN floor are all intact.

---

## 3. The harness fix (routine engineering, not an owner decision)

Before the fix, `router_regression.py` reported **11 CHECK(S) FAILED** (G6 Q2_CS, G3 BAT_MID, G6 BAT_MID, G3/G4 LTC_OV, CONFLICTS U18.8/U18.9, G8-A/B/C/F, G9). All 11 fail for one reason: `fresh(work,name)` makes a full project copy, and post-promotion that copy carries the routed authoritative copper. The failing checks are **primitive router unit/regression vehicles** that lay a handful of tracks from scratch and then assert an EXACT ratsnest-fall, DRC-delta, widest-legal-escape or requested-pad connectivity — i.e. they implicitly assume a copper-EMPTY base:

- a CASES route (G2–G6) on an already-routed net has no ratsnest to fall and carries the 0.20 mm neck below the case floor;
- the CONFLICTS bisection hits routed copper near the pad;
- a G8 "route this pair" is already connected; G9's "a rejected rung leaves no copper" starts non-empty.

Temporarily restoring HEAD's 0-track board made all 11 pass with the *same lever code* — proving fixture coupling, not a routing regression.

### The fixture

A new function `scratch_clean(work, name)`:

- derives from the authoritative board's **same** placement / footprints / GND copper zones / rule areas / DRU+pro rule context (`fresh()` first, then strip);
- removes **only** routed copper — every board-level `(segment …)`, `(arc …)` and `(via …)` — as balanced S-expressions on the file *text*, so pcbnew is never mutated and the authoritative file is never touched (a pcbnew `Remove()`+`Save()` path segfaulted on this KiCad-10 build; the text strip is deterministic and side-effect free, so every clean fixture is byte-identical);
- keeps footprints, GND zones, the 4 authored `DoNotAllowTracks` keep-outs and the 35 `DoNotAllowTracks=False` routing-annotation rule areas. qrouter only treats `PCB_TRACK` and `DoNotAllowTracks` rule areas as obstacles (and never reads vias or GND zone-fill as obstacles), so the clean fixture presents the identical obstacle set the primitives saw on the pre-promotion empty board.

### Every `fresh()` caller audited and classified

| caller | check(s) | classification | why |
|---|---|---|---|
| G1 context copy | project context + DRC == authoritative | **AUTHORITATIVE (`fresh`)** | proves a plain copy carries the rule context so DRC matches the real board — must see the promoted copper |
| base scratch | base DRC-delta + base ratsnest ref, CONFLICTS, G7 | **CLEAN** | primitive references / bisection assume empty base |
| CASES G2–G6 | routed-case contracts | **CLEAN** | lay tracks from scratch, exact ratsnest-fall / DRC-delta |
| G8 / G8C | router-truth connectivity | **CLEAN** | route named pairs from scratch |
| G9 | rejected-rung leaves no copper | **CLEAN** | starts from an empty board |
| G10 worker (`RU.fresh`) | concurrency baseline == authoritative DRC | **AUTHORITATIVE (unchanged)** | must equal `base_a`, the authoritative routed DRC |
| G11 | bounded-probe search | **CLEAN** | unit test of the router budget, not the promoted board |
| G12 | baseline-order / placement DRC | **CLEAN** | isolates the placement-induced delta from routed copper |

The real-DRC / `u11_retarget_probe_004b.py` / exact-judge harnesses all read the authoritative file directly and are unchanged. **Copper is hidden from no check meant to validate the promoted board.**

### CONFLICTS re-pin (placement, not relaxation)

The promoted direction-2 placement MOVES U18: HEAD `(3.0, 72.4)` rot 90° → authoritative `(8.0, 66.5)` rot 180°. Re-measured at U18's authoritative pose on the clean fixture, `U18.8` / `U18.9` admit a widest legal escape of **0.245 mm** (was 0.250 mm at the old pose) — STILL far below their 1.20 / 0.60 mm floors, so both remain NO-LEGAL-ESCAPE. The land-pattern conflict is **preserved**; only the pinned constant tracks the accepted placement. `U14.2`/`U14.3`/`U11.2` did not move (0.240 / 0.200 mm unchanged).

### New contract G17

A standing guard that this was a fixture change, not a test weakening:

1. the authoritative board MAY carry promoted copper (432 tracks / 54 vias);
2. the clean fixture carries ZERO tracks / arcs / vias;
3. the authoritative file is byte-for-byte unchanged (sha256 + size + mtime) after fixture building;
4. placement / layers (6) / footprints (324) / zones (41) / DRU+pro are preserved in the fixture;
5. the authoritative DRC / connectivity is measured on the ROUTED board — auth ratsnest **704** < clean-fixture ratsnest **781**, and `base_a == base_ctx`.

`router_regression.py` = **ALL 79 CHECKS PASS (G1–G17)**, run twice, deterministic.

---

## 4. Verification performed

- `python3 router_regression.py` → **ALL CHECKS PASS** (79 PASS / 0 FAIL, G1–G17); run twice, identical.
- `python3 u11_retarget_probe_004b.py` → **ALL CHECKS PASS** (C36.1 tap routes at ≥1.20 mm, zero new DRC, ≥1.20 mm continuity C36.1→bridge→R75.2→U11.2 flare).
- Real KiCad DRC on the authoritative board → `{hole_clearance:5, lib_footprint_issues:199, solder_mask_bridge:1, unconnected_items:499}` (matches `run_004b2_full.log`).
- Board stats + placement fingerprint + PCB/DRU sha256 → **exact match** to `checks/w/FULL003T_004b2_u11retarget/`.
- Journal 77 entries incl. the `U11.2→C36.1` `reinforcement:True` entry.

---

## 5. Integrity & rollback

- Pre-promotion authoritative PCB `sha256 2235e273…d642d7e` (HEAD `56d0ebe`, 0 tracks) remains the parent of the D-302 commit; tags `beta-v2-p2-battery-pre-authoritative`, `beta-v2-p2-pre-sixlayer-authoritative` stand for rollback.
- D-290 untouched; the accepted `AQROOT_U18BPP_JOIN` (D-297), `AQROOT_U19CAP` (D-299/G14), `AQROOT_LTCGATE_KO` (D-301/G15), `AQROOT_U11_RETARGET` (D-302/G16), `place_003l` (D-285), the D-275/D-288 bridge, D-275 and D-277..D-301 preserved.
- Frozen `beta-full-reference-v1` untouched; `JLCPCB_READINESS` NOT edited (conservative recommendation only).

---

## 6. NOT all routing complete — next task

This promotes **Phase-A battery-block copper ONLY**. The board is **not** fully routed: ratsnest 704 / unconnected_items 499 remain (Phase B and the remaining nets are unrouted).

**Next: FBV2-P2-005 — Phase B bring-up on the promoted board.** Run the driver's Phase B against the now-authoritative routed base, screen full DRC (D-286), and promote only on a genuine gate PASS. No DRU/rule relaxation, no via below the D-257 ladder, no D-290 reauth, no topology/footprint/outline change.

**JLCPCB readiness recommendation (conservative, file NOT edited):** the board now carries its first accepted, DRC-clean authoritative copper, but it is Phase-A only — not fabrication-ready. Keep readiness at ~77 %; do not advance the JLCPCB gate until the board is fully routed and passes a full-board DRC with zero real copper violations.
