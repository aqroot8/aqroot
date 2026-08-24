# AQROOT Full Beta v2 — FBV2-P1 mechanical regions and keepouts

**Status: NORMATIVE for FBV2-P2 and for the enclosure CAD.** Created 2026-08-24 at
**FBV2-P1-001**, **superseded in part 2026-08-24 at FBV2-P1-002**. All coordinates use the
**P1 doc datum**: origin at the **lower-left board corner**, X → right, Y → **up**, millimetres.
`Y_kicad = 148.000 − Y_doc`.

Regions marked **rule area** are real KiCad copper keepouts and are enforced by DRC. Regions
marked **mechanical** are enclosure-only and are drawn on user layers for review — **no copper was
created merely to visualise a zone, and none was created for plastic support.**

---

## 1. Named regions

| id | name | extent | layer | kind | rule |
|---|---|---|---|---|---|
| **A** | `DISPLAY_SHADOW` | X 3.39 … 59.93, Y 55.04 … 140.00 | `User.1` | mechanical | **F.Cu component height ≤ 0.8 mm.** No `J1`, no switches, no module |
| — | `DISPLAY_ACTIVE` | X 7.18 … 56.14, Y 60.80 … 134.24 | `User.1` | mechanical | 48.96 × 73.44 active area, for the front aperture |
| **B** | `BATTERY_SHADOW` | X 6.00 … 66.00, Y 23.50 … 98.50 | `User.2` | mechanical | **B.Cu height ≤ 1.2 mm. No through-hole lead may protrude into it.** 60 × 75 × 8.0 mm. **UNCHANGED at P1-002** |
| **C** | `NFC_CLEAR_D48` | **Ø48 circle, centre 30.800, 124.500** → X 6.80 … 54.80, Y 100.50 … 148.50 | `User.2` | mechanical | **Ø48 metal-free CLEAR region.** No boss, screw, shielding can, battery, speaker or cable. **B.Cu height ≤ 1.0 mm.** F.Cu copper is permitted — the reverse ferrite faces the PCB |
| **C2** | `NFC_PLACEMENT_BOX` | 48 × 48 square, same centre | `User.2` | mechanical | **placement / positioning tolerance envelope only**, per CTO §2A. It is NOT a metal exclusion |
| **D** | `NFC_METAL_D58` | **Ø58 circle, same centre** → X 1.80 … 59.80, Y 95.50 … 153.50 | `User.2` | mechanical | loop perimeter + 5 mm. **No metal: screws, bosses, shielding cans.** Supersedes the 58 × 51 rectangle; the circle is inscribed in it, so only the four corners are reclaimed |
| **E** | `SPEAKER_ZONE` | X 48.00 … 68.00, Y 1.00 … 21.00 | `User.2` | mechanical | Ø20 × 3 driver + **1.5–2.0 cm³ sealed rear cavity. NO B.Cu components at all.** **UNCHANGED** |
| **F** | `ANT433_REGION` | X −2.40 … −0.20, Y 1.50 … 48.50 | `User.3` | mechanical | 433 MHz flex **on the LEFT cavity wall**, 47 × 17 × 0.28 mm, adhesive to plastic. **Not on the PCB** |
| **G** | `COMM_RECESS` | X 59.90 … 70.00, Y 104.00 … 138.00 | `User.3` | mechanical | recess ≥ 1.5 mm below the outer wall, asymmetric **upper-edge** key, **both ends closed to ≤ 0.3 mm**, backing boss carries ≈ 33 N |
| **H** | `USB_APERTURE` | X 36.00 … 48.00, Y −3.50 … 1.20 | `User.3` | mechanical | shell aperture must clear the receptacle **mouth** and the cable overmould |
| **I** | `USD_APERTURE` | X 6.00 … 22.00, Y −21.00 … 1.20 | `User.3` | mechanical | aperture **plus ≈ 22 mm of card insertion travel outside the shell**, clear of the USB plug |
| **J** | `IR_TX_OPTICAL` | X 48.00 … 56.50, Y 140.00 … 148.00 | `User.4` | mechanical | TSAL6100, ±10°, axis **normal to the top face** |
| **J** | `IR_RX_OPTICAL` | X 61.50 … 70.00, Y 140.00 … 148.00 | `User.4` | mechanical | TSOP38238, ±45° FOV |
| **J** | `IR_BARRIER` | **X 56.50 … 61.50**, Y 140.00 … 148.00 | `User.4` | mechanical | **MANDATORY opaque barrier, full height, bonded to BOTH shells.** **WIDENED 3.0 → 5.0 mm at P1-002** so it fills the whole inter-window gap, touching neither window, and **it carries `BOSS2`** |
| **K** | `SMA_APPROACH` | X −1.00 … 11.00, Y 134.00 … 148.00 | `User.4` | mechanical | **Ø6.5 mm bulkhead hole at doc (5.000, 148.000)**, top panel, left half. Ø10.2 washer envelope drawn. **Bend radius ≥ 5 mm, service loop ≥ 15 mm, must not cross the IR path.** **MOVED from x 12.000 at P1-002** |
| **N** | `COAX_915_CHANNEL` | X −1.50 … 6.00, Y 24.00 … 110.00 | `User.4` | mechanical | **NEW at P1-002.** The reserved lane for the 915 MHz assembly between the board's left edge and the battery. **No boss, no rib and no edge-capture rail may occupy it.** The route polyline itself is drawn on the same layer |
| **M** | `MIC_ACOUSTIC` | X 0.50 … 5.50, Y 46.50 … 53.50 | `User.1` | **rule area** | gasket footprint on the **FRONT** face; **no tracks, vias or pours on any copper layer**; Ø1.05 mm NPTH carried by the `MK1` footprint |
| **L** | `BOSS1_KEEPOUT` | X 37.75 … 42.25, Y 9.75 … 14.25 | `User.3` | **rule area** | M2, Ø2.2 NPTH at doc (40.000, 12.000) |
| **L** | `BOSS2_KEEPOUT` | X 56.75 … 61.25, Y 142.75 … 147.25 | `User.3` | **rule area** | M2, Ø2.2 NPTH at doc (59.000, 145.000), inside the IR barrier |
| **P** | `RIB_R1` | X 66.20 … 69.70, Y 24.00 … 44.00 | `User.3` | mechanical | rear non-metallic support pad. **Component-free, verified** |
| **P** | `RIB_R2` | X 66.20 … 69.70, Y 45.00 … 64.00 | `User.3` | mechanical | rear support pad, behind the A/B control area |
| **P** | `RIB_R3` | X 66.20 … 69.70, Y 76.00 … 97.00 | `User.3` | mechanical | rear support pad, mid-upper right margin |
| **P** | `RIB_B1` | X 44.00 … 47.60, Y 21.20 … 23.30 | `User.3` | mechanical | rear support pad, bottom strip below the battery |

**Withdrawn at FBV2-P1-002:** `NFC_ZONE` (the 48 × 48 square metal-free region — superseded by
`NFC_CLEAR_D48` + `NFC_PLACEMENT_BOX`), the 58 × 51 rectangular `NFC_METAL_KEEPOUT` (superseded by
`NFC_METAL_D58`), and `BOSS3_KEEPOUT` together with P1-001's `BOSS1` position at (3.5, 44.0).

## 2. ESP32 antenna keepout

Carried by the **`RF_Module:ESP32-S3-WROOM-1` footprint itself** as an all-copper-layer rule area —
it is not a drawn approximation. **Unchanged at P1-002.**

| item | value |
|---|---|
| Zone | **X 63.06 … 84.06, Y −4.00 … 44.00** (48 × 21 mm, the manufacturer's own keep-out polygon) |
| On-board portion | **6.94 mm** deep along the right edge |
| Off-board portion | **14.06 mm**, i.e. two-thirds of the keep-out is air beyond the board edge |
| Forbids | tracks, vias, pads, copper pours **and footprints**, on **every** copper layer |
| Antenna direction | **+X**, module rotated 270°, radiating through the right plastic wall |
| Clearance to the 433 flex | the flex is on the **left** wall — opposite side of the device |
| Clearance to the NFC clear region | **> 70 mm** |

> **Note for the collision reviewer.** The footprint's `F.CrtYd` bounding box **is** this keep-out
> polygon, not the module body. Collision review must use the module **body**,
> X 42.90 … 63.06, Y 9.90 … 30.10, and test the keep-out separately. `p1_geometry.py` does this
> automatically (`U1_BODY`); reviewing against the raw courtyard reports 58 false collisions.

## 3. Height rules enforced during placement

| region | face | limit | source |
|---|---|---|---|
| `DISPLAY_SHADOW` | F.Cu | **≤ 0.8 mm** | measured Beta-DM limit, retained |
| `BATTERY_SHADOW` | B.Cu | **≤ 1.2 mm** | measured Beta-DM limit, retained |
| `NFC_CLEAR_D48` | B.Cu | **≤ 1.0 mm** | mechanical spec §3.3 Column A rear air gap |
| `SPEAKER_ZONE` | B.Cu | **no components** | sealed acoustic cavity |
| any through-hole part | both | its **leads and holes** occupy both faces | prevents pins entering the battery, NFC or speaker volume |

## 4. Objects recorded INSIDE the Ø58 metal exclusion

Neither is a screw, a boss or a shielding can, so neither breaches the rule as written; both are
recorded so no later reader has to rediscover them.

| object | inside by | note |
|---|---|---|
| battery pouch foil | **3.000 mm** | 1.500 mm inside the superseded rectangle. Zero overlap with the **clear** region (2.000 mm gap) — the locked policy N-5 holds |
| `D1` `TSAL6100` leadframe | **1.381 mm** | 3.619 mm outside the Ø48 loop perimeter. Was inside the superseded rectangle too. Cannot move without breaking the ≥ 15 mm IR TX↔RX rule |

## 5. What is deliberately NOT here

- **No copper pours, no tracks, no vias.** FBV2-P2 owns those.
- **No enclosure CAD.** Every region above is a reservation the CAD must honour, not a model.
- **No stack-up change.** The layer stack and netclasses are the pre-P1 ones. The only
  `.kicad_dru` change is §15, the scoped `U1` thermal-pad hole-size guard.
- **No copper pad for plastic support.** The four `RIB_*` regions are mechanical reservations on
  `User.3` and carry no copper.
