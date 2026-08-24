# AQROOT Full Beta v2 — FBV2-P1 mechanical regions and keepouts

**Status: NORMATIVE for FBV2-P2 and for the enclosure CAD.** Created 2026-08-24 at
**FBV2-P1-001**. All coordinates use the **P1 doc datum**: origin at the **lower-left board
corner**, X → right, Y → **up**, millimetres. `Y_kicad = 148.000 − Y_doc`.

Regions marked **rule area** are real KiCad copper keepouts and are enforced by DRC. Regions
marked **mechanical** are enclosure-only and are drawn on user layers for review — **no copper was
created merely to visualise a zone**.

---

## 1. Named regions

| id | name | X range | Y range | layer | kind | rule |
|---|---|---|---|---|---|---|
| **A** | `DISPLAY_SHADOW` | 3.39 … 59.93 | 55.04 … 140.00 | `User.1` | mechanical | **F.Cu component height ≤ 0.8 mm.** No `J1`, no switches, no module |
| — | `DISPLAY_ACTIVE` | 7.18 … 56.14 | 60.80 … 134.24 | `User.1` | mechanical | 48.96 × 73.44 active area, for the front aperture |
| **B** | `BATTERY_SHADOW` | 6.00 … 66.00 | 23.50 … 98.50 | `User.2` | mechanical | **B.Cu height ≤ 1.2 mm. No through-hole lead may protrude into it.** 60 × 75 × 8.0 mm |
| **C** | `NFC_ZONE` | 0.50 … 48.50 | 102.00 … 148.00 (+2.0 above the board) | `User.2` | mechanical | **48 × 48 clear region.** No boss, screw, shielding can, battery, speaker or cable. **B.Cu height ≤ 1.0 mm** (Column A rear air gap). F.Cu copper is permitted — the reverse ferrite faces the PCB |
| **D** | `NFC_METAL_KEEPOUT` | −4.50 … 53.50 | 97.00 … 148.00 | `User.2` | mechanical | loop perimeter + 5 mm. **No metal: screws, bosses, shielding cans** |
| **E** | `SPEAKER_ZONE` | 48.00 … 68.00 | 1.00 … 21.00 | `User.2` | mechanical | Ø20 × 3 driver + **1.5–2.0 cm³ sealed rear cavity. NO B.Cu components at all** |
| **F** | `ANT433_REGION` | −2.40 … −0.20 | 1.50 … 48.50 | `User.3` | mechanical | 433 MHz flex **on the LEFT cavity wall**, 47 × 17 × 0.28 mm, adhesive to plastic. **Not on the PCB** |
| **G** | `COMM_RECESS` | 59.90 … 70.00 | 104.00 … 138.00 | `User.3` | mechanical | recess ≥ 1.5 mm below the outer wall, asymmetric **upper-edge** key, **both ends closed to ≤ 0.3 mm**, backing boss carries ≈ 33 N |
| **H** | `USB_APERTURE` | 36.00 … 48.00 | −3.50 … 1.20 | `User.3` | mechanical | shell aperture must clear the receptacle **mouth** and the cable overmould |
| **I** | `USD_APERTURE` | 6.00 … 22.00 | −21.00 … 1.20 | `User.3` | mechanical | aperture **plus ≈ 22 mm of card insertion travel outside the shell**, clear of the USB plug |
| **J** | `IR_TX_OPTICAL` | 48.00 … 56.50 | 140.00 … 148.00 | `User.4` | mechanical | TSAL6100, ±10°, axis **normal to the top face** |
| **J** | `IR_RX_OPTICAL` | 61.50 … 70.00 | 140.00 … 148.00 | `User.4` | mechanical | TSOP38238, ±45° FOV |
| **J** | `IR_BARRIER` | 57.50 … 60.50 | 140.00 … 148.00 | `User.4` | mechanical | **MANDATORY opaque barrier, full height, bonded to BOTH shells** |
| **K** | `SMA_APPROACH` | 5.00 … 19.00 | 138.00 … 148.00 | `User.4` | mechanical | Ø6.5 mm bulkhead hole on the top panel, left half; coax approach. **Bend radius ≥ 5 mm, service loop ≥ 15 mm, must not cross the IR path** |
| **M** | `MIC_ACOUSTIC` | 0.50 … 5.50 | 46.50 … 53.50 | `User.1` | **rule area** | gasket footprint on the **FRONT** face; **no tracks, vias or pours on any copper layer**; Ø1.05 mm NPTH carried by the `MK1` footprint |
| **L** | `BOSS1_KEEPOUT` | 1.25 … 5.75 | 41.75 … 46.25 | `User.3` | **rule area** | M2, Ø2.2 NPTH |
| **L** | `BOSS2_KEEPOUT` | 57.25 … 61.75 | 142.75 … 147.25 | `User.3` | **rule area** | M2, Ø2.2 NPTH |
| **L** | `BOSS3_KEEPOUT` | 37.75 … 42.25 | 9.75 … 14.25 | `User.3` | **rule area** | M2, Ø2.2 NPTH |

## 2. ESP32 antenna keepout

Carried by the **`RF_Module:ESP32-S3-WROOM-1` footprint itself** as an all-copper-layer rule area —
it is not a drawn approximation.

| item | value |
|---|---|
| Zone | **X 63.06 … 84.06, Y −4.00 … 44.00** (48 × 21 mm, the manufacturer's own keep-out polygon) |
| On-board portion | **6.94 mm** deep along the right edge |
| Off-board portion | **14.06 mm**, i.e. two-thirds of the keep-out is air beyond the board edge |
| Forbids | tracks, vias, pads, copper pours **and footprints**, on **every** copper layer |
| Antenna direction | **+X**, module rotated 270°, radiating through the right plastic wall |
| Clearance to the 433 flex | the flex is on the **left** wall — opposite side of the device |
| Clearance to the NFC zone | **71.90 mm** |
| Clearance to the speaker | the keep-out clears the speaker cavity in X |

## 3. Height rules enforced during placement

| region | face | limit | source |
|---|---|---|---|
| `DISPLAY_SHADOW` | F.Cu | **≤ 0.8 mm** | measured Beta-DM limit, retained |
| `BATTERY_SHADOW` | B.Cu | **≤ 1.2 mm** | measured Beta-DM limit, retained |
| `NFC_ZONE` | B.Cu | **≤ 1.0 mm** | mechanical spec §3.3 Column A rear air gap |
| `SPEAKER_ZONE` | B.Cu | **no components** | sealed acoustic cavity |
| any through-hole part | both | its leads are treated as occupying **both** faces | prevents pins entering the battery, NFC or speaker volume |

All four limits were checked against **every** placed part. Violations: **zero**.

## 4. What is deliberately NOT here

- **No copper pours, no tracks, no vias.** FBV2-P2 owns those.
- **No enclosure CAD.** Every region above is a reservation the CAD must honour, not a model.
- **No stack-up change.** The layer stack, netclasses and design rules are the pre-P1 ones.
