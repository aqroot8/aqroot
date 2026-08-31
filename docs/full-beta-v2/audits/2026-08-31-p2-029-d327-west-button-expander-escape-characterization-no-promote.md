# FBV2-P2-029 / D-327 — west-button expander escape characterization (no promote)

**Date:** 2026-08-31  
**Starting/ending board:** `sha256 adbea36b8bbcfa393f2810e989c93dbcfab4052b5538f9a7169bc71ff98b3e3f`, 821 tracks / 71 vias / 6 layers / 41 zones / ratsnest 659 / journal 122.  
**Decision:** CHARACTERIZATION; authoritative copper unchanged.

## Outcome

GPT executed the first direct-hardware transition task under the new execution-ownership policy. Three remaining navigation-button nets were independently screened, scratch-routed, and gated. None completed legally at the existing Default 0.200 mm rules, so none was promoted.

- `BTN_DOWN_N` was selected first because it had the lowest measured congestion among the west buttons. Its long B.Cu west haul routed, but the short same-layer `R5.2↔U2.14` edge returned `NO_PATH` even at the 0.05/0.025 mm fine grids.
- `BTN_RIGHT_N` was the measured escape-room alternative. It produced no legal copper and retained `open_edges 3→3`.
- `BTN_A_N`, the shortest remaining west cross-haul, routed its switch-land edge and cross-layer haul but the short `R8.2↔U2.17` B.Cu edge returned `NO_PATH`; the real gate correctly rejected the partial result (`open_edges 3→1`, ratsnest drop −2 where −3 was required).

The common blocker is the pull-up/PCAL9535A expander-side local escape, not the long west haul. No rule, clearance, placement, footprint, topology, or layer role was weakened. Scratch boards only were modified; authoritative PCB and journal remained byte-identical to D-326. The stale-by-design `incremental_baseline_006.json` was restored.

## Integrity evidence

- `router_regression.py`: ALL CHECKS PASS G1–G38, twice.
- `incremental_probe_006..025` and `phaseB_bringup_probe_005`: ALL PASS.
- Independent `kicad-cli pcb drc`: identical D-326 histogram (`lib_footprint_issues:199`, `hole_clearance:5`, `solder_mask_bridge:1`, `unconnected_items:499`; copper clearance remains zero).
- Live PCB sha rechecked as `adbea36b…`; 821 tracks / 71 vias / ratsnest 659 / journal 122.

## Opportunity & simplification scan

The three failures collapse to one reusable lever: a bounded, deterministic endpoint-escape improvement for the B.Cu pull-up/expander cluster, with ordinary nets byte-identical when the lever is irrelevant. This is higher value than testing `BTN_LEFT_N`, whose local escape evidence is worse. The next task is to diagnose that endpoint geometry precisely, add a focused regression contract, and promote the first west button only if the full D-286 gate passes.

No BOM, schematic, footprint, product-feature, mechanical, or DEVICE_SPEC change. Open owner decisions: NONE. JLCPCB readiness remains 78.
