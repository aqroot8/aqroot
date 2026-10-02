# AQROOT Demo — PCBWay 6-layer stackup (D-804 candidate)

**Board:** `aqroot-Beta-v2` (AQROOT Demo), 77.1 × 148.1 mm, 6 copper layers, through-hole vias only.
**Status:** this is the stackup ORDERED for the PCBWay re-check of the D-804 candidate.  It
restates the board file's own stackup block (`aqroot-Beta-v2.kicad_pcb`, also carried as Gerber
X2 `MaterialStackup` in `aqroot-Beta-v2-job.gbrjob`) in PCBWay terms.  It changes no electrical
design constraint.

## 1. Order parameters

| parameter | requirement |
|---|---|
| Layers | **6** |
| Finished board thickness | **1.6 mm nominal**; acceptance **1.474 – 1.674 mm** (declared stack 1.5744 mm ± 0.10 mm) |
| Laminate | FR-4, **Tg ≥ 150 °C**, certified (state brand / grade on the acknowledgement).  **TG130 is refused.** |
| Outer copper L1, L6 | **1 oz finished** (≈ 0.035 mm) |
| Inner copper L2, L3, L4, L5 | **0.5 oz**, finished thickness **≥ 0.0152 mm** on every inner layer (see §3) |
| Surface finish | **ENIG** — not substitutable (state Ni / Au thickness) |
| Solder mask | both sides; **0.000 mm expansion** — the mask aperture IS the copper; do not apply a house expansion |
| Via structure | plated through-holes only; no blind / buried vias |
| Impedance control | **not ordered** (no impedance coupon); the dielectric bounds in §2 protect the RF feeds and USB pair drawn on this stack |

## 2. Layer order and dielectric distribution (reference = the board file)

| # | layer | Gerber file | role | type | thickness (mm) | material |
|---|---|---|---|---|---|---|
| | F.Mask | `aqroot-Beta-v2-F_Mask.gbr` | | mask | 0.0100 | |
| **L1** | F.Cu | `aqroot-Beta-v2-F_Cu.gbr` (`Copper,L1,Top`) | signal + pours | copper | **0.0350** (1 oz) | |
| | dielectric 1 | | | **prepreg** | **0.2104** | 7628, εr 4.4 |
| **L2** | In1.Cu | `aqroot-Beta-v2-In1_Cu.gbr` (`Copper,L2,Inr`) | GND plane | copper | **0.0152** (0.5 oz) | |
| | dielectric 2 | | | **core** | **0.4000** | FR-4, εr 4.4 |
| **L3** | In2.Cu | `aqroot-Beta-v2-In2_Cu.gbr` (`Copper,L3,Inr`) | signal | copper | **0.0152** (0.5 oz) | |
| | dielectric 3 | | | **prepreg** | **0.2028** | 7628, εr 4.4 |
| **L4** | In3.Cu | `aqroot-Beta-v2-In3_Cu.gbr` (`Copper,L4,Inr`) | signal + pours | copper | **0.0152** (0.5 oz) | |
| | dielectric 4 | | | **core** | **0.4000** | FR-4, εr 4.4 |
| **L5** | In4.Cu | `aqroot-Beta-v2-In4_Cu.gbr` (`Copper,L5,Inr`) | GND plane | copper | **0.0152** (0.5 oz) | |
| | dielectric 5 | | | **prepreg** | **0.2104** | 7628, εr 4.4 |
| **L6** | B.Cu | `aqroot-Beta-v2-B_Cu.gbr` (`Copper,L6,Bot`) | signal + pours | copper | **0.0350** (1 oz) | |
| | B.Mask | `aqroot-Beta-v2-B_Mask.gbr` | | mask | 0.0100 | |
| | **total** | | | | **1.5744** | |

Construction: foil-laminated, **prepreg / core / prepreg / core / prepreg**, symmetric about L3–L4.
This is the JLC06161H-7628 distribution the design was drawn on.

## 3. Equivalent stack — allowed only with written approval

PCBWay may propose its closest standard 6-layer 1.6 mm stack.  **It must be returned as a
layer-by-layer stackup drawing for our written approval before any material is cut**, and it is
acceptable only if every line below holds:

1. Same layer order and roles, same symmetric prepreg / core / prepreg / core / prepreg build.
2. **L1–L2 and L5–L6 dielectric 0.19 – 0.23 mm, εr 4.2 – 4.7.**  The RF feeds and the USB pair are
   referenced to these two gaps; a thicker or lower-εr outer gap changes them.
3. L2–L3 and L4–L5 cores 0.36 – 0.44 mm; L3–L4 prepreg 0.18 – 0.23 mm.
4. Finished thickness inside 1.474 – 1.674 mm.
5. **Inner copper finished ≥ 0.0152 mm on L2–L5.**  The rail-ampacity audit sizes every inner-layer
   power path on 0.0152 mm of foil.  If PCBWay's 0.5 oz inner process can finish below that
   (e.g. an IPC minimum near 0.0114 mm), say so and state the guaranteed minimum: that is a
   HOLD — we re-run the ampacity audit before approving.  Heavier inner copper (1 oz) is a
   change too and must be stated, not substituted.
6. Outer copper 1 oz finished; Tg ≥ 150 °C; ENIG.

## 4. Data handling

**Do not edit, cut, shave, re-shape, re-space or re-route any copper, mask, paste, drill or outline
feature.**  If a CAM / DFM check finds anything below your process minimum, stop and send us the
layer, coordinates and measured value; we will return corrected authoritative files.  The fab
notes' named process requirements (via-in-pad POFV, plated slots, sub-floor vias, J3 NPTH, mask
dams) are unchanged by this document.
