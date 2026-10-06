# D-806 IMPLEMENTATION REPORT — JLCPCB MANUFACTURING-READINESS REVISION

Branch `d806-jlcpcb-manufacturing` (worktree `/home/aqroot8/w/d806-jlcpcb`).
**Candidate only. Not promoted to `aqroot-demo`. Nothing ordered, paid, uploaded or submitted.
No fabrication, assembly or non-cancellable procurement is authorized.**

## 1. Frozen D-805 parent identity

| item | value |
|---|---|
| D-805 delivery identity (parent) | `a8837f71667f2f737c69dab47b33dd410bdbd7e7` — D-806 descends from it (verified `merge-base --is-ancestor`) |
| D-805 source milestone beneath it | `4a3585202606de82d71b19960e35a86964c92f87` (ancestor, verified) |
| D-805 board / MANIFEST | `0689d6e6…87c1` / `4f027e25…7ccf` |
| D-805 worktrees | `d805-delivery-artifact` `a8837f71`, `d805-interface` `4a358520`, `d804-u9` `466a5058`: HEAD and status unchanged (see §14). `aqroot-demo` `576c8cec` untouched (it already carried one untracked `mechanical/` entry before D-806). |

Change plan and baseline written before any edit: `hardware/demo/manufacturing/evidence/d806-change-plan.md`.

## 2. Exact D-806 changes

| # | change | file(s) |
|---|---|---|
| G1 | `J2` translated (0, −0.150 mm): (15.000, 142.700) → (15.000, 142.550), rot 180 unchanged; its 13 pad-attached track ends moved with their lands. Outline NOT changed. | board |
| G2 | `U9` eight corner lands (1, 8, 9, 16, 17, 24, 25, 32) heel-trimmed 0.030 mm: 0.75 → 0.72 long, centre 0.015 mm outward; toe, width, pitch, other 24 lands, EP, pose, nets unchanged | board + library master `ST25R3916_AQET.kicad_mod` (identical; descr records the trim and the DS12484 Table 134 L ≤ 0.50 basis) |
| G3 | 35 vias 0.35/0.20 → 0.40/0.20 (drill unchanged) | board |
| G4 | DRU: J2 edge licence 0.20 → **0.25 mm**; U9 intra-footprint floor 0.12 → **0.1524 mm** (KiCad now enforces JLCPCB's numbers natively) | `.kicad_dru` |
| G5 | Zones refilled to their fixed point (2 passes; deterministic: two independent applies → same board `0e59fb64…`) | board |
| — | Script: `manufacturing/apply_d806_jlc_corrections.py` (report `evidence/d806-apply-report.json`) | |

Consequence declared, not intended: the 0.150 mm J2 shift narrows a pre-existing neck of `F +3V3 PLANE`
above `J2.9`'s rear shell land below the pour's 0.20 mm minimum width, so a **69.67 mm² lobe south of
R113 with no pad, no via and no track end** is removed by the filler as an isolated island
(`evidence/d806-inert-pour-lobe.txt`). Shifts of 0.100 and 0.120 mm sever it too (the D-805 neck was
marginal). Connectivity, unconnected set and ledger are unchanged. Owner review requested.

New/changed tooling and gates: `checks/jlc_manufacturing_contract.py` (new), `jlc_drawings.py` (new),
`build_d806_rfq_packages.py` (new), `board_profile_spec.json` (new, frozen from a8837f71),
`export_fab_package.py` (vendor drawings + profile wording), `checks/interface_datum_contract.py`
(declared J2 inset), `interface_datums.json` (J2 datum), `protected_copper.py` +
`checks/contract_regression.py` (declared via-growth word), `Firmware/src/hw/aqroot_demo_board.{h,json}`
(digest only).

## 3. J2 before / after

| | D-805 | D-806 |
|---|---|---|
| shell land `J2.9` to routed J2 tab edge (board polygons) | **0.213 mm** | **0.363 mm** |
| same, Gerber F_Cu flashes vs arc-aware Edge_Cuts | 0.213 mm (control) | **0.363 mm** |
| any J2 land to edge | 0.213 | 0.363 |
| JLCPCB hard ≥ 0.25 / D-806 target ≥ 0.30 | FAIL / FAIL | **PASS / PASS** |

Card access: card-entry face 150.850, 0.150 mm inside the tab edge (declared `face_inset_from_tab_edge_mm`,
measured by ID2); card travel envelope wholly off-board from the tab edge and meets no courtyard (SW4
named); latched card 0.95 mm inside the exterior, ejected 3.05 mm proud. **SW4 unchanged** (ID4). No stop
condition. The tab, its fillets and the 0.5 mm tab-to-wall gap are unchanged.

## 4. U9 before / after

| | D-805 | D-806 |
|---|---|---|
| U9 window different-net min, Gerber (independent extractor) | **4.892 mil** (0.12425 mm), 4 corner pairs | **6.562 mil** (0.16668 mm) |
| same, board polygons over all copper layers (ERROR_OUTSIDE) | 4.89 mil | **6.522 mil** |
| modelled post-CAM (raw − 1.2 mil, JLCPCB's 5.2 → 4.0) | 3.69 mil | **5.362 mil** |
| board-wide Gerber min different-net gap | 4.892 mil (U9) | **5.906 mil** (vendor SOT-563 / MSOP / TPD4E lands, none at U9) |
| gaps < 5.2 mil anywhere / < 4.0 mil | 4 / 0 | **0 / 0** |

NFC architecture, matching network, antenna, U9 placement and every U9 net/route unchanged
(rf_symmetry contract identical to D-805). U9 mask dams at the corners leave the < 0.125 mm table.

## 5. Via geometry audit (JLCPCB: outer ≥ hole + 0.20 mm)

Population: **every `PCB_VIA` on the board (915)**, and independently every Excellon PTH round hit
carrying an F_Cu/B_Cu `ViaPad` flash (915). Plated component holes reported separately (all meet it).

| | D-805 | D-806 |
|---|---|---|
| vias below the rule | **35** (all 0.35/0.20, 0.150 mm) | **0** |
| of which in a solderable land | 6 (`U9.16` D-649 bridge, `R2.1`, `U11.11`, `Q3.3`, `J3` A4/B9 and A9/B4 D-531 POFV) | 0 |
| DRC after growth + refill | — | 0 new violations; every licence rule area still encloses its barrel |

Via-in-pad / land-intersecting barrels still require resin fill + planarize + cap (POFV); the MANIFEST
lists them (`via_in_pad`).

## 6. Board thickness verdict — **HOLD (owner approval required)**

`docs/full-beta-v2/assembly/D806_BOARD_THICKNESS_POSITION.md`. The repository does not prove 1.44–1.76 mm
compatible: **J6 (JST B2B-PH-K-S, fitted THT) is rated for 0.8–1.6 mm board** (`vendor/JST/jst-ph-connector-ePH.txt:25`),
exceeded above 1.60 mm (the D-805 upper bound 1.6744 already exceeded it — pre-existing finding); no GCT
USB4105, C&K JS102011SAQN or PTS645 drawing is archived; no boss/rail/rib Z dimension exists; J5's Z column
fits on paper at 1.76 (22.87 / 23.0 mm) but the enclosure CAD does not exist. Acceptance stays
1.5744 ± 0.10 mm; JLCPCB's ±10 % is a vendor exception; the RFQ asks for their achievable band and a
≤ 1.60 mm maximum. No enclosure tolerance was invented.

## 7. Stepped-profile documentation

`hardware/demo/fab/aqroot-Demo-board-profile.pdf` (A3: 1.8:1 dimensioned view, 5–6:1 tab details,
every primitive tabulated, plated routed slots, "what CAM must not normalise") and
`aqroot-Demo-board-profile.json`; fab notes heading now names the three features (two bottom tabs, east
step) instead of "stepped profile". Profile = 16 lines + 8 arcs (4 drawn R1.000 inside fillets, 4 R0.500
outside corners), 2 sharp inside + 6 sharp outside corners, 4 plated G85 slots. JLC6 proves board ==
declared spec == frozen D-805 == Edge_Cuts Gerber == packaged JSON.

## 8. Assembly-reference mapping proof

Silkscreen untouched. New `aqroot-Demo-assembly-locator-{top,bottom}.pdf` (A3, 2.5:1, bottom mirrored,
every fitted reference labelled at its CPL centroid and sized to its own courtyard, 10 mm lettered grid,
index pages) and `aqroot-Demo-assembly-ref-index.csv`. JLC5: **251/251 fitted references** (83 top, 168
bottom) indexed exactly once, at the CPL coordinates and side, matching the board footprint; 0 DNP
presented as fitted; every reference present in its side's PDF text; board sha256 printed. (D-805's KiCad
plots, still included, lacked `MK1` in the text layer and were illegible at 0.60 scale.)

## 9. BOM / schematic / netlist identity

10/10 `.kicad_sch` byte-identical to a8837f71; `BOM-assembly`, `BOM-full`, `DO-NOT-POPULATE`,
`NON-PURCHASED`, `OFF-BOARD` byte-identical; JLCPCB BOM byte-identical to the D-805 JLCPCB BOM; JLCPCB CPL
differs on the J2 row only. Pad→net identity unchanged on every footprint (bounded diff); KiCad parity
multiset identical (246 warnings, 0 errors). `.kicad_pro` byte-identical.

## 10. Moved components

**J2 only**, by exactly (0, −0.150 mm). Bounded diff `evidence/d806-bounded-diff-vs-d805.json`: footprints
changed {J2}; pad geometry changed only U9.1/8/9/16/17/24/25/32; tracks 3485 → 3485 (13 out / 13 in, all
inside the J2 window); vias 915 → 915, 35 grown in place, 0 other via changes; zone outlines / rule areas 0
changes; Edge.Cuts / drawings 0 changes. SW1, SW4, J3, J5, J8, SW9, U1, BOSS1/2, radios unchanged (ID4/ID5).

## 11. DRC / CAM / contracts / tests

| gate | result |
|---|---|
| KiCad DRC `--severity-all --schematic-parity` | 199 `lib_footprint_issues` warnings (identical items), **0 errors**, 17 unconnected (same pads/nets; KiCad names a different neighbouring track of 2 identical nets), 246 parity warnings identical |
| DRC with the 5 ignored rules promoted | 2 missing_courtyard + 5 track_not_centered_on_via — identical to D-805 |
| `jlc_manufacturing_contract` JLC1–JLC6 | **PASS**, targets met; **16/16 destructive controls refuse** (frozen D-805 board + Gerbers fail JLC1–JLC4; untrimmed U9 corner, pushed U9 flash, shrunk via, missing/offset/DNP/absent ref, changed fillet, straightened tabs all refused) |
| `interface_datum_contract` ID1–ID9 | **PASS**; 9/9 controls incl. new "J2 at its D-805 flush position" and "J2 0.1 mm beyond declared inset" |
| Gerber/Excellon CAM (no KiCad) | open ends 0, shorts 0, diff-net crossings 0, gaps < 4 mil 0, < 5.2 mil 0; split nets 11 = D-805 list; multi-net components 0 |
| FAB1–FAB16 | **16/16 PASS** |
| guarantee evidence | 17/17 keys, 37/37 controls, PASS |
| rail ampacity | all_ok; every rail entry identical to D-805 |
| routing ledger | population / approved-NC / approved-unrouted / connectivity / sheet summary identical; per-net groups identical in membership (only J2 / U9 corner pad coordinates moved) |
| 19 standing contracts vs d805 (`evidence/d806-contract-regression.json`) | **19/19 PASS**, all ran, all children exit 0, not vacuous, baseline complete. Substantive differences, each a D-806 act: placement (claimed J2 move + releases), keepout_stackup (In1/In4 area −1.97 mm², the 30 grown non-GND via clearances), pour_partition (one claimed moved ref), pour_bond (island renumbering after the inert lobe; P1–P4 pass), protected_copper (declared via-growth word: 4 BAT_* vias forgiven; `identical` strictly False; undeclared-row control FAILS as required — `evidence/d806-protected-copper-undeclared-control.json`), fab_provenance (36 vs 31 artifacts: the 5 vendor drawings), demo_feature (release id D-806), firmware_hw_map (a temp-dir path name only). Identical to D-805 elsewhere (rf_symmetry, connection_width, and all other rows apart from input identity) |
| PlatformIO (git archive of the content commit, empty dir) | **5/5 SUCCESS**: aqroot-demo (release image `fe4165b8…10d0e2`), aqroot-demo-fap01 (`ac8d6e65…085b75`), esp32-s3-aqroot, wokwi, esp32-s3-aqroot-dm; only the board digest string changed in `Firmware/src/hw/aqroot_demo_board.{h,json}` |

## 12. Manufacturing package paths / hashes

| artifact | sha256 |
|---|---|
| board `aqroot-Beta-v2.kicad_pcb` | `0e59fb64fe72b0a54b9feea96c19bcaec2db52a82a871bcec270e064d7fda547` |
| `.kicad_dru` | `1a3b5f516cf81a3d157860ccf3aec4bc7baa4592009c5aef3e20c525f8f3110f` |
| `.kicad_pro` (unchanged) | `9b758a753f771b953ae3871b3ed2dc596153f2dc414759686c2cd8b3507e926b` |
| `hardware/demo/fab/MANIFEST.json` (36 files, 25 deterministic) | `651ceb4851e1097b87eb47ebfec1257a8752ae6a782f97ede4aa62790c19db4f` |
| `delivery/AQROOT_D806_JLCPCB_RFQ.zip` (19 entries) | `bf5ad23cb3f3952d3ae56151375e8c66de5f78a4ea5d3bae800da29e871489db` |
| `delivery/AQROOT_D806_Prototype_PCBA_RFQ.zip` (vendor-neutral, PCBWay et al.) | `700165646cd8476879a243d8214fdd3396bfca432dfcbab60d5460fa020807e5` |

Regeneration into a scratch directory reproduces all 25 deterministic artifacts (normalised sha256) and
the locator/profile PDFs and fab notes byte-for-byte; only KiCad's four timestamped PDF plots differ, as at
D-805. The RFQ packages are byte-deterministic (two builds, identical zips); each carries SHA256SUMS
(verified). The JLCPCB handoff (`RFQ_REQUIREMENTS.txt`) states: 2 PCBAs (bare MOQ may be higher); exact
MPNs, no substitution without written approval; production-file confirmation and parts-placement
confirmation REQUIRED MANUAL, no auto-confirm; no change to copper/pads/drills/mask/paste/slots/profile/
placement/stackup/BOM without written approval; J2 requirement and achieved 0.363 mm; U9 pre-CAM and
Gerber evidence; POFV requirement; profile reference; thickness HOLD; edge-rail strategy (no V-score,
finished outline preserved, `D806_PANEL_AND_EDGE_RAIL_STRATEGY.md`); no fabrication/procurement authorized.

## 13. Procurement shortages / consignment

`docs/full-beta-v2/assembly/D806_SOURCING_DECISION_RECORD.md` (D-803 live sweep 2026-09-26, 10 days old;
refresh is a pre-order gate). Short at JLCPCB for 2 PCBAs: U9 ST25R3916-AQET (0), U18 LTC4368IMS-1#TRPBF (0),
U19 TLV7032DDFR (0), U2/U3 PCAL9535APW,118 (1 of 4), D2/D4/D5 TPD4E1B06DRLR (2 of 6), L4 74438357010 (0),
MK1 DMM-4026-B-I2S-R (0, LCSC "no longer manufactured"; DigiKey Active), R40 RT0603BRD07189KL (MOQ 302 >
stock 143), J5 SSQ-124-02-G-S-RA (0, JLC no-buy; Samtec Active). Recommendation: consign the exact MPNs
(class b) with vendor machine placement for every fine-pitch/RF/power part; J5 consigned and hand-soldered
post-reflow (class d); R40 by owner decision (MOQ buy or consign). No class (c) equivalent proposed. ESP32-S3-
WROOM-1-N16R8 in stock (22,421), kept exactly. No procurement authorized.

## 14. Commits and push

* Content commit **`3168738745e86e783ba0f077e0ee74cca97c6621`** on `d806-jlcpcb-manufacturing`, child of the frozen D-805 parent `a8837f71`; **pushed** to `origin/d806-jlcpcb-manufacturing` (new branch).
* Post-commit: committed board `0e59fb64…`, MANIFEST `651ceb48…` and both RFQ zips byte-identical to the gated files; tree clean.
* Identity commit: the commit that records this report's final form and `evidence/d806-review-target.json` (a commit cannot contain its own SHA); pushed to the same branch.
* D-805 / D-804 frozen worktrees: HEAD, branch and status byte-identical before and after (`d805-delivery-artifact` a8837f71, `d805-interface` 4a358520, `d804-u9` 466a5058); `origin/d805-*` refs unchanged; `aqroot-demo` not touched, not merged into.

## 15. Recommendation

**GO — send D-806 back to JLCPCB (`delivery/AQROOT_D806_JLCPCB_RFQ.zip`) and PCBWay (`delivery/AQROOT_D806_Prototype_PCBA_RFQ.zip`) for REQUOTE / ENGINEERING REVIEW.** Every JLCPCB geometric finding is closed with margin and gated (J2 0.363 mm vs ≥ 0.25; U9 6.56 mil vs ≥ 5.2; vias 0/915 below hole + 0.20; refs mapped 251/251; profile explicit).

**HOLD — fabrication / assembly / procurement**, pending the owner's written decisions on: (1) board thickness (JLCPCB 1.6 mm ±10 % vs acceptance 1.5744 ± 0.10; J6 rated ≤ 1.6 mm board); (2) the vendor's returned production files, panel/edge-rail drawing and placement preview (REQUIRED MANUAL gates); (3) consignment of the short lines (U9, U18, U19, U2/U3, D2/D4/D5, L4, MK1, J5; R40 MOQ) after a fresh sourcing refresh; (4) review of the two taught gate words (ID2 J2 inset; protected_copper via growth) and the inert pour lobe; plus the standing D-805/D-804 HOLD items (B01–B14, FA01–FA10, enclosure apertures).

**Manufacturing remains UNAUTHORIZED.** Nothing in D-806 orders, pays for, submits or authorizes
fabrication, assembly or non-cancellable procurement.
