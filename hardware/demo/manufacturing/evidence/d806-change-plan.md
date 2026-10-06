# D-806 CHANGE PLAN AND BASELINE RECORD (written before any edit)

D-806 is a manufacturing-readiness revision driven by JLCPCB engineering feedback received 2026-10-06.
It is **not** a refloor or a feature revision. D-805 is frozen.

## Identity

| item | value |
|---|---|
| branch | `d806-jlcpcb-manufacturing` (worktree `/home/aqroot8/w/d806-jlcpcb`) |
| frozen D-805 parent (delivery identity) | `a8837f71667f2f737c69dab47b33dd410bdbd7e7` |
| frozen D-805 source milestone | `4a3585202606de82d71b19960e35a86964c92f87` (ancestor of the parent, verified) |
| D-805 board sha256 | `0689d6e677df530d84d3986f4a8450fa7ed39272535b2cfc1ecfc6ae857887c1` |
| D-805 `.kicad_dru` sha256 | `78002a27e2bf48db850b63433e179c821279b68ca243cc50686adab547b785a1` |
| D-805 `.kicad_pro` sha256 | `9b758a753f771b953ae3871b3ed2dc596153f2dc414759686c2cd8b3507e926b` |
| D-805 fab `MANIFEST.json` sha256 | `4f027e255f161350c412166c23bdf783a45caf432578ccc9f876de4078e07ccf` |
| D-805 JLCPCB RFQ zip sha256 | `1d5861593821c2faa53717a4ecafc12ac963a13b80a58df74069c9e9b39e2533` |
| `ST25R3916_AQET.kicad_mod` master sha256 | `28f7ae4894eaf98b6eeddf9e1a3b8b65fb1c925cb34148dd2557550675bcc547` |
| `Molex_5025700893.kicad_mod` master sha256 | `c90eb19bbf5ced0dacd2dcf96015ebc8373119ca0d6bc348baf3109e6e9dc860` |
| schematic sheets | 10 `.kicad_sch`, sha256 equal to the D-805 MANIFEST (to be re-verified after D-806) |

Frozen worktrees recorded before work (HEAD, clean): `d805-delivery-artifact` `a8837f71`, `d805-interface` `4a358520`, `d804-u9` `466a5058`; `aqroot-demo` `576c8cec` carries ONE pre-existing untracked entry (`mechanical/`), which this work does not touch.

## Baseline measurements (D-805 board / D-805 Gerbers)

1. **J2 shell lands to routed edge.** `J2.9` shell lands at (8.656, 149.937) and (21.556, 149.937), 1.40 x 1.70 mm, outer extent Y 150.787; the J2 tab edge is Y 151.000. Clearance **0.213 mm** (JLCPCB's figure, reproduced). Tab side clearances 1.956 / 1.744 mm. The only DRU licence is `J2 microSD shell edge clearance (vendor land pattern)` at **0.20 mm**.
2. **Different-net copper gaps, from the D-805 Gerbers (independent extractor, no KiCad), threshold 6.0 mil:** the ONLY gaps under 5.2 mil on the whole board are the four `U9` QFN corner pairs, each **0.12425 mm = 4.892 mil**: `U9.1/U9.32` (+3V3 / SPI_B_MISO), `U9.8/U9.9` (NFC_SUPPLY / NFC_VDD_RF), `U9.16/U9.17` (GND / no-net), `U9.24/U9.25` (NFC_AGDC / no-net). Every other sub-6.0-mil gap is **0.150 mm = 5.906 mil** (12 on F.Cu at D2/D4/D5, 27 on B.Cu at U13/U16/U18/U19/U21/TPD4E/SOT-563 class land patterns), i.e. above the 5.2 mil hard floor.
   Cause: the corner lands are 0.75 x 0.30 mm stadiums whose bounding boxes meet exactly at the package corner, so the gap is sqrt(2) x 0.30 - 0.30 = 0.1243 mm.
3. **Via outer-minus-hole census:** 915 vias (corrected: an earlier draft of this line said 970). **35 are 0.35/0.20 mm (outer - hole 0.150 mm)**, below JLCPCB's 0.20 mm. Six of them sit in a solderable land: `U9.16` (GND, D-649 pour bridge), `R2.1`, `U11.11`, `Q3.3`, `J3.A4/B9` and `J3.A9/B4` (D-531 VBUS POFV). Every other via (0.45/0.20 and up) and every PTH pad meets 0.20 mm.
4. **Assembly drawings:** A4, scale 0.60, F.Fab/B.Fab only. Refs are present in the PDF text layer for 250/251 fitted parts (`MK1` absent), but passive refs are sub-millimetre and overprinted by body outlines: unusable for locating parts, which is JLCPCB's finding.
5. **Profile:** 24 Edge.Cuts items (16 lines, 4 r 1.000 inside fillets, 4 r 0.500 outside corners), bbox 0..77 x 0..151; two sharp inside corners at (72.000, 104.005) and (72.000, 70.500). The phrase "stepped profile" is undefined for the vendor.
6. **DRC baseline (kicad-cli 10.0.5, `--severity-all --schematic-parity`):** 199 `lib_footprint_issues` warnings, 0 errors, 17 unconnected (D-804 declared set), 246 parity warnings.

## Planned changes (minimum geometry)

| # | change | why | expected result |
|---|---|---|---|
| G1 | Translate **J2 by (0, -0.150 mm)** (inward); every J2-pad track end moves with its pad. Outline unchanged. | JLCPCB >= 0.25 mm, D-806 target >= 0.30 mm. Keeps the D-805 tab, tab-to-wall gap and enclosure intent; card-entry face 150.850, inside the 0.25 mm datum tolerance. | J2 shell land to edge **0.363 mm** |
| G2 | **U9 corner-land heel trim**: the 8 corner lands (1, 8, 9, 16, 17, 24, 25, 32) shortened 0.030 mm at the INNER (heel) end, 0.75 -> 0.72 mm, toe and width unchanged. Board instance and library master. | JLCPCB: >= 5.2 mil pre-CAM for >= 4.0 mil post-CAM; D-806 target 6.0 mil. Datasheet DS12484 Rev 3 Table 134: terminal L <= 0.50 mm, so the worst-case terminal ends at 0.50 mm inside the package edge; the trimmed heel still reaches 0.57 mm. U9 placement, nets, matching network and antenna untouched. | corner gap sqrt(2) x 0.33 - 0.30 = **0.1667 mm = 6.56 mil** |
| G3 | Grow the **35 vias 0.35/0.20 -> 0.40/0.20** (drill unchanged). | JLCPCB: outer >= hole + 0.20 mm. Scratch experiment: all 35 grown + zones refilled gives ZERO new DRC violations; every licence area still encloses its barrel. | every via outer - hole >= 0.200 mm |
| G4 | `.kicad_dru`: J2 edge licence 0.20 -> **0.25 mm**; U9 intra-footprint clearance 0.12 -> **0.1524 mm (6.0 mil)**. | KiCad DRC itself then enforces the JLCPCB figures (native, non-regressable). | DRC clean |
| G5 | Zones refilled to their fixed point. | | |
| D1 | New D-806 contract `checks/jlc_manufacturing_contract.py` (J2 edge, U9 gaps on board AND Gerber, via outer-minus-hole on board AND Excellon+Gerber, assembly reference mapping, profile identity), each clause with destructive controls. | | |
| D2 | Readable assembly drawing set (A3, 2:1, ref at every CPL centroid, grid + index) and a dimensioned profile drawing, generated deterministically from the board. | | |
| D3 | JLCPCB-specific handoff: manual production-file and parts-placement confirmation REQUIRED, thickness position, edge-rail strategy, sourcing record. | | |

Not changed: schematic, netlist, BOM identities, outline/profile, stackup, `.kicad_pro`, every footprint pose except J2, every pad except the 8 U9 corner lands.

## Stop conditions watched

SW4 must not move (it does not under G1). If any of G1-G3 produces a DRC/CAM defect that cannot be closed locally, the change is reverted to the documented blocker instead of broadening scope.
