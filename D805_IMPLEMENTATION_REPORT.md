# D-805 IMPLEMENTATION REPORT — interface datum correction (J3 / J2 / SW9)

Branch `d805-interface-fixes`, frozen base `466a5058c7b5b5835ac4427b0db0b2f26d576d43` (D-804 identity).
**Candidate only. Not promoted to `aqroot-demo`. Nothing sent to PCBWay. No manufacturing authorized.**

## 1. Result

| item | value |
|---|---|
| J3 USB-C | (43.000, 147.325), rot 0°, mating face +Y on the J3 tab edge (Y 151.000) |
| J2 microSD | (15.000, 142.700), rot 180°, card entry +Y on the J2 tab edge (Y 151.000) |
| SW9 power slide | (75.200, 86.500), rot 90°, actuator +X, tip at x 79.000 |
| outline | main bottom edge Y 148.000 unchanged; `J2_TAB` x 6.0..24.0 and `J3_TAB` x 36.5..49.5 to Y 151.000 (1.0 mm drawn inside fillets, 0.5 mm outside corners) |
| board bbox | x 0.000..77.000, y 0.000..151.000 mm (KiCad edge bbox −0.05..77.05 × −0.05..151.05 incl. the 0.05 mm stroke) |
| board sha256 | `0689d6e677df530d84d3986f4a8450fa7ed39272535b2cfc1ecfc6ae857887c1` |
| MANIFEST sha256 | `4f027e255f161350c412166c23bdf783a45caf432578ccc9f876de4078e07ccf` |
| changed components | **J2, J3, SW9 only** (J2 also carries the corrected footprint annotation; pads unchanged) |
| unchanged, verified | SW1 (28.3, 142.0), SW4 (13.5, 122.5), J5 (65.9, 39.21), J8 (73.4, 76.4), U1 (57.75, 128.0), BOSS1 (41, 136), BOSS2 (60, 3), radios U7/U8, NFC U9, IR, every other footprint: pose identical |
| schematic / netlist | **identical** — all 10 `.kicad_sch` sha256 equal to D-804's MANIFEST; 212 nets, same names; pad→net identity on all 315 footprints; KiCad schematic-parity multiset identical (246 warnings, 0 errors) |
| BOM | `BOM-assembly.csv`, `BOM-full.csv`, DNP list byte-identical; CPL changes for J2, J3, SW9 rows only |
| stackup / DRU / .kicad_pro | byte-identical to D-804 |

No stop condition occurred: J2 did not need SW4 moved (ID2 card-travel envelope meets no courtyard), J3 did not need U1 moved, SW9 did not need J8/radio/power moved, no schematic/netlist/BOM change, no growth beyond the two declared tabs.

## 2. How it was built

1. `hardware/demo/manufacturing/apply_d805_interface_moves.py` (stage 1): moves, tabs, J3 POFV rule areas, local rip of the three parts' nets inside their own windows.
2. The earlier, stopped D-805 session's scratch (`/tmp/d805/workf`) carried valid local re-routes (J2 SPI/SD, J3 USB D±/SHIELD, SW9). It was inspected once: only J2/J3/SW9 moved, every copper difference lay inside a D-805 window, DRC showed zero clearance/short errors. It was adopted as the base. Its temporary `D805_TMP_ROUTER_FENCE` rule area was **removed** (it does not ship).
3. Six remaining local joins were laid with a small A* router on a 0.05 mm grid (`evidence/d805-local-router.py`, `evidence/d805-local-joins.py`): USB_VBUS_RAW (C20/R35 side to J3 A4, B.Cu 0.5 mm), CC1, CC2, I2C_SDA_INT, WAKE_INT_N, I2S_LRCLK. In2 preferred; no via may land in a solderable land. Dead stubs and barrels left joining one layer only were removed.
4. The board's J2 instance was brought to the corrected library master (`evidence/d805-j2-footprint-update.py`): graphics/annotation only, pads asserted identical.
5. Zones refilled to their fixed point (a further fill is byte-identical).

Bounded diff (`evidence/d805-bounded-diff-vs-d804.txt`): tracks/vias 4469 → 4465; 167 objects out, 167 in, every one inside the J2, J3 or SW9 window or the J2–J3 bottom band; zones: only the two J3 POFV rule areas moved with their pads; Edge.Cuts 8 → 24 items (the two tabs).

## 3. Gates (all on the final board `0689d6e6…`)

| gate | result |
|---|---|
| interface datum `checks/interface_datum_contract.py` | **ID1–ID9 PASS** (incl. ID9 non-vacuity: D-804 J2/J3 turned back 180°, SW9 at its D-804 spot, 0.1 mm J8 nudge, widened tab, wrong tab gap — all refused) |
| KiCad DRC `--severity-all --schematic-parity` | **0 errors of any violation class**; 199 `lib_footprint_issues` warnings (= D-804); **17 unconnected = the D-804 declared set** (16 DNP-reference pads + owner-approved U11.3), identical net multiset; 246 parity warnings, 0 parity errors, identical multiset |
| DRC with the 5 ignored rules promoted | 2 missing_courtyard (BOSS1/2) + 5 track_not_centered_on_via — identical to D-804, none in the D-805 area |
| D-805 moved-interface nets | **all routed**; no new unconnected item |
| routing ledger | population / approved-NC / approved-unrouted / connectivity / sheet summary **identical to D-804** (174 retained, 173 connected, U11.3 approved open, 0 unapproved) |
| 19 standing contracts vs d804 | **19/19 PASS**, all ran, all children exit 0, not vacuous; every substantive difference is a D-805 change (`evidence/d805-contract-regression.json`) |
| FAB1–FAB16 | **16/16 PASS** |
| guarantee evidence | 17/17 keys, 37/37 controls |
| rail ampacity | all_ok; USB_VBUS_RAW improved (19.876 → 17.668 mm, 18.87 → 16.68 mΩ) |
| Gerber/Excellon CAM extract (no KiCad) | open ends 0, different-net gaps < 4 mil 0, crossings 0, shorts 0 on all six layers; split nets 11 = D-804 list |
| via-in-land | 134 lands (D-804: 136); J3 A1/B12 GND barrels gone; J3 VBUS POFV barrels moved with their lands; none added |

## 4. Gate changes — owner review requested

Two placement-contract clauses had no word for acts D-805 legitimately performs. Each was taught that word narrowly, and each has a control proving it still refuses the defect (`evidence/d805-placement-word-controls.json`):

* **PL9** — a barrel that *travelled with its land* (same pin, net, diameter, rotated land-relative offset ≤ 1 µm) is inherited, not swallowed. Applies to J3's two D-531 VBUS POFV barrels. Control: the same barrel 0.100 mm off-centre is still swallowed.
* **PL4 `--overlap-ok A:B`** — a coarse footprint-box overlap may be *declared*, and the declaration is honoured only if KiCad's courtyard polygons on every shared side are disjoint. Used for J2/R113: J2's pin-1 silk dot reaches 0.065 mm into R113's box, while the courtyards stand **0.530 mm** apart (KiCad `courtyards_overlap`, an error-level rule, reports nothing). Control: with R113 pushed until the courtyards touch, PL4 still fails.
* `export_fab_package.py` now reads arcs in `Edge.Cuts`; without that, the fab notes silently dropped the whole stepped-profile/retained-fillet section. The notes now state the four drawn 1.0 mm inside fillets (tool radius ≤ 1.0 mm, nearest copper ≥ 1.19 mm) and keep the two pre-existing sharp inside corners verbatim.
* PL5/PL8 needed no change: the 22 ripped-and-reconnected lands are declared with `--release` and each was re-connected.

## 5. Package

* Repo: `hardware/demo/fab/` (Gerbers, drills, CPL, BOM, assembly PDFs, FAB-NOTES, `MANIFEST.json` release D-805).
* PCBWay review/requote package (local only, **not sent**): `/home/aqroot8/vendor-packages/AQROOT_D805_PCBWay_Requote/` and `.zip` (sha256 `9363c594ad9cdaa9cd66d80cb7c1c8e5e81b00ab57ce4b539ffabbff87a4ef82`); 26/26 files match the MANIFEST; SHA256SUMS verified.
* Firmware: `Firmware/src/hw/aqroot_demo_board.{h,json}` — board digest string only.
* Identity surfaces bound to D-805 (CHANGELOG, CTO_DECISIONS, CURRENT_STATE, fab handoff STATUS, FAP-01 traveler, acceptance register, `evidence/d805-review-target.json`); D-804 fenced HISTORICAL.

## 6. Verdict

**GO for requesting a PCBWay requote** of the D-805 package. That is a price question only. Fabrication stays **HOLD**: the D-804 items stand (post-etch U9 ≥ 4.0 mil, stackup acknowledgement, B01–B14, FA01–FA10, procurement), plus enclosure apertures for J2/J3/SW9 and owner review of the two placement-contract words above.

The content commit, push result and PlatformIO post-commit build are recorded in `hardware/demo/manufacturing/evidence/d805-review-target.json` by the identity commit that follows.
