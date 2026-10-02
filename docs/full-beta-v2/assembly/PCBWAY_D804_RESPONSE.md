# AQROOT Demo — PCBWay CAM / PCBA response, D-804 candidate

**Quote:** PCBWay `T-5D2W1187157A` (PCB fabrication $278.16, assembly $1297.03, components
$708.60 for 5 PCBAs; 123 BOM lines = `aqroot-Demo-BOM-assembly.csv`, 123 lines).
**Board:** `aqroot-Beta-v2.kicad_pcb` sha256 `abb0c391…0de987` on branch
`d804-u9-pcbway-cam-candidate`.  **Candidate only — not promoted to `aqroot-demo`.**

PCBWay is **not** authorized to edit any geometry.  Every finding below that was real is
corrected in the authoritative KiCad board and the Gerbers are regenerated from it.

## 1. Manufacturer CAM concerns

| # | PCBWay concern | Finding (measured on the released Gerbers, independent extractor + KiCad) | Class | Disposition |
|---|---|---|---|---|
| CAM-1 | U9 min clearance 1.55 mil < 4 mil | D-803 Gerber min 2.446 mil at the four U9 diagonal corners. D-804 rounds U9.1/8/9/16/17/24/25/32 (rratio 0.25→0.50; centres, sizes, placement, routing unchanged): **4.892 mil** (0.1243 mm). Every other different-net gap on all 6 copper layers ≥ 5 mil. | REAL DEFECT (land corner geometry) | **Corrected (D804-01).** Ask PCBWay to re-measure AFTER etch compensation and stop/report if < 4.0 mil. |
| CAM-2 | Include custom 6-layer stackup | Board stackup block = Gerber X2 job file: 1.5744 mm, 1 oz outer, 0.5 oz inner (0.0152 mm), 7628 P/C/P/C/P, ENIG. | — | **`PCBWAY_STACKUP.md` (D804-04)** shipped in the package; any PCBWay-equivalent stack must be returned for written approval. |
| CAM-3a | Apparent crossings — overlay | Layer-by-layer: **0 different-net crossings, 0 different-net overlaps, 0 shorts** on every copper layer (D-803 and D-804 alike). Signals run on L1/L3/L4/L6; an all-layer overlay shows them crossing. | BENIGN CAM VIEWER ARTIFACT | Explain; ask PCBWay to view one layer at a time. |
| CAM-3b | Apparent crossings — same layer | 133 same-layer crossings/overlaps, **every one same-net** (L1 32, L3 15, L4 1, L6 85), incl. duplicated segments; listed with coordinates. | INTENTIONAL (same node, not a short) | Build as supplied; do not merge/remove. |
| CAM-4a | Open-ended traces — real | D-803 had **3** draw ends touching no same-net copper: `In2.Cu` `EXT_SDA_BUF` (60.150, 40.800) and (60.300, 40.800) — two D-725 segment ends 0.150 mm apart, joined only by a 0.05 mm cap overlap (0.132 mm neck); `B.Cu` `BQ25185_SYS` (57.150, 37.900), U21.3 stub end 0.075 mm outside `L4.1`. KiCad counted both as connected (shape overlap), so no connectivity gate flagged them. | REAL DEFECT (CAM-class; electrically connected) | **Corrected (D804-03)**: one added segment of the net's own width each, nothing removed. D-804: **0 open ends on all layers.** |
| CAM-4b | Open-ended traces — isolated pads | 46 pads with no routed copper: 18 DNP-part pads (`U13 L2 R44 R45 C34 C35 R107 R68 R112 C81 C82 R123`), `TP9` (DNP `U13` rail), `U11.3` (owner-approved NC, D-742), 26 no-net NC/mounting pads (`J1 J2 J7 J8 U7 U8 U9`). No trace stub on any of them. The 11 split nets are identical D-803 vs D-804 and every split is one of these pads. | APPROVED NC-DNP | Explain; list shipped as CSV. |
| CAM-5 | Do not let PCBWay edit geometry | — | — | Stated in the reply, the stackup doc §4 and FAB-NOTES. |

**Stale export:** none.  The in-tree Gerbers are regenerated from the D-804 board; their copper
is identical (timestamps aside) to the Gerbers the extractor measured, and the earlier
`AQROOT_D804_U9_PCBWay_CAM_RECHECK_Gerbers.zip` (04:02, U9 only) is **superseded** — it lacks D9
and the two joints and must not be sent.

## 2. PCBWay BOM notes (12)

| # | Line | PCBWay note | Finding | Class | Reply |
|---|---|---|---|---|---|
| 1 | `C20` | CC0805KKX7R8BB475 is 25 V, not 10 V | Value text `4.7uF 10V` is the specified minimum; `demo_feature_contract` proves bought rating ≥ specified and survives the absolute stress. Same 0805 land. | BOM description metadata | Confirm; supply exact MPN. |
| 2 | `C25,C37,C38,C62,C63,C67,C85` | CC0603KRX7R8BB105 is 25 V, not 10 V | as above, 0603 | metadata | Confirm. |
| 3 | `C26,C27` | GRM31CR71E106KA12L is 25 V, not 10 V | as above, 1206 | metadata | Confirm. |
| 4 | `C33,C64,C83,C84` | CC0805KKX7R7BB106 is 16 V, not 10 V | as above, 0805 | metadata | Confirm. |
| 5 | `C43` | CL21A475KAQNNNE is 25 V, not 10 V | as above, 0805 | metadata | Confirm. |
| 6 | `C71,C72` | GCM1885C2A301FA16J is 100 V, not 50 V | NFC tuning; worst non-DC ≤ 20 V pk derived; 100 V intended | metadata | Confirm; no substitution. |
| 7 | `C73,C74` | GCM1885C2A152JA16D is 100 V, not 50 V | NFC EMC filter; 100 V intended | metadata | Confirm; no substitution. |
| 8 | `C75,C77` | GQM1875C2E270FB12D is 250 V, not 50 V | NFC receive series; ≤ 26 V pk derived; 250 V intended | metadata | Confirm; no substitution. |
| 9 | `D9` | PMEG2010AEH,115 is SMF (SOD-123FL), not `D_SOD-123` | **Real footprint error.** Nexperia PMEG2010AEH data sheet (8 Oct 2024) and SOD123F package information (27 May 2022): SOD123F, pin 1 = K; reflow land **1.1 × 1.1 at 2.8 pitch**. D-803 land was SOD-123 0.90 × 1.20 at ±1.65. | REAL DEFECT (footprint) | **Corrected (D804-02)**: `Diode_SMD:D_SOD-123F` on board + schematic, polarity unchanged; tier 3 → tier 1. Genuine Nexperia only (LCSC `C110921`); the JSMSEMI `PMEG2010AEH,115-JSM` look-alike is SOD-123 and refused. |
| 10 | `J5` | SSQ-124-02-G-S-RA out of stock; substitute or consign | Already a planned consignment line (Class E manual, FIRST_FIVE_ASSEMBLY_PLAN). No substitute qualified for pinout, 0.635 mm post mating, current, RA geometry. | procurement | **No substitute.** We consign the exact Samtec part. |
| 11 | `J6` | Sensitive part — needs firm pressing; >100 pcs confirm cost | 5 boards; THT manual line. | assembly note | Acknowledge; seat flush and square; no substitution. |
| 12 | `L4` | 74438357010 is SMD 4.1 × 4.1, not "4030" | Würth WE-MAPI size code 4030 = 4.1 ± 0.2 mm body, 3.1 max height (archived data sheet). Same part, same land. | naming only | Confirm exact MPN; we may consign. |

## 3. Email text to PCBWay

The exact text is `hardware/demo/manufacturing/evidence/d804-pcbway-response.txt`, shipped in
the package as `00_READ_FIRST_AQROOT_D804_Response.txt`.
