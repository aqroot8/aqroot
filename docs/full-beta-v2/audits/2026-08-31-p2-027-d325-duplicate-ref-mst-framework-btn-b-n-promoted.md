# FBV2-P2-027 / D-325 — DUPLICATE-REF MST framework fix + `BTN_B_N` promoted

**Date:** 2026-08-31
**Decision:** D-325 (governed CTO accept + promote; a bounded framework fix in
`incremental_router.py` only — `qrouter.py` untouched)
**Starting HEAD:** `45f45bc` (D-324; pushed; `origin/master` identical)
**Board before:** AUTH `sha256 a7bf8bdc11f1bc39303c6f6b6c801e3a4a575add64596cc4be20745c57f9f626`,
781 tracks / 68 vias / 6 layers / 41 zones / ratsnest 665 / journal 116.
**Board after (promoted):** AUTH `sha256 35d32343af5146b952e5390898764fd326742dc88b5e146cf0c5f292dc14a220`,
800 tracks / 70 vias / 6 layers / 41 zones / ratsnest 662 / journal 119.

## Outcome

The nineteenth rest-of-board incremental increment, and the FIRST that required a
framework improvement. A bounded, generic, deterministic **duplicate-ref MST**
fix let the router's MST and the gate's connectivity counter treat a footprint's
two same-numbered physical lands as distinct nodes. With it, `BTN_B_N` — the
navigation/boot button, the first net of the `SWx` user-button family — routed
and PASSED the real full-board gate, and was PROMOTED. The whole user-button
family is now routable by the proven mechanics.

## The precise root cause

`SW7` (Button_Switch_SMD:`SW_SPST_PTS645Sx43SMTR92`) is a 4-pin tactile switch
whose two mechanically-linked terminals BOTH carry pad NUMBER "1" on `BTN_B_N`, at
DIFFERENT physical locations — measured `(49.520, 96.750)` and `(57.480, 96.750)`,
7.96 mm apart (its two GND terminals are likewise both pad "2").

`qrouter.QBoard._scan` keys its pad table `self.pads[(net, "REF.NUM")] = dict`.
Two lands with the same net + pad number produce the identical key, so the second
overwrote the first: `net_pads()` returned only ONE `SW7.1`, and the MST never saw
the other land. D-323 routed only that one terminal; the real full-board gate
FAILed on connectivity (`open_edges 2→1`).

A **matching** collapse lived in the gate: `cmd_gate.net_open_edges()` counted
copper clusters with a `seen` set keyed by ref-string (`REF.NUM`), so it merged
the two physically-distinct `SW7.1` lands and under-counted the net's owed
ratsnest edges (it computed 2 where KiCad's real ratsnest owes 3 for 4 lands).

## The fix — bounded, generic, deterministic; `qrouter.py` untouched

Both halves live entirely in `incremental_router.py`. `qrouter.py` is NOT touched,
so every `router_regression` G-contract that re-routes through `QBoard` (G1–G35)
stays byte-identical.

1. **`physical_net_pads(qb, netfull)`** sources MST nodes by stable PHYSICAL
   identity `(ref, x, y)`, recovering any land the `(net, tag)`-keyed `qb.pads`
   dropped (rebuilt field-for-field identically to `_scan` via `_rr_pad_dict`).
   Ordinary nets — every pad number unique — return exactly the `net_pads()` dict
   objects (verified SAME objects), so their routing and journal are byte-
   unchanged. `cmd_route` sorts the pads by `(ref, x, y)` (a superset of the old
   ref-only order; ties never fire for unique nets) and runs the same MST.

2. **`cmd_gate.net_open_edges()`** was rewritten as a physical-pad union-find
   (nodes keyed by `(ref, x, y)`, copper adjacency from `GetConnectedItems`), so it
   counts copper clusters over PHYSICAL lands — matching KiCad's own ratsnest,
   which owes one edge per physical land. A net whose lands all carry unique pad
   numbers is counted exactly as before.

The change ADDS nodes only for a genuinely duplicated pad number. It weakens no
rule, netclass, clearance, via geometry, placement, footprint, or topology.

## The increment

`BTN_B_N` = {`SW7.1` button (two F.Cu lands), `R9.2` pull-up (B.Cu), `U2.18`
expander (B.Cu)}. The MST hubs on `R9.2` → BOTH `SW7.1` lands (two 0.60/0.30
Default THROUGH vias at `(48.300,96.750)` and `(56.300,95.600)` in the OPEN south
button field; the D-306/D-308 In1/In4 re-pour mechanic runs once for the two
anti-pads) + one SAME-LAYER B.Cu run `R9.2→U2.18`. Default netclass (0.200 mm).
Realized: **19 tracks** (3 F.Cu + 16 B.Cu), **2 through vias**.

## Gate (real full-board, all 10 checks PASS)

- no Phase-A copper deleted or altered; every new copper item is a target-group
  net; copper actually added (21 items); only In1/In4 GND planes re-poured.
- **target net fully connected by copper: `BTN_B_N` pads=4 `open_edges 3→0`** —
  all four physical pads (both `SW7.1` lands + `R9.2` + `U2.18`) in one cluster.
- all Phase-A requested pairs still copper-connected.
- **ratsnest dropped by exactly the requested connections 665 → 662 (−3)** — the
  true KiCad count for a 4-land net.
- no new DRC violation class; no DRC class increased; `unconnected_items` 499→499.

Promote: AUTH `a7bf8bdc…` → `35d32343…`, journal 116 → 119 (3 REST_INC edges).

## Integrity + tests (deterministic, twice)

- `router_regression.py` ALL PASS **G1–G37**, deterministic across two runs.
  - **G36** pins the increment: all four pads copper-connected (both `SW7.1`
    lands joined to the `R9.2` hub), copper legal (19 trk 0.200 mm = 3 F.Cu +
    16 B.Cu, exactly 2 0.60/0.30 through vias), both vias ≥ 0.80 mm from every
    barrel (min 2.915 mm), ADD-ONLY.
  - **G37** pins the framework lever: a duplicate pad number yields distinct
    nodes (4 lands, two `SW7.1`); the MST spans all 4 lands (3 edges); an ordinary
    unique-pad net is byte-identical (SAME dict objects, no phantom node);
    `physical_net_pads` is deterministic across calls.
  - **G1–G35 unchanged** — the fix touches no QBoard-routing path.
- `incremental_probe_006..024` + `phaseB_bringup_probe_005` (800/70/119; 27 routed
  rest nets, 137 unrouted) ALL PASS. `incremental_probe_024.py` is new and proves,
  decisively, that BOTH `SW7.1` lands are copper-joined to the `R9.2` hub and all
  four physical pads form one cluster. `live_fingerprint.py` bumped ONCE to D-325.
- Independent kicad-cli DRC identical to D-323 (`solder_mask_bridge:1 +
  hole_clearance:5 + lib_footprint_issues:199 + unconnected_items:499`; 0
  `clearance`).
- D-269/D-264/DRU A/B swap (committed D-323 board vs promoted D-325 board): `d269`
  FAIL(2) and `dru` FAIL(2) identical on BOTH; `d264` up-to-2-failed, B no worse
  than A. All are the documented western battery/power-tree synthetic-probe
  intrinsic flake (BAT_RAW TAP, Q3.6→R75.1 In2), NONE involving `BTN_B_N` (which
  sits in the south button field 10.68 mm clear of `BAT_PROTECTED_P`). No
  regression. `incremental_baseline_006.json` left stale-by-design.

## Opportunity & Simplification Scan

The duplicate-ref lever is shared by both the router (`physical_net_pads`) and the
gate (`net_open_edges`), so the whole `SWx` user-button family (`BTN_A/UP/DOWN/
LEFT/RIGHT_N` + `Net-(SW9-A)`, ~6 remaining genuine nets) is now routable by the
same proven F/B same-layer + through-via mechanics — the largest coherent
remaining functional block is unlocked. No other repetitive-maintenance
consolidation was due (one fingerprint bump, one new probe, two new G-contracts,
all expected for a promotion).

## Governance

No BOM/footprint/value/polarity/mechanical/firmware/UX change; DEVICE_SPEC
unchanged. **Open owner decisions: NONE** (autonomy continues). All locked
invariants preserved (D-249/D-257/D-269/D-275/D-288/D-290, In1/In4 GND roles,
In2/In3 capacity, RF/USB/mechanical reservations, D-304..D-324); frozen
`beta-full-reference-v1` untouched; journal authoritative (119). PCB routing
~19 %, overall ~76 %, readiness ~78 % (JLCPCB file unchanged).

**NEXT FBV2-P2-028:** route the next `SWx` button net now that the family is
unlocked (a fresh screen + geometry vet first), or the next genuinely-clean
functional open-region net, under the D-286 gate + adding `incremental_probe_025`
+ `G38` on promote.
